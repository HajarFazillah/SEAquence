"""
Avatar Management API Endpoints
CRUD for avatars + user-avatar progress
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query

from app.schemas.avatar_schemas import (
    Avatar,
    AvatarCreate,
    AvatarUpdate,
    AvatarListResponse,
    UserAvatarProgress,
    UserAvatarSummary,
    EnhancedUserProfile,
    UserProfileUpdate,
)
from app.services.avatar_service import avatar_service

router = APIRouter()


# ===========================================
# Avatar CRUD
# ===========================================

@router.post("/create", response_model=Avatar)
async def create_avatar(
    data: AvatarCreate,
    user_id: Optional[str] = Query(None, description="User creating the avatar")
):
    """
    Create a new custom avatar.
    
    System avatars (minsu_senior, professor_kim, etc.) cannot be created,
    they are pre-defined.
    
    Example:
    ```json
    {
      "name_ko": "영희 선배",
      "name_en": "Younghee (Senior)",
      "role": "senior",
      "age": 25,
      "gender": "female",
      "personality": "활발하고 친절한 선배",
      "formality": "polite",
      "difficulty": "medium",
      "topics": ["campus_life", "career_future"],
      "greeting": "안녕! 오랜만이야~"
    }
    ```
    """
    try:
        avatar = avatar_service.create_avatar(data, created_by=user_id)
        return avatar
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list", response_model=AvatarListResponse)
async def list_avatars(
    include_system: bool = Query(True, description="Include system avatars"),
    include_custom: bool = Query(True, description="Include custom avatars"),
    created_by: Optional[str] = Query(None, description="Filter by creator"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    role: Optional[str] = Query(None, description="Filter by role")
):
    """
    List all available avatars.
    
    Filters:
    - include_system: Include default system avatars
    - include_custom: Include user-created avatars
    - created_by: Show only avatars created by specific user
    - difficulty: Filter by easy/medium/hard
    - role: Filter by junior/friend/senior/professor/boss
    """
    avatars = avatar_service.list_avatars(
        include_system=include_system,
        include_custom=include_custom,
        created_by=created_by,
        difficulty=difficulty,
        role=role
    )
    
    system_count = len([a for a in avatars if a.is_system])
    custom_count = len([a for a in avatars if not a.is_system])
    
    return AvatarListResponse(
        avatars=avatars,
        total=len(avatars),
        system_avatars=system_count,
        custom_avatars=custom_count
    )


@router.get("/system")
async def list_system_avatars():
    """Get only system (pre-defined) avatars."""
    avatars = avatar_service.get_system_avatars()
    return {
        "avatars": avatars,
        "total": len(avatars),
        "description": "These are the default avatars available to all users"
    }


@router.get("/custom/{user_id}")
async def list_user_custom_avatars(user_id: str):
    """Get avatars created by a specific user."""
    avatars = avatar_service.get_user_custom_avatars(user_id)
    return {
        "user_id": user_id,
        "avatars": avatars,
        "total": len(avatars)
    }


@router.get("/{avatar_id}", response_model=Avatar)
async def get_avatar(avatar_id: str):
    """Get detailed information about a specific avatar."""
    avatar = avatar_service.get_avatar(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail=f"Avatar not found: {avatar_id}")
    return avatar


@router.patch("/{avatar_id}", response_model=Avatar)
async def update_avatar(
    avatar_id: str,
    data: AvatarUpdate,
    user_id: Optional[str] = Query(None, description="User making the update")
):
    """
    Update a custom avatar.
    
    Note: System avatars cannot be modified.
    """
    try:
        avatar = avatar_service.update_avatar(avatar_id, data, user_id)
        if not avatar:
            raise HTTPException(status_code=404, detail="Avatar not found")
        return avatar
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{avatar_id}")
async def delete_avatar(
    avatar_id: str,
    user_id: Optional[str] = Query(None, description="User deleting the avatar")
):
    """
    Delete a custom avatar.
    
    Note: System avatars cannot be deleted.
    """
    try:
        success = avatar_service.delete_avatar(avatar_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Avatar not found")
        return {"status": "deleted", "avatar_id": avatar_id}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


# ===========================================
# User Profile (Enhanced)
# ===========================================

@router.post("/user/profile", response_model=EnhancedUserProfile)
async def create_user_profile(
    user_id: str,
    username: Optional[str] = None,
    native_language: str = "English",
    korean_level: str = "intermediate",
    interests: List[str] = [],
    learning_goals: List[str] = []
):
    """
    Create enhanced user profile with avatar tracking.
    
    This profile tracks:
    - User preferences
    - Avatars used
    - Progress with each avatar
    - Custom avatars created
    """
    profile = avatar_service.create_user_profile(
        user_id=user_id,
        username=username,
        native_language=native_language,
        korean_level=korean_level,
        interests=interests,
        learning_goals=learning_goals
    )
    return profile


@router.get("/user/profile/{user_id}", response_model=EnhancedUserProfile)
async def get_user_profile(user_id: str):
    """Get user profile with avatar progress."""
    profile = avatar_service.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile


@router.patch("/user/profile/{user_id}", response_model=EnhancedUserProfile)
async def update_user_profile(user_id: str, data: UserProfileUpdate):
    """Update user profile settings."""
    updates = data.model_dump(exclude_none=True)
    profile = avatar_service.update_user_profile(user_id, **updates)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile


# ===========================================
# User-Avatar Progress
# ===========================================

@router.get("/user/{user_id}/progress/{avatar_id}", response_model=UserAvatarProgress)
async def get_user_avatar_progress(user_id: str, avatar_id: str):
    """Get user's progress with a specific avatar."""
    progress = avatar_service.get_user_avatar_progress(user_id, avatar_id)
    if not progress:
        raise HTTPException(
            status_code=404, 
            detail=f"No progress found for user {user_id} with avatar {avatar_id}"
        )
    return progress


