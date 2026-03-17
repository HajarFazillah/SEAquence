"""
Simplified Speech Level Analyzer (3-Level)
Analyzes Korean speech for: 반말 (informal), 해요체 (polite), 합쇼체 (formal)
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


# ===========================================
# SPEECH LEVEL ENUM (Simplified 3-Level)
# ===========================================

class SpeechLevel(Enum):
    """Three main Korean speech levels."""
    FORMAL = "formal"       # 합쇼체 (-습니다, -습니까)
    POLITE = "polite"       # 해요체 (-요, -세요)
    INFORMAL = "informal"   # 반말 (-어, -아, -야)
    UNKNOWN = "unknown"


# ===========================================
# SPEECH LEVEL INFO
# ===========================================

SPEECH_LEVEL_INFO = {
    SpeechLevel.FORMAL: {
        "name_ko": "합쇼체",
        "name_en": "Formal",
        "description_ko": "격식체. 공식적인 상황, 윗사람에게 사용",
        "description_en": "Formal speech. Used in official situations, to superiors",
        "examples": ["감사합니다", "안녕하십니까", "질문이 있습니다"],
        "endings": ["-습니다", "-습니까", "-십시오"],
        "level": 3
    },
    SpeechLevel.POLITE: {
        "name_ko": "해요체",
        "name_en": "Polite",
        "description_ko": "존댓말. 일상적인 존댓말, 처음 만난 사람에게 사용",
        "description_en": "Polite speech. Everyday politeness, used with strangers",
        "examples": ["감사해요", "안녕하세요", "뭐 해요?"],
        "endings": ["-요", "-세요", "-해요"],
        "level": 2
    },
    SpeechLevel.INFORMAL: {
        "name_ko": "반말",
        "name_en": "Informal",
        "description_ko": "반말. 친한 친구, 동생, 아랫사람에게 사용",
        "description_en": "Informal speech. Used with close friends, younger people",
        "examples": ["고마워", "안녕", "뭐 해?"],
        "endings": ["-어", "-아", "-야", "-지"],
        "level": 1
    }
}


# ===========================================
# PATTERN DEFINITIONS
# ===========================================

# Formal endings (합쇼체)
FORMAL_PATTERNS = [
    r'습니다[.?!]?$',
    r'습니까[?]?$',
    r'십시오[.!]?$',
    r'십니까[?]?$',
    r'옵니다[.?!]?$',
    r'옵니까[?]?$',
    r'하십시오[.!]?$',
    r'드립니다[.?!]?$',
    r'드릴까요[?]?$',
    r'겠습니다[.?!]?$',
    r'었습니다[.?!]?$',
    r'았습니다[.?!]?$',
    r'계십니까[?]?$',
]

# Polite endings (해요체)
POLITE_PATTERNS = [
    r'[아어여이]요[.?!]?$',
    r'세요[.?!]?$',
    r'해요[.?!]?$',
    r'예요[.?!]?$',
    r'이에요[.?!]?$',
    r'네요[.?!]?$',
    r'죠[.?!]?$',
    r'나요[.?!]?$',
    r'는데요[.?!]?$',
    r'거든요[.?!]?$',
    r'잖아요[.?!]?$',
    r'할게요[.?!]?$',
    r'갈게요[.?!]?$',
    r'볼게요[.?!]?$',
    r'줄게요[.?!]?$',
    r'할까요[?]?$',
    r'드릴까요[?]?$',
    r'싶어요[.?!]?$',
    r'같아요[.?!]?$',
    r'있어요[.?!]?$',
    r'없어요[.?!]?$',
    r'됐어요[.?!]?$',
    r'됐죠[.?!]?$',
]

# Informal endings (반말)
INFORMAL_PATTERNS = [
    r'[아어][\s.?!]*$',
    r'야[.?!]?$',
    r'지[.?!]?$',
    r'냐[?]?$',
    r'니[?]?$',
    r'네[.?!]?$',
    r'군[.?!]?$',
    r'거야[.?!]?$',
    r'거지[.?!]?$',
    r'잖아[.?!]?$',
    r'는데[.?!]?$',
    r'더라[.?!]?$',
    r'거든[.?!]?$',
    r'할게[.?!]?$',
    r'갈게[.?!]?$',
    r'볼게[.?!]?$',
    r'줄게[.?!]?$',
    r'해봐[.?!]?$',
    r'가자[.?!]?$',
    r'하자[.?!]?$',
    r'먹자[.?!]?$',
    r'뭐야[.?!]?$',
    r'뭐해[.?!]?$',
    r'뭐냐[?]?$',
    r'좋아[.?!]?$',
    r'싫어[.?!]?$',
    r'있어[.?!]?$',
    r'없어[.?!]?$',
    r'됐어[.?!]?$',
    r'했어[.?!]?$',
    r'갔어[.?!]?$',
    r'왔어[.?!]?$',
    r'봤어[.?!]?$',
    r'먹었어[.?!]?$',
]


# ===========================================
# SPEECH ANALYZER CLASS
# ===========================================

@dataclass
class AnalysisResult:
    """Result of speech level analysis."""
    text: str
    speech_level: SpeechLevel
    speech_level_ko: str
    speech_level_en: str
    confidence: float
    matched_patterns: List[str]
    is_appropriate: Optional[bool] = None
    feedback_ko: Optional[str] = None
    feedback_en: Optional[str] = None


class SimpleSpeechAnalyzer:
    """
    Simple 3-level Korean speech analyzer.
    Uses regex patterns to detect 반말/해요체/합쇼체.
    """
    
    def __init__(self):
        # Compile patterns for efficiency
        self.formal_patterns = [re.compile(p, re.IGNORECASE) for p in FORMAL_PATTERNS]
        self.polite_patterns = [re.compile(p, re.IGNORECASE) for p in POLITE_PATTERNS]
        self.informal_patterns = [re.compile(p, re.IGNORECASE) for p in INFORMAL_PATTERNS]
    
    def analyze(self, text: str) -> AnalysisResult:
        """
        Analyze the speech level of Korean text.
        
        Args:
            text: Korean text to analyze
            
        Returns:
            AnalysisResult with detected level and confidence
        """
        if not text or not text.strip():
            return AnalysisResult(
                text=text,
                speech_level=SpeechLevel.UNKNOWN,
                speech_level_ko="알 수 없음",
                speech_level_en="Unknown",
                confidence=0.0,
                matched_patterns=[]
            )
        
        text = text.strip()
        
        # Count matches for each level
        formal_matches = self._find_matches(text, self.formal_patterns)
        polite_matches = self._find_matches(text, self.polite_patterns)
        informal_matches = self._find_matches(text, self.informal_patterns)
        
        # Determine level based on matches
        formal_score = len(formal_matches) * 3  # Higher weight for formal
        polite_score = len(polite_matches) * 2
        informal_score = len(informal_matches) * 1
        
        total = formal_score + polite_score + informal_score
        
        if total == 0:
            # No patterns matched, try to guess from sentence ending
            level, matches = self._guess_from_ending(text)
        elif formal_score >= polite_score and formal_score >= informal_score:
            level = SpeechLevel.FORMAL
            matches = formal_matches
        elif polite_score >= informal_score:
            level = SpeechLevel.POLITE
            matches = polite_matches
        else:
            level = SpeechLevel.INFORMAL
            matches = informal_matches
        
        # Calculate confidence
        if total > 0:
            if level == SpeechLevel.FORMAL:
                confidence = min(1.0, formal_score / total + 0.3)
            elif level == SpeechLevel.POLITE:
                confidence = min(1.0, polite_score / total + 0.2)
            else:
                confidence = min(1.0, informal_score / total + 0.1)
        else:
            confidence = 0.5  # Default confidence for guessed level
        
        level_info = SPEECH_LEVEL_INFO.get(level, {})
        
        return AnalysisResult(
            text=text,
            speech_level=level,
            speech_level_ko=level_info.get("name_ko", "알 수 없음"),
            speech_level_en=level_info.get("name_en", "Unknown"),
            confidence=round(confidence, 2),
            matched_patterns=matches
        )
    
    def _find_matches(self, text: str, patterns: List[re.Pattern]) -> List[str]:
        """Find all matching patterns in text."""
        matches = []
        for pattern in patterns:
            if pattern.search(text):
                matches.append(pattern.pattern)
        return matches
    
    def _guess_from_ending(self, text: str) -> Tuple[SpeechLevel, List[str]]:
        """Guess speech level from sentence ending when no patterns match."""
        text = text.rstrip('?.!')
        
        # Check last characters
        if text.endswith(('습니다', '습니까', '십시오', '옵니다')):
            return SpeechLevel.FORMAL, ['ending_based']
        elif text.endswith(('요', '세요', '해요', '예요', '이에요', '죠')):
            return SpeechLevel.POLITE, ['ending_based']
        elif text.endswith(('어', '아', '야', '지', '냐', '니', '네')):
            return SpeechLevel.INFORMAL, ['ending_based']
        
        return SpeechLevel.UNKNOWN, []
    
    def check_appropriateness(
        self,
        text: str,
        expected_level: str,
        avatar_role: str = None
    ) -> AnalysisResult:
        """
        Check if speech level is appropriate for the situation.
        
        Args:
            text: User's message
            expected_level: Expected level (formal/polite/informal)
            avatar_role: Avatar's role (professor/senior/friend/junior)
            
        Returns:
            AnalysisResult with appropriateness feedback
        """
        result = self.analyze(text)
        
        # Map expected level string to enum
        level_map = {
            "formal": SpeechLevel.FORMAL,
            "very_polite": SpeechLevel.FORMAL,
            "polite": SpeechLevel.POLITE,
            "informal": SpeechLevel.INFORMAL,
            "casual": SpeechLevel.INFORMAL,
        }
        
        expected = level_map.get(expected_level.lower(), SpeechLevel.POLITE)
        detected = result.speech_level
        
        # Check appropriateness
        is_appropriate = True
        feedback_ko = ""
        feedback_en = ""
        
        if detected == SpeechLevel.UNKNOWN:
            is_appropriate = True  # Can't determine, assume OK
            feedback_ko = ""
            feedback_en = ""
        elif expected == SpeechLevel.FORMAL:
            if detected == SpeechLevel.INFORMAL:
                is_appropriate = False
                feedback_ko = "격식체(-습니다)를 사용해야 하는 상황입니다. 반말은 적절하지 않아요."
                feedback_en = "This situation requires formal speech (-습니다). Informal speech is inappropriate."
            elif detected == SpeechLevel.POLITE:
                is_appropriate = True  # Polite is acceptable, but formal is better
                feedback_ko = "해요체도 괜찮지만, 격식체(-습니다)를 사용하면 더 좋아요."
                feedback_en = "Polite speech is acceptable, but formal speech would be better."
        elif expected == SpeechLevel.POLITE:
            if detected == SpeechLevel.INFORMAL:
                is_appropriate = False
                feedback_ko = "존댓말(-요)을 사용해 주세요."
                feedback_en = "Please use polite speech (-요 form)."
            elif detected == SpeechLevel.FORMAL:
                is_appropriate = True  # Being extra polite is fine
                feedback_ko = ""
                feedback_en = ""
        else:  # Expected informal
            if detected in [SpeechLevel.FORMAL, SpeechLevel.POLITE]:
                is_appropriate = True  # Being polite to friend is fine, but can be more casual
                feedback_ko = "친한 사이니까 반말로 편하게 말해도 돼요! 😊"
                feedback_en = "We're close, so you can speak casually!"
        
        result.is_appropriate = is_appropriate
        result.feedback_ko = feedback_ko
        result.feedback_en = feedback_en
        
        return result


# ===========================================
# SINGLETON INSTANCE
# ===========================================

_analyzer: Optional[SimpleSpeechAnalyzer] = None


def get_speech_analyzer() -> SimpleSpeechAnalyzer:
    """Get or create the speech analyzer."""
    global _analyzer
    if _analyzer is None:
        _analyzer = SimpleSpeechAnalyzer()
    return _analyzer


def analyze_speech_level(text: str) -> Dict[str, Any]:
    """Convenience function to analyze speech level."""
    analyzer = get_speech_analyzer()
    result = analyzer.analyze(text)
    
    return {
        "text": result.text,
        "speech_level": result.speech_level.value,
        "speech_level_ko": result.speech_level_ko,
        "speech_level_en": result.speech_level_en,
        "confidence": result.confidence,
        "matched_patterns": result.matched_patterns
    }


def check_appropriateness(
    text: str,
    expected_level: str,
    avatar_role: str = None
) -> Dict[str, Any]:
    """Convenience function to check appropriateness."""
    analyzer = get_speech_analyzer()
    result = analyzer.check_appropriateness(text, expected_level, avatar_role)
    
    return {
        "text": result.text,
        "speech_level": result.speech_level.value,
        "speech_level_ko": result.speech_level_ko,
        "expected_level": expected_level,
        "is_appropriate": result.is_appropriate,
        "feedback_ko": result.feedback_ko,
        "feedback_en": result.feedback_en,
        "confidence": result.confidence
    }
