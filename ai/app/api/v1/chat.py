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
from app.services.clova_service import clova_service


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
    session_id: Optional[str] = None
    session_corrections: List[Dict[str, Any]] = Field(default_factory=list)


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
            session_id=request.session_id,
            session_corrections=request.session_corrections,
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


class SituationSuggestionItem(BaseModel):
    id: str
    name_ko: str
    name_en: str = ""
    description_ko: str
    scene_place: str = ""
    conversation_goal: str = ""
    avatar_role_in_scene: str = ""
    user_role_in_scene: str = ""
    icon: str = "users"
    category: str = "casual"
    contexts: List[str] = Field(default_factory=list)


class SituationSuggestRequest(BaseModel):
    avatar: Dict[str, Any]
    user_profile: Dict[str, Any] = Field(default_factory=dict)
    count: int = Field(default=5, ge=1, le=5)


class SituationSuggestResponse(BaseModel):
    situations: List[SituationSuggestionItem]
    source: str = "ai"


def _avatar_field(avatar: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = avatar.get(key)
        if value:
            return str(value)
    return ""


def _list_field(payload: Dict[str, Any], *keys: str) -> List[str]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
    return []


def _avatar_scene_role(avatar: Dict[str, Any]) -> str:
    return _avatar_field(
        avatar,
        "relationship",
        "custom_role",
        "role",
        "relationship_description",
        "description_ko",
        "description",
    ) or "대화 상대"


def _avatar_allows_service_role(avatar: Dict[str, Any]) -> bool:
    text = " ".join([
        _avatar_field(avatar, "role", "relationship", "custom_role", "relationship_description"),
        _avatar_field(avatar, "description_ko", "description"),
    ]).lower()
    return any(term in text for term in [
        "staff", "employee", "clerk", "server", "cashier", "barista", "waiter",
        "customer", "client", "직원", "점원", "알바", "아르바이트", "종업원",
        "바리스타", "손님", "고객", "사장",
    ])


def _avatar_allows_interviewer_role(avatar: Dict[str, Any]) -> bool:
    text = " ".join([
        _avatar_field(avatar, "role", "relationship", "custom_role", "relationship_description"),
        _avatar_field(avatar, "description_ko", "description"),
    ]).lower()
    return any(term in text for term in ["interviewer", "recruiter", "hr", "면접관", "채용", "인사담당"])


def _sanitize_role_shift_text(value: str, avatar: Dict[str, Any]) -> str:
    text = str(value or "").strip()
    if not text:
        return ""

    if not _avatar_allows_service_role(avatar):
        replacements = {
            "카페 직원으로서": "카페에 함께 있는 사람으로서",
            "카페 점원으로서": "카페에 함께 있는 사람으로서",
            "카페 알바로서": "카페에 함께 있는 사람으로서",
            "직원으로서": "대화 상대방으로서",
            "점원으로서": "대화 상대방으로서",
            "손님": "상대방",
            "저희 카페": "이곳",
            "저희 매장": "이곳",
            "저희 식당": "이곳",
            "저희 가게": "이곳",
        }
        for source, target in replacements.items():
            text = text.replace(source, target)

    if not _avatar_allows_interviewer_role(avatar):
        replacements = {
            "면접관으로서": "대화 상대방으로서",
            "면접을 시작": "대화를 시작",
            "지원자": "상대방",
            "채용 담당자": "대화 상대",
        }
        for source, target in replacements.items():
            text = text.replace(source, target)

    return text


def _find_topic_overlap(left: List[str], right: List[str]) -> Optional[str]:
    normalized_right = [item.strip().lower() for item in right]
    for topic in left:
        normalized_topic = topic.strip().lower()
        if any(normalized_topic in candidate or candidate in normalized_topic for candidate in normalized_right):
            return topic
    return None


def _personalize_situation_suggestions(
    items: List[SituationSuggestionItem],
    avatar: Dict[str, Any],
    user_profile: Dict[str, Any],
) -> List[SituationSuggestionItem]:
    user_likes = _list_field(user_profile, "interests", "likes", "preferences")
    user_dislikes = _list_field(user_profile, "dislikes", "hate", "hates")
    avatar_likes = _list_field(avatar, "interests", "likes", "preferences")
    avatar_dislikes = _list_field(avatar, "dislikes", "hate", "hates")

    shared_like = _find_topic_overlap(user_likes, avatar_likes)
    shared_dislike = _find_topic_overlap(user_dislikes, avatar_dislikes)
    user_like_avatar_dislikes = _find_topic_overlap(user_likes, avatar_dislikes)
    avatar_like_user_dislikes = _find_topic_overlap(avatar_likes, user_dislikes)
    avoid_topic = shared_dislike or user_like_avatar_dislikes or avatar_like_user_dislikes
    focus_topic = shared_like or (avatar_likes[0] if avatar_likes else None) or (user_likes[0] if user_likes else None)

    personalized: List[SituationSuggestionItem] = []
    for index, item in enumerate(items):
        copied = item.model_copy(deep=True)
        if index == 0 and focus_topic:
            copied.id = f"{copied.id}_personalized"
            base = _sanitize_role_shift_text(copied.description_ko, avatar)
            copied.description_ko = (
                f'{base} 공통 관심사나 자연스러운 화제로 "{focus_topic}" 이야기를 활용합니다.'
                if base else f'공통 관심사나 자연스러운 화제로 "{focus_topic}" 이야기를 활용합니다.'
            )
            copied.contexts = list(dict.fromkeys([*copied.contexts, "질문하는 상황"]))
        elif avoid_topic:
            copied.id = f"{copied.id}_avoid"
            base = _sanitize_role_shift_text(copied.description_ko, avatar)
            copied.description_ko = (
                f'{base} 서로 불편할 수 있는 "{avoid_topic}" 이야기는 피하면서 대화를 이어갑니다.'
                if base else f'서로 불편할 수 있는 "{avoid_topic}" 이야기는 피하면서 대화를 이어갑니다.'
            )
            copied.contexts = list(dict.fromkeys([*copied.contexts, "질문하는 상황"]))
        else:
            copied.description_ko = _sanitize_role_shift_text(copied.description_ko, avatar)
        copied.scene_place = _sanitize_role_shift_text(copied.scene_place, avatar)
        copied.conversation_goal = _sanitize_role_shift_text(copied.conversation_goal, avatar)
        copied.avatar_role_in_scene = _sanitize_role_shift_text(copied.avatar_role_in_scene or _avatar_scene_role(avatar), avatar)
        copied.user_role_in_scene = _sanitize_role_shift_text(copied.user_role_in_scene or "학습자", avatar)
        personalized.append(copied)
    return personalized


def _fallback_situation_suggestions(
    avatar: Dict[str, Any],
    user_profile: Optional[Dict[str, Any]] = None,
    count: int = 5,
) -> List[SituationSuggestionItem]:
    role_text = " ".join([
        _avatar_field(avatar, "role", "relationship", "custom_role", "relationship_description"),
        _avatar_field(avatar, "name_ko", "name"),
        _avatar_field(avatar, "description_ko", "description"),
    ]).lower()

    if "professor" in role_text or "교수" in role_text:
        items = [
            SituationSuggestionItem(
                id="professor_feedback",
                name_ko="과제 피드백 요청하기",
                name_en="Asking for Assignment Feedback",
                description_ko="과제 방향이 맞는지 교수님께 정중하게 확인하고 조언을 구합니다.",
                icon="graduationCap",
                category="formal",
                contexts=["도움을 요청하는 상황", "질문하는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="professor_office_hours",
                name_ko="면담 시간 조율하기",
                name_en="Scheduling Office Hours",
                description_ko="수업 내용이나 진로 상담을 위해 교수님께 가능한 시간을 여쭤봅니다.",
                icon="building",
                category="formal",
                contexts=["약속을 잡는 상황", "질문하는 상황", "인사하는 상황"],
            ),
            SituationSuggestionItem(
                id="professor_extension",
                name_ko="제출 기한 문의하기",
                name_en="Asking About a Deadline",
                description_ko="과제 제출 일정이나 지연 가능성을 교수님께 조심스럽게 문의합니다.",
                icon="graduationCap",
                category="formal",
                contexts=["질문하는 상황", "사과하는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="professor_research",
                name_ko="연구 주제 상담하기",
                name_en="Discussing a Research Topic",
                description_ko="관심 있는 연구 주제에 대해 교수님께 의견과 방향을 여쭤봅니다.",
                icon="building",
                category="formal",
                contexts=["질문하는 상황", "도움을 요청하는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="professor_class_question",
                name_ko="수업 내용 질문하기",
                name_en="Asking About Class Content",
                description_ko="이해하지 못한 수업 내용을 교수님께 정중하게 다시 설명해 달라고 요청합니다.",
                icon="graduationCap",
                category="formal",
                contexts=["질문하는 상황", "도움을 요청하는 상황", "인사하는 상황"],
            ),
        ]
    elif "senior" in role_text or "선배" in role_text:
        items = [
            SituationSuggestionItem(
                id="senior_advice",
                name_ko="선배에게 조언 구하기",
                name_en="Asking a Senior for Advice",
                description_ko="학교생활이나 동아리 활동에 대해 선배에게 자연스럽게 조언을 구합니다.",
                icon="users",
                category="casual",
                contexts=["도움을 요청하는 상황", "질문하는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="senior_project",
                name_ko="팀 프로젝트 역할 묻기",
                name_en="Asking About a Project Role",
                description_ko="팀 프로젝트에서 맡을 역할과 진행 방식을 선배에게 확인합니다.",
                icon="handshake",
                category="work",
                contexts=["질문하는 상황", "도움을 요청하는 상황", "약속을 잡는 상황"],
            ),
            SituationSuggestionItem(
                id="senior_career",
                name_ko="진로 경험 물어보기",
                name_en="Asking About Career Experience",
                description_ko="선배의 경험을 바탕으로 진로 선택이나 준비 방법을 물어봅니다.",
                icon="briefcase",
                category="casual",
                contexts=["질문하는 상황", "도움을 요청하는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="senior_club",
                name_ko="동아리 활동 조언받기",
                name_en="Getting Club Advice",
                description_ko="동아리나 학교 활동에서 어떻게 행동하면 좋을지 선배에게 조언을 구합니다.",
                icon="users",
                category="casual",
                contexts=["도움을 요청하는 상황", "질문하는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="senior_meeting",
                name_ko="스터디 약속 잡기",
                name_en="Planning a Study Meeting",
                description_ko="선배와 함께 공부하거나 자료를 확인할 시간을 자연스럽게 정합니다.",
                icon="coffee",
                category="casual",
                contexts=["약속을 잡는 상황", "질문하는 상황", "감사를 표현하는 상황"],
            ),
        ]
    elif any(term in role_text for term in ["boss", "manager", "상사", "팀장"]):
        items = [
            SituationSuggestionItem(
                id="boss_progress",
                name_ko="업무 진행 상황 보고하기",
                name_en="Reporting Work Progress",
                description_ko="상사에게 현재 진행 상황과 막힌 부분을 간결하고 공손하게 보고합니다.",
                icon="briefcase",
                category="work",
                contexts=["질문하는 상황", "도움을 요청하는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="boss_deadline",
                name_ko="마감 일정 조율하기",
                name_en="Discussing a Deadline",
                description_ko="업무 마감 일정이나 우선순위를 상사와 조심스럽게 조율합니다.",
                icon="building",
                category="work",
                contexts=["약속을 잡는 상황", "질문하는 상황", "사과하는 상황"],
            ),
            SituationSuggestionItem(
                id="boss_feedback",
                name_ko="업무 피드백 요청하기",
                name_en="Requesting Work Feedback",
                description_ko="완성한 업무나 초안에 대해 상사에게 개선점을 정중하게 요청합니다.",
                icon="briefcase",
                category="work",
                contexts=["도움을 요청하는 상황", "질문하는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="boss_problem",
                name_ko="문제 상황 공유하기",
                name_en="Sharing a Work Issue",
                description_ko="업무 중 생긴 문제를 숨기지 않고 상사에게 차분하게 설명합니다.",
                icon="building",
                category="work",
                contexts=["질문하는 상황", "도움을 요청하는 상황", "사과하는 상황"],
            ),
            SituationSuggestionItem(
                id="boss_meeting",
                name_ko="회의 의견 말하기",
                name_en="Giving an Opinion in a Meeting",
                description_ko="회의에서 상사에게 자신의 의견을 조심스럽지만 분명하게 전달합니다.",
                icon="handshake",
                category="work",
                contexts=["질문하는 상황", "감사를 표현하는 상황", "인사하는 상황"],
            ),
        ]
    elif any(term in role_text for term in ["customer", "고객", "손님"]):
        items = [
            SituationSuggestionItem(
                id="customer_request",
                name_ko="고객 요청 응대하기",
                name_en="Responding to a Customer Request",
                description_ko="고객의 요청을 확인하고 가능한 해결 방법을 친절하게 안내합니다.",
                icon="shoppingBag",
                category="service",
                contexts=["도움을 요청하는 상황", "질문하는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="customer_problem",
                name_ko="불편 사항 사과하기",
                name_en="Apologizing for an Issue",
                description_ko="고객이 불편을 말했을 때 사과하고 다음 조치를 설명합니다.",
                icon="handshake",
                category="service",
                contexts=["사과하는 상황", "질문하는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="customer_recommendation",
                name_ko="상품 추천하기",
                name_en="Recommending an Option",
                description_ko="고객의 취향과 필요를 물어본 뒤 적절한 선택지를 추천합니다.",
                icon="shoppingBag",
                category="service",
                contexts=["질문하는 상황", "도움을 요청하는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="customer_order",
                name_ko="주문 확인하기",
                name_en="Confirming an Order",
                description_ko="고객의 주문 내용을 다시 확인하고 필요한 정보를 친절하게 묻습니다.",
                icon="utensils",
                category="service",
                contexts=["주문하는 상황", "질문하는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="customer_delay",
                name_ko="대기 시간 안내하기",
                name_en="Explaining a Delay",
                description_ko="고객에게 대기나 지연 상황을 공손하게 설명하고 양해를 구합니다.",
                icon="mapPin",
                category="service",
                contexts=["사과하는 상황", "질문하는 상황", "감사를 표현하는 상황"],
            ),
        ]
    elif "interviewer" in role_text or "면접" in role_text:
        items = [
            SituationSuggestionItem(
                id="interviewer_intro",
                name_ko="면접 자기소개하기",
                name_en="Introducing Yourself in an Interview",
                description_ko="면접관에게 경험과 강점을 격식 있게 소개하고 후속 질문에 답합니다.",
                icon="briefcase",
                category="formal",
                contexts=["처음 만나는 상황", "질문하는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="interviewer_question",
                name_ko="면접 질문 되묻기",
                name_en="Clarifying an Interview Question",
                description_ko="질문을 정확히 이해하지 못했을 때 정중하게 확인하고 답변합니다.",
                icon="handshake",
                category="formal",
                contexts=["질문하는 상황", "사과하는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="interviewer_strength",
                name_ko="강점 설명하기",
                name_en="Explaining Your Strengths",
                description_ko="면접관에게 자신의 강점과 경험을 구체적인 예시로 설명합니다.",
                icon="briefcase",
                category="formal",
                contexts=["질문하는 상황", "감사를 표현하는 상황", "처음 만나는 상황"],
            ),
            SituationSuggestionItem(
                id="interviewer_weakness",
                name_ko="약점 질문 답하기",
                name_en="Answering a Weakness Question",
                description_ko="약점이나 부족한 점을 묻는 질문에 솔직하지만 균형 있게 답합니다.",
                icon="handshake",
                category="formal",
                contexts=["질문하는 상황", "사과하는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="interviewer_closing",
                name_ko="면접 마무리 인사하기",
                name_en="Closing an Interview",
                description_ko="면접 마지막에 감사 인사를 전하고 후속 절차를 정중하게 확인합니다.",
                icon="users",
                category="formal",
                contexts=["감사를 표현하는 상황", "질문하는 상황", "인사하는 상황"],
            ),
        ]
    elif "friend" in role_text or "친구" in role_text:
        items = [
            SituationSuggestionItem(
                id="friend_plan",
                name_ko="카페 약속 잡기",
                name_en="Making Cafe Plans",
                description_ko="친구와 편하게 시간과 장소를 정하고 취향을 물어봅니다.",
                icon="coffee",
                category="casual",
                contexts=["약속을 잡는 상황", "질문하는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="friend_help",
                name_ko="친구에게 부탁하기",
                name_en="Asking a Friend for a Favor",
                description_ko="친구에게 작은 도움을 부탁하고 고마움을 자연스럽게 표현합니다.",
                icon="users",
                category="casual",
                contexts=["도움을 요청하는 상황", "감사를 표현하는 상황", "사과하는 상황"],
            ),
            SituationSuggestionItem(
                id="friend_movie",
                name_ko="같이 볼 콘텐츠 고르기",
                name_en="Choosing Something to Watch",
                description_ko="친구와 보고 싶은 콘텐츠나 취향을 편하게 이야기하며 선택합니다.",
                icon="party",
                category="casual",
                contexts=["질문하는 상황", "약속을 잡는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="friend_apology",
                name_ko="약속 변경 사과하기",
                name_en="Apologizing for Changing Plans",
                description_ko="친구에게 약속 변경을 말하고 미안한 마음을 자연스럽게 전합니다.",
                icon="users",
                category="casual",
                contexts=["사과하는 상황", "약속을 잡는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="friend_trip",
                name_ko="주말 계획 이야기하기",
                name_en="Talking About Weekend Plans",
                description_ko="친구와 주말에 무엇을 할지 취향을 묻고 편하게 계획을 세웁니다.",
                icon="mapPin",
                category="casual",
                contexts=["약속을 잡는 상황", "질문하는 상황", "감사를 표현하는 상황"],
            ),
        ]
    else:
        items = [
            SituationSuggestionItem(
                id="default_first_meeting",
                name_ko="처음 만나 인사하기",
                name_en="First Meeting Greeting",
                description_ko="상대와 처음 만난 상황에서 자연스럽게 인사하고 기본 정보를 묻습니다.",
                icon="users",
                category="casual",
                contexts=["처음 만나는 상황", "인사하는 상황", "질문하는 상황"],
            ),
            SituationSuggestionItem(
                id="default_help",
                name_ko="정중하게 도움 요청하기",
                name_en="Politely Asking for Help",
                description_ko="상대와의 관계에 맞는 말투로 필요한 도움을 요청합니다.",
                icon="handshake",
                category="formal",
                contexts=["도움을 요청하는 상황", "질문하는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="default_plan",
                name_ko="약속 시간 정하기",
                name_en="Setting a Meeting Time",
                description_ko="상대와 가능한 시간을 확인하고 부담스럽지 않게 약속을 조율합니다.",
                icon="coffee",
                category="casual",
                contexts=["약속을 잡는 상황", "질문하는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="default_question",
                name_ko="궁금한 점 물어보기",
                name_en="Asking a Question",
                description_ko="상대에게 궁금한 내용을 관계에 맞는 말투로 자연스럽게 질문합니다.",
                icon="handshake",
                category="formal",
                contexts=["질문하는 상황", "인사하는 상황", "감사를 표현하는 상황"],
            ),
            SituationSuggestionItem(
                id="default_thanks",
                name_ko="도움에 감사 표현하기",
                name_en="Thanking Someone for Help",
                description_ko="상대가 도와준 뒤 고마움을 구체적이고 자연스럽게 표현합니다.",
                icon="users",
                category="casual",
                contexts=["감사를 표현하는 상황", "인사하는 상황", "질문하는 상황"],
            ),
        ]

    return _personalize_situation_suggestions(items[:count], avatar, user_profile or {})


class EndSessionRequest(BaseModel):
    """End-of-chat hook: extract durable per-avatar memories from the session."""
    user_id: str
    avatar_id: str
    avatar_name: Optional[str] = None
    session_id: Optional[str] = None
    conversation_history: List[ChatMessage] = []


class EndSessionResponse(BaseModel):
    memories_extracted: int
    summary: Optional[str] = None


@router.post("/end-session", response_model=EndSessionResponse)
async def end_session(request: EndSessionRequest):
    """Persist long-term memories (facts/preferences/events) for the (user, avatar)
    pair so the next chat with the same avatar feels familiar.

    Safe to call from a fire-and-forget client; never raises on extraction failure.
    """
    from app.services.memory_service import memory_service

    messages = [{"role": m.role, "content": m.content} for m in request.conversation_history]
    if not messages:
        return EndSessionResponse(memories_extracted=0)

    extracted: List[Any] = []
    try:
        extracted = await memory_service.extract_memories(
            user_id=request.user_id,
            avatar_id=request.avatar_id,
            messages=messages,
        )
    except Exception as e:
        print(f"[end-session] extract_memories failed: {e}")

    summary_text: Optional[str] = None
    try:
        summary_obj = await memory_service.summarize_conversation(
            user_id=request.user_id,
            avatar_id=request.avatar_id,
            conversation_id=request.session_id or f"{request.user_id}_{request.avatar_id}",
            messages=messages,
        )
        summary_text = getattr(summary_obj, "summary", None) if summary_obj else None
    except Exception as e:
        print(f"[end-session] summarize_conversation failed: {e}")

    return EndSessionResponse(
        memories_extracted=len(extracted),
        summary=summary_text,
    )


@router.post("/generate-bio", response_model=BioResponse)
async def generate_bio(request: BioGenerateRequest):
    """Generate AI bio/conversation guide for avatar."""
    try:
        bio = await chat_service.generate_avatar_bio(request.avatar)
        return BioResponse(bio=bio)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest-situations", response_model=SituationSuggestResponse)
async def suggest_situations(request: SituationSuggestRequest):
    """Generate avatar-specific practice situations.

    The avatar should never tutor here; this endpoint only creates practice
    scenario drafts for the UI.
    """
    fallback = _fallback_situation_suggestions(request.avatar, request.user_profile, request.count)
    prompt = f"""
You create Korean conversation practice situations for one avatar.

Avatar JSON:
{request.avatar}

User profile JSON:
{request.user_profile}

Return strict JSON only:
{{
  "situations": [
    {{
      "id": "short_snake_case_id",
      "name_ko": "Korean title",
      "name_en": "English title",
      "description_ko": "One sentence about what the learner practices",
      "scene_place": "Where this happens, e.g. 카페, 연구실, 회의실",
      "conversation_goal": "What the learner practices, e.g. 약속 시간 정하기",
      "avatar_role_in_scene": "The avatar's role in this scene; must match the avatar relationship, not the place",
      "user_role_in_scene": "The user's role in this scene",
      "icon": "coffee|utensils|shoppingBag|graduationCap|briefcase|building|users|handshake|party|mapPin",
      "category": "casual|service|formal|work",
      "contexts": ["처음 만나는 상황|도움을 요청하는 상황|주문하는 상황|질문하는 상황|인사하는 상황|약속을 잡는 상황|감사를 표현하는 상황|사과하는 상황"]
    }}
  ]
}}

Rules:
- Create exactly {request.count} situations.
- Each situation must fit this avatar's relationship to the user.
- Base the situation on the pair: user preferences, user dislikes, avatar preferences, and avatar dislikes.
- Prefer shared interests when they exist.
- Avoid topics either side dislikes, and avoid topics one side likes if the other explicitly dislikes them.
- Do not reuse generic fixed situations for every avatar.
- Do not write tutoring advice, corrections, or meta explanations.
- Keep each description practical and roleplay-ready.
- A place does not change the avatar's identity. If the avatar is a friend in a cafe, avatar_role_in_scene is friend, not cafe staff.
- Do not make the avatar a cafe worker, shop clerk, interviewer, teacher, or other new role unless that already matches the avatar JSON.
"""

    try:
        data = await clova_service.analyze_json(prompt, max_tokens=900, temperature=0.8)
        raw_items = data.get("situations") if isinstance(data, dict) else None
        if not isinstance(raw_items, list):
            return SituationSuggestResponse(situations=fallback, source="fallback")

        allowed_icons = {"coffee", "utensils", "shoppingBag", "graduationCap", "briefcase", "building", "users", "handshake", "party", "mapPin"}
        allowed_categories = {"casual", "service", "formal", "work"}
        suggestions: List[SituationSuggestionItem] = []
        for index, item in enumerate(raw_items[:request.count]):
            if not isinstance(item, dict):
                continue
            name_ko = str(item.get("name_ko") or "").strip()
            description_ko = _sanitize_role_shift_text(str(item.get("description_ko") or "").strip(), request.avatar)
            if not name_ko or not description_ko:
                continue
            contexts = item.get("contexts") if isinstance(item.get("contexts"), list) else []
            suggestions.append(SituationSuggestionItem(
                id=str(item.get("id") or f"ai_situation_{index + 1}").strip(),
                name_ko=name_ko,
                name_en=str(item.get("name_en") or "").strip(),
                description_ko=description_ko,
                scene_place=_sanitize_role_shift_text(str(item.get("scene_place") or "").strip(), request.avatar),
                conversation_goal=_sanitize_role_shift_text(str(item.get("conversation_goal") or "").strip(), request.avatar),
                avatar_role_in_scene=_sanitize_role_shift_text(str(item.get("avatar_role_in_scene") or _avatar_scene_role(request.avatar)).strip(), request.avatar),
                user_role_in_scene=_sanitize_role_shift_text(str(item.get("user_role_in_scene") or "학습자").strip(), request.avatar),
                icon=item.get("icon") if item.get("icon") in allowed_icons else "users",
                category=item.get("category") if item.get("category") in allowed_categories else "casual",
                contexts=[str(context).strip() for context in contexts if str(context).strip()][:4],
            ))

        if not suggestions:
            return SituationSuggestResponse(situations=fallback, source="fallback")
        return SituationSuggestResponse(situations=suggestions, source="ai")
    except Exception as e:
        print(f"[suggest-situations] failed: {e}")
        return SituationSuggestResponse(situations=fallback, source="fallback")


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


# ── Response suggestion for realtime sessions ─────────────────────────────────

class SuggestRequest(BaseModel):
    partner_text: str
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    avatar_role: Optional[str] = None
    speech_level: str = "polite"

class SuggestResponse(BaseModel):
    suggestions: List[str] = Field(default_factory=list)

@router.post("/suggest", response_model=SuggestResponse)
async def suggest_responses(request: SuggestRequest):
    """Generate 3 natural Korean response options for the user after a partner turn."""
    level_labels = {"formal": "합쇼체", "polite": "해요체", "informal": "반말"}
    level_label = level_labels.get(request.speech_level, "해요체")

    role_line = f"상대방은 {request.avatar_role}입니다." if request.avatar_role else ""
    history_lines = "\n".join(
        f"{h.get('speaker', '?')}: {h.get('text', '')}"
        for h in (request.conversation_history or [])[-4:]
        if h.get("text", "").strip()
    )

    prompt = f"""한국어 대화 연습 도우미입니다. 사용자가 {level_label}로 상대방에게 자연스럽게 답할 수 있도록 도와주세요.
{role_line}
{"이전 대화:\n" + history_lines + "\n" if history_lines else ""}상대방: {request.partner_text}

이 말에 대한 자연스러운 {level_label} 응답 3가지를 제안하세요.
각 응답은 20자 이내로 짧고 실용적이어야 합니다. 다양한 반응(동의, 질문, 감탄 등)을 포함하세요.

JSON만 반환하세요:
{{"suggestions": ["응답1", "응답2", "응답3"]}}"""

    try:
        data = await clova_service.analyze_json(prompt, max_tokens=200, temperature=0.8)
        items = data.get("suggestions") if isinstance(data, dict) else None
        if not isinstance(items, list):
            items = data.get("items") if isinstance(data, dict) else None
        if isinstance(items, list):
            return SuggestResponse(suggestions=[str(s).strip() for s in items[:3] if str(s).strip()])
        return SuggestResponse(suggestions=[])
    except Exception as e:
        print(f"[suggest] error: {e}")
        return SuggestResponse(suggestions=[])
