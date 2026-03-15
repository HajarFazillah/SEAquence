"""
Emotion & Conversation Status System
Simulates avatar emotions and provides visual feedback based on user performance
"""

from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from enum import Enum


# ===========================================
# Emotion Types
# ===========================================

class AvatarEmotion(str, Enum):
    """Avatar emotional states based on conversation flow"""
    HAPPY = "happy"              # User doing great
    EXCITED = "excited"          # User achieved goal or improved
    NEUTRAL = "neutral"          # Normal conversation
    THINKING = "thinking"        # User made minor mistake
    CONFUSED = "confused"        # User made formality mistake
    CONCERNED = "concerned"      # User struggling
    ENCOURAGING = "encouraging"  # Cheering user on
    PROUD = "proud"              # User improved a lot


class ConversationStatus(str, Enum):
    """Overall conversation quality status"""
    PERFECT = "perfect"              # 90-100 score, no mistakes
    EXCELLENT = "excellent"          # 80-89 score, minor mistakes
    GOOD = "good"                    # 70-79 score
    NEEDS_PRACTICE = "needs_practice"  # 60-69 score
    STRUGGLING = "struggling"        # Below 60


class WarningLevel(str, Enum):
    """Warning severity for mistakes"""
    NONE = "none"
    HINT = "hint"           # Gentle suggestion
    MILD = "mild"           # Small mistake
    MODERATE = "moderate"   # Noticeable mistake
    STRONG = "strong"       # Major mistake


# ===========================================
# Emotion Response Models
# ===========================================

class EmotionState(BaseModel):
    """Current avatar emotion state"""
    emotion: AvatarEmotion = AvatarEmotion.NEUTRAL
    emoji: str = "😐"
    message_ko: Optional[str] = None  # Optional reaction message
    message_en: Optional[str] = None
    
    # For animation/UI
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)  # 0-1 scale


class ConversationStatusInfo(BaseModel):
    """Conversation status with visual feedback"""
    status: ConversationStatus = ConversationStatus.GOOD
    emoji: str = "🙂"
    label_ko: str = "좋아요"
    label_en: str = "Good"
    color: str = "#4CAF50"  # Green
    
    # Score info
    current_score: int = 0
    average_score: float = 0.0
    
    # Progress bar (0-100)
    progress: int = 0


class Warning(BaseModel):
    """Warning/feedback for user mistakes"""
    level: WarningLevel = WarningLevel.NONE
    
    # Visual
    emoji: str = ""
    color: str = ""
    
    # Message
    message_ko: str = ""
    message_en: str = ""
    
    # What to fix
    category: Optional[str] = None  # particles, formality, etc.
    original: Optional[str] = None
    suggestion: Optional[str] = None
    
    # Show correction button?
    show_correction: bool = False


class EmotionFeedback(BaseModel):
    """Complete emotion and feedback response"""
    # Avatar emotion
    avatar_emotion: EmotionState
    
    # Conversation status (shown at bottom)
    conversation_status: ConversationStatusInfo
    
    # Warnings (if any)
    warnings: List[Warning] = []
    
    # Encouragement (positive reinforcement)
    encouragement: Optional[str] = None
    
    # Tips (based on mistakes)
    tips: List[str] = []


# ===========================================
# Emotion Calculator
# ===========================================

