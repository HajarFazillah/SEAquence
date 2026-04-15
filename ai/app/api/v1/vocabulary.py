"""
Vocabulary API Endpoints

Spaced repetition vocabulary learning.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.services.vocabulary_service import (
    vocabulary_service,
    VocabItem,
    VocabType,
    MasteryLevel,
    ReviewSession,
    VocabStats,
)


router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])


# ============================================================================
# Request/Response Models
# ============================================================================

class AddVocabRequest(BaseModel):
    """Request to add vocabulary"""
    user_id: str
    korean: str
    meaning: str
    type: str = "word"  # word/phrase/grammar
    example: Optional[str] = None
    source_avatar_id: Optional[str] = None
    source_avatar_name: Optional[str] = None


class ExtractVocabRequest(BaseModel):
    """Request to extract vocab from conversation"""
    user_id: str
    avatar_id: str
    avatar_name: str
    messages: List[dict]  # [{"role": "user/assistant", "content": "..."}]


class RecordReviewRequest(BaseModel):
    """Request to record a review result"""
    user_id: str
    vocab_id: str
    correct: bool
    response_time_ms: Optional[int] = None
    hint_used: bool = False


class VocabResponse(BaseModel):
    """Single vocabulary item response"""
    id: str
    korean: str
    meaning: str
    type: str
    example: Optional[str]
    
    mastery_score: int
    mastery_level: str
    streak: int
    
    interval_days: int
    next_review: datetime
    last_reviewed: Optional[datetime]
    
    correct_count: int
    incorrect_count: int
    
    source_avatar_name: Optional[str]
    created_at: datetime


class VocabListResponse(BaseModel):
    """List of vocabulary items"""
    items: List[VocabResponse]
    total: int


class ReviewSessionResponse(BaseModel):
    """Review session response"""
    session_id: str
    items: List[VocabResponse]
    total_items: int


class StatsResponse(BaseModel):
    """Vocabulary statistics"""
    total_words: int
    total_phrases: int
    total_grammar: int
    
    mastered_count: int
    reviewing_count: int
    learning_count: int
    new_count: int
    
    due_today: int
    words_learned_this_week: int
    review_accuracy: float


def vocab_to_response(item: VocabItem) -> VocabResponse:
    """Convert VocabItem to response"""
    return VocabResponse(
        id=item.id,
        korean=item.korean,
        meaning=item.meaning,
        type=item.type.value,
        example=item.example,
        mastery_score=item.mastery_score,
        mastery_level=item.mastery_level.value,
        streak=item.streak,
        interval_days=item.interval_days,
        next_review=item.next_review,
        last_reviewed=item.last_reviewed,
        correct_count=item.correct_count,
        incorrect_count=item.incorrect_count,
        source_avatar_name=item.source_avatar_name,
        created_at=item.created_at,
    )


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/add", response_model=VocabResponse)
async def add_vocabulary(request: AddVocabRequest):
    """
    Add a new vocabulary item.
    
    Types:
    - word: 단어
    - phrase: 표현/문장
    - grammar: 문법 패턴
    """
    try:
        item = await vocabulary_service.add_vocabulary(
            user_id=request.user_id,
            korean=request.korean,
            meaning=request.meaning,
            vocab_type=VocabType(request.type),
            example=request.example,
            source_avatar_id=request.source_avatar_id,
            source_avatar_name=request.source_avatar_name,
        )
        return vocab_to_response(item)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract", response_model=VocabListResponse)
async def extract_from_conversation(request: ExtractVocabRequest):
    """
    Extract vocabulary from a conversation.
    
    Uses AI to identify useful words and expressions.
    """
    try:
        items = await vocabulary_service.add_from_conversation(
            user_id=request.user_id,
            conversation_messages=request.messages,
            avatar_id=request.avatar_id,
            avatar_name=request.avatar_name,
        )
        
        return VocabListResponse(
            items=[vocab_to_response(i) for i in items],
            total=len(items),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review", response_model=VocabResponse)
async def record_review(request: RecordReviewRequest):
    """
    Record a review result.
    
    Updates the spaced repetition schedule based on:
    - Whether the answer was correct
    - Response time
    - Whether a hint was used
    """
    try:
        item = vocabulary_service.record_review(
            user_id=request.user_id,
            vocab_id=request.vocab_id,
            correct=request.correct,
            response_time_ms=request.response_time_ms,
            hint_used=request.hint_used,
        )
        
        if not item:
            raise HTTPException(status_code=404, detail="Vocabulary item not found")
        
        return vocab_to_response(item)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/due", response_model=VocabListResponse)
async def get_due_reviews(
    user_id: str,
    limit: int = Query(default=20, le=50),
):
    """
    Get vocabulary items due for review.
    
    Returns items sorted by urgency.
    """
    items = vocabulary_service.get_due_reviews(user_id, limit)
    return VocabListResponse(
        items=[vocab_to_response(i) for i in items],
        total=len(items),
    )


@router.get("/{user_id}/session", response_model=ReviewSessionResponse)
async def get_review_session(
    user_id: str,
    count: int = Query(default=10, le=30),
):
    """
    Get a review session.
    
    Returns a shuffled set of items due for review.
    """
    session = vocabulary_service.get_review_session(user_id, count)
    
    return ReviewSessionResponse(
        session_id=session.id,
        items=[vocab_to_response(i) for i in session.items],
        total_items=session.total_items,
    )


@router.get("/{user_id}/stats", response_model=StatsResponse)
async def get_stats(user_id: str):
    """
    Get vocabulary statistics for a user.
    
    Includes:
    - Total counts by type
    - Mastery level breakdown
    - Items due today
    - Weekly progress
    - Accuracy rate
    """
    stats = vocabulary_service.get_stats(user_id)
    
    return StatsResponse(
        total_words=stats.total_words,
        total_phrases=stats.total_phrases,
        total_grammar=stats.total_grammar,
        mastered_count=stats.mastered_count,
        reviewing_count=stats.reviewing_count,
        learning_count=stats.learning_count,
        new_count=stats.new_count,
        due_today=stats.due_today,
        words_learned_this_week=stats.words_learned_this_week,
        review_accuracy=stats.review_accuracy,
    )


@router.get("/{user_id}/all", response_model=VocabListResponse)
async def get_all_vocabulary(
    user_id: str,
    type: Optional[str] = None,
    level: Optional[str] = None,
):
    """
    Get all vocabulary for a user.
    
    Optionally filter by:
    - type: word/phrase/grammar
    - level: new/learning/reviewing/mastered
    """
    if level:
        items = vocabulary_service.get_vocabulary_by_level(
            user_id, 
            MasteryLevel(level)
        )
    else:
        items = vocabulary_service.get_all_vocabulary(user_id)
    
    if type:
        items = [i for i in items if i.type.value == type]
    
    return VocabListResponse(
        items=[vocab_to_response(i) for i in items],
        total=len(items),
    )


@router.delete("/{user_id}/{vocab_id}")
async def delete_vocabulary(user_id: str, vocab_id: str):
    """Delete a vocabulary item"""
    success = vocabulary_service.delete_vocabulary(user_id, vocab_id)
    if success:
        return {"status": "deleted", "vocab_id": vocab_id}
    raise HTTPException(status_code=404, detail="Vocabulary item not found")


# ============================================================================
# Batch Operations
# ============================================================================

class BatchAddRequest(BaseModel):
    """Batch add vocabulary"""
    user_id: str
    items: List[dict]  # [{"korean": "...", "meaning": "...", "type": "word"}]


@router.post("/batch-add", response_model=VocabListResponse)
async def batch_add_vocabulary(request: BatchAddRequest):
    """Add multiple vocabulary items at once"""
    added = []
    
    for item in request.items:
        try:
            vocab = await vocabulary_service.add_vocabulary(
                user_id=request.user_id,
                korean=item.get("korean", ""),
                meaning=item.get("meaning", ""),
                vocab_type=VocabType(item.get("type", "word")),
                example=item.get("example"),
            )
            added.append(vocab)
        except Exception:
            continue
    
    return VocabListResponse(
        items=[vocab_to_response(i) for i in added],
        total=len(added),
    )


class BatchReviewRequest(BaseModel):
    """Batch record reviews"""
    user_id: str
    reviews: List[dict]  # [{"vocab_id": "...", "correct": true}]


class BatchReviewResponse(BaseModel):
    """Batch review response"""
    processed: int
    updated_items: List[VocabResponse]


@router.post("/batch-review", response_model=BatchReviewResponse)
async def batch_record_reviews(request: BatchReviewRequest):
    """Record multiple review results at once"""
    updated = []
    
    for review in request.reviews:
        try:
            item = vocabulary_service.record_review(
                user_id=request.user_id,
                vocab_id=review.get("vocab_id", ""),
                correct=review.get("correct", False),
                response_time_ms=review.get("response_time_ms"),
                hint_used=review.get("hint_used", False),
            )
            if item:
                updated.append(item)
        except Exception:
            continue
    
    return BatchReviewResponse(
        processed=len(updated),
        updated_items=[vocab_to_response(i) for i in updated],
    )
