"""
Session-Aware Chat Schemas
For multi-avatar, multi-situation session management
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ===========================================
# Session Identification
# ===========================================

class SessionKey(BaseModel):
    """
    Unique identifier for a session.
    A session is uniquely identified by: user + avatar + situation
    """
    user_id: str
    avatar_id: str
    situation_id: str
    
    def to_key(self) -> str:
        """Generate unique session key string."""
        return f"{self.user_id}:{self.avatar_id}:{self.situation_id}"


class SessionInfo(BaseModel):
    """
    Session information passed from Backend to AI Server.
    Backend stores this; AI Server receives it per request.
    """
    session_id: str                    # Unique session ID from Backend
    session_key: SessionKey            # user + avatar + situation
    
    # Session state
    is_new_session: bool = True        # First message in session?
    message_count: int = 0             # Messages so far in this session
    
    # Timestamps
    started_at: Optional[str] = None
    last_message_at: Optional[str] = None
    
    # Session-specific context (what happened so far)
    conversation_summary: Optional[str] = None  # AI-generated summary
    topics_discussed: List[str] = []
    
    # Goals achieved in this session
    situation_goals_completed: List[str] = []


# ===========================================
# Conversation History (from Backend)
# ===========================================

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Single message in conversation history."""
    role: MessageRole
    content: str
    timestamp: Optional[str] = None
    
    # Analysis results (stored by backend)
    mistakes: Optional[List[Dict[str, Any]]] = None
    score: Optional[int] = None


class ConversationHistory(BaseModel):
    """
    Conversation history passed from Backend.
    Backend stores full history; sends recent N messages to AI.
    """
    messages: List[ChatMessage] = []
    total_messages: int = 0
    
    # Summary of older messages (if history is long)
    older_summary: Optional[str] = None


# ===========================================
# Session-Aware Chat Request
# ===========================================

class SessionChatRequest(BaseModel):
    """
    Chat request with full session context.
    Backend sends this to AI Server with each message.
    """
    # Current message
    message: str
    
    # Session identification
    session_info: SessionInfo
    
    # Recent conversation history (last N messages)
    history: ConversationHistory = Field(
        default_factory=ConversationHistory,
        description="Recent messages from backend DB"
    )
    
    # Situation context
    situation_id: str
    situation_context: Optional[Dict[str, Any]] = None  # Full situation data
    
    # User context (learning progress)
    user_context: Optional[Dict[str, Any]] = None
    
    # Options
    include_analysis: bool = True
    include_tips: bool = True
    include_emotion: bool = True  # Include avatar emotion feedback
    max_history_messages: int = Field(default=10, description="How many past messages to consider")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "아메리카노 한 잔 주세요",
                "session_info": {
                    "session_id": "sess_abc123",
                    "session_key": {
                        "user_id": "user123",
                        "avatar_id": "hyunwoo_barista",
                        "situation_id": "cafe_order"
                    },
                    "is_new_session": False,
                    "message_count": 3
                },
                "history": {
                    "messages": [
                        {"role": "assistant", "content": "어서 오세요! 주문하시겠어요?"},
                        {"role": "user", "content": "네, 메뉴 좀 볼게요."},
                        {"role": "assistant", "content": "네, 천천히 보세요~"}
                    ]
                },
                "situation_id": "cafe_order"
            }
        }


# ===========================================
# Session-Aware Chat Response
# ===========================================

class SessionChatResponse(BaseModel):
    """
    Chat response with session-aware information.
    Backend stores relevant parts in DB.
    """
    # Response
    response: str
    
    # Session info (for backend to track)
    session_id: str
    message_number: int              # Message count after this
    
    # Analysis of user's message
    analysis: Optional[Dict[str, Any]] = None
    mistakes_found: List[Dict[str, Any]] = []
    score: Optional[int] = None
    
    # Situation-specific feedback
    situation_appropriate: bool = True
    situation_feedback: Optional[str] = None
    goals_achieved: List[str] = []   # New goals completed this message
    
    # Learning insights
    personalized_tips: List[str] = []
    improvements_noticed: List[str] = []
    
    # 🆕 Emotion & Visual Feedback
    emotion_feedback: Optional[Dict[str, Any]] = Field(
        None,
        description="Avatar emotion, conversation status, warnings for UI"
    )
    
    # For backend to update session
    should_end_session: bool = False  # Natural conversation end?
    suggested_next_topic: Optional[str] = None
    
    # Conversation summary update (if needed)
    updated_summary: Optional[str] = None
    
    status: str = "success"


# ===========================================
# Session Start/End
# ===========================================

class StartSessionRequest(BaseModel):
    """Request to start a new session."""
    user_id: str
    avatar_id: str
    situation_id: str
    
    # Optional user context
    user_context: Optional[Dict[str, Any]] = None


class StartSessionResponse(BaseModel):
    """Response when starting a session."""
    session_id: str
    session_key: SessionKey
    
    # Avatar's opening line for this situation
    opening_message: str
    
    # Situation info
    situation_name: str
    situation_goals: List[str]
    expected_formality: str
    
    # Tips for user
    tips: List[str]
    key_expressions: List[str]
    
    status: str = "success"


class EndSessionRequest(BaseModel):
    """Request to end a session."""
    session_id: str
    
    # Final conversation history
    full_history: Optional[ConversationHistory] = None


class SessionSummary(BaseModel):
    """Summary generated when session ends."""
    session_id: str
    session_key: SessionKey
    
    # Stats
    total_messages: int
    duration_seconds: int
    
    # Performance
    average_score: float
    total_mistakes: int
    mistake_breakdown: Dict[str, int] = {}  # category -> count
    
    # Goals
    goals_total: int
    goals_completed: int
    goals_completed_list: List[str] = []
    
    # Achievements
    achievements: List[str] = []
    
    # AI-generated summary
    conversation_summary: str
    
    # Recommendations
    recommendations: List[str] = []
    suggested_practice: Optional[str] = None


class EndSessionResponse(BaseModel):
    """Response when ending a session."""
    session_id: str
    summary: SessionSummary
    status: str = "success"


# ===========================================
# Session History Query (for Backend)
# ===========================================

class UserSessionsRequest(BaseModel):
    """Request to get user's session history."""
    user_id: str
    avatar_id: Optional[str] = None      # Filter by avatar
    situation_id: Optional[str] = None   # Filter by situation
    limit: int = 10


class SessionListItem(BaseModel):
    """Session item in list."""
    session_id: str
    avatar_id: str
    avatar_name: str
    situation_id: str
    situation_name: str
    
    started_at: str
    ended_at: Optional[str] = None
    
    message_count: int
    average_score: float
    
    is_completed: bool = False


# ===========================================
# Avatar-Situation Progress
# ===========================================

class AvatarSituationProgress(BaseModel):
    """
    User's progress with a specific avatar + situation combination.
    Backend tracks this across sessions.
    """
    user_id: str
    avatar_id: str
    situation_id: str
    
    # Sessions
    total_sessions: int = 0
    completed_sessions: int = 0
    
    # Messages
    total_messages: int = 0
    
    # Scores
    average_score: float = 0.0
    best_score: int = 0
    recent_scores: List[int] = []
    
    # Mastery
    mastery_level: int = Field(default=1, ge=1, le=5)  # 1-5
    is_mastered: bool = False
    
    # Goals
    goals_completed: List[str] = []
    
    # Mistakes in this context
    common_mistakes: Dict[str, int] = {}
    
    # Time
    total_practice_minutes: int = 0
    last_practiced: Optional[str] = None
    first_practiced: Optional[str] = None
