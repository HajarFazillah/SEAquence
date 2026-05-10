"""
Sophisticated Korean Speech Level Analyzer
Advanced NLP-based analysis of Korean honorific system (경어법)

Features:
1. 7 Korean Speech Levels (격식/비격식)
2. Morphological Analysis with KoNLPy (형태소 분석)
3. Honorific System Analysis (경어법 분석)
   - Subject Honorification (주체 높임법)
   - Object Honorification (객체 높임법)  
   - Addressee Honorification (상대 높임법)
4. Pragmatic Markers (화용적 표지)
5. Consistency Analysis (일관성 분석)
6. Context-Aware Detection (문맥 인식)

KoNLPy Integration:
- Uses Okt (Open Korean Text) for morphological analysis
- Extracts: 어미 (endings), 조사 (particles), 동사 (verbs)
- Falls back to regex-based analysis if KoNLPy unavailable
"""

import re
from typing import Dict, List, Any, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from collections import Counter
import logging

logger = logging.getLogger(__name__)


# ===========================================
# KONLPY WRAPPER
# ===========================================

class KoNLPyAnalyzer:
    """
    Wrapper for KoNLPy morphological analyzers.
    Provides graceful fallback when KoNLPy is not available.
    """
    
    def __init__(self):
        self.analyzer = None
        self.analyzer_name = None
        self._load_analyzer()
    
    def _load_analyzer(self):
        """Try to load KoNLPy analyzer (Okt preferred, then Komoran, then Hannanum)."""
        
        # Try Okt first (best for colloquial Korean)
        try:
            from konlpy.tag import Okt
            self.analyzer = Okt()
            self.analyzer_name = "Okt"
            logger.info("KoNLPy Okt loaded successfully")
            return
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Okt load failed: {e}")
        
        # Try Komoran (good accuracy)
        try:
            from konlpy.tag import Komoran
            self.analyzer = Komoran()
            self.analyzer_name = "Komoran"
            logger.info("KoNLPy Komoran loaded successfully")
            return
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Komoran load failed: {e}")
        
        # Try Hannanum (lightweight)
        try:
            from konlpy.tag import Hannanum
            self.analyzer = Hannanum()
            self.analyzer_name = "Hannanum"
            logger.info("KoNLPy Hannanum loaded successfully")
            return
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Hannanum load failed: {e}")
        
        logger.warning("KoNLPy not available - using regex-based analysis only")
    
    @property
    def is_available(self) -> bool:
        return self.analyzer is not None
    
    def pos(self, text: str) -> List[Tuple[str, str]]:
        """
        Get POS tags for text.
        Returns list of (morpheme, tag) tuples.
        """
        if not self.analyzer:
            return []
        
        try:
            return self.analyzer.pos(text)
        except Exception as e:
            logger.warning(f"POS tagging failed: {e}")
            return []
    
    def morphs(self, text: str) -> List[str]:
        """Get morphemes only."""
        if not self.analyzer:
            return []
        
        try:
            return self.analyzer.morphs(text)
        except Exception as e:
            logger.warning(f"Morpheme extraction failed: {e}")
            return []
    
    def nouns(self, text: str) -> List[str]:
        """Extract nouns."""
        if not self.analyzer:
            return []
        
        try:
            return self.analyzer.nouns(text)
        except Exception as e:
            return []


# Global KoNLPy instance
konlpy_analyzer = KoNLPyAnalyzer()


# ===========================================
# POS TAG MAPPINGS
# ===========================================

class POSCategory(str, Enum):
    """Simplified POS categories for analysis."""
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ENDING = "ending"           # 어미
    PARTICLE = "particle"       # 조사
    ADVERB = "adverb"
    INTERJECTION = "interjection"
    SUFFIX = "suffix"
    OTHER = "other"


# Mapping from KoNLPy tags to our categories
# Different analyzers use different tag sets
POS_TAG_MAP = {
    # Okt tags
    "Noun": POSCategory.NOUN,
    "Verb": POSCategory.VERB,
    "Adjective": POSCategory.ADJECTIVE,
    "Adverb": POSCategory.ADVERB,
    "Josa": POSCategory.PARTICLE,        # 조사
    "Eomi": POSCategory.ENDING,          # 어미
    "PreEomi": POSCategory.ENDING,       # 선어말어미
    "Suffix": POSCategory.SUFFIX,
    "Exclamation": POSCategory.INTERJECTION,
    
    # Komoran tags
    "NNG": POSCategory.NOUN,     # 일반 명사
    "NNP": POSCategory.NOUN,     # 고유 명사
    "VV": POSCategory.VERB,      # 동사
    "VA": POSCategory.ADJECTIVE, # 형용사
    "VX": POSCategory.VERB,      # 보조 동사
    "JKS": POSCategory.PARTICLE, # 주격 조사
    "JKO": POSCategory.PARTICLE, # 목적격 조사
    "JKB": POSCategory.PARTICLE, # 부사격 조사
    "JX": POSCategory.PARTICLE,  # 보조사
    "EC": POSCategory.ENDING,    # 연결 어미
    "EF": POSCategory.ENDING,    # 종결 어미
    "EP": POSCategory.ENDING,    # 선어말 어미 (includes -시-)
    "ETM": POSCategory.ENDING,   # 관형형 전성 어미
    "MAG": POSCategory.ADVERB,   # 일반 부사
    "IC": POSCategory.INTERJECTION,
    
    # Hannanum tags
    "NC": POSCategory.NOUN,
    "NQ": POSCategory.NOUN,
    "PV": POSCategory.VERB,
    "PA": POSCategory.ADJECTIVE,
    "JC": POSCategory.PARTICLE,
    "JX": POSCategory.PARTICLE,
    "E": POSCategory.ENDING,
    "MA": POSCategory.ADVERB,
}


def get_pos_category(tag: str) -> POSCategory:
    """Convert KoNLPy tag to our category."""
    return POS_TAG_MAP.get(tag, POSCategory.OTHER)


# ===========================================
# KOREAN SPEECH LEVEL SYSTEM (7 Levels)
# ===========================================

class SpeechLevel(IntEnum):
    """
    Korean has 7 traditional speech levels (상대 높임법).
    Modern usage typically uses 4-5 of these.
    """
    # 격식체 (Formal)
    HASOSEO = 7      # 하소서체 - Highest, archaic (하나이다, 하소서)
    HAPSYO = 6       # 합쇼체 - Very formal (습니다, 십시오)
    HAO = 5          # 하오체 - Formal, older generation (하오, 구려)
    HAGE = 4         # 하게체 - Formal, to younger (하게, 하네)
    
    # 비격식체 (Informal)  
    HAERA = 3        # 해라체 - Plain/written (한다, 하느냐)
    HAEYO = 2        # 해요체 - Polite informal (해요, 하세요)
    HAE = 1          # 해체 - Casual (해, 하지)


class HonorificType(str, Enum):
    """Types of Korean honorification"""
    SUBJECT = "subject"      # 주체 높임법 (-시-)
    OBJECT = "object"        # 객체 높임법 (드리다, 뵙다)
    ADDRESSEE = "addressee"  # 상대 높임법 (sentence endings)


class PragmaticFunction(str, Enum):
    """Pragmatic functions in speech"""
    HEDGING = "hedging"              # 완곡 표현
    SOFTENING = "softening"          # 완화 표현
    INTENSIFYING = "intensifying"    # 강조 표현
    INDIRECT = "indirect"            # 간접 표현
    FACE_SAVING = "face_saving"      # 체면 유지
    SOLIDARITY = "solidarity"        # 친밀감 표현
    DISTANCE = "distance"            # 거리감 표현


