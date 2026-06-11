"""
Chat Service - Handles avatar conversations with real-time correction
"""
import re
import difflib
import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager
from collections import Counter
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from app.core.config import settings
from app.schemas.avatar import AvatarBase, SpeechLevel, get_speech_levels_for_role, get_role_label
from app.schemas.user import UserProfile, KoreanLevel
from app.services.clova_service import clova_service, Message
from app.services.simple_speech_analyzer import (
    get_speech_analyzer,
    detect_speech_level_by_morpheme,
)
from app.services.korean_coaching_prompt_builder import (
    build_native_korean_coaching_prompt,
    sanitize_json_like_model_output,
)
from app.services.speech_analysis_service import analyze_user_korean_message
from app.services.prompt_builder import (
    build_avatar_system_prompt,
    build_speech_correction_prompt,
    build_conversation_analysis_prompt,
    build_bio_generation_prompt,
    SPEECH_LEVEL_INFO,
    postprocess_model_output,
)
from app.ml.korean_nlp import morpheme_analyzer

# ============================================================================
# Enums & Models
# ============================================================================

class CorrectionType(str, Enum):
    SPEECH_LEVEL = "speech_level"
    GRAMMAR      = "grammar"
    SPELLING     = "spelling"
    VOCABULARY   = "vocabulary"
    EXPRESSION   = "expression"
    HONORIFIC    = "honorific"


class CorrectionSeverity(str, Enum):
    INFO    = "info"
    WARNING = "warning"
    ERROR   = "error"


class InlineCorrection(BaseModel):
    original:    str                = Field(..., description="원래 표현")
    corrected:   str                = Field(..., description="수정된 표현")
    type:        CorrectionType     = Field(..., description="오류 유형")
    severity:    CorrectionSeverity = Field(default=CorrectionSeverity.WARNING)
    explanation: str                = Field(..., description="설명")
    tip:         Optional[str]      = Field(None, description="학습 팁")


class NaturalAlternative(BaseModel):
    expression:  str = Field(..., description="더 자연스러운 표현")
    explanation: str = Field(..., description="왜 더 자연스러운지")


class RealTimeCorrection(BaseModel):
    original_message:  str
    corrected_message: Optional[str] = None
    has_errors:        bool = False
    corrections:       List[InlineCorrection] = []
    natural_alternatives: List[NaturalAlternative] = []

    expected_speech_level: str
    expected_speech_level_code: Optional[str] = None
    detected_speech_level: Optional[str] = None
    detected_speech_level_code: Optional[str] = None
    speech_level_correct:  bool = True

    accuracy_score: int           = 100
    verdict:        Optional[str] = None
    summary:        Optional[str] = None
    input_kind:     Optional[str] = None
    scorable:       bool          = True
    encouragement:  Optional[str] = None
    streak_bonus:   bool          = False


class ChatMessage(BaseModel):
    role:      str
    content:   str
    timestamp: Optional[str] = None


class ChatResponse(BaseModel):
    message:    str
    correction: Optional[RealTimeCorrection] = None

    mood_change:  int = 0
    current_mood: int = 100
    mood_emoji:   str = ""

    suggestions:    List[str]    = []
    hint:           Optional[str] = None
    correct_streak: int           = 0
    session_summary: Optional[str] = None


class ConversationAnalysis(BaseModel):
    scores:              Dict[str, int]
    mistakes:            List[Dict[str, str]]
    vocabulary_to_learn: List[Dict[str, str]]
    phrases_to_learn:    List[Dict[str, str]]
    overall_feedback:    str
    score_details:       Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    used_fallback_scores: bool = False


class StructuredErrorItem(BaseModel):
    type:                str
    subtype:             Optional[str] = None
    original_fragment:   str
    corrected_fragment:  str
    explanation:         str
    severity:            int
    severity_label:      str


class StructuredMessageAnalysis(BaseModel):
    had_errors:                   bool
    accuracy_score:               int
    error_count:                  int
    expected_speech_level:        str
    expected_speech_level_code:   Optional[str] = None
    detected_speech_level:        Optional[str] = None
    detected_speech_level_code:   Optional[str] = None
    speech_level_correct:         bool
    intent:                       str = ""
    context_signals:              Dict[str, Any] = Field(default_factory=dict)
    corrected_message:            Optional[str] = None
    summary:                      Optional[str] = None
    encouragement:                Optional[str] = None
    top_focus:                    Optional[str] = None
    error_breakdown:              Dict[str, int] = Field(default_factory=dict)
    errors:                       List[StructuredErrorItem] = Field(default_factory=list)


class StructuredMessageReply(BaseModel):
    avatar_message:        Optional[str] = None
    used_corrected_meaning: bool = False
    suggestions:           List[str] = Field(default_factory=list)
    hint:                  Optional[str] = None


class StructuredMessageResult(BaseModel):
    analysis: StructuredMessageAnalysis
    reply:    Optional[StructuredMessageReply] = None


def _label_for_correction_type(correction: InlineCorrection) -> str:
    if correction.type == CorrectionType.HONORIFIC:
        return "요청 표현" if "주세" in correction.corrected or "주실" in correction.corrected else "호칭/높임"
    if correction.type == CorrectionType.SPEECH_LEVEL:
        return "말투"
    if correction.type == CorrectionType.VOCABULARY:
        return "어휘"
    if correction.type == CorrectionType.SPELLING:
        return "띄어쓰기" if correction.original.replace(" ", "") == correction.corrected.replace(" ", "") else "오타"
    if correction.type == CorrectionType.GRAMMAR:
        return "문법"
    return "표현"


def build_human_feedback_summary(
    has_errors: bool,
    corrections: List[InlineCorrection],
    verdict: str,
    speech_level_correct: bool,
    expected_speech_level: SpeechLevel,
    message_intent: str,
) -> str:
    if not has_errors:
        if message_intent == "greeting":
            return "인사말이 자연스럽고 상황에도 잘 맞아요."
        return "지금 문장도 충분히 자연스럽게 들려요."

    labels: List[str] = []
    for correction in corrections:
        label = _label_for_correction_type(correction)
        if label not in labels:
            labels.append(label)

    if not labels and not speech_level_correct:
        labels = ["말투"]

    if len(labels) >= 3:
        lead = f"{labels[0]}, {labels[1]}, {labels[2]}"
    elif len(labels) == 2:
        lead = f"{labels[0]}와 {labels[1]}"
    elif len(labels) == 1:
        lead = labels[0]
    else:
        lead = SPEECH_LEVEL_INFO[expected_speech_level]["name_ko"]
    object_particle = "를" if lead.endswith(("투", "휘")) else "을"

    if verdict == "speech_and_spelling":
        return f"{lead}{object_particle} 함께 다듬으면 훨씬 자연스럽게 들려요."
    if verdict == "spelling":
        return f"{lead}만 정리해도 문장이 훨씬 매끄러워져요."
    if verdict == "wrong_speech_level":
        return f"지금 상황에서는 {lead}{object_particle} 조금 더 맞춰 주면 자연스러워요."
    if verdict == "needs_revision":
        return f"{lead}{object_particle} 조금만 손보면 훨씬 더 자연스럽게 들려요."
    return f"{lead}{object_particle} 다듬으면 지금 상황에 더 잘 어울려요."


def build_human_encouragement(
    has_errors: bool,
    corrections: List[InlineCorrection],
    message_intent: str,
) -> Optional[str]:
    return None


def apply_error_based_score_cap(
    accuracy_score: int,
    corrections: List[InlineCorrection],
    speech_level_correct: bool,
) -> int:
    real_corrections = [
        correction for correction in corrections
        if correction.severity in {CorrectionSeverity.ERROR, CorrectionSeverity.WARNING}
        and correction.original != correction.corrected
    ]
    if not real_corrections and speech_level_correct:
        return accuracy_score

    cap = 99
    labels = {correction.type for correction in real_corrections}

    if not speech_level_correct or CorrectionType.SPEECH_LEVEL in labels:
        cap = min(cap, 60)
    if CorrectionType.HONORIFIC in labels:
        cap = min(cap, 72)
    if CorrectionType.VOCABULARY in labels:
        cap = min(cap, 78)

    spelling_like = [c for c in real_corrections if c.type == CorrectionType.SPELLING]
    if spelling_like:
        spacing_only = all(
            re.sub(r"\s+", "", correction.original) == re.sub(r"\s+", "", correction.corrected)
            for correction in spelling_like
        )
        cap = min(cap, 92 if spacing_only else 88)

    if len(real_corrections) >= 2:
        cap = min(cap, 84)
    if len(real_corrections) >= 3:
        cap = min(cap, 78)

    return min(accuracy_score, cap)


# ============================================================================
# 단답형 → 자연스러운 대안 맵
# ============================================================================

_SHORT_ALTERNATIVES: Dict[str, Dict[str, List[Dict[str, str]]]] = {
    "네": {
        "polite":   [
            {"expression": "네, 맞아요!", "explanation": "더 활기차고 자연스러운 동의 표현이에요"},
            {"expression": "네, 그렇군요!", "explanation": "상대방 말에 공감할 때 자주 써요"},
        ],
        "formal":   [
            {"expression": "네, 맞습니다.", "explanation": "격식 있는 동의 표현이에요"},
            {"expression": "그렇습니다.", "explanation": "격식체에서 자주 쓰는 동의 표현이에요"},
        ],
        "informal": [
            {"expression": "어, 맞아!", "explanation": "친한 사이에서 자연스러운 동의예요"},
            {"expression": "응, 그렇지!", "explanation": "캐주얼하게 동의할 때 써요"},
        ],
    },
    "넵": {
        "polite":   [
            {"expression": "네, 알겠어요!", "explanation": "더 적극적이고 자연스러운 대답이에요"},
            {"expression": "네, 그렇군요.", "explanation": "'넵'보다 조금 더 부드러운 표현이에요"},
        ],
        "formal":   [{"expression": "네, 알겠습니다.", "explanation": "격식 있는 상황에서 쓰는 표현이에요"}],
        "informal": [{"expression": "어, 알았어!", "explanation": "친한 사이에서 자연스러운 대답이에요"}],
    },
    "응": {
        "informal": [
            {"expression": "어, 맞아!", "explanation": "더 활기차고 자연스러운 동의예요"},
            {"expression": "그렇지!", "explanation": "확실히 동의할 때 쓰는 표현이에요"},
        ],
        "polite": [{"expression": "네, 그래요!", "explanation": "반말 '응' 대신 해요체로 바꾸면 이렇게요"}],
    },
    "어": {
        "informal": [
            {"expression": "맞아, 그렇네!", "explanation": "더 생동감 있는 반응이에요"},
            {"expression": "오, 그래?", "explanation": "관심과 놀라움을 표현할 때 써요"},
        ],
        "polite": [{"expression": "아, 그렇군요!", "explanation": "'어' 대신 해요체로 자연스럽게 반응하는 표현이에요"}],
    },
    "그래": {
        "informal": [
            {"expression": "맞아, 그렇지!", "explanation": "더 확신을 담은 동의 표현이에요"},
            {"expression": "어, 그러네!", "explanation": "가볍게 동의할 때 자연스러운 표현이에요"},
        ],
        "polite": [{"expression": "그렇군요, 맞아요!", "explanation": "해요체로 더 자연스럽게 바꾼 표현이에요"}],
    },
    "아니": {
        "informal": [
            {"expression": "아니, 그건 좀 달라!", "explanation": "더 구체적으로 반대 의견을 표현할 수 있어요"},
            {"expression": "음, 그건 아닌 것 같아.", "explanation": "부드럽게 반대할 때 쓰는 표현이에요"},
        ],
        "polite": [{"expression": "아니요, 그건 좀 달라요.", "explanation": "해요체로 정중하게 반대하는 표현이에요"}],
    },
    "아니요": {
        "polite": [
            {"expression": "아니요, 그렇지 않아요.", "explanation": "더 명확하게 부정하는 표현이에요"},
            {"expression": "음, 그건 좀 아닌 것 같아요.", "explanation": "부드럽게 반대할 때 써요"},
        ],
        "formal": [{"expression": "아닙니다, 그렇지 않습니다.", "explanation": "격식 있게 부정하는 표현이에요"}],
    },
    "맞아": {
        "informal": [
            {"expression": "맞아, 진짜 그렇지!", "explanation": "더 강하게 동의할 때 써요"},
            {"expression": "어, 완전 동감이야!", "explanation": "강한 공감을 표현할 때 자연스러운 표현이에요"},
        ],
        "polite": [{"expression": "맞아요, 정말 그렇네요!", "explanation": "해요체로 더 자연스럽게 동의하는 표현이에요"}],
    },
}

_BAD_NATURAL_ALT_PATTERNS = [
    re.compile(r"^이렇게도 말할 수 있어요", re.IGNORECASE),
    re.compile(r"^더 자연스러운 .*표현", re.IGNORECASE),
    re.compile(r"^원래 문장이 이미 자연스러워", re.IGNORECASE),
    re.compile(r"^변경할 필요가 없", re.IGNORECASE),
]


# ============================================================================
# ── 핵심 수정: context-aware correction prompt ─────────────────────────────
# ============================================================================

