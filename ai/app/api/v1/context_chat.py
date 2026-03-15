"""
Context-Aware Chat API Endpoints
Provides personalized chat with mistake tracking
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from pydantic import BaseModel

from app.services.context_aware_chat import context_aware_chat
from app.services.session_memory import session_memory
from app.schemas.context_schemas import (
    ContextAwareChatRequest, ContextAwareChatResponse,
    MistakeSummary, UserLearningContext
)

router = APIRouter(prefix="/context-chat", tags=["Context-Aware Chat"])


# ==================== Request/Response Models ====================

class SimpleChatRequest(BaseModel):
    """Simplified chat request for quick testing"""
    message: str
    user_id: str = "test_user"
    avatar_id: str = "sujin_friend"
    topic: Optional[str] = None


class UserSummaryResponse(BaseModel):
    """User learning summary response"""
    user_id: str
    total_messages: int
    total_mistakes: int
    accuracy_rate: float
    top_problem_categories: list
    recommendations: list
    strengths: list
    estimated_level: str


# ==================== Endpoints ====================

@router.post("/chat", response_model=ContextAwareChatResponse)
async def context_aware_chat_endpoint(request: ContextAwareChatRequest):
    """
    Chat with context awareness and personalized feedback.
    
    This endpoint:
    - Analyzes user's Korean for mistakes
    - Tracks mistake patterns over time
    - Provides personalized tips based on history
    - Remembers user's progress across sessions
    
    **For Backend Integration:**
    - Pass `user_context` from your database for persistent tracking
    - Store the returned `updated_context` back to your database
    
    **For Demo/Testing:**
    - Just pass `user_id` or `session_id`
    - Context is maintained in memory (resets on server restart)
    """
    try:
        response = await context_aware_chat.chat(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simple", response_model=ContextAwareChatResponse)
async def simple_context_chat(request: SimpleChatRequest):
    """
    Simplified chat endpoint for quick testing.
    
    Just send a message and user_id - context is automatically managed.
    
    Example:
    ```
    POST /api/v1/context-chat/simple
    {
        "message": "안녕하세요! 저는 한국어를 배워요.",
        "user_id": "user123"
    }
    ```
    """
    full_request = ContextAwareChatRequest(
        message=request.message,
        user_id=request.user_id,
        avatar_id=request.avatar_id,
        topic=request.topic,
        include_mistake_feedback=True
    )
    
    try:
        response = await context_aware_chat.chat(full_request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{user_id}", response_model=UserSummaryResponse)
async def get_user_summary(user_id: str):
    """
    Get learning summary for a user.
    
    Returns:
    - Total messages and mistakes
    - Accuracy rate
    - Top problem areas
    - Personalized recommendations
    - Identified strengths
    """
    summary = context_aware_chat.get_user_summary(user_id)
    
    if not summary:
        raise HTTPException(
            status_code=404, 
            detail=f"No session found for user: {user_id}"
        )
    
    return UserSummaryResponse(
        user_id=user_id,
        **summary
    )


@router.get("/context/{user_id}")
async def get_user_context(user_id: str):
    """
    Get raw user learning context.
    
    Useful for:
    - Backend to retrieve and store user context
    - Debugging user's learning history
    """
    context = session_memory.get(user_id)
    
    if not context:
        raise HTTPException(
            status_code=404,
            detail=f"No session found for user: {user_id}"
        )
    
    return {
        "user_id": user_id,
        "context": context.dict()
    }


@router.delete("/context/{user_id}")
async def reset_user_context(user_id: str):
    """
    Reset user's learning context.
    
    Use this to:
    - Start fresh tracking for a user
    - Clear test data
    """
    success = context_aware_chat.reset_user_context(user_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"No session found for user: {user_id}"
        )
    
    return {"message": f"Context reset for user: {user_id}"}


@router.get("/stats")
async def get_session_stats():
    """
    Get session memory statistics.
    
    Returns:
    - Number of active sessions
    - Memory configuration
    """
    return session_memory.get_stats()


@router.post("/analyze")
async def analyze_message(
    message: str,
    expected_formality: str = "polite",
    user_id: Optional[str] = None
):
    """
    Analyze a Korean message for mistakes without chatting.
    
    Useful for:
    - Quick grammar/spelling checks
    - Testing mistake detection
    
    Args:
        message: Korean text to analyze
        expected_formality: Expected speech level (informal/polite/formal)
        user_id: Optional user ID for context-aware analysis
    """
    from app.services.mistake_tracker import mistake_tracker
    from app.services.politeness_service import politeness_service
    
    # Get user context if available
    context = None
    if user_id:
        context = session_memory.get(user_id)
    
    # Analyze for mistakes
    mistakes = mistake_tracker.analyze_message(
        message=message,
        expected_formality=expected_formality,
        context=context
    )
    
    # Get politeness analysis
    politeness = politeness_service.analyze(message)
    
    return {
        "message": message,
        "expected_formality": expected_formality,
        "mistakes_found": [m.dict() for m in mistakes],
        "mistake_count": len(mistakes),
        "politeness_analysis": politeness,
        "has_issues": len(mistakes) > 0
    }


# ==================== Backend Integration Helpers ====================

@router.post("/import-context")
async def import_user_context(context: UserLearningContext):
    """
    Import user context from backend database.
    
    Use this when:
    - User starts a new session
    - Backend wants to sync context to AI server
    
    The backend should:
    1. Load user's learning history from database
    2. Call this endpoint with the context
    3. Use /context-chat/chat for conversations
    4. Save updated_context back to database periodically
    """
    session_memory.update(context.user_id, context)
    
    return {
        "message": f"Context imported for user: {context.user_id}",
        "total_messages": context.total_messages,
        "total_mistakes": context.total_mistakes
    }


@router.get("/export-context/{user_id}")
async def export_user_context(user_id: str):
    """
    Export user context for backend storage.
    
    Backend should call this periodically or at session end
    to persist user's learning progress.
    """
    context = session_memory.get(user_id)
    
    if not context:
        raise HTTPException(
            status_code=404,
            detail=f"No session found for user: {user_id}"
        )
    
    return {
        "user_id": user_id,
        "context": context.dict(),
        "export_note": "Store this in your database. Import it when user returns."
    }