# ===========================================
# DATA CLASSES
# ===========================================

@dataclass
class MorphemeInfo:
    """Information about a morpheme"""
    surface: str        # Surface form
    tag: str           # POS tag
    is_honorific: bool = False
    honorific_type: Optional[HonorificType] = None


@dataclass
class SentenceAnalysis:
    """Analysis of a single sentence"""
    text: str
    speech_level: SpeechLevel
    confidence: float
    endings: List[str]
    honorific_markers: List[Dict[str, Any]]
    pragmatic_markers: List[Dict[str, Any]]
    morphemes: List[MorphemeInfo] = field(default_factory=list)


@dataclass 
class SpeechAnalysisResult:
    """Complete analysis result"""
    # Primary classification
    primary_level: SpeechLevel
    primary_level_name: str
    confidence: float
    
    # Detailed scores
    formality_score: float          # 0-100, higher = more formal
    politeness_score: float         # 0-100, higher = more polite
    honorific_density: float        # 0-1, ratio of honorific markers
    
    # Honorific analysis
    subject_honorification: Dict[str, Any]
    object_honorification: Dict[str, Any]
    addressee_honorification: Dict[str, Any]
    
    # Pragmatic analysis
    pragmatic_markers: List[Dict[str, Any]]
    
    # Consistency
    is_consistent: bool
    consistency_issues: List[str]
    
    # Per-sentence breakdown
    sentence_analyses: List[SentenceAnalysis]
    
    # Feature vector (for ML)
    feature_vector: Dict[str, float]
    
    # Human-readable summary
    summary_ko: str
    summary_en: str


# ===========================================
# PATTERN DATABASES
# ===========================================