def build_realtime_correction_prompt(
    user_message:          str,
    expected_speech_level: SpeechLevel,
    avatar_role:           str,
    user_level:            str = "intermediate",
    conversation_history:  List[ChatMessage] = [],   # ← 추가
    edit_strategy_hint:    str = "minimal",
    situation_signals:     Optional[Dict[str, Any]] = None,
    message_intent:        str = "small_talk",
    konlpy_hints:          Optional[Dict[str, Any]] = None,
) -> str:
    speech_info = SPEECH_LEVEL_INFO[expected_speech_level]
    level_guidance = {
        "beginner":     "초급 학습자입니다. 쉬운 설명과 기본적인 오류만 지적하세요.",
        "intermediate": "중급 학습자입니다. 주요 오류와 자연스러운 표현을 알려주세요.",
        "advanced":     "고급 학습자입니다. 미묘한 뉘앙스와 고급 표현도 피드백하세요.",
    }

    # ── 최근 대화 3턴 추출 ────────────────────────────────────────────────
    recent = conversation_history[-3:] if conversation_history else []
    context_lines = "\n".join([
        f"{'사용자' if m.role == 'user' else '아바타'}: {m.content}"
        for m in recent
    ])
    context_section = f"""
## 최근 대화 맥락 (교정 시 반드시 참고하세요)
{context_lines if context_lines else "(대화 시작)"}

⚠️ 중요: 위 대화 맥락을 반드시 고려하세요.
- 앞 대화에서 나온 주제나 단어를 사용하는 것은 자연스러운 표현입니다.
- 문맥상 자연스러운 표현은 오류로 처리하지 마세요.
- 예: 앞서 봄축제 얘기를 했다면 "봄축제야"는 정상적인 표현입니다.
""" if recent else ""

    situation_signals = situation_signals or {}
    konlpy_hints = konlpy_hints or {}
    situation_section = f"""
## 추론된 상황 신호
- 상대 유형: {situation_signals.get('counterpart', avatar_role)}
- 격식 수준: {situation_signals.get('formality', 'medium')}
- 서비스 상황 여부: {'예' if situation_signals.get('service_situation') else '아니오'}
- 처음 만남 가능성: {'예' if situation_signals.get('first_meeting') else '아니오'}
- 관계 방향: {situation_signals.get('power_direction', 'peer')}
- 사용자 발화 의도: {message_intent}
"""

    konlpy_section = f"""
## KoNLPy 형태소 힌트
- 명사 후보: {', '.join(konlpy_hints.get('nouns', []) or ['없음'])}
- 동사 후보: {', '.join(konlpy_hints.get('verbs', []) or ['없음'])}
- 어미 후보: {', '.join(konlpy_hints.get('endings', []) or ['없음'])}
"""

    strategy_line = {
        "none": "- 현재 문장이 충분히 자연스러우면 굳이 고치지 마세요.",
        "minimal": "- 이번 입력은 최소 수정이 우선입니다. 오타, 말투, 조사처럼 꼭 필요한 부분만 고치세요.",
        "rewrite": "- 이번 입력은 문장 전체의 어색함을 먼저 검토하되, 필요할 때만 전체 재작성하세요.",
    }.get(edit_strategy_hint, "- 과교정보다 보수적으로 판단하세요.")

    return f"""사용자의 한국어 메시지를 분석하여 실시간 교정 피드백을 제공하세요.
이 작업은 교정 분석 전용입니다. 아바타 답변이나 역할극 대사는 절대 만들지 마세요.

## 대화 상황
- 대화 상대: {avatar_role}
- 사용해야 할 말투: **{speech_info['name_ko']}** ({speech_info['name_en']})
- {speech_info['description']}
- 올바른 예시: {', '.join(speech_info['examples'])}

## 사용자 수준
{level_guidance.get(user_level, level_guidance['intermediate'])}
{context_section}
## 분석할 사용자 메시지
"{user_message}"

## 교정 원칙
- **말투(speech level)는 여러 오류 유형 중 하나입니다.** 조사·동사 활용·어휘가 틀렸다면 그것을 먼저 지적하세요.
- 조사 오류(이/가, 을/를, 은/는, 에/에서/에게 혼동)는 항상 별도 correction으로 명시하세요.
- 동사 불규칙 활용 오류(ㄷ불규칙, ㅂ불규칙, 르불규칙 등)도 명시하세요.
- 말투가 맞더라도 조사나 어미가 틀렸으면 has_errors를 true로 처리하세요.
- 사용자의 의도, 관계의 거리감, 문장의 온도를 최대한 유지한 채 최소한으로 고치세요.
- 단순한 문법 정답보다 실제 대화에서 더 자연스럽게 들리는 표현을 우선하세요.
- 원래 문장도 충분히 자연스러우면 억지로 바꾸지 마세요.
- 번역투, 어색한 조사, 부자연스러운 어순, 관계에 안 맞는 말투만 선별적으로 고치세요.
{strategy_line}
{situation_section}
{konlpy_section}
## corrected_message 생성 규칙 (반드시 준수)
corrected_message는 **발견된 모든 오류를 함께 수정한** 가장 자연스러운 한국어 문장입니다.
말투(speech level)는 여러 오류 유형 중 하나일 뿐이며, 조사·동사 활용·어휘 오류가 있다면 그것도 함께 고쳐야 합니다.

✅ 올바른 예:
- "저는 밥을 먹었어" (조사 맞지만 반말) → "저는 밥을 먹었습니다." (말투만 수정)
- "나는 밥을 먹었어" (조사+반말) → "저는 밥을 먹었습니다." (조사+말투 함께 수정)
- "도서관에서 책을 보다" (어색한 어미) → "도서관에서 책을 봤습니다." (어미 수정)
- "안녕 모해" → "안녕하십니까, 뭐 하십니까?" (어휘 보존, 말투 변환)

❌ 잘못된 예 (절대 금지):
- "안녕 모해" → "안녕하십니까, 어떻게 지내십니까?" (뜻이 달라짐)
- "밥 먹었어?" → "오늘 점심은 드셨나요?" (새 정보 추가)

**단계별 작업:**
1. **오타·맞춤법**을 가장 먼저 수정하세요 (예: 면당→면담, 됬→됐). corrected_message에 오타가 하나라도 남으면 안 됩니다.
2. 조사 오류(을/를, 이/가, 은/는, 에/에서 등)를 확인하세요.
3. 동사 활용 오류(불규칙 활용, 어미 오류)를 확인하세요.
4. 어휘 선택이 관계/상황에 맞는지 확인하세요.
5. 마지막으로 말투({speech_info['name_ko']}) 끝맺음을 맞추세요.
6. 위 1~5를 모두 반영한 corrected_message를 작성하세요.
7. 결과 문장이 원문과 핵심 의미가 다르면 다시 작성하세요.
8. 서비스/주문 상황에서는 메뉴 이름·수량·핵심 명사를 보존하세요.

## 응답 형식 (JSON only)
{{
    "edit_strategy": "none / minimal / rewrite",
    "has_errors": true,
    "corrected_message": "오류가 있으면 의미를 보존하여 {speech_info['name_ko']}로 수정한 전체 메시지. 오류 없으면 null",
    "detected_speech_level": "formal / polite / informal / unknown 중 하나",
    "speech_level_correct": false,
    "accuracy_score": 85,
    "corrections": [
        {{
            "original": "반드시 사용자 메시지에 실제로 존재하는 정확한 부분 문자열",
            "corrected": "올바른 표현 (말투 변환이 아닌 경우 같은 speech level로 수정)",
            "type": "speech_level/grammar/spelling/vocabulary/expression/honorific",
            "severity": "info/warning/error",
            "explanation": "왜 고치면 좋은지 한국어 한 문장 — 학습 포인트를 명확히 설명하세요",
            "tip": "관련 문법 규칙이나 패턴을 한 줄로 (예: '받침 있으면 을, 없으면 를') 또는 null"
        }}
    ],
    "natural_alternatives": [
        {{
            "expression": "사용자가 그대로 따라 말할 수 있는 완전한 한국어 문장",
            "explanation": "왜 이 표현이 더 자연스러운지 한국어 한 문장"
        }}
    ],
    "encouragement": "잘한 점을 언급한 긍정적인 피드백 (1문장)"
}}

## JSON 계약
- JSON 객체 하나만 출력하세요. 마크다운, 코드블록, 설명 문장, 추가 키는 금지합니다.
- 모든 문자열 값은 한국어로 작성하세요. 단, type/severity/level 코드는 지정된 영어 코드만 사용하세요.
- corrected_message는 사용자의 원래 의미를 보존해야 합니다. 새 정보, 새 감정, 새 의도를 추가하지 마세요. 어휘를 다른 뜻의 단어로 교체하지 마세요 — 말투 변환(어미·존칭)만 허용됩니다.
- has_errors가 false이면 corrected_message는 null, corrections는 [], natural_alternatives는 []로 두세요.
- has_errors가 true이면 corrected_message는 null이 아니어야 합니다.
- corrections[].original은 반드시 사용자 메시지에 실제로 있는 텍스트와 정확히 일치해야 합니다.
- 부분 문자열이 애매하면 original에 전체 사용자 메시지를 넣으세요.
- 같은 오류를 여러 번 반복하지 마세요.

## natural_alternatives 규칙
- natural_alternatives는 선택사항입니다. 정말 더 자연스럽고 학습 가치가 있을 때만 0~1개 제안하세요.
- 오류가 없고 현재 문장이 이미 자연스러우면 natural_alternatives는 빈 배열로 두세요.
- corrected_message와 의미 차이가 거의 없거나 단순 어미만 바꾼 수준이면 굳이 alternative를 만들지 마세요.
- 같은 의미지만 더 자연스럽고 세련된 {speech_info['name_ko']} 표현으로만 제안하세요.
- 원어민이 실제로 쓰는 표현으로, 대화 맥락에 맞는 표현만 제안하세요.
- "이렇게도 말할 수 있어요", "더 자연스러운 표현", "변경할 필요가 없습니다" 같은 메타 문구를 expression에 쓰지 마세요.
- expression은 반드시 사용자가 실제로 바로 따라 말할 수 있는 완전한 한국어 문장만 쓰세요.
- corrected_message와 완전히 같은 문장을 natural_alternatives에 다시 넣지 마세요.

## 절대 규칙
- detected_speech_level 은 formal / polite / informal / unknown 중 하나 (null 불가)
- corrected_message 는 모든 오류(조사·어미·어휘·말투)를 함께 수정한 문장. 말투 오류가 없으면 {speech_info['name_ko']}로 강제 변환하지 마세요.
- corrections original 은 사용자 메시지에 실제 존재하는 표현만
- 맥락상 자연스러운 표현은 오류 처리 금지
- 한국어의 자연스러운 여운, 완곡함, 구어적 뉘앙스를 기계적으로 교정하지 마세요.
- 받아들일 수 있는 구어체, 담화 표지, 친근한 말버릇은 의미나 관계를 해치지 않으면 오류로 처리하지 마세요.
- 확실하지 않으면 과교정보다 보수적으로 판단하세요.
- 오류 없으면 corrections 빈 배열, has_errors false"""


def _is_valid_natural_alternative(
    expression: str,
    explanation: str,
    user_message: str,
    corrected_message: Optional[str],
    expected_norm: Optional[str] = None,
) -> bool:
    expression = (expression or "").strip()
    explanation = (explanation or "").strip()
    user_message = (user_message or "").strip()
    corrected_message = (corrected_message or "").strip()

    if not expression:
        return False
    if len(expression) < 2:
        return False
    if any(pattern.search(expression) for pattern in _BAD_NATURAL_ALT_PATTERNS):
        return False
    if expression == user_message:
        return False
    if corrected_message and expression == corrected_message:
        return False
    if explanation and any(pattern.search(explanation) for pattern in _BAD_NATURAL_ALT_PATTERNS):
        return False
    if expected_norm:
        detected_norm = verify_with_rules(apply_spelling_fixes(expression), "")
        if detected_norm and detected_norm != expected_norm:
            return False
    normalized_expression = re.sub(r"\s+", " ", expression).strip()
    normalized_user = re.sub(r"\s+", " ", user_message).strip()
    normalized_corrected = re.sub(r"\s+", " ", corrected_message).strip() if corrected_message else ""
    if normalized_expression in {normalized_user, normalized_corrected}:
        return False
    if normalized_corrected:
        shared_prefix = 0
        for left, right in zip(normalized_expression, normalized_corrected):
            if left != right:
                break
            shared_prefix += 1
        if shared_prefix >= max(4, min(len(normalized_expression), len(normalized_corrected)) - 1):
            return False
    return True


def build_contextual_hint_prompt(
    avatar:               AvatarBase,
    conversation_history: List[ChatMessage],
    user_level:           str,
) -> str:
    speech_levels = get_speech_levels_for_role(avatar.role)
    speech_info   = SPEECH_LEVEL_INFO[speech_levels["from_user"]]
    recent        = conversation_history[-4:] if conversation_history else []
    context       = "\n".join([
        f"{'사용자' if m.role == 'user' else avatar.name_ko}: {m.content}"
        for m in recent
    ])

    return f"""대화 맥락을 보고 사용자에게 도움이 될 힌트를 제공하세요.

## 아바타 정보
- 이름: {avatar.name_ko}
- 관계: {get_role_label(avatar.role, None)}
- 관심사: {', '.join(avatar.interests[:3]) if avatar.interests else '다양한 주제'}

## 사용해야 할 말투
{speech_info['name_ko']}: {speech_info['description']}

## 최근 대화
{context if context else "(대화 시작)"}

다음 JSON 형식으로 응답하세요:
{{
    "hint": "지금 상황에서 사용할 수 있는 자연스러운 표현 1-2개",
    "example_responses": ["응답 예시 1", "응답 예시 2", "응답 예시 3"],
    "grammar_tip": "이 상황에서 유용한 문법 포인트 (선택사항)"
}}"""


RELATIONSHIP_KEYWORDS = {
    "service": ["카페", "주문", "식당", "매장", "계산", "직원", "점원", "사장님", "접수", "데스크", "배달"],
    "professor": ["교수", "연구실", "면담", "발표", "수업", "조교"],
    "senior": ["선배", "동아리", "사수", "팀장"],
    "first_meeting": ["처음", "첫 만남", "소개", "면접", "방문"],
}

REQUEST_INTENT_KEYWORDS = {
    "order": ["주문", "주세요", "하나", "한 잔", "두 잔", "포장", "추가", "빼주세요"],
    "request": ["도와", "부탁", "가능", "해줘", "해 주세요", "주면", "주실", "부탁드려"],
    "question": ["?", "뭐", "언제", "어디", "왜", "어떻게", "가능한가", "있나요"],
}


def infer_situation_signals(
    situation: Optional[str],
    avatar_role: str,
    expected_norm: str,
) -> Dict[str, Any]:
    combined = " ".join(part for part in [situation or "", avatar_role or ""] if part).strip()
    text = combined.lower()

    service = any(keyword in combined for keyword in RELATIONSHIP_KEYWORDS["service"])
    professor = any(keyword in combined for keyword in RELATIONSHIP_KEYWORDS["professor"])
    senior = any(keyword in combined for keyword in RELATIONSHIP_KEYWORDS["senior"])
    first_meeting = any(keyword in combined for keyword in RELATIONSHIP_KEYWORDS["first_meeting"])

    if professor:
        counterpart = "교수/선생님"
        power_direction = "other_higher"
    elif senior:
        counterpart = "선배/윗사람"
        power_direction = "other_higher"
    elif service:
        counterpart = "서비스 상대"
        power_direction = "distant_equal"
    else:
        counterpart = avatar_role or "대화 상대"
        power_direction = "peer"

    if expected_norm == "formal" or professor:
        formality = "high"
    elif expected_norm == "polite" or service or first_meeting:
        formality = "medium"
    else:
        formality = "low"

    return {
        "combined_text": combined,
        "counterpart": counterpart,
        "power_direction": power_direction,
        "service_situation": service,
        "first_meeting": first_meeting,
        "formality": formality,
    }


def infer_message_intent(
    user_message: str,
    situation_signals: Dict[str, Any],
) -> str:
    text = (user_message or "").strip()
    if any(keyword in text for keyword in REQUEST_INTENT_KEYWORDS["order"]) and situation_signals.get("service_situation"):
        return "order"
    if any(keyword in text for keyword in REQUEST_INTENT_KEYWORDS["request"]):
        return "request"
    if any(keyword in text for keyword in REQUEST_INTENT_KEYWORDS["question"]):
        return "question"
    if re.search(r"(안녕|반가워|처음 뵙|오랜만|잘 지내)", text):
        return "greeting"
    return "small_talk"


def should_use_benchmark_case(
    user_message: str,
    expected_norm: str,
    situation_signals: Dict[str, Any],
    message_intent: str,
) -> bool:
    text = (user_message or "").strip()
    if not text:
        return False
    if len(text) > 12:
        return False
    if situation_signals.get("service_situation"):
        return False
    if situation_signals.get("first_meeting"):
        return False
    if situation_signals.get("power_direction") == "other_higher":
        return False
    if message_intent in {"order", "request", "question"}:
        return False
    return lookup_benchmark_case(user_message, expected_norm) is not None


def extract_konlpy_prompt_hints(text: str) -> Dict[str, Any]:
    hints = {
        "nouns": [],
        "verbs": [],
        "endings": [],
    }
    try:
        analysis = morpheme_analyzer.analyze(text)
        hints["nouns"] = [noun for noun in getattr(analysis, "nouns", [])[:4] if noun]
        hints["verbs"] = [verb for verb in getattr(analysis, "verbs", [])[:3] if verb]
        hints["endings"] = [ending for ending in getattr(analysis, "endings", [])[:4] if ending]
    except Exception:
        pass
    return hints


# ============================================================================
# 말투 레벨 정규화 맵
# ============================================================================
LEVEL_MAP = {
    "반말":             "informal", "informal":          "informal",
    "비격식":           "informal", "casual":            "informal",
    "편한말":           "informal", "편한 말":           "informal",
    "해요체":           "polite",   "polite":            "polite",
    "존댓말":           "polite",   "공손한 말투":       "polite",
    "공손한말투":       "polite",   "공손":              "polite",
    "공손한":           "polite",   "경어":              "polite",
    "정중한 말투":      "polite",   "정중한말투":        "polite",
    "정중":             "polite",   "높임말":            "polite",
    "높임":             "polite",   "존대":              "polite",
    "합쇼체":           "formal",   "formal":            "formal",
    "격식체":           "formal",   "격식":              "formal",
    "격식적":           "formal",   "공식적":            "formal",
}

_FORMAL_ENDINGS   = ["습니다", "습니까", "십니까", "겠습니다", "십시오", "으십시오", "니다", "니까"]
_POLITE_ENDINGS   = ["어요", "아요", "이에요", "예요", "해요", "세요",
                     "네요", "군요", "죠", "나요", "가요", "래요",
                     "데요", "을게요", "ㄹ게요", "겠어요"]
_INFORMAL_ENDINGS = ["이야", "야", "이어", "어", "아", "지", "니",
                     "냐", "거야", "잖아", "이잖아", "구나", "군",
                     "을게", "ㄹ게", "자", "해", "래", "네",
                     "돼", "줘", "봐", "봐라", "와"]
_GENERIC_GREETING_CORRECTIONS = {"안녕", "안녕하세요", "안녕하십니까"}

_SHORT_RESPONSES = {
    "응", "어", "네", "넵", "넹", "예", "아니", "아니요", "ㅇ", "ㅇㅇ",
    "ㄴㄴ", "ㄴ", "그래", "응응", "오", "아", "음", "흠", "헐", "와",
    "오케이", "ok", "OK", "ㅋㅋ", "ㅎㅎ", "맞아", "맞아요", "그렇구나",
}

LEVEL_KO_LABELS = {
    "formal": "합쇼체",
    "polite": "해요체",
    "informal": "반말",
    "unknown": "불분명한 말투",
}

_LEVEL_EXAMPLES = {
    "formal": "안녕하십니까. 만나서 반갑습니다.",
    "polite": "안녕하세요. 만나서 반가워요.",
    "informal": "안녕. 만나서 반가워.",
}

_COMMON_TYPO_FIXES = [
    ("안녕하새요", "안녕하세요", "'안녕하새요'는 오타이고, 표준 표현은 '안녕하세요'입니다."),
    ("안녕하세여", "안녕하세요", "'안녕하세여'는 채팅식 표기이고, 연습 문장에서는 '안녕하세요'가 자연스럽습니다."),
    ("감사함니다", "감사합니다", "'감사함니다'가 아니라 '감사합니다'로 적는 것이 맞습니다."),
    ("어떻개", "어떻게", "'어떻개'는 오타이고, '어떻게'가 맞습니다."),
    ("어떡게", "어떻게", "'어떡게'는 오타이고, '어떻게'가 맞습니다."),
    ("괜찬", "괜찮", "'괜찬'보다 '괜찮'이 맞는 표기입니다."),
    ("할께", "할게", "미래의 의지를 말할 때는 '할게'가 자연스럽고 맞는 표기입니다."),
    ("되요", "돼요", "'되요'보다 '돼요'가 맞는 표기입니다."),
    ("됬", "됐", "'됬'은 잘못된 표기이고, '됐'이 맞습니다."),
    ("오랫만", "오랜만", "'오랫만'이 아니라 '오랜만'이 맞는 표기입니다."),
    ("몇일", "며칠", "'몇일'보다 '며칠'이 표준어입니다."),
    ("왠만", "웬만", "'왠만'이 아니라 '웬만'이 맞습니다."),
    ("설겆이", "설거지", "'설겆이'보다 '설거지'가 표준어입니다."),
    ("반가워여", "반가워요", "'반가워여'는 채팅식 표기이고, 연습 문장에서는 '반가워요'가 자연스럽습니다."),
    ("고마워여", "고마워요", "'고마워여'는 채팅식 표기이고, 연습 문장에서는 '고마워요'가 자연스럽습니다."),
    ("미안해여", "미안해요", "'미안해여'는 채팅식 표기이고, 연습 문장에서는 '미안해요'가 자연스럽습니다."),
    ("한잔", "한 잔", "'한잔'보다 '한 잔'처럼 띄어 쓰는 것이 자연스럽습니다."),
    ("두개", "두 개", "'두개'보다 '두 개'처럼 띄어 쓰는 것이 자연스럽습니다."),
    ("세개", "세 개", "'세개'보다 '세 개'처럼 띄어 쓰는 것이 자연스럽습니다."),
    ("갑시당", "갑시다", "'갑시당'은 장난스러운 채팅식 표기이고, 연습 문장에서는 '갑시다'가 자연스럽습니다."),
    ("봅시당", "봅시다", "'봅시당'은 장난스러운 채팅식 표기이고, 연습 문장에서는 '봅시다'가 자연스럽습니다."),
    ("합시당", "합시다", "'합시당'은 장난스러운 채팅식 표기이고, 연습 문장에서는 '합시다'가 자연스럽습니다."),
]

