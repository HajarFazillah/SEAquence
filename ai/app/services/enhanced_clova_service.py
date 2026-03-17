"""
Enhanced HyperCLOVA X Service
With personalized system prompts and teaching mode
"""

import httpx
import json
import logging
from typing import Optional, List, Dict, Any, AsyncGenerator

from app.core.config import settings
from app.core.constants import (
    AVATARS, TOPIC_TAXONOMY,
    get_formality_instruction
)

logger = logging.getLogger(__name__)


# ===========================================
# Formality Instructions (Enhanced)
# ===========================================

FORMALITY_INSTRUCTIONS_DETAILED = {
    "informal": {
        "name_ko": "반말",
        "name_en": "Informal",
        "instruction": """반말을 사용하세요.
문장 끝: ~어/아, ~지, ~냐, ~야, ~거든, ~잖아
예시: "뭐해?", "밥 먹었어?", "가자", "알았어"
금지: ~요, ~습니다 사용하지 마세요.""",
        "examples": ["야 뭐해?", "밥 먹었어?", "같이 가자", "알았어"],
        "endings": ["~어", "~아", "~지", "~냐", "~야"]
    },
    "polite": {
        "name_ko": "존댓말",
        "name_en": "Polite",
        "instruction": """존댓말(-요)을 사용하세요.
문장 끝: ~요, ~세요, ~죠, ~네요, ~거든요
예시: "뭐 해요?", "밥 먹었어요?", "가요"
선배/초면에게 적절한 말투입니다.""",
        "examples": ["뭐 해요?", "밥 먹었어요?", "같이 가요", "알겠어요"],
        "endings": ["~요", "~세요", "~죠", "~네요"]
    },
    "very_polite": {
        "name_ko": "격식체",
        "name_en": "Formal",
        "instruction": """격식체(-습니다)를 사용하세요.
문장 끝: ~습니다, ~습니까, ~십시오, ~겠습니다
높임말: 드리다, 여쭙다, 말씀, 뵙다, 계시다
예시: "무엇을 하십니까?", "식사하셨습니까?"
교수님/상사에게 사용하는 가장 공손한 말투입니다.""",
        "examples": ["안녕하십니까?", "감사합니다", "여쭤봐도 될까요?"],
        "endings": ["~습니다", "~습니까", "~십시오"]
    }
}


# ===========================================
# Teaching Prompts
# ===========================================

TEACHING_PROMPTS = {
    "beginner": """
## 교정 방식 (초급자용)
- 학습자가 실수하면 친절하게 올바른 표현을 알려주세요
- 예시와 함께 설명해주세요
- 예: "아, '{correct}'라고 하면 더 좋아요! 😊"
- 너무 많은 정보를 한번에 주지 마세요
- 격려와 칭찬을 많이 해주세요
""",
    "intermediate": """
## 교정 방식 (중급자용)
- 학습자가 실수하면 자연스럽게 올바른 표현을 사용해서 대답하세요
- 직접적인 교정보다 모델링을 통해 알려주세요
- 가끔 "참고로 이런 상황에서는 ~라고 해요"처럼 팁을 주세요
""",
    "advanced": """
## 교정 방식 (고급자용)
- 미묘한 뉘앙스 차이를 설명해주세요
- 더 자연스러운 표현이나 관용구를 알려주세요
- 학습자를 동등한 대화 상대로 대해주세요
"""
}


ERROR_CORRECTION_PROMPTS = {
    "ending_mismatch": """
- 학습자가 문장 끝을 잘못 사용하면 (예: 교수님께 "있어요" 사용):
  자연스럽게 올바른 어미를 사용해서 대답하고, 
  "참고로 저한테는 '~습니다'로 말씀해 주시면 돼요" 같이 알려주세요.
""",
    "honorific_missing": """
- 학습자가 높임말을 빠뜨리면 (예: "먹었어요?" 대신 "드셨어요?"):
  "네, 점심 먹었어요~ 참, 어른께는 '드셨어요?'라고 여쭤보면 더 좋아요!"
""",
    "formality_mixed": """
- 학습자가 말투를 섞어 사용하면:
  "앗, 방금 반말이랑 존댓말이 섞였어요! 저한테는 ~로 통일해서 말해주세요 😊"
"""
}


