"""
Personalized Chat API Endpoints
Chat with avatars using personalized feedback
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException

from app.schemas.user_schemas import (
    UserContext,
    PersonalizedChatRequest,
    PersonalizedFeedback,
)
from app.services.progress_service import progress_service
from app.services.personalized_feedback_service import personalized_feedback_service

router = APIRouter()


@router.post("/message/personalized")
async def send_personalized_message(request: PersonalizedChatRequest):
    """
    Send a chat message with personalized feedback.
    
    This endpoint:
    1. Analyzes the message for politeness
    2. Generates personalized feedback based on user context
    3. Updates error tracking
    4. Returns avatar response with adaptive feedback
    
    User context can be:
    - Provided in request (recommended for Backend integration)
    - Fetched from progress_service (if user_id exists)
    """
    from app.services.chat_service import chat_service
    from app.services.enhanced_politeness_service import enhanced_politeness_service
    from app.core.constants import AVATARS
    
    # Get session
    session = chat_service.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    avatar = AVATARS.get(session.avatar_id)
    
    # Get or use provided user context
    user_context = request.user_context
    if not user_context:
        user_context = progress_service.get_user_context(session.user_id)
    
    # Analyze politeness with enhanced service
    analysis = enhanced_politeness_service.analyze(
        text=request.message,
        target_role=avatar["role"],
        target_age=avatar["age"]
    )
    
    # Get user's error history for personalization
    error_records = {}
    user_errors = progress_service.get_errors(user_context.user_id)
    if user_errors:
        error_records = {
            err_type: record.total_count 
            for err_type, record in user_errors.errors.items()
        }
    
    # Generate personalized feedback
    personalized = personalized_feedback_service.generate_feedback(
        analysis_result={
            "level": analysis.level,
            "score": analysis.score,
            "is_appropriate": analysis.is_appropriate,
            "errors": analysis.errors,
            "corrections": analysis.corrections,
            "recommended_level": analysis.recommended_level,
        },
        user_context=user_context,
        error_records=error_records
    )
    
    # Record errors for tracking
    for error in analysis.errors:
        progress_service.record_error(
            user_id=user_context.user_id,
            error_type=error["error_type"],
            name_ko=error["name_ko"],
            name_en=error["name_en"],
            context=f"{session.avatar_id}_{session.topic}"
        )
    
    # Update skill based on score
    skill_map = {
        "very_polite": "formal_speech",
        "polite": "polite_speech",
        "informal": "informal_speech"
    }
    target_skill = skill_map.get(avatar["formality"], "polite_speech")
    progress_service.update_skill(
        user_id=user_context.user_id,
        skill_type=target_skill,
        score=analysis.score
    )
    
    # Get avatar response (using regular chat service)
    chat_result = await chat_service.send_message(
        session_id=request.session_id,
        message=request.message,
        include_feedback=False,  # We have our own
        include_audio=request.include_audio
    )
    
    return {
        "session_id": request.session_id,
        "user_message": {
            "content": request.message,
            "analysis": {
                "level": analysis.level,
                "level_ko": analysis.level_ko,
                "score": analysis.score,
                "is_appropriate": analysis.is_appropriate,
                "word_analysis": analysis.word_analysis,
                "corrections": analysis.corrections,
                "errors": analysis.errors
            }
        },
        "avatar_response": chat_result["avatar_response"],
        "personalized_feedback": {
            "feedback_ko": personalized.feedback_ko,
            "feedback_en": personalized.feedback_en,
            "error_history_note": personalized.error_history_note,
            "tip_ko": personalized.personalized_tip_ko,
            "tip_en": personalized.personalized_tip_en,
            "progress_note": personalized.progress_note,
            "encouragement_ko": personalized.encouragement_ko,
            "encouragement_en": personalized.encouragement_en
        },
        "turn_count": chat_result["turn_count"],
        "current_topic": chat_result.get("current_topic")
    }


@router.post("/analyze/personalized")
async def analyze_with_personalization(
    text: str,
    target_role: str = "senior",
    user_id: Optional[str] = None,
    user_context: Optional[UserContext] = None
):
    """
    Analyze text with personalized feedback (without chat session).
    
    Useful for:
    - Practice mode
    - Real-time typing feedback
    - Testing before sending
    """
    from app.services.enhanced_politeness_service import enhanced_politeness_service
    from app.core.constants import ROLE_LEVELS
    
    # Get user context
    if not user_context and user_id:
        user_context = progress_service.get_user_context(user_id)
    
    if not user_context:
        user_context = UserContext(user_id=user_id or "anonymous")
    
    # Analyze
    analysis = enhanced_politeness_service.analyze(
        text=text,
        target_role=target_role
    )
    
    # Get error history
    error_records = {}
    if user_id:
        user_errors = progress_service.get_errors(user_id)
        if user_errors:
            error_records = {
                err_type: record.total_count 
                for err_type, record in user_errors.errors.items()
            }
    
    # Generate personalized feedback
    personalized = personalized_feedback_service.generate_feedback(
        analysis_result={
            "level": analysis.level,
            "score": analysis.score,
            "is_appropriate": analysis.is_appropriate,
            "errors": analysis.errors,
            "corrections": analysis.corrections,
            "recommended_level": analysis.recommended_level,
        },
        user_context=user_context,
        error_records=error_records
    )
    
    return {
        "analysis": {
            "level": analysis.level,
            "level_ko": analysis.level_ko,
            "score": analysis.score,
            "is_appropriate": analysis.is_appropriate,
            "level_breakdown": analysis.level_breakdown,
            "word_analysis": analysis.word_analysis,
            "corrections": analysis.corrections,
            "errors": analysis.errors
        },
        "personalized_feedback": {
            "feedback_ko": personalized.feedback_ko,
            "feedback_en": personalized.feedback_en,
            "error_history_note": personalized.error_history_note,
            "tip_ko": personalized.personalized_tip_ko,
            "tip_en": personalized.personalized_tip_en,
            "encouragement_ko": personalized.encouragement_ko
        }
    }


@router.post("/session/end/personalized")
async def end_session_with_summary(
    session_id: str,
    user_id: Optional[str] = None
):
    """
    End session and get personalized summary.
    
    Returns:
    - Session statistics
    - Personalized analysis
    - Improvement suggestions
    - Next practice recommendation
    """
    from app.services.chat_service import chat_service
    from app.services.recommendation_service import recommendation_service
    from app.schemas.user_schemas import SessionSummary
    from datetime import datetime
    
    # End session and get basic summary
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    user_id = user_id or session.user_id
    
    # Create session summary
    avg_score = sum(session.scores) / len(session.scores) if session.scores else 0
    session_summary = SessionSummary(
        session_id=session_id,
        avatar_id=session.avatar_id,
        topic=session.topic,
        average_score=avg_score,
        highest_score=max(session.scores) if session.scores else 0,
        lowest_score=min(session.scores) if session.scores else 0,
        total_messages=len([m for m in session.messages if m["role"] == "user"]),
        correct_messages=len([s for s in session.scores if s >= 70]),
        started_at=session.created_at.isoformat(),
        ended_at=datetime.now().isoformat(),
        duration_seconds=(datetime.now() - session.created_at).seconds
    )
    
    # Record session for progress tracking
    progress_service.record_session(user_id, session_summary)
    
    # Get updated context
    user_context = progress_service.get_user_context(user_id)
    progress = progress_service.get_progress(user_id)
    skills = progress_service.get_skills(user_id)
    errors = progress_service.get_errors(user_id)
    
    # Get next recommendation
    recommendations = recommendation_service.generate_recommendations(
        user_context=user_context,
        skills=skills,
        errors=errors,
        progress=progress,
        num_recommendations=1
    )
    
    next_practice = None
    if recommendations.recommended_practices:
        rec = recommendations.recommended_practices[0]
        next_practice = {
            "avatar_id": rec.recommended_avatar,
            "avatar_name": rec.avatar_name_ko,
            "topic": rec.recommended_topic,
            "reason": rec.reason_ko
        }
    
    # End the session
    basic_summary = await chat_service.end_session(session_id)
    
    return {
        "session_summary": {
            **basic_summary,
            "average_score": avg_score,
            "highest_score": session_summary.highest_score,
            "lowest_score": session_summary.lowest_score,
        },
        "personalized_summary": {
            "trend": user_context.trend,
            "improvement_rate": progress.improvement_rate if progress else 0,
            "total_sessions": progress.total_sessions if progress else 1,
            "overall_average": progress.overall_average_score if progress else avg_score,
            "weak_skills": user_context.weak_skills,
            "common_errors": user_context.common_errors,
        },
        "suggestions": basic_summary.get("suggestions", []),
        "personalized_tips": recommendations.personalized_tips,
        "motivation": recommendations.motivation_message_ko,
        "next_practice": next_practice,
        "daily_goals": recommendations.daily_goals
    }
