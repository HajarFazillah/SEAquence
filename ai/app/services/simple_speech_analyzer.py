"""
Korean Speech Level Analyzer - Context-Aware Rule-Based Prototype

Purpose:
- Detect Korean speech level: 합쇼체 / 해요체 / 반말
- Detect mixed speech levels within one message
- Detect honorific vocabulary issues
- Detect directness issues in requests, permissions, apologies, refusals
- Evaluate appropriateness based on social context:
  avatar role, situation, speech act, age gap, closeness, public/private setting

This module is designed as a first-layer analyzer before optional LLM-based
natural feedback generation.

Recommended use in Talkativ:
1. Run this analyzer first.
2. Use the returned structured errors as evidence.
3. Optionally pass the result to an LLM to generate more natural coaching feedback.
"""

import re
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


# ============================================================
# Enums
# ============================================================

class SpeechLevel(Enum):
    FORMAL = "formal"       # 합쇼체
    POLITE = "polite"       # 해요체
    INFORMAL = "informal"   # 반말
    UNKNOWN = "unknown"


class ErrorType(Enum):
    WRONG_LEVEL = "wrong_level"
    MIXED_LEVEL = "mixed_level"
    HONORIFIC_MISSING = "honorific_missing"
    WORD_CHOICE = "word_choice"
    PRONOUN_ERROR = "pronoun_error"
    DIALECT = "dialect"
    DIRECTNESS = "directness"
    TOO_STIFF = "too_stiff"
    TOO_CASUAL = "too_casual"
    UNCERTAIN = "uncertain"


# ============================================================
# Dictionaries and pattern rules
# ============================================================

SHORT_INFORMAL = {
    "응", "어", "어어", "응응", "어응", "아",
    "ㅇ", "ㅇㅇ", "ㅇㅇㅇ", "ㅇㅋ", "ㄴ", "ㄴㄴ", "ㄱㄱ",
    "ㅋ", "ㅋㅋ", "ㅋㅋㅋ", "ㅎ", "ㅎㅎ", "ㅎㅎㅎ",
    "ㅠ", "ㅠㅠ", "ㅜ", "ㅜㅜ", "ㅠㅠㅠ", "ㄷㄷ", "ㄷㄷㄷ", "ㄹㅇ", "ㅂㅂ",
    "야", "야야", "아니", "맞아", "좋아", "싫어",
    "몰라", "알아", "그래", "안돼", "됐어",
    "와", "우와", "헐", "대박", "진짜",
}

SHORT_POLITE = {
    "네", "예", "아네", "아예", "네네", "예예",
    "맞아요", "그래요", "좋아요", "알겠어요",
    "감사해요", "괜찮아요", "천만에요",
}

SHORT_FORMAL = {
    "네, 알겠습니다", "그렇습니다", "알겠습니다",
    "감사합니다", "죄송합니다", "실례합니다", "아닙니다",
}

AMBIGUOUS_SHORT = {"네", "예", "아"}


DIALECT_SLANG = {
    "머해": "뭐 해",
    "머라": "뭐라",
    "와캐": "왜 그래",
    "왜캐": "왜 그래",
    "이거머": "이게 뭐야",
    "마": "말",
    "ㅇㅈ": "인정",
    "ㅂㅂ": "바이바이",
    "ㅈㅅ": "죄송",
    "ㄱㅅ": "감사",
    "ㅊㅋ": "축하",
    "ㄷㄷ": "덜덜",
    "ㅇㅋ": "오케이",
    "왜이래": "왜 이러는 거야",
    "왜그래": "왜 그러는 거야",
    "어쩌라고": "어떻게 하라는 거야",
}


WORD_FORMALITY_ERRORS = {
    "나 ": {
        "expected": "저 ",
        "level": "polite",
        "type": ErrorType.PRONOUN_ERROR,
        "explanation": "윗사람이나 공식적인 상황에서는 '나'보다 '저'를 사용하는 것이 자연스럽습니다.",
    },
    "나는": {
        "expected": "저는",
        "level": "polite",
        "type": ErrorType.PRONOUN_ERROR,
        "explanation": "'나는'보다 '저는'이 더 공손합니다.",
    },
    "나가": {
        "expected": "제가",
        "level": "polite",
        "type": ErrorType.PRONOUN_ERROR,
        "explanation": "'나가' 대신 '제가'를 사용하세요.",
    },
    "내가": {
        "expected": "제가",
        "level": "polite",
        "type": ErrorType.PRONOUN_ERROR,
        "explanation": "'내가'보다 '제가'가 더 공손합니다.",
    },
    "나를": {
        "expected": "저를",
        "level": "polite",
        "type": ErrorType.PRONOUN_ERROR,
        "explanation": "'나를'보다 '저를'이 더 공손합니다.",
    },
    "나한테": {
        "expected": "저한테",
        "level": "polite",
        "type": ErrorType.PRONOUN_ERROR,
        "explanation": "'나한테'보다 '저한테'가 더 공손합니다.",
    },
    "우리": {
        "expected": "저희",
        "level": "formal",
        "type": ErrorType.WORD_CHOICE,
        "explanation": "공식적인 자기소개나 발표 상황에서는 '우리'보다 '저희'가 더 자연스러울 수 있습니다.",
    },
    "밥 ": {
        "expected": "식사 ",
        "level": "formal",
        "type": ErrorType.WORD_CHOICE,
        "explanation": "윗사람에게는 '밥'보다 '식사'가 더 공손합니다.",
    },
    "밥은": {
        "expected": "식사는",
        "level": "formal",
        "type": ErrorType.WORD_CHOICE,
        "explanation": "윗사람에게는 '밥'보다 '식사'가 더 공손합니다.",
    },
    "밥을": {
        "expected": "식사를",
        "level": "formal",
        "type": ErrorType.WORD_CHOICE,
        "explanation": "윗사람에게는 '밥'보다 '식사'가 더 공손합니다.",
    },
    "이름": {
        "expected": "성함",
        "level": "formal",
        "type": ErrorType.WORD_CHOICE,
        "explanation": "상대방의 이름을 공손하게 말할 때는 '성함'이 더 자연스럽습니다.",
    },
    "나이": {
        "expected": "연세",
        "level": "formal",
        "type": ErrorType.WORD_CHOICE,
        "explanation": "어른의 나이를 공손하게 말할 때는 '연세'가 더 자연스럽습니다.",
    },
    "아빠": {
        "expected": "아버지",
        "level": "polite",
        "type": ErrorType.WORD_CHOICE,
        "explanation": "공식적인 상황에서는 '아빠'보다 '아버지'가 더 적절합니다.",
    },
    "엄마": {
        "expected": "어머니",
        "level": "polite",
        "type": ErrorType.WORD_CHOICE,
        "explanation": "공식적인 상황에서는 '엄마'보다 '어머니'가 더 적절합니다.",
    },
}