class EmotionCalculator:
    """
    Calculates avatar emotion and conversation status
    based on user's performance in the conversation.
    """
    
    # Emotion emoji mapping
    EMOTION_EMOJIS = {
        AvatarEmotion.HAPPY: "😊",
        AvatarEmotion.EXCITED: "🤩",
        AvatarEmotion.NEUTRAL: "😐",
        AvatarEmotion.THINKING: "🤔",
        AvatarEmotion.CONFUSED: "😕",
        AvatarEmotion.CONCERNED: "😟",
        AvatarEmotion.ENCOURAGING: "💪",
        AvatarEmotion.PROUD: "🥰",
    }
    
    # Status configuration
    STATUS_CONFIG = {
        ConversationStatus.PERFECT: {
            "emoji": "😊",
            "label_ko": "완벽한 대화",
            "label_en": "Perfect conversation",
            "color": "#4CAF50",  # Green
        },
        ConversationStatus.EXCELLENT: {
            "emoji": "😄",
            "label_ko": "아주 좋아요",
            "label_en": "Excellent",
            "color": "#8BC34A",  # Light green
        },
        ConversationStatus.GOOD: {
            "emoji": "🙂",
            "label_ko": "좋아요",
            "label_en": "Good",
            "color": "#CDDC39",  # Lime
        },
        ConversationStatus.NEEDS_PRACTICE: {
            "emoji": "😅",
            "label_ko": "연습이 필요해요",
            "label_en": "Needs practice",
            "color": "#FFC107",  # Amber
        },
        ConversationStatus.STRUGGLING: {
            "emoji": "😓",
            "label_ko": "힘내세요!",
            "label_en": "Keep trying!",
            "color": "#FF9800",  # Orange
        },
    }
    
    # Warning configuration
    WARNING_CONFIG = {
        WarningLevel.HINT: {
            "emoji": "💡",
            "color": "#2196F3",  # Blue
        },
        WarningLevel.MILD: {
            "emoji": "📝",
            "color": "#FFC107",  # Amber
        },
        WarningLevel.MODERATE: {
            "emoji": "⚠️",
            "color": "#FF9800",  # Orange
        },
        WarningLevel.STRONG: {
            "emoji": "❗",
            "color": "#F44336",  # Red
        },
    }
    
    def calculate_emotion(
        self,
        current_score: int,
        mistakes: List[Dict[str, Any]],
        recent_scores: List[int] = None,
        goals_achieved: List[str] = None,
        is_improving: bool = False
    ) -> EmotionState:
        """
        Calculate avatar emotion based on user's current performance.
        
        Args:
            current_score: Score for current message (0-100)
            mistakes: List of mistakes in current message
            recent_scores: Last few message scores
            goals_achieved: Goals achieved this message
            is_improving: Whether user is improving overall
        """
        recent_scores = recent_scores or []
        goals_achieved = goals_achieved or []
        
        # Default emotion
        emotion = AvatarEmotion.NEUTRAL
        intensity = 0.5
        message_ko = None
        message_en = None
        
        # Check for goal achievement first (highest priority)
        if goals_achieved:
            emotion = AvatarEmotion.EXCITED
            intensity = 0.9
            message_ko = "와! 잘했어요! 🎉"
            message_en = "Wow! Great job!"
        
        # Check for improvement
        elif is_improving and len(recent_scores) >= 3:
            if sum(recent_scores[-3:]) / 3 > sum(recent_scores[:3]) / 3 + 10:
                emotion = AvatarEmotion.PROUD
                intensity = 0.8
                message_ko = "많이 늘었어요!"
                message_en = "You've improved a lot!"
        
        # Score-based emotion
        elif current_score >= 95:
            emotion = AvatarEmotion.HAPPY
            intensity = 0.9
            message_ko = "완벽해요!"
            message_en = "Perfect!"
        
        elif current_score >= 85:
            emotion = AvatarEmotion.HAPPY
            intensity = 0.7
        
        elif current_score >= 70:
            emotion = AvatarEmotion.NEUTRAL
            intensity = 0.5
        
        elif current_score >= 60:
            # Check mistake types
            mistake_types = [m.get("category", "") for m in mistakes]
            
            if "formality" in mistake_types:
                emotion = AvatarEmotion.CONFUSED
                intensity = 0.6
                message_ko = "말투가 조금 어색해요"
                message_en = "The speech level seems off"
            else:
                emotion = AvatarEmotion.THINKING
                intensity = 0.5
        
        else:  # Below 60
            if len(mistakes) >= 3:
                emotion = AvatarEmotion.CONCERNED
                intensity = 0.7
                message_ko = "천천히 해봐요"
                message_en = "Take your time"
            else:
                emotion = AvatarEmotion.ENCOURAGING
                intensity = 0.6
                message_ko = "힘내요!"
                message_en = "You can do it!"
        
        return EmotionState(
            emotion=emotion,
            emoji=self.EMOTION_EMOJIS[emotion],
            message_ko=message_ko,
            message_en=message_en,
            intensity=intensity
        )
    
    def calculate_conversation_status(
        self,
        current_score: int,
        average_score: float,
        total_mistakes: int,
        message_count: int
    ) -> ConversationStatusInfo:
        """
        Calculate overall conversation status.
        
        Shown at bottom of chat screen.
        """
        # Determine status based on average score
        if average_score >= 90 and total_mistakes == 0:
            status = ConversationStatus.PERFECT
        elif average_score >= 80:
            status = ConversationStatus.EXCELLENT
        elif average_score >= 70:
            status = ConversationStatus.GOOD
        elif average_score >= 60:
            status = ConversationStatus.NEEDS_PRACTICE
        else:
            status = ConversationStatus.STRUGGLING
        
        config = self.STATUS_CONFIG[status]
        
        # Calculate progress (0-100)
        progress = min(100, int(average_score))
        
        return ConversationStatusInfo(
            status=status,
            emoji=config["emoji"],
            label_ko=config["label_ko"],
            label_en=config["label_en"],
            color=config["color"],
            current_score=current_score,
            average_score=round(average_score, 1),
            progress=progress
        )
    
    def generate_warnings(
        self,
        mistakes: List[Dict[str, Any]],
        expected_formality: str = "polite"
    ) -> List[Warning]:
        """
        Generate warnings for mistakes.
        
        Returns list of warnings with visual feedback.
        """
        warnings = []
        
        for mistake in mistakes:
            category = mistake.get("category", "other")
            severity = mistake.get("severity", "minor")
            
            # Determine warning level
            if severity == "major":
                level = WarningLevel.STRONG
            elif severity == "moderate":
                level = WarningLevel.MODERATE
            elif category == "formality":
                level = WarningLevel.MODERATE  # Formality is important
            else:
                level = WarningLevel.MILD
            
            config = self.WARNING_CONFIG.get(level, self.WARNING_CONFIG[WarningLevel.MILD])
            
            # Generate message
            message_ko, message_en = self._get_warning_message(category, mistake)
            
            warning = Warning(
                level=level,
                emoji=config["emoji"],
                color=config["color"],
                message_ko=message_ko,
                message_en=message_en,
                category=category,
                original=mistake.get("original"),
                suggestion=mistake.get("corrected"),
                show_correction=True
            )
            warnings.append(warning)
        
        return warnings
    
    def _get_warning_message(
        self, 
        category: str, 
        mistake: Dict[str, Any]
    ) -> Tuple[str, str]:
        """Get warning message based on mistake category."""
        
        original = mistake.get("original", "")
        corrected = mistake.get("corrected", "")
        
        messages = {
            "particles": (
                f"'{original}' → '{corrected}'로 바꿔보세요",
                f"Try using '{corrected}' instead of '{original}'"
            ),
            "formality": (
                "말투를 확인해 주세요",
                "Check your speech level"
            ),
            "honorifics": (
                "높임말을 사용해 보세요",
                "Try using honorific forms"
            ),
            "spelling": (
                f"'{original}' → '{corrected}'",
                f"'{original}' → '{corrected}'"
            ),
            "verb_conjugation": (
                "동사 활용을 확인해 주세요",
                "Check the verb conjugation"
            ),
        }
        
        return messages.get(category, (
            mistake.get("explanation", "수정이 필요해요"),
            mistake.get("explanation_en", "Needs correction")
        ))
    
    def generate_encouragement(
        self,
        current_score: int,
        is_improving: bool,
        goals_achieved: List[str],
        mistake_count: int
    ) -> Optional[str]:
        """Generate encouragement message."""
        
        if goals_achieved:
            return f"🎉 목표 달성: {', '.join(goals_achieved)}"
        
        if current_score >= 95:
            return "✨ 완벽해요!"
        
        if current_score >= 85 and mistake_count == 0:
            return "👍 아주 잘하고 있어요!"
        
        if is_improving:
            return "📈 점점 좋아지고 있어요!"
        
        if mistake_count == 0:
            return "👏 실수 없이 잘했어요!"
        
        return None
    
    def calculate_full_feedback(
        self,
        current_score: int,
        mistakes: List[Dict[str, Any]],
        recent_scores: List[int] = None,
        average_score: float = None,
        total_mistakes: int = 0,
        message_count: int = 1,
        goals_achieved: List[str] = None,
        expected_formality: str = "polite"
    ) -> EmotionFeedback:
        """
        Calculate complete emotion feedback for a message.
        
        Returns everything needed for UI display.
        """
        recent_scores = recent_scores or []
        goals_achieved = goals_achieved or []
        
        if average_score is None:
            average_score = current_score
        
        # Check if improving
        is_improving = False
        if len(recent_scores) >= 5:
            first_half = sum(recent_scores[:len(recent_scores)//2]) / (len(recent_scores)//2)
            second_half = sum(recent_scores[len(recent_scores)//2:]) / (len(recent_scores) - len(recent_scores)//2)
            is_improving = second_half > first_half + 5
        
        # Calculate all components
        avatar_emotion = self.calculate_emotion(
            current_score=current_score,
            mistakes=mistakes,
            recent_scores=recent_scores,
            goals_achieved=goals_achieved,
            is_improving=is_improving
        )
        
        conversation_status = self.calculate_conversation_status(
            current_score=current_score,
            average_score=average_score,
            total_mistakes=total_mistakes,
            message_count=message_count
        )
        
        warnings = self.generate_warnings(
            mistakes=mistakes,
            expected_formality=expected_formality
        )
        
        encouragement = self.generate_encouragement(
            current_score=current_score,
            is_improving=is_improving,
            goals_achieved=goals_achieved,
            mistake_count=len(mistakes)
        )
        
        # Generate tips based on mistakes
        tips = self._generate_tips(mistakes)
        
        return EmotionFeedback(
            avatar_emotion=avatar_emotion,
            conversation_status=conversation_status,
            warnings=warnings,
            encouragement=encouragement,
            tips=tips
        )
    
    def _generate_tips(self, mistakes: List[Dict[str, Any]]) -> List[str]:
        """Generate tips based on mistake patterns."""
        tips = []
        categories_seen = set()
        
        tip_templates = {
            "particles": "💡 조사 팁: 받침 있으면 '을', 없으면 '를'!",
            "formality": "💡 말투를 일관되게 유지해 보세요!",
            "honorifics": "💡 높임말에서는 '-시-'를 사용하세요!",
            "spelling": "💡 맞춤법을 다시 확인해 보세요!",
            "verb_conjugation": "💡 불규칙 동사 활용을 복습해 보세요!",
        }
        
        for mistake in mistakes:
            category = mistake.get("category", "other")
            if category not in categories_seen and category in tip_templates:
                tips.append(tip_templates[category])
                categories_seen.add(category)
        
        return tips[:2]  # Max 2 tips


# Singleton
emotion_calculator = EmotionCalculator()
