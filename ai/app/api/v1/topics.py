"""
Topics API
GET  /api/v1/topics/            - List all topics
POST /api/v1/topics/detect      - Detect topic from text
POST /api/v1/topics/recommend   - Recommend topics
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List

from app.services.topic_service import topic_service
from app.core.constants import TOPIC_TAXONOMY, get_safe_topics

router = APIRouter(prefix="/topics", tags=["topics"])


class DetectRequest(BaseModel):
    text: str
    top_k: int = 3
    include_sensitive: bool = False


class RecommendRequest(BaseModel):
    user_topics: List[str] = []
    avatar_topics: List[str] = []
    exclude_topics: List[str] = []
    context: Optional[str] = None
    top_k: int = 5


@router.get("/")
async def list_topics(include_sensitive: bool = Query(False)):
    """List all available conversation topics."""
    topics = []
    for tid, info in TOPIC_TAXONOMY.items():
        if info["sensitive"] and not include_sensitive:
            continue
        topics.append({
            "id": tid,
            "name_ko": info["name_ko"],
            "name_en": info["name_en"],
            "sensitive": info["sensitive"],
            "keyword_count": len(info.get("keywords", [])),
        })
    return {"topics": topics, "total": len(topics)}


@router.post("/detect")
async def detect_topic(request: DetectRequest):
    """Detect topics from text."""
    results = topic_service.detect(
        text=request.text,
        top_k=request.top_k,
        include_sensitive=request.include_sensitive,
    )
    return {"topics": results}


@router.post("/recommend")
async def recommend_topics(request: RecommendRequest):
    """Recommend topics based on user and avatar preferences."""
    result = topic_service.recommend(
        user_topics=request.user_topics,
        avatar_topics=request.avatar_topics,
        exclude_topics=request.exclude_topics,
        context=request.context,
        top_k=request.top_k,
    )
    return result
