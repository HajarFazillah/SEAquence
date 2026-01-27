"""
API Schemas
Pydantic models for request/response validation
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ===========================================
# Topic Schemas
# ===========================================

class TopicDetectRequest(BaseModel):
    """Request to detect topics from text."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to analyze")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of topics to return")
    include_sensitive: bool = Field(default=False, description="Include sensitive topics")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "text": "오늘 중간고사 때문에 도서관에서 공부했어요",
                "top_k": 3
            }]
        }
    }


class TopicResult(BaseModel):
    """Single topic detection result."""
    topic_id: str
    topic_name_ko: str
    topic_name_en: str
    confidence: float = Field(ge=0, le=1)
    is_sensitive: bool
    match_count: int = 0


class TopicDetectResponse(BaseModel):
    """Response for topic detection."""
    topics: List[TopicResult]


class TopicRecommendRequest(BaseModel):
    """Request for topic recommendations."""
    user_topics: List[str] = Field(default=[], description="User's preferred topics")
    avatar_topics: List[str] = Field(default=[], description="Avatar's topics")
    context: Optional[str] = Field(default=None, description="Context text")
    top_k: int = Field(default=5, ge=1, le=10)


class TopicRecommendResponse(BaseModel):
    """Response for topic recommendations."""
    recommended_topics: List[Dict[str, Any]]
    common_topics: List[str]
    context_detected: List[str]


# ===========================================
# Politeness Schemas
# ===========================================

class PolitenessAnalyzeRequest(BaseModel):
    """Request for politeness analysis."""
    text: str = Field(..., min_length=1, max_length=5000)
    target_role: Optional[str] = Field(default=None, description="Target person's role")
    target_age: Optional[int] = Field(default=None, ge=1, le=100)
    user_age: int = Field(default=22, ge=1, le=100)
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "text": "교수님, 질문이 있습니다",
                "target_role": "professor",
                "target_age": 50
            }]
        }
    }


class PolitenessResult(BaseModel):
    """Politeness analysis result."""
    level: str
    level_ko: str
    level_en: str
    score: int = Field(ge=0, le=100)
    is_appropriate: bool
    recommended_level: Optional[str] = None
    feedback_ko: Optional[str] = None
    feedback_en: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# ===========================================
# Chat Schemas
# ===========================================

class ChatStartRequest(BaseModel):
    """Request to start a chat session."""
    user_id: str = Field(..., min_length=1)
    avatar_id: str = Field(..., description="Avatar to chat with")
    topic: Optional[str] = Field(default=None, description="Initial topic")
    korean_level: str = Field(default="intermediate")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "user_id": "user_123",
                "avatar_id": "minsu_senior",
                "topic": "campus_life"
            }]
        }
    }


class ChatStartResponse(BaseModel):
    """Response after starting a chat session."""
    session_id: str
    avatar_id: str
    avatar_name_ko: str
    avatar_name_en: str
    greeting: str
    recommended_formality: str
    difficulty: str
    avatar_topics: List[str]
    created_at: str


class ChatMessageRequest(BaseModel):
    """Request to send a message."""
    session_id: str
    message: str = Field(..., min_length=1, max_length=1000)
    include_feedback: bool = Field(default=True)
    include_audio: bool = Field(default=False)


class MessageFeedback(BaseModel):
    """Feedback for a user message."""
    level: str
    level_ko: str
    score: int
    is_appropriate: bool
    feedback_ko: Optional[str] = None
    feedback_en: Optional[str] = None


class UserMessage(BaseModel):
    """User message with feedback."""
    content: str
    feedback: Optional[MessageFeedback] = None


class AvatarMessage(BaseModel):
    """Avatar response message."""
    content: str
    avatar_name: str
    audio: Optional[str] = None  # Base64 encoded
    audio_format: Optional[str] = None


class ChatMessageResponse(BaseModel):
    """Response after sending a message."""
    session_id: str
    user_message: UserMessage
    avatar_response: AvatarMessage
    turn_count: int
    current_topic: Optional[str] = None


class ChatEndRequest(BaseModel):
    """Request to end a chat session."""
    session_id: str


class ChatSummary(BaseModel):
    """Summary of a completed chat session."""
    session_id: str
    avatar_id: str
    total_turns: int
    duration_seconds: int
    average_score: float
    started_at: str
    ended_at: str
    politeness_breakdown: Dict[str, int]
    suggestions: List[str]


# ===========================================
# Avatar Schemas
# ===========================================

class AvatarSummary(BaseModel):
    """Brief avatar information."""
    id: str
    name_ko: str
    name_en: str
    role: str
    difficulty: str
    formality: str


class AvatarDetail(BaseModel):
    """Detailed avatar information."""
    id: str
    name_ko: str
    name_en: str
    role: str
    age: int
    gender: str
    personality: str
    topics: List[str]
    difficulty: str
    formality: str
    greeting: str


class AvatarListResponse(BaseModel):
    """Response for avatar list."""
    avatars: List[AvatarSummary]
    total: int


# ===========================================
# Speech Schemas
# ===========================================

class TTSRequest(BaseModel):
    """Request for text-to-speech."""
    text: str = Field(..., min_length=1, max_length=5000)
    speaker: str = Field(default="nara")
    speed: int = Field(default=0, ge=-5, le=5)
    pitch: int = Field(default=0, ge=-5, le=5)


class TTSResponse(BaseModel):
    """Response for text-to-speech."""
    audio: str  # Base64 encoded
    format: str
    status: str


class STTResponse(BaseModel):
    """Response for speech-to-text."""
    text: str
    status: str


# ===========================================
# Common Schemas
# ===========================================

class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    message: str
    detail: Optional[Any] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str
    services: Dict[str, bool]
