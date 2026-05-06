"""
Chat API Endpoints

Real-time correction during conversation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.schemas.avatar import AvatarCreate
from app.schemas.user import UserProfileCreate
from app.services.chat_service import (
    chat_service, 
    ChatMessage, 
    ChatResponse, 
    ConversationAnalysis,
    RealTimeCorrection,
    InlineCorrection,
    StructuredMessageResult,
)


router = APIRouter(prefix="/chat", tags=["chat"])


class CorrectionContextFeedback(BaseModel):
    """Frontend-provided correction hint for the latest user turn."""
    verdict: Optional[str] = None
    has_errors: bool = False
    accuracy_score: Optional[int] = None
    detected_speech_level: Optional[str] = None
    detected_speech_level_code: Optional[str] = None
    summary: Optional[str] = None
    corrections: List[Dict[str, Any]] = Field(default_factory=list)


class CorrectionContextMistake(BaseModel):
    """Recent mistake hint from the current frontend session."""
    message: str
    corrected: str
    verdict: Optional[str] = None
    summary: Optional[str] = None


class CorrectionContext(BaseModel):
    """Optional context payload used to make chat replies correction-aware."""
    session_id: Optional[str] = None
    expected_speech_level_code: Optional[str] = None
    expected_speech_level_label: Optional[str] = None
    latest_user_message: Optional[str] = None
    corrected_user_message: Optional[str] = None
    latest_feedback: Optional[CorrectionContextFeedback] = None
    recent_mistakes: List[CorrectionContextMistake] = Field(default_factory=list)
    response_guidance: List[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    """Request for chat endpoint"""
    avatar: AvatarCreate
    user_message: str
    conversation_history: List[ChatMessage] = []
    user_profile: Optional[UserProfileCreate] = None
    situation: Optional[str] = None
    user_id: Optional[str] = "default"  # For streak tracking
    session_id: Optional[str] = None
    expected_speech_level: Optional[str] = None
    correction_context: Optional[CorrectionContext] = None
    response_instruction: List[str] = Field(default_factory=list)


class ChatAnalyzeRequest(BaseModel):
    """Request for conversation analysis"""
    avatar: AvatarCreate
    conversation_history: List[ChatMessage]


class AnalyzeMessageRequest(BaseModel):
    """Structured analysis request for one user message."""
    avatar: AvatarCreate
    user_message: str
    conversation_history: List[ChatMessage] = []
    user_profile: Optional[UserProfileCreate] = None
    situation: Optional[str] = None
    user_id: Optional[str] = "default"
    session_id: Optional[str] = None
    expected_speech_level: Optional[str] = None
    correction_context: Optional[CorrectionContext] = None
    response_instruction: List[str] = Field(default_factory=list)
    include_reply: bool = True


class ConversationAnalysisResponse(BaseModel):
    """Conversation analysis with score provenance."""
    scores: Dict[str, int]
    mistakes: List[Dict[str, str]]
    vocabulary_to_learn: List[Dict[str, str]]
    phrases_to_learn: List[Dict[str, str]]
    overall_feedback: str
    score_details: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    used_fallback_scores: bool = False


class StructuredErrorItemResponse(BaseModel):
    type: str
    subtype: Optional[str] = None
    original_fragment: str
    corrected_fragment: str
    explanation: str
    severity: int
    severity_label: str


class StructuredMessageAnalysisResponse(BaseModel):
    had_errors: bool
    accuracy_score: int
    error_count: int
    expected_speech_level: str
    expected_speech_level_code: Optional[str] = None
    detected_speech_level: Optional[str] = None
    detected_speech_level_code: Optional[str] = None
    speech_level_correct: bool
    intent: str
    context_signals: Dict[str, Any] = Field(default_factory=dict)
    corrected_message: Optional[str] = None
    summary: Optional[str] = None
    encouragement: Optional[str] = None
    top_focus: Optional[str] = None
    error_breakdown: Dict[str, int] = Field(default_factory=dict)
    errors: List[StructuredErrorItemResponse] = Field(default_factory=list)


class StructuredMessageReplyResponse(BaseModel):
    avatar_message: Optional[str] = None
    used_corrected_meaning: bool = False
    suggestions: List[str] = Field(default_factory=list)
    hint: Optional[str] = None


class AnalyzeMessageResponse(BaseModel):
    analysis: StructuredMessageAnalysisResponse
    reply: Optional[StructuredMessageReplyResponse] = None


# Re-export response models for API docs
class CorrectionResponse(BaseModel):
    """Inline correction detail"""
    original: str
    corrected: str
    type: str
    severity: str
    explanation: str
    tip: Optional[str] = None


class NaturalAlternativeResponse(BaseModel):
    """Natural alternative expression."""
    expression: str
    explanation: str


class RealTimeCorrectionResponse(BaseModel):
    """Real-time correction feedback"""
    original_message: str
    corrected_message: Optional[str] = None
    has_errors: bool = False
    corrections: List[CorrectionResponse] = []
    natural_alternatives: List[NaturalAlternativeResponse] = []
    expected_speech_level: str
    expected_speech_level_code: Optional[str] = None
    detected_speech_level: Optional[str] = None
    detected_speech_level_code: Optional[str] = None
    speech_level_correct: bool = True
    accuracy_score: int = 100
    verdict: Optional[str] = None
    summary: Optional[str] = None
    input_kind: Optional[str] = None
    scorable: bool = True
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
            session_id=request.session_id,
            expected_speech_level=request.expected_speech_level,
            correction_context=(
                request.correction_context.model_dump()
                if request.correction_context
                else None
            ),
            response_instruction=request.response_instruction,
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
                natural_alternatives=[
                    NaturalAlternativeResponse(
                        expression=a.expression,
                        explanation=a.explanation,
                    )
                    for a in response.correction.natural_alternatives
                ],
                expected_speech_level=response.correction.expected_speech_level,
                expected_speech_level_code=response.correction.expected_speech_level_code,
                detected_speech_level=response.correction.detected_speech_level,
                detected_speech_level_code=response.correction.detected_speech_level_code,
                speech_level_correct=response.correction.speech_level_correct,
                accuracy_score=response.correction.accuracy_score,
                verdict=response.correction.verdict,
                summary=response.correction.summary,
                input_kind=response.correction.input_kind,
                scorable=response.correction.scorable,
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


@router.post("/analyze", response_model=ConversationAnalysisResponse)
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


@router.post("/analyze-message", response_model=AnalyzeMessageResponse)
async def analyze_message(request: AnalyzeMessageRequest):
    """
    Analyze one user message and return storage-friendly structured errors.

    This endpoint is intended for downstream session aggregation:
    - normalized error items
    - context signals
    - message intent
    - corrected full sentence
    - optional avatar reply
    """
    try:
        result: StructuredMessageResult = await chat_service.analyze_message(
            avatar=request.avatar,
            user_message=request.user_message,
            conversation_history=request.conversation_history,
            user_profile=request.user_profile,
            situation=request.situation,
            user_id=request.user_id or "default",
            session_id=request.session_id,
            expected_speech_level=request.expected_speech_level,
            correction_context=(
                request.correction_context.model_dump()
                if request.correction_context
                else None
            ),
            response_instruction=request.response_instruction,
            include_reply=request.include_reply,
        )

        return AnalyzeMessageResponse(
            analysis=StructuredMessageAnalysisResponse(
                had_errors=result.analysis.had_errors,
                accuracy_score=result.analysis.accuracy_score,
                error_count=result.analysis.error_count,
                expected_speech_level=result.analysis.expected_speech_level,
                expected_speech_level_code=result.analysis.expected_speech_level_code,
                detected_speech_level=result.analysis.detected_speech_level,
                detected_speech_level_code=result.analysis.detected_speech_level_code,
                speech_level_correct=result.analysis.speech_level_correct,
                intent=result.analysis.intent,
                context_signals=result.analysis.context_signals,
                corrected_message=result.analysis.corrected_message,
                summary=result.analysis.summary,
                encouragement=result.analysis.encouragement,
                top_focus=result.analysis.top_focus,
                error_breakdown=result.analysis.error_breakdown,
                errors=[
                    StructuredErrorItemResponse(
                        type=item.type,
                        subtype=item.subtype,
                        original_fragment=item.original_fragment,
                        corrected_fragment=item.corrected_fragment,
                        explanation=item.explanation,
                        severity=item.severity,
                        severity_label=item.severity_label,
                    )
                    for item in result.analysis.errors
                ],
            ),
            reply=(
                StructuredMessageReplyResponse(
                    avatar_message=result.reply.avatar_message,
                    used_corrected_meaning=result.reply.used_corrected_meaning,
                    suggestions=result.reply.suggestions,
                    hint=result.reply.hint,
                )
                if result.reply
                else None
            ),
        )
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
            natural_alternatives=[
                NaturalAlternativeResponse(
                    expression=a.expression,
                    explanation=a.explanation,
                )
                for a in correction.natural_alternatives
            ],
            expected_speech_level=correction.expected_speech_level,
            expected_speech_level_code=correction.expected_speech_level_code,
            detected_speech_level=correction.detected_speech_level,
            detected_speech_level_code=correction.detected_speech_level_code,
            speech_level_correct=correction.speech_level_correct,
            accuracy_score=correction.accuracy_score,
            verdict=correction.verdict,
            summary=correction.summary,
            input_kind=correction.input_kind,
            scorable=correction.scorable,
            encouragement=correction.encouragement,
            streak_bonus=False,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
