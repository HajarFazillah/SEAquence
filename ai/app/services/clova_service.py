"""
HyperCLOVA X Service
Naver Cloud Platform LLM integration for conversation generation
"""

import httpx
import json
import logging
from typing import Optional, List, Dict, Any, AsyncGenerator

from app.core.config import settings
from app.core.constants import (
    AVATARS, FORMALITY_INSTRUCTIONS, TOPIC_TAXONOMY,
    get_formality_instruction
)

logger = logging.getLogger(__name__)


class ClovaService:
    """
    Service for interacting with Naver HyperCLOVA X API.
    
    Supports:
    - Chat completion (streaming and non-streaming)
    - Avatar-based conversation with appropriate formality
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
    
    def _build_system_prompt(
        self,
        avatar_id: str,
        topic: Optional[str] = None,
        custom_instruction: Optional[str] = None
    ) -> str:
        """
        Build system prompt for avatar conversation.
        
        Args:
            avatar_id: Avatar identifier
            topic: Current conversation topic
            custom_instruction: Additional instructions
        """
        avatar = AVATARS.get(avatar_id)
        if not avatar:
            avatar = AVATARS["sujin_friend"]  # Default
        
        formality = avatar["formality"]
        formality_inst = get_formality_instruction(formality)
        
        topic_context = ""
        if topic and topic in TOPIC_TAXONOMY:
            topic_info = TOPIC_TAXONOMY[topic]
            topic_context = f"\n현재 대화 주제: {topic_info['name_ko']} ({topic_info['description']})"
        
        system_prompt = f"""당신은 한국어 대화 연습을 도와주는 AI 아바타입니다.

## 캐릭터 정보
- 이름: {avatar['name_ko']}
- 역할: {avatar['role']}
- 나이: {avatar['age']}세
- 성격: {avatar['personality']}
{topic_context}

## 말투 지침
{formality_inst}

## 대화 규칙
1. 캐릭터에 맞는 자연스러운 한국어로 대화하세요.
2. 짧고 자연스러운 대화체를 사용하세요 (1-3문장).
3. 한국 대학생 문화에 맞는 표현을 사용하세요.
4. 정치, 종교 등 민감한 주제는 피하세요.
5. 상대방의 말투 수준에 맞춰 자연스럽게 반응하세요.

{custom_instruction or ""}
"""
        return system_prompt.strip()
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        avatar_id: str = "sujin_friend",
        topic: Optional[str] = None,
        max_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.8,
    ) -> Dict[str, Any]:
        """
        Send chat completion request to HyperCLOVA X.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            avatar_id: Avatar to use for personality
            topic: Current conversation topic
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            top_p: Top-p sampling
            
        Returns:
            Dict with 'content', 'usage', and 'status'
        """
        if not self.is_configured:
            raise ValueError("CLOVA API not configured. Check environment variables.")
        
        system_prompt = self._build_system_prompt(avatar_id, topic)
        
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
                    return {
                        "content": None,
                        "error": f"API error: {response.status_code}",
                        "status": "error"
                    }
                
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
                    return {
                        "content": None,
                        "error": "Unexpected response format",
                        "status": "error"
                    }
                    
        except httpx.TimeoutException:
            logger.error("CLOVA API timeout")
            return {"content": None, "error": "Request timeout", "status": "error"}
        except Exception as e:
            logger.error(f"CLOVA API exception: {e}")
            return {"content": None, "error": str(e), "status": "error"}
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        avatar_id: str = "sujin_friend",
        topic: Optional[str] = None,
        max_tokens: int = 256,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion response from HyperCLOVA X.
        
        Yields text chunks as they arrive.
        """
        if not self.is_configured:
            raise ValueError("CLOVA API not configured")
        
        system_prompt = self._build_system_prompt(avatar_id, topic)
        
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
            yield f"[Error: {str(e)}]"
    
    async def generate_avatar_response(
        self,
        user_message: str,
        avatar_id: str,
        conversation_history: List[Dict[str, str]] = None,
        topic: Optional[str] = None,
    ) -> str:
        """
        Generate avatar response to user message.
        
        Args:
            user_message: User's input message
            avatar_id: Avatar ID for personality
            conversation_history: Previous messages
            topic: Current topic
            
        Returns:
            Avatar's response text
        """
        messages = conversation_history or []
        messages.append({"role": "user", "content": user_message})
        
        result = await self.chat(
            messages=messages,
            avatar_id=avatar_id,
            topic=topic,
            max_tokens=150,
            temperature=0.8
        )
        
        if result["status"] == "success" and result["content"]:
            return result["content"]
        else:
            # Fallback response
            avatar = AVATARS.get(avatar_id, AVATARS["sujin_friend"])
            fallback_responses = {
                "informal": "응? 뭐라고? 다시 말해줘!",
                "polite": "죄송해요, 잘 못 들었어요. 다시 말씀해 주시겠어요?",
                "very_polite": "죄송합니다, 잘 이해하지 못했습니다. 다시 말씀해 주시겠습니까?",
            }
            return fallback_responses.get(avatar["formality"], "네?")


# Singleton instance
clova_service = ClovaService()
