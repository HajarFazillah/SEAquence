"""
Chat API Endpoints

Real-time correction during conversation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.schemas.avatar import AvatarCreate
from app.schemas.user import UserProfileCreate
from app.services.chat_service import (
    chat_service, 
    ChatMessage, 
    ChatResponse, 
    ConversationAnalysis,
    RealTimeCorrection,
    InlineCorrection,
)


router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Request for chat endpoint"""
    avatar: AvatarCreate
    user_message: str
    conversation_history: List[ChatMessage] = []
    user_profile: Optional[UserProfileCreate] = None
    situation: Optional[str] = None
    user_id: Optional[str] = "default"  # For streak tracking


class ChatAnalyzeRequest(BaseModel):
    """Request for conversation analysis"""
    avatar: AvatarCreate
    conversation_history: List[ChatMessage]


# Re-export response models for API docs
class CorrectionResponse(BaseModel):
    """Inline correction detail"""
    original: str
    corrected: str
    type: str
    severity: str
    explanation: str
    tip: Optional[str] = None


class RealTimeCorrectionResponse(BaseModel):
    """Real-time correction feedback"""
    original_message: str
    corrected_message: Optional[str] = None
    has_errors: bool = False
    corrections: List[CorrectionResponse] = []
    expected_speech_level: str
    detected_speech_level: Optional[str] = None
    speech_level_correct: bool = True
    accuracy_score: int = 100
    encouragement: Optional[str] = None
    streak_bonus: bool = False


class FullChatResponse(BaseModel):
    """Full chat response with correction"""
    # Avatar's response
    message: str
    
    # Real-time correction
    correction: Optional[RealTimeCorrectionResponse] = None
    
    # Avatar mood
    mood_change: int = 0
    current_mood: int = 100
    mood_emoji: str = "😊"
    
    # Help
    suggestions: List[str] = []
    hint: Optional[str] = None
    
    # Stats
    correct_streak: int = 0


@router.post("", response_model=FullChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message to avatar and get response with real-time correction.
    
    ## Returns
    - **message**: Avatar's response
    - **correction**: Real-time correction feedback
      - `has_errors`: Whether there are mistakes
      - `corrections`: List of inline corrections with explanations
      - `accuracy_score`: 0-100 score
      - `encouragement`: Positive feedback message
    - **mood_change**: How much avatar's mood changed (-10 to +8)
    - **current_mood**: Avatar's current mood (0-100)
    - **suggestions**: Example responses to help user
    - **correct_streak**: Consecutive correct messages
    
    ## Correction Types
    - `speech_level`: 말투 오류 (합쇼체/해요체/반말)
    - `grammar`: 문법 오류
    - `spelling`: 맞춤법 오류
    - `vocabulary`: 어휘 선택
    - `expression`: 자연스러운 표현
    - `honorific`: 존칭/호칭 오류
    
    ## Severity Levels
    - `info`: 참고 (더 좋은 표현 제안)
    - `warning`: 주의 (조금 어색함)
    - `error`: 오류 (명확한 실수)
    """
    try:
        response = await chat_service.generate_response(
            avatar=request.avatar,
            user_message=request.user_message,
            conversation_history=request.conversation_history,
            user_profile=request.user_profile,
            situation=request.situation,
            user_id=request.user_id or "default",
        )
        
        # Convert to response model
        correction_response = None
        if response.correction:
            correction_response = RealTimeCorrectionResponse(
                original_message=response.correction.original_message,
                corrected_message=response.correction.corrected_message,
                has_errors=response.correction.has_errors,
                corrections=[
                    CorrectionResponse(
                        original=c.original,
                        corrected=c.corrected,
                        type=c.type.value,
                        severity=c.severity.value,
                        explanation=c.explanation,
                        tip=c.tip,
                    )
                    for c in response.correction.corrections
                ],
                expected_speech_level=response.correction.expected_speech_level,
                detected_speech_level=response.correction.detected_speech_level,
                speech_level_correct=response.correction.speech_level_correct,
                accuracy_score=response.correction.accuracy_score,
                encouragement=response.correction.encouragement,
                streak_bonus=response.correction.streak_bonus,
            )
        
        return FullChatResponse(
            message=response.message,
            correction=correction_response,
            mood_change=response.mood_change,
            current_mood=response.current_mood,
            mood_emoji=response.mood_emoji,
            suggestions=response.suggestions,
            hint=response.hint,
            correct_streak=response.correct_streak,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=ConversationAnalysis)
async def analyze_conversation(request: ChatAnalyzeRequest):
    """
    Analyze a completed conversation.
    
    Returns comprehensive feedback including:
    - Scores (speech_accuracy, vocabulary, naturalness)
    - List of mistakes with corrections
    - Vocabulary to learn
    - Phrases to learn
    - Overall feedback
    """
    try:
        analysis = await chat_service.analyze_conversation(
            avatar=request.avatar,
            conversation_history=request.conversation_history,
        )
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class BioGenerateRequest(BaseModel):
    avatar: AvatarCreate


class BioResponse(BaseModel):
    bio: str


@router.post("/generate-bio", response_model=BioResponse)
async def generate_bio(request: BioGenerateRequest):
    """Generate AI bio/conversation guide for avatar."""
    try:
        bio = await chat_service.generate_avatar_bio(request.avatar)
        return BioResponse(bio=bio)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Quick correction check (without generating response)
class QuickCorrectionRequest(BaseModel):
    """Request for quick correction check"""
    message: str
    expected_speech_level: str = "polite"  # formal/polite/informal
    avatar_role: str = "friend"
    user_level: str = "intermediate"  # beginner/intermediate/advanced


@router.post("/check", response_model=RealTimeCorrectionResponse)
async def quick_correction_check(request: QuickCorrectionRequest):
    """
    Quick correction check without generating avatar response.
    
    Useful for:
    - Previewing corrections before sending
    - Learning mode / practice
    - Testing specific sentences
    """
    from app.schemas.avatar import SpeechLevel
    
    try:
        level_map = {
            "formal": SpeechLevel.FORMAL,
            "polite": SpeechLevel.POLITE,
            "informal": SpeechLevel.INFORMAL,
        }
        
        expected_level = level_map.get(request.expected_speech_level, SpeechLevel.POLITE)
        
        correction = await chat_service._analyze_realtime(
            user_message=request.message,
            expected_speech_level=expected_level,
            avatar_role=request.avatar_role,
            user_level=request.user_level,
        )
        
        return RealTimeCorrectionResponse(
            original_message=correction.original_message,
            corrected_message=correction.corrected_message,
            has_errors=correction.has_errors,
            corrections=[
                CorrectionResponse(
                    original=c.original,
                    corrected=c.corrected,
                    type=c.type.value,
                    severity=c.severity.value,
                    explanation=c.explanation,
                    tip=c.tip,
                )
                for c in correction.corrections
            ],
            expected_speech_level=correction.expected_speech_level,
            detected_speech_level=correction.detected_speech_level,
            speech_level_correct=correction.speech_level_correct,
            accuracy_score=correction.accuracy_score,
            encouragement=correction.encouragement,
            streak_bonus=False,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
