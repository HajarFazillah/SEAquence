"""
Personalized Feedback Service
Generates adaptive feedback based on user's history and progress
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from app.schemas.user_schemas import (
    UserContext,
    PersonalizedFeedback,
)
from app.core.corrections import ERROR_CATEGORIES

logger = logging.getLogger(__name__)


class PersonalizedFeedbackService:
    """
    Service for generating personalized feedback.
    
    Takes into account:
    - User's error history (has user made this mistake before?)
    - User's skill level (adjust complexity of feedback)
    - User's progress trend (encouraging vs supportive)
    - User's preferences (language, hints)
    """
    
    def generate_feedback(
        self,
        analysis_result: Dict[str, Any],
        user_context: Optional[UserContext] = None,
        error_records: Optional[Dict[str, int]] = None
    ) -> PersonalizedFeedback:
        """
        Generate personalized feedback based on analysis and user context.
        
        Args:
            analysis_result: Result from politeness analysis
            user_context: User's context for personalization
            error_records: Dict of error_type -> count from user's history
            
        Returns:
            PersonalizedFeedback with adaptive messages
        """
        # Base feedback
        level = analysis_result.get("level", "polite")
        score = analysis_result.get("score", 50)
        is_appropriate = analysis_result.get("is_appropriate", True)
        
        # Use defaults if no context
        if not user_context:
            user_context = UserContext(
                user_id="anonymous",
                korean_level="intermediate"
            )
        
        # Generate personalized feedback text
        feedback_ko, feedback_en = self._generate_feedback_text(
            analysis_result,
            user_context,
            is_appropriate
        )
        
        # Generate error history note
        error_history_note = self._generate_error_history_note(
            analysis_result.get("errors", []),
            error_records,
            user_context.feedback_language
        )
        
        # Generate personalized tip
        tip_ko, tip_en = self._generate_tip(
            analysis_result,
            user_context
        )
        
        # Generate progress note
        progress_note = self._generate_progress_note(
            score,
            user_context
        )
        
        # Generate encouragement
        encouragement_ko, encouragement_en = self._generate_encouragement(
            score,
            is_appropriate,
            user_context
        )
        
        return PersonalizedFeedback(
            level=level,
            score=score,
            is_appropriate=is_appropriate,
            feedback_ko=feedback_ko,
            feedback_en=feedback_en,
            error_history_note=error_history_note,
            personalized_tip_ko=tip_ko,
            personalized_tip_en=tip_en,
            progress_note=progress_note,
            encouragement_ko=encouragement_ko,
            encouragement_en=encouragement_en
        )
    
    def _generate_feedback_text(
        self,
        analysis: Dict[str, Any],
        context: UserContext,
        is_appropriate: bool
    ) -> Tuple[str, str]:
        """Generate main feedback text."""
        level = analysis.get("level", "polite")
        recommended = analysis.get("recommended_level", "polite")
        
        level_names_ko = {
            "informal": "반말",
            "polite": "존댓말(-요)",
            "very_polite": "격식체(-습니다)",
            "mixed": "혼용체"
        }
        
        level_names_en = {
            "informal": "informal speech",
            "polite": "polite speech (-요)",
            "very_polite": "formal speech (-습니다)",
            "mixed": "mixed speech levels"
        }
        
        if is_appropriate:
            # Good job!
            if context.korean_level == "beginner":
                feedback_ko = f"잘했어요! 👏 {level_names_ko[level]}을 잘 사용했어요."
                feedback_en = f"Good job! 👏 You used {level_names_en[level]} correctly."
            elif context.korean_level == "advanced":
                feedback_ko = f"적절한 말투입니다. {level_names_ko[level]} 사용이 정확합니다."
                feedback_en = f"Appropriate speech level. Your use of {level_names_en[level]} is accurate."
            else:
                feedback_ko = f"좋아요! {level_names_ko[level]}을 올바르게 사용했어요."
                feedback_en = f"Nice! You correctly used {level_names_en[level]}."
        else:
            # Needs improvement
            current_ko = level_names_ko.get(level, level)
            expected_ko = level_names_ko.get(recommended, recommended)
            
            if context.korean_level == "beginner":
                feedback_ko = f"앗! {expected_ko}를 사용해보세요. 지금은 {current_ko}를 사용하고 있어요."
                feedback_en = f"Oops! Try using {level_names_en.get(recommended, recommended)}. You're currently using {level_names_en.get(level, level)}."
            else:
                feedback_ko = f"{expected_ko}가 더 적절해요. 현재 {current_ko}를 사용 중입니다."
                feedback_en = f"{level_names_en.get(recommended, recommended)} would be more appropriate. Currently using {level_names_en.get(level, level)}."
        
        return feedback_ko, feedback_en
    
    def _generate_error_history_note(
        self,
        current_errors: List[Dict],
        error_records: Optional[Dict[str, int]],
        language: str
    ) -> Optional[str]:
        """Generate note about error history."""
        if not current_errors or not error_records:
            return None
        
        # Find most significant repeated error
        for error in current_errors:
            error_type = error.get("error_type", "")
            if error_type in error_records:
                count = error_records[error_type]
                if count >= 3:
                    error_name = error.get("name_ko", error_type)
                    if language == "ko":
                        return f"💡 이 실수({error_name})를 {count}번 했어요. 집중해서 연습해봐요!"
                    else:
                        return f"💡 You've made this mistake ({error_type}) {count} times. Let's focus on this!"
        
        return None
    
    def _generate_tip(
        self,
        analysis: Dict[str, Any],
        context: UserContext
    ) -> Tuple[Optional[str], Optional[str]]:
        """Generate personalized tip based on errors and user level."""
        errors = analysis.get("errors", [])
        corrections = analysis.get("corrections", [])
        
        if not errors and not corrections:
            return None, None
        
        # If user has hints enabled
        if not context.show_hints:
            return None, None
        
        # Generate tip based on first error
        if errors:
            error_type = errors[0].get("error_type", "")
            
            tips = {
                "ending_mismatch": {
                    "beginner": {
                        "ko": "팁: '-요'나 '-습니다'로 문장을 끝내보세요!",
                        "en": "Tip: Try ending sentences with -요 or -습니다!"
                    },
                    "intermediate": {
                        "ko": "팁: 상대방의 지위에 따라 어미를 선택하세요.",
                        "en": "Tip: Choose your sentence ending based on the listener's status."
                    },
                    "advanced": {
                        "ko": "어미 선택이 상황과 맞지 않습니다. 격식 수준을 조정해보세요.",
                        "en": "Your sentence ending doesn't match the situation. Adjust the formality level."
                    }
                },
                "honorific_missing": {
                    "beginner": {
                        "ko": "팁: 높은 분에게는 '드리다', '계시다'를 사용해요!",
                        "en": "Tip: Use 드리다, 계시다 when talking to superiors!"
                    },
                    "intermediate": {
                        "ko": "높임 동사를 사용하면 더 공손해보여요 (먹다→드시다).",
                        "en": "Using honorific verbs shows more respect (먹다→드시다)."
                    },
                    "advanced": {
                        "ko": "높임 표현이 필요한 맥락입니다.",
                        "en": "This context requires honorific expressions."
                    }
                },
                "formality_mixed": {
                    "beginner": {
                        "ko": "팁: 한 문장에서는 같은 말투를 사용해요!",
                        "en": "Tip: Use the same speech level throughout a sentence!"
                    },
                    "intermediate": {
                        "ko": "말투가 섞이지 않게 주의하세요.",
                        "en": "Be careful not to mix speech levels."
                    },
                    "advanced": {
                        "ko": "격식 수준의 일관성을 유지하세요.",
                        "en": "Maintain consistency in formality level."
                    }
                }
            }
            
            if error_type in tips:
                level_tips = tips[error_type].get(
                    context.korean_level, 
                    tips[error_type]["intermediate"]
                )
                return level_tips["ko"], level_tips["en"]
        
        # If corrections available, use first one
        if corrections:
            correction = corrections[0]
            original = correction.get("original", "")
            corrected = correction.get("corrected", "")
            
            if original and corrected:
                tip_ko = f"팁: '{original}' 대신 '{corrected}'를 사용해보세요."
                tip_en = f"Tip: Try '{corrected}' instead of '{original}'."
                return tip_ko, tip_en
        
        return None, None
    
    def _generate_progress_note(
        self,
        score: int,
        context: UserContext
    ) -> Optional[str]:
        """Generate note about user's progress."""
        if context.sessions_completed < 3:
            return None  # Not enough data
        
        avg = context.average_score
        trend = context.trend
        
        if trend == "improving":
            diff = round(score - avg, 1)
            if diff > 0:
                return f"📈 평균보다 {diff}점 높아요! 실력이 늘고 있어요!"
            else:
                return "📈 꾸준히 실력이 늘고 있어요!"
        elif trend == "declining":
            return "📉 조금 어려워하고 있는 것 같아요. 천천히 해봐요."
        
        return None
    
    def _generate_encouragement(
        self,
        score: int,
        is_appropriate: bool,
        context: UserContext
    ) -> Tuple[Optional[str], Optional[str]]:
        """Generate encouraging message."""
        
        # Score-based encouragement
        if score >= 90:
            return ("완벽해요! 🌟", "Perfect! 🌟")
        elif score >= 80:
            return ("아주 잘했어요! 👏", "Very well done! 👏")
        elif score >= 70:
            if is_appropriate:
                return ("좋아요! 계속 연습해봐요.", "Good! Keep practicing.")
            else:
                return ("괜찮아요, 조금만 더 신경쓰면 돼요!", "Not bad, just a little more attention needed!")
        elif score >= 50:
            if context.korean_level == "beginner":
                return ("좋은 시작이에요! 💪", "Good start! 💪")
            else:
                return ("조금 더 연습하면 좋아질 거예요!", "A bit more practice will help!")
        else:
            if context.trend == "improving":
                return ("포기하지 마세요! 실력이 늘고 있어요.", "Don't give up! You're improving.")
            else:
                return ("어려워도 괜찮아요. 함께 연습해요!", "It's okay if it's hard. Let's practice together!")
    
    def adjust_feedback_for_level(
        self,
        feedback: str,
        korean_level: str,
        language: str = "ko"
    ) -> str:
        """Adjust feedback complexity based on user's Korean level."""
        if korean_level == "beginner":
            # Simplify vocabulary, add more emoji
            feedback = feedback.replace("적절", "좋은")
            feedback = feedback.replace("격식", "공손한 말투")
            feedback = feedback.replace("맥락", "상황")
        elif korean_level == "advanced":
            # Use more formal/technical terms
            feedback = feedback.replace("말투", "어체")
            feedback = feedback.replace("공손한", "격식있는")
        
        return feedback


# Singleton instance
personalized_feedback_service = PersonalizedFeedbackService()
