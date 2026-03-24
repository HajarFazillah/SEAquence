"""
Korean Speech Level Analyzer - Native-Grade
Analyzes Korean speech for: 합쇼체 / 해요체 / 반말

Improvements over basic version:
- Sentence-by-sentence analysis (catches mixing within a message)
- Short reply dictionary (네, 응, ㅇㅇ etc.)
- Dialect and slang detection
- Honorific particle -시- detection (not just endings)
- Word-level formality errors (나→저, 밥→식사 etc.)
- Penalty scoring for mixing levels
- Detailed per-sentence breakdown for UI
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class SpeechLevel(Enum):
    FORMAL   = "formal"
    POLITE   = "polite"
    INFORMAL = "informal"
    UNKNOWN  = "unknown"


class ErrorType(Enum):
    WRONG_LEVEL        = "wrong_level"
    MIXED_LEVEL        = "mixed_level"
    HONORIFIC_MISSING  = "honorific_missing"
    WORD_CHOICE        = "word_choice"
    PRONOUN_ERROR      = "pronoun_error"
    DIALECT            = "dialect"


SHORT_INFORMAL = {
    "응","어","어어","응응","어응","아",
    "ㅇ","ㅇㅇ","ㅇㅇㅇ","ㅇㅋ","ㄴ","ㄴㄴ","ㄱㄱ",
    "ㅋ","ㅋㅋ","ㅋㅋㅋ","ㅎ","ㅎㅎ","ㅎㅎㅎ",
    "ㅠ","ㅠㅠ","ㅜ","ㅜㅜ","ㅠㅠㅠ","ㄷㄷ","ㄷㄷㄷ","ㄹㅇ","ㅂㅂ",
    "야","야야","아니","맞아","좋아","싫어",
    "몰라","알아","그래","안돼","됐어",
    "와","우와","헐","대박","진짜","ㄹㅇ",
}

SHORT_POLITE = {
    "네","예","아네","아예","네네","예예",
    "맞아요","그래요","좋아요","알겠어요",
    "감사해요","괜찮아요","천만에요",
}

SHORT_FORMAL = {
    "네, 알겠습니다","그렇습니다","알겠습니다",
    "감사합니다","죄송합니다","실례합니다","아닙니다",
}

AMBIGUOUS_SHORT = {"네","예","아"}

DIALECT_SLANG = {
    "머해":"뭐 해","머라":"뭐라","와캐":"왜 그래","왜캐":"왜 그래",
    "이거머":"이게 뭐야","마":"말",
    "ㅇㅈ":"인정","ㅂㅂ":"바이바이","ㅈㅅ":"죄송","ㄱㅅ":"감사",
    "ㅊㅋ":"축하","ㄷㄷ":"덜덜","ㅇㅋ":"오케이",
    "왜이래":"왜 이러는 거야","왜그래":"왜 그러는 거야",
    "어쩌라고":"어떻게 하라는 거야",
}

WORD_FORMALITY_ERRORS = {
    "나 ":     {"expected":"저 ",    "level":"polite",  "type":ErrorType.PRONOUN_ERROR, "explanation":"윗사람에게는 '나' 대신 '저'를 사용하세요"},
    "나는":    {"expected":"저는",   "level":"polite",  "type":ErrorType.PRONOUN_ERROR, "explanation":"'나는' 대신 '저는'을 사용하세요"},
    "나가":    {"expected":"제가",   "level":"polite",  "type":ErrorType.PRONOUN_ERROR, "explanation":"'나가' 대신 '제가'를 사용하세요"},
    "내가":    {"expected":"제가",   "level":"polite",  "type":ErrorType.PRONOUN_ERROR, "explanation":"'내가' 대신 '제가'를 사용하세요"},
    "나를":    {"expected":"저를",   "level":"polite",  "type":ErrorType.PRONOUN_ERROR, "explanation":"'나를' 대신 '저를'을 사용하세요"},
    "나한테":  {"expected":"저한테", "level":"polite",  "type":ErrorType.PRONOUN_ERROR, "explanation":"'나한테' 대신 '저한테'를 사용하세요"},
    "우리":    {"expected":"저희",   "level":"formal",  "type":ErrorType.WORD_CHOICE,   "explanation":"격식 상황에서는 '우리' 대신 '저희'를 사용하세요"},
    "밥 ":     {"expected":"식사 ",  "level":"formal",  "type":ErrorType.WORD_CHOICE,   "explanation":"'밥' 대신 '식사'를 사용하세요"},
    "밥은":    {"expected":"식사는", "level":"formal",  "type":ErrorType.WORD_CHOICE,   "explanation":"'밥' 대신 '식사'를 사용하세요"},
    "밥을":    {"expected":"식사를", "level":"formal",  "type":ErrorType.WORD_CHOICE,   "explanation":"'밥' 대신 '식사'를 사용하세요"},
    "이름":    {"expected":"성함",   "level":"formal",  "type":ErrorType.WORD_CHOICE,   "explanation":"상대방 이름은 '성함'이라고 하세요"},
    "나이":    {"expected":"연세",   "level":"formal",  "type":ErrorType.WORD_CHOICE,   "explanation":"어른의 나이는 '연세'라고 하세요"},
    "아빠":    {"expected":"아버지", "level":"polite",  "type":ErrorType.WORD_CHOICE,   "explanation":"격식 상황에서는 '아버지'를 사용하세요"},
    "엄마":    {"expected":"어머니", "level":"polite",  "type":ErrorType.WORD_CHOICE,   "explanation":"격식 상황에서는 '어머니'를 사용하세요"},
}

REQUIRES_HONORIFIC_VERBS = {
    "먹어요":"드세요","먹었어요":"드셨어요",
    "자요":"주무세요","잤어요":"주무셨어요",
    "있어요":"계세요","있었어요":"계셨어요",
    "말해요":"말씀하세요","물어봐요":"여쭤봐요",
    "줘요":"드려요","봐요":"뵈어요",
}

HONORIFIC_SI_PATTERNS = [
    r'[가-힣]+시[고는도며서]',r'[가-힣]+세요',r'[가-힣]+셨',
    r'[가-힣]+시겠',r'[가-힣]+으시',r'계세요',r'계십니',r'드세요',r'드셨',
]

FORMAL_PATTERNS = [
    r'습니다[.?!]?$',r'습니까[?]?$',r'십시오[.!]?$',r'십니까[?]?$',
    r'옵니다[.?!]?$',r'옵니까[?]?$',r'하십시오[.!]?$',
    r'드립니다[.?!]?$',r'드릴까요[?]?$',r'드렸습니다[.?!]?$',r'드리겠습니다[.?!]?$',
    r'겠습니다[.?!]?$',r'겠습니까[?]?$',
    r'었습니다[.?!]?$',r'았습니다[.?!]?$',r'였습니다[.?!]?$',
    r'계십니까[?]?$',r'계십니다[.?!]?$',
    r'입니다[.?!]?$',r'입니까[?]?$',r'였습니까[?]?$',
    r'아닙니다[.?!]?$',r'아닙니까[?]?$',
    r'주십시오[.!]?$',r'해주십시오[.!]?$',r'알려주십시오[.!]?$',
    r'부탁드립니다[.?!]?$',r'말씀해주십시오[.!]?$',r'바랍니다[.?!]?$',
    r'시겠습니까[?]?$',r'시겠습니다[.?!]?$',r'셨습니다[.?!]?$',r'셨습니까[?]?$',
    r'합니다[.?!]?$',r'됩니다[.?!]?$',r'됩니까[?]?$',
    r'있습니다[.?!]?$',r'없습니다[.?!]?$',r'있습니까[?]?$',r'없습니까[?]?$',
]

POLITE_PATTERNS = [
    r'[아어여이]요[.?!]?$',r'해요[.?!]?$',r'세요[.?!]?$',r'예요[.?!]?$',r'이에요[.?!]?$',
    r'네요[.?!]?$',r'죠[.?!]?$',r'나요[.?!]?$',r'는데요[.?!]?$',r'ㄴ데요[.?!]?$',
    r'거든요[.?!]?$',r'잖아요[.?!]?$',r'군요[.?!]?$',r'구나요[.?!]?$',
    r'더라고요[.?!]?$',r'더라구요[.?!]?$',
    r'할게요[.?!]?$',r'갈게요[.?!]?$',r'볼게요[.?!]?$',r'줄게요[.?!]?$',
    r'올게요[.?!]?$',r'먹을게요[.?!]?$',r'말할게요[.?!]?$',
    r'할까요[?]?$',r'갈까요[?]?$',r'볼까요[?]?$',r'먹을까요[?]?$',
    r'드릴까요[?]?$',r'일까요[?]?$',r'될까요[?]?$',
    r'싶어요[.?!]?$',r'같아요[.?!]?$',r'있어요[.?!]?$',r'없어요[.?!]?$',
    r'좋아요[.?!]?$',r'싫어요[.?!]?$',r'됐어요[.?!]?$',r'됐죠[.?!]?$',
    r'맞아요[.?!]?$',r'괜찮아요[.?!]?$',r'어때요[?]?$',r'어떠세요[?]?$',
    r'했어요[.?!]?$',r'갔어요[.?!]?$',r'왔어요[.?!]?$',r'봤어요[.?!]?$',
    r'먹었어요[.?!]?$',r'마셨어요[.?!]?$',r'받았어요[.?!]?$',r'끝났어요[.?!]?$',
    r'알았어요[.?!]?$',r'몰랐어요[.?!]?$',
    r'겠어요[.?!]?$',r'겠죠[.?!]?$',
    r'주세요[.!]?$',r'해주세요[.!]?$',r'알려주세요[.!]?$',
    r'말씀해주세요[.!]?$',r'부탁해요[.?!]?$',
    r'것 같아요[.?!]?$',r'것 같죠[.?!]?$',r'인 것 같아요[.?!]?$',
    r'시어요[.?!]?$',r'셔요[.?!]?$',r'싶죠[.?!]?$',
]

INFORMAL_PATTERNS = [
    r'[아어][\s.?!]*$',r'야[.?!]?$',r'지[.?!]?$',r'냐[?]?$',r'니[?]?$',
    r'네[.?!]?$',r'군[.?!]?$',r'구나[.?!]?$',
    r'거야[.?!]?$',r'거지[.?!]?$',r'잖아[.?!]?$',r'는데[.?!]?$',r'ㄴ데[.?!]?$',
    r'더라[.?!]?$',r'거든[.?!]?$',r'더라고[.?!]?$',r'더라구[.?!]?$',r'잖니[?]?$',
    r'할게[.?!]?$',r'갈게[.?!]?$',r'볼게[.?!]?$',r'줄게[.?!]?$',
    r'올게[.?!]?$',r'먹을게[.?!]?$',r'말할게[.?!]?$',
    r'가자[.?!]?$',r'하자[.?!]?$',r'먹자[.?!]?$',r'보자[.?!]?$',
    r'놀자[.?!]?$',r'자자[.?!]?$',r'끝내자[.?!]?$',
    r'해봐[.?!]?$',r'해봐라[.?!]?$',r'해라[.!]?$',r'가라[.!]?$',
    r'봐라[.!]?$',r'먹어라[.!]?$',r'와라[.!]?$',
    r'뭐야[.?!]?$',r'뭐해[.?!]?$',r'뭐냐[?]?$',r'어디야[?]?$',
    r'어디가[?]?$',r'왜야[?]?$',r'언제야[?]?$',r'누구야[?]?$',
    r'좋아[.?!]?$',r'싫어[.?!]?$',r'있어[.?!]?$',r'없어[.?!]?$',
    r'맞아[.?!]?$',r'아니야[.?!]?$',r'괜찮아[.?!]?$',r'어때[?]?$',
    r'몰라[.?!]?$',r'알아[.?!]?$',
    r'됐어[.?!]?$',r'했어[.?!]?$',r'갔어[.?!]?$',r'왔어[.?!]?$',
    r'봤어[.?!]?$',r'먹었어[.?!]?$',r'마셨어[.?!]?$',r'받았어[.?!]?$',
    r'끝났어[.?!]?$',r'알았어[.?!]?$',r'몰랐어[.?!]?$',
    r'겠어[.?!]?$',r'할 거야[.?!]?$',r'갈 거야[.?!]?$',
    r'할거야[.?!]?$',r'갈거야[.?!]?$',
    r'이야[.?!]?$',r'인데[.?!]?$',r'싶어[.?!]?$',
    r'할까[?]?$',r'갈까[?]?$',r'볼까[?]?$',r'먹을까[?]?$',
    r'같아[.?!]?$',r'것 같아[.?!]?$',
    r'ㅋ+$',r'ㅎ+$',r'ㄷㄷ$',r'ㅠ+$',r'ㅜ+$',
    r'마[.?!]?$',r'가[.?!]?$',r'데이[.?!]?$',
]

LEVEL_INFO = {
    SpeechLevel.FORMAL:   {"ko":"합쇼체","en":"Formal"},
    SpeechLevel.POLITE:   {"ko":"해요체","en":"Polite"},
    SpeechLevel.INFORMAL: {"ko":"반말",  "en":"Informal"},
    SpeechLevel.UNKNOWN:  {"ko":"알 수 없음","en":"Unknown"},
}


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
    is_appropriate: Optional[bool] = None
    expected_level: Optional[str] = None
    feedback_ko: Optional[str] = None
    feedback_en: Optional[str] = None
    score: int = 100


def split_sentences(text: str) -> List[str]:
    parts = re.split(r'(?<=[.?!])\s+|(?<=[.?!])$', text.strip())
    result = []
    for part in parts:
        for line in part.split('\n'):
            line = line.strip()
            if not line:
                continue
            if len(line) > 40 and ',' in line:
                result.extend([p.strip() for p in line.split(',') if p.strip()])
            else:
                result.append(line)
    return result


class NativeSpeechAnalyzer:
    def __init__(self):
        self._f = [re.compile(p) for p in FORMAL_PATTERNS]
        self._p = [re.compile(p) for p in POLITE_PATTERNS]
        self._i = [re.compile(p) for p in INFORMAL_PATTERNS]

    def analyze(self, text: str) -> AnalysisResult:
        sentences = split_sentences(text)
        if not sentences:
            return self._empty(text)

        sent_results = [self._analyze_sentence(s) for s in sentences]
        overall = self._aggregate(sent_results)
        is_mixed, mixed_detail = self._detect_mixing(sent_results)
        word_errors = self._check_words(text)
        dialect_found = self._detect_dialect(text)
        missing_honorifics = self._check_honorifics(text)
        score = self._score(sent_results, is_mixed, word_errors, missing_honorifics)

        info = LEVEL_INFO[overall]
        return AnalysisResult(
            text=text,
            overall_level=overall,
            overall_level_ko=info["ko"],
            overall_level_en=info["en"],
            confidence=round(sum(r.confidence for r in sent_results) / len(sent_results), 2),
            sentences=sent_results,
            is_mixed=is_mixed,
            mixed_detail=mixed_detail,
            word_errors=word_errors,
            dialect_found=dialect_found,
            missing_honorifics=missing_honorifics,
            score=score,
        )

    def check_appropriateness(self, text: str, expected_level: str, avatar_role: str = None) -> AnalysisResult:
        result = self.analyze(text)
        order = {"informal":0,"polite":1,"formal":2,"unknown":1}
        detected = result.overall_level.value
        exp = expected_level.replace("very_polite","formal")

        if detected == "unknown":
            result.is_appropriate = True
        else:
            result.is_appropriate = order.get(detected,1) >= order.get(exp,1)

        result.expected_level = exp

        if not result.is_appropriate:
            role_ko = {"professor":"교수님","boss":"상사","senior":"선배",
                       "teacher":"선생님","doctor":"의사 선생님"}.get(avatar_role or "", "상대방")
            try:
                exp_lv = SpeechLevel(exp)
            except ValueError:
                exp_lv = SpeechLevel.POLITE
            level_name = LEVEL_INFO[exp_lv]["ko"]
            detected_name = LEVEL_INFO[result.overall_level]["ko"]
            result.feedback_ko = (
                f"{role_ko}에게는 {level_name}를 사용해야 합니다. "
                f"현재 {detected_name}를 사용하고 있습니다."
            )
            result.feedback_en = (
                f"Please use {exp} speech with {avatar_role or 'this person'}. "
                f"Currently using {detected}."
            )

        if result.is_mixed:
            msg = f" 또한 한 메시지 안에서 말투가 섞여 있습니다: {result.mixed_detail}"
            result.feedback_ko = (result.feedback_ko or "") + msg

        return result

    def _analyze_sentence(self, s: str) -> SentenceResult:
        sl = s.lower()

        if sl in SHORT_INFORMAL:
            return SentenceResult(s, SpeechLevel.INFORMAL, 0.95, is_short=True)
        if sl in SHORT_POLITE:
            return SentenceResult(s, SpeechLevel.POLITE, 0.95, is_short=True)
        if sl in SHORT_FORMAL:
            return SentenceResult(s, SpeechLevel.FORMAL, 0.95, is_short=True)
        if sl in AMBIGUOUS_SHORT:
            return SentenceResult(s, SpeechLevel.UNKNOWN, 0.3, is_short=True)

        is_dialect = any(d in s for d in DIALECT_SLANG if d != "저기요")

        fm = sum(1 for p in self._f if p.search(s))
        pm = sum(1 for p in self._p if p.search(s))
        im = sum(1 for p in self._i if p.search(s))

        fs, ps, is_ = fm*3, pm*2, im*1
        total = fs + ps + is_

        if total == 0:
            level, pat = self._guess(s)
            conf = 0.4
        elif fs >= ps and fs >= is_:
            level, pat = SpeechLevel.FORMAL, "formal"
            conf = min(0.98, 0.6 + fs/(total+1)*0.4)
        elif ps >= is_:
            level, pat = SpeechLevel.POLITE, "polite"
            conf = min(0.95, 0.5 + ps/(total+1)*0.4)
        else:
            level, pat = SpeechLevel.INFORMAL, "informal"
            conf = min(0.90, 0.4 + is_/(total+1)*0.4)

        word_errors = self._check_words(s)
        return SentenceResult(s, level, conf, pat, is_dialect=is_dialect, word_errors=word_errors)

    def _guess(self, text: str) -> Tuple[SpeechLevel, Optional[str]]:
        t = text.rstrip('?.! ')
        if t.endswith(('습니다','습니까','십시오','옵니다','입니다')):
            return SpeechLevel.FORMAL, "guess"
        if t.endswith(('요','세요','해요','죠','네요')):
            return SpeechLevel.POLITE, "guess"
        if t.endswith(('어','아','야','지','냐','니','네','군','구나')):
            return SpeechLevel.INFORMAL, "guess"
        return SpeechLevel.UNKNOWN, None

    def _aggregate(self, results: List[SentenceResult]) -> SpeechLevel:
        counts = {SpeechLevel.FORMAL:0.0, SpeechLevel.POLITE:0.0,
                  SpeechLevel.INFORMAL:0.0, SpeechLevel.UNKNOWN:0.0}
        for r in results:
            counts[r.level] += r.confidence
        known = {k:v for k,v in counts.items() if k != SpeechLevel.UNKNOWN}
        if not any(known.values()):
            return SpeechLevel.UNKNOWN
        return max(known, key=known.get)

    def _detect_mixing(self, results: List[SentenceResult]) -> Tuple[bool, str]:
        if len(results) < 2:
            return False, ""
        levels = [r.level for r in results if r.level != SpeechLevel.UNKNOWN]
        if len(set(levels)) <= 1:
            return False, ""
        pairs = [f'"{r.sentence}" → {LEVEL_INFO[r.level]["ko"]}'
                 for r in results if r.level != SpeechLevel.UNKNOWN]
        return True, " / ".join(pairs[:3])

    def _check_words(self, text: str) -> List[dict]:
        errors = []
        for word, info in WORD_FORMALITY_ERRORS.items():
            if word in text:
                errors.append({
                    "original":    word.strip(),
                    "expected":    info["expected"],
                    "type":        info["type"].value,
                    "explanation": info["explanation"],
                    "severity":    "warning" if info["level"] == "formal" else "error",
                })
        return errors

    def _check_honorifics(self, text: str) -> List[dict]:
        missing = []
        for wrong, correct in REQUIRES_HONORIFIC_VERBS.items():
            if wrong in text:
                missing.append({
                    "original":    wrong,
                    "corrected":   correct,
                    "explanation": f"'{wrong}' 대신 '{correct}'를 사용하세요 (높임말)",
                    "severity":    "error",
                })
        return missing

    def _detect_dialect(self, text: str) -> List[str]:
        return [
            f"'{d}' (표준어: '{s}')"
            for d, s in DIALECT_SLANG.items()
            if d in text and s is not None
        ]

    def _score(self, sentences, is_mixed, word_errors, missing_honorifics) -> int:
        score = 100
        if is_mixed:
            score -= 20
        score -= len(word_errors) * 8
        score -= len(missing_honorifics) * 12
        avg_conf = sum(r.confidence for r in sentences) / len(sentences) if sentences else 1
        if avg_conf < 0.5:
            score -= 10
        return max(0, score)

    def _empty(self, text: str) -> AnalysisResult:
        return AnalysisResult(text=text, overall_level=SpeechLevel.UNKNOWN,
                              overall_level_ko="알 수 없음", overall_level_en="Unknown",
                              confidence=0.0, score=50)


analyzer = NativeSpeechAnalyzer()


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
            {"sentence": s.sentence, "level": s.level.value,
             "confidence": s.confidence, "is_short": s.is_short,
             "is_dialect": s.is_dialect}
            for s in result.sentences
        ],
    }


def check_appropriateness(text: str, expected_level: str, avatar_role: str = None) -> Dict[str, Any]:
    result = analyzer.check_appropriateness(text, expected_level, avatar_role)
    return {
        "text": result.text,
        "speech_level": result.overall_level.value,
        "speech_level_ko": result.overall_level_ko,
        "expected_level": result.expected_level,
        "is_appropriate": result.is_appropriate,
        "is_mixed": result.is_mixed,
        "score": result.score,
        "feedback_ko": result.feedback_ko,
        "feedback_en": result.feedback_en,
        "word_errors": result.word_errors,
        "missing_honorifics": result.missing_honorifics,
        "dialect_found": result.dialect_found,
        "sentence_breakdown": [
            {"sentence": s.sentence, "level": s.level.value, "confidence": s.confidence}
            for s in result.sentences
        ],
    }


def get_speech_analyzer():
    return analyzer
