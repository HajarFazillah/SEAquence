"""
Progress API
POST /api/v1/progress/profile          - Create/update user profile
GET  /api/v1/progress/profile/{id}     - Get user profile
GET  /api/v1/progress/skills/{id}      - Get skill levels
GET  /api/v1/progress/recommendations/{id} - Get recommendations
GET  /api/v1/progress/errors/{id}      - Get error patterns
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/progress", tags=["progress"])

# In-memory store
_profiles: dict = {}
_skills: dict = {}


class ProfileRequest(BaseModel):
    user_id: str
    korean_level: str = "intermediate"
    native_language: str = "en"
    interests: List[str] = []
    learning_goals: List[str] = []
    username: Optional[str] = None


class SkillUpdate(BaseModel):
    skill_type: str
    correct: bool


@router.post("/profile")
async def create_profile(request: ProfileRequest):
    """Create or update user profile."""
    profile = {
        "user_id": request.user_id,
        "username": request.username,
        "korean_level": request.korean_level,
        "native_language": request.native_language,
        "interests": request.interests,
        "learning_goals": request.learning_goals,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    _profiles[request.user_id] = profile
    return {"status": "ok", "profile": profile}


@router.get("/profile/{user_id}")
async def get_profile(user_id: str):
    """Get user profile."""
    profile = _profiles.get(user_id)
    if not profile:
        # Return default profile
        return {
            "user_id": user_id,
            "korean_level": "intermediate",
            "native_language": "en",
            "interests": [],
            "learning_goals": [],
        }
    return profile


@router.get("/skills/{user_id}")
async def get_skills(user_id: str):
    """Get user skill levels."""
    default_skills = {
        "user_id": user_id,
        "informal_speech": {"level": 3, "total_practice": 0},
        "polite_speech":   {"level": 2, "total_practice": 0},
        "formal_speech":   {"level": 2, "total_practice": 0},
        "honorifics":      {"level": 2, "total_practice": 0},
        "vocabulary":      {"level": 3, "total_practice": 0},
        "grammar":         {"level": 3, "total_practice": 0},
    }
    return _skills.get(user_id, default_skills)


@router.get("/recommendations/{user_id}")
async def get_recommendations(user_id: str):
    """Get personalized practice recommendations."""
    profile = _profiles.get(user_id, {})
    level = profile.get("korean_level", "intermediate")

    # Simple rule-based recommendations
    avatar_map = {
        "beginner":     {"avatar_id": "sujin_friend",   "topic_id": "daily_life"},
        "intermediate": {"avatar_id": "minsu_senior",   "topic_id": "campus_life"},
        "advanced":     {"avatar_id": "professor_kim",  "topic_id": "professor_meeting"},
    }
    rec = avatar_map.get(level, avatar_map["intermediate"])

    return {
        "user_id": user_id,
        "recommendations": {
            "avatar": {
                "avatar_id": rec["avatar_id"],
                "reason": f"Recommended for {level} level",
            },
            "topic": {
                "topic_id": rec["topic_id"],
                "reason": "Matches your learning goals",
            },
            "focus_skill": "polite_speech",
            "daily_goal_minutes": 10,
        },
        "generated_at": datetime.now().isoformat(),
    }


@router.get("/errors/{user_id}")
async def get_error_patterns(user_id: str):
    """Get user's common error patterns."""
    return {
        "user_id": user_id,
        "errors": [],
        "most_common": [],
        "total_mistakes": 0,
    }
