"""
Configuration settings for AI server
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # CLOVA Studio (LLM)
    NAVER_CLOVA_API_KEY: Optional[str] = None
    NAVER_CLOVA_API_KEY_PRIMARY: Optional[str] = None   # alias used by revision_service
    NAVER_CLOVA_HOST: str = "https://clovastudio.stream.ntruss.com"
    NAVER_CLOVA_CHAT_ENDPOINT: str = "/v3/chat-completions/HCX-DASH-002"
    NAVER_CLOVA_REQUEST_ID: Optional[str] = None

    # CLOVA Speech (STT)
    NAVER_SPEECH_CLIENT_ID: Optional[str] = None
    NAVER_SPEECH_CLIENT_SECRET: Optional[str] = None
    NAVER_SPEECH_URL: str = "https://naveropenapi.apigw.ntruss.com/recog/v1/stt"

    # CLOVA Voice (TTS)
    NAVER_VOICE_CLIENT_ID: Optional[str] = None
    NAVER_VOICE_CLIENT_SECRET: Optional[str] = None
    NAVER_VOICE_URL: str = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"

    # Server
    DEBUG: bool = False

    def model_post_init(self, __context):
        """If PRIMARY key not set, fall back to main key."""
        if not self.NAVER_CLOVA_API_KEY_PRIMARY and self.NAVER_CLOVA_API_KEY:
            object.__setattr__(self, 'NAVER_CLOVA_API_KEY_PRIMARY', self.NAVER_CLOVA_API_KEY)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