class PatternDatabase:
    """Comprehensive pattern database for Korean speech analysis"""
    
    # ===========================================
    # SENTENCE ENDING PATTERNS BY LEVEL
    # ===========================================
    
    ENDINGS = {
        SpeechLevel.HASOSEO: {
            "patterns": [
                (r"나이다[.!]?$", "나이다", "statement"),
                (r"나이까[?]?$", "나이까", "question"),
                (r"소서[.!]?$", "소서", "request"),
                (r"사옵니다[.!]?$", "사옵니다", "humble"),
            ],
            "description_ko": "하소서체 (가장 높은 격식)",
            "description_en": "Hasoseo-che (Highest formal, archaic)",
        },
        
        SpeechLevel.HAPSYO: {
            "patterns": [
                # Statements - ㅂ니다 forms (받침 + 니다)
                (r"습니다[.!]?$", "습니다", "statement"),
                (r"[립닙밉십집팁]니다[.!]?$", "ㅂ니다", "statement"),  # 받침 ㅂ + 니다
                (r"입니다[.!]?$", "입니다", "copula"),
                (r"옵니다[.!]?$", "옵니다", "humble_statement"),
                (r"겠습니다[.!]?$", "겠습니다", "intention/future"),
                (r"었습니다[.!]?$", "었습니다", "past"),
                (r"았습니다[.!]?$", "았습니다", "past"),
                (r"셨습니다[.!]?$", "셨습니다", "honorific_past"),
                (r"니다[.!]?$", "니다", "formal_ending"),  # General -ㅂ니다
                
                # Questions
                (r"습니까[?]?$", "습니까", "question"),
                (r"[립닙밉십집팁]니까[?]?$", "ㅂ니까", "question"),
                (r"입니까[?]?$", "입니까", "copula_question"),
                (r"겠습니까[?]?$", "겠습니까", "intention_question"),
                (r"셨습니까[?]?$", "셨습니까", "honorific_past_question"),
                (r"니까[?]?$", "니까", "formal_question"),  # General -ㅂ니까
                
                # Imperatives/Requests
                (r"십시오[.!]?$", "십시오", "request"),
                (r"시오[.!]?$", "시오", "request_short"),
                (r"십시요[.!]?$", "십시요", "request_variant"),
                (r"주십시오[.!]?$", "주십시오", "please_request"),
                (r"시기 바랍니다[.!]?$", "시기 바랍니다", "formal_request"),
                (r"주시기 바랍니다[.!]?$", "주시기 바랍니다", "formal_please"),
                
                # Propositives
                (r"[립닙밉십집팁]시다[.!]?$", "ㅂ시다", "propositive"),
                (r"읍시다[.!]?$", "읍시다", "propositive"),
                (r"시겠습니까[?]?$", "시겠습니까", "polite_proposal"),
            ],
            "description_ko": "합쇼체 (격식 높임)",
            "description_en": "Hapsyo-che (Formal polite)",
        },
        
        SpeechLevel.HAO: {
            "patterns": [
                (r"하오[.!]?$", "하오", "statement"),
                (r"[았었]소[.!]?$", "았소/었소", "past"),
                (r"구려[.!]?$", "구려", "exclamatory"),
                (r"[으]?시오[.!]?$", "시오", "request"),
                (r"[으]?오[.!]?$", "오", "statement"),  # More restrictive
            ],
            "description_ko": "하오체 (예스러운 격식)",
            "description_en": "Hao-che (Old formal, rare)",
        },
        
        SpeechLevel.HAGE: {
            "patterns": [
                (r"[하]?게[.!]?$", "게", "statement/request"),
                (r"[하]?네[.!]?$", "네", "statement"),
                (r"[하]?나[?]?$", "나", "question"),
                (r"[하]?ㄴ가[?]?$", "ㄴ가", "question"),
                (r"주게[.!]?$", "주게", "request"),
            ],
            "description_ko": "하게체 (예스러운 하대)",
            "description_en": "Hage-che (Old informal to younger)",
        },
        
        SpeechLevel.HAERA: {
            "patterns": [
                # Plain form statements
                (r"[ㄴ는]다[.!]?$", "ㄴ다/는다", "plain_statement"),
                (r"다[.]?$", "다", "plain_statement"),
                (r"[이]?라[.!]?$", "라/이라", "copula_plain"),
                
                # Questions
                (r"[느]?냐[?]?$", "냐/느냐", "plain_question"),
                (r"[ㄴ는]?가[?]?$", "ㄴ가/는가", "plain_question"),
                (r"[이]?니[?]?$", "니", "plain_question"),
                
                # Imperatives
                (r"[아어여]라[.!]?$", "아라/어라", "plain_imperative"),
                (r"해라[.!]?$", "해라", "plain_imperative"),
                
                # Propositives
                (r"자[.!]?$", "자", "plain_propositive"),
                
                # Exclamatory
                (r"[는]?구나[.!]?$", "구나", "exclamatory"),
                (r"[는]?군[.!]?$", "군", "exclamatory"),
                (r"로다[.!]?$", "로다", "literary_exclamatory"),
            ],
            "description_ko": "해라체 (예사 낮춤 / 문어체)",
            "description_en": "Haera-che (Plain/written form)",
        },
        
        SpeechLevel.HAEYO: {
            "patterns": [
                # Basic polite endings
                (r"[아어여]요[.?!]?$", "아요/어요/여요", "polite_statement"),
                (r"해요[.?!]?$", "해요", "polite_statement"),
                (r"[이]?에요[.?!]?$", "에요/이에요", "copula_polite"),
                (r"예요[.?!]?$", "예요", "copula_polite"),
                (r"[이]?요[.?!]?$", "요", "polite_particle"),
                
                # Honorific polite
                (r"[으]?세요[.?!]?$", "세요", "honorific_polite"),
                (r"[으]?셔요[.?!]?$", "셔요", "honorific_polite"),
                (r"시어요[.?!]?$", "시어요", "honorific_polite_full"),
                
                # -죠/-지요 (confirmation seeking)
                (r"죠[.?!]?$", "죠", "confirmation"),
                (r"지요[.?!]?$", "지요", "confirmation"),
                
                # Exclamatory
                (r"네요[.!]?$", "네요", "exclamatory_polite"),
                (r"군요[.!]?$", "군요", "exclamatory_polite"),
                (r"구나요[.!]?$", "구나요", "exclamatory_polite"),
                
                # Reason/Cause
                (r"거든요[.!]?$", "거든요", "reason_polite"),
                (r"잖아요[.?!]?$", "잖아요", "obvious_polite"),
                (r"니까요[.!]?$", "니까요", "cause_polite"),
                (r"[아어]서요[.!]?$", "아서요/어서요", "sequential_polite"),
                
                # Questions
                (r"[ㄴ나]요[?]?$", "나요", "question_polite"),
                (r"[ㄹ을]까요[?]?$", "ㄹ까요/을까요", "suggestion_polite"),
                (r"[ㄹ을]래요[?]?$", "ㄹ래요/을래요", "intention_question"),
                
                # Connective with 요
                (r"[ㄴ는]데요[.?!]?$", "는데요/ㄴ데요", "background_polite"),
                (r"더니요[.?!]?$", "더니요", "retrospective_polite"),
                (r"더라고요[.!]?$", "더라고요", "hearsay_polite"),
                (r"다고요[.?!]?$", "다고요", "quotative_polite"),
                (r"래요[.!]?$", "래요", "hearsay_polite"),
                (r"대요[.!]?$", "대요", "hearsay_polite"),
                
                # Promise/Intention
                (r"[ㄹ을]게요[.!]?$", "ㄹ게요/을게요", "promise_polite"),
                
                # Retrospective
                (r"던데요[.?!]?$", "던데요", "retrospective_polite"),
                (r"었는데요[.?!]?$", "었는데요", "past_background"),
            ],
            "description_ko": "해요체 (비격식 높임)",
            "description_en": "Haeyo-che (Informal polite)",
        },
        
        SpeechLevel.HAE: {
            "patterns": [
                # Basic casual
                (r"해[.?!]?$", "해", "casual_statement"),
                (r"[아어여][.?!]?$", "아/어/여", "casual_ending"),
                
                # Casual with particles
                (r"[이]?야[.?!]?$", "야/이야", "casual_copula"),
                
                # Questions
                (r"[하]?니[?]?$", "니", "casual_question"),
                (r"[하]?냐[?]?$", "냐", "casual_question"),
                (r"[ㄹ을]?래[?]?$", "래/ㄹ래", "intention_casual"),
                (r"[ㄹ을]?까[?]?$", "까/ㄹ까", "suggestion_casual"),
                
                # Connective casual
                (r"[ㄴ는]?데[.?!]?$", "데/ㄴ데/는데", "background_casual"),
                (r"거든[.!]?$", "거든", "reason_casual"),
                (r"잖아[.?!]?$", "잖아", "obvious_casual"),
                (r"[ㄹ을]?걸[.!]?$", "걸", "speculation_casual"),
                
                # Exclamatory
                (r"네[.!]?$", "네", "exclamatory_casual"),
                (r"구나[.!]?$", "구나", "realization_casual"),
                (r"군[.!]?$", "군", "realization_casual"),
                (r"다니[.!]?$", "다니", "surprise_casual"),
                
                # Retrospective
                (r"더라[.!]?$", "더라", "retrospective_casual"),
                (r"던데[.?!]?$", "던데", "retrospective_casual"),
                
                # Promise
                (r"[ㄹ을]게[.!]?$", "게/ㄹ게", "promise_casual"),
                
                # Plain connective
                (r"지[.?!]?$", "지", "assertion_casual"),
                (r"[아어]서[.?!]?$", "아서/어서", "sequential"),
                (r"니까[.?!]?$", "니까", "cause"),
            ],
            "description_ko": "해체 (비격식 낮춤, 반말)",
            "description_en": "Hae-che (Casual/Banmal)",
        },
    }
    
    # ===========================================
    # SUBJECT HONORIFICATION (주체 높임법)
    # ===========================================
    
    SUBJECT_HONORIFIC = {
        # -시- suffix patterns
        "suffix_patterns": [
            (r"시[어아]", "-시어/-시아", "honorific_verb"),
            (r"셔", "-셔 (contracted)", "honorific_verb"),
            (r"시[었았]", "-시었/-시았", "honorific_past"),
            (r"셨", "-셨 (contracted)", "honorific_past"),
            (r"시겠", "-시겠", "honorific_future"),
            (r"[으]?실", "-실/-으실", "honorific_modifier"),
            (r"[으]?신", "-신/-으신", "honorific_modifier"),
            (r"[으]?시[ㄴ는]", "-시ㄴ/-시는", "honorific_modifier"),
            (r"시[면]", "-시면", "honorific_conditional"),
            (r"시[니]", "-시니", "honorific_reason"),
            (r"시[어아]서", "-시어서/-시아서", "honorific_sequential"),
            (r"셔서", "-셔서 (contracted)", "honorific_sequential"),
            (r"시[고]", "-시고", "honorific_and"),
            (r"시[며]", "-시며", "honorific_while"),
            (r"시[자]", "-시자", "honorific_as_soon_as"),
            (r"시[도]", "-시도", "honorific_even_if"),
            (r"시[다가]", "-시다가", "honorific_while_then"),
        ],
        
        # Honorific verb replacements (높임말 동사)
        "verb_replacements": {
            # Basic verbs → Honorific forms
            "있다": ("계시다", "be/exist"),
            "없다": ("안 계시다", "not be/exist"),
            "먹다": ("잡수시다/드시다", "eat"),
            "마시다": ("드시다", "drink"),
            "자다": ("주무시다", "sleep"),
            "말하다": ("말씀하시다", "speak"),
            "죽다": ("돌아가시다", "pass away"),
            "아프다": ("편찮으시다", "be sick"),
            "나이": ("연세", "age"),
            "이름": ("성함/존함", "name"),
            "집": ("댁", "house"),
            "밥": ("진지", "meal"),
            "생일": ("생신", "birthday"),
        },
        
        # Honorific particles
        "particles": {
            "께서": ("subject particle", 15),
            "께서는": ("subject + topic", 15),
            "께옵서": ("archaic subject", 12),
        },
    }
    
    # ===========================================
    # OBJECT HONORIFICATION (객체 높임법)
    # ===========================================
    
    OBJECT_HONORIFIC = {
        # Humble verbs (겸양어)
        "humble_verbs": {
            "드리다": ("give (humble)", "주다"),
            "올리다": ("give upward (humble)", "주다"),
            "바치다": ("offer (humble)", "주다"),
            "여쭙다": ("ask (humble)", "묻다"),
            "여쭤보다": ("ask (humble)", "묻다"),
            "여쭈다": ("ask (humble)", "묻다"),
            "아뢰다": ("report (humble)", "말하다"),
            "사뢰다": ("report (humble, archaic)", "말하다"),
            "뵙다": ("see/meet (humble)", "보다"),
            "뵈다": ("see/meet (humble)", "보다"),
            "모시다": ("serve/accompany (humble)", "데리다"),
            "받들다": ("serve/support (humble)", "돕다"),
        },
        
        # Object honorific particles
        "particles": {
            "께": ("dative honorific", 10),
            "께로": ("directional honorific", 8),
        },
        
        # Honorific noun forms
        "nouns": {
            "말씀": ("words", "말"),
            "분부": ("command", "명령"),
            "옥체": ("body (very honorific)", "몸"),
            "기체": ("health", "건강"),
            "춘추": ("age (very honorific)", "나이"),
            "귀하": ("you (honorific)", "당신"),
            "존안": ("face (honorific)", "얼굴"),
        },
    }
    
    # ===========================================
    # PRAGMATIC MARKERS (화용적 표지)
    # ===========================================
    
    PRAGMATIC_MARKERS = {
        PragmaticFunction.HEDGING: {
            "patterns": [
                (r"것 같아", "것 같다", "speculation"),
                (r"[ㄴ는]?듯", "듯하다", "appearance"),
                (r"[아어]보이", "보이다", "seems"),
                (r"[으]?려나", "려나", "wondering"),
                (r"[ㄴ는]?지", "는지", "wondering"),
                (r"[을ㄹ]?지도", "지도 모르다", "maybe"),
                (r"[은는]?가 봐", "나 보다", "seems like"),
                (r"[을ㄹ]?수도", "수도 있다", "might"),
            ],
            "words": ["아마", "혹시", "어쩌면", "글쎄", "설마", "모르겠는데"],
            "description": "Hedging expressions reduce certainty",
        },
        
        PragmaticFunction.SOFTENING: {
            "patterns": [
                (r"[아어]도 될까", "도 될까요", "permission_soft"),
                (r"[아어]줄 수", "줄 수 있어요", "request_soft"),
                (r"[으]?면 좋겠", "으면 좋겠다", "wish"),
                (r"[아어]주시면", "주시면", "if_you_could"),
                (r"괜찮으시[다면]?", "괜찮으시다면", "if_okay"),
                (r"실례지만", "실례지만", "excuse_me"),
                (r"죄송하지만", "죄송하지만", "sorry_but"),
            ],
            "words": ["혹시", "조금", "약간", "좀", "살짝"],
            "description": "Softening expressions reduce imposition",
        },
        
        PragmaticFunction.INTENSIFYING: {
            "patterns": [
                (r"정말[로]?", "정말", "really"),
                (r"진짜[로]?", "진짜", "really"),
                (r"너무", "너무", "too_much"),
                (r"완전", "완전", "completely"),
                (r"엄청", "엄청", "extremely"),
                (r"매우", "매우", "very"),
                (r"굉장히", "굉장히", "greatly"),
                (r"대단히", "대단히", "greatly"),
            ],
            "words": ["꼭", "반드시", "절대로", "무조건", "확실히"],
            "description": "Intensifiers strengthen the statement",
        },
        
        PragmaticFunction.INDIRECT: {
            "patterns": [
                (r"[으]?면 어떨까", "으면 어떨까요", "suggestion"),
                (r"[으]?면 안 될까", "으면 안 될까요", "indirect_request"),
                (r"[아어]주실 수", "주실 수 있으세요", "can_you"),
                (r"[으]?시겠어", "시겠어요", "would_you"),
                (r"[으]?시겠습니까", "시겠습니까", "would_you_formal"),
                (r"[으]?ㄹ까 해", "ㄹ까 하다", "thinking_of"),
            ],
            "words": [],
            "description": "Indirect speech acts for politeness",
        },
        
        PragmaticFunction.FACE_SAVING: {
            "patterns": [
                (r"죄송합니다만", "죄송합니다만", "sorry_but"),
                (r"실례합니다만", "실례합니다만", "excuse_but"),
                (r"송구합니다만", "송구합니다만", "sorry_but_formal"),
                (r"감사합니다만", "감사합니다만", "thank_but"),
                (r"말씀 중에", "말씀 중에", "while_speaking"),
            ],
            "words": ["죄송", "실례", "송구", "면목", "황송"],
            "description": "Face-saving expressions maintain harmony",
        },
        
        PragmaticFunction.SOLIDARITY: {
            "patterns": [
                (r"[우리]?같이", "같이", "together"),
                (r"우리[가]?", "우리", "we"),
                (r"[ㄹ을]?까[요]?", "ㄹ까요", "shall_we"),
                (r"[자]?[요]?", "자/자요", "let's"),
            ],
            "words": ["우리", "저희", "같이", "함께"],
            "description": "Solidarity markers show closeness",
        },
        
        PragmaticFunction.DISTANCE: {
            "patterns": [
                (r"저[는]?", "저", "humble_I"),
                (r"저희[는]?", "저희", "humble_we"),
                (r"귀[사하]", "귀사/귀하", "your_company"),
                (r"폐사", "폐사", "humble_company"),
                (r"소생", "소생", "humble_self"),
            ],
            "words": ["저", "저희", "귀", "폐", "본인"],
            "description": "Distance markers show respect through formality",
        },
    }
    
    # ===========================================
    # INFORMAL MARKERS
    # ===========================================
    
    INFORMAL_MARKERS = {
        "pronouns": {
            "나": ("I", -3),
            "너": ("you", -5),
            "넌": ("you (contracted)", -5),
            "난": ("I (contracted)", -3),
            "내가": ("I (subject)", -3),
            "네가": ("you (subject)", -5),
            "니가": ("you (subject, colloquial)", -6),
            "얘": ("this person/kid", -5),
            "걔": ("that person/kid", -5),
            "쟤": ("that person over there", -5),
            "우리": ("we", 0),  # Neutral, context-dependent
        },
        
        "address_terms": {
            "야": ("hey", -8),
            "임마": ("hey (rough)", -10),
            "자식아": ("hey (rough)", -10),
            "이놈아": ("hey (rough)", -12),
            "아": ("vocative particle", -5),
        },
        
        "interjections": {
            "응": ("yeah", -4),
            "어": ("uh/yeah", -4),
            "그래": ("okay", -3),
            "뭐": ("what", -2),
            "왜": ("why", -1),
            "야": ("hey/wow", -5),
            "헐": ("wow (slang)", -6),
            "대박": ("wow (slang)", -5),
            "ㅋㅋ": ("laughter", -4),
            "ㅎㅎ": ("laughter", -3),
        },
        
        "contractions": {
            "뭐야": ("what is it", -5),
            "왜 그래": ("what's wrong", -4),
            "어디야": ("where is it", -4),
            "뭐해": ("what doing", -5),
            "어때": ("how is it", -4),
        },
    }