@router.get("/user/{user_id}/summary", response_model=UserAvatarSummary)
async def get_user_avatar_summary(user_id: str):
    """
    Get summary of user's interactions with all avatars.
    
    Returns:
    - Total avatars used
    - Favorite avatar (most sessions)
    - Progress with each avatar
    """
    summary = avatar_service.get_user_avatar_summary(user_id)
    return summary


@router.get("/user/{user_id}/recommend")
async def get_recommended_avatar(user_id: str):
    """
    Get recommended avatar for user based on their progress.
    
    Considers:
    - User's Korean level
    - Avatars already practiced with
    - Time since last practice with each avatar
    """
    avatar_id = avatar_service.get_recommended_avatar(user_id)
    avatar = avatar_service.get_avatar(avatar_id)
    
    return {
        "user_id": user_id,
        "recommended_avatar": avatar_id,
        "avatar_name": avatar.name_ko if avatar else avatar_id,
        "difficulty": avatar.difficulty if avatar else "medium",
        "reason": "Based on your Korean level and practice history"
    }


# ===========================================
# Quick Stats
# ===========================================

@router.get("/user/{user_id}/stats")
async def get_user_quick_stats(user_id: str):
    """Get quick stats for user dashboard."""
    profile = avatar_service.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    summary = avatar_service.get_user_avatar_summary(user_id)
    
    return {
        "user_id": user_id,
        "korean_level": profile.korean_level,
        "total_sessions": profile.total_sessions,
        "total_practice_minutes": profile.total_practice_minutes,
        "overall_average_score": round(profile.overall_average_score, 1),
        "avatars_used": len(profile.avatars_used),
        "custom_avatars_created": len(profile.custom_avatars),
        "favorite_avatar": summary.favorite_avatar,
        "last_active": profile.last_active
    }


# ===========================================
# Avatar Formality Tips
# ===========================================

@router.get("/{avatar_id}/tips")
async def get_avatar_tips(avatar_id: str):
    """Get conversation tips for a specific avatar."""
    avatar = avatar_service.get_avatar(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    formality = avatar.formality
    
    tips = {
        "informal": {
            "tips": [
                "반말을 사용하세요",
                "편하게 대화해도 됩니다",
                "'야', '뭐해?'처럼 친구에게 말하듯이"
            ],
            "endings": ["-어/아", "-지", "-냐"],
            "examples": ["뭐해?", "밥 먹었어?", "같이 가자"]
        },
        "polite": {
            "tips": [
                "존댓말(-요)을 사용하세요",
                "예의 바르지만 친근하게",
                "'요'를 붙이는 것을 잊지 마세요"
            ],
            "endings": ["-요", "-세요", "-죠"],
            "examples": ["뭐 해요?", "밥 먹었어요?", "같이 가요"]
        },
        "very_polite": {
            "tips": [
                "격식체(-습니다)를 사용하세요",
                "최대한 공손하게 말하세요",
                "높임말(드리다, 여쭙다)을 사용하세요"
            ],
            "endings": ["-습니다", "-습니까", "-십시오"],
            "examples": ["무엇을 하십니까?", "식사하셨습니까?"]
        }
    }
    
    return {
        "avatar_id": avatar_id,
        "avatar_name": avatar.name_ko,
        "role": avatar.role,
        "formality": formality,
        **tips.get(formality, tips["polite"])
    }
