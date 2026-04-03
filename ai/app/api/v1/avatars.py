"""
Avatars API Endpoints
Avatar information and management
"""

from typing import Optional
from fastapi import APIRouter, HTTPException

from app.schemas.schemas import (
    AvatarSummary,
    AvatarDetail,
    AvatarListResponse,
)
from app.core.constants import AVATARS, FORMALITY_INSTRUCTIONS

router = APIRouter()


@router.get("", response_model=AvatarListResponse)
async def list_avatars(
    difficulty: Optional[str] = None,
    role: Optional[str] = None
):
    """
    List all available avatars.
    
    Filter by difficulty (easy/medium/hard) or role (friend/senior/professor).
    """
    avatars = []
    
    for avatar_id, data in AVATARS.items():
        # Apply filters
        if difficulty and data["difficulty"] != difficulty:
            continue
        if role and data["role"] != role:
            continue
        
        avatars.append(AvatarSummary(
            id=data["id"],
            name_ko=data["name_ko"],
            name_en=data["name_en"],
            role=data["role"],
            difficulty=data["difficulty"],
            formality=data["formality"]
        ))
    
    return AvatarListResponse(avatars=avatars, total=len(avatars))


@router.get("/{avatar_id}", response_model=AvatarDetail)
async def get_avatar(avatar_id: str):
    """
    Get detailed information about a specific avatar.
    """
    if avatar_id not in AVATARS:
        raise HTTPException(status_code=404, detail=f"Avatar not found: {avatar_id}")
    
    data = AVATARS[avatar_id]
    return AvatarDetail(
        id=data["id"],
        name_ko=data["name_ko"],
        name_en=data["name_en"],
        role=data["role"],
        age=data["age"],
        gender=data["gender"],
        personality=data["personality"],
        topics=data["topics"],
        difficulty=data["difficulty"],
        formality=data["formality"],
        greeting=data["greeting"]
    )


@router.get("/{avatar_id}/formality")
async def get_avatar_formality(avatar_id: str):
    """
    Get recommended formality level and tips for chatting with an avatar.
    """
    if avatar_id not in AVATARS:
        raise HTTPException(status_code=404, detail=f"Avatar not found: {avatar_id}")
    
    data = AVATARS[avatar_id]
    formality = data["formality"]
    
    tips_by_level = {
        "informal": [
            "반말을 사용하세요",
            "편하게 대화해도 됩니다",
            "친한 친구처럼 말하세요",
            "예: '뭐해?', '같이 가자'"
        ],
        "polite": [
            "존댓말(-요)을 사용하세요",
            "예의 바르지만 친근하게 대화하세요",
            "예: '뭐 해요?', '같이 가요'"
        ],
        "very_polite": [
            "격식체(-습니다)를 사용하세요",
            "최대한 공손하게 말하세요",
            "높임말을 적극 사용하세요",
            "예: '무엇을 하십니까?', '감사합니다'"
        ]
    }
    
    return {
        "avatar_id": avatar_id,
        "avatar_name": data["name_ko"],
        "role": data["role"],
        "recommended_formality": formality,
        "formality_ko": {"informal": "반말", "polite": "존댓말", "very_polite": "격식체"}[formality],
        "tips": tips_by_level.get(formality, []),
        "sample_endings": _get_sample_endings(formality)
    }


@router.get("/{avatar_id}/topics")
async def get_avatar_topics(avatar_id: str):
    """
    Get topics that an avatar can discuss.
    """
    if avatar_id not in AVATARS:
        raise HTTPException(status_code=404, detail=f"Avatar not found: {avatar_id}")
    
    data = AVATARS[avatar_id]
    return {
        "avatar_id": avatar_id,
        "avatar_name": data["name_ko"],
        "topics": data["topics"],
        "total_topics": len(data["topics"])
    }


def _get_sample_endings(formality: str) -> dict:
    """Get sample sentence endings for formality level."""
    endings = {
        "informal": {
            "statement": ["-어/아", "-지", "-야"],
            "question": ["-어?", "-냐?", "-니?"],
            "request": ["-어줘", "-해라"]
        },
        "polite": {
            "statement": ["-요", "-어요/아요"],
            "question": ["-요?", "-세요?"],
            "request": ["-주세요", "-해 주세요"]
        },
        "very_polite": {
            "statement": ["-습니다", "-ㅂ니다"],
            "question": ["-습니까?", "-ㅂ니까?"],
            "request": ["-주십시오", "-해 주시겠습니까?"]
        }
    }
    return endings.get(formality, endings["polite"])
