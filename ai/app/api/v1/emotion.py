"""
Emotion & Feedback API Endpoints
Provides avatar emotion and conversation status for UI
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.services.emotion_service import emotion_calculator, EmotionFeedback

router = APIRouter(prefix="/emotion", tags=["Emotion & Feedback"])


# ===========================================
# Request/Response Models
# ===========================================

class EmotionRequest(BaseModel):
    """Request for emotion calculation"""
    current_score: int
    mistakes: List[Dict[str, Any]] = []
    recent_scores: List[int] = []
    average_score: Optional[float] = None
    total_mistakes: int = 0
    message_count: int = 1
    goals_achieved: List[str] = []
    expected_formality: str = "polite"


class QuickEmotionRequest(BaseModel):
    """Quick emotion check with minimal data"""
    score: int
    mistake_count: int = 0
    goals_achieved: bool = False


# ===========================================
# Endpoints
# ===========================================

@router.post("/calculate")
async def calculate_emotion_feedback(request: EmotionRequest):
    """
    Calculate full emotion feedback based on conversation state.
    
    **Use this for:**
    - Getting avatar emotion after each message
    - Updating conversation status display
    - Showing warnings and tips
    
    **Returns:**
    - avatar_emotion: Current avatar emotional state
    - conversation_status: Overall conversation quality
    - warnings: List of warnings for mistakes
    - encouragement: Positive reinforcement message
    - tips: Learning tips based on mistakes
    """
    try:
        average = request.average_score or request.current_score
        
        result = emotion_calculator.calculate_full_feedback(
            current_score=request.current_score,
            mistakes=request.mistakes,
            recent_scores=request.recent_scores,
            average_score=average,
            total_mistakes=request.total_mistakes,
            message_count=request.message_count,
            goals_achieved=request.goals_achieved,
            expected_formality=request.expected_formality
        )
        
        return {
            "avatar_emotion": {
                "emotion": result.avatar_emotion.emotion.value,
                "emoji": result.avatar_emotion.emoji,
                "message_ko": result.avatar_emotion.message_ko,
                "message_en": result.avatar_emotion.message_en,
                "intensity": result.avatar_emotion.intensity
            },
            "conversation_status": {
                "status": result.conversation_status.status.value,
                "emoji": result.conversation_status.emoji,
                "label_ko": result.conversation_status.label_ko,
                "label_en": result.conversation_status.label_en,
                "color": result.conversation_status.color,
                "current_score": result.conversation_status.current_score,
                "average_score": result.conversation_status.average_score,
                "progress": result.conversation_status.progress
            },
            "warnings": [
                {
                    "level": w.level.value,
                    "emoji": w.emoji,
                    "color": w.color,
                    "message_ko": w.message_ko,
                    "message_en": w.message_en,
                    "category": w.category,
                    "original": w.original,
                    "suggestion": w.suggestion,
                    "show_correction": w.show_correction
                }
                for w in result.warnings
            ],
            "encouragement": result.encouragement,
            "tips": result.tips
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick")
async def quick_emotion_check(request: QuickEmotionRequest):
    """
    Quick emotion check with minimal data.
    
    **Use this for:**
    - Real-time emoji updates
    - Simple status displays
    
    **Input:**
    - score: Current message score (0-100)
    - mistake_count: Number of mistakes
    - goals_achieved: Whether a goal was achieved
    """
    # Simple emotion calculation
    if request.goals_achieved:
        emotion = "excited"
        emoji = "🤩"
        status = "perfect"
    elif request.score >= 90:
        emotion = "happy"
        emoji = "😊"
        status = "perfect"
    elif request.score >= 80:
        emotion = "happy"
        emoji = "😄"
        status = "excellent"
    elif request.score >= 70:
        emotion = "neutral"
        emoji = "🙂"
        status = "good"
    elif request.score >= 60:
        if request.mistake_count > 0:
            emotion = "thinking"
            emoji = "🤔"
        else:
            emotion = "neutral"
            emoji = "😐"
        status = "needs_practice"
    else:
        emotion = "encouraging"
        emoji = "💪"
        status = "struggling"
    
    return {
        "emotion": emotion,
        "emoji": emoji,
        "status": status,
        "score": request.score
    }


@router.get("/status-types")
async def get_status_types():
    """
    Get all available status types with their configurations.
    
    Useful for frontend to set up status indicators.
    """
    return {
        "statuses": {
            "perfect": {
                "emoji": "😊",
                "label_ko": "완벽한 대화",
                "label_en": "Perfect conversation",
                "color": "#4CAF50",
                "min_score": 90,
                "description": "No mistakes, excellent performance"
            },
            "excellent": {
                "emoji": "😄",
                "label_ko": "아주 좋아요",
                "label_en": "Excellent",
                "color": "#8BC34A",
                "min_score": 80,
                "description": "Minor mistakes, great performance"
            },
            "good": {
                "emoji": "🙂",
                "label_ko": "좋아요",
                "label_en": "Good",
                "color": "#CDDC39",
                "min_score": 70,
                "description": "Some mistakes, good effort"
            },
            "needs_practice": {
                "emoji": "😅",
                "label_ko": "연습이 필요해요",
                "label_en": "Needs practice",
                "color": "#FFC107",
                "min_score": 60,
                "description": "Several mistakes, keep trying"
            },
            "struggling": {
                "emoji": "😓",
                "label_ko": "힘내세요!",
                "label_en": "Keep trying!",
                "color": "#FF9800",
                "min_score": 0,
                "description": "Many mistakes, but don't give up!"
            }
        },
        "emotions": {
            "happy": {"emoji": "😊", "description": "User doing great"},
            "excited": {"emoji": "🤩", "description": "Goal achieved!"},
            "neutral": {"emoji": "😐", "description": "Normal conversation"},
            "thinking": {"emoji": "🤔", "description": "Minor mistake made"},
            "confused": {"emoji": "😕", "description": "Formality mismatch"},
            "concerned": {"emoji": "😟", "description": "User struggling"},
            "encouraging": {"emoji": "💪", "description": "Cheering user on"},
            "proud": {"emoji": "🥰", "description": "User improved a lot"}
        },
        "warning_levels": {
            "hint": {"emoji": "💡", "color": "#2196F3"},
            "mild": {"emoji": "📝", "color": "#FFC107"},
            "moderate": {"emoji": "⚠️", "color": "#FF9800"},
            "strong": {"emoji": "❗", "color": "#F44336"}
        }
    }


@router.post("/analyze-message")
async def analyze_message_emotion(
    message: str,
    expected_formality: str = "polite",
    context: Optional[str] = None
):
    """
    Analyze a message and return emotion feedback.
    
    This is a combined endpoint that:
    1. Analyzes the message for mistakes
    2. Calculates emotion based on analysis
    3. Returns everything needed for UI
    """
    from app.services.mistake_tracker import mistake_tracker
    from app.services.politeness_service import politeness_service
    
    # Analyze message
    mistakes = mistake_tracker.analyze_message(
        message=message,
        expected_formality=expected_formality
    )
    
    # Get politeness analysis
    politeness = politeness_service.analyze(message)
    
    # Calculate score
    score = 100
    for m in mistakes:
        severity = m.severity.value if hasattr(m, 'severity') else 'minor'
        if severity == "major":
            score -= 15
        elif severity == "moderate":
            score -= 10
        else:
            score -= 5
    
    # Formality check
    detected = politeness.get("level", "polite")
    formality_map = {"casual": "informal", "polite": "polite", "formal": "very_polite"}
    expected_mapped = formality_map.get(expected_formality, expected_formality)
    if detected != expected_mapped:
        score -= 10
    
    score = max(0, min(100, score))
    
    # Get emotion feedback
    result = emotion_calculator.calculate_full_feedback(
        current_score=score,
        mistakes=[m.dict() for m in mistakes],
        expected_formality=expected_formality
    )
    
    return {
        "message": message,
        "score": score,
        "mistakes": [m.dict() for m in mistakes],
        "politeness": politeness,
        "emotion_feedback": {
            "avatar_emotion": {
                "emotion": result.avatar_emotion.emotion.value,
                "emoji": result.avatar_emotion.emoji,
                "message_ko": result.avatar_emotion.message_ko,
                "message_en": result.avatar_emotion.message_en,
            },
            "conversation_status": {
                "status": result.conversation_status.status.value,
                "emoji": result.conversation_status.emoji,
                "label_ko": result.conversation_status.label_ko,
                "label_en": result.conversation_status.label_en,
                "color": result.conversation_status.color,
            },
            "warnings": [
                {
                    "emoji": w.emoji,
                    "message_ko": w.message_ko,
                    "original": w.original,
                    "suggestion": w.suggestion,
                }
                for w in result.warnings
            ],
            "encouragement": result.encouragement,
        }
    }