REQUIRES_HONORIFIC_VERBS = {
    "먹어요": "드세요",
    "먹었어요": "드셨어요",
    "자요": "주무세요",
    "잤어요": "주무셨어요",
    "있어요": "계세요",
    "있었어요": "계셨어요",
    "말해요": "말씀하세요",
    "물어봐요": "여쭤봐요",
    "줘요": "드려요",
    "봐요": "뵈어요",
}


SERVICE_REQUEST_PATTERNS = [
    {
        "pattern": re.compile(r"주면\s*돼"),
        "expected": "주세요",
        "explanation": "주문이나 요청 상황에서는 '주면 돼'보다 '주세요'가 더 자연스럽고 공손합니다.",
    },
    {
        "pattern": re.compile(r"주라"),
        "expected": "주세요",
        "explanation": "가게 직원이나 처음 만난 사람에게는 명령형보다 '주세요'가 더 자연스럽습니다.",
    },
    {
        "pattern": re.compile(r"줘\b"),
        "expected": "주세요",
        "explanation": "서비스 상황에서는 '줘'보다 '주세요'가 더 자연스럽습니다.",
    },
]


DIRECT_REQUEST_PATTERNS = [
    {
        "pattern": re.compile(r"(해줘|줘|보내줘|알려줘|가져와|도와줘)"),
        "softened": "해주실 수 있을까요?",
        "explanation": "요청 표현이 직접적으로 들릴 수 있습니다. 정중한 상황에서는 간접 요청 표현이 더 자연스럽습니다.",
    },
    {
        "pattern": re.compile(r"(해도 돼요|내도 돼요|가도 돼요|써도 돼요|먹어도 돼요|봐도 돼요)"),
        "softened": "해도 괜찮을까요?",
        "explanation": "'돼요?'는 상황에 따라 가볍게 들릴 수 있습니다. 공식적인 상황에서는 '괜찮을까요?'가 더 정중합니다.",
    },
    {
        "pattern": re.compile(r"(빨리|지금 바로|당장)"),
        "softened": "가능하시다면",
        "explanation": "상대에게 부담을 줄 수 있는 표현입니다. 완곡한 표현을 함께 쓰는 것이 좋습니다.",
    },
    {
        "pattern": re.compile(r"(왜 안|왜 못|왜 이렇게)"),
        "softened": "혹시 어떤 이유로",
        "explanation": "질문이 따지거나 비난하는 느낌으로 들릴 수 있습니다. 이유를 부드럽게 묻는 표현이 더 자연스럽습니다.",
    },
]


HONORIFIC_SI_PATTERNS = [
    r"[가-힣]+시[고는도며서]",
    r"[가-힣]+세요",
    r"[가-힣]+셨",
    r"[가-힣]+시겠",
    r"[가-힣]+으시",
    r"계세요",
    r"계십니",
    r"드세요",
    r"드셨",
]


FORMAL_PATTERNS = [
    r"습니다[.?!]?$",
    r"습니까[?]?$",
    r"십시오[.!]?$",
    r"십니까[?]?$",
    r"옵니다[.?!]?$",
    r"옵니까[?]?$",
    r"하십시오[.!]?$",
    r"드립니다[.?!]?$",
    r"드릴까요[?]?$",
    r"드렸습니다[.?!]?$",
    r"드리겠습니다[.?!]?$",
    r"겠습니다[.?!]?$",
    r"겠습니까[?]?$",
    r"었습니다[.?!]?$",
    r"았습니다[.?!]?$",
    r"였습니다[.?!]?$",
    r"계십니까[?]?$",
    r"계십니다[.?!]?$",
    r"입니다[.?!]?$",
    r"입니까[?]?$",
    r"였습니까[?]?$",
    r"아닙니다[.?!]?$",
    r"아닙니까[?]?$",
    r"주십시오[.!]?$",
    r"해주십시오[.!]?$",
    r"알려주십시오[.!]?$",
    r"부탁드립니다[.?!]?$",
    r"말씀해주십시오[.!]?$",
    r"바랍니다[.?!]?$",
    r"시겠습니까[?]?$",
    r"시겠습니다[.?!]?$",
    r"셨습니다[.?!]?$",
    r"셨습니까[?]?$",
    r"합니다[.?!]?$",
    r"됩니다[.?!]?$",
    r"됩니까[?]?$",
    r"있습니다[.?!]?$",
    r"없습니다[.?!]?$",
    r"있습니까[?]?$",
    r"없습니까[?]?$",
]


POLITE_PATTERNS = [
    r"[아어여이]요[.?!]?$",
    r"해요[.?!]?$",
    r"세요[.?!]?$",
    r"예요[.?!]?$",
    r"이에요[.?!]?$",
    r"네요[.?!]?$",
    r"죠[.?!]?$",
    r"나요[.?!]?$",
    r"는데요[.?!]?$",
    r"ㄴ데요[.?!]?$",
    r"거든요[.?!]?$",
    r"잖아요[.?!]?$",
    r"군요[.?!]?$",
    r"구나요[.?!]?$",
    r"더라고요[.?!]?$",
    r"더라구요[.?!]?$",
    r"할게요[.?!]?$",
    r"갈게요[.?!]?$",
    r"볼게요[.?!]?$",
    r"줄게요[.?!]?$",
    r"올게요[.?!]?$",
    r"먹을게요[.?!]?$",
    r"말할게요[.?!]?$",
    r"할까요[?]?$",
    r"갈까요[?]?$",
    r"볼까요[?]?$",
    r"먹을까요[?]?$",
    r"드릴까요[?]?$",
    r"일까요[?]?$",
    r"될까요[?]?$",
    r"싶어요[.?!]?$",
    r"같아요[.?!]?$",
    r"있어요[.?!]?$",
    r"없어요[.?!]?$",
    r"좋아요[.?!]?$",
    r"싫어요[.?!]?$",
    r"됐어요[.?!]?$",
    r"됐죠[.?!]?$",
    r"맞아요[.?!]?$",
    r"괜찮아요[.?!]?$",
    r"어때요[?]?$",
    r"어떠세요[?]?$",
    r"했어요[.?!]?$",
    r"갔어요[.?!]?$",
    r"왔어요[.?!]?$",
    r"봤어요[.?!]?$",
    r"먹었어요[.?!]?$",
    r"마셨어요[.?!]?$",
    r"받았어요[.?!]?$",
    r"끝났어요[.?!]?$",
    r"알았어요[.?!]?$",
    r"몰랐어요[.?!]?$",
    r"겠어요[.?!]?$",
    r"겠죠[.?!]?$",
    r"주세요[.!]?$",
    r"해주세요[.!]?$",
    r"알려주세요[.!]?$",
    r"말씀해주세요[.!]?$",
    r"부탁해요[.?!]?$",
    r"것 같아요[.?!]?$",
    r"것 같죠[.?!]?$",
    r"인 것 같아요[.?!]?$",
    r"시어요[.?!]?$",
    r"셔요[.?!]?$",
    r"싶죠[.?!]?$",
]