_CORRECTION_BENCHMARK_CASES = [
    {
        "pattern": re.compile(r"^안녕하새요[.!?…]*$"),
        "expected_norm": "informal",
        "detected_norm": "polite",
        "corrected": "안녕",
        "verdict": "speech_and_spelling",
        "summary": "오타와 말투를 함께 고치면 더 자연스러워요.",
        "type": CorrectionType.SPEECH_LEVEL,
        "severity": CorrectionSeverity.ERROR,
        "explanation": "오타를 고치고 반말로 바꾸면 더 자연스럽습니다.",
    },
    {
        "pattern": re.compile(r"^갑시당[.!?…]*$"),
        "expected_norm": "informal",
        "detected_norm": "formal",
        "corrected": "가자",
        "verdict": "speech_and_spelling",
        "summary": "장난스러운 표기와 말투를 함께 고치면 더 자연스러워요.",
        "type": CorrectionType.SPEECH_LEVEL,
        "severity": CorrectionSeverity.ERROR,
        "explanation": "채팅식 표기인 '갑시당' 대신 반말 권유형으로 바꾸는 것이 자연스럽습니다.",
    },
    {
        "pattern": re.compile(r"^카페 갑시당[.!?…]*$"),
        "expected_norm": "informal",
        "detected_norm": "formal",
        "corrected": "카페 가자",
        "verdict": "speech_and_spelling",
        "summary": "장난스러운 표기와 말투를 함께 고치면 더 자연스러워요.",
        "type": CorrectionType.SPEECH_LEVEL,
        "severity": CorrectionSeverity.ERROR,
        "explanation": "채팅식 표기와 격식체를 반말 권유형으로 바꾸는 것이 자연스럽습니다.",
    },
    {
        "pattern": re.compile(r"^같이 가요[.!?…]*$"),
        "expected_norm": "informal",
        "detected_norm": "polite",
        "corrected": "같이 가자",
        "verdict": "wrong_speech_level",
        "summary": "반말에 맞게 끝맺음을 바꾸면 더 자연스러워요.",
        "type": CorrectionType.SPEECH_LEVEL,
        "severity": CorrectionSeverity.ERROR,
        "explanation": "의미는 자연스럽지만 반말 관계라면 권유형도 반말로 맞추는 편이 좋습니다.",
    },
    {
        "pattern": re.compile(r"^어떻개 지내\??$"),
        "expected_norm": "polite",
        "detected_norm": "informal",
        "corrected": "어떻게 지내세요?",
        "verdict": "speech_and_spelling",
        "summary": "오타와 말투를 함께 고치면 더 자연스러워요.",
        "type": CorrectionType.SPEECH_LEVEL,
        "severity": CorrectionSeverity.ERROR,
        "explanation": "오타를 고치고 해요체로 바꾸면 더 자연스럽습니다.",
    },
    {
        "pattern": re.compile(r"^안녕하십니까[.!?…]*$"),
        "expected_norm": "polite",
        "detected_norm": "formal",
        "corrected": "안녕하세요",
        "verdict": "wrong_speech_level",
        "summary": "조금 덜 격식 있는 해요체로 바꾸면 지금 관계에 더 잘 맞아요.",
        "type": CorrectionType.SPEECH_LEVEL,
        "severity": CorrectionSeverity.WARNING,
        "explanation": "문장은 맞지만 지금 관계에서는 해요체가 더 자연스럽습니다.",
    },
    {
        "pattern": re.compile(r"^교수님 안녕[.!?…]*$"),
        "expected_norm": "polite",
        "detected_norm": "informal",
        "corrected": "교수님, 안녕하세요.",
        "verdict": "wrong_speech_level",
        "summary": "호칭과 인사말을 함께 다듬으면 더 자연스러워요.",
        "type": CorrectionType.HONORIFIC,
        "severity": CorrectionSeverity.ERROR,
        "explanation": "교수님처럼 높여야 하는 상대에게는 인사말도 더 공손하게 하는 편이 자연스럽습니다.",
    },
    {
        "pattern": re.compile(r"^봄축제야[.!?…]*$"),
        "expected_norm": "informal",
        "detected_norm": "informal",
        "corrected": "봄축제야",
        "verdict": "ok",
        "summary": "",
        "type": CorrectionType.EXPRESSION,
        "severity": CorrectionSeverity.INFO,
        "explanation": "문맥상 자연스러운 표현입니다.",
    },
]

_DIAGNOSTIC_REPLY_PATTERN = re.compile(
    r"(polite|formal|informal|speech level|detected|accuracy|score|감지|점수|정확도|분석 결과|말투 분석)",
    re.IGNORECASE,
)

_GENERIC_REPLY_PATTERN = re.compile(
    r"(네,?\s*그렇군요|더 이야기해|계속.*대화|무엇을 도와|도와드릴|말씀해 주세요)"
)

_INFORMAL_TO_POLITE = {
    "이야": "이에요", "거야": "거예요", "잖아": "잖아요", "구나": "군요",
    "거든": "거든요", "지만": "지만요", "는데": "는데요", "ㄴ데": "ㄴ데요",
    "을게": "을게요", "ㄹ게": "ㄹ게요", "을래": "을래요", "ㄹ래": "ㄹ래요",
    "을까": "을까요", "ㄹ까": "ㄹ까요", "싶음": "싶어요", "없음": "없어요",
    "있음": "있어요", "함": "해요", "임": "이에요", "음": "어요",
    "야": "요", "해": "해요", "어": "어요", "아": "아요",
    "지": "지요", "군": "군요", "네": "네요", "래": "래요", "자": "시죠",
}

_INFORMAL_TO_FORMAL = {
    "이야": "입니다", "거야": "겁니다", "싶음": "싶습니다",
    "없음": "없습니다", "있음": "있습니다", "함": "합니다",
    "임": "입니다", "음": "습니다", "야": "습니다",
    "해": "합니다", "어": "습니다", "아": "습니다",
    "지": "지요", "군": "군요", "네": "네요",
}


def simple_convert_to_level(text: str, target: str) -> Optional[str]:
    text  = text.strip()
    converted_hapsida = convert_hapsida_to_target(text, target)
    if converted_hapsida and converted_hapsida != text:
        return converted_hapsida
    if target == "informal":
        invitation_converted = replace_all(text, [
            (r"같이 가요([?？!]?)$", r"같이 가자\1"),
            (r"같이 해요([?？!]?)$", r"같이 하자\1"),
            (r"같이 봐요([?？!]?)$", r"같이 보자\1"),
            (r"같이 먹어요([?？!]?)$", r"같이 먹자\1"),
            (r"같이 마셔요([?？!]?)$", r"같이 마시자\1"),
        ]).strip()
        if invitation_converted and invitation_converted != text:
            return invitation_converted
        changed = replace_all(text, [
            (r"안녕하세요", "안녕"),
            (r"안녕하십니까", "안녕"),
            (r"감사합니다|고마워요", "고마워"),
            (r"죄송합니다|죄송해요|미안해요", "미안해"),
            (r"어떻게 지내세요[?？]?|어떻게 지내요[?？]?", "어떻게 지내?"),
            (r"([가-힣]+)이에요$", r"\1이야"),
            (r"([가-힣]+)예요$", r"\1야"),
            (r"([가-힣]+)요$", r"\1"),
        ]).strip()
        return changed if changed and changed != text else None
    table = _INFORMAL_TO_POLITE if target == "polite" else _INFORMAL_TO_FORMAL
    for informal, formal in sorted(table.items(), key=lambda x: -len(x[0])):
        if text.endswith(informal):
            return text[: -len(informal)] + formal
    if target == "formal":
        haeyo_converted = convert_haeyo_to_hapsyo(text)
        if haeyo_converted and haeyo_converted != text:
            return haeyo_converted
    if target == "polite":
        best_effort = best_effort_informal_to_polite(text)
        return best_effort if best_effort != text else None
    return None


def get_final_consonant_index(char: str) -> int:
    if not char or len(char) != 1:
        return -1
    code = ord(char)
    if not (0xAC00 <= code <= 0xD7A3):
        return -1
    return (code - 0xAC00) % 28


def has_batchim_bieup(char: str) -> bool:
    return get_final_consonant_index(char) == 17


def remove_final_bieup(char: str) -> str:
    return chr(ord(char) - 17) if has_batchim_bieup(char) else char


def ends_with_hapsida_formal(text: str) -> bool:
    if text.endswith("읍시다") or text.endswith("십시다"):
        return True
    if not text.endswith("시다") or len(text) < 3:
        return False
    return has_batchim_bieup(text[-3])


def convert_hapsida_to_target(text: str, target: str) -> Optional[str]:
    trailing_match = re.search(r'([.!?…。？！"\'\)\]\s]*)$', text)
    trailing = trailing_match.group(1) if trailing_match else ""
    core = text[: len(text) - len(trailing)] if trailing else text
    if not core:
        return None

    if target == "informal":
        if core.endswith("읍시다") and len(core) >= 4:
            return f"{core[:-4]}{core[-4]}자{trailing}"
        if core.endswith("시다") and len(core) >= 3 and has_batchim_bieup(core[-3]):
            return f"{core[:-3]}{remove_final_bieup(core[-3])}자{trailing}"

    if target == "polite":
        replacements = {
            "갑시다": "가요",
            "봅시다": "봐요",
            "합시다": "해요",
            "해봅시다": "해봐요",
        }
        for original, corrected in replacements.items():
            if core.endswith(original):
                return f"{core[:-len(original)]}{corrected}{trailing}"

    return None


_POLITE_TO_FORMAL_STATEMENT = {
    "이에요": "입니다", "예요": "입니다", "있어요": "있습니다", "없어요": "없습니다",
    "해요": "합니다", "돼요": "됩니다", "와요": "옵니다", "봐요": "봅니다",
    "줘요": "줍니다", "가요": "갑니다", "세요": "십니다", "워요": "웁니다",
    "아요": "습니다", "어요": "습니다", "여요": "입니다",
}

_POLITE_TO_FORMAL_QUESTION = {
    "이에요": "입니까", "예요": "입니까", "있어요": "있습니까", "없어요": "없습니까",
    "해요": "합니까", "돼요": "됩니까", "와요": "옵니까", "봐요": "봅니까",
    "줘요": "줍니까", "가요": "갑니까", "세요": "십니까", "워요": "웁니까",
    "아요": "습니까", "어요": "습니까", "여요": "입니까",
}


def convert_haeyo_to_hapsyo(text: str) -> Optional[str]:
    """해요체 종결 어미를 합쇼체(-습니다/-습니까)로 변환합니다."""
    trailing_match = re.search(r'([.!?…。？！"\'\)\]\s]*)$', text)
    trailing = trailing_match.group(1) if trailing_match else ""
    core = text[: len(text) - len(trailing)] if trailing else text
    if not core:
        return None
    is_question = "?" in trailing or "？" in trailing or core.endswith("까요") or core.endswith("나요")
    table = _POLITE_TO_FORMAL_QUESTION if is_question else _POLITE_TO_FORMAL_STATEMENT
    for ending, formal in sorted(table.items(), key=lambda x: -len(x[0])):
        if core.endswith(ending):
            return f"{core[:-len(ending)]}{formal}{trailing}"
    return None


def verify_with_rules(text: str, clova_detected: str) -> str:
    text = re.sub(r"[.!?…。？！\"')\]\s]+$", "", text.strip())
    clova_detected = LEVEL_MAP.get((clova_detected or "").strip().lower(), clova_detected or "")
    if ends_with_hapsida_formal(text):
        return "formal"
    if re.search(r"(안녕하세요|고마워요|감사해요|미안해요|죄송해요|반가워요|괜찮아요|좋아요|있어요|없어요|이에요|예요|세요|해요|아요|어요|나요|죠|지요|네요|군요|까요)$", text):
        return "polite"
    if re.search(r"(어떻게 지내|뭐 해|뭐해|잘 지내|했어|할래|줄래|가자|먹자|보자|자)$", text):
        return "informal"
    for e in _FORMAL_ENDINGS:
        if text.endswith(e): return "formal"
    for e in _POLITE_ENDINGS:
        if text.endswith(e): return "polite"
    for e in _INFORMAL_ENDINGS:
        if text.endswith(e): return "informal"
    # Surface regex didn't fire — try Komoran morpheme analysis. This catches
    # contractions and irregular forms where the final 어미 isn't visible as a
    # word suffix (e.g. "안 해도 돼" ends in the morpheme 어, not 돼).
    morph_level = detect_speech_level_by_morpheme(text)
    if morph_level:
        return morph_level
    return clova_detected


def _prefer_rule_correction(
    user_message: str,
    clova_corrected: str,
    rule_corrected: Optional[str],
    expected_norm: str,
) -> Optional[str]:
    if not rule_corrected:
        return None
    if verify_with_rules(rule_corrected, "") != expected_norm:
        return None
    if not clova_corrected:
        return rule_corrected
    if clova_corrected in _GENERIC_GREETING_CORRECTIONS and "안녕" not in user_message:
        return rule_corrected
    if (
        clova_corrected in _GENERIC_GREETING_CORRECTIONS
        and not re.search(r"(안녕|반가워|처음 뵙|오랜만)", user_message)
    ):
        return rule_corrected
    if len(clova_corrected) <= 3 and len(rule_corrected) > len(clova_corrected):
        return rule_corrected
    return None


def normalize_level_code(level: Optional[str]) -> str:
    if not level:
        return ""
    normalized = str(level).strip().lower()
    compact = re.sub(r"\s+", "", normalized)
    return LEVEL_MAP.get(normalized) or LEVEL_MAP.get(compact) or normalized


def coerce_speech_level(level: Optional[str], fallback: SpeechLevel) -> SpeechLevel:
    normalized = normalize_level_code(level)
    try:
        return SpeechLevel(normalized) if normalized else fallback
    except ValueError:
        return fallback


def get_typo_corrections(text: str) -> List[InlineCorrection]:
    corrections: List[InlineCorrection] = []
    for original, corrected, explanation in _COMMON_TYPO_FIXES:
        if original in text:
            corrections.append(InlineCorrection(
                original=original,
                corrected=corrected,
                type=CorrectionType.SPELLING,
                severity=CorrectionSeverity.ERROR,
                explanation=explanation,
            ))
    return corrections


def apply_spelling_fixes(text: str) -> str:
    fixed = text
    for original, corrected, _ in _COMMON_TYPO_FIXES:
        fixed = fixed.replace(original, corrected)
    return fixed


def replace_all(text: str, pairs: List[tuple]) -> str:
    result = text
    for pattern, replacement in pairs:
        result = re.sub(pattern, replacement, result)
    return result


def normalize_benchmark_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def lookup_benchmark_case(user_message: str, expected_norm: str) -> Optional[Dict[str, Any]]:
    normalized = normalize_benchmark_text(user_message)
    for case in _CORRECTION_BENCHMARK_CASES:
        if case["expected_norm"] != expected_norm:
            continue
        if case["pattern"].match(normalized):
            return case
    return None


def build_benchmark_correction(
    user_message: str,
    expected_speech_level: SpeechLevel,
    case: Dict[str, Any],
) -> RealTimeCorrection:
    expected_norm = expected_speech_level.value.lower()
    expected_label = SPEECH_LEVEL_INFO[expected_speech_level]["name_ko"]
    verdict = case["verdict"]
    corrected = case["corrected"]
    detected_norm = case["detected_norm"]
    spelling_count = len(get_typo_corrections(user_message))
    has_errors = verdict != "ok"

    corrections: List[InlineCorrection] = []
    if has_errors and case.get("corrections"):
        for item in case["corrections"]:
            corrections.append(InlineCorrection(
                original=item["original"],
                corrected=item["corrected"],
                type=item["type"],
                severity=item["severity"],
                explanation=item["explanation"],
                tip=item.get("tip"),
            ))
    elif has_errors:
        corrections.append(InlineCorrection(
            original=user_message,
            corrected=corrected,
            type=case["type"],
            severity=case["severity"],
            explanation=case["explanation"],
            tip=f"예시: {_LEVEL_EXAMPLES[expected_norm]}" if case["type"] == CorrectionType.SPEECH_LEVEL else None,
        ))

    if spelling_count and corrected != apply_spelling_fixes(user_message) and not case.get("corrections"):
        spelling_fixed = apply_spelling_fixes(user_message)
        corrections.append(InlineCorrection(
            original=user_message,
            corrected=spelling_fixed,
            type=CorrectionType.SPELLING,
            severity=CorrectionSeverity.WARNING,
            explanation="먼저 오타를 바로잡으면 의미가 더 분명해집니다.",
        ))

    score = 100
    if verdict == "speech_and_spelling":
        score = 50
    elif verdict == "spelling":
        score = 75
    elif verdict == "wrong_speech_level":
        score = 60

    return RealTimeCorrection(
        original_message=user_message,
        corrected_message=None if not has_errors else corrected,
        has_errors=has_errors,
        corrections=corrections,
        natural_alternatives=[],
        expected_speech_level=expected_label,
        expected_speech_level_code=expected_norm,
        detected_speech_level=LEVEL_KO_LABELS.get(detected_norm, detected_norm or expected_norm),
        detected_speech_level_code=detected_norm or expected_norm,
        speech_level_correct=detected_norm == expected_norm,
        accuracy_score=score,
        verdict=verdict,
        summary=build_human_feedback_summary(
            has_errors=has_errors,
            corrections=corrections,
            verdict=verdict,
            speech_level_correct=detected_norm == expected_norm,
            expected_speech_level=expected_speech_level,
            message_intent="small_talk",
        ),
        input_kind="benchmark",
        encouragement=build_human_encouragement(has_errors, corrections, "small_talk"),
    )


