"""
Enhanced Schemas with Situation Support
Adds conversation situation/scenario to avatars and chat sessions
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ===========================================
# Situation Enums
# ===========================================

class SituationCategory(str, Enum):
    """Categories of conversation situations"""
    CASUAL = "casual"               # 일상적인 만남
    SERVICE = "service"             # 서비스 상황 (주문, 요청)
    ACADEMIC = "academic"           # 학교/학업 관련
    PROFESSIONAL = "professional"   # 직장/업무 관련
    SOCIAL = "social"               # 사교 모임
    EMERGENCY = "emergency"         # 긴급 상황


class SituationFormality(str, Enum):
    """Expected formality for the situation"""
    CASUAL = "casual"       # 반말 OK
    POLITE = "polite"       # 해요체
    FORMAL = "formal"       # 합니다체
    MIXED = "mixed"         # 상황에 따라


# ===========================================
# Situation Model
# ===========================================

class Situation(BaseModel):
    """Defines a conversation situation/scenario"""
    
    situation_id: str = Field(..., description="Unique situation ID")
    
    # Basic Info
    name_ko: str = Field(..., description="상황 이름 (한국어)")
    name_en: str = Field(..., description="Situation name (English)")
    description_ko: str = Field(..., description="상황 설명")
    description_en: Optional[str] = None
    
    # Category
    category: SituationCategory = Field(default=SituationCategory.CASUAL)
    
    # Formality
    expected_formality: SituationFormality = Field(default=SituationFormality.POLITE)
    
    # Location/Setting
    location_ko: str = Field(..., description="장소 (예: 카페, 교수 연구실)")
    location_en: Optional[str] = None
    
    # Context
    context_ko: str = Field(..., description="상황 배경 설명")
    context_en: Optional[str] = None
    
    # Conversation Goals
    goals_ko: List[str] = Field(default=[], description="대화 목표")
    goals_en: List[str] = Field(default=[])
    
    # Key Vocabulary
    key_vocabulary: List[str] = Field(default=[], description="이 상황에서 유용한 어휘")
    key_expressions: List[str] = Field(default=[], description="자주 쓰는 표현")
    
    # Difficulty
    difficulty: str = Field(default="medium")  # easy/medium/hard
    
    # Related Topics
    related_topics: List[str] = Field(default=[])
    
    # Tips
    tips_ko: List[str] = Field(default=[], description="이 상황에서의 팁")
    tips_en: List[str] = Field(default=[])

    class Config:
        json_schema_extra = {
            "example": {
                "situation_id": "cafe_order",
                "name_ko": "카페에서 주문하기",
                "name_en": "Ordering at a Cafe",
                "description_ko": "카페에서 음료와 음식을 주문하는 상황",
                "category": "service",
                "expected_formality": "polite",
                "location_ko": "카페",
                "location_en": "Cafe",
                "context_ko": "카페에 들어가서 바리스타에게 주문합니다.",
                "goals_ko": ["음료 주문하기", "추가 요청하기", "결제하기"],
                "key_vocabulary": ["아메리카노", "라떼", "샷 추가", "테이크아웃"],
                "key_expressions": ["~주세요", "~할게요", "~있나요?"],
                "difficulty": "easy",
                "tips_ko": ["해요체를 사용하세요", "감사합니다로 마무리하세요"]
            }
        }


# ===========================================
# Enhanced Avatar with Situation
# ===========================================

class AvatarSituation(BaseModel):
    """Avatar-specific situation configuration"""
    
    situation_id: str
    situation: Situation
    
    # Avatar's role in this situation
    avatar_role_ko: str = Field(..., description="이 상황에서 아바타의 역할")
    avatar_role_en: Optional[str] = None
    
    # Opening line for this situation
    opening_line: str = Field(..., description="상황 시작 대사")
    
    # Example conversations
    example_dialogues: List[Dict[str, str]] = Field(
        default=[],
        description="예시 대화 [{user: ..., avatar: ...}]"
    )


class EnhancedAvatar(BaseModel):
    """Avatar with situation support"""
    
    avatar_id: str
    
    # Basic Info (existing)
    name_ko: str
    name_en: str
    role: str  # junior/friend/senior/professor/boss
    age: int
    gender: str
    personality: str
    formality: str  # informal/polite/very_polite
    difficulty: str  # easy/medium/hard
    topics: List[str] = []
    greeting: str
    voice_id: str = "nara"
    is_system: bool = True
    
    # 🆕 Situations (NEW)
    situations: List[AvatarSituation] = Field(
        default=[],
        description="상황별 설정"
    )
    default_situation: Optional[str] = Field(
        None,
        description="기본 상황 ID"
    )
    
    # Stats
    total_sessions: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ===========================================
# Enhanced Chat Request with Situation
# ===========================================

class SituationChatRequest(BaseModel):
    """Chat request with situation context"""
    
    message: str
    user_id: str
    avatar_id: str
    
    # 🆕 Situation (NEW)
    situation_id: Optional[str] = Field(
        None,
        description="상황 ID (없으면 기본 상황)"
    )
    
    # Optional context
    topic: Optional[str] = None
    include_feedback: bool = True


class SituationChatResponse(BaseModel):
    """Chat response with situation context"""
    
    response: str
    avatar_id: str
    
    # Situation info
    situation_id: Optional[str] = None
    situation_name: Optional[str] = None
    
    # Analysis
    mistakes_found: List[Dict[str, Any]] = []
    personalized_tips: List[str] = []
    
    # Situation-specific feedback
    situation_appropriate: bool = True
    situation_feedback: Optional[str] = None
    
    status: str = "success"


# ===========================================
# Enhanced User Profile with Situation Progress
# ===========================================

class SituationProgress(BaseModel):
    """User's progress in a specific situation"""
    
    situation_id: str
    situation_name: str
    
    # Practice stats
    times_practiced: int = 0
    total_messages: int = 0
    
    # Scores
    average_score: float = 0.0
    best_score: int = 0
    
    # Mastery
    mastery_level: int = Field(default=1, ge=1, le=5)  # 1-5
    is_mastered: bool = False
    
    # Last practice
    last_practiced: Optional[str] = None


class EnhancedUserProfile(BaseModel):
    """User profile with situation tracking"""
    
    user_id: str
    username: Optional[str] = None
    
    # Basic Info
    native_language: str = "English"
    korean_level: str = "intermediate"
    
    # Preferences
    interests: List[str] = []
    learning_goals: List[str] = []
    preferred_difficulty: str = "medium"
    
    # Progress
    total_sessions: int = 0
    total_messages: int = 0
    overall_average_score: float = 0.0
    
    # Avatar progress
    avatars_used: List[str] = []
    favorite_avatars: List[str] = []
    
    # 🆕 Situation Progress (NEW)
    situations_practiced: List[str] = Field(
        default=[],
        description="상황 ID 목록"
    )
    situation_progress: Dict[str, SituationProgress] = Field(
        default={},
        description="상황별 진행 상황"
    )
    mastered_situations: List[str] = Field(
        default=[],
        description="마스터한 상황들"
    )
    recommended_situations: List[str] = Field(
        default=[],
        description="추천 상황들"
    )
    
    # Timestamps
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
