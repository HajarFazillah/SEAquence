"""
Enhanced Politeness Analysis Service
With word-level analysis, corrections, and error categorization
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

from app.core.constants import (
    ENDING_PATTERNS,
    HONORIFIC_WORDS,
    ROLE_LEVELS,
)
from app.core.corrections import (
    INFORMAL_TO_POLITE,
    POLITE_TO_FORMAL,
    INFORMAL_TO_FORMAL,
    HONORIFIC_VERBS,
    WORD_FORMALITY,
    ERROR_CATEGORIES,
    get_correction,
    get_honorific_form,
    get_formal_word,
)

logger = logging.getLogger(__name__)


# ===========================================
# Data Classes for Structured Output
# ===========================================

@dataclass
class WordAnalysis:
    """Analysis of a single word."""
    word: str
    position_start: int
    position_end: int
    current_level: str  # informal, polite, very_polite, neutral, honorific
    expected_level: Optional[str]
    is_correct: bool
    suggestion: Optional[str]
    error_type: Optional[str]


@dataclass
class Correction:
    """Suggested correction."""
    original: str
    corrected: str
    reason_ko: str
    reason_en: str
    position_start: int
    position_end: int


@dataclass
class ErrorDetail:
    """Categorized error."""
    error_type: str
    name_ko: str
    name_en: str
    severity: str  # high, medium, low
    count: int
    examples: List[str]


@dataclass
class EnhancedPolitenessResult:
    """Complete politeness analysis result."""
    # Basic info
    level: str
    level_ko: str
    level_en: str
    score: int
    is_appropriate: bool
    
    # Level breakdown
    level_breakdown: Dict[str, float]
    
    # Word-level analysis
    word_analysis: List[Dict]
    
    # Corrections
    corrections: List[Dict]
    
    # Error summary
    errors: List[Dict]
    
    # Feedback
    recommended_level: Optional[str]
    feedback_ko: Optional[str]
    feedback_en: Optional[str]
    
    # Original details
    details: Dict[str, Any]


# ===========================================
# Enhanced Politeness Service
# ===========================================

class EnhancedPolitenessService:
    """
    Enhanced service for analyzing Korean politeness/formality levels.
    
    Features:
    - Word-level analysis with positions
    - Specific correction suggestions
    - Error categorization
    - Level breakdown (formal/polite/informal ratios)
    """
    
    def __init__(self):
        self._compile_patterns()
        self._build_word_level_map()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns."""
        self._compiled_patterns = {}
        for level, patterns in ENDING_PATTERNS.items():
            self._compiled_patterns[level] = [
                re.compile(p) for p in patterns
            ]
    
    def _build_word_level_map(self):
        """Build mapping of words to their formality level."""
        self._word_levels = {}
        
        # Informal endings/words
        informal_markers = ["해", "가", "와", "먹어", "있어", "없어", "했어", "뭐해", "해줘"]
        for word in informal_markers:
            self._word_levels[word] = "informal"
        
        # Polite endings/words
        polite_markers = ["해요", "가요", "와요", "먹어요", "있어요", "없어요", "했어요", "주세요"]
        for word in polite_markers:
            self._word_levels[word] = "polite"
        
        # Formal endings/words
        formal_markers = ["합니다", "갑니다", "옵니다", "있습니다", "없습니다", "했습니다", "주십시오"]
        for word in formal_markers:
            self._word_levels[word] = "very_polite"
        
        # Honorific markers
        for word in HONORIFIC_WORDS.keys():
            self._word_levels[word] = "honorific"
    
    def analyze(
        self,
        text: str,
        target_role: Optional[str] = None,
        target_age: Optional[int] = None,
        user_age: int = 22
    ) -> EnhancedPolitenessResult:
        """
        Perform enhanced politeness analysis.
        
        Args:
            text: Korean text to analyze
            target_role: Role of person being addressed
            target_age: Age of person being addressed
            user_age: Age of speaker
            
        Returns:
            EnhancedPolitenessResult with all analysis details
        """
        # Get expected level based on relationship
        expected_level = self._get_expected_level(target_role, target_age, user_age)
        
        # Tokenize and analyze each word
        word_analyses = self._analyze_words(text, expected_level)
        
        # Calculate level breakdown
        level_breakdown = self._calculate_level_breakdown(word_analyses)
        
        # Determine dominant level
        dominant_level = self._get_dominant_level(level_breakdown)
        
        # Generate corrections
        corrections = self._generate_corrections(text, word_analyses, expected_level)
        
        # Categorize errors
        errors = self._categorize_errors(word_analyses)
        
        # Calculate score
        score = self._calculate_score(
            dominant_level, 
            expected_level, 
            level_breakdown,
            len(errors)
        )
        
        # Check appropriateness
        is_appropriate = self._check_appropriateness(dominant_level, expected_level)
        
        # Generate feedback
        feedback_ko, feedback_en = self._generate_feedback(
            dominant_level, 
            expected_level, 
            target_role,
            errors
        )
        
        level_names = {
            "informal": ("반말", "Informal"),
            "polite": ("존댓말", "Polite"),
            "very_polite": ("격식체", "Formal"),
            "mixed": ("혼용체", "Mixed"),
        }
        
        return EnhancedPolitenessResult(
            level=dominant_level,
            level_ko=level_names.get(dominant_level, ("", ""))[0],
            level_en=level_names.get(dominant_level, ("", ""))[1],
            score=score,
            is_appropriate=is_appropriate,
            level_breakdown=level_breakdown,
            word_analysis=[asdict(w) for w in word_analyses],
            corrections=[asdict(c) for c in corrections],
            errors=[asdict(e) for e in errors],
            recommended_level=expected_level,
            feedback_ko=feedback_ko,
            feedback_en=feedback_en,
            details={
                "text_length": len(text),
                "word_count": len(word_analyses),
                "error_count": sum(e.count for e in errors)
            }
        )
    
    def _analyze_words(
        self, 
        text: str, 
        expected_level: str
    ) -> List[WordAnalysis]:
        """Analyze each word in the text."""
        analyses = []
        
        # Simple tokenization (space-based + ending detection)
        # In production, use KoNLPy for proper morphological analysis
        words = self._tokenize(text)
        
        position = 0
        for word in words:
            word_clean = word.strip()
            if not word_clean:
                continue
            
            # Find position in original text
            start = text.find(word_clean, position)
            end = start + len(word_clean)
            position = end
            
            # Detect word level
            current_level = self._detect_word_level(word_clean)
            
            # Check if correct for expected level
            is_correct = self._is_word_correct(current_level, expected_level)
            
            # Get suggestion if incorrect
            suggestion = None
            error_type = None
            
            if not is_correct and current_level != "neutral":
                suggestion = self._get_suggestion(word_clean, current_level, expected_level)
                error_type = self._get_error_type(current_level, expected_level)
            
            analyses.append(WordAnalysis(
                word=word_clean,
                position_start=start,
                position_end=end,
                current_level=current_level,
                expected_level=expected_level if current_level != "neutral" else None,
                is_correct=is_correct,
                suggestion=suggestion,
                error_type=error_type
            ))
        
        return analyses
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for Korean text."""
        # Split by spaces and punctuation
        tokens = re.findall(r'[\w가-힣]+|[^\s\w]', text)
        return tokens
    
    def _detect_word_level(self, word: str) -> str:
        """Detect formality level of a word."""
        # Check direct mapping
        if word in self._word_levels:
            return self._word_levels[word]
        
        # Check endings
        for level, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(word):
                    return level
        
        # Check if contains honorific
        for hon_word in HONORIFIC_WORDS.keys():
            if hon_word in word:
                return "honorific"
        
        return "neutral"
    
    def _is_word_correct(self, current: str, expected: str) -> bool:
        """Check if word level is appropriate for expected level."""
        if current == "neutral":
            return True
        if current == "honorific":
            return True  # Honorifics are always good for formal situations
        
        level_order = {"informal": 0, "polite": 1, "very_polite": 2}
        current_val = level_order.get(current, 1)
        expected_val = level_order.get(expected, 1)
        
        # Current should be >= expected (being more polite is OK)
        return current_val >= expected_val
    
    def _get_suggestion(self, word: str, current: str, expected: str) -> Optional[str]:
        """Get correction suggestion for a word."""
        if current == "informal" and expected == "polite":
            return INFORMAL_TO_POLITE.get(word)
        elif current == "informal" and expected == "very_polite":
            return INFORMAL_TO_FORMAL.get(word)
        elif current == "polite" and expected == "very_polite":
            return POLITE_TO_FORMAL.get(word)
        return None
    
    def _get_error_type(self, current: str, expected: str) -> str:
        """Determine error type based on mismatch."""
        if current in ["informal", "polite", "very_polite"]:
            return "ending_mismatch"
        return "tone_inappropriate"
    
    def _calculate_level_breakdown(self, analyses: List[WordAnalysis]) -> Dict[str, float]:
        """Calculate ratio of each formality level."""
        counts = {"informal": 0, "polite": 0, "very_polite": 0, "honorific": 0}
        
        for a in analyses:
            if a.current_level in counts:
                counts[a.current_level] += 1
        
        total = sum(counts.values())
        if total == 0:
            return {"informal": 0, "polite": 0, "very_polite": 0, "honorific": 0}
        
        return {
            level: round(count / total, 2)
            for level, count in counts.items()
        }
    
    def _get_dominant_level(self, breakdown: Dict[str, float]) -> str:
        """Determine dominant formality level."""
        # Check for mixed
        non_zero = [l for l, v in breakdown.items() if v > 0 and l != "honorific"]
        if len(non_zero) > 1:
            # Check if significantly mixed
            values = [breakdown[l] for l in non_zero]
            if min(values) > 0.2:
                return "mixed"
        
        # Return highest non-honorific level
        if breakdown.get("very_polite", 0) > 0:
            return "very_polite"
        elif breakdown.get("polite", 0) > 0:
            return "polite"
        elif breakdown.get("informal", 0) > 0:
            return "informal"
        
        return "polite"  # default
    
    def _generate_corrections(
        self, 
        text: str,
        analyses: List[WordAnalysis],
        expected_level: str
    ) -> List[Correction]:
        """Generate specific corrections."""
        corrections = []
        
        for a in analyses:
            if not a.is_correct and a.suggestion:
                reason_ko, reason_en = self._get_correction_reason(
                    a.current_level, expected_level
                )
                
                corrections.append(Correction(
                    original=a.word,
                    corrected=a.suggestion,
                    reason_ko=reason_ko,
                    reason_en=reason_en,
                    position_start=a.position_start,
                    position_end=a.position_end
                ))
        
        return corrections
    
    def _get_correction_reason(self, current: str, expected: str) -> Tuple[str, str]:
        """Get explanation for why correction is needed."""
        reasons = {
            ("informal", "polite"): (
                "반말 대신 존댓말(-요)을 사용하세요",
                "Use polite speech (-요) instead of informal"
            ),
            ("informal", "very_polite"): (
                "반말 대신 격식체(-습니다)를 사용하세요",
                "Use formal speech (-습니다) instead of informal"
            ),
            ("polite", "very_polite"): (
                "존댓말 대신 격식체(-습니다)를 사용하세요",
                "Use formal speech (-습니다) instead of polite"
            ),
        }
        return reasons.get((current, expected), ("", ""))
    
    def _categorize_errors(self, analyses: List[WordAnalysis]) -> List[ErrorDetail]:
        """Categorize all errors found."""
        error_counts: Dict[str, List[str]] = {}
        
        for a in analyses:
            if a.error_type:
                if a.error_type not in error_counts:
                    error_counts[a.error_type] = []
                error_counts[a.error_type].append(f"{a.word} → {a.suggestion or '?'}")
        
        errors = []
        for error_type, examples in error_counts.items():
            info = ERROR_CATEGORIES.get(error_type, {})
            errors.append(ErrorDetail(
                error_type=error_type,
                name_ko=info.get("name_ko", error_type),
                name_en=info.get("name_en", error_type),
                severity=info.get("severity", "medium"),
                count=len(examples),
                examples=examples[:3]  # Limit to 3 examples
            ))
        
        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        errors.sort(key=lambda e: severity_order.get(e.severity, 1))
        
        return errors
    
    def _calculate_score(
        self,
        dominant: str,
        expected: str,
        breakdown: Dict[str, float],
        error_count: int
    ) -> int:
        """Calculate politeness score (0-100)."""
        base_score = 50
        
        # Match bonus
        level_order = {"informal": 0, "polite": 1, "very_polite": 2}
        dominant_val = level_order.get(dominant, 1)
        expected_val = level_order.get(expected, 1)
        
        if dominant_val >= expected_val:
            base_score += 30
        elif dominant_val == expected_val - 1:
            base_score += 10
        else:
            base_score -= 10
        
        # Consistency bonus
        max_ratio = max(breakdown.get("informal", 0), 
                       breakdown.get("polite", 0), 
                       breakdown.get("very_polite", 0))
        if max_ratio > 0.8:
            base_score += 15  # Consistent usage
        elif max_ratio < 0.5:
            base_score -= 10  # Too mixed
        
        # Error penalty
        base_score -= min(error_count * 5, 20)
        
        # Honorific bonus
        if breakdown.get("honorific", 0) > 0:
            base_score += 5
        
        return max(0, min(100, base_score))
    
    def _check_appropriateness(self, actual: str, expected: str) -> bool:
        """Check if actual level is appropriate."""
        if actual == "mixed":
            return False
        
        level_order = {"informal": 0, "polite": 1, "very_polite": 2}
        return level_order.get(actual, 1) >= level_order.get(expected, 1)
    
    def _get_expected_level(
        self,
        target_role: Optional[str],
        target_age: Optional[int],
        user_age: int
    ) -> str:
        """Determine expected formality level."""
        if not target_role:
            return "polite"
        
        target_level = ROLE_LEVELS.get(target_role.lower(), 1)
        
        if target_level >= 3:  # professor, boss
            return "very_polite"
        elif target_level >= 2:  # senior
            return "polite"
        else:
            return "informal"
    
    def _generate_feedback(
        self,
        actual: str,
        expected: str,
        target_role: Optional[str],
        errors: List[ErrorDetail]
    ) -> Tuple[Optional[str], Optional[str]]:
        """Generate feedback message."""
        if actual == expected or self._check_appropriateness(actual, expected):
            return (
                "잘했어요! 적절한 말투를 사용했습니다.",
                "Great job! You used appropriate speech level."
            )
        
        level_names_ko = {
            "informal": "반말",
            "polite": "존댓말(-요)",
            "very_polite": "격식체(-습니다)",
            "mixed": "혼용체"
        }
        
        role_names_ko = {
            "professor": "교수님",
            "boss": "상사",
            "senior": "선배",
            "friend": "친구",
            "junior": "후배",
        }
        
        role_ko = role_names_ko.get(target_role, target_role) if target_role else "상대방"
        expected_ko = level_names_ko.get(expected, expected)
        actual_ko = level_names_ko.get(actual, actual)
        
        feedback_ko = f"{role_ko}에게는 {expected_ko}를 사용하세요. 현재 {actual_ko}를 사용하고 있습니다."
        
        # Add specific error feedback
        if errors:
            top_error = errors[0]
            feedback_ko += f" ({top_error.name_ko} 오류 {top_error.count}개)"
        
        feedback_en = f"Use {expected} speech with {target_role}. Currently using {actual}."
        
        return feedback_ko, feedback_en


# Singleton instance
enhanced_politeness_service = EnhancedPolitenessService()
