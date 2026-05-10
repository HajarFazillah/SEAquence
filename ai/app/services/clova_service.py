"""
CLOVA Service - HyperCLOVA X API Integration

Uses Bearer token authentication with v3 API.
"""

import httpx
import json
import re
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
        self.api_key    = settings.NAVER_CLOVA_API_KEY
        self.host       = settings.NAVER_CLOVA_HOST
        self.endpoint   = settings.NAVER_CLOVA_CHAT_ENDPOINT
        self.request_id = settings.NAVER_CLOVA_REQUEST_ID

        self.base_url = f"{self.host}{self.endpoint}"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-NCP-CLOVASTUDIO-REQUEST-ID": self.request_id,
        }

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.host and self.endpoint)

    async def chat(
        self,
        messages:    List[Message],
        max_tokens:  int   = 1024,
        temperature: float = 0.7,
        top_p:       float = 0.8,
    ) -> CLOVAResponse:
        """Send chat completion request to HyperCLOVA X v3."""

        if not self.is_configured:
            print("[CLOVA] ⚠️  API not configured — using mock response")
            return await self._mock_response(messages)

        payload = {
            "messages":    [m.dict() for m in messages],
            "maxTokens":   max_tokens,
            "temperature": temperature,
            "topP":        top_p,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                )

                if response.status_code != 200:
                    print(f"[CLOVA] ❌ HTTP {response.status_code}: {response.text}")
                    return await self._mock_response(messages)

                data = response.json()

                if data.get("status", {}).get("code") != "20000":
                    print(f"[CLOVA] ❌ API error: {data.get('status')}")
                    return await self._mock_response(messages)

                # ── v3 응답 파싱 ──────────────────────────────────────────
                result  = data.get("result", {})
                message = result.get("message", {})
                content = message.get("content", "")
                usage   = result.get("usage", {})

                print(f"[CLOVA] ✅ OK — tokens: {usage.get('totalTokens', 0)}")

                return CLOVAResponse(
                    content=content,
                    finish_reason=result.get("finishReason"),
                    usage={
                        "input_tokens":  usage.get("promptTokens",    0),
                        "output_tokens": usage.get("completionTokens", 0),
                        "total_tokens":  usage.get("totalTokens",      0),
                    }
                )

        except httpx.TimeoutException:
            print("[CLOVA] ❌ Timeout — 30초 초과")
            return await self._mock_response(messages)

        except Exception as e:
            print(f"[CLOVA] ❌ Unexpected error: {e}")
            return await self._mock_response(messages)

    async def _mock_response(self, messages: List[Message]) -> CLOVAResponse:
        """Generate mock response when API is not available"""
        import random
        mock_responses = [
            "네, 좋아요! 더 이야기해 주세요.",
            "아, 그렇군요. 흥미롭네요!",
            "정말요? 더 자세히 말씀해 주세요.",
        ]
        print("[CLOVA] ⚠️  Using mock response")
        return CLOVAResponse(
            content=random.choice(mock_responses),
            finish_reason="mock",
            usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        )

    async def generate_with_system_prompt(
        self,
        system_prompt:        str,
        user_message:         str,
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
        """Generate a JSON response and return it parsed.

        Always returns a dict for backwards compatibility — if the model emits
        a JSON array, callers wouldn't have known how to handle it before, so
        we still surface arrays as `{"items": [...]}` only when explicitly
        opted in. Parsing/sanitization is delegated to the shared
        `sanitize_json_like_model_output` so all JSON-handling code in the
        codebase uses the same rules.
        """
        # Local import to avoid any chance of circular import at module load.
        from app.services.korean_coaching_prompt_builder import (
            sanitize_json_like_model_output,
        )

        response = await self.chat(
            [Message(role="user", content=prompt)], **kwargs
        )

        if response.finish_reason == "mock":
            print("[CLOVA] analyze_json received mock — returning empty dict")
            return {}

        parsed = sanitize_json_like_model_output(response.content)
        if parsed is None:
            print(f"[CLOVA] No usable JSON in response: {response.content[:300]}")
            return {}
        if isinstance(parsed, list):
            # Caller expected a dict; surface array under a stable key.
            return {"items": parsed}
        return parsed


clova_service = CLOVAService()