class EnhancedClovaService:
    """
    Enhanced HyperCLOVA X Service with:
    - Personalized system prompts
    - User context awareness
    - Teaching/correction mode
    - Adaptive difficulty
    """
    
    def __init__(self):
        self.host = settings.NAVER_CLOVA_HOST
        self.endpoint = settings.NAVER_CLOVA_CHAT_ENDPOINT
        self.api_key = settings.NAVER_CLOVA_API_KEY
        self.api_key_primary = settings.NAVER_CLOVA_API_KEY_PRIMARY
        self.request_id = settings.NAVER_CLOVA_REQUEST_ID
        
    @property
    def is_configured(self) -> bool:
        """Check if CLOVA API is properly configured."""
        return bool(self.api_key and self.api_key_primary)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers for CLOVA API."""
        return {
            "X-NCP-CLOVASTUDIO-API-KEY": self.api_key,
            "X-NCP-APIGW-API-KEY": self.api_key_primary,
            "X-NCP-CLOVASTUDIO-REQUEST-ID": self.request_id or "",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    
    def build_system_prompt(
        self,
        avatar_id: str,
        topic: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
        custom_instruction: Optional[str] = None
    ) -> str:
        """
        Build personalized system prompt for avatar conversation.
        
        Args:
            avatar_id: Avatar identifier
            topic: Current conversation topic
            user_context: User's learning context (level, weak skills, etc.)
            custom_instruction: Additional instructions
            
        Returns:
            Complete system prompt string
        """
        # Get avatar info
        avatar = AVATARS.get(avatar_id)
        if not avatar:
            avatar = AVATARS.get("sujin_friend", {
                "name_ko": "수진",
                "role": "friend",
                "age": 22,
                "personality": "친근한 친구",
                "formality": "informal"
            })
        
        formality = avatar.get("formality", "polite")
        formality_info = FORMALITY_INSTRUCTIONS_DETAILED.get(formality, FORMALITY_INSTRUCTIONS_DETAILED["polite"])
        
        # Build topic context
        topic_context = ""
        if topic and topic in TOPIC_TAXONOMY:
            topic_info = TOPIC_TAXONOMY[topic]
            topic_context = f"""
## 현재 대화 주제
- 주제: {topic_info.get('name_ko', topic)}
- 설명: {topic_info.get('description', '')}
- 관련 키워드: {', '.join(topic_info.get('keywords', [])[:5])}
"""
        
        # Build user context section
        user_section = self._build_user_context_section(user_context)
        
        # Build teaching section
        teaching_section = self._build_teaching_section(user_context)
        
        # Build error correction section
        error_section = self._build_error_correction_section(user_context)
        
        # Assemble the complete prompt
        system_prompt = f"""당신은 한국어 대화 연습을 도와주는 AI 아바타입니다.
사용자가 한국어로 자연스럽게 대화하는 연습을 할 수 있도록 도와주세요.

## 캐릭터 정보
- 이름: {avatar.get('name_ko', '아바타')}
- 역할: {avatar.get('role', 'friend')}
- 나이: {avatar.get('age', 22)}세
- 성격: {avatar.get('personality', '친근함')}
{topic_context}
{user_section}
## 말투 지침 ({formality_info['name_ko']})
{formality_info['instruction']}

예시 문장:
{chr(10).join('- ' + ex for ex in formality_info['examples'])}
{teaching_section}
{error_section}
## 대화 규칙
1. 캐릭터에 맞는 자연스러운 한국어로 대화하세요.
2. 짧고 자연스러운 대화체를 사용하세요 (1-3문장).
3. 한국 대학생 문화에 맞는 표현을 사용하세요.
4. 정치, 종교 등 민감한 주제는 피하세요.
5. 상대방이 말투를 잘못 사용해도 대화를 이어가되, 적절히 교정해주세요.
6. 너무 길게 말하지 마세요. 실제 대화처럼 짧게 주고받으세요.

