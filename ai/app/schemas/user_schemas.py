"""
User Schemas for Personalization
User profiles, progress tracking, and context
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ===========================================
# Enums
# ===========================================

class KoreanLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class SkillType(str, Enum):
    INFORMAL_SPEECH = "informal_speech"
    POLITE_SPEECH = "polite_speech"
    FORMAL_SPEECH = "formal_speech"
    HONORIFICS = "honorifics"
    VOCABULARY = "vocabulary"
    GRAMMAR = "grammar"


# ===========================================
# User Profile
# ===========================================

class UserProfile(BaseModel):
    """Complete user profile for personalization."""
    user_id: str
    
    # Basic info
    username: Optional[str] = None
    native_language: str = Field(default="English", description="User's native language")
    korean_level: KoreanLevel = Field(default=KoreanLevel.INTERMEDIATE)
    
    # Preferences
    interests: List[str] = Field(
        default=["daily_life", "cafe_food"],
        description="Preferred conversation topics"
    )
    learning_goals: List[str] = Field(
        default=["polite_speech"],
        description="What user wants to improve"
    )
    preferred_difficulty: str = Field(default="medium")
    
    # Settings
    feedback_language: str = Field(default="ko", description="ko or en")
    show_hints: bool = Field(default=True)
    
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UserProfileCreate(BaseModel):
    """Request to create user profile."""
    user_id: str
    username: Optional[str] = None
    native_language: str = "English"
    korean_level: str = "intermediate"
    interests: List[str] = []
    learning_goals: List[str] = []


# ===========================================
# Skill Levels
# ===========================================

class SkillLevel(BaseModel):
    """User's skill level in a specific area."""
    skill_type: str
    level: int = Field(ge=1, le=5, description="Skill level 1-5")
    total_practice: int = Field(default=0, description="Total practice count")
    last_practiced: Optional[str] = None
    
    # Trend
    recent_scores: List[int] = Field(default=[], description="Last 10 scores")
    is_improving: bool = Field(default=False)


class UserSkills(BaseModel):
    """All skill levels for a user."""
    user_id: str
    
    informal_speech: SkillLevel = Field(
        default_factory=lambda: SkillLevel(skill_type="informal_speech", level=3)
    )
    polite_speech: SkillLevel = Field(
        default_factory=lambda: SkillLevel(skill_type="polite_speech", level=2)
    )
    formal_speech: SkillLevel = Field(
        default_factory=lambda: SkillLevel(skill_type="formal_speech", level=2)
    )
    honorifics: SkillLevel = Field(
        default_factory=lambda: SkillLevel(skill_type="honorifics", level=2)
    )
    vocabulary: SkillLevel = Field(
        default_factory=lambda: SkillLevel(skill_type="vocabulary", level=3)
    )
    grammar: SkillLevel = Field(
        default_factory=lambda: SkillLevel(skill_type="grammar", level=3)
    )
    
    def get_weakest_skills(self, n: int = 2) -> List[str]:
        """Get n weakest skills."""
        skills = {
            "informal_speech": self.informal_speech.level,
            "polite_speech": self.polite_speech.level,
            "formal_speech": self.formal_speech.level,
            "honorifics": self.honorifics.level,
        }
        sorted_skills = sorted(skills.items(), key=lambda x: x[1])
        return [s[0] for s in sorted_skills[:n]]
    
    def get_strongest_skills(self, n: int = 2) -> List[str]:
        """Get n strongest skills."""
        skills = {
            "informal_speech": self.informal_speech.level,
            "polite_speech": self.polite_speech.level,
            "formal_speech": self.formal_speech.level,
            "honorifics": self.honorifics.level,
        }
        sorted_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)
        return [s[0] for s in sorted_skills[:n]]


# ===========================================
# Error Tracking
# ===========================================

class ErrorRecord(BaseModel):
    """Record of a specific error type."""
    error_type: str
    name_ko: str
    name_en: str
    
    # Counts
    total_count: int = Field(default=0)
    this_week_count: int = Field(default=0)
    this_session_count: int = Field(default=0)
    
    # Trend
    last_occurrence: Optional[str] = None
    is_decreasing: bool = Field(default=False, description="Is user making this error less?")
    
    # Context
    common_contexts: List[str] = Field(
        default=[],
        description="Avatars/topics where this error occurs most"
    )


class UserErrors(BaseModel):
    """All error records for a user."""
    user_id: str
    errors: Dict[str, ErrorRecord] = Field(default={})
    
    def get_most_common_errors(self, n: int = 3) -> List[ErrorRecord]:
        """Get n most common errors."""
        sorted_errors = sorted(
            self.errors.values(),
            key=lambda e: e.total_count,
            reverse=True
        )
        return sorted_errors[:n]
    
    def get_recent_errors(self, n: int = 3) -> List[ErrorRecord]:
        """Get n most recent errors."""
        sorted_errors = sorted(
            self.errors.values(),
            key=lambda e: e.last_occurrence or "",
            reverse=True
        )
        return sorted_errors[:n]


