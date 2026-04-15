"""
Avatars API
GET  /api/v1/avatars/           - List system avatars
GET  /api/v1/avatars/{id}       - Get avatar detail
POST /api/v1/avatars/create     - Create custom avatar
GET  /api/v1/avatars/user/{id}  - Get user's custom avatars
GET  /api/v1/avatars/{avatar_id}/situations - Get avatar situations
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.core.constants import AVATARS
from app.core.situations import AVATAR_SITUATIONS, SITUATIONS

router = APIRouter(prefix="/avatars", tags=["avatars"])

# In-memory store for custom avatars
_custom_avatars: dict = {}


class CreateAvatarRequest(BaseModel):
    user_id: str
    name: str
    name_ko: str
    role: str = "friend"
    age: Optional[int] = None
    personality: str = "친절한"
    formality: str = "polite"
    interests: List[str] = []
    topics: List[str] = []
    greeting: str = "안녕하세요!"


@router.get("/")
async def list_avatars():
    """List all system avatars."""
    avatars = []
    for aid, info in AVATARS.items():
        avatars.append({
            "avatar_id": aid,
            "name_ko": info["name_ko"],
            "name_en": info["name_en"],
            "role": info["role"],
            "difficulty": info["difficulty"],
            "formality": info["formality"],
            "topics": info["topics"],
            "greeting": info["greeting"],
        })
    return avatars


@router.get("/{avatar_id}")
async def get_avatar(avatar_id: str):
    """Get a specific avatar by ID."""
    avatar = AVATARS.get(avatar_id) or _custom_avatars.get(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail=f"Avatar '{avatar_id}' not found")
    return avatar


@router.post("/create")
async def create_avatar(request: CreateAvatarRequest):
    """Create a custom avatar."""
    import uuid
    avatar_id = f"custom_{uuid.uuid4().hex[:8]}"
    avatar = {
        "avatar_id": avatar_id,
        "name_ko": request.name_ko,
        "name_en": request.name,
        "role": request.role,
        "age": request.age,
        "personality": request.personality,
        "formality": request.formality,
        "interests": request.interests,
        "topics": request.topics,
        "greeting": request.greeting,
        "created_by": request.user_id,
        "is_system": False,
    }
    _custom_avatars[avatar_id] = avatar
    # Track per user
    user_key = f"user_{request.user_id}"
    if user_key not in _custom_avatars:
        _custom_avatars[user_key] = []
    _custom_avatars[user_key].append(avatar_id)
    return avatar


@router.get("/user/{user_id}")
async def get_user_avatars(user_id: str):
    """Get all custom avatars created by a user."""
    user_key = f"user_{user_id}"
    avatar_ids = _custom_avatars.get(user_key, [])
    avatars = [_custom_avatars[aid] for aid in avatar_ids if aid in _custom_avatars]
    return {"user_id": user_id, "custom_avatars": avatars, "total": len(avatars)}


@router.get("/{avatar_id}/situations")
async def get_avatar_situations(avatar_id: str):
    """Get situations available for an avatar."""
    situations = AVATAR_SITUATIONS.get(avatar_id, [])
    result = []
    for s in situations:
        sid = s.get("situation_id")
        base = SITUATIONS.get(sid, {})
        result.append({**base, **s})
    return {"avatar_id": avatar_id, "situations": result, "total": len(result)}