INFORMAL_PATTERNS = [
    r"[아어][\s.?!]*$",
    r"야[.?!]?$",
    r"지[.?!]?$",
    r"냐[?]?$",
    r"니[?]?$",
    r"네[.?!]?$",
    r"군[.?!]?$",
    r"구나[.?!]?$",
    r"거야[.?!]?$",
    r"거지[.?!]?$",
    r"잖아[.?!]?$",
    r"는데[.?!]?$",
    r"ㄴ데[.?!]?$",
    r"더라[.?!]?$",
    r"거든[.?!]?$",
    r"더라고[.?!]?$",
    r"더라구[.?!]?$",
    r"잖니[?]?$",
    r"할게[.?!]?$",
    r"갈게[.?!]?$",
    r"볼게[.?!]?$",
    r"줄게[.?!]?$",
    r"올게[.?!]?$",
    r"먹을게[.?!]?$",
    r"말할게[.?!]?$",
    r"가자[.?!]?$",
    r"하자[.?!]?$",
    r"먹자[.?!]?$",
    r"보자[.?!]?$",
    r"놀자[.?!]?$",
    r"자자[.?!]?$",
    r"끝내자[.?!]?$",
    r"해봐[.?!]?$",
    r"해봐라[.?!]?$",
    r"해라[.!]?$",
    r"가라[.!]?$",
    r"봐라[.!]?$",
    r"먹어라[.!]?$",
    r"와라[.!]?$",
    r"뭐야[.?!]?$",
    r"뭐해[.?!]?$",
    r"뭐냐[?]?$",
    r"어디야[?]?$",
    r"어디가[?]?$",
    r"왜야[?]?$",
    r"언제야[?]?$",
    r"누구야[?]?$",
    r"좋아[.?!]?$",
    r"싫어[.?!]?$",
    r"있어[.?!]?$",
    r"없어[.?!]?$",
    r"맞아[.?!]?$",
    r"아니야[.?!]?$",
    r"괜찮아[.?!]?$",
    r"어때[?]?$",
    r"몰라[.?!]?$",
    r"알아[.?!]?$",
    r"됐어[.?!]?$",
    r"했어[.?!]?$",
    r"갔어[.?!]?$",
    r"왔어[.?!]?$",
    r"봤어[.?!]?$",
    r"먹었어[.?!]?$",
    r"마셨어[.?!]?$",
    r"받았어[.?!]?$",
    r"끝났어[.?!]?$",
    r"알았어[.?!]?$",
    r"몰랐어[.?!]?$",
    r"겠어[.?!]?$",
    r"할 거야[.?!]?$",
    r"갈 거야[.?!]?$",
    r"할거야[.?!]?$",
    r"갈거야[.?!]?$",
    r"이야[.?!]?$",
    r"인데[.?!]?$",
    r"싶어[.?!]?$",
    r"할까[?]?$",
    r"갈까[?]?$",
    r"볼까[?]?$",
    r"먹을까[?]?$",
    r"같아[.?!]?$",
    r"것 같아[.?!]?$",
    r"ㅋ+$",
    r"ㅎ+$",
    r"ㄷㄷ$",
    r"ㅠ+$",
    r"ㅜ+$",
    r"마[.?!]?$",
    r"가[.?!]?$",
    r"데이[.?!]?$",
    r"돼[.?!]?$",
    r"줘[.?!]?$",
    r"봐[.?!]?$",
]


LEVEL_INFO = {
    SpeechLevel.FORMAL: {"ko": "합쇼체", "en": "Formal"},
    SpeechLevel.POLITE: {"ko": "해요체", "en": "Polite"},
    SpeechLevel.INFORMAL: {"ko": "반말", "en": "Informal"},
    SpeechLevel.UNKNOWN: {"ko": "알 수 없음", "en": "Unknown"},
}


# ============================================================
# Morpheme-based speech level detection (Komoran)
# ============================================================
#
# Korean speech level is carried by the final 어미 (sentence ending), which is
# a *morpheme*, not a substring — so suffix regex on word tails will always
# miss contractions like "안 해도 돼" (the 어미 is `어`, not `돼`).
#
# Komoran POS-tags inflected verbs into stem + endings (e.g.
# "해주세요" → [(하,VV),(아,EC),(주,VX),(시,EP),(어요,EC)]). We look at the LAST
# E-tag morpheme and map it to a speech level. This catches the cases that the
# surface-form regex layer misses.
#
# Komoran is not perfect (it sometimes misclassifies set phrases like
# "안녕하십니까" as a single noun), so this layer is intentionally a *fallback*
# for cases where the surface regex doesn't fire — the LLM still gets the
# final say downstream.

_FINAL_ENDINGS_FORMAL = {
    "습니다", "ㅂ니다", "습니까", "ㅂ니까", "십시오", "으십시오",
    "십니다", "십니까", "겠습니다", "겠습니까", "셨습니다", "셨습니까",
    "였습니다", "였습니까", "옵니다", "옵니까",
}

_FINAL_ENDINGS_POLITE = {
    "어요", "아요", "여요", "예요", "에요", "이에요",
    "세요", "으세요", "셔요", "시어요",
    "네요", "군요", "구나요", "죠", "지요",
    "나요", "까요", "ㄹ까요", "을까요", "ㄹ게요", "을게요",
    "는데요", "ㄴ데요", "데요", "거든요", "잖아요",
    "래요", "ㄹ래요", "을래요", "더라고요", "더라구요",
    "겠어요", "겠죠",
}

_FINAL_ENDINGS_INFORMAL = {
    "어", "아", "여", "지", "네", "군", "구나", "구만",
    "거야", "거지", "거든", "잖아", "잖니",
    "ㄹ게", "을게", "ㄹ까", "을까", "ㄹ래", "을래",
    "냐", "니", "자", "야",
    "더라", "더라고", "더라구", "ㄴ데", "는데",
    "겠어", "이야",
}

_komoran_instance = None
_komoran_init_attempted = False


def _get_komoran():
    """Lazily initialize a Komoran instance. Returns None if unavailable."""
    global _komoran_instance, _komoran_init_attempted
    if _komoran_init_attempted:
        return _komoran_instance
    _komoran_init_attempted = True
    try:
        from konlpy.tag import Komoran
        _komoran_instance = Komoran()
        logger.info("Komoran morpheme analyzer initialized for speech-level detection")
    except Exception as e:
        logger.warning(f"Komoran unavailable, morpheme-level detection disabled: {e}")
        _komoran_instance = None
    return _komoran_instance


def detect_speech_level_by_morpheme(text: str) -> str:
    """Detect speech level from the final sentence-ending morpheme.

    Returns one of "formal", "polite", "informal", or "" (unknown / not
    confident). Falls back gracefully to "" if Komoran isn't installed or
    if the tagger produces no recognizable ending.
    """
    if not text:
        return ""

    komoran = _get_komoran()
    if komoran is None:
        return ""

    cleaned = re.sub(r"[.!?…。？！\"')\]\s]+$", "", text.strip())
    if not cleaned:
        return ""

    try:
        morphs = komoran.pos(cleaned)
    except Exception:
        return ""

    # Walk back from the end looking for the final ending morpheme.
    for token, tag in reversed(morphs):
        if not tag.startswith("E"):
            continue
        if token in _FINAL_ENDINGS_FORMAL:
            return "formal"
        if token in _FINAL_ENDINGS_POLITE:
            return "polite"
        if token in _FINAL_ENDINGS_INFORMAL:
            return "informal"
        # Unknown ending shape — keep walking; the very last E-tag may be a
        # connective like 아도/어서, with the real terminal ending earlier.
    return ""


