"""
Situation API Endpoints
Manage conversation situations/scenarios
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List

from app.core.situations import (
    SITUATIONS, 
    SITUATION_CATEGORIES,
    AVATAR_SITUATIONS,
    get_situation,
    get_situations_by_category,
    get_situations_for_avatar,
    get_avatar_situation
)

router = APIRouter(prefix="/situations", tags=["Situations"])


# ===========================================
# List Endpoints
# ===========================================

@router.get("/")
async def list_all_situations():
    """
    Get all available conversation situations.
    
    Returns:
        List of all situations with details
    """
    situations = list(SITUATIONS.values())
    return {
        "situations": situations,
        "total": len(situations),
        "categories": list(SITUATION_CATEGORIES.keys())
    }


@router.get("/categories")
async def list_categories():
    """
    Get all situation categories.
    
    Returns:
        List of categories with descriptions
    """
    return {
        "categories": SITUATION_CATEGORIES
    }


@router.get("/category/{category}")
async def get_situations_in_category(category: str):
    """
    Get all situations in a specific category.
    
    Args:
        category: casual, service, academic, professional, social
    """
    if category not in SITUATION_CATEGORIES:
        raise HTTPException(
            status_code=404,
            detail=f"Category not found: {category}. Available: {list(SITUATION_CATEGORIES.keys())}"
        )
    
    situations = get_situations_by_category(category)
    return {
        "category": category,
        "category_info": SITUATION_CATEGORIES[category],
        "situations": situations,
        "total": len(situations)
    }


@router.get("/{situation_id}")
async def get_situation_details(situation_id: str):
    """
    Get detailed information about a specific situation.
    
    Args:
        situation_id: Unique situation identifier
    """
    situation = get_situation(situation_id)
    
    if not situation:
        raise HTTPException(
            status_code=404,
            detail=f"Situation not found: {situation_id}"
        )
    
    # Find which avatars support this situation
    supported_avatars = []
    for avatar_id, avatar_situations in AVATAR_SITUATIONS.items():
        for s in avatar_situations:
            if s["situation_id"] == situation_id:
                supported_avatars.append({
                    "avatar_id": avatar_id,
                    "avatar_role_ko": s.get("avatar_role_ko"),
                    "opening_line": s.get("opening_line")
                })
    
    return {
        "situation": situation,
        "supported_avatars": supported_avatars
    }


# ===========================================
# Avatar-Situation Endpoints
# ===========================================

@router.get("/avatar/{avatar_id}")
async def get_avatar_situations(avatar_id: str):
    """
    Get all situations available for a specific avatar.
    
    Args:
        avatar_id: Avatar identifier
    """
    situations = get_situations_for_avatar(avatar_id)
    
    if not situations:
        return {
            "avatar_id": avatar_id,
            "situations": [],
            "message": "No situations configured for this avatar"
        }
    
    return {
        "avatar_id": avatar_id,
        "situations": situations,
        "total": len(situations)
    }


@router.get("/avatar/{avatar_id}/{situation_id}")
async def get_avatar_situation_config(avatar_id: str, situation_id: str):
    """
    Get specific avatar-situation configuration.
    
    Returns the combined situation info with avatar-specific settings
    like opening line and role.
    """
    config = get_avatar_situation(avatar_id, situation_id)
    
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Situation '{situation_id}' not found for avatar '{avatar_id}'"
        )
    
    return {
        "avatar_id": avatar_id,
        "situation_id": situation_id,
        "config": config
    }


# ===========================================
# Difficulty-based Endpoints
# ===========================================

@router.get("/difficulty/{level}")
async def get_situations_by_difficulty(level: str):
    """
    Get situations filtered by difficulty level.
    
    Args:
        level: easy, medium, hard
    """
    if level not in ["easy", "medium", "hard"]:
        raise HTTPException(
            status_code=400,
            detail="Level must be: easy, medium, or hard"
        )
    
    situations = [s for s in SITUATIONS.values() if s.get("difficulty") == level]
    
    return {
        "difficulty": level,
        "situations": situations,
        "total": len(situations)
    }


# ===========================================
# Recommendation Endpoints
# ===========================================

@router.get("/recommend")
async def recommend_situations(
    korean_level: str = "intermediate",
    interests: Optional[str] = None,  # comma-separated
    practiced: Optional[str] = None,  # comma-separated situation IDs already practiced
    limit: int = 3
):
    """
    Get recommended situations based on user profile.
    
    Args:
        korean_level: beginner, intermediate, advanced
        interests: Comma-separated topics user is interested in
        practiced: Comma-separated situation IDs user has already practiced
    """
    # Map korean level to difficulty
    level_to_difficulty = {
        "beginner": "easy",
        "intermediate": "medium",
        "advanced": "hard"
    }
    
    target_difficulty = level_to_difficulty.get(korean_level, "medium")
    
    # Parse inputs
    interest_list = interests.split(",") if interests else []
    practiced_list = practiced.split(",") if practiced else []
    
    # Score each situation
    scored = []
    for s in SITUATIONS.values():
        score = 0
        
        # Not yet practiced = higher score
        if s["situation_id"] not in practiced_list:
            score += 10
        
        # Matches difficulty
        if s.get("difficulty") == target_difficulty:
            score += 5
        elif target_difficulty == "medium":
            score += 3  # medium level can do easy/hard too
        
        # Matches interests
        for topic in s.get("related_topics", []):
            if topic in interest_list:
                score += 3
        
        scored.append((score, s))
    
    # Sort by score and take top N
    scored.sort(key=lambda x: x[0], reverse=True)
    recommended = [s for _, s in scored[:limit]]
    
    return {
        "korean_level": korean_level,
        "recommended": recommended,
        "total": len(recommended)
    }


# ===========================================
# Quick Start
# ===========================================

@router.get("/quickstart")
async def get_quickstart_situations():
    """
    Get recommended situations for new users.
    
    Returns easy situations perfect for beginners.
    """
    beginner_friendly = [
        SITUATIONS.get("cafe_chat"),
        SITUATIONS.get("cafe_order"),
        SITUATIONS.get("first_meeting"),
    ]
    
    return {
        "message": "추천 시작 상황 (Recommended for beginners)",
        "situations": [s for s in beginner_friendly if s],
        "tip": "Start with these easy situations to build confidence!"
    }
