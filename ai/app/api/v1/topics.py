"""
Topics API Endpoints
"""

from fastapi import APIRouter, HTTPException

from app.schemas.schemas import (
    TopicDetectRequest,
    TopicDetectResponse,
    TopicResult,
    TopicRecommendRequest,
    TopicRecommendResponse,
)
from app.services.topic_service import topic_service
from app.core.constants import TOPIC_TAXONOMY

router = APIRouter()


@router.post("/detect", response_model=TopicDetectResponse)
async def detect_topics(request: TopicDetectRequest):
    """
    Detect topics from Korean text.
    
    Uses keyword matching to identify conversation topics.
    """
    results = topic_service.detect(
        text=request.text,
        top_k=request.top_k,
        include_sensitive=request.include_sensitive
    )
    
    return TopicDetectResponse(
        topics=[TopicResult(**r) for r in results]
    )


@router.post("/recommend", response_model=TopicRecommendResponse)
async def recommend_topics(request: TopicRecommendRequest):
    """
    Get topic recommendations based on user and avatar preferences.
    
    Excludes sensitive topics and prioritizes common interests.
    """
    result = topic_service.recommend(
        user_topics=request.user_topics,
        avatar_topics=request.avatar_topics,
        context=request.context,
        top_k=request.top_k
    )
    
    return TopicRecommendResponse(**result)


@router.get("/list")
async def list_topics(include_sensitive: bool = False):
    """
    List all available topics.
    """
    topics = []
    for tid, info in TOPIC_TAXONOMY.items():
        if info["sensitive"] and not include_sensitive:
            continue
        topics.append({
            "topic_id": tid,
            "name_ko": info["name_ko"],
            "name_en": info["name_en"],
            "is_sensitive": info["sensitive"],
            "keywords_sample": info["keywords"][:5]
        })
    
    return {
        "topics": topics,
        "total": len(topics),
        "sensitive_excluded": not include_sensitive
    }


@router.get("/{topic_id}")
async def get_topic(topic_id: str):
    """
    Get detailed information about a specific topic.
    """
    if topic_id not in TOPIC_TAXONOMY:
        raise HTTPException(status_code=404, detail=f"Topic not found: {topic_id}")
    
    info = TOPIC_TAXONOMY[topic_id]
    return {
        "topic_id": topic_id,
        "name_ko": info["name_ko"],
        "name_en": info["name_en"],
        "description": info["description"],
        "keywords": info["keywords"],
        "is_sensitive": info["sensitive"]
    }
