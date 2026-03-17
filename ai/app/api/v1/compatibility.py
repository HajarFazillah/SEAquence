"""
Compatibility API
ML-based compatibility analysis between user and avatar
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.ml.compatibility_service import analyze_compatibility, get_compatibility_analyzer
from app.core.constants import AVATARS

router = APIRouter(prefix="/compatibility", tags=["Compatibility"])


# ===========================================
# SCHEMAS
# ===========================================

class UserPreferences(BaseModel):
    """User's likes, dislikes, and personality traits."""
    likes: List[str] = Field(
        default=[],
        description="Things user likes (free-text keywords)",
        example=["BTS", "스타벅스", "여행", "넷플릭스"]
    )
    dislikes: List[str] = Field(
        default=[],
        description="Things user dislikes",
        example=["정치", "아침형 인간"]
    )
    personality_traits: List[str] = Field(
        default=[],
        description="User's personality traits",
        example=["외향적", "유머러스"]
    )


class AvatarPreferences(BaseModel):
    """Avatar's likes, dislikes, and personality traits."""
    avatar_id: str
    likes: List[str] = Field(default=[])
    dislikes: List[str] = Field(default=[])
    personality_traits: List[str] = Field(default=[])


class CompatibilityRequest(BaseModel):
    """Request for compatibility analysis."""
    user: UserPreferences
    avatar_id: str = Field(description="Avatar ID to check compatibility with")
    
    # Optional: override avatar preferences (if not using defaults)
    avatar_likes: Optional[List[str]] = None
    avatar_dislikes: Optional[List[str]] = None
    avatar_traits: Optional[List[str]] = None


class CompatibilityMatch(BaseModel):
    """A semantic match between user and avatar interests."""
    item_a: str = Field(description="User's interest")
    item_b: str = Field(description="Avatar's interest")
    similarity: float = Field(description="Semantic similarity (0-1)")
    is_exact: bool = Field(description="Whether it's an exact string match")


class CompatibilityResponse(BaseModel):
    """Response for compatibility analysis."""
    avatar_id: str
    avatar_name_ko: str
    
    score: float = Field(description="Compatibility score (0-100)")
    chemistry_level: str = Field(description="Chemistry level: excellent/good/okay/low")
    
    common_interests: List[CompatibilityMatch]
    suggested_topics: List[str] = Field(description="Topics to discuss")
    avoid_topics: List[str] = Field(description="Topics to avoid")
    
    personality_match: float = Field(description="Personality compatibility (0-100)")
    
    summary_ko: str
    summary_en: str
    match_reasons: List[str]
    
    ml_available: bool = Field(description="Whether ML model was used")


class BatchCompatibilityRequest(BaseModel):
    """Request for checking compatibility with multiple avatars."""
    user: UserPreferences


class AvatarCompatibility(BaseModel):
    """Compatibility result for a single avatar."""
    avatar_id: str
    avatar_name_ko: str
    avatar_role: str
    score: float
    chemistry_level: str
    common_interests: List[CompatibilityMatch]
    summary_ko: str


class BatchCompatibilityResponse(BaseModel):
    """Response for batch compatibility check."""
    user_likes: List[str]
    results: List[AvatarCompatibility]
    ml_available: bool


# ===========================================
# DEFAULT AVATAR PREFERENCES
# ===========================================

# These can be stored in DB, but for now defined here
AVATAR_PREFERENCES = {
    "professor_kim": {
        "likes": ["연구", "독서", "클래식 음악", "학문", "커피"],
        "dislikes": ["게으름", "무단 결석", "표절", "지각"],
        "traits": ["엄격함", "지적임", "배려심"]
    },
    "minsu_senior": {
        "likes": ["여행", "맥주", "축구", "진로 상담", "캠핑"],
        "dislikes": ["게으름", "무책임", "거짓말"],
        "traits": ["배려심", "리더십", "유머러스"]
    },
    "sujin_friend": {
        "likes": ["K-POP", "카페", "드라마", "쇼핑", "SNS", "여행"],
        "dislikes": ["정치 얘기", "아침형 인간", "공부 얘기"],
        "traits": ["외향적", "유머러스", "친절함"]
    },
    "manager_lee": {
        "likes": ["효율성", "커피", "계획", "운동", "독서"],
        "dislikes": ["지각", "변명", "무책임", "비효율"],
        "traits": ["체계적", "공정함", "바쁨"]
    },
    "jiwon_junior": {
        "likes": ["게임", "애니메이션", "라면", "유튜브", "만화"],
        "dislikes": ["과제", "아침 수업", "발표"],
        "traits": ["순수함", "호기심", "예의바름"]
    }
}


