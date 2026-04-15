"""
Integrated Chat API - full session lifecycle
POST /api/v1/integrated/start         - Start session
POST /api/v1/integrated/message       - Send message
POST /api/v1/integrated/end/{id}      - End session
GET  /api/v1/integrated/session/{id}  - Get session info
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

from app.core.constants import AVATARS, TOPIC_TAXONOMY
from app.services.clova_service import clova_service, Message
from app.services.politeness_service import politeness_service

router = APIRouter(prefix="/integrated", tags=["integrated"])

# In-memory session store
_sessions: dict = {}


class StartSessionRequest(BaseModel):
    user_id: str
    avatar_id: str
    topic: Optional[str] = None
    situation: Optional[str] = None
    include_revision: bool = True


class SendMessageRequest(BaseModel):
    session_id: str
    message: str
    include_revision: bool = True
    include_samples: bool = False


@router.post("/start")
async def start_session(request: StartSessionRequest):
    """Start an integrated chat session."""
    avatar = AVATARS.get(request.avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail=f"Avatar '{request.avatar_id}' not found")

    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    topic_name = TOPIC_TAXONOMY.get(request.topic or "", {}).get("name_ko", request.topic or "일상")

    session = {
        "session_id": session_id,
        "user_id": request.user_id,
        "avatar_id": request.avatar_id,
        "avatar_name": avatar["name_ko"],
        "topic": request.topic,
        "situation": request.situation,
        "history": [],
        "scores": [],
        "started_at": datetime.now().isoformat(),
        "formality": avatar.get("formality", "polite"),
    }
    _sessions[session_id] = session

    return {
        "session_id": session_id,
        "avatar_name": avatar["name_ko"],
        "avatar_role": avatar["role"],
        "opening_message": avatar.get("greeting", "안녕하세요!"),
        "topic": request.topic,
        "topic_name_ko": topic_name,
        "expected_formality": avatar.get("formality", "polite"),
        "status": "started",
    }


@router.post("/message")
async def send_message(request: SendMessageRequest):
    """Send a message in an integrated session."""
    session = _sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    avatar = AVATARS.get(session["avatar_id"], {})
    formality = session.get("formality", "polite")

    # Analyze user message
    analysis = politeness_service.analyze(
        text=request.message,
        target_role=avatar.get("role"),
    )

    score = analysis.get("score", 70)
    session["scores"].append(score)

    # Build CLOVA prompt
    formality_map = {
        "very_polite": "격식체(-습니다)를 사용하세요.",
        "polite":      "해요체(-요)를 사용하세요.",
        "informal":    "반말을 사용하세요.",
    }
    system_prompt = (
        f"당신은 '{avatar.get('name_ko', '아바타')}'입니다. "
        f"{avatar.get('personality', '')} "
        f"{formality_map.get(formality, '해요체를 사용하세요.')} "
        "짧고 자연스럽게 대화하세요."
    )

    history = session["history"][-10:]  # last 10 messages
    messages = [Message(role="system", content=system_prompt)]
    for h in history:
        messages.append(Message(role=h["role"], content=h["content"]))
    messages.append(Message(role="user", content=request.message))

    clova_response = await clova_service.chat(messages)
    avatar_reply = clova_response.content

    # Update history
    session["history"].append({"role": "user",      "content": request.message})
    session["history"].append({"role": "assistant",  "content": avatar_reply})

    # Build revision if requested
    revision = None
    if request.include_revision and not analysis.get("is_appropriate", True):
        from app.core.constants import FORMALITY_INSTRUCTIONS
        revision = {
            "original": request.message,
            "revised": request.message,  # placeholder — revision_service would improve this
            "has_error": True,
            "feedback": analysis.get("feedback_ko", ""),
        }

    return {
        "session_id": request.session_id,
        "user_message": {
            "content": request.message,
            "analysis": analysis,
        },
        "avatar_response": {
            "content": avatar_reply,
            "avatar_name": avatar.get("name_ko"),
        },
        "revision": revision,
        "turn_count": len(session["scores"]),
        "average_score": round(sum(session["scores"]) / len(session["scores"]), 1),
    }


@router.post("/end/{session_id}")
async def end_session(session_id: str):
    """End an integrated chat session and return summary."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    scores = session.get("scores", [0])
    avg = round(sum(scores) / len(scores), 1) if scores else 0

    session["ended_at"] = datetime.now().isoformat()

    return {
        "session_id": session_id,
        "summary": {
            "total_messages": len(scores),
            "average_score": avg,
            "best_score": max(scores) if scores else 0,
            "avatar_id": session["avatar_id"],
            "topic": session.get("topic"),
            "duration": "N/A",
        },
        "status": "ended",
    }


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session info."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
