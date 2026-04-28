"""
Chat Service - Handles avatar conversations with real-time correction
"""
import re
from collections import Counter
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from app.schemas.avatar import AvatarBase, SpeechLevel, get_speech_levels_for_role, get_role_label
from app.schemas.user import UserProfile, KoreanLevel
from app.services.clova_service import clova_service, Message
from app.services.simple_speech_analyzer import get_speech_analyzer
from app.services.sophisticated_speech_analyzer import get_analyzer as get_sophisticated_speech_analyzer
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
    mood_emoji:   str = "😊"

    suggestions:    List[str]    = []
    hint:           Optional[str] = None
    correct_streak: int           = 0


class ConversationAnalysis(BaseModel):
    scores:              Dict[str, int]
    mistakes:            List[Dict[str, str]]
    vocabulary_to_learn: List[Dict[str, str]]
    phrases_to_learn:    List[Dict[str, str]]
    overall_feedback:    str
    score_details:       Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    used_fallback_scores: bool = False


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

    return f"""사용자의 한국어 메시지를 분석하여 실시간 교정 피드백을 제공하세요.

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

## 응답 형식 (JSON)
{{
    "has_errors": true/false,
    "corrected_message": "반드시 {speech_info['name_ko']}로 수정된 전체 메시지. 오류 없으면 null",
    "detected_speech_level": "formal / polite / informal 중 하나",
    "speech_level_correct": true/false,
    "accuracy_score": 0-100,
    "corrections": [
        {{
            "original": "반드시 사용자 메시지에 실제로 존재하는 표현만",
            "corrected": "올바른 {speech_info['name_ko']} 표현",
            "type": "speech_level/grammar/spelling/vocabulary/expression/honorific",
            "severity": "info/warning/error",
            "explanation": "왜 틀렸는지 한국어로 설명",
            "tip": "기억하기 쉬운 팁 (선택사항)"
        }}
    ],
    "natural_alternatives": [
        {{
            "expression": "이렇게도 말할 수 있어요 — 더 자연스러운 {speech_info['name_ko']} 표현",
            "explanation": "왜 이 표현이 더 자연스러운지 한 줄로"
        }}
    ],
    "encouragement": "잘한 점을 언급한 긍정적인 피드백 (1문장)"
}}

## natural_alternatives 규칙
- 오류가 없어도 반드시 1~2개 제안하세요
- 같은 의미지만 더 자연스럽고 세련된 {speech_info['name_ko']} 표현으로
- 원어민이 실제로 쓰는 표현으로
- 대화 맥락에 맞는 표현을 제안하세요
- "이렇게도 말할 수 있어요", "더 자연스러운 표현", "변경할 필요가 없습니다" 같은 메타 문구를 expression에 쓰지 마세요
- expression은 반드시 사용자가 실제로 바로 따라 말할 수 있는 완전한 한국어 문장만 쓰세요
- corrected_message와 완전히 같은 문장을 natural_alternatives에 다시 넣지 마세요

## 절대 규칙
- detected_speech_level 은 formal / polite / informal 중 하나 (null 불가)
- corrected_message 는 반드시 {speech_info['name_ko']} 말투로
- corrections original 은 사용자 메시지에 실제 존재하는 표현만
- 맥락상 자연스러운 표현은 오류 처리 금지
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

_FORMAL_ENDINGS   = ["습니다", "습니까", "십니까", "겠습니다", "십시오", "으십시오"]
_POLITE_ENDINGS   = ["어요", "아요", "이에요", "예요", "해요", "세요",
                     "네요", "군요", "죠", "나요", "가요", "래요",
                     "데요", "을게요", "ㄹ게요", "겠어요"]
_INFORMAL_ENDINGS = ["이야", "야", "이어", "어", "아", "지", "니",
                     "냐", "거야", "잖아", "이잖아", "구나", "군",
                     "을게", "ㄹ게", "자", "해", "래", "네"]
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
    ("갑시당", "갑시다", "'갑시당'은 장난스러운 채팅식 표기이고, 연습 문장에서는 '갑시다'가 자연스럽습니다."),
    ("봅시당", "봅시다", "'봅시당'은 장난스러운 채팅식 표기이고, 연습 문장에서는 '봅시다'가 자연스럽습니다."),
    ("합시당", "합시다", "'합시당'은 장난스러운 채팅식 표기이고, 연습 문장에서는 '합시다'가 자연스럽습니다."),
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
        return changed if changed and changed != text else _LEVEL_EXAMPLES["informal"]

    if expected_norm == "formal":
        changed = replace_all(spelling_fixed, [
            (r"안녕하세요|안녕", "안녕하십니까"),
            (r"만나서 반가워요|만나서 반가워", "만나서 반갑습니다"),
            (r"고마워요|고마워", "감사합니다"),
            (r"미안해요|미안해", "죄송합니다"),
            (r"어떻게 지내세요[?？]?|어떻게 지내요[?？]?|어떻게 지내[?？]?", "어떻게 지내십니까?"),
            (r"이에요|예요", "입니다"),
        ]).strip()
        return changed if changed and changed != text else _LEVEL_EXAMPLES["formal"]

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
    return changed if changed and changed != text else _LEVEL_EXAMPLES["polite"]


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
    speech_level_correct = (detected_norm == expected_norm) or (detected_norm == "")

    corrected_message = spelling_fixed if spelling_corrections else None
    if not speech_level_correct:
        corrected_message = make_level_suggestion(user_message, expected_norm)
        corrections.insert(0, InlineCorrection(
            original=user_message,
            corrected=corrected_message,
            type=CorrectionType.SPEECH_LEVEL,
            severity=CorrectionSeverity.ERROR,
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

    verdict = infer_verdict(has_errors, typo_count, speech_level_correct)
    alternative = corrected_message or spelling_fixed

    return RealTimeCorrection(
        original_message=user_message,
        corrected_message=corrected_message,
        has_errors=has_errors,
        corrections=corrections,
        natural_alternatives=[
            NaturalAlternative(
                expression=alternative,
                explanation=f"{expected_label} 상황에 맞게 더 자연스럽게 고친 표현입니다.",
            )
        ] if alternative and alternative != user_message else [],
        expected_speech_level=expected_label,
        expected_speech_level_code=expected_norm,
        detected_speech_level=LEVEL_KO_LABELS.get(detected_norm, detected_norm or expected_norm),
        detected_speech_level_code=detected_norm or expected_norm,
        speech_level_correct=speech_level_correct,
        accuracy_score=score,
        verdict=verdict,
        summary=(
            "오타와 말투를 함께 고치면 더 자연스러워요."
            if verdict == "speech_and_spelling"
            else "오타를 고치면 더 자연스러워요."
            if verdict == "spelling"
            else f"{expected_label}에 맞게 문장 끝맺음을 바꿔 주세요."
            if verdict == "wrong_speech_level"
            else ""
        ),
        encouragement="조금만 고치면 훨씬 자연스럽게 들려요." if has_errors else "자연스럽게 잘 말했어요.",
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
        self.sophisticated_speech_analyzer = None
        try:
            self.sophisticated_speech_analyzer = get_sophisticated_speech_analyzer()
        except Exception:
            self.sophisticated_speech_analyzer = None

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

    def _analyze_with_konlpy(self, text: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "available": False,
            "source": None,
            "speech": None,
            "morphemes": None,
        }

        try:
            if self.sophisticated_speech_analyzer and getattr(self.sophisticated_speech_analyzer, "use_morphological", False):
                speech_result = self.sophisticated_speech_analyzer.analyze(text)
                result["speech"] = speech_result
                result["available"] = True
                result["source"] = getattr(self.sophisticated_speech_analyzer.konlpy, "analyzer_name", "KoNLPy")
        except Exception:
            result["speech"] = None

        try:
            morph_result = morpheme_analyzer.analyze(text)
            if getattr(morph_result, "morphemes", None):
                result["morphemes"] = morph_result
                result["available"] = True
                if not result["source"]:
                    result["source"] = getattr(morpheme_analyzer, "engine", "KoNLPy")
        except Exception:
            result["morphemes"] = None

        return result

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
        score = max(0, min(100, round(100 - average_penalty)))

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

        advanced_terms = {
            "괜찮으시면", "도와주십시오", "부탁드립니다", "말씀", "연구실", "상담",
            "주문", "추가", "테이크아웃", "프로젝트", "발표", "회의", "피드백",
            "죄송합니다", "감사합니다", "알겠습니다", "어색하다", "자연스럽다",
        }
        advanced_token_count = sum(1 for token in tokens if token in advanced_terms or len(token) >= 4)
        difficulty_ratio = advanced_token_count / max(1, token_count)
        difficulty_score = min(100, round(25 + difficulty_ratio * 75))

        score = max(0, min(100, round(diversity_score * 0.7 + difficulty_score * 0.3)))

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
                "top_tokens": [token for token, _ in Counter(tokens).most_common(5)],
                "konlpy_samples_used": konlpy_samples_used,
                "konlpy_sources": sorted(set(konlpy_sources)),
            },
            "note": (
                "KoNLPy 형태소 분석으로 명사/동사를 뽑아 단어 다양성과 난도를 계산했습니다."
                if konlpy_samples_used > 0
                else "단어 다양성과 상대적으로 난도가 높은 어휘 사용 비율을 함께 반영했습니다."
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
        score = max(0, min(100, round(100 - average_penalty)))

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

        system_prompt += self._build_turn_context_section(
            user_message=user_message,
            correction=correction,
            correction_context=correction_context,
            response_instruction=response_instruction or [],
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
            suggestions = hint_result.get("example_responses", [])
            hint        = hint_result.get("hint")

        self._remember_session_turn(session_key, user_message, final_message, effective_history)

        return ChatResponse(
            message=final_message,
            correction=correction,
            mood_change=mood_change,
            current_mood=new_mood,
            mood_emoji=mood_emoji,
            suggestions=suggestions,
            hint=hint,
            correct_streak=streak,
        )

    def _get_effective_history(
        self,
        session_key: str,
        conversation_history: List[ChatMessage],
    ) -> List[ChatMessage]:
        """Merge frontend-sent history with server-side session memory."""
        incoming = conversation_history or []
        stored = self.session_turns.get(session_key, [])
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
        self.session_turns[session_key] = history[-20:]

    def _build_turn_context_section(
        self,
        user_message: str,
        correction: RealTimeCorrection,
        correction_context: Optional[Dict[str, Any]],
        response_instruction: List[str],
    ) -> str:
        corrected = correction.corrected_message or self._best_corrected_expression(correction) or user_message
        recent_mistakes = (correction_context or {}).get("recent_mistakes") or []
        recent_mistake_lines = "\n".join(
            f"- {m.get('message', '')} -> {m.get('corrected', '')}"
            for m in recent_mistakes[-4:]
            if isinstance(m, dict)
        )
        extra_guidance = "\n".join(
            f"- {line}" for line in response_instruction if str(line).strip()
        )

        return f"""