# ============================================================
# Dataclasses
# ============================================================

@dataclass
class ConversationContext:
    avatar_role: Optional[str] = None
    relationship: Optional[str] = None
    situation: Optional[str] = None
    speech_act: Optional[str] = None
    age_gap: Optional[int] = None
    closeness: Optional[int] = None  # 1 = not close, 5 = very close
    is_public: bool = False
    user_goal: Optional[str] = None


@dataclass
class SentenceResult:
    sentence: str
    level: SpeechLevel
    confidence: float
    matched_pattern: Optional[str] = None
    is_short: bool = False
    is_dialect: bool = False
    word_errors: List[dict] = field(default_factory=list)


@dataclass
class AnalysisResult:
    text: str
    overall_level: SpeechLevel
    overall_level_ko: str
    overall_level_en: str
    confidence: float
    sentences: List[SentenceResult] = field(default_factory=list)
    is_mixed: bool = False
    mixed_detail: str = ""
    word_errors: List[dict] = field(default_factory=list)
    dialect_found: List[str] = field(default_factory=list)
    missing_honorifics: List[dict] = field(default_factory=list)
    directness_errors: List[dict] = field(default_factory=list)
    suggested_correction: Optional[str] = None
    native_alternative: Optional[str] = None
    is_appropriate: Optional[bool] = None
    expected_level: Optional[str] = None
    acceptable_levels: List[str] = field(default_factory=list)
    appropriateness_reason_ko: Optional[str] = None
    feedback_ko: Optional[str] = None
    feedback_en: Optional[str] = None
    score: int = 100


# ============================================================
# Utility functions
# ============================================================

def normalize_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def split_sentences(text: str) -> List[str]:
    """
    Splits text into sentence-like chunks.
    Keeps this simple because Korean informal text can be fragmented.
    """
    text = text.strip()
    if not text:
        return []

    parts = re.split(r"(?<=[.?!])\s+|(?<=[.?!])$", text)

    result = []
    for part in parts:
        part = part.strip()
        if not part:
            continue

        for line in part.split("\n"):
            line = line.strip()
            if not line:
                continue

            if len(line) > 40 and "," in line:
                result.extend([p.strip() for p in line.split(",") if p.strip()])
            else:
                result.append(line)

    return result


# ============================================================
# Main Analyzer
# ============================================================