{custom_instruction or ""}
"""
        return system_prompt.strip()
    
    def _build_user_context_section(self, user_context: Optional[Dict[str, Any]]) -> str:
        """Build user context section of the prompt."""
        if not user_context:
            return ""
        
        korean_level = user_context.get("korean_level", "intermediate")
        weak_skills = user_context.get("weak_skills", [])
        common_errors = user_context.get("common_errors", [])
        sessions_completed = user_context.get("sessions_completed", 0)
        average_score = user_context.get("average_score", 0)
        
        level_descriptions = {
            "beginner": "초급 - 기본 문장 구성 가능, 어휘 제한적",
            "intermediate": "중급 - 일상 대화 가능, 복잡한 문법 연습 중",
            "advanced": "고급 - 자연스러운 대화 가능, 미묘한 표현 학습 중"
        }
        
        skill_names = {
            "formal_speech": "격식체 사용",
            "polite_speech": "존댓말 사용",
            "informal_speech": "반말 사용",
            "honorifics": "높임말 사용"
        }
        
        error_names = {
            "ending_mismatch": "문장 어미 실수",
            "honorific_missing": "높임 표현 누락",
            "formality_mixed": "말투 혼용"
        }
        
        weak_skills_str = ", ".join([skill_names.get(s, s) for s in weak_skills]) if weak_skills else "없음"
        common_errors_str = ", ".join([error_names.get(e, e) for e in common_errors]) if common_errors else "없음"
        
        section = f"""
