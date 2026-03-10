"""
Session-Aware Chat API Endpoints
For Backend integration with multi-avatar, multi-situation sessions
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any

from app.services.session_chat_service import session_chat_service
from app.schemas.session_schemas import (
    SessionChatRequest, SessionChatResponse,
    StartSessionRequest, StartSessionResponse,
    EndSessionRequest, EndSessionResponse,
    SessionKey
)

router = APIRouter(prefix="/session", tags=["Session Chat"])


# ===========================================
# Session Lifecycle
# ===========================================

@router.post("/start", response_model=StartSessionResponse)
async def start_session(request: StartSessionRequest):
    """
    Start a new conversation session.
    
    **Backend should:**
    1. Call this when user selects avatar + situation
    2. Create ChatSession record in DB with returned session_id
    3. Store the opening_message as first assistant message
    4. Display opening_message and tips to user
    
    **Returns:**
    - session_id: Unique session identifier
    - opening_message: Avatar's first line in this situation
    - situation_goals: Goals to achieve in this conversation
    - tips: Helpful tips for this situation
    """
    try:
        response = await session_chat_service.start_session(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=SessionChatResponse)
async def session_chat(request: SessionChatRequest):
    """
    Process a chat message within a session.
    
    **Backend should:**
    1. Load session from DB using session_id
    2. Load recent messages (last 10) from DB
    3. Build history array in format: [{role, content}, ...]
    4. Call this endpoint
    5. Store user message and AI response in DB
    6. Store mistakes_found and score with user's message
    7. Update session stats (message_count, etc.)
    8. Update goals_completed if new goals achieved
    
    **Request includes:**
    - message: User's current message
    - session_info: Session identification and state
    - history: Recent conversation history
    - situation_id: Current situation
    
    **Returns:**
    - response: Avatar's reply
    - mistakes_found: Analysis of user's Korean
    - score: Performance score (0-100)
    - goals_achieved: New goals completed this message
    - personalized_tips: Learning tips
    """
    try:
        response = await session_chat_service.chat(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/end", response_model=EndSessionResponse)
async def end_session(
    request: EndSessionRequest,
    session_data: Optional[Dict[str, Any]] = None
):
    """
    End a session and get summary.
    
    **Backend should:**
    1. Call this when user ends conversation or session times out
    2. Pass full session data (messages, stats, etc.)
    3. Store the returned summary in DB
    4. Update user's overall progress
    5. Update avatar-situation progress
    
    **session_data should include:**
    ```json
    {
        "user_id": "user123",
        "avatar_id": "hyunwoo_barista",
        "situation_id": "cafe_order",
        "messages": [
            {"role": "user", "content": "...", "mistakes": [...], "score": 85},
            {"role": "assistant", "content": "..."}
        ],
        "goals_completed": ["음료 주문하기", "결제하기"],
        "duration_seconds": 300
    }
    ```
    
    **Returns:**
    - summary: Complete session summary with stats, achievements, recommendations
    """
    if not session_data:
        session_data = {}
    
    try:
        response = await session_chat_service.end_session(request, session_data)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===========================================
# Helper Endpoints
# ===========================================

@router.get("/available/{user_id}/{avatar_id}")
async def get_available_situations(user_id: str, avatar_id: str):
    """
    Get available situations for an avatar.
    
    **Backend should:**
    - Call this to show situation selection screen
    - Include user's progress for each situation (from your DB)
    """
    from app.core.situations import get_situations_for_avatar
    
    situations = get_situations_for_avatar(avatar_id)
    
    return {
        "avatar_id": avatar_id,
        "situations": [
            {
                "situation_id": s.get("situation_id"),
                "name_ko": s.get("name_ko"),
                "name_en": s.get("name_en"),
                "difficulty": s.get("difficulty"),
                "opening_line": s.get("opening_line"),
                "goals": s.get("goals_ko", [])
            }
            for s in situations
        ],
        "total": len(situations)
    }


@router.post("/validate-formality")
async def validate_formality(
    message: str,
    situation_id: str,
    avatar_id: str
):
    """
    Quick formality check for a message.
    Useful for real-time feedback before sending.
    """
    from app.core.situations import get_situation
    from app.services.politeness_service import politeness_service
    
    situation = get_situation(situation_id)
    expected = situation.get("expected_formality", "polite") if situation else "polite"
    
    analysis = politeness_service.analyze(message)
    detected = analysis.get("level", "polite")
    
    # Map formality names
    formality_map = {
        "casual": "informal",
        "polite": "polite", 
        "formal": "very_polite"
    }
    expected_mapped = formality_map.get(expected, expected)
    
    is_appropriate = detected == expected_mapped
    
    feedback = None
    if not is_appropriate:
        feedback_map = {
            ("formal", "polite"): "격식체(-습니다)를 사용해 주세요.",
            ("formal", "informal"): "격식체(-습니다)가 필요한 상황이에요.",
            ("polite", "informal"): "'-요'를 붙여 주세요.",
            ("casual", "polite"): "반말로 편하게 말해도 돼요!",
        }
        feedback = feedback_map.get((expected, detected), "")
    
    return {
        "message": message,
        "expected_formality": expected,
        "detected_formality": detected,
        "is_appropriate": is_appropriate,
        "feedback": feedback
    }
