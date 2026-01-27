"""
Configuration management for Talkativ AI
Loads settings from environment variables
"""

from typing import Optional, List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # App Settings
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    
    # ===========================================
    # Naver Cloud Platform - HyperCLOVA X
    # ===========================================
    NAVER_CLOVA_API_KEY: Optional[str] = None
    NAVER_CLOVA_API_KEY_PRIMARY: Optional[str] = None
    NAVER_CLOVA_REQUEST_ID: Optional[str] = None
    NAVER_CLOVA_HOST: str = "https://clovastudio.stream.ntruss.com"
    NAVER_CLOVA_CHAT_ENDPOINT: str = "/testapp/v1/chat-completions/HCX-003"
    
    # ===========================================
    # Naver Cloud Platform - CLOVA Speech (STT)
    # ===========================================
    NAVER_SPEECH_CLIENT_ID: Optional[str] = None
    NAVER_SPEECH_CLIENT_SECRET: Optional[str] = None
    NAVER_SPEECH_URL: str = "https://naveropenapi.apigw.ntruss.com/recog/v1/stt"
    
    # ===========================================
    # Naver Cloud Platform - CLOVA Voice (TTS)
    # ===========================================
    NAVER_VOICE_CLIENT_ID: Optional[str] = None
    NAVER_VOICE_CLIENT_SECRET: Optional[str] = None
    NAVER_VOICE_URL: str = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"
    
    # ===========================================
    # OpenAI (Fallback)
    # ===========================================
    OPENAI_API_KEY: Optional[str] = None
    
    # ===========================================
    # Redis
    # ===========================================
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # ===========================================
    # Model Settings
    # ===========================================
    EMBEDDING_MODEL: str = "jhgan/ko-sroberta-multitask"
    MODEL_DIR: str = "./models"
    
    # ===========================================
    # Properties
    # ===========================================
    
    @property
    def clova_chat_url(self) -> str:
        """Full URL for HyperCLOVA X chat completion."""
        return f"{self.NAVER_CLOVA_HOST}{self.NAVER_CLOVA_CHAT_ENDPOINT}"
    
    @property
    def has_clova(self) -> bool:
        """Check if CLOVA credentials are configured."""
        return bool(self.NAVER_CLOVA_API_KEY and self.NAVER_CLOVA_API_KEY_PRIMARY)
    
    @property
    def has_openai(self) -> bool:
        """Check if OpenAI is configured."""
        return bool(self.OPENAI_API_KEY)
    
    @property
    def has_speech(self) -> bool:
        """Check if CLOVA Speech is configured."""
        return bool(self.NAVER_SPEECH_CLIENT_ID and self.NAVER_SPEECH_CLIENT_SECRET)
    
    @property
    def has_voice(self) -> bool:
        """Check if CLOVA Voice is configured."""
        return bool(self.NAVER_VOICE_CLIENT_ID and self.NAVER_VOICE_CLIENT_SECRET)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
