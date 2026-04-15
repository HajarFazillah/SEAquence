"""
User Profile Schema - Aligned with Mobile UI (v3)

Fields:
- age: User's age
- memo: AI context memo (for personalized responses)
- interests: Topics user likes
- dislikes: Topics to avoid
- korean_level: beginner/intermediate/advanced
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class KoreanLevel(str, Enum):
    BEGINNER = "beginner"  # 초급
    INTERMEDIATE = "intermediate"  # 중급
    ADVANCED = "advanced"  # 고급


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class AgeGroup(str, Enum):
    TEEN = "teen"  # < 20
    TWENTIES = "20s"  # 20-29
    THIRTIES = "30s"  # 30-39
    FORTIES = "40s"  # 40-49
    FIFTIES_PLUS = "50+"  # 50+


def get_age_group(age: Optional[int]) -> AgeGroup:
    """Convert age to age group"""
    if age is None:
        return AgeGroup.TWENTIES
    if age < 20:
        return AgeGroup.TEEN
    elif age < 30:
        return AgeGroup.TWENTIES
    elif age < 40:
        return AgeGroup.THIRTIES
    elif age < 50:
        return AgeGroup.FORTIES
    else:
        return AgeGroup.FIFTIES_PLUS


class UserProfileBase(BaseModel):
    """Base user profile fields"""
    name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    
    age: Optional[int] = Field(None, ge=1, le=120)
    gender: Gender = Field(default=Gender.OTHER)
    
    korean_level: KoreanLevel = Field(default=KoreanLevel.INTERMEDIATE)
    
    interests: List[str] = Field(
        default_factory=list,
        description="Topics user is interested in",
        max_items=50
    )
    
    dislikes: List[str] = Field(
        default_factory=list,
        description="Topics to avoid in conversation",
        max_items=50
    )
    
    memo: Optional[str] = Field(
        None,
        description="AI context memo - personality, learning goals, preferences",
        max_length=2000
    )


class UserProfileCreate(UserProfileBase):
    """Schema for creating user profile"""
    pass


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile"""
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[Gender] = None
    korean_level: Optional[KoreanLevel] = None
    interests: Optional[List[str]] = None
    dislikes: Optional[List[str]] = None
    memo: Optional[str] = None


class UserProfile(UserProfileBase):
    """Full user profile with computed fields"""
    id: str
    
    # Computed
    age_group: Optional[AgeGroup] = None
    
    # Stats
    words_learned: int = 0
    phrases_learned: int = 0
    current_streak: int = 0
    total_minutes: int = 0
    
    class Config:
        from_attributes = True
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.age:
            self.age_group = get_age_group(self.age)


class AIContext(BaseModel):
    """
    Context sent to AI for personalized responses.
    Derived from user profile.
    """
    user_description: Optional[str] = Field(None, description="From user memo")
    preferred_topics: List[str] = Field(default_factory=list)
    avoided_topics: List[str] = Field(default_factory=list)
    language_level: KoreanLevel = Field(default=KoreanLevel.INTERMEDIATE)
    age_group: AgeGroup = Field(default=AgeGroup.TWENTIES)
    
    @classmethod
    def from_user_profile(cls, profile: UserProfile) -> "AIContext":
        return cls(
            user_description=profile.memo,
            preferred_topics=profile.interests,
            avoided_topics=profile.dislikes,
            language_level=profile.korean_level,
            age_group=get_age_group(profile.age),
        )


class SavedVocabulary(BaseModel):
    """Saved word or phrase"""
    id: str
    user_id: str
    type: str = Field(..., description="'word' or 'phrase'")
    content: str
    meaning: str
    example: Optional[str] = None
    source_avatar_id: Optional[str] = None
    source_avatar_name: Optional[str] = None
    created_at: str


class UserStats(BaseModel):
    """User learning statistics"""
    user_id: str
    words_learned: int = 0
    phrases_learned: int = 0
    current_streak: int = 0
    total_minutes: int = 0
    total_conversations: int = 0
    avg_accuracy: float = 0.0
