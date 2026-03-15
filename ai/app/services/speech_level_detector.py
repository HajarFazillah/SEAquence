"""
Comprehensive Korean Speech Level Detection
Detects 반말, 해요체, 합니다체 with detailed pattern analysis
"""

import re
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class SpeechLevel(str, Enum):
    """Korean speech levels"""
    FORMAL = "formal"           # 격식체 / 합니다체
    POLITE = "polite"           # 해요체
    INFORMAL = "informal"       # 반말
    MIXED = "mixed"             # 혼용
    UNKNOWN = "unknown"


@dataclass
class SpeechLevelResult:
    """Result of speech level analysis"""
    level: SpeechLevel
    confidence: float           # 0.0 - 1.0
    detected_patterns: List[str]
    honorific_score: int
    details: Dict[str, Any]


class KoreanSpeechLevelDetector:
    """
    Comprehensive Korean speech level detector.
    
    Analyzes:
    1. Sentence endings (어미)
    2. Honorific markers (-시-)
    3. Honorific vocabulary
    4. Honorific particles (께서, 께)
    5. Speech style consistency
    """
    
    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile all regex patterns for efficiency."""
        
        # ===========================================
        # 1. SENTENCE ENDINGS (어미)
        # ===========================================
        
        # 격식체 / 합니다체 (Formal)
        self.formal_endings = [
            # Statement endings
            (r"습니다[.!]?$", "습니다 ending"),
            (r"ㅂ니다[.!]?$", "ㅂ니다 ending"),
            (r"입니다[.!]?$", "입니다 ending"),
            (r"옵니다[.!]?$", "옵니다 ending (archaic)"),
            (r"나이다[.!]?$", "나이다 ending (archaic)"),
            
            # Question endings
            (r"습니까[?]?$", "습니까 question"),
            (r"ㅂ니까[?]?$", "ㅂ니까 question"),
            (r"입니까[?]?$", "입니까 question"),
            
            # Imperative/Request endings
            (r"십시오[.!]?$", "십시오 imperative"),
            (r"십시요[.!]?$", "십시요 (variant)"),
            (r"시오[.!]?$", "시오 imperative"),
            (r"시기 바랍니다[.!]?$", "시기 바랍니다"),
            
            # Propositive endings
            (r"ㅂ시다[.!]?$", "ㅂ시다 propositive"),
            (r"읍시다[.!]?$", "읍시다 propositive"),
        ]
        
        # 해요체 (Polite)
        self.polite_endings = [
            # Basic -요 endings
            (r"해요[.?!]?$", "해요 ending"),
            (r"[아어]요[.?!]?$", "아요/어요 ending"),
            (r"여요[.?!]?$", "여요 ending"),
            (r"이에요[.?!]?$", "이에요 ending"),
            (r"예요[.?!]?$", "예요 ending"),
            (r"에요[.?!]?$", "에요 ending"),
            
            # -세요 endings (honorific + polite)
            (r"세요[.?!]?$", "세요 ending"),
            (r"으세요[.?!]?$", "으세요 ending"),
            (r"시어요[.?!]?$", "시어요 ending"),
            (r"셔요[.?!]?$", "셔요 ending"),
            
            # -죠 endings (contraction of -지요)
            (r"죠[.?!]?$", "죠 ending"),
            (r"지요[.?!]?$", "지요 ending"),
            
            # Exclamatory endings
            (r"네요[.!]?$", "네요 exclamatory"),
            (r"군요[.!]?$", "군요 exclamatory"),
            (r"구나요[.!]?$", "구나요 exclamatory"),
            
            # Reason/Cause endings
            (r"거든요[.!]?$", "거든요 reason"),
            (r"잖아요[.?!]?$", "잖아요"),
            (r"니까요[.?!]?$", "니까요 reason"),
            (r"서요[.?!]?$", "서요 reason"),
            
            # Question endings
            (r"나요[?]?$", "나요 question"),
            (r"가요[?]?$", "가요 question"),
            (r"ㄴ가요[?]?$", "ㄴ가요 question"),
            (r"던가요[?]?$", "던가요 question"),
            (r"래요[?]?$", "래요 question"),
            (r"을까요[?]?$", "을까요 question"),
            (r"ㄹ까요[?]?$", "ㄹ까요 question"),
            
            # Other polite endings
            (r"ㄴ데요[.?!]?$", "ㄴ데요"),
            (r"는데요[.?!]?$", "는데요"),
            (r"던데요[.?!]?$", "던데요"),
            (r"더라고요[.!]?$", "더라고요 retrospective"),
            (r"다고요[.?!]?$", "다고요 quotative"),
            (r"래요[.!]?$", "래요"),
            (r"대요[.!]?$", "대요 hearsay"),
            (r"ㄹ게요[.!]?$", "ㄹ게요 promise"),
            (r"을게요[.!]?$", "을게요 promise"),
            (r"ㄹ래요[.?!]?$", "ㄹ래요 intention"),
            (r"을래요[.?!]?$", "을래요 intention"),
        ]
        
        # 반말 (Informal)
        self.informal_endings = [
            # Basic informal endings
            (r"해[.?!]?$", "해 ending"),
            (r"[아어][.?!]?$", "아/어 ending"),
            (r"여[.?!]?$", "여 ending"),
            (r"야[.?!]?$", "야 ending"),
            (r"이야[.?!]?$", "이야 ending"),
            
            # Question endings
            (r"니[?]?$", "니 question"),
            (r"냐[?]?$", "냐 question"),
            (r"나[?]?$", "나 question"),
            (r"가[?]?$", "가 question"),
            (r"ㄴ가[?]?$", "ㄴ가 question"),
            (r"던가[?]?$", "던가 question"),
            (r"래[?]?$", "래 question"),
            (r"ㄹ래[?]?$", "ㄹ래 question"),
            (r"을래[?]?$", "을래 question"),
            (r"ㄹ까[?]?$", "ㄹ까 question"),
            (r"을까[?]?$", "을까 question"),
            
            # Exclamatory endings
            (r"네[.!]?$", "네 exclamatory"),
            (r"군[.!]?$", "군 exclamatory"),
            (r"구나[.!]?$", "구나 exclamatory"),
            (r"구만[.!]?$", "구만 exclamatory"),
            (r"다니[.!]?$", "다니 exclamatory"),
            
            # Statement endings
            (r"지[.?!]?$", "지 ending"),
            (r"잖아[.?!]?$", "잖아"),
            (r"거든[.!]?$", "거든"),
            (r"걸[.!]?$", "걸"),
            
            # Reason/Cause
            (r"서[.?!]?$", "서 reason"),
            (r"니까[.?!]?$", "니까 reason"),
            
            # Other informal
            (r"는데[.?!]?$", "는데"),
            (r"ㄴ데[.?!]?$", "ㄴ데"),
            (r"던데[.?!]?$", "던데"),
            (r"더라[.!]?$", "더라 retrospective"),
            (r"다고[.?!]?$", "다고 quotative"),
            (r"대[.!]?$", "대 hearsay"),
            (r"ㄹ게[.!]?$", "ㄹ게 promise"),
            (r"을게[.!]?$", "을게 promise"),
            
            # Imperative informal
            (r"해라[.!]?$", "해라 imperative"),
            (r"[아어]라[.!]?$", "아라/어라 imperative"),
            (r"여라[.!]?$", "여라 imperative"),
            
            # Plain form (written)
            (r"다[.]?$", "다 plain ending"),
            (r"ㄴ다[.]?$", "ㄴ다 plain ending"),
            (r"는다[.]?$", "는다 plain ending"),
        ]
        
        # ===========================================
        # 2. HONORIFIC SUFFIX (-시-)
        # ===========================================
        
        self.honorific_suffix_patterns = [
            (r"시[어아]", "시어/시아 honorific"),
            (r"셔", "셔 (contracted 시어)"),
            (r"시[었았]", "시었/시았 past honorific"),
            (r"셨", "셨 (contracted 시었)"),
            (r"시[겠]", "시겠 future/polite honorific"),
            (r"실", "실 (시+ㄹ)"),
            (r"시[ㄴ는]", "시ㄴ/시는 modifier honorific"),
            (r"신", "신 (contracted 시ㄴ)"),
            (r"십", "십 formal honorific"),
            (r"세요", "세요 polite honorific"),
            (r"시죠", "시죠 polite honorific"),
            (r"시네", "시네 exclamatory honorific"),
            (r"시군", "시군 exclamatory honorific"),
        ]
        
        # ===========================================
        # 3. HONORIFIC PARTICLES
        # ===========================================
        
        self.honorific_particles = {
            "께서": ("subject honorific particle", 15),
            "께": ("dative honorific particle", 10),
            "께서는": ("subject honorific + topic", 15),
            "께도": ("honorific + also", 10),
        }
        
        # ===========================================
        # 4. HONORIFIC VOCABULARY
        # ===========================================
        
        self.honorific_vocabulary = {
            # Special honorific verbs (높임말 동사)
            "드리다": ("give (humble)", 15),
            "올리다": ("give/submit (humble)", 10),
            "여쭙다": ("ask (humble)", 15),
            "여쭤보다": ("ask (humble)", 15),
            "여쭤": ("ask (humble, contracted)", 12),
            "뵙다": ("see/meet (humble)", 15),
            "뵈다": ("see/meet (humble)", 15),
            "모시다": ("serve/accompany (humble)", 12),
            "말씀드리다": ("speak (humble)", 15),
            "아뢰다": ("report (humble, archaic)", 12),
            
            # Special honorific verbs (존경어 동사)
            "계시다": ("exist/be (honorific)", 15),
            "주무시다": ("sleep (honorific)", 15),
            "잡수시다": ("eat (honorific)", 15),
            "드시다": ("eat/drink (honorific)", 15),
            "돌아가시다": ("pass away (honorific)", 12),
            "편찮으시다": ("be unwell (honorific)", 12),
            
            # Honorific nouns
            "말씀": ("words (honorific)", 10),
            "성함": ("name (honorific)", 12),
            "연세": ("age (honorific)", 12),
            "진지": ("meal (honorific)", 10),
            "댁": ("home (honorific)", 8),
            "병환": ("illness (honorific)", 10),
            "기체": ("health (honorific)", 8),
            "존함": ("name (very honorific)", 12),
            "옥체": ("body (very honorific)", 10),
            "어르신": ("elder (honorific)", 10),
            "선생님": ("teacher (honorific)", 8),
            "교수님": ("professor (honorific)", 8),
            "사장님": ("CEO (honorific)", 8),
            "부장님": ("department head (honorific)", 8),
            
            # Polite expressions
            "실례": ("excuse (polite)", 5),
            "죄송": ("sorry (polite)", 5),
            "감사": ("thanks (polite)", 5),
            "혹시": ("perhaps (polite softener)", 3),
            "부디": ("please (earnest)", 5),
            "아무쪼록": ("by all means", 5),
        }
        
        # ===========================================
        # 5. INFORMAL VOCABULARY
        # ===========================================
        
        self.informal_vocabulary = {
            # Informal pronouns
            "나": ("I (informal)", -3),
            "너": ("you (informal)", -5),
            "넌": ("you (contracted)", -5),
            "난": ("I (contracted)", -3),
            "얘": ("this kid/person", -5),
            "걔": ("that kid/person", -5),
            "쟤": ("that kid/person over there", -5),
            
            # Informal address
            "야": ("hey", -5),
            "임마": ("hey (rough)", -8),
            "이놈": ("you (rough)", -10),
            
            # Informal expressions
            "뭐": ("what (informal)", -2),
            "왜": ("why (can be informal)", -1),
            "응": ("yeah", -3),
            "어": ("uh/yeah", -3),
            "그래": ("okay/yeah", -2),
        }
        
        # Compile regex patterns
        self.compiled_formal = [(re.compile(p), d) for p, d in self.formal_endings]
        self.compiled_polite = [(re.compile(p), d) for p, d in self.polite_endings]
        self.compiled_informal = [(re.compile(p), d) for p, d in self.informal_endings]
        self.compiled_honorific_suffix = [(re.compile(p), d) for p, d in self.honorific_suffix_patterns]
    
    def detect(self, text: str) -> SpeechLevelResult:
        """
        Detect the speech level of Korean text.
        
        Args:
            text: Korean text to analyze
            
        Returns:
            SpeechLevelResult with level, confidence, and details
        """
        # Split into sentences
        sentences = self._split_sentences(text)
        
        # Analyze each component
        ending_results = self._analyze_endings(sentences)
        honorific_suffix_count = self._count_honorific_suffixes(text)
        honorific_vocab_score = self._score_honorific_vocabulary(text)
        particle_score = self._score_honorific_particles(text)
        informal_vocab_score = self._score_informal_vocabulary(text)
        
        # Calculate total honorific score
        total_honorific = (
            honorific_suffix_count * 5 +
            honorific_vocab_score +
            particle_score +
            informal_vocab_score  # This is negative for informal
        )
        
        # Determine speech level
        level, confidence = self._determine_level(
            ending_results,
            total_honorific
        )
        
        # Compile detected patterns
        detected_patterns = []
        for level_name, patterns in ending_results.items():
            for pattern in patterns:
                detected_patterns.append(f"[{level_name}] {pattern}")
        
        return SpeechLevelResult(
            level=level,
            confidence=confidence,
            detected_patterns=detected_patterns,
            honorific_score=total_honorific,
            details={
                "ending_analysis": ending_results,
                "honorific_suffix_count": honorific_suffix_count,
                "honorific_vocab_score": honorific_vocab_score,
                "particle_score": particle_score,
                "informal_vocab_score": informal_vocab_score,
                "sentences_analyzed": len(sentences)
            }
        )
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Split by common sentence endings
        sentences = re.split(r'[.?!]\s*', text)
        # Filter empty strings
        return [s.strip() for s in sentences if s.strip()]
    
    def _analyze_endings(self, sentences: List[str]) -> Dict[str, List[str]]:
        """Analyze sentence endings."""
        results = {
            "formal": [],
            "polite": [],
            "informal": []
        }
        
        for sentence in sentences:
            # Check formal endings
            for pattern, desc in self.compiled_formal:
                if pattern.search(sentence):
                    results["formal"].append(desc)
                    break
            else:
                # Check polite endings
                for pattern, desc in self.compiled_polite:
                    if pattern.search(sentence):
                        results["polite"].append(desc)
                        break
                else:
                    # Check informal endings
                    for pattern, desc in self.compiled_informal:
                        if pattern.search(sentence):
                            results["informal"].append(desc)
                            break
        
        return results
    
    def _count_honorific_suffixes(self, text: str) -> int:
        """Count honorific suffix (-시-) occurrences."""
        count = 0
        for pattern, desc in self.compiled_honorific_suffix:
            count += len(pattern.findall(text))
        return count
    
    def _score_honorific_vocabulary(self, text: str) -> int:
        """Score honorific vocabulary usage."""
        score = 0
        for word, (desc, points) in self.honorific_vocabulary.items():
            if word in text:
                score += points
        return score
    
    def _score_honorific_particles(self, text: str) -> int:
        """Score honorific particle usage."""
        score = 0
        for particle, (desc, points) in self.honorific_particles.items():
            if particle in text:
                score += points
        return score
    
    def _score_informal_vocabulary(self, text: str) -> int:
        """Score informal vocabulary usage (returns negative)."""
        score = 0
        for word, (desc, points) in self.informal_vocabulary.items():
            if word in text:
                score += points  # points are already negative
        return score
    
    def _determine_level(
        self,
        ending_results: Dict[str, List[str]],
        honorific_score: int
    ) -> Tuple[SpeechLevel, float]:
        """Determine overall speech level."""
        
        formal_count = len(ending_results["formal"])
        polite_count = len(ending_results["polite"])
        informal_count = len(ending_results["informal"])
        total = formal_count + polite_count + informal_count
        
        if total == 0:
            return SpeechLevel.UNKNOWN, 0.0
        
        # Calculate ratios
        formal_ratio = formal_count / total
        polite_ratio = polite_count / total
        informal_ratio = informal_count / total
        
        # Check for mixed usage
        levels_used = sum([
            1 if formal_count > 0 else 0,
            1 if polite_count > 0 else 0,
            1 if informal_count > 0 else 0
        ])
        
        if levels_used > 1 and max(formal_ratio, polite_ratio, informal_ratio) < 0.7:
            return SpeechLevel.MIXED, 0.5
        
        # Determine dominant level
        if formal_ratio >= polite_ratio and formal_ratio >= informal_ratio:
            confidence = formal_ratio
            # Boost confidence with high honorific score
            if honorific_score > 20:
                confidence = min(1.0, confidence + 0.1)
            return SpeechLevel.FORMAL, confidence
        
        elif polite_ratio >= formal_ratio and polite_ratio >= informal_ratio:
            confidence = polite_ratio
            # Boost with honorific score
            if honorific_score > 10:
                confidence = min(1.0, confidence + 0.1)
            return SpeechLevel.POLITE, confidence
        
        else:
            confidence = informal_ratio
            # Reduce confidence if some honorifics present
            if honorific_score > 5:
                confidence = max(0.5, confidence - 0.1)
            return SpeechLevel.INFORMAL, confidence
    
    def get_expected_level_for_situation(self, situation_id: str) -> SpeechLevel:
        """Get expected speech level for a situation."""
        formal_situations = ["professor_office", "job_interview", "office_meeting"]
        polite_situations = ["cafe_order", "restaurant_order", "shopping", 
                            "campus_meetup", "group_project", "first_meeting"]
        informal_situations = ["cafe_chat", "party"]
        
        if situation_id in formal_situations:
            return SpeechLevel.FORMAL
        elif situation_id in polite_situations:
            return SpeechLevel.POLITE
        elif situation_id in informal_situations:
            return SpeechLevel.INFORMAL
        else:
            return SpeechLevel.POLITE  # Default
    
    def check_appropriateness(
        self,
        detected: SpeechLevel,
        expected: SpeechLevel
    ) -> Tuple[bool, str]:
        """
        Check if detected level is appropriate for expected.
        
        Returns:
            (is_appropriate, feedback_message)
        """
        if detected == expected:
            return True, ""
        
        if detected == SpeechLevel.MIXED:
            return False, "말투가 섞여 있어요. 하나로 통일해 주세요."
        
        if detected == SpeechLevel.UNKNOWN:
            return True, ""  # Can't determine, assume OK
        
        # Level mismatch feedback
        feedback_map = {
            (SpeechLevel.INFORMAL, SpeechLevel.FORMAL): 
                "격식체(-습니다)를 사용해야 하는 상황이에요.",
            (SpeechLevel.INFORMAL, SpeechLevel.POLITE): 
                "'-요'를 붙여서 존댓말로 말해 주세요.",
            (SpeechLevel.POLITE, SpeechLevel.FORMAL): 
                "이 상황에서는 격식체(-습니다)가 더 적절해요.",
            (SpeechLevel.POLITE, SpeechLevel.INFORMAL): 
                "친한 사이니까 반말로 편하게 말해도 돼요!",
            (SpeechLevel.FORMAL, SpeechLevel.POLITE): 
                "해요체(-어요)로 조금 더 편하게 말해도 괜찮아요.",
            (SpeechLevel.FORMAL, SpeechLevel.INFORMAL): 
                "반말로 편하게 말해도 돼요!",
        }
        
        feedback = feedback_map.get((detected, expected), "말투를 확인해 주세요.")
        return False, feedback


# Singleton instance
speech_level_detector = KoreanSpeechLevelDetector()


# ===========================================
# Quick Helper Functions
# ===========================================

def detect_speech_level(text: str) -> Dict[str, Any]:
    """Quick function to detect speech level."""
    result = speech_level_detector.detect(text)
    return {
        "level": result.level.value,
        "confidence": result.confidence,
        "detected_patterns": result.detected_patterns,
        "honorific_score": result.honorific_score,
        "details": result.details
    }


def is_appropriate_for_situation(text: str, situation_id: str) -> Dict[str, Any]:
    """Check if text is appropriate for situation."""
    result = speech_level_detector.detect(text)
    expected = speech_level_detector.get_expected_level_for_situation(situation_id)
    is_ok, feedback = speech_level_detector.check_appropriateness(result.level, expected)
    
    return {
        "detected_level": result.level.value,
        "expected_level": expected.value,
        "is_appropriate": is_ok,
        "feedback": feedback,
        "confidence": result.confidence
    }
