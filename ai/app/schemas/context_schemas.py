"""
Context-Aware Learning Schemas
Tracks user mistakes and learning progress for personalized feedback
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MistakeCategory(str, Enum):
    """Categories of Korean language mistakes"""
    FORMALITY = "formality"           # 존댓말/반말 confusion
    PARTICLES = "particles"           # 조사 errors (은/는, 이/가, 을/를)
    VERB_CONJUGATION = "verb_conjugation"  # 동사 활용 errors
    HONORIFICS = "honorifics"         # 높임말 errors (시, 드리다, etc.)
    WORD_ORDER = "word_order"         # 어순 errors
    VOCABULARY = "vocabulary"         # Unnatural word choices
    SPACING = "spacing"               # 띄어쓰기 errors
    SPELLING = "spelling"             # 맞춤법 errors
    TENSE = "tense"                   # 시제 errors
    NEGATION = "negation"             # 부정문 errors
    OTHER = "other"


class MistakeSeverity(str, Enum):
    """How serious the mistake is"""
    MINOR = "minor"         # Still understandable
    MODERATE = "moderate"   # Confusing but recoverable
    MAJOR = "major"         # Changes meaning significantly


class MistakeRecord(BaseModel):
    """Single mistake instance"""
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S%f"))
    category: MistakeCategory
    severity: MistakeSeverity = MistakeSeverity.MINOR
    original: str                    # What user wrote
    corrected: str                   # Correct form
    explanation: str                 # Why it's wrong (Korean)
    explanation_en: Optional[str] = None  # English explanation
    context: Optional[str] = None    # Surrounding context
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MistakePattern(BaseModel):
    """Recurring mistake pattern"""
    category: MistakeCategory
    count: int = 1
    examples: List[str] = []         # Recent examples
    first_seen: datetime = Field(default_factory=datetime.now)
    last_seen: datetime = Field(default_factory=datetime.now)
    
    # Improvement tracking
    recent_correct: int = 0          # Times used correctly recently
    improving: bool = False


class UserLearningContext(BaseModel):
    """
    Complete user learning context.
    This can be:
    1. Passed from backend (persistent)
    2. Maintained in AI server session (temporary)
    """
    user_id: str
    
    # Proficiency assessment
    estimated_level: str = "beginner"  # beginner, intermediate, advanced
    preferred_formality: str = "polite"  # informal, polite, formal
    native_language: str = "en"
    
    # Mistake tracking
    mistake_history: List[MistakeRecord] = []
    mistake_patterns: Dict[str, MistakePattern] = {}  # category -> pattern
    
    # Strengths (things they do well)
    strengths: List[str] = []
    
    # Session stats
    total_messages: int = 0
    total_mistakes: int = 0
    session_start: datetime = Field(default_factory=datetime.now)
    last_active: datetime = Field(default_factory=datetime.now)
    
    # Topics practiced
    topics_practiced: List[str] = []
    avatars_used: List[str] = []
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ContextAwareChatRequest(BaseModel):
    """Chat request with optional user context"""
    message: str
    avatar_id: str = "sujin_friend"
    topic: Optional[str] = None
    
    # User context (from backend or session)
    user_id: Optional[str] = None
    user_context: Optional[UserLearningContext] = None
    
    # Session management
    session_id: Optional[str] = None
    include_mistake_feedback: bool = True


class ContextAwareChatResponse(BaseModel):
    """Chat response with learning insights"""
    # Basic response
    response: str
    avatar_id: str
    
    # Analysis results
    politeness_analysis: Optional[Dict[str, Any]] = None
    
    # Mistakes found in this message
    mistakes_found: List[MistakeRecord] = []
    
    # Personalized feedback based on history
    personalized_tips: List[str] = []
    
    # Encouragement for improvements
    improvements_noticed: List[str] = []
    
    # Updated context (for backend to store)
    updated_context: Optional[UserLearningContext] = None
    
    status: str = "success"


class MistakeSummaryRequest(BaseModel):
    """Request for mistake summary"""
    user_id: str
    session_id: Optional[str] = None
    include_recommendations: bool = True


class MistakeSummary(BaseModel):
    """Summary of user's mistakes and recommendations"""
    user_id: str
    
    # Overall stats
    total_messages: int
    total_mistakes: int
    accuracy_rate: float  # percentage
    
    # Top problem areas
    top_problem_categories: List[Dict[str, Any]]
    
    # Recent mistakes
    recent_mistakes: List[MistakeRecord]
    
    # Personalized recommendations
    recommendations: List[str]
    
    # Practice suggestions
    suggested_topics: List[str]
    suggested_avatars: List[str]
    
    # Encouragement
    strengths: List[str]
    improvement_areas: List[str]