def classify_edit_strategy(
    user_message: str,
    local_rule_correction: RealTimeCorrection,
    native_feedback: Any,
) -> str:
    correction_types = {c.type for c in local_rule_correction.corrections}
    has_spelling = CorrectionType.SPELLING in correction_types
    has_speech = CorrectionType.SPEECH_LEVEL in correction_types
    has_native_content_issue = bool(
        getattr(native_feedback, "word_errors", None)
        or getattr(native_feedback, "missing_honorifics", None)
        or getattr(native_feedback, "is_mixed", False)
    )
    text = (user_message or "").strip()

    if not local_rule_correction.has_errors and not has_native_content_issue:
        return "none"
    if has_native_content_issue:
        return "rewrite"
    if correction_types and correction_types.issubset({CorrectionType.SPELLING, CorrectionType.SPEECH_LEVEL}):
        return "minimal"
    if (has_spelling or has_speech) and len(text) <= 18:
        return "minimal"
    return "rewrite"


def build_contextual_base_corrections(
    user_message: str,
    expected_speech_level: SpeechLevel,
    situation_signals: Dict[str, Any],
    message_intent: str,
) -> Dict[str, Any]:
    expected_norm = expected_speech_level.value.lower()
    corrections: List[InlineCorrection] = []
    corrected_message: Optional[str] = None
    text = (user_message or "").strip()

    if (
        message_intent == "greeting"
        and expected_norm in {"polite", "formal"}
        and "안녕하세요" not in text
        and "안녕하십니까" not in text
    ):
        greeting_match = re.search(r"안녕([.!?…]*)$", text)
        if greeting_match:
            target_greeting = "안녕하세요" if expected_norm == "polite" else "안녕하십니까"
            titled_match = re.match(r"^\s*([가-힣]+님)\s+안녕([.!?…]*)$", text)
            if titled_match:
                corrected_message = f"{titled_match.group(1)}, {target_greeting}{titled_match.group(2)}".strip()
            else:
                corrected_message = f"{text[:greeting_match.start()]}{target_greeting}{greeting_match.group(1)}".strip()
            correction_type = (
                CorrectionType.HONORIFIC
                if situation_signals.get("power_direction") == "other_higher" or situation_signals.get("first_meeting")
                else CorrectionType.SPEECH_LEVEL
            )
            corrections.append(InlineCorrection(
                original="안녕",
                corrected=target_greeting,
                type=correction_type,
                severity=CorrectionSeverity.ERROR,
                explanation="상대가 낯설거나 더 높여야 하는 관계라면 인사말도 더 공손하게 하는 편이 자연스럽습니다.",
                tip=f"예시: {_LEVEL_EXAMPLES[expected_norm]}",
            ))

    return {
        "corrections": corrections,
        "corrected_message": corrected_message,
    }


def build_minimal_edit_correction(
    user_message: str,
    expected_norm: str,
    local_rule_correction: RealTimeCorrection,
) -> Optional[str]:
    if not local_rule_correction.has_errors:
        return None
    correction_types = {c.type for c in local_rule_correction.corrections}
    has_spelling = CorrectionType.SPELLING in correction_types
    has_speech = CorrectionType.SPEECH_LEVEL in correction_types or not local_rule_correction.speech_level_correct

    if not has_spelling and not has_speech:
        return None
    if has_speech:
        return make_level_suggestion(user_message, expected_norm)
    if has_spelling:
        fixed = apply_spelling_fixes(user_message).strip()
        return fixed if fixed != user_message.strip() else None
    return None


def infer_surface_correction_type(original: str, corrected: str) -> CorrectionType:
    original = (original or "").strip()
    corrected = (corrected or "").strip()
    if not original or not corrected:
        return CorrectionType.EXPRESSION
    original_norm = re.sub(r"[.!?…\s]+$", "", original)
    corrected_norm = re.sub(r"[.!?…\s]+$", "", corrected)
    original_level = verify_with_rules(original_norm, "")
    corrected_level = verify_with_rules(corrected_norm, "")
    if (
        original_level
        and corrected_level
        and original_level != corrected_level
        and difflib.SequenceMatcher(
            a=original_norm.replace(" ", ""),
            b=corrected_norm.replace(" ", ""),
        ).ratio() >= 0.55
    ):
        return CorrectionType.SPEECH_LEVEL
    if any(
        [
            corrected_norm.endswith("까요") and original_norm.endswith("까"),
            corrected_norm.endswith("래요") and original_norm.endswith("래"),
            corrected_norm.endswith("어요") and original_norm.endswith("어"),
            corrected_norm.endswith("아요") and original_norm.endswith("아"),
            corrected_norm.endswith("해요") and original_norm.endswith("해"),
        ]
    ):
        return CorrectionType.SPEECH_LEVEL
    # Informal short-form endings (음/ㅁ/함) converting to formal/polite
    _informal_endings = ("음", "ㅁ", "함", "싶음", "겠음", "임", "됨", "없음", "있음")
    _formal_endings = ("습니다", "습니까", "어요", "아요", "세요", "십시오", "겠습니다")
    if (
        any(original_norm.endswith(e) for e in _informal_endings)
        and any(corrected_norm.endswith(e) for e in _formal_endings)
    ):
        return CorrectionType.SPEECH_LEVEL
    if any(token in corrected for token in ["주세요", "주실", "드려", "해 주세요", "해주시"]):
        return CorrectionType.HONORIFIC
    # Adding honorific title suffix (선배 → 선배님, 선생님 already ends in 님)
    if corrected_norm.endswith("님") and not original_norm.endswith("님"):
        return CorrectionType.HONORIFIC
    if any(token in corrected for token in ["저", "저는", "제가", "저를", "저한테"]):
        return CorrectionType.VOCABULARY
    if re.sub(r"\s+", "", original) == re.sub(r"\s+", "", corrected):
        return CorrectionType.SPELLING
    return CorrectionType.SPELLING


def infer_surface_explanation(original: str, corrected: str, correction_type: CorrectionType) -> str:
    if correction_type == CorrectionType.SPEECH_LEVEL:
        return "같은 의미라도 지금 상황에 맞는 말투로 끝맺음을 바꾸는 것이 자연스럽습니다."
    if correction_type == CorrectionType.HONORIFIC:
        return "상황에 맞게 요청 표현을 더 공손하게 바꾸는 것이 자연스럽습니다."
    if correction_type == CorrectionType.VOCABULARY:
        return "현재 관계와 상황에 더 맞는 어휘로 바꾸는 것이 자연스럽습니다."
    if original.replace(" ", "") == corrected.replace(" ", ""):
        return "띄어쓰기를 다듬으면 더 자연스럽습니다."
    return "표현을 자연스럽게 다듬으면 더 매끄럽게 들립니다."


def _score_alignment_candidate(original_token: str, candidate: str) -> float:
    original_norm = original_token.replace(" ", "")
    candidate_norm = candidate.replace(" ", "")
    if not original_norm or not candidate_norm:
        return 0.0

    ratio = difflib.SequenceMatcher(a=original_norm, b=candidate_norm).ratio()
    if candidate_norm == original_norm:
        ratio += 0.5
    if candidate_norm.startswith(original_norm) or original_norm.startswith(candidate_norm):
        ratio += 0.08
    if len(candidate.split()) > 1 and candidate_norm == original_norm:
        ratio += 0.2
    if re.search(r"(줘|주라|주면돼|주면 돼)$", original_token) and ("주세요" in candidate or "주실" in candidate):
        ratio += 0.45
    if re.search(r"(개|잔)$", original_norm) and candidate_norm == original_norm:
        ratio += 0.12
    return ratio


def _build_pattern_level_corrections(original_text: str, corrected_text: str) -> List[InlineCorrection]:
    derived: List[InlineCorrection] = []
    seen = set()

    def add(original: str, corrected: str, correction_type: CorrectionType, explanation: str) -> None:
        key = (original, corrected, correction_type)
        if not original or not corrected or original == corrected or key in seen:
            return
        seen.add(key)
        derived.append(InlineCorrection(
            original=original,
            corrected=corrected,
            type=correction_type,
            severity=CorrectionSeverity.ERROR if correction_type in {CorrectionType.HONORIFIC, CorrectionType.VOCABULARY} else CorrectionSeverity.WARNING,
            explanation=explanation,
        ))

    if "안녕" in original_text and "안녕하세요" in corrected_text and "안녕하세요" not in original_text:
        add("안녕", "안녕하세요", CorrectionType.SPEECH_LEVEL, "상황에 맞게 인사말을 더 공손하게 바꾸는 것이 자연스럽습니다.")
    if "안녕" in original_text and "안녕하십니까" in corrected_text and "안녕하십니까" not in original_text:
        add("안녕", "안녕하십니까", CorrectionType.SPEECH_LEVEL, "격식 있는 상황이라면 인사말도 더 높여서 쓰는 편이 자연스럽습니다.")

    for token in (original_text or "").strip().split():
        if token.endswith("줘") and "주세요" in corrected_text:
            add(token, f"{token[:-1]} 주세요" if len(token) > 1 else "주세요", CorrectionType.HONORIFIC, "요청 표현을 더 공손하게 바꾸는 것이 자연스럽습니다.")
        elif token.endswith("주라") and "주세요" in corrected_text:
            add(token, f"{token[:-2]}주세요" if len(token) > 2 else "주세요", CorrectionType.HONORIFIC, "명령형 대신 공손한 요청 표현을 쓰는 편이 자연스럽습니다.")

    corrected_tokens = re.sub(r"[.!?…]+$", "", (corrected_text or "").strip()).split()
    for token in (original_text or "").strip().split():
        compact = token.replace(" ", "")
        for idx in range(len(corrected_tokens) - 1):
            candidate = f"{corrected_tokens[idx]} {corrected_tokens[idx + 1]}"
            if candidate.replace(" ", "") == compact and candidate != token:
                add(token, candidate, CorrectionType.SPELLING, "띄어쓰기를 다듬으면 더 자연스럽습니다.")
                break

    return derived


def derive_surface_corrections(
    original_text: str,
    corrected_text: str,
) -> List[InlineCorrection]:
    original_tokens = (original_text or "").strip().split()
    corrected_tokens = re.sub(r"[.!?…]+$", "", (corrected_text or "").strip()).split()
    if not original_tokens or not corrected_tokens:
        return []

    derived: List[InlineCorrection] = _build_pattern_level_corrections(original_text, corrected_text)
    seen = {(item.original, item.corrected, item.type) for item in derived}
    corrected_index = 0

    for original_token in original_tokens:
        best_ratio = 0.0
        best_span = None
        for span_size in range(1, min(3, len(corrected_tokens) - corrected_index) + 1):
            candidate_tokens = corrected_tokens[corrected_index: corrected_index + span_size]
            candidate = " ".join(candidate_tokens).strip()
            ratio = _score_alignment_candidate(original_token, candidate)
            if ratio > best_ratio:
                best_ratio = ratio
                best_span = (candidate, corrected_index + span_size)

        if not best_span:
            continue

        corrected_chunk, next_index = best_span
        if corrected_chunk and original_token != corrected_chunk and best_ratio >= 0.45:
            correction_type = infer_surface_correction_type(original_token, corrected_chunk)
            key = (original_token, corrected_chunk, correction_type)
            if key not in seen:
                derived.append(InlineCorrection(
                    original=original_token,
                    corrected=corrected_chunk,
                    type=correction_type,
                    severity=CorrectionSeverity.ERROR if correction_type in {CorrectionType.HONORIFIC, CorrectionType.VOCABULARY} else CorrectionSeverity.WARNING,
                    explanation=infer_surface_explanation(original_token, corrected_chunk, correction_type),
                ))
                seen.add(key)
        corrected_index = next_index

    return derived


def best_effort_informal_to_polite(text: str) -> str:
    stripped = (text or "").strip()
    if not stripped:
        return stripped

    trailing_match = re.search(r'([.!?…。？！"\')\]\s]*)$', stripped)
    trailing = trailing_match.group(1) if trailing_match else ""
    core = stripped[: len(stripped) - len(trailing)] if trailing else stripped

    replacements = [
        (r"뭐해$", "뭐 해요"),
        (r"좋아해$", "좋아해요"),
        (r"싫어해$", "싫어해요"),
        (r"사랑해$", "사랑해요"),
        (r"괜찮아$", "괜찮아요"),
        (r"좋아$", "좋아요"),
        (r"싫어$", "싫어요"),
        (r"있어$", "있어요"),
        (r"없어$", "없어요"),
        (r"맞아$", "맞아요"),
        (r"알아$", "알아요"),
        (r"몰라$", "몰라요"),
        (r"해$", "해요"),
        (r"가$", "가요"),
        (r"와$", "와요"),
        (r"봐$", "봐요"),
        (r"먹어$", "먹어요"),
        (r"마셔$", "마셔요"),
        (r"줘$", "주세요"),
        (r"주라$", "주세요"),
        (r"주면\s*돼$", "주세요"),
        (r"야$", "예요"),
        (r"이야$", "이에요"),
    ]

    converted = core
    for pattern, replacement in replacements:
        updated = re.sub(pattern, replacement, converted)
        if updated != converted:
            converted = updated
            break

    if converted == core and not re.search(r"(요|니다|습니다|세요|까요)$", core):
        if core.endswith("어") or core.endswith("아") or core.endswith("해"):
            converted = f"{core}요"
        elif core.endswith("니") or core.endswith("냐"):
            converted = f"{core[:-1]}나요"

    return f"{converted}{trailing}".strip()


def prune_suspicious_corrections(
    corrections: List[InlineCorrection],
    corrected_message: Optional[str],
) -> List[InlineCorrection]:
    if not corrected_message:
        corrected_message = ""

    ranked: Dict[tuple, InlineCorrection] = {}
    for correction in corrections:
        corrected = correction.corrected.strip()
        original = correction.original.strip()
        if re.sub(r"[,.!?…]+", "", corrected).strip() == re.sub(r"[,.!?…]+", "", original).strip():
            continue
        if (
            correction.type == CorrectionType.SPELLING
            and len(corrected.replace(" ", "")) >= len(original.replace(" ", "")) + 4
            and original in corrected
            and corrected in corrected_message
            and original not in corrected_message
        ):
            continue
        if (
            correction.type == CorrectionType.SPELLING
            and corrected == corrected_message.strip()
            and original in corrected
            and any(item.original == "안녕" and item.corrected in corrected_message for item in corrections)
        ):
            continue
        normalized_corrected = re.sub(r"[.!?…]+$", "", corrected).strip()
        key = (original, normalized_corrected)
        existing = ranked.get(key)
        if not existing:
            ranked[key] = correction
            continue
        if existing.type == CorrectionType.SPELLING and correction.type != CorrectionType.SPELLING:
            ranked[key] = correction
            continue
        if existing.severity == CorrectionSeverity.WARNING and correction.severity == CorrectionSeverity.ERROR:
            ranked[key] = correction
    candidates = list(ranked.values())
    pruned: List[InlineCorrection] = []
    for correction in candidates:
        is_redundant = False
        for other in candidates:
            if other is correction:
                continue
            if len(other.original) <= len(correction.original):
                continue
            if correction.original in other.original and correction.corrected.replace(" ", "") in other.corrected.replace(" ", ""):
                is_redundant = True
                break
        if not is_redundant:
            pruned.append(correction)
    return pruned


def compose_corrected_message_from_corrections(
    original_message: str,
    corrections: List[InlineCorrection],
) -> Optional[str]:
    rebuilt = (original_message or "").strip()
    if not rebuilt:
        return None

    applicable = [
        correction for correction in corrections
        if correction.original and correction.corrected and correction.original != correction.corrected
    ]
    applicable.sort(key=lambda correction: len(correction.original), reverse=True)

    changed = False
    for correction in applicable:
        if correction.original in rebuilt:
            rebuilt = rebuilt.replace(correction.original, correction.corrected, 1)
            changed = True

    rebuilt = re.sub(r"\s{2,}", " ", rebuilt).strip()
    return rebuilt if changed and rebuilt != original_message.strip() else None


def make_level_suggestion(text: str, expected_norm: str) -> str:
    spelling_fixed = apply_spelling_fixes(text).strip()

    if expected_norm == "informal":
        converted_hapsida = convert_hapsida_to_target(spelling_fixed, "informal")
        if converted_hapsida and converted_hapsida != text:
            return converted_hapsida
        changed = replace_all(spelling_fixed, [
            (r"안녕하십니까|안녕하세요", "안녕"),
            (r"만나서 반갑습니다|만나서 반가워요", "만나서 반가워"),
            (r"감사합니다|고마워요", "고마워"),
            (r"죄송합니다|죄송해요|미안해요", "미안해"),
            (r"어떻게 지내세요[?？]?|어떻게 지내요[?？]?", "어떻게 지내?"),
            (r"이에요", "이야"),
            (r"예요", "야"),
            (r"입니다", "이야"),
            (r"([가-힣])요([.!?…。！]?)$", r"\1\2"),
            (r"습니다$", "어"),
            (r"니다$", "야"),
        ]).strip()
        return changed if changed and changed != text else spelling_fixed

    if expected_norm == "formal":
        changed = replace_all(spelling_fixed, [
            (r"안녕하세요|안녕", "안녕하십니까"),
            (r"만나서 반가워요|만나서 반가워", "만나서 반갑습니다"),
            (r"고마워요|고마워", "감사합니다"),
            (r"미안해요|미안해", "죄송합니다"),
            (r"어떻게 지내세요[?？]?|어떻게 지내요[?？]?|어떻게 지내[?？]?", "어떻게 지내십니까?"),
            (r"이에요|예요", "입니다"),
        ]).strip()
        return changed if changed and changed != text else spelling_fixed

    changed = replace_all(spelling_fixed, [
        (r"안녕하십니까|안녕", "안녕하세요"),
        (r"만나서 반갑습니다|만나서 반가워", "만나서 반가워요"),
        (r"감사합니다|고마워", "고마워요"),
        (r"죄송합니다|미안해", "미안해요"),
        (r"어떻게 지내십니까[?？]?|어떻게 지내[?？]?", "어떻게 지내세요?"),
    ]).strip()
    converted_hapsida = convert_hapsida_to_target(spelling_fixed, "polite")
    if converted_hapsida and converted_hapsida != text:
        return converted_hapsida
    best_effort = best_effort_informal_to_polite(spelling_fixed)
    if best_effort and best_effort != text:
        return best_effort
    return changed if changed and changed != text else spelling_fixed