class NativeSpeechAnalyzer:
    def __init__(self):
        self._formal_patterns = [re.compile(p) for p in FORMAL_PATTERNS]
        self._polite_patterns = [re.compile(p) for p in POLITE_PATTERNS]
        self._informal_patterns = [re.compile(p) for p in INFORMAL_PATTERNS]
        self._honorific_si_patterns = [re.compile(p) for p in HONORIFIC_SI_PATTERNS]

    # ------------------------------------------------------------
    # Basic speech-level analysis
    # ------------------------------------------------------------

    def analyze(self, text: str) -> AnalysisResult:
        text = normalize_text(text)
        sentences = split_sentences(text)

        if not sentences:
            return self._empty(text)

        sentence_results = [self._analyze_sentence(sentence) for sentence in sentences]

        overall = self._aggregate(sentence_results)
        is_mixed, mixed_detail = self._detect_mixing(sentence_results)
        word_errors = self._check_words(text)
        dialect_found = self._detect_dialect(text)
        missing_honorifics = self._check_honorifics(text)

        score = self._score(
            sentences=sentence_results,
            is_mixed=is_mixed,
            word_errors=word_errors,
            missing_honorifics=missing_honorifics,
            directness_errors=[],
        )

        info = LEVEL_INFO[overall]

        return AnalysisResult(
            text=text,
            overall_level=overall,
            overall_level_ko=info["ko"],
            overall_level_en=info["en"],
            confidence=round(sum(r.confidence for r in sentence_results) / len(sentence_results), 2),
            sentences=sentence_results,
            is_mixed=is_mixed,
            mixed_detail=mixed_detail,
            word_errors=word_errors,
            dialect_found=dialect_found,
            missing_honorifics=missing_honorifics,
            score=score,
        )

    def _analyze_sentence(self, sentence: str) -> SentenceResult:
        s = sentence.strip()
        lower = s.lower()

        if lower in SHORT_INFORMAL:
            return SentenceResult(s, SpeechLevel.INFORMAL, 0.95, is_short=True)

        if lower in SHORT_POLITE:
            return SentenceResult(s, SpeechLevel.POLITE, 0.95, is_short=True)

        if lower in SHORT_FORMAL:
            return SentenceResult(s, SpeechLevel.FORMAL, 0.95, is_short=True)

        if lower in AMBIGUOUS_SHORT:
            return SentenceResult(s, SpeechLevel.UNKNOWN, 0.3, is_short=True)

        is_dialect = any(d in s for d in DIALECT_SLANG)

        formal_matches = sum(1 for pattern in self._formal_patterns if pattern.search(s))
        polite_matches = sum(1 for pattern in self._polite_patterns if pattern.search(s))
        informal_matches = sum(1 for pattern in self._informal_patterns if pattern.search(s))

        formal_score = formal_matches * 3
        polite_score = polite_matches * 2
        informal_score = informal_matches * 1

        total_score = formal_score + polite_score + informal_score

        if total_score == 0:
            level, matched_pattern = self._guess(s)
            confidence = 0.4 if level != SpeechLevel.UNKNOWN else 0.2

        elif formal_score >= polite_score and formal_score >= informal_score:
            level = SpeechLevel.FORMAL
            matched_pattern = "formal"
            confidence = min(0.98, 0.6 + formal_score / (total_score + 1) * 0.4)

        elif polite_score >= informal_score:
            level = SpeechLevel.POLITE
            matched_pattern = "polite"
            confidence = min(0.95, 0.5 + polite_score / (total_score + 1) * 0.4)

        else:
            level = SpeechLevel.INFORMAL
            matched_pattern = "informal"
            confidence = min(0.90, 0.4 + informal_score / (total_score + 1) * 0.4)

        word_errors = self._check_words(s)

        return SentenceResult(
            sentence=s,
            level=level,
            confidence=round(confidence, 2),
            matched_pattern=matched_pattern,
            is_short=False,
            is_dialect=is_dialect,
            word_errors=word_errors,
        )

    def _guess(self, text: str) -> Tuple[SpeechLevel, Optional[str]]:
        t = text.rstrip("?.! ")

        if t.endswith(("습니다", "습니까", "십시오", "옵니다", "입니다", "드립니다")):
            return SpeechLevel.FORMAL, "guess"

        if t.endswith(("요", "세요", "해요", "죠", "네요", "까요")):
            return SpeechLevel.POLITE, "guess"

        if t.endswith(("어", "아", "야", "지", "냐", "니", "군", "구나")):
            return SpeechLevel.INFORMAL, "guess"

        return SpeechLevel.UNKNOWN, None

    def _aggregate(self, results: List[SentenceResult]) -> SpeechLevel:
        counts = {
            SpeechLevel.FORMAL: 0.0,
            SpeechLevel.POLITE: 0.0,
            SpeechLevel.INFORMAL: 0.0,
            SpeechLevel.UNKNOWN: 0.0,
        }

        for result in results:
            counts[result.level] += result.confidence

        known = {k: v for k, v in counts.items() if k != SpeechLevel.UNKNOWN}

        if not any(known.values()):
            return SpeechLevel.UNKNOWN

        return max(known, key=known.get)

    def _detect_mixing(self, results: List[SentenceResult]) -> Tuple[bool, str]:
        if len(results) < 2:
            return False, ""

        levels = [r.level for r in results if r.level != SpeechLevel.UNKNOWN]

        if len(set(levels)) <= 1:
            return False, ""

        pairs = [
            f'"{r.sentence}" → {LEVEL_INFO[r.level]["ko"]}'
            for r in results
            if r.level != SpeechLevel.UNKNOWN
        ]

        return True, " / ".join(pairs[:5])

    # ------------------------------------------------------------
    # Context-aware appropriateness
    # ------------------------------------------------------------

    def check_appropriateness(
        self,
        text: str,
        expected_level: str,
        avatar_role: Optional[str] = None,
    ) -> AnalysisResult:
        """Method form expected by chat_service: pass text + expected level +
        avatar role, get back the full ``AnalysisResult`` (attribute access).

        Mirrors the legacy module-level ``check_appropriateness`` function but
        returns the rich object so callers can read ``.is_appropriate``,
        ``.score``, ``.word_errors``, etc. directly without dict lookups.
        """
        context = ConversationContext(
            avatar_role=avatar_role,
            situation=None,
            speech_act=None,
            closeness=3,
            age_gap=None,
        )
        result = self.check_contextual_appropriateness(text, context)
        # Honor caller-provided expected level (matches the old function's
        # behavior: e.g. "very_polite" → "formal" alias).
        result.expected_level = (expected_level or "").replace("very_polite", "formal") or result.expected_level
        return result

    def check_contextual_appropriateness(
        self,
        text: str,
        context: ConversationContext,
    ) -> AnalysisResult:
        result = self.analyze(text)
        profile = self._get_expected_profile(context)

        detected = result.overall_level

        directness_errors = self._check_directness(text, context)
        service_request_errors = self._check_service_request_style(
            text=text,
            expected_level=profile["preferred"].value,
            avatar_role=context.avatar_role,
        )

        result.directness_errors = directness_errors
        result.word_errors.extend(service_request_errors)
        result.word_errors.extend(directness_errors)

        result.expected_level = profile["preferred"].value
        result.acceptable_levels = [level.value for level in profile["acceptable"]]
        result.appropriateness_reason_ko = profile["reason"]

        if detected == SpeechLevel.UNKNOWN:
            result.is_appropriate = True
            result.feedback_ko = (
                "표현이 너무 짧거나 말투 판단에 필요한 단서가 부족합니다. "
                "문장 전체를 입력하면 더 정확하게 판단할 수 있습니다."
            )
            result.feedback_en = (
                "The sentence is too short or unclear to judge the speech level confidently."
            )
            result.score = max(40, result.score - 10)
            return result

        if detected in profile["acceptable"]:
            result.is_appropriate = True

            if detected in profile["too_stiff"]:
                result.is_appropriate = False
                result.feedback_ko = (
                    "문법적으로는 공손하지만, 이 관계에서는 다소 딱딱하게 들릴 수 있습니다. "
                    f"{profile['reason']}"
                )
                result.feedback_en = (
                    "The sentence is polite, but it may sound too stiff for this relationship."
                )
            else:
                result.feedback_ko = (
                    f"현재 말투는 전반적으로 적절합니다. {profile['reason']}"
                )
                result.feedback_en = (
                    "The current speech level is generally appropriate for this context."
                )

        else:
            result.is_appropriate = False

            if detected in profile["too_casual"]:
                result.feedback_ko = (
                    "현재 표현은 이 상황에 비해 다소 가볍거나 무례하게 들릴 수 있습니다. "
                    f"{profile['reason']}"
                )
                result.feedback_en = (
                    "The current expression may sound too casual for this context."
                )
            else:
                result.feedback_ko = (
                    f"현재 말투가 상황과 완전히 맞지 않을 수 있습니다. {profile['reason']}"
                )
                result.feedback_en = (
                    "The current speech level may not fully match the context."
                )

        if result.is_mixed:
            result.is_appropriate = False
            result.feedback_ko += f" 또한 한 메시지 안에서 말투가 섞여 있습니다: {result.mixed_detail}"
            result.feedback_en += " Also, multiple speech levels are mixed in one message."

        if directness_errors:
            result.is_appropriate = False
            result.feedback_ko += " 요청 표현이 다소 직접적이므로 더 완곡한 표현을 사용하는 것이 좋습니다."
            result.feedback_en += " The request sounds somewhat direct, so a softer expression is recommended."

        if result.missing_honorifics:
            result.is_appropriate = False
            result.feedback_ko += " 높임 대상에게는 높임 어휘나 '-시-' 표현을 사용하는 것이 더 자연스럽습니다."
            result.feedback_en += " Honorific vocabulary or honorific verb forms are recommended for this listener."

        result.suggested_correction = self.suggest_correction(text, context)
        result.native_alternative = self.suggest_native_alternative(text, context)

        result.score = self._score(
            sentences=result.sentences,
            is_mixed=result.is_mixed,
            word_errors=result.word_errors,
            missing_honorifics=result.missing_honorifics,
            directness_errors=result.directness_errors,
        )

        return result

    def _get_expected_profile(self, context: ConversationContext) -> dict:
        """
        Returns preferred, acceptable, too casual, and too stiff speech levels.
        This is intentionally rule-based and explainable.
        """

        role = (context.avatar_role or "").lower()
        relationship = (context.relationship or "").lower()
        situation = (context.situation or "").lower()
        speech_act = (context.speech_act or "").lower()

        closeness = context.closeness if context.closeness is not None else 3
        age_gap = context.age_gap if context.age_gap is not None else 0

        profile = {
            "preferred": SpeechLevel.POLITE,
            "acceptable": {SpeechLevel.POLITE},
            "too_casual": {SpeechLevel.INFORMAL},
            "too_stiff": set(),
            "reason": "기본적으로 해요체가 안전한 표현입니다.",
        }

        high_respect_roles = [
            "professor", "teacher", "boss", "doctor", "interviewer",
            "senior", "manager", "supervisor",
            "교수", "선생", "상사", "의사", "면접관", "선배",
        ]

        service_roles = [
            "staff", "employee", "clerk", "server", "cashier",
            "직원", "점원", "알바", "사장", "종업원",
        ]

        formal_situations = [
            "interview", "presentation", "business", "official", "meeting",
            "office_hour", "email", "consultation",
            "면접", "발표", "회의", "공식", "상담",
        ]

        sensitive_acts = [
            "request", "permission", "apology", "refusal", "complaint",
            "ask_extension", "favor",
            "요청", "허락", "사과", "거절", "불만",
        ]

        casual_relationships = [
            "friend", "close_friend", "classmate", "younger_sibling",
            "친구", "친한 친구", "동기", "후배",
        ]

        if any(keyword in role for keyword in high_respect_roles):
            if speech_act in sensitive_acts or any(s in situation for s in formal_situations):
                profile["preferred"] = SpeechLevel.FORMAL
            else:
                profile["preferred"] = SpeechLevel.POLITE

            profile["acceptable"] = {SpeechLevel.POLITE, SpeechLevel.FORMAL}
            profile["too_casual"] = {SpeechLevel.INFORMAL}
            profile["too_stiff"] = set()
            profile["reason"] = (
                "상대가 교수님, 선생님, 상사처럼 사회적 지위가 높은 관계이므로 "
                "해요체 이상이 필요합니다. 요청이나 사과 상황에서는 더 정중한 표현이 자연스럽습니다."
            )

        elif any(keyword in role for keyword in service_roles):
            profile["preferred"] = SpeechLevel.POLITE
            profile["acceptable"] = {SpeechLevel.POLITE, SpeechLevel.FORMAL}
            profile["too_casual"] = {SpeechLevel.INFORMAL}
            profile["too_stiff"] = set()
            profile["reason"] = (
                "처음 만난 직원이나 점원에게는 해요체가 가장 자연스럽습니다. "
                "반말은 무례하게 들릴 수 있습니다."
            )

        elif any(keyword in situation for keyword in formal_situations):
            profile["preferred"] = SpeechLevel.FORMAL
            profile["acceptable"] = {SpeechLevel.FORMAL, SpeechLevel.POLITE}
            profile["too_casual"] = {SpeechLevel.INFORMAL}
            profile["too_stiff"] = set()
            profile["reason"] = (
                "공식적인 상황에서는 합쇼체 또는 정중한 해요체가 적절합니다."
            )

        elif any(keyword in relationship for keyword in casual_relationships) or (
            closeness >= 4 and abs(age_gap) <= 3
        ):
            profile["preferred"] = SpeechLevel.INFORMAL
            profile["acceptable"] = {SpeechLevel.INFORMAL, SpeechLevel.POLITE}
            profile["too_casual"] = set()
            profile["too_stiff"] = {SpeechLevel.FORMAL}
            profile["reason"] = (
                "친한 관계에서는 반말이나 자연스러운 해요체가 가능하지만, "
                "지나치게 격식적인 합쇼체는 어색하게 들릴 수 있습니다."
            )

        elif age_gap >= 10 and closeness <= 2:
            profile["preferred"] = SpeechLevel.POLITE
            profile["acceptable"] = {SpeechLevel.POLITE, SpeechLevel.FORMAL}
            profile["too_casual"] = {SpeechLevel.INFORMAL}
            profile["too_stiff"] = set()
            profile["reason"] = (
                "나이 차이가 크고 친밀도가 낮으므로 반말은 부적절할 수 있습니다."
            )

        if context.is_public:
            profile["acceptable"].add(SpeechLevel.FORMAL)
            profile["too_casual"].add(SpeechLevel.INFORMAL)
            profile["reason"] += " 공개적인 상황이므로 평소보다 더 정중한 표현이 안전합니다."

        return profile

    # ------------------------------------------------------------
    # Error checks
    # ------------------------------------------------------------

    def _check_words(self, text: str) -> List[dict]:
        errors = []

        for word, info in WORD_FORMALITY_ERRORS.items():
            if word in text:
                errors.append({
                    "original": word.strip(),
                    "expected": info["expected"],
                    "type": info["type"].value,
                    "explanation": info["explanation"],
                    "severity": "warning" if info["level"] == "formal" else "error",
                })

        return errors

    def _check_honorifics(self, text: str) -> List[dict]:
        missing = []

        for wrong, correct in REQUIRES_HONORIFIC_VERBS.items():
            if wrong in text:
                missing.append({
                    "original": wrong,
                    "corrected": correct,
                    "type": ErrorType.HONORIFIC_MISSING.value,
                    "explanation": f"높임 대상에게는 '{wrong}'보다 '{correct}'가 더 자연스럽습니다.",
                    "severity": "error",
                })

        return missing

    def _check_directness(self, text: str, context: ConversationContext) -> List[dict]:
        role = (context.avatar_role or "").lower()
        situation = (context.situation or "").lower()
        speech_act = (context.speech_act or "").lower()

        needs_softness = (
            speech_act in {
                "request", "permission", "apology", "refusal", "complaint",
                "ask_extension", "favor", "요청", "허락", "사과", "거절", "불만",
            }
            or any(r in role for r in [
                "professor", "teacher", "boss", "doctor", "interviewer", "senior",
                "교수", "선생", "상사", "의사", "면접관", "선배",
            ])
            or any(s in situation for s in [
                "interview", "presentation", "business", "official", "meeting",
                "office_hour", "면접", "발표", "회의", "공식",
            ])
        )

        if not needs_softness:
            return []

        errors = []

        for rule in DIRECT_REQUEST_PATTERNS:
            match = rule["pattern"].search(text)
            if match:
                errors.append({
                    "original": match.group(0),
                    "expected": rule["softened"],
                    "type": ErrorType.DIRECTNESS.value,
                    "explanation": rule["explanation"],
                    "severity": "warning",
                })

        return errors

    def _check_service_request_style(
        self,
        text: str,
        expected_level: str,
        avatar_role: Optional[str] = None,
    ) -> List[dict]:
        role_text = avatar_role or ""

        service_or_formal = (
            expected_level in {"polite", "formal"}
            or any(keyword in role_text for keyword in [
                "직원", "점원", "사장", "교수", "선생", "의사", "손님",
                "staff", "employee", "clerk", "server", "cashier",
            ])
        )

        if not service_or_formal:
            return []

        errors = []

        for rule in SERVICE_REQUEST_PATTERNS:
            match = rule["pattern"].search(text)
            if not match:
                continue

            errors.append({
                "original": match.group(0),
                "expected": rule["expected"],
                "type": ErrorType.WORD_CHOICE.value,
                "explanation": rule["explanation"],
                "severity": "error",
            })

        return errors

    def _detect_dialect(self, text: str) -> List[str]:
        found = []

        for dialect, standard in DIALECT_SLANG.items():
            if dialect in text and standard is not None:
                found.append(f"'{dialect}' (표준어: '{standard}')")

        return found

    # ------------------------------------------------------------
    # Suggestions
    # ------------------------------------------------------------

    def suggest_correction(self, text: str, context: ConversationContext) -> str:
        corrected = text

        replacements = {
            "나는": "저는",
            "내가": "제가",
            "나를": "저를",
            "나한테": "저한테",
            "밥": "식사",
            "먹었어요": "드셨어요",
            "먹어요": "드세요",
            "자요": "주무세요",
            "잤어요": "주무셨어요",
            "있어요": "계세요",
            "있었어요": "계셨어요",
            "말해요": "말씀하세요",
            "물어봐요": "여쭤봐요",
            "줘요": "드려요",
            "해줘요": "해주실 수 있을까요",
            "알려줘요": "알려주실 수 있을까요",
            "내도 돼요": "제출해도 괜찮을까요",
            "가도 돼요": "가도 괜찮을까요",
            "써도 돼요": "사용해도 괜찮을까요",
            "해도 돼요": "해도 괜찮을까요",
        }

        for wrong, right in replacements.items():
            corrected = corrected.replace(wrong, right)

        return corrected

    def suggest_native_alternative(self, text: str, context: ConversationContext) -> str:
        role = (context.avatar_role or "").lower()
        situation = (context.situation or "").lower()
        speech_act = (context.speech_act or "").lower()
        goal = context.user_goal or ""

        is_professor = "professor" in role or "교수" in role
        is_interview = "interview" in situation or "면접" in situation
        is_store = any(x in role for x in ["staff", "employee", "clerk", "server", "cashier", "직원", "점원"])

        if is_professor and speech_act in {"permission", "request", "ask_extension", "허락", "요청"}:
            return "교수님, 혹시 과제 제출 기한을 조금 연장할 수 있을까요?"

        if is_professor:
            return "교수님, 혹시 시간 괜찮으실 때 확인해 주실 수 있을까요?"

        if is_interview:
            return "말씀해 주신 부분을 바탕으로 성실히 답변드리겠습니다."

        if is_store:
            return "저기요, 혹시 이것으로 주문해도 될까요?"

        if speech_act in {"apology", "사과"}:
            return "죄송합니다. 다음부터는 더 주의하겠습니다."

        if speech_act in {"refusal", "거절"}:
            return "죄송하지만, 이번에는 참여하기 어려울 것 같습니다."

        if goal:
            return f"상황에 맞게 더 자연스럽게 말하면: {self.suggest_correction(text, context)}"

        return self.suggest_correction(text, context)

    # ------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------

    def _score(
        self,
        sentences: List[SentenceResult],
        is_mixed: bool,
        word_errors: List[dict],
        missing_honorifics: List[dict],
        directness_errors: List[dict],
    ) -> int:
        score = 100

        if is_mixed:
            score -= 20

        for error in word_errors:
            severity = error.get("severity", "warning")
            if severity == "error":
                score -= 10
            else:
                score -= 6

        score -= len(missing_honorifics) * 12
        score -= len(directness_errors) * 8

        avg_confidence = (
            sum(sentence.confidence for sentence in sentences) / len(sentences)
            if sentences
            else 1
        )

        if avg_confidence < 0.5:
            score -= 10

        return max(0, min(100, score))

    def _empty(self, text: str) -> AnalysisResult:
        return AnalysisResult(
            text=text,
            overall_level=SpeechLevel.UNKNOWN,
            overall_level_ko="알 수 없음",
            overall_level_en="Unknown",
            confidence=0.0,
            score=50,
        )