## 현재 턴 응답 생성 규칙 (최우선)
- 사용자 원문: {user_message}
- 교정 후 의도: {corrected}
- 기대 말투: {correction.expected_speech_level}
- 감지 말투: {correction.detected_speech_level or "불명확"}
- 오류 여부: {"있음" if correction.has_errors else "없음"}
- 요약: {correction.summary or "특이사항 없음"}

## 채팅 말풍선 규칙
- 채팅 답변에는 "polite detected", "감지", "점수", "정확도", "분석 결과" 같은 분석 라벨을 절대 쓰지 마세요.
- 오류가 있으면 첫 문장에서 자연스러운 수정 문장을 짧게 알려주고, 바로 캐릭터답게 대화를 이어가세요.
- 오류가 없으면 교정 설명을 길게 하지 말고, 사용자의 내용에 자연스럽게 반응하세요.
- 답변은 1~3문장으로 짧고 실제 사람이 말하듯 작성하세요.
- 이모지와 장식 기호는 사용하지 마세요.

## 최근 반복 실수
{recent_mistake_lines or "- 없음"}
{extra_guidance}
"""

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
        if correction.natural_alternatives:
            return correction.natural_alternatives[0].expression
        if correction.corrections:
            return correction.corrections[0].corrected
        return correction.corrected_message

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
            corrected = self._best_corrected_expression(correction) or user_message
            if correction.verdict == "speech_and_spelling":
                return f'"{corrected}"라고 하면 더 자연스러워. 좋아, 그 표현으로 다시 이어가 보자.'
            if correction.verdict == "spelling":
                return f'"{corrected}"가 맞는 표기야. 무슨 말인지 알겠어. 이어서 말해줘.'
            if correction.verdict == "wrong_speech_level":
                return f'"{corrected}"처럼 말하면 지금 관계에 더 잘 맞아. 그럼 계속 이야기해 보자.'
            return f'"{corrected}"라고 하면 더 자연스러워. 계속 이어가 볼게.'

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
        conversation_history:  List[ChatMessage] = [],   # ← 추가
    ) -> RealTimeCorrection:

        msg_stripped  = user_message.strip()
        expected_norm = LEVEL_MAP.get(
            SPEECH_LEVEL_INFO[expected_speech_level]["name_ko"].lower(),
            expected_speech_level.value.lower(),
        )
        local_rule_correction = build_rule_based_correction(user_message, expected_speech_level)

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
        is_level_correct = (detected_norm == expected_norm) or (detected_norm == "")

        # ── has_errors — info 제외 ────────────────────────────────────────────
        real_errors = [
            c for c in corrections
            if c.severity in (CorrectionSeverity.ERROR, CorrectionSeverity.WARNING)
        ]
        has_errors     = (len(real_errors) > 0) or not is_level_correct or local_rule_correction.has_errors
        accuracy_score = int(result.get("accuracy_score", 100) or 100)

        if not has_errors and corrections:
            accuracy_score = max(accuracy_score, 90)
        if local_rule_correction.has_errors:
            accuracy_score = min(accuracy_score, local_rule_correction.accuracy_score)

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
        if best_corrected:
            corrected_message = best_corrected
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
        verdict = result.get("verdict") or infer_verdict(has_errors, typo_count, is_level_correct)
        accuracy_score = max(0, min(100, int(accuracy_score)))

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
            summary=summary,
            encouragement=postprocess_model_output(result.get("encouragement")) or local_rule_correction.encouragement,
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
            return 8 if correction.streak_bonus else 3
        error_count   = sum(1 for c in correction.corrections if c.severity == CorrectionSeverity.ERROR)
        warning_count = sum(1 for c in correction.corrections if c.severity == CorrectionSeverity.WARNING)
        if error_count >= 2:     return -10
        elif error_count == 1:   return -5
        elif warning_count >= 2: return -3
        else:                    return -1

    def _update_mood(self, avatar_key: str, change: int) -> int:
        current  = self.user_moods.get(avatar_key, 80)
        new_mood = max(0, min(100, current + change))
        self.user_moods[avatar_key] = new_mood
        return new_mood

    def _get_mood_emoji(self, mood: int) -> str:
        if mood >= 90:   return "😄"
        elif mood >= 70: return "😊"
        elif mood >= 50: return "😐"
        elif mood >= 30: return "😕"
        else:            return "😢"

    async def analyze_conversation(
        self,
        avatar:               AvatarBase,
        conversation_history: List[ChatMessage],
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

        prompt = build_conversation_analysis_prompt(
            messages=[{"role": m.role, "content": m.content} for m in conversation_history],
            avatar_name=avatar.name_ko,
            expected_speech_level=expected_level,
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
            min(100, round(naturalness_meta["score"] * 0.7 + llm_naturalness * 0.3)),
        )
        naturalness_meta["note"] = "규칙 기반 점수에 LLM 자연스러움 평가를 보조적으로 섞었습니다."

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
