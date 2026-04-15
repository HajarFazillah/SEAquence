"""
Avatar Schema - Aligned with Mobile UI (v3)

Fields:
- avatarType: 'fictional' | 'real' (가상 인물 vs 실제 인물)
- description: AI prompt for avatar personality/behavior
- memo: Additional AI context
- customRole: User-defined role if not in predefined list
- Expanded roles (30+)
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum


class AvatarType(str, Enum):
    FICTIONAL = "fictional"  # 가상 인물
    REAL = "real"  # 실제 인물


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class SpeechLevel(str, Enum):
    FORMAL = "formal"  # 합쇼체 (-습니다)
    POLITE = "polite"  # 해요체 (-어요)
    INFORMAL = "informal"  # 반말 (-어, -야)


# Predefined roles with speech level mappings
ROLE_SPEECH_MAPPING = {
    # 친구/동기
    "friend": {"to_user": "informal", "from_user": "informal"},
    "close_friend": {"to_user": "informal", "from_user": "informal"},
    "classmate": {"to_user": "informal", "from_user": "informal"},
    "roommate": {"to_user": "informal", "from_user": "informal"},
    "club_member": {"to_user": "informal", "from_user": "informal"},
    
    # 가족
    "younger_sibling": {"to_user": "informal", "from_user": "informal"},
    "older_brother": {"to_user": "informal", "from_user": "polite"},
    "older_sister": {"to_user": "informal", "from_user": "polite"},
    "cousin": {"to_user": "informal", "from_user": "informal"},
    "parent": {"to_user": "polite", "from_user": "formal"},
    "grandparent": {"to_user": "polite", "from_user": "formal"},
    
    # 학교
    "junior": {"to_user": "polite", "from_user": "informal"},
    "senior": {"to_user": "informal", "from_user": "polite"},
    "professor": {"to_user": "polite", "from_user": "formal"},
    "teacher": {"to_user": "polite", "from_user": "formal"},
    "tutor": {"to_user": "polite", "from_user": "polite"},
    "classmate_formal": {"to_user": "informal", "from_user": "informal"},
    
    # 직장
    "colleague": {"to_user": "polite", "from_user": "polite"},
    "teammate": {"to_user": "polite", "from_user": "polite"},
    "team_leader": {"to_user": "polite", "from_user": "formal"},
    "boss": {"to_user": "polite", "from_user": "formal"},
    "ceo": {"to_user": "formal", "from_user": "formal"},
    "intern": {"to_user": "polite", "from_user": "informal"},
    "client": {"to_user": "formal", "from_user": "formal"},
    
    # 서비스/기타
    "staff": {"to_user": "polite", "from_user": "polite"},
    "stranger": {"to_user": "polite", "from_user": "polite"},
    "neighbor": {"to_user": "polite", "from_user": "polite"},
    "doctor": {"to_user": "polite", "from_user": "formal"},
    "delivery": {"to_user": "polite", "from_user": "polite"},
    "taxi_driver": {"to_user": "polite", "from_user": "polite"},
}

ROLE_LABELS = {
    "friend": "친구",
    "close_friend": "절친",
    "classmate": "동기",
    "roommate": "룸메이트",
    "club_member": "동아리 멤버",
    "younger_sibling": "동생",
    "older_brother": "형/오빠",
    "older_sister": "누나/언니",
    "cousin": "사촌",
    "parent": "부모님",
    "grandparent": "조부모님",
    "junior": "후배",
    "senior": "선배",
    "professor": "교수님",
    "teacher": "선생님",
    "tutor": "튜터/과외선생",
    "classmate_formal": "같은 반 친구",
    "colleague": "동료",
    "teammate": "팀원",
    "team_leader": "팀장",
    "boss": "상사/부장",
    "ceo": "대표/사장님",
    "intern": "인턴",
    "client": "고객/클라이언트",
    "staff": "직원/점원",
    "stranger": "처음 만난 사람",
    "neighbor": "이웃",
    "doctor": "의사",
    "delivery": "배달원",
    "taxi_driver": "택시기사",
}


class AvatarBase(BaseModel):
    """Base avatar fields"""
    name_ko: str = Field(..., description="Korean name", min_length=1, max_length=50)
    name_en: Optional[str] = Field(None, description="English name", max_length=50)
    age: Optional[int] = Field(None, description="Avatar age", ge=1, le=120)
    gender: Gender = Field(default=Gender.OTHER)
    
    avatar_type: AvatarType = Field(default=AvatarType.FICTIONAL, description="가상 인물 vs 실제 인물")
    
    role: Optional[str] = Field(None, description="Predefined role ID")
    custom_role: Optional[str] = Field(None, description="User-defined custom role", max_length=50)
    
    relationship_description: Optional[str] = Field(
        None, 
        description="Description of relationship",
        max_length=500
    )
    
    description: Optional[str] = Field(
        None,
        description="AI prompt: personality, speaking style, characteristics",
        max_length=2000
    )
    
    personality_traits: List[str] = Field(default_factory=list, max_items=20)
    speaking_style: Optional[str] = Field(None, max_length=500)
    interests: List[str] = Field(default_factory=list, max_items=30)
    dislikes: List[str] = Field(default_factory=list, max_items=30)
    
    difficulty: Difficulty = Field(default=Difficulty.MEDIUM)
    
    memo: Optional[str] = Field(
        None,
        description="Additional AI context memo",
        max_length=1000
    )
    
    # Visual
    avatar_bg: Optional[str] = Field(None, description="Background color hex")
    icon: Optional[str] = Field(default="user", description="Icon name")


class AvatarCreate(AvatarBase):
    """Schema for creating avatar"""
    pass


class AvatarUpdate(BaseModel):
    """Schema for updating avatar (all fields optional)"""
    name_ko: Optional[str] = None
    name_en: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[Gender] = None
    avatar_type: Optional[AvatarType] = None
    role: Optional[str] = None
    custom_role: Optional[str] = None
    relationship_description: Optional[str] = None
    description: Optional[str] = None
    personality_traits: Optional[List[str]] = None
    speaking_style: Optional[str] = None
    interests: Optional[List[str]] = None
    dislikes: Optional[List[str]] = None
    difficulty: Optional[Difficulty] = None
    memo: Optional[str] = None
    avatar_bg: Optional[str] = None
    icon: Optional[str] = None


class Avatar(AvatarBase):
    """Full avatar with computed fields"""
    id: str
    
    # Computed speech levels based on role
    formality_to_user: SpeechLevel = Field(default=SpeechLevel.POLITE)
    formality_from_user: SpeechLevel = Field(default=SpeechLevel.POLITE)
    
    # AI-generated bio
    bio: Optional[str] = None
    
    # Stats
    total_conversations: int = 0
    total_minutes: int = 0
    avg_score: float = 0.0
    
    class Config:
        from_attributes = True


class AvatarWithSpeechRecommendation(Avatar):
    """Avatar with speech level recommendation"""
    recommended_speech_to_user: SpeechLevel
    recommended_speech_from_user: SpeechLevel
    speech_recommendation_reason: str


def get_speech_levels_for_role(role: Optional[str], custom_role: Optional[str] = None) -> dict:
    """
    Get recommended speech levels based on role.
    Returns dict with 'to_user' and 'from_user' speech levels.
    """
    if role and role in ROLE_SPEECH_MAPPING:
        mapping = ROLE_SPEECH_MAPPING[role]
        return {
            "to_user": SpeechLevel(mapping["to_user"]),
            "from_user": SpeechLevel(mapping["from_user"]),
        }
    
    # Default for custom roles or unknown roles
    return {
        "to_user": SpeechLevel.POLITE,
        "from_user": SpeechLevel.POLITE,
    }


def get_role_label(role: Optional[str], custom_role: Optional[str] = None) -> str:
    """Get display label for role"""
    if custom_role:
        return custom_role
    if role and role in ROLE_LABELS:
        return ROLE_LABELS[role]
    return "지인"

# Updated get_speech_levels_for_role with custom role analyzer support
def get_speech_levels_for_role_v2(role: Optional[str], custom_role: Optional[str] = None) -> dict:
    """
    Get recommended speech levels based on role.
    Priority: predefined role → custom role text analysis → default
    """
    if role and role in ROLE_SPEECH_MAPPING:
        mapping = ROLE_SPEECH_MAPPING[role]
        return {
            "to_user": SpeechLevel(mapping["to_user"]),
            "from_user": SpeechLevel(mapping["from_user"]),
        }

    if custom_role and custom_role.strip():
        try:
            from app.services.custom_role_analyzer import get_speech_levels_for_custom_role
            return get_speech_levels_for_custom_role(custom_role)
        except Exception:
            pass

    return {
        "to_user": SpeechLevel.POLITE,
        "from_user": SpeechLevel.POLITE,
    }
