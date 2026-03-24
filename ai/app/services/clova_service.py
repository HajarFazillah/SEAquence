"""
CLOVA Service - HyperCLOVA X API Integration

Uses Bearer token authentication with v3 API.
"""

import httpx
import json
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.core.config import settings


class Message(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str


class CLOVAResponse(BaseModel):
    content: str
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None


class CLOVAService:
    """Service for interacting with HyperCLOVA X API"""
    
    def __init__(self):
        self.api_key = settings.NAVER_CLOVA_API_KEY
        self.host = settings.NAVER_CLOVA_HOST
        self.endpoint = settings.NAVER_CLOVA_CHAT_ENDPOINT
        self.request_id = settings.NAVER_CLOVA_REQUEST_ID
        
        self.base_url = f"{self.host}{self.endpoint}"
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-NCP-CLOVASTUDIO-REQUEST-ID": self.request_id,
        }
    
    @property
    def is_configured(self) -> bool:
        """Check if CLOVA API is properly configured"""
        return bool(self.api_key and self.host and self.endpoint)
    
    async def chat(
        self,
        messages: List[Message],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.8,
    ) -> CLOVAResponse:
        """Send chat completion request to HyperCLOVA X."""
        if not self.is_configured:
            return await self._mock_response(messages)
        
        payload = {
            "messages": [m.dict() for m in messages],
            "maxTokens": max_tokens,
            "temperature": temperature,
            "topP": top_p,
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                )
                response.raise_for_status()
                
                data = response.json()
                result = data.get("result", {})
                message = result.get("message", {})
                content = message.get("content", "")
                
                return CLOVAResponse(
                    content=content,
                    finish_reason=result.get("stopReason"),
                    usage={
                        "input_tokens": result.get("inputLength", 0),
                        "output_tokens": result.get("outputLength", 0),
                    }
                )
        
        except Exception as e:
            print(f"CLOVA API error: {e}")
            return await self._mock_response(messages)
    
    async def _mock_response(self, messages: List[Message]) -> CLOVAResponse:
        """Generate mock response when API is not available"""
        import random
        mock_responses = [
            "네, 좋아요! 더 이야기해 주세요.",
            "아, 그렇군요. 흥미롭네요!",
            "정말요? 더 자세히 말씀해 주세요.",
        ]
        return CLOVAResponse(
            content=random.choice(mock_responses),
            finish_reason="mock",
            usage={"input_tokens": 0, "output_tokens": 0}
        )
    
    async def generate_with_system_prompt(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Message]] = None,
        **kwargs
    ) -> CLOVAResponse:
        """Generate response with system prompt and conversation history."""
        messages = [Message(role="system", content=system_prompt)]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append(Message(role="user", content=user_message))
        return await self.chat(messages, **kwargs)
    
    async def analyze_json(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate JSON response and parse it."""
        response = await self.chat([Message(role="user", content=prompt)], **kwargs)
        try:
            content = response.content.strip()
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            return json.loads(content)
        except json.JSONDecodeError:
            return {}


clova_service = CLOVAService()