## 학습자 정보
- 한국어 수준: {level_descriptions.get(korean_level, korean_level)}
- 연습 횟수: {sessions_completed}회
- 평균 점수: {average_score:.0f}점
- 약한 부분: {weak_skills_str}
- 자주 하는 실수: {common_errors_str}
"""
        return section
    
    def _build_teaching_section(self, user_context: Optional[Dict[str, Any]]) -> str:
        """Build teaching instruction section based on user level."""
        if not user_context:
            return TEACHING_PROMPTS["intermediate"]
        
        korean_level = user_context.get("korean_level", "intermediate")
        return TEACHING_PROMPTS.get(korean_level, TEACHING_PROMPTS["intermediate"])
    
    def _build_error_correction_section(self, user_context: Optional[Dict[str, Any]]) -> str:
        """Build error correction section based on user's common errors."""
        if not user_context:
            return ""
        
        common_errors = user_context.get("common_errors", [])
        if not common_errors:
            return ""
        
        section = "\n## 이 학습자가 자주 하는 실수 교정법\n"
        for error in common_errors[:3]:  # Top 3 errors
            if error in ERROR_CORRECTION_PROMPTS:
                section += ERROR_CORRECTION_PROMPTS[error]
        
        return section
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        avatar_id: str = "sujin_friend",
        topic: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.8,
    ) -> Dict[str, Any]:
        """
        Send chat completion request to HyperCLOVA X with personalization.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            avatar_id: Avatar to use for personality
            topic: Current conversation topic
            user_context: User's learning context for personalization
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            top_p: Top-p sampling
            
        Returns:
            Dict with 'content', 'usage', and 'status'
        """
        if not self.is_configured:
            logger.warning("CLOVA API not configured, using fallback")
            return self._get_fallback_response(avatar_id)
        
        system_prompt = self.build_system_prompt(
            avatar_id=avatar_id,
            topic=topic,
            user_context=user_context
        )
        
        # Format messages for CLOVA API
        formatted_messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        for msg in messages:
            role = "user" if msg["role"] == "user" else "assistant"
            formatted_messages.append({
                "role": role,
                "content": msg["content"]
            })
        
        payload = {
            "messages": formatted_messages,
            "maxTokens": max_tokens,
            "temperature": temperature,
            "topP": top_p,
            "stopBefore": [],
            "includeAiFilters": True,
        }
        
        url = f"{self.host}{self.endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json=payload
                )
                
                if response.status_code != 200:
                    logger.error(f"CLOVA API error: {response.status_code} - {response.text}")
                    return self._get_fallback_response(avatar_id)
                
                result = response.json()
                
                # Extract response content
                if "result" in result and "message" in result["result"]:
                    content = result["result"]["message"]["content"]
                    return {
                        "content": content,
                        "usage": result.get("result", {}).get("usage", {}),
                        "status": "success"
                    }
                else:
                    return self._get_fallback_response(avatar_id)
                    
        except httpx.TimeoutException:
            logger.error("CLOVA API timeout")
            return self._get_fallback_response(avatar_id)
        except Exception as e:
            logger.error(f"CLOVA API exception: {e}")
            return self._get_fallback_response(avatar_id)
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        avatar_id: str = "sujin_friend",
        topic: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 256,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion response from HyperCLOVA X.
        
        Yields text chunks as they arrive.
        """
        if not self.is_configured:
            yield self._get_fallback_response(avatar_id)["content"]
            return
        
        system_prompt = self.build_system_prompt(
            avatar_id=avatar_id,
            topic=topic,
            user_context=user_context
        )
        
        formatted_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            role = "user" if msg["role"] == "user" else "assistant"
            formatted_messages.append({"role": role, "content": msg["content"]})
        
        payload = {
            "messages": formatted_messages,
            "maxTokens": max_tokens,
            "temperature": temperature,
            "topP": 0.8,
            "stopBefore": [],
            "includeAiFilters": True,
        }
        
        # Use streaming endpoint
        stream_endpoint = self.endpoint.replace("chat-completions", "chat-completions/stream")
        url = f"{self.host}{stream_endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    url,
                    headers=self._get_headers(),
                    json=payload
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            data = line[5:].strip()
                            if data and data != "[DONE]":
                                try:
                                    chunk = json.loads(data)
                                    if "message" in chunk and "content" in chunk["message"]:
                                        yield chunk["message"]["content"]
                                except json.JSONDecodeError:
                                    continue
        except Exception as e:
            logger.error(f"CLOVA streaming error: {e}")
            yield self._get_fallback_response(avatar_id)["content"]
    
    async def generate_avatar_response(
        self,
        user_message: str,
        avatar_id: str,
        conversation_history: List[Dict[str, str]] = None,
        topic: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate avatar response to user message with personalization.
        
        Args:
            user_message: User's input message
            avatar_id: Avatar ID for personality
            conversation_history: Previous messages
            topic: Current topic
            user_context: User's learning context
            
        Returns:
            Avatar's response text
        """
        messages = conversation_history.copy() if conversation_history else []
        messages.append({"role": "user", "content": user_message})
        
        result = await self.chat(
            messages=messages,
            avatar_id=avatar_id,
            topic=topic,
            user_context=user_context,
            max_tokens=150,
            temperature=0.8
        )
        
        return result.get("content", "네?")
    
    def _get_fallback_response(self, avatar_id: str) -> Dict[str, Any]:
        """Get fallback response when API is unavailable."""
        avatar = AVATARS.get(avatar_id, {})
        formality = avatar.get("formality", "polite")
        
        fallback_responses = {
            "informal": [
                "응? 뭐라고?",
                "아 그래? 재밌다!",
                "헐 진짜? 대박",
                "ㅋㅋㅋ 뭐야",
                "아 그렇구나~"
            ],
            "polite": [
                "아 네, 그렇군요!",
                "정말요? 재밌네요.",
                "아~ 그렇구나요.",
                "네네, 알겠어요!",
                "오 그래요?"
            ],
            "very_polite": [
                "네, 알겠습니다.",
                "아, 그렇습니까?",
                "말씀 감사합니다.",
                "네, 이해했습니다.",
                "좋은 말씀이십니다."
            ]
        }
        
        import random
        responses = fallback_responses.get(formality, fallback_responses["polite"])
        
        return {
            "content": random.choice(responses),
            "status": "fallback",
            "usage": {}
        }
    
    def get_system_prompt_preview(
        self,
        avatar_id: str,
        topic: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get a preview of the system prompt (for debugging/testing).
        
        Returns the full system prompt that would be sent to CLOVA.
        """
        return self.build_system_prompt(
            avatar_id=avatar_id,
            topic=topic,
            user_context=user_context
        )


# Singleton instance
enhanced_clova_service = EnhancedClovaService()


# For backward compatibility
clova_service = enhanced_clova_service