# ===========================================
# API ENDPOINTS
# ===========================================

@router.post("/analyze", response_model=CompatibilityResponse)
async def analyze_avatar_compatibility(request: CompatibilityRequest):
    """
    Analyze compatibility between user and a specific avatar.
    
    Uses ML-based semantic matching to find common interests,
    even when words are different but meanings are similar.
    
    Example:
    - User likes "BTS" → Matches with avatar's "K-POP" (similarity: 0.89)
    - User likes "스타벅스" → Matches with avatar's "카페" (similarity: 0.87)
    """
    
    # Get avatar info
    avatar = AVATARS.get(request.avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail=f"Avatar not found: {request.avatar_id}")
    
    # Get avatar preferences (from request or defaults)
    default_prefs = AVATAR_PREFERENCES.get(request.avatar_id, {})
    
    avatar_likes = request.avatar_likes or default_prefs.get("likes", [])
    avatar_dislikes = request.avatar_dislikes or default_prefs.get("dislikes", [])
    avatar_traits = request.avatar_traits or default_prefs.get("traits", [])
    
    # Analyze compatibility
    result = analyze_compatibility(
        user_likes=request.user.likes,
        user_dislikes=request.user.dislikes,
        avatar_likes=avatar_likes,
        avatar_dislikes=avatar_dislikes,
        user_traits=request.user.personality_traits,
        avatar_traits=avatar_traits
    )
    
    return CompatibilityResponse(
        avatar_id=request.avatar_id,
        avatar_name_ko=avatar.get("name_ko", ""),
        score=result["score"],
        chemistry_level=result["chemistry_level"],
        common_interests=[CompatibilityMatch(**m) for m in result["common_interests"]],
        suggested_topics=result["suggested_topics"],
        avoid_topics=result["avoid_topics"],
        personality_match=result["personality_match"],
        summary_ko=result["summary_ko"],
        summary_en=result["summary_en"],
        match_reasons=result["match_reasons"],
        ml_available=result["ml_available"]
    )


@router.post("/batch", response_model=BatchCompatibilityResponse)
async def analyze_all_avatars_compatibility(request: BatchCompatibilityRequest):
    """
    Analyze compatibility with all system avatars.
    
    Returns a ranked list of avatars sorted by compatibility score.
    Useful for showing "recommended avatars" to the user.
    """
    
    results = []
    analyzer = get_compatibility_analyzer()
    
    for avatar_id, avatar in AVATARS.items():
        # Get avatar preferences
        prefs = AVATAR_PREFERENCES.get(avatar_id, {})
        
        # Analyze
        result = analyze_compatibility(
            user_likes=request.user.likes,
            user_dislikes=request.user.dislikes,
            avatar_likes=prefs.get("likes", []),
            avatar_dislikes=prefs.get("dislikes", []),
            user_traits=request.user.personality_traits,
            avatar_traits=prefs.get("traits", [])
        )
        
        results.append(AvatarCompatibility(
            avatar_id=avatar_id,
            avatar_name_ko=avatar.get("name_ko", ""),
            avatar_role=avatar.get("role", ""),
            score=result["score"],
            chemistry_level=result["chemistry_level"],
            common_interests=[CompatibilityMatch(**m) for m in result["common_interests"][:3]],
            summary_ko=result["summary_ko"]
        ))
    
    # Sort by score (highest first)
    results.sort(key=lambda x: x.score, reverse=True)
    
    return BatchCompatibilityResponse(
        user_likes=request.user.likes,
        results=results,
        ml_available=analyzer.is_ml_available
    )


@router.get("/avatar/{avatar_id}/preferences")
async def get_avatar_preferences(avatar_id: str):
    """
    Get an avatar's predefined preferences (likes, dislikes, traits).
    """
    
    avatar = AVATARS.get(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail=f"Avatar not found: {avatar_id}")
    
    prefs = AVATAR_PREFERENCES.get(avatar_id, {})
    
    return {
        "avatar_id": avatar_id,
        "avatar_name_ko": avatar.get("name_ko", ""),
        "likes": prefs.get("likes", []),
        "dislikes": prefs.get("dislikes", []),
        "personality_traits": prefs.get("traits", [])
    }


@router.get("/status")
async def get_compatibility_status():
    """
    Check if ML model is loaded and ready.
    """
    analyzer = get_compatibility_analyzer()
    
    return {
        "ml_available": analyzer.is_ml_available,
        "model": "jhgan/ko-sroberta-multitask" if analyzer.is_ml_available else "fallback",
        "cache_size": len(analyzer.embedding_cache)
    }