# ===========================================
# MAIN ANALYZER CLASS
# ===========================================

class SophisticatedSpeechAnalyzer:
    """
    Sophisticated Korean speech level analyzer.
    
    Analyzes:
    - 7 speech levels (상대 높임법)
    - Subject honorification (주체 높임법)
    - Object honorification (객체 높임법)
    - Pragmatic markers (화용적 표지)
    - Consistency across sentences
    
    Uses KoNLPy for morphological analysis when available.
    """
    
    def __init__(self):
        self.db = PatternDatabase()
        self._compile_patterns()
        
        # Use global KoNLPy analyzer
        self.konlpy = konlpy_analyzer
        self.use_morphological = self.konlpy.is_available
        
        if self.use_morphological:
            logger.info(f"Using KoNLPy ({self.konlpy.analyzer_name}) for morphological analysis")
        else:
            logger.info("Using regex-based analysis (KoNLPy not available)")
    
    def _compile_patterns(self):
        """Compile all regex patterns."""
        self.compiled_endings = {}
        for level, data in self.db.ENDINGS.items():
            self.compiled_endings[level] = [
                (re.compile(p), name, func) 
                for p, name, func in data["patterns"]
            ]
        
        self.compiled_subject_hon = [
            (re.compile(p), name, desc)
            for p, name, desc in self.db.SUBJECT_HONORIFIC["suffix_patterns"]
        ]
        
        self.compiled_pragmatic = {}
        for func, data in self.db.PRAGMATIC_MARKERS.items():
            self.compiled_pragmatic[func] = [
                (re.compile(p), name, desc)
                for p, name, desc in data["patterns"]
            ]
    
    def analyze(self, text: str, context: Optional[Dict[str, Any]] = None) -> SpeechAnalysisResult:
        """
        Perform comprehensive speech level analysis.
        
        Args:
            text: Korean text to analyze
            context: Optional context (speaker, addressee, situation)
            
        Returns:
            SpeechAnalysisResult with detailed analysis
        """
        # Split into sentences
        sentences = self._split_sentences(text)
        
        # Analyze each sentence
        sentence_analyses = []
        for sent in sentences:
            analysis = self._analyze_sentence(sent)
            sentence_analyses.append(analysis)
        
        # Aggregate results
        primary_level, confidence = self._determine_primary_level(sentence_analyses)
        
        # Check consistency
        is_consistent, consistency_issues = self._check_consistency(sentence_analyses)
        
        # Analyze honorific system
        subject_hon = self._analyze_subject_honorification(text)
        object_hon = self._analyze_object_honorification(text)
        addressee_hon = self._analyze_addressee_honorification(sentence_analyses)
        
        # Analyze pragmatic markers
        pragmatic_markers = self._analyze_pragmatic_markers(text)
        
        # Calculate scores
        formality_score = self._calculate_formality_score(
            primary_level, subject_hon, object_hon, sentence_analyses
        )
        politeness_score = self._calculate_politeness_score(
            primary_level, subject_hon, object_hon, pragmatic_markers
        )
        honorific_density = self._calculate_honorific_density(
            text, subject_hon, object_hon
        )
        
        # Generate feature vector for ML
        feature_vector = self._generate_feature_vector(
            primary_level, formality_score, politeness_score,
            honorific_density, subject_hon, object_hon, pragmatic_markers
        )
        
        # Generate summaries
        summary_ko = self._generate_summary_ko(
            primary_level, formality_score, is_consistent, consistency_issues
        )
        summary_en = self._generate_summary_en(
            primary_level, formality_score, is_consistent, consistency_issues
        )
        
        return SpeechAnalysisResult(
            primary_level=primary_level,
            primary_level_name=self._get_level_name(primary_level),
            confidence=confidence,
            formality_score=formality_score,
            politeness_score=politeness_score,
            honorific_density=honorific_density,
            subject_honorification=subject_hon,
            object_honorification=object_hon,
            addressee_honorification=addressee_hon,
            pragmatic_markers=pragmatic_markers,
            is_consistent=is_consistent,
            consistency_issues=consistency_issues,
            sentence_analyses=sentence_analyses,
            feature_vector=feature_vector,
            summary_ko=summary_ko,
            summary_en=summary_en,
        )
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Split by sentence-ending punctuation
        sentences = re.split(r'(?<=[.?!])\s+', text)
        # Also split by newlines
        result = []
        for s in sentences:
            result.extend(s.split('\n'))
        return [s.strip() for s in result if s.strip()]
    
    def _analyze_sentence(self, sentence: str) -> SentenceAnalysis:
        """
        Analyze a single sentence using weighted scoring.
        Uses KoNLPy morphological analysis when available for better accuracy.
        """
        detected_endings = []
        level_scores = {level: 0.0 for level in SpeechLevel}
        
        # Strip whitespace
        sentence = sentence.strip()
        
        # ===========================================
        # MORPHOLOGICAL ANALYSIS (KoNLPy)
        # ===========================================
        morphemes = []
        morpheme_endings = []
        morpheme_particles = []
        has_honorific_suffix = False
        
        if self.use_morphological:
            pos_tags = self.konlpy.pos(sentence)
            
            for surface, tag in pos_tags:
                category = get_pos_category(tag)
                is_honorific = False
                hon_type = None
                
                # Check for honorific suffix -시-
                if surface in ['시', '셔', '셨', '시어', '세', '신', '실', '십']:
                    is_honorific = True
                    hon_type = HonorificType.SUBJECT
                    has_honorific_suffix = True
                
                morphemes.append(MorphemeInfo(
                    surface=surface,
                    tag=tag,
                    is_honorific=is_honorific,
                    honorific_type=hon_type
                ))
                
                # Collect endings (어미)
                if category == POSCategory.ENDING:
                    morpheme_endings.append((surface, tag))
                
                # Collect particles (조사)
                if category == POSCategory.PARTICLE:
                    morpheme_particles.append((surface, tag))
            
            # Use morpheme endings for better level detection
            level_scores = self._score_from_morphemes(morpheme_endings, level_scores)
        
        # ===========================================
        # REGEX PATTERN MATCHING (Supplement/Fallback)
        # ===========================================
        priority_order = [
            SpeechLevel.HAPSYO,   # -습니다 (most formal)
            SpeechLevel.HAEYO,    # -요 (most common polite)
            SpeechLevel.HAE,      # 반말 (most common casual)
            SpeechLevel.HAERA,    # 해라체 (written)
            SpeechLevel.HASOSEO,  # Archaic
            SpeechLevel.HAGE,     # Old
            SpeechLevel.HAO,      # Old (check last to avoid false positives)
        ]
        
        for level in priority_order:
            for pattern, name, func in self.compiled_endings.get(level, []):
                match = pattern.search(sentence)
                if match:
                    # Weight by match position (closer to end = higher score)
                    match_end = match.end()
                    sent_len = len(sentence)
                    position_weight = 1.0 if match_end >= sent_len - 2 else 0.5
                    
                    # Weight by pattern specificity (longer patterns = more specific)
                    pattern_len = len(name)
                    specificity_weight = min(2.0, pattern_len / 2)
                    
                    score = position_weight * specificity_weight
                    level_scores[level] += score
                    
                    detected_endings.append({
                        "pattern": name,
                        "function": func,
                        "level": level.name,
                        "score": score,
                        "source": "regex"
                    })
        
        # ===========================================
        # DETERMINE SPEECH LEVEL
        # ===========================================
        if any(s > 0 for s in level_scores.values()):
            best_level = max(level_scores.items(), key=lambda x: x[1])[0]
            max_score = max(level_scores.values())
        else:
            best_level = SpeechLevel.HAEYO  # Default
            max_score = 0
        
        # Apply informal marker penalty/boost
        informal_score = self._check_informal_markers(sentence)
        if informal_score < -5:  # Strong informal markers
            if best_level.value >= SpeechLevel.HAGE.value:
                best_level = SpeechLevel.HAE
        
        # Boost confidence if honorific suffix detected via morphology
        honorific_boost = 0.1 if has_honorific_suffix else 0
        
        # ===========================================
        # HONORIFIC MARKER ANALYSIS
        # ===========================================
        honorific_markers = []
        
        # From regex patterns
        for pattern, name, desc in self.compiled_subject_hon:
            if pattern.search(sentence):
                honorific_markers.append({
                    "type": "subject",
                    "pattern": name,
                    "description": desc,
                    "source": "regex"
                })
        
        # From morphological analysis
        if self.use_morphological:
            for morph in morphemes:
                if morph.is_honorific and morph.honorific_type:
                    honorific_markers.append({
                        "type": morph.honorific_type.value,
                        "pattern": morph.surface,
                        "description": f"Morpheme: {morph.tag}",
                        "source": "konlpy"
                    })
            
            # Check for honorific particles
            for surface, tag in morpheme_particles:
                if surface in ['께서', '께']:
                    honorific_markers.append({
                        "type": "subject" if surface == "께서" else "object",
                        "pattern": surface,
                        "description": f"Honorific particle ({tag})",
                        "source": "konlpy"
                    })
        
        # Deduplicate honorific markers
        seen_patterns = set()
        unique_markers = []
        for m in honorific_markers:
            if m["pattern"] not in seen_patterns:
                seen_patterns.add(m["pattern"])
                unique_markers.append(m)
        honorific_markers = unique_markers
        
        # ===========================================
        # PRAGMATIC MARKER ANALYSIS
        # ===========================================
        pragmatic_markers = []
        for func, patterns in self.compiled_pragmatic.items():
            for pattern, name, desc in patterns:
                if pattern.search(sentence):
                    pragmatic_markers.append({
                        "function": func.value,
                        "pattern": name,
                        "description": desc
                    })
        
        # ===========================================
        # CALCULATE CONFIDENCE
        # ===========================================
        total_score = sum(level_scores.values())
        if total_score > 0 and max_score > 0:
            confidence = min(0.95, 0.5 + (max_score / total_score) * 0.5)
        else:
            confidence = 0.5
        
        # Boost confidence for honorific markers and morphological analysis
        confidence = min(1.0, confidence + honorific_boost)
        if honorific_markers:
            confidence = min(1.0, confidence + 0.05)
        if self.use_morphological and morpheme_endings:
            confidence = min(1.0, confidence + 0.05)
        
        return SentenceAnalysis(
            text=sentence,
            speech_level=best_level,
            confidence=confidence,
            endings=[e["pattern"] for e in detected_endings],
            honorific_markers=honorific_markers,
            pragmatic_markers=pragmatic_markers,
            morphemes=morphemes
        )
    
    def _score_from_morphemes(
        self, 
        endings: List[Tuple[str, str]], 
        level_scores: Dict[SpeechLevel, float]
    ) -> Dict[SpeechLevel, float]:
        """
        Score speech levels based on morpheme endings extracted by KoNLPy.
        This provides more accurate detection than regex alone.
        """
        # Ending → Speech Level mapping
        # These are the actual morpheme forms extracted by KoNLPy
        ending_map = {
            # HAPSYO (합쇼체) - Formal
            "습니다": (SpeechLevel.HAPSYO, 3.0),
            "ㅂ니다": (SpeechLevel.HAPSYO, 3.0),
            "입니다": (SpeechLevel.HAPSYO, 3.0),
            "습니까": (SpeechLevel.HAPSYO, 3.0),
            "ㅂ니까": (SpeechLevel.HAPSYO, 3.0),
            "십시오": (SpeechLevel.HAPSYO, 3.0),
            "십시": (SpeechLevel.HAPSYO, 2.5),
            "ㅂ시다": (SpeechLevel.HAPSYO, 2.5),
            
            # HAEYO (해요체) - Polite informal
            "어요": (SpeechLevel.HAEYO, 2.5),
            "아요": (SpeechLevel.HAEYO, 2.5),
            "여요": (SpeechLevel.HAEYO, 2.5),
            "에요": (SpeechLevel.HAEYO, 2.5),
            "예요": (SpeechLevel.HAEYO, 2.5),
            "세요": (SpeechLevel.HAEYO, 2.5),
            "셔요": (SpeechLevel.HAEYO, 2.5),
            "죠": (SpeechLevel.HAEYO, 2.0),
            "지요": (SpeechLevel.HAEYO, 2.0),
            "네요": (SpeechLevel.HAEYO, 2.0),
            "군요": (SpeechLevel.HAEYO, 2.0),
            "거든요": (SpeechLevel.HAEYO, 2.0),
            "잖아요": (SpeechLevel.HAEYO, 2.0),
            "ㄹ까요": (SpeechLevel.HAEYO, 2.0),
            "ㄹ게요": (SpeechLevel.HAEYO, 2.0),
            "나요": (SpeechLevel.HAEYO, 1.5),
            "ㄴ데요": (SpeechLevel.HAEYO, 1.5),
            "는데요": (SpeechLevel.HAEYO, 1.5),
            
            # HAE (해체) - Casual/반말
            "어": (SpeechLevel.HAE, 2.0),
            "아": (SpeechLevel.HAE, 2.0),
            "여": (SpeechLevel.HAE, 2.0),
            "야": (SpeechLevel.HAE, 2.0),
            "지": (SpeechLevel.HAE, 1.5),
            "니": (SpeechLevel.HAE, 1.5),
            "냐": (SpeechLevel.HAE, 1.5),
            "네": (SpeechLevel.HAE, 1.5),
            "군": (SpeechLevel.HAE, 1.5),
            "거든": (SpeechLevel.HAE, 1.5),
            "잖아": (SpeechLevel.HAE, 1.5),
            "ㄹ까": (SpeechLevel.HAE, 1.5),
            "ㄹ게": (SpeechLevel.HAE, 1.5),
            "더라": (SpeechLevel.HAE, 1.5),
            "는데": (SpeechLevel.HAE, 1.0),
            "ㄴ데": (SpeechLevel.HAE, 1.0),
            
            # HAERA (해라체) - Plain form
            "다": (SpeechLevel.HAERA, 1.5),
            "ㄴ다": (SpeechLevel.HAERA, 2.0),
            "는다": (SpeechLevel.HAERA, 2.0),
            "냐": (SpeechLevel.HAERA, 1.5),
            "느냐": (SpeechLevel.HAERA, 2.0),
            "자": (SpeechLevel.HAERA, 1.5),
            "구나": (SpeechLevel.HAERA, 2.0),
            "어라": (SpeechLevel.HAERA, 2.0),
            "아라": (SpeechLevel.HAERA, 2.0),
        }
        
        for surface, tag in endings:
            if surface in ending_map:
                level, score = ending_map[surface]
                level_scores[level] += score
        
        return level_scores
    
    def _check_informal_markers(self, text: str) -> int:
        """Check for informal markers and return a score (negative = informal)."""
        score = 0
        
        for category in ["pronouns", "address_terms", "interjections"]:
            for word, (desc, points) in self.db.INFORMAL_MARKERS.get(category, {}).items():
                if word in text:
                    score += points
        
        return score
    
    def _determine_primary_level(
        self, 
        analyses: List[SentenceAnalysis]
    ) -> Tuple[SpeechLevel, float]:
        """Determine the primary speech level from sentence analyses."""
        if not analyses:
            return SpeechLevel.HAEYO, 0.5  # Default
        
        # Count levels
        level_counts = Counter(a.speech_level for a in analyses)
        
        # Weight by confidence
        level_scores = {}
        for a in analyses:
            level_scores[a.speech_level] = level_scores.get(a.speech_level, 0) + a.confidence
        
        # Get most common
        most_common = max(level_scores.items(), key=lambda x: x[1])
        primary_level = most_common[0]
        
        # Calculate confidence
        total_confidence = sum(a.confidence for a in analyses)
        if total_confidence > 0:
            confidence = most_common[1] / total_confidence
        else:
            confidence = 0.5
        
        return primary_level, confidence
    
    def _check_consistency(
        self, 
        analyses: List[SentenceAnalysis]
    ) -> Tuple[bool, List[str]]:
        """Check consistency of speech level across sentences."""
        if len(analyses) <= 1:
            return True, []
        
        issues = []
        levels = [a.speech_level for a in analyses]
        unique_levels = set(levels)
        
        # Check for mixing formal/informal
        has_formal = any(l.value >= SpeechLevel.HAPSYO.value for l in levels)
        has_informal = any(l.value <= SpeechLevel.HAE.value for l in levels)
        
        if has_formal and has_informal:
            issues.append("격식체와 비격식체가 섞여 있습니다")
        
        # Check for mixing 해요 and 해
        has_haeyo = SpeechLevel.HAEYO in levels
        has_hae = SpeechLevel.HAE in levels
        
        if has_haeyo and has_hae:
            issues.append("존댓말과 반말이 섞여 있습니다")
        
        # Check for more than 2 different levels
        if len(unique_levels) > 2:
            issues.append(f"{len(unique_levels)}가지 다른 말투가 사용되었습니다")
        
        return len(issues) == 0, issues
    
    def _analyze_subject_honorification(self, text: str) -> Dict[str, Any]:
        """Analyze subject honorification (주체 높임법)."""
        results = {
            "suffix_count": 0,
            "suffixes_found": [],
            "honorific_verbs": [],
            "particles": [],
            "score": 0
        }
        
        # Check -시- suffixes
        for pattern, name, desc in self.compiled_subject_hon:
            matches = pattern.findall(text)
            if matches:
                results["suffix_count"] += len(matches)
                results["suffixes_found"].append({
                    "pattern": name,
                    "count": len(matches),
                    "description": desc
                })
                results["score"] += len(matches) * 5
        
        # Check honorific verb replacements
        for plain, (honorific, meaning) in self.db.SUBJECT_HONORIFIC["verb_replacements"].items():
            # Check if honorific form is used
            hon_forms = honorific.split("/")
            for hon in hon_forms:
                if hon in text:
                    results["honorific_verbs"].append({
                        "used": hon,
                        "plain_form": plain,
                        "meaning": meaning
                    })
                    results["score"] += 10
        
        # Check honorific particles
        for particle, (desc, points) in self.db.SUBJECT_HONORIFIC["particles"].items():
            if particle in text:
                results["particles"].append({
                    "particle": particle,
                    "description": desc
                })
                results["score"] += points
        
        return results
    
    def _analyze_object_honorification(self, text: str) -> Dict[str, Any]:
        """Analyze object honorification (객체 높임법)."""
        results = {
            "humble_verbs": [],
            "particles": [],
            "honorific_nouns": [],
            "score": 0
        }
        
        # Check humble verbs
        for humble, (desc, plain) in self.db.OBJECT_HONORIFIC["humble_verbs"].items():
            if humble in text:
                results["humble_verbs"].append({
                    "verb": humble,
                    "plain_form": plain,
                    "description": desc
                })
                results["score"] += 15
        
        # Check object particles
        for particle, (desc, points) in self.db.OBJECT_HONORIFIC["particles"].items():
            if particle in text:
                results["particles"].append({
                    "particle": particle,
                    "description": desc
                })
                results["score"] += points
        
        # Check honorific nouns
        for hon_noun, (meaning, plain) in self.db.OBJECT_HONORIFIC["nouns"].items():
            if hon_noun in text:
                results["honorific_nouns"].append({
                    "noun": hon_noun,
                    "plain_form": plain,
                    "meaning": meaning
                })
                results["score"] += 8
        
        return results
    
    def _analyze_addressee_honorification(
        self, 
        analyses: List[SentenceAnalysis]
    ) -> Dict[str, Any]:
        """Analyze addressee honorification (상대 높임법)."""
        level_distribution = Counter(a.speech_level for a in analyses)
        
        # Get dominant level
        if level_distribution:
            dominant = level_distribution.most_common(1)[0]
            dominant_level = dominant[0]
            dominant_count = dominant[1]
        else:
            dominant_level = SpeechLevel.HAEYO
            dominant_count = 0
        
        return {
            "dominant_level": dominant_level.name,
            "dominant_level_value": dominant_level.value,
            "level_description_ko": self.db.ENDINGS[dominant_level]["description_ko"],
            "level_description_en": self.db.ENDINGS[dominant_level]["description_en"],
            "distribution": {l.name: c for l, c in level_distribution.items()},
            "all_endings": [
                e for a in analyses for e in a.endings
            ]
        }
    
    def _analyze_pragmatic_markers(self, text: str) -> List[Dict[str, Any]]:
        """Analyze pragmatic markers in text."""
        markers = []
        
        for func, data in self.db.PRAGMATIC_MARKERS.items():
            func_markers = []
            
            # Check patterns
            for pattern, name, desc in self.compiled_pragmatic.get(func, []):
                if pattern.search(text):
                    func_markers.append({
                        "type": "pattern",
                        "value": name,
                        "description": desc
                    })
            
            # Check words
            for word in data.get("words", []):
                if word in text:
                    func_markers.append({
                        "type": "word",
                        "value": word
                    })
            
            if func_markers:
                markers.append({
                    "function": func.value,
                    "description": data.get("description", ""),
                    "markers": func_markers,
                    "count": len(func_markers)
                })
        
        return markers
    
    def _calculate_formality_score(
        self,
        primary_level: SpeechLevel,
        subject_hon: Dict,
        object_hon: Dict,
        analyses: List[SentenceAnalysis]
    ) -> float:
        """Calculate formality score (0-100)."""
        # Base score from speech level
        level_scores = {
            SpeechLevel.HASOSEO: 100,
            SpeechLevel.HAPSYO: 90,
            SpeechLevel.HAO: 80,
            SpeechLevel.HAGE: 60,
            SpeechLevel.HAERA: 40,
            SpeechLevel.HAEYO: 50,
            SpeechLevel.HAE: 20,
        }
        base_score = level_scores.get(primary_level, 50)
        
        # Boost for honorific usage
        hon_boost = min(20, (subject_hon.get("score", 0) + object_hon.get("score", 0)) / 5)
        
        return min(100, base_score + hon_boost)
    
    def _calculate_politeness_score(
        self,
        primary_level: SpeechLevel,
        subject_hon: Dict,
        object_hon: Dict,
        pragmatic_markers: List[Dict]
    ) -> float:
        """Calculate politeness score (0-100)."""
        # Base from formality
        base = 50 if primary_level.value >= SpeechLevel.HAEYO.value else 30
        
        # Add honorific points
        hon_points = (subject_hon.get("score", 0) + object_hon.get("score", 0)) / 3
        
        # Add pragmatic marker points
        pragmatic_points = 0
        for marker in pragmatic_markers:
            if marker["function"] in ["softening", "face_saving", "hedging"]:
                pragmatic_points += marker.get("count", 1) * 3
        
        return min(100, base + hon_points + pragmatic_points)
    
    def _calculate_honorific_density(
        self,
        text: str,
        subject_hon: Dict,
        object_hon: Dict
    ) -> float:
        """Calculate density of honorific markers (0-1)."""
        total_chars = len(text)
        if total_chars == 0:
            return 0.0
        
        # Count honorific elements
        hon_count = (
            subject_hon.get("suffix_count", 0) +
            len(subject_hon.get("honorific_verbs", [])) +
            len(subject_hon.get("particles", [])) +
            len(object_hon.get("humble_verbs", [])) +
            len(object_hon.get("particles", []))
        )
        
        # Normalize (assume average word is 3 chars)
        estimated_words = total_chars / 3
        if estimated_words > 0:
            return min(1.0, hon_count / estimated_words)
        return 0.0
    
    def _generate_feature_vector(
        self,
        primary_level: SpeechLevel,
        formality_score: float,
        politeness_score: float,
        honorific_density: float,
        subject_hon: Dict,
        object_hon: Dict,
        pragmatic_markers: List[Dict]
    ) -> Dict[str, float]:
        """Generate feature vector for ML models."""
        # One-hot encode speech level
        level_features = {f"level_{l.name}": 0.0 for l in SpeechLevel}
        level_features[f"level_{primary_level.name}"] = 1.0
        
        # Count pragmatic functions
        pragmatic_features = {f"pragmatic_{f.value}": 0.0 for f in PragmaticFunction}
        for marker in pragmatic_markers:
            key = f"pragmatic_{marker['function']}"
            pragmatic_features[key] = marker.get("count", 1)
        
        return {
            **level_features,
            "formality_score": formality_score / 100,
            "politeness_score": politeness_score / 100,
            "honorific_density": honorific_density,
            "subject_hon_score": subject_hon.get("score", 0) / 100,
            "object_hon_score": object_hon.get("score", 0) / 100,
            "suffix_count": subject_hon.get("suffix_count", 0),
            "honorific_verb_count": len(subject_hon.get("honorific_verbs", [])),
            "humble_verb_count": len(object_hon.get("humble_verbs", [])),
            **pragmatic_features,
        }
    
    def _get_level_name(self, level: SpeechLevel) -> str:
        """Get Korean name for speech level."""
        names = {
            SpeechLevel.HASOSEO: "하소서체",
            SpeechLevel.HAPSYO: "합쇼체",
            SpeechLevel.HAO: "하오체",
            SpeechLevel.HAGE: "하게체",
            SpeechLevel.HAERA: "해라체",
            SpeechLevel.HAEYO: "해요체",
            SpeechLevel.HAE: "해체 (반말)",
        }
        return names.get(level, "알 수 없음")
    
    def _generate_summary_ko(
        self,
        level: SpeechLevel,
        formality: float,
        consistent: bool,
        issues: List[str]
    ) -> str:
        """Generate Korean summary."""
        level_name = self._get_level_name(level)
        
        summary = f"주로 {level_name}을(를) 사용하고 있습니다. "
        
        if formality >= 80:
            summary += "매우 격식 있는 말투입니다. "
        elif formality >= 60:
            summary += "예의 바른 말투입니다. "
        elif formality >= 40:
            summary += "일상적인 말투입니다. "
        else:
            summary += "친근한 말투입니다. "
        
        if not consistent:
            summary += "⚠️ " + " ".join(issues)
        
        return summary
    
    def _generate_summary_en(
        self,
        level: SpeechLevel,
        formality: float,
        consistent: bool,
        issues: List[str]
    ) -> str:
        """Generate English summary."""
        level_desc = self.db.ENDINGS[level]["description_en"]
        
        summary = f"Primary speech level: {level_desc}. "
        
        if formality >= 80:
            summary += "Very formal register. "
        elif formality >= 60:
            summary += "Polite register. "
        elif formality >= 40:
            summary += "Casual-polite register. "
        else:
            summary += "Casual/informal register. "
        
        if not consistent:
            summary += "⚠️ Inconsistent speech levels detected."
        
        return summary


