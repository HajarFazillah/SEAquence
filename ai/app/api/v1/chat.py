"""
Chat API Endpoints
Conversation management with avatars
"""

from fastapi import APIRouter, HTTPException

from app.schemas.schemas import (
    ChatStartRequest,
    ChatStartResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatEndRequest,
    ChatSummary,
    UserMessage,
    AvatarMessage,
    MessageFeedback,
)
from app.services.chat_service import chat_service

router = APIRouter()


@router.post("/start", response_model=ChatStartResponse)
async def start_chat(request: ChatStartRequest):
    """
    Start a new chat session with an avatar.
    
    Returns session ID and avatar's greeting message.
    """
    result = await chat_service.start_session(
        user_id=request.user_id,
        avatar_id=request.avatar_id,
        topic=request.topic,
        korean_level=request.korean_level
    )
    
    return ChatStartResponse(**result)


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(request: ChatMessageRequest):
    """
    Send a message in an active chat session.
    
    Returns avatar's response and optional politeness feedback.
    Set include_audio=true to get TTS audio of the response.
    """
    try:
        result = await chat_service.send_message(
            session_id=request.session_id,
            message=request.message,
            include_feedback=request.include_feedback,
            include_audio=request.include_audio
        )
        
        # Convert to response model
        feedback = None
        if result["user_message"].get("feedback"):
            f = result["user_message"]["feedback"]
            feedback = MessageFeedback(
                level=f["level"],
                level_ko=f["level_ko"],
                score=f["score"],
                is_appropriate=f["is_appropriate"],
                feedback_ko=f.get("feedback_ko"),
                feedback_en=f.get("feedback_en")
            )
        
        return ChatMessageResponse(
            session_id=result["session_id"],
            user_message=UserMessage(
                content=result["user_message"]["content"],
                feedback=feedback
            ),
            avatar_response=AvatarMessage(
                content=result["avatar_response"]["content"],
                avatar_name=result["avatar_response"]["avatar_name"],
                audio=result["avatar_response"].get("audio"),
                audio_format=result["avatar_response"].get("audio_format")
            ),
            turn_count=result["turn_count"],
            current_topic=result.get("current_topic")
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/end", response_model=ChatSummary)
async def end_chat(request: ChatEndRequest):
    """
    End a chat session and get summary.
    
    Returns statistics and improvement suggestions.
    """
    try:
        result = await chat_service.end_session(request.session_id)
        return ChatSummary(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """
    Get information about an active session.
    """
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "avatar_id": session.avatar_id,
        "topic": session.topic,
        "turn_count": len([m for m in session.messages if m["role"] == "user"]),
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat()
    }
