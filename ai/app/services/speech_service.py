"""
CLOVA Speech & Voice Services
STT (Speech-to-Text) and TTS (Text-to-Speech) integration
"""

import httpx
import logging
from typing import Optional, Dict, Any
import base64

from app.core.config import settings
from app.core.constants import AVATARS

logger = logging.getLogger(__name__)


class SpeechService:
    """
    CLOVA Speech (STT) Service.
    Converts audio to text.
    """
    
    def __init__(self):
        self.client_id = settings.NAVER_SPEECH_CLIENT_ID
        self.client_secret = settings.NAVER_SPEECH_CLIENT_SECRET
        self.url = settings.NAVER_SPEECH_URL
    
    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)
    
    def _get_headers(self, content_type: str = "application/octet-stream") -> Dict[str, str]:
        return {
            "X-NCP-APIGW-API-KEY-ID": self.client_id,
            "X-NCP-APIGW-API-KEY": self.client_secret,
            "Content-Type": content_type,
        }
    
    async def recognize(
        self,
        audio_data: bytes,
        language: str = "Kor"
    ) -> Dict[str, Any]:
        """
        Convert audio to text using CLOVA Speech.
        
        Args:
            audio_data: Audio file bytes (MP3, WAV, etc.)
            language: Language code ("Kor", "Eng", "Jpn", "Chn")
            
        Returns:
            Dict with 'text' and 'status'
        """
        if not self.is_configured:
            return {"text": None, "error": "Speech API not configured", "status": "error"}
        
        url = f"{self.url}?lang={language}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    content=audio_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "text": result.get("text", ""),
                        "status": "success"
                    }
                else:
                    logger.error(f"Speech API error: {response.status_code}")
                    return {
                        "text": None,
                        "error": f"API error: {response.status_code}",
                        "status": "error"
                    }
                    
        except Exception as e:
            logger.error(f"Speech API exception: {e}")
            return {"text": None, "error": str(e), "status": "error"}


class VoiceService:
    """
    CLOVA Voice (TTS) Service.
    Converts text to speech audio.
    """
    
    # Available voice IDs
    VOICES = {
        # Female voices
        "mijin": "여성, 차분한 낭독체",
        "jinho": "남성, 차분한 낭독체",
        "nara": "여성, 차분한 또박또박",
        "nhajun": "아동 남성",
        "ndain": "아동 여성",
        "nsujin": "여성, 밝은 어조",
        "njiyun": "여성, 아나운서체",
        "nara_call": "여성, 고객센터",
        "nminsang": "남성, 밝은 어조",
        "nmeow": "고양이체 (재미용)",
        # Emotional voices (Premium)
        "vara": "여성, 감정 조절 가능",
        "vmikyung": "여성, 중년",
        "vdaeseong": "남성, 중년",
        "nwontak": "남성, 젊은 어조",
        "nseonghoon": "남성, 차분한",
        "njooahn": "여성, 부드러운",
        "nsabina": "영어 여성",
    }
    
    def __init__(self):
        self.client_id = settings.NAVER_VOICE_CLIENT_ID
        self.client_secret = settings.NAVER_VOICE_CLIENT_SECRET
        self.url = settings.NAVER_VOICE_URL
    
    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "X-NCP-APIGW-API-KEY-ID": self.client_id,
            "X-NCP-APIGW-API-KEY": self.client_secret,
            "Content-Type": "application/x-www-form-urlencoded",
        }
    
    async def synthesize(
        self,
        text: str,
        speaker: str = "nara",
        speed: int = 0,
        pitch: int = 0,
        volume: int = 0,
        emotion: Optional[int] = None,
        emotion_strength: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Convert text to speech audio using CLOVA Voice.
        
        Args:
            text: Text to synthesize (max 5000 chars)
            speaker: Voice ID (see VOICES dict)
            speed: Speech speed (-5 to 5, default 0)
            pitch: Voice pitch (-5 to 5, default 0)
            volume: Volume (-5 to 5, default 0)
            emotion: Emotion type for vara voice (0: neutral, 1: happy, 2: sad, 3: angry)
            emotion_strength: Emotion strength (0-3)
            
        Returns:
            Dict with 'audio' (base64), 'format', and 'status'
        """
        if not self.is_configured:
            return {"audio": None, "error": "Voice API not configured", "status": "error"}
        
        if len(text) > 5000:
            text = text[:5000]
        
        data = {
            "speaker": speaker,
            "text": text,
            "speed": str(speed),
            "pitch": str(pitch),
            "volume": str(volume),
            "format": "mp3",
        }
        
        # Emotional voice settings (for vara)
        if emotion is not None and speaker.startswith("v"):
            data["emotion"] = str(emotion)
            if emotion_strength is not None:
                data["emotion-strength"] = str(emotion_strength)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.url,
                    headers=self._get_headers(),
                    data=data
                )
                
                if response.status_code == 200:
                    audio_base64 = base64.b64encode(response.content).decode("utf-8")
                    return {
                        "audio": audio_base64,
                        "format": "mp3",
                        "status": "success"
                    }
                else:
                    error_msg = response.text
                    logger.error(f"Voice API error: {response.status_code} - {error_msg}")
                    return {
                        "audio": None,
                        "error": f"API error: {response.status_code}",
                        "status": "error"
                    }
                    
        except Exception as e:
            logger.error(f"Voice API exception: {e}")
            return {"audio": None, "error": str(e), "status": "error"}
    
    async def synthesize_for_avatar(
        self,
        text: str,
        avatar_id: str
    ) -> Dict[str, Any]:
        """
        Synthesize speech using avatar's configured voice.
        
        Args:
            text: Text to synthesize
            avatar_id: Avatar identifier
            
        Returns:
            Dict with 'audio', 'format', 'status'
        """
        avatar = AVATARS.get(avatar_id)
        if not avatar:
            avatar = AVATARS["sujin_friend"]
        
        voice_id = avatar.get("voice_id", "nara")
        
        # Adjust speed/pitch based on avatar personality
        speed = 0
        pitch = 0
        
        if avatar["role"] == "professor":
            speed = -1  # Slightly slower
            pitch = -1  # Lower pitch
        elif avatar["role"] == "friend":
            speed = 1   # Slightly faster
            pitch = 1   # Higher pitch
        
        return await self.synthesize(
            text=text,
            speaker=voice_id,
            speed=speed,
            pitch=pitch
        )


# Singleton instances
speech_service = SpeechService()
voice_service = VoiceService()