# ===========================================
# Progress Tracking
# ===========================================

class SessionSummary(BaseModel):
    """Summary of a single session."""
    session_id: str
    avatar_id: str
    topic: Optional[str]
    
    # Scores
    average_score: float
    highest_score: int
    lowest_score: int
    
    # Counts
    total_messages: int
    correct_messages: int
    
    # Errors in this session
    errors: Dict[str, int] = Field(default={})
    
    # Timestamp
    started_at: str
    ended_at: str
    duration_seconds: int


class UserProgress(BaseModel):
    """Overall progress for a user."""
    user_id: str
    
    # Overall stats
    total_sessions: int = 0
    total_messages: int = 0
    total_practice_minutes: int = 0
    
    # Scores
    overall_average_score: float = 0.0
    best_score: int = 0
    current_streak: int = Field(default=0, description="Days practiced in a row")
    
    # Recent sessions
    recent_sessions: List[SessionSummary] = Field(default=[])
    
    # Score history (for charts)
    score_history: List[Dict[str, Any]] = Field(
        default=[],
        description="Daily/weekly score averages"
    )
    
    # Improvement
    improvement_rate: float = Field(
        default=0.0,
        description="Score improvement percentage over last 7 days"
    )
    trend: str = Field(
        default="stable",
        description="improving/stable/declining"
    )
    
    # Achievements
    achievements: List[str] = Field(default=[])
    
    # Last activity
    last_practice_date: Optional[str] = None


# ===========================================
# User Context (for API requests)
# ===========================================

class UserContext(BaseModel):
    """
    User context sent with each request.
    Backend sends this to AI server for personalization.
    """
    user_id: str
    
    # Level
    korean_level: str = "intermediate"
    
    # Skills (simplified)
    weak_skills: List[str] = Field(
        default=[],
        description="Skills that need practice"
    )
    strong_skills: List[str] = Field(
        default=[],
        description="Skills user is good at"
    )
    
    # Errors (simplified)
    common_errors: List[str] = Field(
        default=[],
        description="Error types user makes often"
    )
    recent_errors: List[str] = Field(
        default=[],
        description="Errors from recent sessions"
    )
    
    # Progress
    sessions_completed: int = 0
    average_score: float = 0.0
    trend: str = "stable"  # improving/stable/declining
    
    # Preferences
    interests: List[str] = Field(default=[])
    learning_goals: List[str] = Field(default=[])
    
    # Settings
    feedback_language: str = "ko"
    show_hints: bool = True


class UserContextMinimal(BaseModel):
    """Minimal context for quick requests."""
    user_id: str
    korean_level: str = "intermediate"
    weak_skills: List[str] = []
    common_errors: List[str] = []


# ===========================================
# Recommendations
# ===========================================

class PracticeRecommendation(BaseModel):
    """Recommended practice for user."""
    # What to practice
    recommended_avatar: str
    avatar_name_ko: str
    recommended_topic: str
    topic_name_ko: str
    
    # Why
    reason_ko: str
    reason_en: str
    
    # Focus
    focus_skill: str
    focus_errors: List[str]
    
    # Difficulty
    difficulty: str
    estimated_duration_minutes: int = 10
    
    # Priority
    priority: int = Field(ge=1, le=3, description="1=high, 2=medium, 3=low")


class UserRecommendations(BaseModel):
    """All recommendations for a user."""
    user_id: str
    generated_at: str
    
    # Practice recommendations
    recommended_practices: List[PracticeRecommendation]
    
    # Daily goals
    daily_goals: List[str]
    
    # Tips based on errors
    personalized_tips: List[str]
    
    # Motivation
    motivation_message_ko: str
    motivation_message_en: str


# ===========================================
# API Request/Response Models
# ===========================================

class PersonalizedChatRequest(BaseModel):
    """Chat request with personalization context."""
    session_id: str
    message: str
    include_feedback: bool = True
    include_audio: bool = False
    
    # Personalization
    user_context: Optional[UserContext] = None


class PersonalizedFeedback(BaseModel):
    """Personalized feedback response."""
    # Basic feedback
    level: str
    score: int
    is_appropriate: bool
    
    # Personalized parts
    feedback_ko: str
    feedback_en: str
    
    # Error context
    error_history_note: Optional[str] = Field(
        None,
        description="e.g., 'You made this mistake 5 times this week'"
    )
    
    # Personalized tip
    personalized_tip_ko: Optional[str] = None
    personalized_tip_en: Optional[str] = None
    
    # Progress note
    progress_note: Optional[str] = Field(
        None,
        description="e.g., 'You're improving! Score up 10% this week'"
    )
    
    # Encouragement
    encouragement_ko: Optional[str] = None
    encouragement_en: Optional[str] = None


class ProgressUpdateRequest(BaseModel):
    """Request to update user progress after session."""
    user_id: str
    session_summary: SessionSummary


class ProgressResponse(BaseModel):
    """Response with user's progress."""
    user_id: str
    progress: UserProgress
    skills: UserSkills
    errors: UserErrors
    recommendations: UserRecommendations
