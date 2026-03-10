"""
Revision & Sample Reply Service
Uses HyperCLOVA X to correct user's Korean and provide sample replies
"""

import httpx
import json
import logging
from typing import Optional, List, Dict, Any

from app.core.config import settings
from app.core.constants import AVATARS, TOPIC_TAXONOMY

logger = logging.getLogger(__name__)


class RevisionService:
    """
    Service for revising user's Korean sentences and generating sample replies.
    
    Features:
    - Correct grammar and formality errors
    - Provide properly formatted sample replies
    - Explain what was wrong and why
    - Suggest alternative expressions
    """
    
    def __init__(self):
        self.host = settings.NAVER_CLOVA_HOST
        self.endpoint = settings.NAVER_CLOVA_CHAT_ENDPOINT
        self.api_key = settings.NAVER_CLOVA_API_KEY
        self.api_key_primary = settings.NAVER_CLOVA_API_KEY_PRIMARY
        self.request_id = settings.NAVER_CLOVA_REQUEST_ID
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key_primary)
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "X-NCP-CLOVASTUDIO-API-KEY": self.api_key,
            "X-NCP-APIGW-API-KEY": self.api_key_primary,
            "X-NCP-CLOVASTUDIO-REQUEST-ID": self.request_id or "",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    
    async def revise_and_sample(
        self,
        user_sentence: str,
        target_role: str = "senior",
        target_formality: str = "polite",
        context: Optional[str] = None,
        user_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Revise user's sentence and provide sample reply.
        
        Args:
            user_sentence: User's original Korean sentence
            target_role: Who user is talking to (friend, senior, professor, boss)
            target_formality: Expected formality (informal, polite, very_polite)
            context: Conversation context (optional)
            user_level: User's Korean level for explanation complexity
            
        Returns:
            Dict with revision, sample_reply, explanation, alternatives
        """
        system_prompt = self._build_revision_prompt(
            target_role=target_role,
            target_formality=target_formality,
            context=context,
            user_level=user_level
        )
        
        user_prompt = f"""다음 문장을 분석하고 교정해주세요:

원문: "{user_sentence}"

JSON 형식으로 응답해주세요:
{{
  "original": "원문",
  "has_error": true/false,
  "revised": "교정된 문장",
  "sample_replies": ["예시 답변 1", "예시 답변 2"],
  "errors": [
    {{
      "type": "오류 유형",
      "original_part": "잘못된 부분",
      "corrected_part": "교정된 부분",
      "explanation_ko": "한국어 설명",
      "explanation_en": "English explanation"
    }}
  ],
  "alternatives": ["대안 표현 1", "대안 표현 2"],
  "tips": ["팁 1", "팁 2"],
  "formality_score": 0-100
}}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        if not self.is_configured:
            return self._get_fallback_revision(user_sentence, target_formality)
        
        try:
            result = await self._call_api(messages)
            
            if result.get("status") == "success":
                content = result.get("content", "")
                parsed = self._parse_json_response(content)
                if parsed:
                    return parsed
            
            return self._get_fallback_revision(user_sentence, target_formality)
            
        except Exception as e:
            logger.error(f"Revision API error: {e}")
            return self._get_fallback_revision(user_sentence, target_formality)
    
    async def get_sample_reply(
        self,
        situation: str,
        target_role: str = "senior",
        target_formality: str = "polite",
        num_samples: int = 3
    ) -> Dict[str, Any]:
        """
        Generate sample Korean replies for a given situation.
        
        Args:
            situation: What user wants to say (in any language)
            target_role: Who user is talking to
            target_formality: Expected formality level
            num_samples: Number of sample replies to generate
            
        Returns:
            Dict with sample replies at different formality levels
        """
        system_prompt = """당신은 한국어 교육 전문가입니다.
주어진 상황에 맞는 자연스러운 한국어 표현을 제공해주세요.

각 표현에 대해:
1. 실제 한국인이 사용하는 자연스러운 표현
2. 상황과 관계에 맞는 적절한 격식
3. 다양한 표현 방법 제시

JSON 형식으로 응답해주세요."""

        user_prompt = f"""상황: {situation}
대화 상대: {target_role}
필요한 격식: {target_formality}
예시 개수: {num_samples}

JSON 형식으로 응답:
{{
  "situation": "상황 설명",
  "target_role": "대화 상대",
  "recommended_formality": "권장 격식",
  "samples": [
    {{
      "korean": "한국어 표현",
      "formality": "격식 수준",
      "romanization": "로마자 표기",
      "literal_meaning": "직역",
      "usage_note": "사용 팁"
    }}
  ],
  "common_mistakes": ["흔한 실수 1", "흔한 실수 2"],
  "cultural_note": "문화적 팁"
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        if not self.is_configured:
            return self._get_fallback_samples(situation, target_formality)
        
        try:
            result = await self._call_api(messages, max_tokens=500)
            
            if result.get("status") == "success":
                content = result.get("content", "")
                parsed = self._parse_json_response(content)
                if parsed:
                    return parsed
            
            return self._get_fallback_samples(situation, target_formality)
            
        except Exception as e:
            logger.error(f"Sample reply API error: {e}")
            return self._get_fallback_samples(situation, target_formality)
    
    async def explain_difference(
        self,
        sentence1: str,
        sentence2: str
    ) -> Dict[str, Any]:
        """
        Explain the difference between two Korean sentences.
        
        Useful for showing why one form is better than another.
        """
        system_prompt = """당신은 한국어 교육 전문가입니다.
두 문장의 차이점을 명확하게 설명해주세요.

분석 항목:
1. 격식 수준 차이
2. 뉘앙스 차이
3. 어떤 상황에서 각각 사용하는지
4. 문법적 차이점

JSON 형식으로 응답해주세요."""

        user_prompt = f"""다음 두 문장의 차이를 설명해주세요:

문장 1: "{sentence1}"
문장 2: "{sentence2}"

JSON 형식:
{{
  "sentence1": {{
    "text": "문장 1",
    "formality": "격식 수준",
    "appropriate_for": ["적절한 상대"],
    "nuance": "뉘앙스 설명"
  }},
  "sentence2": {{
    "text": "문장 2",
    "formality": "격식 수준",
    "appropriate_for": ["적절한 상대"],
    "nuance": "뉘앙스 설명"
  }},
  "differences": [
    {{
      "aspect": "차이점 유형",
      "explanation_ko": "한국어 설명",
      "explanation_en": "English explanation"
    }}
  ],
  "recommendation": "어떤 상황에서 어떤 문장을 쓰라는 추천"
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        if not self.is_configured:
            return {
                "sentence1": {"text": sentence1, "formality": "unknown"},
                "sentence2": {"text": sentence2, "formality": "unknown"},
                "differences": [],
                "recommendation": "API not configured"
            }
        
        try:
            result = await self._call_api(messages, max_tokens=500)
            
            if result.get("status") == "success":
                content = result.get("content", "")
                parsed = self._parse_json_response(content)
                if parsed:
                    return parsed
            
            return {
                "sentence1": {"text": sentence1},
                "sentence2": {"text": sentence2},
                "differences": [],
                "error": "Could not parse response"
            }
            
        except Exception as e:
            logger.error(f"Explain difference API error: {e}")
            return {"error": str(e)}
    
    def _build_revision_prompt(
        self,
        target_role: str,
        target_formality: str,
        context: Optional[str],
        user_level: str
    ) -> str:
        """Build system prompt for revision."""
        
        formality_guide = {
            "informal": {
                "name": "반말",
                "endings": "~어/아, ~지, ~냐, ~야",
                "example": "뭐해?, 밥 먹었어?"
            },
            "polite": {
                "name": "존댓말 (-요)",
                "endings": "~요, ~세요, ~죠",
                "example": "뭐 해요?, 밥 먹었어요?"
            },
            "very_polite": {
                "name": "격식체 (-습니다)",
                "endings": "~습니다, ~습니까, ~십시오",
                "example": "무엇을 하십니까?, 식사하셨습니까?"
            }
        }
        
        level_instructions = {
            "beginner": "쉬운 단어로 간단하게 설명해주세요.",
            "intermediate": "문법 용어를 사용해서 설명해주세요.",
            "advanced": "미묘한 뉘앙스 차이까지 설명해주세요."
        }
        
        guide = formality_guide.get(target_formality, formality_guide["polite"])
        level_inst = level_instructions.get(user_level, level_instructions["intermediate"])
        
        context_str = f"\n상황: {context}" if context else ""
        
        return f"""당신은 한국어 교정 및 교육 전문가입니다.

## 교정 기준
- 대화 상대: {target_role}
- 필요한 격식: {guide['name']}
- 올바른 어미: {guide['endings']}
- 예시: {guide['example']}
{context_str}

## 교정 방침
1. 문법 오류를 찾아 교정합니다.
2. 격식 수준이 맞지 않으면 교정합니다.
3. 자연스럽지 않은 표현을 교정합니다.
4. 높임말이 필요한데 빠졌으면 추가합니다.

## 설명 수준
{level_inst}

## 응답 형식
반드시 유효한 JSON으로 응답하세요. 추가 텍스트 없이 JSON만 출력하세요."""
    
    async def _call_api(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 400
    ) -> Dict[str, Any]:
        """Call HyperCLOVA X API."""
        payload = {
            "messages": messages,
            "maxTokens": max_tokens,
            "temperature": 0.3,  # Lower for more consistent corrections
            "topP": 0.8,
            "stopBefore": [],
            "includeAiFilters": True,
        }
        
        url = f"{self.host}{self.endpoint}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"API error: {response.status_code}")
                return {"status": "error", "error": response.text}
            
            result = response.json()
            
            if "result" in result and "message" in result["result"]:
                return {
                    "status": "success",
                    "content": result["result"]["message"]["content"]
                }
            
            return {"status": "error", "error": "Unexpected format"}
    
    def _parse_json_response(self, content: str) -> Optional[Dict]:
        """Parse JSON from LLM response."""
        try:
            # Try direct parsing
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code block
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object in text
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        logger.warning(f"Could not parse JSON from: {content[:200]}")
        return None
    
    def _get_fallback_revision(
        self,
        user_sentence: str,
        target_formality: str
    ) -> Dict[str, Any]:
        """Fallback revision when API is unavailable."""
        
        # Simple rule-based corrections
        revised = user_sentence
        errors = []
        
        # Check for common issues
        if target_formality == "very_polite":
            # Should end with -습니다/-습니까
            if user_sentence.endswith("요") or user_sentence.endswith("요?"):
                revised = user_sentence.replace("어요", "습니다").replace("아요", "습니다")
                revised = revised.replace("해요", "합니다").replace("요?", "습니까?")
                errors.append({
                    "type": "ending_mismatch",
                    "original_part": "~요",
                    "corrected_part": "~습니다/습니까",
                    "explanation_ko": "교수님/상사에게는 격식체(-습니다)를 사용하세요.",
                    "explanation_en": "Use formal speech (-습니다) with professors/bosses."
                })
        
        elif target_formality == "polite":
            # Should end with -요
            informal_endings = ["어", "아", "지", "냐", "야"]
            for ending in informal_endings:
                if user_sentence.endswith(ending):
                    revised = user_sentence + "요"
                    errors.append({
                        "type": "ending_mismatch",
                        "original_part": f"~{ending}",
                        "corrected_part": f"~{ending}요",
                        "explanation_ko": "선배/처음 만난 사람에게는 존댓말(-요)을 사용하세요.",
                        "explanation_en": "Use polite speech (-요) with seniors/strangers."
                    })
                    break
        
        sample_replies = {
            "informal": ["응, 알았어!", "그래, 좋아~", "어, 그렇구나"],
            "polite": ["네, 알겠어요!", "그렇군요~", "아, 그래요?"],
            "very_polite": ["네, 알겠습니다.", "그렇습니까?", "감사합니다."]
        }
        
        return {
            "original": user_sentence,
            "has_error": len(errors) > 0,
            "revised": revised,
            "sample_replies": sample_replies.get(target_formality, sample_replies["polite"]),
            "errors": errors,
            "alternatives": [],
            "tips": ["API가 연결되면 더 정확한 교정을 받을 수 있습니다."],
            "formality_score": 50 if errors else 85,
            "status": "fallback"
        }
    
    def _get_fallback_samples(
        self,
        situation: str,
        target_formality: str
    ) -> Dict[str, Any]:
        """Fallback sample replies when API is unavailable."""
        
        samples_by_formality = {
            "informal": [
                {"korean": "야, 고마워!", "formality": "informal", "usage_note": "친한 친구에게"},
                {"korean": "응, 알았어~", "formality": "informal", "usage_note": "동기/후배에게"},
            ],
            "polite": [
                {"korean": "감사해요!", "formality": "polite", "usage_note": "선배/일반적 상황"},
                {"korean": "네, 알겠어요.", "formality": "polite", "usage_note": "정중한 대화"},
            ],
            "very_polite": [
                {"korean": "감사합니다.", "formality": "very_polite", "usage_note": "교수님/상사"},
                {"korean": "알겠습니다.", "formality": "very_polite", "usage_note": "공식적 상황"},
            ]
        }
        
        return {
            "situation": situation,
            "recommended_formality": target_formality,
            "samples": samples_by_formality.get(target_formality, samples_by_formality["polite"]),
            "common_mistakes": ["격식 수준 혼용", "어미 실수"],
            "cultural_note": "한국에서는 상대방과의 관계에 따라 말투가 달라집니다.",
            "status": "fallback"
        }


# Singleton instance
revision_service = RevisionService()
