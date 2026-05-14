"""
ML Analysis API
GET  /api/v1/ml/status          - ML component status
POST /api/v1/ml/topic           - Topic classification
POST /api/v1/ml/politeness      - Politeness analysis (ML)
POST /api/v1/ml/emotion         - Emotion detection
POST /api/v1/ml/intent          - Intent detection
POST /api/v1/ml/comprehensive   - Full combined analysis
POST /api/v1/ml/similarity      - Semantic similarity
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List
from dataclasses import asdict

from app.ml.unified_service import ml_service

router = APIRouter(prefix="/ml", tags=["ml"])


class TopicRequest(BaseModel):
    text: str
    conversation_history: Optional[List[str]] = None
    top_k: int = 3


class PolitenessRequest(BaseModel):
    text: str
    target_role: Optional[str] = None
    target_age: Optional[int] = None
    user_age: int = 22


class ComprehensiveRequest(BaseModel):
    text: str
    target_role: Optional[str] = None
    target_age: Optional[int] = None
    user_age: int = 22
    conversation_history: Optional[List[str]] = None
    avatar_formality: str = "polite"


class SimilarityRequest(BaseModel):
    text1: str
    text2: str


@router.get("/status")
async def get_ml_status():
    """Get status of all ML components."""
    status = ml_service.get_status()
    return {
        "ml_status": status,
        "available": any(status.values()),
    }


@router.post("/topic")
async def classify_topic(request: TopicRequest):
    """Classify the topic of Korean text."""
    result = ml_service.analyze_topic(
        text=request.text,
        conversation_history=request.conversation_history,
        top_k=request.top_k,
    )
    return result


@router.post("/politeness")
async def analyze_politeness(request: PolitenessRequest):
    """Analyze politeness level using ML."""
    result = ml_service.analyze_politeness(
        text=request.text,
        target_role=request.target_role,
        target_age=request.target_age,
        user_age=request.user_age,
    )
    return result


@router.post("/emotion")
async def detect_emotion(text: str = Query(...)):
    """Detect emotion in Korean text."""
    result = ml_service.analyze_emotion(text)
    return result


@router.post("/intent")
async def detect_intent(text: str = Query(...)):
    """Detect user intent in Korean text."""
    result = ml_service.analyze_intent(text)
    return result


@router.post("/comprehensive")
async def comprehensive_analysis(request: ComprehensiveRequest):
    """Full combined ML analysis."""
    result = ml_service.analyze_comprehensive(
        text=request.text,
        target_role=request.target_role,
        target_age=request.target_age,
        user_age=request.user_age,
        conversation_history=request.conversation_history,
        avatar_formality=request.avatar_formality,
    )
    return asdict(result)


@router.post("/similarity")
async def calculate_similarity(request: SimilarityRequest):
    """Calculate semantic similarity between two texts."""
    result = ml_service.calculate_similarity(request.text1, request.text2)
    return result
