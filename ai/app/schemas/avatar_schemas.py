"""
Avatar Management Schemas
Support for multiple avatars and custom avatar creation
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ===========================================
# Enums
# ===========================================

class AvatarRole(str, Enum):
    JUNIOR = "junior"
    FRIEND = "friend"
    SENIOR = "senior"
    PROFESSOR = "professor"
    BOSS = "boss"
    CUSTOM = "custom"


class AvatarDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class AvatarFormality(str, Enum):
    INFORMAL = "informal"
    POLITE = "polite"
    VERY_POLITE = "very_polite"


# ===========================================
# Avatar Models
# ===========================================

class AvatarBase(BaseModel):
    """Base avatar information."""
    name_ko: str = Field(..., description="Korean name")
    name_en: str = Field(..., description="English name")
    role: AvatarRole = Field(..., description="Social role")
    age: int = Field(..., ge=10, le=80, description="Avatar age")
    gender: str = Field(..., description="male/female/other")
    personality: str = Field(..., description="Personality description in Korean")
    formality: AvatarFormality = Field(..., description="Expected speech level")
    difficulty: AvatarDifficulty = Field(..., description="Conversation difficulty")
    topics: List[str] = Field(default=[], description="Topics avatar can discuss")
    greeting: str = Field(..., description="Avatar's greeting message")


class AvatarCreate(AvatarBase):
    """Request to create a new avatar."""
    avatar_id: Optional[str] = Field(None, description="Custom ID or auto-generate")
    created_by: Optional[str] = Field(None, description="User who created this avatar")
    voice_id: str = Field(default="nara", description="CLOVA Voice ID")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "name_ko": "영희 선배",
                "name_en": "Younghee (Senior)",
                "role": "senior",
                "age": 25,
                "gender": "female",
                "personality": "활발하고 친절한 선배",
                "formality": "polite",
                "difficulty": "medium",
                "topics": ["campus_life", "career_future", "kpop"],
                "greeting": "안녕! 오랜만이야. 잘 지냈어?"
            }]
        }
    }


class AvatarUpdate(BaseModel):
    """Request to update an avatar."""
    name_ko: Optional[str] = None
    name_en: Optional[str] = None
    personality: Optional[str] = None
    topics: Optional[List[str]] = None
    greeting: Optional[str] = None
    difficulty: Optional[AvatarDifficulty] = None
    voice_id: Optional[str] = None


class Avatar(AvatarBase):
    """Full avatar model."""
    avatar_id: str
    voice_id: str = "nara"
    is_system: bool = Field(default=False, description="System default or user-created")
    created_by: Optional[str] = None
    created_at: str
    updated_at: str
    
    # Stats
    total_sessions: int = 0
    total_users: int = 0


class AvatarListResponse(BaseModel):
    """Response for listing avatars."""
    avatars: List[Avatar]
    total: int
    system_avatars: int
    custom_avatars: int


# ===========================================
# User-Avatar Progress
# ===========================================

class UserAvatarProgress(BaseModel):
    """Progress for a specific user-avatar pair."""
    user_id: str
    avatar_id: str
    avatar_name: str
    
    # Session stats
    total_sessions: int = 0
    total_messages: int = 0
    total_time_minutes: int = 0
    
    # Scores
    average_score: float = 0.0
    best_score: int = 0
    recent_scores: List[int] = Field(default=[])
    
    # Skill progress with this avatar
    skill_progress: Dict[str, float] = Field(
        default={},
        description="Skill improvement with this avatar"
    )
    
    # Interaction
    first_chat: Optional[str] = None
    last_chat: Optional[str] = None
    
    # Relationship level (gamification)
    friendship_level: int = Field(default=1, ge=1, le=10)
    friendship_points: int = Field(default=0)


class UserAvatarSummary(BaseModel):
    """Summary of user's interactions with all avatars."""
    user_id: str
    total_avatars_used: int
    favorite_avatar: Optional[str] = None
    avatar_progress: List[UserAvatarProgress]


# ===========================================
# Enhanced User Profile
# ===========================================

class EnhancedUserProfile(BaseModel):
    """Enhanced user profile with avatar tracking."""
    user_id: str
    username: Optional[str] = None
    
    # Basic info
    native_language: str = "English"
    korean_level: str = "intermediate"
    
    # Preferences
    interests: List[str] = Field(default=[])
    learning_goals: List[str] = Field(default=[])
    preferred_difficulty: str = "medium"
    
    # Overall progress
    total_sessions: int = 0
    total_messages: int = 0
    total_practice_minutes: int = 0
    overall_average_score: float = 0.0
    
    # Avatar-specific
    avatars_used: List[str] = Field(default=[], description="Avatar IDs user has chatted with")
    favorite_avatars: List[str] = Field(default=[], description="User's favorite avatars")
    avatar_progress: Dict[str, UserAvatarProgress] = Field(
        default={},
        description="Progress per avatar"
    )
    
    # Custom avatars
    custom_avatars: List[str] = Field(default=[], description="Avatars created by this user")
    
    # Timestamps
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_active: Optional[str] = None


class UserProfileUpdate(BaseModel):
    """Request to update user profile."""
    username: Optional[str] = None
    native_language: Optional[str] = None
    korean_level: Optional[str] = None
    interests: Optional[List[str]] = None
    learning_goals: Optional[List[str]] = None
    preferred_difficulty: Optional[str] = None
    favorite_avatars: Optional[List[str]] = None