# ===========================================
# SINGLETON & HELPER FUNCTIONS
# ===========================================

# Global analyzer instance
_analyzer: Optional[SophisticatedSpeechAnalyzer] = None

def get_analyzer() -> SophisticatedSpeechAnalyzer:
    """Get or create the analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = SophisticatedSpeechAnalyzer()
    return _analyzer


def analyze_speech_level(text: str) -> Dict[str, Any]:
    """
    Analyze Korean speech level (convenience function).
    
    Returns a dictionary with complete analysis.
    """
    analyzer = get_analyzer()
    result = analyzer.analyze(text)
    
    return {
        "primary_level": result.primary_level.name,
        "primary_level_korean": result.primary_level_name,
        "confidence": result.confidence,
        
        "scores": {
            "formality": result.formality_score,
            "politeness": result.politeness_score,
            "honorific_density": result.honorific_density,
        },
        
        "honorification": {
            "subject": result.subject_honorification,
            "object": result.object_honorification,
            "addressee": result.addressee_honorification,
        },
        
        "pragmatic_markers": result.pragmatic_markers,
        
        "consistency": {
            "is_consistent": result.is_consistent,
            "issues": result.consistency_issues,
        },
        
        "summary": {
            "korean": result.summary_ko,
            "english": result.summary_en,
        },
        
        "sentence_count": len(result.sentence_analyses),
        "feature_vector": result.feature_vector,
    }


def check_appropriateness(
    text: str, 
    expected_level: str,
    situation: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check if speech level is appropriate.
    
    Args:
        text: Korean text to check
        expected_level: Expected level (FORMAL, POLITE, INFORMAL)
        situation: Optional situation context
    
    Returns:
        Appropriateness check result
    """
    analyzer = get_analyzer()
    result = analyzer.analyze(text)
    
    # Map expected level
    level_map = {
        "FORMAL": [SpeechLevel.HAPSYO, SpeechLevel.HASOSEO],
        "POLITE": [SpeechLevel.HAEYO],
        "INFORMAL": [SpeechLevel.HAE, SpeechLevel.HAERA],
        "formal": [SpeechLevel.HAPSYO, SpeechLevel.HASOSEO],
        "polite": [SpeechLevel.HAEYO],
        "informal": [SpeechLevel.HAE, SpeechLevel.HAERA],
        "casual": [SpeechLevel.HAE, SpeechLevel.HAERA],
    }
    
    expected_levels = level_map.get(expected_level, [SpeechLevel.HAEYO])
    is_appropriate = result.primary_level in expected_levels
    
    # Generate feedback
    feedback_ko = ""
    feedback_en = ""
    
    if not is_appropriate:
        if expected_level in ["FORMAL", "formal"]:
            feedback_ko = "격식체(-습니다)를 사용해야 하는 상황입니다."
            feedback_en = "This situation requires formal speech (-습니다 form)."
        elif expected_level in ["POLITE", "polite"]:
            if result.primary_level in [SpeechLevel.HAE, SpeechLevel.HAERA]:
                feedback_ko = "존댓말(-요)을 사용해 주세요."
                feedback_en = "Please use polite speech (-요 form)."
            else:
                feedback_ko = "해요체로 조금 더 편하게 말해도 괜찮아요."
                feedback_en = "You can speak more casually using -요 form."
        else:  # informal
            feedback_ko = "친한 사이니까 반말로 편하게 말해도 돼요!"
            feedback_en = "We're close, so you can speak casually!"
    
    return {
        "is_appropriate": is_appropriate,
        "detected_level": result.primary_level.name,
        "detected_level_korean": result.primary_level_name,
        "expected_level": expected_level,
        "confidence": result.confidence,
        "feedback_ko": feedback_ko,
        "feedback_en": feedback_en,
        "is_consistent": result.is_consistent,
        "consistency_issues": result.consistency_issues,
        "formality_score": result.formality_score,
        "politeness_score": result.politeness_score,
    }