def infer_verdict(
    has_errors: bool,
    typo_count: int,
    speech_level_correct: bool,
) -> str:
    if not has_errors:
        return "ok"
    if typo_count > 0 and not speech_level_correct:
        return "speech_and_spelling"
    if typo_count > 0:
        return "spelling"
    if not speech_level_correct:
        return "wrong_speech_level"
    return "needs_revision"


def build_rule_based_correction(
    user_message: str,
    expected_speech_level: SpeechLevel,
    base_corrections: Optional[List[InlineCorrection]] = None,
) -> RealTimeCorrection:
    expected_norm = expected_speech_level.value.lower()
    expected_label = SPEECH_LEVEL_INFO[expected_speech_level]["name_ko"]
    spelling_corrections = get_typo_corrections(user_message)
    corrections = [*(base_corrections or []), *spelling_corrections]
    spelling_fixed = apply_spelling_fixes(user_message)
    detected_norm = verify_with_rules(spelling_fixed, "")
    # Empty detection means rules couldn't classify the level — flag uncertainty
    # rather than auto-affirming. The LLM pass downstream gets the final say.
    speech_level_uncertain = (detected_norm == "")
    speech_level_correct   = (detected_norm == expected_norm) or speech_level_uncertain

    corrected_message = spelling_fixed if spelling_corrections else None
    if not speech_level_correct:
        corrected_message = make_level_suggestion(user_message, expected_norm)
        # Using informal when polite/formal is expected is a serious breach → ERROR.
        # Switching between polite and formal is a style mismatch, not rudeness → WARNING.
        _LEVEL_ORDER = {"informal": 0, "polite": 1, "formal": 2}
        is_rudeness = (
            _LEVEL_ORDER.get(detected_norm, 1) < _LEVEL_ORDER.get(expected_norm, 1) - 1
            or (detected_norm == "informal" and expected_norm != "informal")
        )
        speech_level_severity = CorrectionSeverity.ERROR if is_rudeness else CorrectionSeverity.WARNING
        corrections.insert(0, InlineCorrection(
            original=user_message,
            corrected=corrected_message,
            type=CorrectionType.SPEECH_LEVEL,
            severity=speech_level_severity,
            explanation=f"{expected_label}를 사용해야 합니다. 지금 문장은 {LEVEL_KO_LABELS.get(detected_norm, detected_norm)}에 가까워요.",
            tip=f"예시: {_LEVEL_EXAMPLES[expected_norm]}",
        ))

    has_errors = bool(corrections) or not speech_level_correct
    typo_count = len(spelling_corrections)
    score = 100
    if typo_count:
        score = min(score, 75)
    if not speech_level_correct:
        score = min(score, 60)
    if speech_level_uncertain:
        # Don't claim "완벽" when rules couldn't verify the speech level.
        score = min(score, 85)

    verdict = infer_verdict(has_errors, typo_count, speech_level_correct)
    return RealTimeCorrection(
        original_message=user_message,
        corrected_message=corrected_message,
        has_errors=has_errors,
        corrections=corrections,
        natural_alternatives=[],
        expected_speech_level=expected_label,
        expected_speech_level_code=expected_norm,
        detected_speech_level=LEVEL_KO_LABELS.get(detected_norm, detected_norm or expected_norm),
        detected_speech_level_code=detected_norm or expected_norm,
        speech_level_correct=speech_level_correct,
        accuracy_score=score,
        verdict=verdict,
        summary=build_human_feedback_summary(
            has_errors=has_errors,
            corrections=corrections,
            verdict=verdict,
            speech_level_correct=speech_level_correct,
            expected_speech_level=expected_speech_level,
            message_intent="small_talk",
        ),
        encouragement=build_human_encouragement(has_errors, corrections, "small_talk"),
    )


def get_short_response_alternatives(
    text: str,
    expected_norm: str,
) -> List[NaturalAlternative]:
    text     = text.strip()
    alts_map = _SHORT_ALTERNATIVES.get(text, {})
    alts     = alts_map.get(expected_norm, [])
    if not alts:
        for level in ["polite", "informal", "formal"]:
            alts = alts_map.get(level, [])
            if alts: break
    return [
        NaturalAlternative(expression=a["expression"], explanation=a["explanation"])
        for a in alts
    ]


# ============================================================================
# Chat Service
# ============================================================================

