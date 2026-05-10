"""
Politeness Analysis Service
Analyze Korean speech levels and formality
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple

from app.core.constants import (
    ENDING_PATTERNS,
    HONORIFIC_WORDS,
    ROLE_LEVELS,
    FormailtyLevel,
)

logger = logging.getLogger(__name__)


class PolitenessService:
    """
    Service for analyzing Korean politeness/formality levels.
    
    Detects:
    - Speech level (반말/존댓말/격식체)
    - Honorific words
    - Appropriateness for context
    """
    
    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for efficiency."""
        self._compiled_patterns = {}
        for level, patterns in ENDING_PATTERNS.items():
            self._compiled_patterns[level] = [
                re.compile(p) for p in patterns
            ]
    
    def analyze(
        self,
        text: str,
        target_role: Optional[str] = None,
        target_age: Optional[int] = None,
        user_age: int = 22
    ) -> Dict[str, Any]:
        """
        Analyze politeness level of Korean text.
        
        Args:
            text: Korean text to analyze
            target_role: Role of the person being addressed
            target_age: Age of the person being addressed
            user_age: Age of the speaker
            
        Returns:
            Dict with level, score, is_appropriate, feedback
        """
        # Split into sentences for analysis
        sentences = self._split_sentences(text)
        
        # Analyze each sentence
        level_counts = {"very_polite": 0, "polite": 0, "informal": 0}
        endings_found = []
        honorifics_found = []
        
        for sentence in sentences:
            sentence_level, ending = self._detect_sentence_level(sentence)
            if sentence_level:
                level_counts[sentence_level] += 1
                if ending:
                    endings_found.append(ending)
        
        # Check for honorific words
        honorific_score = 0
        for word, points in HONORIFIC_WORDS.items():
            if word in text:
                honorifics_found.append(word)
                honorific_score += points
        
        # Determine overall level
        dominant_level = self._get_dominant_level(level_counts, honorific_score)
        
        # Calculate score (0-100)
        score = self._calculate_score(dominant_level, honorific_score, level_counts)
        
        # Determine appropriateness
        is_appropriate = True
        recommended_level = None
        feedback_ko = None
        feedback_en = None
        
        if target_role:
            recommended_level = self._get_recommended_level(
                target_role, target_age, user_age
            )
            is_appropriate = self._check_appropriateness(
                dominant_level, recommended_level
            )
            
            if not is_appropriate:
                feedback_ko, feedback_en = self._generate_feedback(
                    dominant_level, recommended_level, target_role
                )
        
        level_names = {
            "informal": ("반말", "Informal"),
            "polite": ("존댓말", "Polite"),
            "very_polite": ("격식체", "Formal/Very Polite"),
        }
        
        return {
            "level": dominant_level,
            "level_ko": level_names[dominant_level][0],
            "level_en": level_names[dominant_level][1],
            "score": score,
            "is_appropriate": is_appropriate,
            "recommended_level": recommended_level,
            "feedback_ko": feedback_ko,
            "feedback_en": feedback_en,
            "details": {
                "level_counts": level_counts,
                "endings_found": endings_found[:5],
                "honorifics_found": honorifics_found[:5],
                "honorific_score": honorific_score,
            }
        }
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Korean sentence endings
        sentences = re.split(r'[.?!。？！]\s*', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _detect_sentence_level(self, sentence: str) -> Tuple[Optional[str], Optional[str]]:
        """Detect politeness level of a single sentence."""
        sentence = sentence.strip()
        if not sentence:
            return None, None
        
        # Check patterns in order of formality (most formal first)
        for level in ["very_polite", "polite", "informal"]:
            for pattern in self._compiled_patterns[level]:
                if pattern.search(sentence):
                    return level, pattern.pattern
        
        return None, None
    
    def _get_dominant_level(
        self,
        level_counts: Dict[str, int],
        honorific_score: int
    ) -> str:
        """Determine dominant politeness level."""
        # High honorific score suggests formal speech
        if honorific_score >= 15:
            return "very_polite"
        
        # Check counts
        if level_counts["very_polite"] > 0:
            return "very_polite"
        elif level_counts["polite"] > level_counts["informal"]:
            return "polite"
        elif level_counts["informal"] > 0:
            return "informal"
        else:
            return "polite"  # Default
    
    def _calculate_score(
        self,
        level: str,
        honorific_score: int,
        level_counts: Dict[str, int]
    ) -> int:
        """Calculate politeness score (0-100)."""
        base_scores = {
            "informal": 20,
            "polite": 60,
            "very_polite": 85,
        }
        
        score = base_scores.get(level, 50)
        
        # Add honorific bonus
        score += min(honorific_score, 15)
        
        # Consistency bonus
        total = sum(level_counts.values())
        if total > 0:
            dominant_ratio = level_counts[level] / total
            if dominant_ratio >= 0.8:
                score += 5  # Consistent usage bonus
        
        return min(100, max(0, score))
    
    def _get_recommended_level(
        self,
        target_role: str,
        target_age: Optional[int],
        user_age: int
    ) -> str:
        """Determine recommended formality level based on relationship."""
        target_level = ROLE_LEVELS.get(target_role.lower(), 1)
        user_level = ROLE_LEVELS.get("student", 0)  # Assume student
        
        power_distance = target_level - user_level
        
        # High status (professor, boss)
        if target_level >= 3:
            return "very_polite"
        
        # Senior or older
        if power_distance > 0:
            return "polite"
        
        # Age consideration
        if target_age and target_age > user_age + 3:
            return "polite"
        
        # Peer or junior
        if power_distance <= 0:
            return "informal"
        
        return "polite"
    
    def _check_appropriateness(
        self,
        actual: str,
        recommended: str
    ) -> bool:
        """Check if actual level is appropriate for recommended."""
        level_order = {"informal": 0, "polite": 1, "very_polite": 2}
        
        actual_val = level_order.get(actual, 1)
        recommended_val = level_order.get(recommended, 1)
        
        # Actual level should be >= recommended
        # Being more polite is always acceptable
        return actual_val >= recommended_val
    
    def _generate_feedback(
        self,
        actual: str,
        recommended: str,
        target_role: str
    ) -> Tuple[str, str]:
        """Generate feedback for inappropriate politeness level."""
        
        level_names_ko = {
            "informal": "반말",
            "polite": "존댓말(-요)",
            "very_polite": "격식체(-습니다)",
        }
        
        level_names_en = {
            "informal": "informal speech",
            "polite": "polite speech (-요)",
            "very_polite": "formal speech (-습니다)",
        }
        
        role_names_ko = {
            "professor": "교수님",
            "boss": "상사",
            "senior": "선배",
            "friend": "친구",
            "junior": "후배",
        }
        
        actual_ko = level_names_ko[actual]
        recommended_ko = level_names_ko[recommended]
        role_ko = role_names_ko.get(target_role.lower(), target_role)
        
        feedback_ko = f"{role_ko}에게는 {recommended_ko}를 사용하세요. 현재 {actual_ko}를 사용하고 있습니다."
        
        feedback_en = (
            f"Please use {level_names_en[recommended]} when speaking to "
            f"{target_role}. You are currently using {level_names_en[actual]}."
        )
        
        return feedback_ko, feedback_en
    
    def get_formality_tips(self, level: str) -> Dict[str, Any]:
        """Get tips for using a specific formality level."""
        tips = {
            "informal": {
                "name_ko": "반말",
                "name_en": "Informal",
                "usage": "친구, 후배, 어린 사람에게",
                "endings": ["-어/아", "-지", "-냐", "-야"],
                "examples": ["뭐해?", "밥 먹었어?", "같이 가자"],
            },
            "polite": {
                "name_ko": "존댓말",
                "name_en": "Polite",
                "usage": "선배, 처음 만난 사람, 약간 나이 많은 사람에게",
                "endings": ["-요", "-세요", "-죠"],
                "examples": ["뭐 해요?", "밥 먹었어요?", "같이 가요"],
            },
            "very_polite": {
                "name_ko": "격식체",
                "name_en": "Formal / Very Polite",
                "usage": "교수님, 상사, 공식적인 상황에서",
                "endings": ["-습니다", "-습니까", "-십시오"],
                "examples": ["무엇을 하십니까?", "식사하셨습니까?"],
                "honorifics": ["드리다", "여쭙다", "말씀", "뵙다", "계시다"],
            },
        }
        return tips.get(level, tips["polite"])


# Singleton instance
politeness_service = PolitenessService()