# ============================================================
# Singleton analyzer
# ============================================================

analyzer = NativeSpeechAnalyzer()


# ============================================================
# Public API functions
# ============================================================

def analyze_speech_level(text: str) -> Dict[str, Any]:
    result = analyzer.analyze(text)

    return {
        "text": result.text,
        "speech_level": result.overall_level.value,
        "speech_level_ko": result.overall_level_ko,
        "speech_level_en": result.overall_level_en,
        "confidence": result.confidence,
        "score": result.score,
        "is_mixed": result.is_mixed,
        "mixed_detail": result.mixed_detail,
        "word_errors": result.word_errors,
        "dialect_found": result.dialect_found,
        "missing_honorifics": result.missing_honorifics,
        "sentence_breakdown": [
            {
                "sentence": s.sentence,
                "level": s.level.value,
                "confidence": s.confidence,
                "is_short": s.is_short,
                "is_dialect": s.is_dialect,
                "word_errors": s.word_errors,
            }
            for s in result.sentences
        ],
    }


def check_appropriateness(
    text: str,
    expected_level: str,
    avatar_role: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Backward-compatible function.
    This keeps your old interface working, but internally converts it
    into the new context-aware format.
    """

    context = ConversationContext(
        avatar_role=avatar_role,
        situation=None,
        speech_act=None,
        closeness=3,
        age_gap=None,
    )

    result = analyzer.check_contextual_appropriateness(text, context)

    # If caller explicitly provides expected_level, override display field.
    normalized_expected = expected_level.replace("very_polite", "formal")
    result.expected_level = normalized_expected

    return _result_to_dict(result)


def check_contextual_appropriateness(
    text: str,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Recommended function for Talkativ.

    Example:
        check_contextual_appropriateness(
            "교수님, 과제 좀 늦게 내도 돼요?",
            {
                "avatar_role": "professor",
                "situation": "office_hour",
                "speech_act": "permission",
                "age_gap": 25,
                "closeness": 1,
                "user_goal": "ask for assignment extension"
            }
        )
    """

    ctx = ConversationContext(
        avatar_role=context.get("avatar_role"),
        relationship=context.get("relationship"),
        situation=context.get("situation"),
        speech_act=context.get("speech_act"),
        age_gap=context.get("age_gap"),
        closeness=context.get("closeness"),
        is_public=context.get("is_public", False),
        user_goal=context.get("user_goal"),
    )

    result = analyzer.check_contextual_appropriateness(text, ctx)

    return _result_to_dict(result)


def suggest_correction(text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    context = context or {}

    ctx = ConversationContext(
        avatar_role=context.get("avatar_role"),
        relationship=context.get("relationship"),
        situation=context.get("situation"),
        speech_act=context.get("speech_act"),
        age_gap=context.get("age_gap"),
        closeness=context.get("closeness"),
        is_public=context.get("is_public", False),
        user_goal=context.get("user_goal"),
    )

    return {
        "original": text,
        "suggested": analyzer.suggest_correction(text, ctx),
        "native_alternative": analyzer.suggest_native_alternative(text, ctx),
    }


def get_speech_analyzer() -> NativeSpeechAnalyzer:
    return analyzer


# ============================================================
# Spelling detection
# ============================================================
#
# Lightweight heuristic typo dictionary for the most common Korean texting
# slips a learner makes. This is intentionally conservative: each entry is a
# clear misspelling, not a stylistic choice. Returning an empty list is the
# common (correct) case and the caller treats that as "no spelling issues".

_TYPO_HINTS: Dict[str, str] = {
    "되요": "돼요",          # 되-/돼- 혼동
    "안되요": "안 돼요",
    "않되요": "안 돼요",
    "않돼요": "안 돼요",
    "되써요": "돼써요",       # rare
    "되서": "돼서",
    "않좋아": "안 좋아",
    "않좋아요": "안 좋아요",
    "않좋": "안 좋",
    "예의가있": "예의가 있",  # 띄어쓰기
    "할께요": "할게요",
    "할께": "할게",
    "할꺼야": "할 거야",
    "할꺼에요": "할 거예요",
    "할꺼예요": "할 거예요",
    "그래요?": "그래요?",     # placeholder; safe no-op kept for shape
    "어떻해": "어떡해",
    "어떻게요": "어떡해요",
    "왠일": "웬일",
    "왠지": "왠지",           # this one IS correct, kept as no-op
    "맞춰": "맞춰",           # no-op
    "맞춰요": "맞춰요",       # no-op
    "않그래": "안 그래",
    "안되겠": "안 되겠",
    "할수있": "할 수 있",
    "할수없": "할 수 없",
    "감사하니다": "감사합니다",
    "죄송하니다": "죄송합니다",
    "그렇하니다": "그렇습니다",
    "안되여": "안 돼요",
    "맏아요": "맞아요",
    "괜잖아": "괜찮아",
    "괜잖아요": "괜찮아요",
    "괞찮": "괜찮",
}


def detect_spelling(text: str) -> List[Dict[str, str]]:
    """Return a list of likely spelling/typo hits in `text`.

    Each hit: { "original": "<typo>", "expected": "<fixed>", "type": "spelling" }

    Hits where `original == expected` (kept as no-ops in the dictionary above)
    are filtered out so callers only see real issues.
    """
    if not text:
        return []

    hits: List[Dict[str, str]] = []
    for typo, fixed in _TYPO_HINTS.items():
        if typo == fixed:
            continue
        if typo in text:
            hits.append({
                "original": typo,
                "expected": fixed,
                "type": "spelling",
                "explanation": f"'{typo}'은 '{fixed}'의 흔한 오타/오기입니다.",
                "severity": "warning",
            })
    return hits


# ============================================================
# Intent inference
# ============================================================
#
# Heuristic mapping from sentence-final cues + lexical hints to a coarse
# speech act label. Used by speech_analysis_service to enrich the rule-based
# analysis without an LLM round-trip.

_INTENT_RULES: List[Tuple[str, re.Pattern]] = [
    ("apology",    re.compile(r"(죄송|미안|사과|용서)")),
    ("greeting",   re.compile(r"(안녕|반갑|처음|뵙겠)")),
    ("permission", re.compile(r"(돼요\?|돼\?|해도|봐도|가도|괜찮을까요)")),
    ("request",    re.compile(r"(주세요|해주세요|부탁|좀\s*\w*\s*해|좀\s*\w*\s*줘)")),
    ("refusal",    re.compile(r"(못\s*해|못\s*가|어려울|힘들|안\s*돼)")),
    ("question",   re.compile(r"\?$|뭐야|뭔가요|언제|어디|왜|누구|어떻게")),
    ("agreement",  re.compile(r"(그래요|네\b|예\b|맞아요|맞습니다|좋아요|좋습니다)")),
    ("statement",  re.compile(r".")),  # catch-all fallback
]


def infer_intent(
    text: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Optional[str]:
    """Infer a coarse speech-act label from the message text alone.

    Rule order matters: more-specific patterns come first. `conversation_history`
    is accepted for future use (e.g. distinguishing a fresh request from a
    follow-up answer); current heuristic ignores it.
    """
    if not text or not text.strip():
        return None

    stripped = text.strip()
    for label, pattern in _INTENT_RULES:
        if pattern.search(stripped):
            return label
    return None


def _result_to_dict(result: AnalysisResult) -> Dict[str, Any]:
    return {
        "text": result.text,
        "normalized": normalize_text(result.text),
        "speech_level": result.overall_level.value,
        "speech_level_ko": result.overall_level_ko,
        "speech_level_en": result.overall_level_en,
        "confidence": result.confidence,
        "expected_level": result.expected_level,
        "acceptable_levels": result.acceptable_levels,
        "is_appropriate": result.is_appropriate,
        "is_mixed": result.is_mixed,
        "mixed_detail": result.mixed_detail,
        "score": result.score,
        "appropriateness_reason_ko": result.appropriateness_reason_ko,
        "feedback_ko": result.feedback_ko,
        "feedback_en": result.feedback_en,
        "suggested_correction": result.suggested_correction,
        "native_alternative": result.native_alternative,
        "word_errors": result.word_errors,
        "directness_errors": result.directness_errors,
        "missing_honorifics": result.missing_honorifics,
        "dialect_found": result.dialect_found,
        "sentence_breakdown": [
            {
                "sentence": s.sentence,
                "level": s.level.value,
                "level_ko": LEVEL_INFO[s.level]["ko"],
                "confidence": s.confidence,
                "is_short": s.is_short,
                "is_dialect": s.is_dialect,
                "word_errors": s.word_errors,
            }
            for s in result.sentences
        ],
    }


# ============================================================
# Local test examples
# ============================================================

if __name__ == "__main__":
    examples = [
        {
            "text": "교수님, 과제 좀 늦게 내도 돼요?",
            "context": {
                "avatar_role": "professor",
                "situation": "office_hour",
                "speech_act": "permission",
                "age_gap": 25,
                "closeness": 1,
                "user_goal": "ask for assignment extension",
            },
        },
        {
            "text": "야 밥 먹었어?",
            "context": {
                "avatar_role": "friend",
                "relationship": "close_friend",
                "situation": "casual_chat",
                "speech_act": "question",
                "age_gap": 0,
                "closeness": 5,
            },
        },
        {
            "text": "선생님 밥 먹었어요?",
            "context": {
                "avatar_role": "teacher",
                "situation": "school",
                "speech_act": "question",
                "age_gap": 20,
                "closeness": 1,
            },
        },
        {
            "text": "이거 줘.",
            "context": {
                "avatar_role": "staff",
                "situation": "restaurant",
                "speech_act": "request",
                "age_gap": 0,
                "closeness": 1,
            },
        },
        {
            "text": "네 알겠습니다. 그럼 내일 봐.",
            "context": {
                "avatar_role": "professor",
                "situation": "office_hour",
                "speech_act": "response",
                "age_gap": 25,
                "closeness": 1,
            },
        },
    ]

    for item in examples:
        print("=" * 80)
        print("INPUT:", item["text"])
        output = check_contextual_appropriateness(item["text"], item["context"])
        print("LEVEL:", output["speech_level_ko"])
        print("APPROPRIATE:", output["is_appropriate"])
        print("SCORE:", output["score"])
        print("FEEDBACK:", output["feedback_ko"])
        print("SUGGESTED:", output["suggested_correction"])
        print("NATIVE:", output["native_alternative"])