"""
Integrated Chat API Endpoints
Chat + Analysis + Revision + Sample Replies in one flow
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


# ===========================================
# Request/Response Models
# ===========================================

class StartSessionRequest(BaseModel):
    """Request to start integrated chat session."""
    user_id: str
    avatar_id: str
    topic: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "user_id": "nalin",
                "avatar_id": "professor_kim",
                "topic": "professor_meeting",
                "user_context": {
                    "korean_level": "intermediate",
                    "weak_skills": ["formal_speech"]
                }
            }]
        }
    }


class SendMessageRequest(BaseModel):
    """Request to send message in integrated chat."""
    session_id: str
    message: str = Field(..., min_length=1, max_length=500)
    include_revision: bool = Field(default=True, description="Include sentence revision")
    include_samples: bool = Field(default=True, description="Include sample replies")


class IntegratedResponse(BaseModel):
    """Complete response with chat, analysis, revision, and samples."""
    session_id: str
    turn: int
    
    # User message analysis
    user_message: Dict[str, Any]
    
    # Avatar response
    avatar_response: Dict[str, Any]
    
    # Feedback
    feedback: Dict[str, str]
    
    # Optional: Revision
    revision: Optional[Dict[str, Any]] = None
    
    # Optional: Sample replies
    sample_replies: Optional[List[Dict[str, str]]] = None


# ===========================================
# Endpoints
# ===========================================

@router.post("/start")
async def start_integrated_session(request: StartSessionRequest):
    """
    Start an integrated chat session.
    
    This combines all features:
    - Avatar chat
    - Real-time politeness analysis
    - Sentence revision (when errors found)
    - Sample reply suggestions
    """
    from app.services.integrated_chat_service import integrated_chat_service
    
    result = await integrated_chat_service.start_session(
        user_id=request.user_id,
        avatar_id=request.avatar_id,
        topic=request.topic,
        user_context=request.user_context
    )
    
    return result


@router.post("/message", response_model=IntegratedResponse)
async def send_integrated_message(request: SendMessageRequest):
    """
    Send a message and get comprehensive response.
    
    Response includes:
    
    1. **user_message**: Your message with analysis
       - level: Detected formality (반말/존댓말/격식체)
       - score: Politeness score (0-100)
       - is_appropriate: Whether it matches the avatar
       - word_analysis: Which words are wrong
       - errors: List of errors found
    
    2. **avatar_response**: Avatar's reply
    
    3. **feedback**: Feedback in Korean and English
    
    4. **revision** (if errors found):
       - original: Your sentence
       - revised: Corrected sentence
       - errors: What was wrong
       - tips: How to improve
    
    5. **sample_replies** (if errors found):
       - Alternative ways to say the same thing correctly
    
    Example Flow:
    ```
    User: "교수님 질문 있어요" (wrong - should be formal)
    
    Response:
    - score: 65
    - is_appropriate: false
    - revision: "교수님, 질문이 있습니다"
    - sample_replies: [
        "교수님, 여쭤볼 것이 있습니다",
        "교수님, 질문 드려도 될까요?"
      ]
    - avatar_response: "네, 말씀해 보세요. 
        참고로 저한테는 '있습니다'라고 하시면 돼요."
    ```
    """
    from app.services.integrated_chat_service import integrated_chat_service
    
    try:
        result = await integrated_chat_service.send_message(
            session_id=request.session_id,
            message=request.message,
            include_revision=request.include_revision,
            include_samples=request.include_samples
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/end/{session_id}")
async def end_integrated_session(session_id: str):
    """
    End session and get comprehensive summary.
    
    Returns:
    - Session statistics
    - All revisions made during session
    - Improvement areas
    - Practice suggestions
    """
    from app.services.integrated_chat_service import integrated_chat_service
    
    try:
        result = await integrated_chat_service.get_session_summary(session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/quick-chat")
async def quick_chat(
    avatar_id: str,
    message: str,
    topic: Optional[str] = None
):
    """
    Quick one-shot chat without creating a session.
    
    Good for testing or single interactions.
    """
    from app.services.integrated_chat_service import integrated_chat_service
    
    # Create temporary session
    session = await integrated_chat_service.start_session(
        user_id="quick_user",
        avatar_id=avatar_id,
        topic=topic
    )
    
    # Send message
    result = await integrated_chat_service.send_message(
        session_id=session["session_id"],
        message=message,
        include_revision=True,
        include_samples=True
    )
    
    return result


# ===========================================
# Demo Endpoint
# ===========================================

@router.get("/demo")
async def demo_integrated_chat():
    """
    Demo showing how the integrated chat works.
    
    Shows example input/output for different scenarios.
    """
    return {
        "description": "Integrated Chat Demo",
        "features": [
            "Avatar chat with personality",
            "Real-time politeness analysis",
            "Sentence revision when errors found",
            "Sample reply suggestions"
        ],
        "example_scenarios": [
            {
                "scenario": "Talking to professor with wrong formality",
                "input": {
                    "avatar_id": "professor_kim",
                    "message": "교수님 질문 있어요"
                },
                "expected_output": {
                    "analysis": {
                        "level": "polite",
                        "expected": "very_polite",
                        "score": 65,
                        "is_appropriate": False
                    },
                    "revision": {
                        "original": "교수님 질문 있어요",
                        "revised": "교수님, 질문이 있습니다",
                        "error": "ending_mismatch"
                    },
                    "sample_replies": [
                        "교수님, 여쭤볼 것이 있습니다",
                        "교수님, 질문 드려도 될까요?"
                    ],
                    "avatar_response": "네, 말씀해 보세요."
                }
            },
            {
                "scenario": "Talking to friend correctly",
                "input": {
                    "avatar_id": "sujin_friend",
                    "message": "야 오늘 뭐해?"
                },
                "expected_output": {
                    "analysis": {
                        "level": "informal",
                        "expected": "informal",
                        "score": 90,
                        "is_appropriate": True
                    },
                    "revision": None,
                    "sample_replies": None,
                    "avatar_response": "나? 그냥 집에서 쉬려고~ 왜?"
                }
            }
        ],
        "api_endpoints": [
            "POST /api/v1/integrated/start - Start session",
            "POST /api/v1/integrated/message - Send message",
            "POST /api/v1/integrated/end/{session_id} - End session",
            "POST /api/v1/integrated/quick-chat - One-shot chat"
        ]
    }
