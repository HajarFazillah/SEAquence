"""
Progress & Personalization API Endpoints
User profiles, progress tracking, and recommendations
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException

from app.schemas.user_schemas import (
    UserProfile,
    UserProfileCreate,
    UserSkills,
    UserErrors,
    UserProgress,
    UserContext,
    UserRecommendations,
    PracticeRecommendation,
    SessionSummary,
    ProgressResponse,
)
from app.services.progress_service import progress_service
from app.services.recommendation_service import recommendation_service

router = APIRouter()


# ===========================================
# User Profile
# ===========================================

@router.post("/profile", response_model=UserProfile)
async def create_user_profile(request: UserProfileCreate):
    """
    Create a new user profile.
    
    This initializes:
    - User profile with preferences
    - Initial skill levels based on korean_level
    - Empty error tracking
    - Empty progress data
    """
    profile = progress_service.create_profile(
        user_id=request.user_id,
        native_language=request.native_language,
        korean_level=request.korean_level,
        interests=request.interests,
        learning_goals=request.learning_goals
    )
    return profile


@router.get("/profile/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: str):
    """Get user profile."""
    profile = progress_service.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile


@router.patch("/profile/{user_id}")
async def update_user_profile(
    user_id: str,
    native_language: Optional[str] = None,
    korean_level: Optional[str] = None,
    interests: Optional[List[str]] = None,
    learning_goals: Optional[List[str]] = None,
    feedback_language: Optional[str] = None,
    show_hints: Optional[bool] = None
):
    """Update user profile settings."""
    updates = {}
    if native_language:
        updates["native_language"] = native_language
    if korean_level:
        updates["korean_level"] = korean_level
    if interests is not None:
        updates["interests"] = interests
    if learning_goals is not None:
        updates["learning_goals"] = learning_goals
    if feedback_language:
        updates["feedback_language"] = feedback_language
    if show_hints is not None:
        updates["show_hints"] = show_hints
    
    profile = progress_service.update_profile(user_id, **updates)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"status": "updated", "profile": profile}


# ===========================================
# Skills
# ===========================================

@router.get("/skills/{user_id}", response_model=UserSkills)
async def get_user_skills(user_id: str):
    """Get user's skill levels."""
    skills = progress_service.get_skills(user_id)
    if not skills:
        raise HTTPException(status_code=404, detail="User not found")
    return skills


@router.get("/skills/{user_id}/weak")
async def get_weak_skills(user_id: str, n: int = 2):
    """Get user's weakest skills."""
    weak = progress_service.get_weak_skills(user_id, n)
    return {"user_id": user_id, "weak_skills": weak}


@router.get("/skills/{user_id}/strong")
async def get_strong_skills(user_id: str, n: int = 2):
    """Get user's strongest skills."""
    strong = progress_service.get_strong_skills(user_id, n)
    return {"user_id": user_id, "strong_skills": strong}


# ===========================================
# Errors
# ===========================================

@router.get("/errors/{user_id}", response_model=UserErrors)
async def get_user_errors(user_id: str):
    """Get user's error history."""
    errors = progress_service.get_errors(user_id)
    if not errors:
        return UserErrors(user_id=user_id, errors={})
    return errors


@router.get("/errors/{user_id}/common")
async def get_common_errors(user_id: str, n: int = 3):
    """Get user's most common errors."""
    common = progress_service.get_common_errors(user_id, n)
    return {"user_id": user_id, "common_errors": common}


# ===========================================
# Progress
# ===========================================

@router.get("/progress/{user_id}", response_model=UserProgress)
async def get_user_progress(user_id: str):
    """Get user's overall progress."""
    progress = progress_service.get_progress(user_id)
    if not progress:
        return UserProgress(user_id=user_id)
    return progress


@router.post("/progress/{user_id}/session")
async def record_session(user_id: str, session: SessionSummary):
    """
    Record a completed session.
    
    This updates:
    - Total sessions and messages
    - Average score
    - Score history
    - Improvement trend
    """
    progress_service.record_session(user_id, session)
    return {"status": "recorded", "session_id": session.session_id}


# ===========================================
# User Context (for API calls)
# ===========================================

@router.get("/context/{user_id}", response_model=UserContext)
async def get_user_context(user_id: str):
    """
    Get user context for personalized API calls.
    
    This is what Backend should send to AI server
    with each chat request for personalization.
    """
    context = progress_service.get_user_context(user_id)
    return context


# ===========================================
# Recommendations
# ===========================================

@router.get("/recommendations/{user_id}", response_model=UserRecommendations)
async def get_recommendations(user_id: str):
    """
    Get personalized practice recommendations.
    
    Based on:
    - Weak skills
    - Common errors
    - Learning goals
    - Interests
    - Progress trend
    """
    context = progress_service.get_user_context(user_id)
    skills = progress_service.get_skills(user_id)
    errors = progress_service.get_errors(user_id)
    progress = progress_service.get_progress(user_id)
    
    recommendations = recommendation_service.generate_recommendations(
        user_context=context,
        skills=skills,
        errors=errors,
        progress=progress
    )
    
    return recommendations


@router.get("/recommendations/{user_id}/quick")
async def get_quick_recommendation(user_id: str):
    """
    Get single quick recommendation for "Start Practice" button.
    """
    context = progress_service.get_user_context(user_id)
    skills = progress_service.get_skills(user_id)
    
    recommendations = recommendation_service.generate_recommendations(
        user_context=context,
        skills=skills,
        num_recommendations=1
    )
    
    if recommendations.recommended_practices:
        rec = recommendations.recommended_practices[0]
        return {
            "avatar_id": rec.recommended_avatar,
            "avatar_name": rec.avatar_name_ko,
            "topic": rec.recommended_topic,
            "topic_name": rec.topic_name_ko,
            "reason": rec.reason_ko,
            "difficulty": rec.difficulty
        }
    
    # Default recommendation
    return {
        "avatar_id": "sujin_friend",
        "avatar_name": "수진",
        "topic": "daily_life",
        "topic_name": "일상생활",
        "reason": "편하게 대화 연습해봐요!",
        "difficulty": "easy"
    }


# ===========================================
# Analytics
# ===========================================

@router.get("/analytics/{user_id}")
async def get_user_analytics(user_id: str):
    """
    Get comprehensive analytics for user dashboard.
    
    Includes:
    - Skill levels (for radar chart)
    - Error breakdown (for bar chart)
    - Score history (for line chart)
    - Overall stats
    """
    analytics = progress_service.get_analytics(user_id)
    if "error" in analytics:
        raise HTTPException(status_code=404, detail=analytics["error"])
    return analytics


# ===========================================
# Combined Response
# ===========================================

@router.get("/full/{user_id}", response_model=ProgressResponse)
async def get_full_progress(user_id: str):
    """
    Get complete user progress data.
    
    Combines profile, skills, errors, progress, and recommendations
    in a single response for dashboard.
    """
    profile = progress_service.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    context = progress_service.get_user_context(user_id)
    skills = progress_service.get_skills(user_id)
    errors = progress_service.get_errors(user_id) or UserErrors(user_id=user_id, errors={})
    progress = progress_service.get_progress(user_id) or UserProgress(user_id=user_id)
    
    recommendations = recommendation_service.generate_recommendations(
        user_context=context,
        skills=skills,
        errors=errors,
        progress=progress
    )
    
    return ProgressResponse(
        user_id=user_id,
        progress=progress,
        skills=skills,
        errors=errors,
        recommendations=recommendations
    )
