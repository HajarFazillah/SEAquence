"""
Analysis API Endpoints
Politeness and relationship analysis
"""

from fastapi import APIRouter

from app.schemas.schemas import (
    PolitenessAnalyzeRequest,
    PolitenessResult,
)
from app.services.politeness_service import politeness_service
from app.core.constants import ROLE_LEVELS

router = APIRouter()


@router.post("/politeness", response_model=PolitenessResult)
async def analyze_politeness(request: PolitenessAnalyzeRequest):
    """
    Analyze politeness level of Korean text.
    
    Detects speech level (반말/존댓말/격식체) and provides
    feedback on appropriateness for the context.
    """
    result = politeness_service.analyze(
        text=request.text,
        target_role=request.target_role,
        target_age=request.target_age,
        user_age=request.user_age
    )
    
    return PolitenessResult(**result)


@router.post("/relationship")
async def analyze_relationship(
    user_role: str = "student",
    user_age: int = 22,
    avatar_role: str = "senior",
    avatar_age: int = 26
):
    """
    Analyze relationship between user and avatar.
    
    Returns recommended formality level and difficulty.
    """
    user_level = ROLE_LEVELS.get(user_role.lower(), 0)
    avatar_level = ROLE_LEVELS.get(avatar_role.lower(), 1)
    
    power_distance = avatar_level - user_level
    age_gap = avatar_age - user_age
    
    # Determine difficulty
    if avatar_level >= 3 or age_gap > 20:
        difficulty = "hard"
        difficulty_score = 0.8
    elif power_distance > 0 or age_gap > 5:
        difficulty = "medium"
        difficulty_score = 0.5
    else:
        difficulty = "easy"
        difficulty_score = 0.2
    
    # Determine formality
    if avatar_level >= 3:
        formality = "very_polite"
    elif power_distance > 0:
        formality = "polite"
    else:
        formality = "informal"
    
    return {
        "difficulty": difficulty,
        "difficulty_score": difficulty_score,
        "recommended_formality": formality,
        "power_distance": power_distance,
        "age_gap": age_gap,
        "tips": _get_relationship_tips(formality, avatar_role)
    }


@router.get("/formality-tips/{level}")
async def get_formality_tips(level: str):
    """
    Get tips for using a specific formality level.
    """
    tips = politeness_service.get_formality_tips(level)
    return tips


def _get_relationship_tips(formality: str, role: str) -> list:
    """Generate tips for the relationship."""
    tips = []
    
    if formality == "very_polite":
        tips.append("격식체(-습니다/-습니까)를 사용하세요")
        tips.append("높임 표현(드리다, 여쭙다)을 적극 활용하세요")
        if role == "professor":
            tips.append("'교수님'이라고 호칭하세요")
    elif formality == "polite":
        tips.append("존댓말(-요)을 기본으로 사용하세요")
        tips.append("친근하지만 예의 바르게 대화하세요")
        if role == "senior":
            tips.append("'선배(님)'이라고 호칭하세요")
    else:
        tips.append("반말을 사용해도 괜찮아요")
        tips.append("편하게 대화하세요")
    
    return tips