class ChatService:

    def __init__(self):
        self.user_streaks: Dict[str, int] = {}
        self.user_moods:   Dict[str, int] = {}
        self.session_turns: Dict[str, List[ChatMessage]] = {}
        self.native_speech_analyzer = get_speech_analyzer()

    def _extract_user_messages(self, conversation_history: List[ChatMessage]) -> List[str]:
        return [
            (message.content or "").strip()
            for message in conversation_history
            if message.role == "user" and (message.content or "").strip()
        ]

    def _extract_korean_tokens(self, texts: List[str]) -> List[str]:
        tokens: List[str] = []
        for text in texts:
            tokens.extend(re.findall(r"[가-힣]{2,}", text))
        return tokens

    async def coach_user_message(
        self,
        *,
        user_message: str,
        expected_speech_level: str = "polite",
        avatar_role: Optional[str] = None,
        avatar_name: Optional[str] = None,
        situation: Optional[str] = None,
        conversation_history: Optional[List[ChatMessage]] = None,
        use_llm: bool = True,
        clova_temperature: float = 0.2,
        clova_max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """Coaching pipeline for a single user message — the blessed path.

        Composes the three new modules:
        1. `analyze_user_korean_message` for deterministic rule-based analysis.
        2. `build_native_korean_coaching_prompt` to build a strict-JSON LLM prompt
            seeded with that rule-based evidence.
        3. `clova_service.analyze_json` (which delegates to
            `sanitize_json_like_model_output`) to parse the model's response.

        Returns a unified dict with keys:
        - `rule_based`:  the deterministic analysis (same shape as
          `analyze_user_korean_message` returns)
        - `llm`:         the parsed LLM JSON (or {} if disabled / unavailable)
        - `corrections`: the merged correction list (LLM-preferred, rule-based fallback)
        - `corrected_message`: best-effort whole-message rewrite
        - `has_errors`:  True if any path found at least one issue
        """
        history_dicts: Optional[List[Dict[str, str]]] = None
        if conversation_history:
            history_dicts = [
                {"role": m.role, "content": m.content}
                for m in conversation_history
                if m.content
            ]

        rule_based = analyze_user_korean_message(
            message=user_message,
            expected_speech_level=expected_speech_level,
            avatar_role=avatar_role,
            situation=situation,
            conversation_history=history_dicts,
        )

        llm_payload: Dict[str, Any] = {}
        if use_llm and (rule_based.get("analysis") or {}).get("text"):
            prompt = build_native_korean_coaching_prompt(
                user_message=user_message,
                expected_speech_level=expected_speech_level,
                avatar_role=avatar_role,
                avatar_name=avatar_name,
                situation=situation,
                conversation_history=history_dicts,
                detected_speech_level=(rule_based.get("analysis") or {}).get("speech_level"),
                rule_based_evidence={
                    "spelling": rule_based.get("spelling") or [],
                    "inferred_intent": rule_based.get("inferred_intent"),
                    "is_appropriate": (rule_based.get("analysis") or {}).get("is_appropriate"),
                    "word_errors": (rule_based.get("analysis") or {}).get("word_errors") or [],
                    "missing_honorifics": (rule_based.get("analysis") or {}).get("missing_honorifics") or [],
                },
            )
            try:
                llm_payload = await clova_service.analyze_json(
                    prompt,
                    temperature=clova_temperature,
                    max_tokens=clova_max_tokens,
                )
            except Exception as e:
                print(f"[coach_user_message] LLM call failed: {e}")
                llm_payload = {}

        # Merge corrections: LLM output preferred, rule-based fills the gaps.
        merged_corrections: List[Dict[str, Any]] = []
        seen_pairs = set()

        for c in (llm_payload.get("corrections") or []):
            original = (c.get("original") or "").strip()
            corrected = (c.get("corrected") or "").strip()
            if not original or not corrected:
                continue
            key = (original, corrected)
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            merged_corrections.append({
                "original": original,
                "corrected": corrected,
                "type": c.get("type") or "expression",
                "severity": c.get("severity") or "warning",
                "explanation": (c.get("explanation") or "").strip(),
                "tip": (c.get("tip") or None),
            })

        analysis = rule_based.get("analysis") or {}
        for source_key in ("word_errors", "missing_honorifics", "directness_errors"):
            for item in (analysis.get(source_key) or []):
                original = (item.get("original") or "").strip()
                corrected = (item.get("corrected") or item.get("expected") or "").strip()
                if not original or not corrected:
                    continue
                key = (original, corrected)
                if key in seen_pairs:
                    continue
                seen_pairs.add(key)
                merged_corrections.append({
                    "original": original,
                    "corrected": corrected,
                    "type": item.get("type") or source_key.rstrip("s"),
                    "severity": item.get("severity") or "warning",
                    "explanation": (item.get("explanation") or "").strip(),
                    "tip": item.get("tip"),
                })

        for hit in (rule_based.get("spelling") or []):
            key = (hit["original"], hit["expected"])
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            merged_corrections.append({
                "original": hit["original"],
                "corrected": hit["expected"],
                "type": "spelling",
                "severity": hit.get("severity") or "warning",
                "explanation": hit.get("explanation") or "",
                "tip": None,
            })

        corrected_message = (
            (llm_payload.get("corrected_message") or "").strip()
            or (analysis.get("suggested_correction") or "").strip()
            or user_message
        )
        has_errors = bool(
            llm_payload.get("has_errors")
            or merged_corrections
            or analysis.get("is_appropriate") is False
        )

        return {
            "rule_based": rule_based,
            "llm": llm_payload,
            "corrections": merged_corrections,
            "corrected_message": corrected_message,
            "has_errors": has_errors,
        }

    def _analyze_with_konlpy(self, text: str) -> Dict[str, Any]:
        # Note: the legacy `speech` field (formerly populated by the deprecated
        # sophisticated_speech_analyzer) is intentionally always None now.
        # Downstream scoring code already guards on `if speech_result:` so
        # those branches simply no-op, falling back to pure rule-based scoring.
        result: Dict[str, Any] = {
            "available": False,
            "source": None,
            "speech": None,
            "morphemes": None,
        }

        try:
            morph_result = morpheme_analyzer.analyze(text)
            if getattr(morph_result, "morphemes", None):
                result["morphemes"] = morph_result
                result["available"] = True
                result["source"] = getattr(morpheme_analyzer, "engine", "KoNLPy")
        except Exception:
            result["morphemes"] = None

        return result

    def _apply_confidence_weighting(
        self,
        raw_score: int,
        message_count: int,
        baseline: int = 70,
    ) -> Dict[str, Any]:
        """Blend raw score toward a baseline when sample size is small.

        - <  3 messages: 50/50 blend with baseline (low confidence)
        - 3-5 messages: graded blend (medium confidence)
        - >= 6 messages: raw score (full confidence)
        """
        if message_count <= 0:
            return {"adjusted": raw_score, "confidence": "none", "raw_score": raw_score}

        if message_count < 3:
            confidence = "low"
            weight = 0.5
        elif message_count < 6:
            confidence = "medium"
            weight = 0.5 + (message_count - 3) * 0.15  # 0.5 → 0.8
        else:
            confidence = "high"
            weight = 1.0

        adjusted = round(raw_score * weight + baseline * (1 - weight))
        return {
            "adjusted": max(0, min(100, adjusted)),
            "confidence": confidence,
            "raw_score": raw_score,
            "weight": round(weight, 2),
        }

    def _calculate_speech_accuracy_score(
        self,
        user_messages: List[str],
        expected_level: SpeechLevel,
        avatar_role: str,
    ) -> Dict[str, Any]:
        if not user_messages:
            return {
                "score": 0,
                "source": "rule_based",
                "used_fallback": False,
                "components": {
                    "messages_evaluated": 0,
                    "matched_messages": 0,
                    "speech_level_penalty": 0,
                    "honorific_penalty": 0,
                    "spelling_penalty": 0,
                    "mixed_style_penalty": 0,
                },
                "note": "분석할 사용자 메시지가 없어 점수를 계산하지 못했습니다.",
            }

        expected_norm = expected_level.value
        total_penalty = 0
        matched_messages = 0
        speech_level_penalty = 0
        honorific_penalty = 0
        spelling_penalty = 0
        mixed_style_penalty = 0
        konlpy_samples_used = 0
        konlpy_sources: List[str] = []

        for text in user_messages:
            fixed = apply_spelling_fixes(text)
            typo_count = len(get_typo_corrections(text))
            detected_norm = verify_with_rules(fixed, "")
            native = self.native_speech_analyzer.check_appropriateness(fixed, expected_norm, avatar_role)
            konlpy_meta = self._analyze_with_konlpy(fixed)
            speech_result = konlpy_meta["speech"]

            message_penalty = 0
            if detected_norm and detected_norm != expected_norm:
                speech_level_penalty += 24
                message_penalty += 24
            else:
                matched_messages += 1

            if native.is_appropriate is False:
                speech_level_penalty += 12
                message_penalty += 12

            if native.missing_honorifics:
                penalty = min(18, len(native.missing_honorifics) * 6)
                honorific_penalty += penalty
                message_penalty += penalty

            if native.is_mixed:
                mixed_style_penalty += 8
                message_penalty += 8

            if speech_result:
                konlpy_samples_used += 1
                if konlpy_meta["source"]:
                    konlpy_sources.append(konlpy_meta["source"])
                primary_name = getattr(getattr(speech_result, "primary_level", None), "name", "").lower()
                if primary_name == "hapsyo":
                    konlpy_level = "formal"
                elif primary_name == "haeyo":
                    konlpy_level = "polite"
                elif primary_name == "hae":
                    konlpy_level = "informal"
                else:
                    konlpy_level = ""

                if konlpy_level and konlpy_level != expected_norm:
                    speech_level_penalty += 10
                    message_penalty += 10
                if not getattr(speech_result, "is_consistent", True):
                    mixed_style_penalty += 6
                    message_penalty += 6
                honorific_density = float(getattr(speech_result, "honorific_density", 0.0) or 0.0)
                if expected_norm in {"formal", "polite"} and honorific_density < 0.02:
                    honorific_penalty += 4
                    message_penalty += 4

            if typo_count:
                penalty = min(12, typo_count * 4)
                spelling_penalty += penalty
                message_penalty += penalty

            total_penalty += min(55, message_penalty)

        average_penalty = total_penalty / max(1, len(user_messages))
        raw_score = max(0, min(100, round(100 - average_penalty)))
        weighted = self._apply_confidence_weighting(raw_score, len(user_messages))
        score = weighted["adjusted"]

        return {
            "score": score,
            "source": "rule_based+konlpy" if konlpy_samples_used > 0 else "rule_based",
            "used_fallback": False,
            "components": {
                "messages_evaluated": len(user_messages),
                "matched_messages": matched_messages,
                "speech_level_penalty": speech_level_penalty,
                "honorific_penalty": honorific_penalty,
                "spelling_penalty": spelling_penalty,
                "mixed_style_penalty": mixed_style_penalty,
                "konlpy_samples_used": konlpy_samples_used,
                "konlpy_sources": sorted(set(konlpy_sources)),
                "raw_score": weighted["raw_score"],
                "confidence": weighted["confidence"],
            },
            "note": (
                "KoNLPy 형태소 분석을 보조로 사용해 말투 어미, 높임 표현, 오타, 혼용 여부를 계산했습니다."
                if konlpy_samples_used > 0
                else "말투 어미, 높임 표현, 오타, 혼용 여부를 규칙 기반으로 계산했습니다."
            ),
        }

    def _calculate_vocabulary_score(self, user_messages: List[str]) -> Dict[str, Any]:
        tokens: List[str] = []
        konlpy_samples_used = 0
        konlpy_sources: List[str] = []
        for text in user_messages:
            konlpy_meta = self._analyze_with_konlpy(text)
            morph_result = konlpy_meta["morphemes"]
            if morph_result and getattr(morph_result, "nouns", None):
                tokens.extend([token for token in morph_result.nouns if len(token) >= 2])
                tokens.extend([token for token in getattr(morph_result, "verbs", []) if len(token) >= 2])
                konlpy_samples_used += 1
                if konlpy_meta["source"]:
                    konlpy_sources.append(konlpy_meta["source"])
            else:
                tokens.extend(re.findall(r"[가-힣]{2,}", text))

        if not tokens:
            return {
                "score": 0,
                "source": "rule_based",
                "used_fallback": False,
                "components": {
                    "token_count": 0,
                    "unique_count": 0,
                    "diversity_score": 0,
                    "difficulty_score": 0,
                    "advanced_token_count": 0,
                },
                "note": "어휘를 계산할 사용자 표현이 부족했습니다.",
            }

        unique_tokens = set(tokens)
        token_count = len(tokens)
        unique_count = len(unique_tokens)
        diversity_ratio = unique_count / max(1, token_count)
        diversity_score = min(100, round(35 + diversity_ratio * 65))

        # Data-driven difficulty: longer Korean tokens are typically rarer/more advanced.
        # 4+ syllables = clearly advanced; 3 syllables = mildly advanced.
        long_tokens = sum(1 for t in tokens if len(t) >= 4)
        mid_tokens = sum(1 for t in tokens if len(t) == 3)
        advanced_token_count = long_tokens
        difficulty_ratio = (long_tokens * 1.0 + mid_tokens * 0.5) / max(1, token_count)
        difficulty_score = min(100, round(30 + difficulty_ratio * 90))

        raw_score = max(0, min(100, round(diversity_score * 0.6 + difficulty_score * 0.4)))
        weighted = self._apply_confidence_weighting(raw_score, len(user_messages))
        score = weighted["adjusted"]

        return {
            "score": score,
            "source": "rule_based+konlpy" if konlpy_samples_used > 0 else "rule_based",
            "used_fallback": False,
            "components": {
                "token_count": token_count,
                "unique_count": unique_count,
                "diversity_score": diversity_score,
                "difficulty_score": difficulty_score,
                "advanced_token_count": advanced_token_count,
                "long_tokens": long_tokens,
                "mid_tokens": mid_tokens,
                "top_tokens": [token for token, _ in Counter(tokens).most_common(5)],
                "konlpy_samples_used": konlpy_samples_used,
                "konlpy_sources": sorted(set(konlpy_sources)),
                "raw_score": weighted["raw_score"],
                "confidence": weighted["confidence"],
            },
            "note": (
                "KoNLPy 형태소 분석으로 명사/동사를 뽑아 단어 다양성과 단어 길이 기반 난도를 계산했습니다."
                if konlpy_samples_used > 0
                else "단어 다양성과 단어 길이(3음절 이상) 비율을 함께 반영했습니다."
            ),
        }

    def _calculate_rule_naturalness_score(
        self,
        user_messages: List[str],
        expected_level: SpeechLevel,
        avatar_role: str,
    ) -> Dict[str, Any]:
        if not user_messages:
            return {
                "score": 0,
                "source": "hybrid",
                "used_fallback": False,
                "components": {
                    "messages_evaluated": 0,
                    "error_penalty": 0,
                    "unnatural_expression_penalty": 0,
                    "mixed_style_penalty": 0,
                    "llm_score": None,
                },
                "note": "분석할 사용자 메시지가 없습니다.",
            }

        expected_norm = expected_level.value
        total_penalty = 0
        error_penalty = 0
        unnatural_expression_penalty = 0
        mixed_style_penalty = 0
        konlpy_samples_used = 0
        konlpy_sources: List[str] = []

        for text in user_messages:
            fixed = apply_spelling_fixes(text)
            typo_count = len(get_typo_corrections(text))
            native = self.native_speech_analyzer.check_appropriateness(fixed, expected_norm, avatar_role)
            konlpy_meta = self._analyze_with_konlpy(fixed)
            speech_result = konlpy_meta["speech"]
            message_penalty = 0

            if typo_count:
                penalty = min(18, typo_count * 6)
                error_penalty += penalty
                message_penalty += penalty

            if native.word_errors:
                penalty = min(24, len(native.word_errors) * 8)
                unnatural_expression_penalty += penalty
                message_penalty += penalty

            if native.missing_honorifics:
                penalty = min(16, len(native.missing_honorifics) * 5)
                error_penalty += penalty
                message_penalty += penalty

            if native.is_mixed:
                mixed_style_penalty += 8
                message_penalty += 8

            if speech_result:
                konlpy_samples_used += 1
                if konlpy_meta["source"]:
                    konlpy_sources.append(konlpy_meta["source"])
                if not getattr(speech_result, "is_consistent", True):
                    mixed_style_penalty += 6
                    message_penalty += 6
                pragmatics = getattr(speech_result, "pragmatic_markers", []) or []
                if len(pragmatics) == 0 and len(fixed) >= 8:
                    unnatural_expression_penalty += 3
                    message_penalty += 3

            total_penalty += min(60, message_penalty)

        average_penalty = total_penalty / max(1, len(user_messages))
        raw_score = max(0, min(100, round(100 - average_penalty)))
        weighted = self._apply_confidence_weighting(raw_score, len(user_messages))
        score = weighted["adjusted"]

        return {
            "score": score,
            "source": "hybrid+konlpy" if konlpy_samples_used > 0 else "hybrid",
            "used_fallback": False,
            "components": {
                "messages_evaluated": len(user_messages),
                "error_penalty": error_penalty,
                "unnatural_expression_penalty": unnatural_expression_penalty,
                "mixed_style_penalty": mixed_style_penalty,
                "llm_score": None,
                "konlpy_samples_used": konlpy_samples_used,
                "konlpy_sources": sorted(set(konlpy_sources)),
                "raw_score": weighted["raw_score"],
                "confidence": weighted["confidence"],
            },
            "note": (
                "KoNLPy 기반 일관성/형태소 신호와 오류 수를 함께 반영해 자연스러움을 계산했습니다."
                if konlpy_samples_used > 0
                else "오류 수, 부자연한 표현, 말투 혼용을 기준으로 자연스러움을 계산했습니다."
            ),
        }
    
    async def generate_response(
        self,
        avatar:               AvatarBase,
        user_message:         str,
        conversation_history: List[ChatMessage],
        user_profile:         Optional[UserProfile] = None,
        situation:            Optional[str]         = None,
        user_id:              str                   = "default",
        session_id:           Optional[str]         = None,
        expected_speech_level: Optional[str]         = None,
        correction_context:   Optional[Dict[str, Any]] = None,
        response_instruction: Optional[List[str]]    = None,
        use_memory:           bool                  = True,
        session_context:       Optional[Dict[str, Any]] = None,
    ) -> ChatResponse:

        speech_levels  = get_speech_levels_for_role(avatar.role)
        expected_level = coerce_speech_level(expected_speech_level, speech_levels["from_user"])
        user_level     = (
            user_profile.korean_level.value
            if user_profile and hasattr(user_profile.korean_level, "value")
            else "intermediate"
        )
        session_key = session_id or f"{user_id}_{getattr(avatar, 'name_ko', 'avatar')}"
        effective_history = self._get_effective_history(session_key, conversation_history)

        # ── 핵심: conversation_history 전달 ───────────────────────────────
        correction = await self._analyze_realtime(
            user_message=user_message,
            expected_speech_level=expected_level,
            avatar_role=get_role_label(avatar.role, None),
            user_level=user_level,
            situation=situation,
            conversation_history=effective_history,   # ← 추가
        )
        correction = self._merge_frontend_correction_context(
            correction=correction,
            user_message=user_message,
            expected_level=expected_level,
            correction_context=correction_context,
        )

        mood_key     = f"{user_id}_{avatar.name_ko}"
        current_mood = self.user_moods.get(mood_key, 80)

        system_prompt = build_avatar_system_prompt(
            avatar=avatar,
            user_profile=user_profile,
            situation=situation,
            current_mood=current_mood,
            is_level_correct=correction.speech_level_correct,
        )

        if use_memory:
            try:
                from app.services.memory_service import memory_service
                avatar_id      = getattr(avatar, "id", avatar.name_ko)
                memory_section = memory_service.build_memory_prompt_section(user_id, avatar_id)
                if memory_section:
                    system_prompt += "\n" + memory_section
            except Exception as e:
                print(f"Memory integration error: {e}")

        session_summary = (
            (session_context or {}).get("session_summary")
            if session_context
            else None
        )
                
        system_prompt += self._build_turn_context_section(
            user_message=user_message,
            correction=correction,
            correction_context=correction_context,
            response_instruction=response_instruction or [],
            session_summary=session_summary,
        )

        history = [
            Message(role=msg.role, content=msg.content)
            for msg in effective_history[-10:]
        ]
        reply_user_message = self._make_reply_user_message(user_message, correction)

        response = await clova_service.generate_with_system_prompt(
            system_prompt=system_prompt,
            user_message=reply_user_message,
            conversation_history=history,
            temperature=0.65,
        )
        final_message = self._finalize_ai_reply(response.content, user_message, correction)

        streak                  = self._update_streak(user_id, correction.has_errors)
        correction.streak_bonus = streak >= 3

        mood_change = self._calculate_mood_change(correction)
        new_mood    = self._update_mood(mood_key, mood_change)
        mood_emoji  = self._get_mood_emoji(new_mood)

        suggestions = []
        hint        = None
        if len(user_message) < 15 or correction.has_errors:
            hint_result = await self._get_contextual_hint(
                avatar=avatar,
                conversation_history=effective_history,
                user_level=user_level,
            )
            suggestions = [
                cleaned for cleaned in (
                    postprocess_model_output(text)
                    for text in hint_result.get("example_responses", [])
                )
                if cleaned
            ]
            hint = postprocess_model_output(hint_result.get("hint"))
        if correction.has_errors:
            try:
                self._save_mistakes(session_key, correction)
            except Exception as e:
                print(f"[mistakes] failed to save: {e}")

        # Persist this turn server-side so the next call sees a coherent rolling
        # history + summary even if the client trims its conversation_history.
        try:
            self._remember_session_turn(
                session_key=session_key,
                user_message=user_message,
                assistant_message=final_message,
                existing_history=effective_history,
            )
        except Exception as e:
            print(f"[session] failed to persist turn: {e}")

        # Surface the freshest summary on the response (clients can ignore it).
        latest_summary = None
        try:
            _, latest_summary = self._load_session(session_key)
        except Exception:
            latest_summary = session_summary

        return ChatResponse(
            message=final_message,
            correction=correction,
            mood_change=mood_change,
            current_mood=new_mood,
            mood_emoji=mood_emoji,
            suggestions=suggestions,
            hint=hint,
            correct_streak=streak,
            session_summary=latest_summary or session_summary,
        )

    def _get_effective_history(
        self,
        session_key: str,
        conversation_history: List[ChatMessage],
    ) -> List[ChatMessage]:
        """Merge frontend-sent history with server-side session memory."""
        incoming = conversation_history or []
        stored, _ = self._load_session(session_key)
        if not stored:
            return incoming
        if not incoming:
            return stored

        seen = {(m.role, m.content) for m in incoming}
        merged = incoming[:]
        for msg in stored:
            key = (msg.role, msg.content)
            if key not in seen:
                merged.append(msg)
                seen.add(key)
        return merged[-20:]

    def _remember_session_turn(
        self,
        session_key: str,
        user_message: str,
        assistant_message: str,
        existing_history: List[ChatMessage],
    ) -> None:
        history = (existing_history or [])[-18:]
        history = [
            *history,
            ChatMessage(role="user", content=user_message),
            ChatMessage(role="assistant", content=assistant_message),
        ]
        final_summary = self._update_session_summary(
            session_key, user_message, assistant_message, existing_history
        )
        self._save_session(session_key, history[-20:], final_summary)
    def _update_session_summary(
        self,
        session_key: str,
        user_message: str,
        assistant_message: str,
        existing_history: List[ChatMessage],
        session_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        stored_history, previous_summary = self._load_session(session_key)
        base_history = existing_history or stored_history or []
        history = base_history[-18:]
        history = [
            *history,
            ChatMessage(role="user", content=user_message),
            ChatMessage(role="assistant", content=assistant_message),
        ]
        if session_context and not previous_summary:
            previous_summary = session_context.get("session_summary") or ""
        recent_topics: List[str] = []
        recent_messages = history[-6:]
        for msg in recent_messages:
            content = msg.content.strip()
            if content:
                recent_topics.append(f"{msg.role}: {content}")

        if not recent_topics and not previous_summary:
            return None

        joined_recent = " | ".join(recent_topics)
        if previous_summary and joined_recent:
            return f"{previous_summary} || Recent: {joined_recent}"[:1000]
        if previous_summary:
            return previous_summary[:1000]
        return f"Recent: {joined_recent}"[:1000]
    def _build_turn_context_section(
        self,
        user_message: str,
        correction: RealTimeCorrection,
        correction_context: Optional[Dict[str, Any]],
        response_instruction: List[str],
        session_summary: Optional[str] = None,
    ) -> str:
        corrected = correction.corrected_message or self._best_corrected_expression(correction) or user_message
        summary_line = f"\n[SESSION SUMMARY]\n{session_summary}\n" if session_summary else ""
        extra_guidance = "\n".join(
            f"- {line}" for line in response_instruction if str(line).strip()
        )

        summary_section = f"\n[SESSION SUMMARY]\n{session_summary}\n" if session_summary else ""
        return f"""
    
        {summary_section}

## 현재 턴 응답 생성 규칙 (최우선)
- 사용자 원문: {user_message}
- 교정 후 의도: {corrected}
- 기대 말투: {correction.expected_speech_level}
- 감지 말투: {correction.detected_speech_level or "불명확"}
- 오류 여부: {"있음" if correction.has_errors else "없음"}
- 요약: {correction.summary or "특이사항 없음"}

## 채팅 말풍선 규칙
- 채팅 답변에는 "polite detected", "감지", "점수", "정확도", "분석 결과" 같은 분석 라벨을 절대 쓰지 마세요.
- 교정 내용은 별도 UI가 보여줍니다. 당신은 corrected intent를 조용히 이해하고, 캐릭터답게 대화만 이어가세요.
- 오류가 있어도 "X가 맞는 표현이야", "이렇게 말하세요"처럼 직접 교정하지 마세요.
- 문법, 말투, 표현, 점수, 학습 팁, 모범 답안, 예시 문장을 말풍선에서 제공하지 마세요.
- 당신은 튜터, 코치, 선생님, 평가자가 아닙니다. 오직 현재 아바타 캐릭터입니다.
- 오류가 없으면 사용자의 내용에 자연스럽게 반응하세요.
- 답변은 1~3문장으로 짧고 실제 사람이 말하듯 작성하세요.
- 이모지와 장식 기호는 사용하지 마세요.

{extra_guidance}
"""

    @contextmanager
    def _get_db_connection(self):
        """Database connection context manager"""
        conn = None
        try:
            conn = mysql.connector.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database=settings.DB_NAME,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci',
                use_unicode=True,
            )
            cursor = conn.cursor()
            cursor.execute("SET NAMES utf8mb4")
            cursor.close()
            yield conn
        finally:
            if conn and conn.is_connected():
                conn.close()

    def _load_session(self, session_key):
        """Load session turns + summary from DB"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Get summary
            cursor.execute("SELECT summary FROM session_summaries WHERE session_id = %s", (session_key,))
            summary_row = cursor.fetchone()
            previous_summary = summary_row['summary'] if summary_row else ""
            
            # Get recent 20 turns
            cursor.execute("""
                SELECT role, message FROM chat_turns 
                WHERE session_id = %s 
                ORDER BY turn_number DESC 
                LIMIT 20
            """, (session_key,))
            turns = cursor.fetchall()
            
            # Convert to ChatMessage format
            history = []
            for turn in reversed(turns):  # Oldest first
                history.append(ChatMessage(role=turn['role'], content=turn['message']))
            
            cursor.close()
            return history, previous_summary

    def _save_session(self, session_key, history, summary):
        """Save session turns + summary to DB"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Upsert session summary
            cursor.execute("""
                INSERT INTO session_summaries (session_id, summary, turn_count) 
                VALUES (%s, %s, %s) 
                ON DUPLICATE KEY UPDATE 
                summary = VALUES(summary), 
                turn_count = VALUES(turn_count),
                updated_at = CURRENT_TIMESTAMP
            """, (session_key, summary, len(history)))
            
            # Clear old turns, insert new ones
            cursor.execute("DELETE FROM chat_turns WHERE session_id = %s", (session_key,))
            for i, msg in enumerate(history[-20:], 1):
                cursor.execute("""
                    INSERT INTO chat_turns (session_id, turn_number, role, message)
                    VALUES (%s, %s, %s, %s)
                """, (session_key, i, msg.role, msg.content))
            
            conn.commit()
            cursor.close()

    def _save_mistakes(self, session_key: str, correction: "RealTimeCorrection") -> None:
        """Persist per-turn inline corrections to session_mistakes table."""
        for c in correction.corrections:
            print(f"[mistakes-debug] type={type(c.original).__name__} original={c.original!r} corrected={c.corrected!r}")
        real = [
            c for c in correction.corrections
            if c.original != c.corrected
        ]
        if not real:
            return
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COALESCE(MAX(turn_number), 0) FROM session_mistakes WHERE session_id = %s",
                (session_key,),
            )
            row = cursor.fetchone()
            next_turn = (row[0] if row else 0) + 1
            for c in real:
                cursor.execute(
                    """
                    INSERT INTO session_mistakes
                        (session_id, turn_number, original, corrected, error_type, severity, explanation)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        session_key,
                        next_turn,
                        c.original,
                        c.corrected,
                        c.type.value if hasattr(c.type, "value") else str(c.type),
                        c.severity.value if hasattr(c.severity, "value") else str(c.severity),
                        c.explanation,
                    ),
                )
            conn.commit()
            cursor.close()

    def _load_session_mistakes(self, session_key: str) -> List[Dict[str, str]]:
        """Load all stored mistakes for a session."""
        with self._get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT original, corrected, error_type, severity, explanation
                FROM session_mistakes
                WHERE session_id = %s
                ORDER BY turn_number, id
                """,
                (session_key,),
            )
            rows = cursor.fetchall()
            cursor.close()
        return rows or []

    def _make_reply_user_message(
        self,
        user_message: str,
        correction: RealTimeCorrection,
    ) -> str:
        if not correction.has_errors:
            return user_message
        corrected = correction.corrected_message or self._best_corrected_expression(correction) or user_message
        return (
            f"사용자 원문: {user_message}\n"
            f"교정 후 의도: {corrected}\n"
            "위 의도를 기준으로 자연스럽게 답하세요. 분석 라벨이나 점수는 말하지 마세요."
        )

    def _best_corrected_expression(self, correction: RealTimeCorrection) -> Optional[str]:
        if correction.corrected_message:
            return correction.corrected_message
        if correction.corrections:
            return correction.corrections[0].corrected
        if correction.natural_alternatives:
            return correction.natural_alternatives[0].expression
        return None

    def _finalize_ai_reply(
        self,
        raw_message: str,
        user_message: str,
        correction: RealTimeCorrection,
    ) -> str:
        cleaned = postprocess_model_output(raw_message)
        is_bad_reply = (
            not cleaned
            or bool(_DIAGNOSTIC_REPLY_PATTERN.search(cleaned))
            or (correction.has_errors and bool(_GENERIC_REPLY_PATTERN.search(cleaned)))
        )

        if correction.has_errors and is_bad_reply:
            return "무슨 말인지 알겠어. 그 얘기 조금만 더 해 봐."

        if is_bad_reply:
            return "좋아, 계속 이야기해 보자."
        return cleaned

    def _merge_frontend_correction_context(
        self,
        correction: RealTimeCorrection,
        user_message: str,
        expected_level: SpeechLevel,
        correction_context: Optional[Dict[str, Any]],
    ) -> RealTimeCorrection:
        """Use frontend hints only as a fallback when backend analysis misses a visible issue."""
        latest_feedback = (correction_context or {}).get("latest_feedback") or {}
        if correction.has_errors or not latest_feedback.get("has_errors"):
            return correction

        frontend_corrections = []
        for item in latest_feedback.get("corrections", []):
            try:
                original = (item.get("original") or user_message).strip()
                corrected = (item.get("corrected") or "").strip()
                if not corrected:
                    continue
                correction_type = item.get("type", "expression")
                if correction_type == "spelling_speech_level":
                    correction_type = "speech_level"
                frontend_corrections.append(InlineCorrection(
                    original=original,
                    corrected=corrected,
                    type=CorrectionType(correction_type),
                    severity=CorrectionSeverity(item.get("severity", "warning")),
                    explanation=item.get("explanation") or item.get("reason") or "더 자연스러운 표현으로 고쳐야 합니다.",
                    tip=item.get("tip"),
                ))
            except (ValueError, AttributeError):
                continue

        corrected_message = (
            (correction_context or {}).get("corrected_user_message")
            or (frontend_corrections[0].corrected if frontend_corrections else None)
        )
        expected_norm = expected_level.value
        detected_norm = normalize_level_code(latest_feedback.get("detected_speech_level_code"))
        detected_label = (
            latest_feedback.get("detected_speech_level")
            or LEVEL_KO_LABELS.get(detected_norm)
            or correction.detected_speech_level
        )

        correction.has_errors = True
        correction.corrected_message = corrected_message
        correction.corrections = frontend_corrections or correction.corrections
        correction.natural_alternatives = [
            NaturalAlternative(
                expression=corrected_message,
                explanation="현재 대화 상황에 맞게 고친 자연스러운 문장입니다.",
            )
        ] if corrected_message else correction.natural_alternatives
        correction.accuracy_score = min(correction.accuracy_score, latest_feedback.get("accuracy_score") or 75)
        correction.speech_level_correct = False if detected_norm and detected_norm != expected_norm else correction.speech_level_correct
        correction.detected_speech_level = detected_label
        correction.detected_speech_level_code = detected_norm or correction.detected_speech_level_code
        correction.verdict = latest_feedback.get("verdict") or correction.verdict or "needs_revision"
        correction.summary = latest_feedback.get("summary") or correction.summary
        correction.encouragement = correction.encouragement or "조금만 고치면 훨씬 자연스럽게 들려요."
        return correction

    def _apply_native_analyzer_feedback(
        self,
        user_message: str,
        expected_norm: str,
        avatar_role: str,
        corrections: List[InlineCorrection],
        natural_alternatives: List[NaturalAlternative],
        detected_norm: str,
        is_level_correct: bool,
        accuracy_score: int,
        summary: str,
    ) -> Dict[str, Any]:
        """Augment CLOVA output with native analyzer signals."""
        analyzed_text = apply_spelling_fixes(user_message)
        native = self.native_speech_analyzer.check_appropriateness(
            analyzed_text,
            expected_norm,
            avatar_role,
        )

        existing_pairs = {(c.original, c.corrected, c.type) for c in corrections}

        for item in native.word_errors:
            original = (item.get("original") or "").strip()
            corrected = (item.get("expected") or "").strip()
            if not original or not corrected:
                continue
            key = (original, corrected, CorrectionType.VOCABULARY)
            if key in existing_pairs:
                continue
            corrections.append(InlineCorrection(
                original=original,
                corrected=corrected,
                type=CorrectionType.VOCABULARY,
                severity=CorrectionSeverity.ERROR if item.get("severity") == "error" else CorrectionSeverity.WARNING,
                explanation=item.get("explanation") or "이 상황에서는 더 적절한 표현이 있어요.",
            ))
            existing_pairs.add(key)

        for item in native.missing_honorifics:
            original = (item.get("original") or "").strip()
            corrected = (item.get("corrected") or "").strip()
            if not original or not corrected:
                continue
            key = (original, corrected, CorrectionType.HONORIFIC)
            if key in existing_pairs:
                continue
            corrections.append(InlineCorrection(
                original=original,
                corrected=corrected,
                type=CorrectionType.HONORIFIC,
                severity=CorrectionSeverity.ERROR,
                explanation=item.get("explanation") or "높임말 표현으로 바꾸는 것이 자연스럽습니다.",
            ))
            existing_pairs.add(key)

        if native.is_mixed and native.mixed_detail:
            has_mixed_note = any(c.type == CorrectionType.SPEECH_LEVEL and "섞여" in c.explanation for c in corrections)
            if not has_mixed_note:
                corrections.append(InlineCorrection(
                    original=user_message,
                    corrected=user_message,
                    type=CorrectionType.SPEECH_LEVEL,
                    severity=CorrectionSeverity.WARNING,
                    explanation=f"한 문장 안에서 말투가 섞여 있어요. {native.mixed_detail}",
                    tip="한 메시지 안에서는 말투를 하나로 통일해 보세요.",
                ))

        native_level = native.overall_level.value if native.overall_level.value != "unknown" else ""
        if native_level and not detected_norm:
            detected_norm = native_level
        if native_level and detected_norm != native_level and expected_norm != native_level:
            # When regex/LLM disagree but native analyzer finds a clearer wrong level, prefer it.
            detected_norm = native_level

        native_inappropriate = native.is_appropriate is False
        if native_inappropriate:
            is_level_correct = False

        if corrections:
            accuracy_score = min(accuracy_score, native.score)
        elif native_level and native_level == expected_norm and native.score < 100:
            accuracy_score = min(accuracy_score, native.score)

        if not summary:
            summary = native.feedback_ko or ""
        elif native.feedback_ko and native.feedback_ko not in summary:
            summary = f"{summary} {native.feedback_ko}".strip()

        return {
            "corrections": corrections,
            "natural_alternatives": natural_alternatives,
            "detected_norm": detected_norm,
            "is_level_correct": is_level_correct,
            "accuracy_score": accuracy_score,
            "summary": summary,
        }

    async def _analyze_realtime(
        self,
        user_message:          str,
        expected_speech_level: SpeechLevel,
        avatar_role:           str,
        user_level:            str,
        situation:             Optional[str] = None,
        conversation_history:  List[ChatMessage] = [],   # ← 추가
    ) -> RealTimeCorrection:

        msg_stripped  = user_message.strip()
        expected_norm = LEVEL_MAP.get(
            SPEECH_LEVEL_INFO[expected_speech_level]["name_ko"].lower(),
            expected_speech_level.value.lower(),
        )
        situation_signals = infer_situation_signals(situation, avatar_role, expected_norm)
        message_intent = infer_message_intent(user_message, situation_signals)
        contextual_base = build_contextual_base_corrections(
            user_message=user_message,
            expected_speech_level=expected_speech_level,
            situation_signals=situation_signals,
            message_intent=message_intent,
        )
        local_rule_correction = build_rule_based_correction(
            user_message,
            expected_speech_level,
            base_corrections=contextual_base["corrections"],
        )
        if contextual_base.get("corrected_message") and not local_rule_correction.corrected_message:
            local_rule_correction.corrected_message = contextual_base["corrected_message"]
            local_rule_correction.has_errors = True
            local_rule_correction.accuracy_score = min(local_rule_correction.accuracy_score, 60)
            local_rule_correction.verdict = local_rule_correction.verdict or "wrong_speech_level"
            local_rule_correction.summary = local_rule_correction.summary or "인사말을 조금 더 공손하게 하면 자연스러워요."
        native_snapshot = self.native_speech_analyzer.check_appropriateness(
            apply_spelling_fixes(user_message),
            expected_norm,
            avatar_role,
        )
        konlpy_hints = extract_konlpy_prompt_hints(user_message)
        benchmark_case = lookup_benchmark_case(user_message, expected_norm)
        if benchmark_case and should_use_benchmark_case(
            user_message=user_message,
            expected_norm=expected_norm,
            situation_signals=situation_signals,
            message_intent=message_intent,
        ):
            return build_benchmark_correction(user_message, expected_speech_level, benchmark_case)
        edit_strategy = classify_edit_strategy(user_message, local_rule_correction, native_snapshot)

        # ── 단답형 스킵 ──────────────────────────────────────────────────────
        is_short = (
            msg_stripped in _SHORT_RESPONSES
            or msg_stripped.lower() in _SHORT_RESPONSES
        )
        if is_short:
            detected_norm    = verify_with_rules(msg_stripped, "")
            is_level_correct = (detected_norm == expected_norm) or (detected_norm == "")
            alternatives     = get_short_response_alternatives(msg_stripped, expected_norm)
            return RealTimeCorrection(
                original_message=user_message,
                expected_speech_level=SPEECH_LEVEL_INFO[expected_speech_level]["name_ko"],
                expected_speech_level_code=expected_norm,
                detected_speech_level=detected_norm or expected_norm,
                detected_speech_level_code=detected_norm or expected_norm,
                speech_level_correct=is_level_correct,
                accuracy_score=100 if is_level_correct else 60,
                verdict="ok" if is_level_correct else "wrong_speech_level",
                summary=None if is_level_correct else f"{SPEECH_LEVEL_INFO[expected_speech_level]['name_ko']}에 맞게 바꿔 주세요.",
                natural_alternatives=alternatives,
                encouragement="좋아요. 계속해서 대화해 보세요.",
            )

        # ── 대화 기록 포함하여 프롬프트 생성 ─────────────────────────────────
        prompt = build_realtime_correction_prompt(
            user_message=user_message,
            expected_speech_level=expected_speech_level,
            avatar_role=avatar_role,
            user_level=user_level,
            conversation_history=conversation_history,   # ← 추가
            edit_strategy_hint=edit_strategy,
            situation_signals=situation_signals,
            message_intent=message_intent,
            konlpy_hints=konlpy_hints,
        )

        result = await clova_service.analyze_json(prompt, temperature=0.2, max_tokens=1024)

        if not result:
            native_augmented = self._apply_native_analyzer_feedback(
                user_message=user_message,
                expected_norm=expected_norm,
                avatar_role=avatar_role,
                corrections=local_rule_correction.corrections[:],
                natural_alternatives=local_rule_correction.natural_alternatives[:],
                detected_norm=local_rule_correction.detected_speech_level_code or "",
                is_level_correct=local_rule_correction.speech_level_correct,
                accuracy_score=local_rule_correction.accuracy_score,
                summary=local_rule_correction.summary or "",
            )
            local_rule_correction.corrections = native_augmented["corrections"]
            local_rule_correction.natural_alternatives = native_augmented["natural_alternatives"]
            local_rule_correction.detected_speech_level_code = native_augmented["detected_norm"] or local_rule_correction.detected_speech_level_code
            local_rule_correction.detected_speech_level = LEVEL_KO_LABELS.get(
                local_rule_correction.detected_speech_level_code or "",
                local_rule_correction.detected_speech_level or local_rule_correction.expected_speech_level,
            )
            local_rule_correction.speech_level_correct = native_augmented["is_level_correct"]
            local_rule_correction.accuracy_score = max(0, min(100, int(native_augmented["accuracy_score"])))
            local_rule_correction.summary = native_augmented["summary"] or local_rule_correction.summary
            local_rule_correction.has_errors = (
                any(c.severity in (CorrectionSeverity.ERROR, CorrectionSeverity.WARNING) and c.original != c.corrected
                    for c in local_rule_correction.corrections)
                or not local_rule_correction.speech_level_correct
            )
            local_rule_correction.verdict = infer_verdict(
                local_rule_correction.has_errors,
                sum(1 for c in local_rule_correction.corrections if c.type == CorrectionType.SPELLING),
                local_rule_correction.speech_level_correct,
            )
            return local_rule_correction

        # ── corrections 파싱 + 필터링 ─────────────────────────────────────────
        corrections = []
        for c in result.get("corrections", []) or []:
            try:
                original  = (c.get("original",  "") or "").strip()
                corrected = (c.get("corrected", "") or "").strip()
                if not original or not corrected:  continue
                if original == corrected:          continue
                if original not in user_message:
                    print(f"[ChatService] ⚠️ Hallucination skip: '{original}' not in '{user_message}'")
                    continue
                corrections.append(InlineCorrection(
                    original=original,
                    corrected=corrected,
                    type=CorrectionType(c.get("type", "grammar")),
                    severity=CorrectionSeverity(c.get("severity", "warning")),
                    explanation=c.get("explanation", ""),
                    tip=c.get("tip"),
                ))
            except (ValueError, KeyError):
                continue

        existing_pairs = {(c.original, c.corrected, c.type) for c in corrections}
        for c in local_rule_correction.corrections:
            key = (c.original, c.corrected, c.type)
            if key not in existing_pairs:
                corrections.append(c)
                existing_pairs.add(key)

        # ── natural_alternatives 파싱 ─────────────────────────────────────────
        natural_alternatives = []
        for a in result.get("natural_alternatives", []) or []:
            try:
                expression  = (a.get("expression",  "") or "").strip()
                explanation = (a.get("explanation", "") or "").strip()
                if not _is_valid_natural_alternative(
                    expression,
                    explanation,
                    user_message,
                    (result.get("corrected_message") or "").strip() or local_rule_correction.corrected_message,
                    expected_norm,
                ):
                    continue
                natural_alternatives.append(NaturalAlternative(
                    expression=expression,
                    explanation=explanation,
                ))
            except Exception:
                continue

        # ── 하이브리드 발화 레벨 감지 ──────────────────────────────────────────
        clova_raw        = (result.get("detected_speech_level") or "").strip().lower()
        clova_norm       = LEVEL_MAP.get(clova_raw, clova_raw)
        detected_norm    = verify_with_rules(apply_spelling_fixes(user_message), clova_norm)
        # If neither the rules nor the LLM produced a level, treat it as
        # uncertain rather than silently affirming "matches expected" — this
        # prevents informal endings the rules don't recognize (e.g. ending in
        # 돼/줘/봐) from quietly scoring 100.
        is_level_uncertain = (detected_norm == "")
        is_level_correct   = (detected_norm == expected_norm)

        # ── has_errors — info 제외 ────────────────────────────────────────────
        real_errors = [
            c for c in corrections
            if c.severity in (CorrectionSeverity.ERROR, CorrectionSeverity.WARNING)
        ]
        has_errors     = (len(real_errors) > 0) or (not is_level_correct and not is_level_uncertain) or local_rule_correction.has_errors
        accuracy_score = int(result.get("accuracy_score", 100) or 100)

        if not has_errors and corrections:
            accuracy_score = max(accuracy_score, 90)
        if local_rule_correction.has_errors:
            accuracy_score = min(accuracy_score, local_rule_correction.accuracy_score)
        # Cap "완벽" claims when we genuinely couldn't verify the speech level —
        # better to land in "잘했어요" territory than to falsely affirm.
        if is_level_uncertain:
            accuracy_score = min(accuracy_score, 85)

        # ── 말투 오류 시 corrected 검증 ──────────────────────────────────────
        best_corrected = None
        if not is_level_correct:
            accuracy_score = min(accuracy_score, 60)
            expected_name  = SPEECH_LEVEL_INFO[expected_speech_level]["name_ko"]
            example        = SPEECH_LEVEL_INFO[expected_speech_level]["examples"][0]

            clova_corrected      = (result.get("corrected_message") or "").strip()
            clova_corrected_norm = verify_with_rules(clova_corrected, "") if clova_corrected else ""
            rule_corrected = simple_convert_to_level(user_message, expected_norm)
            preferred_rule = _prefer_rule_correction(
                user_message=user_message,
                clova_corrected=clova_corrected,
                rule_corrected=rule_corrected,
                expected_norm=expected_norm,
            )

            if preferred_rule:
                best_corrected = preferred_rule
            elif clova_corrected and clova_corrected_norm == expected_norm:
                best_corrected = clova_corrected
            else:
                if rule_corrected and verify_with_rules(rule_corrected, "") == expected_norm:
                    best_corrected = rule_corrected
                else:
                    best_corrected = example

            has_speech_correction = any(c.type == CorrectionType.SPEECH_LEVEL for c in corrections)
            if not has_speech_correction:
                corrections.insert(0, InlineCorrection(
                    original=user_message,
                    corrected=best_corrected,
                    type=CorrectionType.SPEECH_LEVEL,
                    severity=CorrectionSeverity.ERROR,
                    explanation=f"{expected_name}를 사용해야 합니다. 지금 문장은 {LEVEL_KO_LABELS.get(detected_norm, detected_norm)}에 가까워요.",
                    tip=f"예시: {example}",
                ))
            else:
                corrections = [
                    InlineCorrection(
                        original=c.original,
                        corrected=best_corrected if c.type == CorrectionType.SPEECH_LEVEL else c.corrected,
                        type=c.type,
                        severity=c.severity,
                        explanation=c.explanation,
                        tip=c.tip,
                    )
                    for c in corrections
                ]

        corrected_message = (result.get("corrected_message") or "").strip() or local_rule_correction.corrected_message
        contextual_corrected_message = (contextual_base.get("corrected_message") or "").strip()
        if (
            contextual_corrected_message
            and message_intent == "greeting"
            and situation_signals.get("power_direction") == "other_higher"
            and "안녕" in user_message
        ):
            corrected_message = contextual_corrected_message
        if best_corrected:
            corrected_message = best_corrected

        if corrected_message:
            derived_corrections = derive_surface_corrections(user_message, corrected_message)
            for derived in derived_corrections:
                replaced = False
                for index, existing in enumerate(corrections):
                    if existing.original != derived.original:
                        continue
                    existing_strength = len(existing.corrected.replace(" ", ""))
                    derived_strength = len(derived.corrected.replace(" ", ""))
                    if derived_strength > existing_strength or (
                        existing.type == CorrectionType.SPELLING
                        and derived.type in {CorrectionType.HONORIFIC, CorrectionType.VOCABULARY}
                    ):
                        corrections[index] = derived
                        replaced = True
                        break
                    if existing.corrected == derived.corrected and existing.type == derived.type:
                        replaced = True
                        break
                if not replaced:
                    corrections.append(derived)
            corrections = prune_suspicious_corrections(corrections, corrected_message)

        minimal_corrected = build_minimal_edit_correction(user_message, expected_norm, local_rule_correction)
        if edit_strategy == "minimal" and minimal_corrected and not corrected_message:
            corrected_message = minimal_corrected
            natural_alternatives = []
            corrections = [
                InlineCorrection(
                    original=c.original,
                    corrected=(minimal_corrected if c.type == CorrectionType.SPEECH_LEVEL else c.corrected),
                    type=c.type,
                    severity=c.severity,
                    explanation=c.explanation,
                    tip=c.tip,
                )
                for c in corrections
            ]
        if has_errors and not corrected_message:
            corrected_message = compose_corrected_message_from_corrections(user_message, corrections)
        if has_errors and not corrected_message:
            corrected_message = corrections[0].corrected if corrections else None
        if not has_errors:
            corrected_message = None

        if not natural_alternatives and local_rule_correction.natural_alternatives:
            natural_alternatives = [
                alt for alt in local_rule_correction.natural_alternatives
                if _is_valid_natural_alternative(
                    alt.expression,
                    alt.explanation,
                    user_message,
                    corrected_message,
                    expected_norm,
                )
            ]

        summary = result.get("summary") or result.get("overall_feedback") or local_rule_correction.summary
        native_augmented = self._apply_native_analyzer_feedback(
            user_message=user_message,
            expected_norm=expected_norm,
            avatar_role=avatar_role,
            corrections=corrections,
            natural_alternatives=natural_alternatives,
            detected_norm=detected_norm,
            is_level_correct=is_level_correct,
            accuracy_score=accuracy_score,
            summary=summary,
        )
        corrections = native_augmented["corrections"]
        corrections = prune_suspicious_corrections(corrections, corrected_message)
        natural_alternatives = [
            alt for alt in native_augmented["natural_alternatives"]
            if _is_valid_natural_alternative(
                alt.expression,
                alt.explanation,
                user_message,
                corrected_message,
                expected_norm,
            )
        ]
        detected_norm = native_augmented["detected_norm"]
        is_level_correct = native_augmented["is_level_correct"]
        accuracy_score = native_augmented["accuracy_score"]
        summary = native_augmented["summary"]

        real_errors = [
            c for c in corrections
            if c.severity in (CorrectionSeverity.ERROR, CorrectionSeverity.WARNING)
            and c.original != c.corrected
        ]
        has_errors = (len(real_errors) > 0) or not is_level_correct

        typo_count = sum(1 for c in corrections if c.type == CorrectionType.SPELLING)
        if has_errors and not corrected_message:
            corrected_message = compose_corrected_message_from_corrections(user_message, corrections) or corrected_message

        # Patch any spelling corrections into corrected_message even if LLM already set one.
        # LLMs often detect typos as corrections but forget to fix them in corrected_message.
        if corrected_message:
            spelling_corrections = [
                c for c in corrections
                if c.type == CorrectionType.SPELLING
                and c.original and c.corrected
                and c.original != c.corrected
                and c.original in corrected_message
            ]
            for sc in spelling_corrections:
                corrected_message = corrected_message.replace(sc.original, sc.corrected, 1)
        verdict = result.get("verdict") or infer_verdict(has_errors, typo_count, is_level_correct)
        accuracy_score = max(0, min(100, int(accuracy_score)))
        accuracy_score = apply_error_based_score_cap(accuracy_score, corrections, is_level_correct)
        human_summary = build_human_feedback_summary(
            has_errors=has_errors,
            corrections=corrections,
            verdict=verdict,
            speech_level_correct=is_level_correct,
            expected_speech_level=expected_speech_level,
            message_intent=message_intent,
        )
        human_encouragement = build_human_encouragement(
            has_errors=has_errors,
            corrections=corrections,
            message_intent=message_intent,
        )

        return RealTimeCorrection(
            original_message=user_message,
            corrected_message=corrected_message,
            has_errors=has_errors,
            corrections=corrections,
            natural_alternatives=natural_alternatives,
            expected_speech_level=SPEECH_LEVEL_INFO[expected_speech_level]["name_ko"],
            expected_speech_level_code=expected_norm,
            detected_speech_level=LEVEL_KO_LABELS.get(detected_norm, detected_norm or clova_raw or expected_norm),
            detected_speech_level_code=detected_norm or clova_norm or expected_norm,
            speech_level_correct=is_level_correct,
            accuracy_score=accuracy_score,
            verdict=verdict,
            summary=human_summary or summary,
            input_kind=edit_strategy,
            encouragement=human_encouragement or postprocess_model_output(result.get("encouragement")) or local_rule_correction.encouragement,
        )

    async def _get_contextual_hint(
        self,
        avatar:               AvatarBase,
        conversation_history: List[ChatMessage],
        user_level:           str,
    ) -> Dict[str, Any]:

        prompt = build_contextual_hint_prompt(
            avatar=avatar,
            conversation_history=conversation_history,
            user_level=user_level,
        )

        result = await clova_service.analyze_json(prompt, temperature=0.5, max_tokens=300)

        if not result:
            speech_levels = get_speech_levels_for_role(avatar.role)
            level         = speech_levels["from_user"]
            if level == SpeechLevel.FORMAL:
                return {"example_responses": ["네, 알겠습니다.", "감사합니다.", "그렇군요."]}
            elif level == SpeechLevel.POLITE:
                return {"example_responses": ["그렇군요!", "더 알려주세요.", "저도 그래요."]}
            else:
                return {"example_responses": ["그래?", "진짜?", "나도!"]}

        return result

    def _update_streak(self, user_id: str, has_errors: bool) -> int:
        if has_errors:
            self.user_streaks[user_id] = 0
        else:
            self.user_streaks[user_id] = self.user_streaks.get(user_id, 0) + 1
        return self.user_streaks[user_id]

    def _calculate_mood_change(self, correction: RealTimeCorrection) -> int:
        if not correction.has_errors:
            if correction.streak_bonus:
                return 6
            if correction.accuracy_score >= 95:
                return 4
            return 2

        error_count   = sum(1 for c in correction.corrections if c.severity == CorrectionSeverity.ERROR)
        warning_count = sum(1 for c in correction.corrections if c.severity == CorrectionSeverity.WARNING)
        accuracy = correction.accuracy_score or 100

        if accuracy < 40:
            return -18
        if error_count >= 3:
            return -16
        if error_count >= 2:
            return -14
        if error_count == 1 and warning_count >= 1:
            return -10
        if error_count == 1:
            return -8
        if not correction.speech_level_correct:
            return -6
        if warning_count >= 2:
            return -5
        if warning_count == 1:
            return -3
        return -1

    def _update_mood(self, avatar_key: str, change: int) -> int:
        current  = self.user_moods.get(avatar_key, 80)
        new_mood = max(0, min(100, current + change))
        self.user_moods[avatar_key] = new_mood
        return new_mood

    def _get_mood_emoji(self, mood: int) -> str:
        if mood >= 75:
            return "happy"
        if mood >= 50:
            return "soso"
        if mood >= 25:
            return "sad"
        return "angry"

    async def analyze_message(
        self,
        avatar:               "AvatarBase",
        user_message:         str,
        conversation_history: List[ChatMessage],
        user_profile:         Optional[Any] = None,
        situation:            Optional[str] = None,
        user_id:              str = "default",
        session_id:           Optional[str] = None,
        expected_speech_level: Optional[str] = None,
        correction_context:   Optional[Dict[str, Any]] = None,
        response_instruction: Optional[List[str]] = None,
        include_reply:        bool = True,
    ) -> StructuredMessageResult:
        speech_levels  = get_speech_levels_for_role(avatar.role)
        expected_level = coerce_speech_level(expected_speech_level, speech_levels["from_user"])
        user_level     = (
            user_profile.korean_level.value
            if user_profile and hasattr(user_profile.korean_level, "value")
            else "intermediate"
        )
        session_key = session_id or f"{user_id}_{getattr(avatar, 'name_ko', 'avatar')}"
        effective_history = self._get_effective_history(session_key, conversation_history)

        correction = await self._analyze_realtime(
            user_message=user_message,
            expected_speech_level=expected_level,
            avatar_role=get_role_label(avatar.role, None),
            user_level=user_level,
            situation=situation,
            conversation_history=effective_history,
        )
        correction = self._merge_frontend_correction_context(
            correction=correction,
            user_message=user_message,
            expected_level=expected_level,
            correction_context=correction_context,
        )

        severity_map = {
            CorrectionSeverity.ERROR:   (2, "error"),
            CorrectionSeverity.WARNING: (1, "warning"),
            CorrectionSeverity.INFO:    (0, "info"),
        }
        error_breakdown: Dict[str, int] = {}
        errors: List[StructuredErrorItem] = []
        for c in correction.corrections:
            if c.original == c.corrected:
                continue
            sev_int, sev_label = severity_map.get(c.severity, (1, "warning"))
            errors.append(StructuredErrorItem(
                type=c.type.value if hasattr(c.type, "value") else str(c.type),
                subtype=None,
                original_fragment=c.original,
                corrected_fragment=c.corrected,
                explanation=c.explanation,
                severity=sev_int,
                severity_label=sev_label,
            ))
            key = c.type.value if hasattr(c.type, "value") else str(c.type)
            error_breakdown[key] = error_breakdown.get(key, 0) + 1

        top_focus = max(error_breakdown, key=lambda k: error_breakdown[k]) if error_breakdown else None

        analysis = StructuredMessageAnalysis(
            had_errors=correction.has_errors,
            accuracy_score=correction.accuracy_score,
            error_count=len(errors),
            expected_speech_level=correction.expected_speech_level,
            expected_speech_level_code=correction.expected_speech_level_code,
            detected_speech_level=correction.detected_speech_level,
            detected_speech_level_code=correction.detected_speech_level_code,
            speech_level_correct=correction.speech_level_correct,
            corrected_message=correction.corrected_message,
            summary=correction.summary,
            encouragement=correction.encouragement,
            top_focus=top_focus,
            error_breakdown=error_breakdown,
            errors=errors,
        )

        reply: Optional[StructuredMessageReply] = None
        if include_reply:
            try:
                current_mood = self.user_moods.get(f"{user_id}_{avatar.name_ko}", 80)
                system_prompt = build_avatar_system_prompt(
                    avatar=avatar,
                    user_profile=user_profile,
                    situation=situation,
                    current_mood=current_mood,
                    is_level_correct=correction.speech_level_correct,
                )
                system_prompt += self._build_turn_context_section(
                    user_message=user_message,
                    correction=correction,
                    correction_context=correction_context,
                    response_instruction=response_instruction or [],
                )
                history = [Message(role=m.role, content=m.content) for m in effective_history[-10:]]
                reply_user_msg = self._make_reply_user_message(user_message, correction)
                response = await clova_service.generate_with_system_prompt(
                    system_prompt=system_prompt,
                    user_message=reply_user_msg,
                    conversation_history=history,
                    temperature=0.65,
                )
                avatar_message = self._finalize_ai_reply(response.content, user_message, correction)
                hint_result = await self._get_contextual_hint(
                    avatar=avatar,
                    conversation_history=effective_history,
                    user_level=user_level,
                )
                suggestions = [
                    postprocess_model_output(t)
                    for t in hint_result.get("example_responses", [])
                    if postprocess_model_output(t)
                ]
                hint = postprocess_model_output(hint_result.get("hint"))
                reply = StructuredMessageReply(
                    avatar_message=avatar_message,
                    used_corrected_meaning=correction.has_errors,
                    suggestions=suggestions,
                    hint=hint,
                )
            except Exception as e:
                print(f"[analyze_message] reply generation failed: {e}")

        if correction.has_errors and session_key:
            try:
                self._save_mistakes(session_key, correction)
            except Exception as e:
                print(f"[analyze_message] failed to save mistakes: {e}")

        return StructuredMessageResult(analysis=analysis, reply=reply)

    async def analyze_conversation(
        self,
        avatar:               AvatarBase,
        conversation_history: List[ChatMessage],
        session_id:           Optional[str] = None,
        session_corrections:  Optional[List[Dict]] = None,
    ) -> ConversationAnalysis:
        speech_levels  = get_speech_levels_for_role(avatar.role)
        expected_level = speech_levels["from_user"]
        user_messages = self._extract_user_messages(conversation_history)

        speech_meta = self._calculate_speech_accuracy_score(
            user_messages=user_messages,
            expected_level=expected_level,
            avatar_role=avatar.role,
        )
        vocabulary_meta = self._calculate_vocabulary_score(user_messages)
        naturalness_meta = self._calculate_rule_naturalness_score(
            user_messages=user_messages,
            expected_level=expected_level,
            avatar_role=avatar.role,
        )

        stored_mistakes: List[Dict[str, str]] = []
        if session_id:
            try:
                stored_mistakes = self._load_session_mistakes(session_id)
            except Exception as e:
                print(f"[mistakes] failed to load: {e}")

        # Adjust speech_accuracy down based on actual saved mistakes per message.
        # 0 mistakes/msg → no change; 1+ mistakes/msg → up to -20.
        if user_messages:
            mistake_rate = len(stored_mistakes) / len(user_messages)
            mistake_penalty = round(min(20, mistake_rate * 20))
            if mistake_penalty > 0:
                speech_meta["score"] = max(0, speech_meta["score"] - mistake_penalty)
                speech_meta["components"]["stored_mistake_count"] = len(stored_mistakes)
                speech_meta["components"]["stored_mistake_penalty"] = mistake_penalty

        prompt = build_conversation_analysis_prompt(
            messages=[{"role": m.role, "content": m.content} for m in conversation_history],
            avatar_name=avatar.name_ko,
            expected_speech_level=expected_level,
            stored_mistakes=stored_mistakes or None,
            session_corrections=session_corrections or None,
        )

        result = await clova_service.analyze_json(prompt, temperature=0.3, max_tokens=2048)

        if not result:
            return ConversationAnalysis(
                scores={
                    "speech_accuracy": speech_meta["score"],
                    "vocabulary": vocabulary_meta["score"],
                    "naturalness": naturalness_meta["score"],
                },
                mistakes=[],
                vocabulary_to_learn=[],
                phrases_to_learn=[],
                overall_feedback="세션 점수는 규칙 기반으로 계산했어요. 모델 분석은 받지 못했지만, 말투와 표현 오류를 기준으로 점수를 만들었습니다.",
                score_details={
                    "speech_accuracy": speech_meta,
                    "vocabulary": vocabulary_meta,
                    "naturalness": naturalness_meta,
                },
                used_fallback_scores=False,
            )
        llm_scores = result.get("scores") or {}
        llm_naturalness = int(llm_scores.get("naturalness", naturalness_meta["score"]) or naturalness_meta["score"])
        naturalness_meta["components"]["llm_score"] = llm_naturalness
        naturalness_meta["score"] = max(
            0,
            min(100, round(naturalness_meta["score"] * 0.5 + llm_naturalness * 0.5)),
        )
        naturalness_meta["note"] = "규칙 기반 점수와 LLM 자연스러움 평가를 50:50으로 결합했습니다."

        final_scores = {
            "speech_accuracy": speech_meta["score"],
            "vocabulary": vocabulary_meta["score"],
            "naturalness": naturalness_meta["score"],
        }

        return ConversationAnalysis(
            scores=final_scores,
            mistakes=result.get("mistakes") or [],
            vocabulary_to_learn=result.get("vocabulary_to_learn") or [],
            phrases_to_learn=result.get("phrases_to_learn") or [],
            overall_feedback=result.get("overall_feedback") or "대화를 잘 진행하셨습니다!",
            score_details={
                "speech_accuracy": speech_meta,
                "vocabulary": vocabulary_meta,
                "naturalness": naturalness_meta,
            },
            used_fallback_scores=False,
        )

    async def generate_avatar_bio(self, avatar: AvatarBase) -> str:
        prompt   = build_bio_generation_prompt(avatar)
        response = await clova_service.chat(
            [Message(role="user", content=prompt)],
            temperature=0.7,
            max_tokens=500,
        )
        return response.content


# Global service instance
chat_service = ChatService()
