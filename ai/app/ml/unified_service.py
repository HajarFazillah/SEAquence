"""
Unified ML Analysis Service
Integrates all ML components for comprehensive text analysis
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class ComprehensiveAnalysisResult:
    """Complete analysis result combining all ML modules."""
    text: str
    
    # Topic Analysis
    topic: Dict[str, Any] = field(default_factory=dict)
    
    # Politeness Analysis
    politeness: Dict[str, Any] = field(default_factory=dict)
    
    # Emotion Analysis
    emotion: Dict[str, Any] = field(default_factory=dict)
    
    # Intent Analysis
    intent: Dict[str, Any] = field(default_factory=dict)
    
    # Similarity (if reference provided)
    similarity: Optional[Dict[str, Any]] = None
    
    # Overall Assessment
    overall_score: int = 0
    is_appropriate: bool = True
    
    # Suggestions
    suggestions: List[str] = field(default_factory=list)
    
    # Recommended avatar response style
    recommended_response_style: Dict[str, Any] = field(default_factory=dict)


class UnifiedMLService:
    """
    Unified service integrating all ML analysis components.
    
    Provides:
    1. Topic classification
    2. Politeness analysis
    3. Emotion detection
    4. Intent classification
    5. Semantic similarity
    6. Comprehensive analysis
    """
    
    def __init__(self):
        self._topic_classifier = None
        self._politeness_analyzer = None
        self._emotion_analyzer = None
        self._intent_analyzer = None
        self._embedding_service = None
        self._initialized = False
    
    def _initialize(self):
        """Lazy initialization of all components."""
        if self._initialized:
            return
        
        try:
            from app.ml.topic_classifier import topic_classifier
            self._topic_classifier = topic_classifier
        except Exception as e:
            logger.warning(f"Topic classifier not available: {e}")
        
        try:
            from app.ml.politeness_analyzer import politeness_analyzer
            self._politeness_analyzer = politeness_analyzer
        except Exception as e:
            logger.warning(f"Politeness analyzer not available: {e}")
        
        try:
            from app.ml.emotion_intent import emotion_analyzer, intent_analyzer
            self._emotion_analyzer = emotion_analyzer
            self._intent_analyzer = intent_analyzer
        except Exception as e:
            logger.warning(f"Emotion/Intent analyzers not available: {e}")
        
        try:
            from app.ml.korean_nlp import embedding_service
            self._embedding_service = embedding_service
            self._embedding_service.load()
        except Exception as e:
            logger.warning(f"Embedding service not available: {e}")
        
        self._initialized = True
    
    def analyze_topic(
        self,
        text: str,
        conversation_history: List[str] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Classify the topic of text.
        
        Args:
            text: Text to analyze
            conversation_history: Previous messages for context
            top_k: Number of top topics to return
            
        Returns:
            Dict with topic classification results
        """
        self._initialize()
        
        if not self._topic_classifier:
            return {"error": "Topic classifier not available"}
        
        result = self._topic_classifier.classify(
            text=text,
            conversation_history=conversation_history,
            top_k=top_k
        )
        
        return {
            "primary_topic": result.primary_topic.topic_id if result.primary_topic else None,
            "primary_topic_ko": result.primary_topic.name_ko if result.primary_topic else None,
            "confidence": result.primary_topic.confidence if result.primary_topic else 0,
            "secondary_topics": [
                {"id": t.topic_id, "name": t.name_ko, "score": t.final_score}
                for t in result.secondary_topics
            ],
            "is_sensitive": result.is_sensitive
        }
    
    def analyze_politeness(
        self,
        text: str,
        target_role: str = None,
        target_age: int = None,
        user_age: int = 22
    ) -> Dict[str, Any]:
        """
        Analyze politeness level of text.
        
        Args:
            text: Text to analyze
            target_role: Role of person being addressed
            target_age: Age of target
            user_age: Age of speaker
            
        Returns:
            Dict with politeness analysis results
        """
        self._initialize()
        
        if not self._politeness_analyzer:
            return {"error": "Politeness analyzer not available"}
        
        result = self._politeness_analyzer.analyze(
            text=text,
            target_role=target_role,
            target_age=target_age,
            user_age=user_age
        )
        
        return {
            "level": result.overall_level.value,
            "level_ko": result.overall_level_ko,
            "confidence": result.overall_confidence,
            "score": result.overall_score,
            "is_appropriate": result.is_appropriate,
            "expected_level": result.expected_level.value if result.expected_level else None,
            "corrections": result.corrections,
            "feedback_ko": result.feedback_ko,
            "feedback_en": result.feedback_en,
            "features": result.feature_breakdown
        }
    
    def analyze_emotion(self, text: str) -> Dict[str, Any]:
        """
        Detect emotion in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict with emotion analysis results
        """
        self._initialize()
        
        if not self._emotion_analyzer:
            return {"error": "Emotion analyzer not available"}
        
        result = self._emotion_analyzer.analyze(text)
        
        return {
            "primary_emotion": result.primary_emotion.value,
            "emotion_score": result.primary_score,
            "confidence": result.confidence,
            "sentiment": result.sentiment,
            "sentiment_score": result.sentiment_score,
            "all_emotions": result.emotion_scores,
            "suggested_response_style": result.suggested_response_style
        }
    
    def analyze_intent(self, text: str) -> Dict[str, Any]:
        """
        Detect user intent.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict with intent analysis results
        """
        self._initialize()
        
        if not self._intent_analyzer:
            return {"error": "Intent analyzer not available"}
        
        result = self._intent_analyzer.analyze(text)
        
        return {
            "primary_intent": result.primary_intent.value,
            "confidence": result.confidence,
            "sub_intents": [i.value for i in result.sub_intents],
            "entities": result.entities,
            "expected_response_type": result.expected_response_type,
            "all_intents": result.intent_scores
        }
    
    def calculate_similarity(self, text1: str, text2: str) -> Dict[str, Any]:
        """
        Calculate semantic similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Dict with similarity results
        """
        self._initialize()
        
        if not self._embedding_service:
            return {"error": "Embedding service not available"}
        
        result = self._embedding_service.similarity(text1, text2)
        
        return {
            "score": result.score,
            "method": result.method,
            "confidence": result.confidence
        }
    
    def analyze_comprehensive(
        self,
        text: str,
        target_role: str = None,
        target_age: int = None,
        user_age: int = 22,
        conversation_history: List[str] = None,
        avatar_formality: str = "polite"
    ) -> ComprehensiveAnalysisResult:
        """
        Perform comprehensive analysis combining all ML modules.
        
        Args:
            text: Text to analyze
            target_role: Role of person being addressed
            target_age: Age of target
            user_age: Age of speaker
            conversation_history: Previous messages
            avatar_formality: Expected formality for avatar
            
        Returns:
            ComprehensiveAnalysisResult with all analyses
        """
        self._initialize()
        
        # Run all analyses
        topic_result = self.analyze_topic(text, conversation_history)
        politeness_result = self.analyze_politeness(text, target_role, target_age, user_age)
        emotion_result = self.analyze_emotion(text)
        intent_result = self.analyze_intent(text)
        
        # Calculate overall score
        politeness_score = politeness_result.get("score", 50)
        is_appropriate = politeness_result.get("is_appropriate", True)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(
            politeness_result, emotion_result, intent_result, avatar_formality
        )
        
        # Determine recommended response style
        response_style = self._determine_response_style(
            politeness_result, emotion_result, intent_result, avatar_formality
        )
        
        return ComprehensiveAnalysisResult(
            text=text,
            topic=topic_result,
            politeness=politeness_result,
            emotion=emotion_result,
            intent=intent_result,
            overall_score=politeness_score,
            is_appropriate=is_appropriate,
            suggestions=suggestions,
            recommended_response_style=response_style
        )
    
    def _generate_suggestions(
        self,
        politeness: Dict,
        emotion: Dict,
        intent: Dict,
        avatar_formality: str
    ) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []
        
        # Politeness suggestions
        if not politeness.get("is_appropriate", True):
            feedback = politeness.get("feedback_ko", "")
            if feedback:
                suggestions.append(feedback)
            
            corrections = politeness.get("corrections", [])
            for c in corrections[:2]:
                suggestions.append(
                    f"'{c.get('original')}' → '{c.get('corrected')}'"
                )
        
        # Emotion-based suggestions
        emotion_type = emotion.get("primary_emotion", "neutral")
        if emotion_type == "angry" or emotion_type == "frustrated":
            suggestions.append("차분하게 말씀해 보세요 😊")
        
        # Intent-based suggestions
        intent_type = intent.get("primary_intent", "unknown")
        if intent_type == "question" and avatar_formality == "very_polite":
            suggestions.append("질문할 때는 '여쭤봐도 될까요?'를 사용해보세요")
        
        return suggestions[:5]  # Max 5 suggestions
    
    def _determine_response_style(
        self,
        politeness: Dict,
        emotion: Dict,
        intent: Dict,
        avatar_formality: str
    ) -> Dict[str, Any]:
        """Determine recommended avatar response style."""
        style = {
            "formality": avatar_formality,
            "tone": "neutral",
            "include_correction": False,
            "encouragement_level": "medium"
        }
        
        # Adjust based on politeness
        if not politeness.get("is_appropriate", True):
            style["include_correction"] = True
            style["tone"] = "helpful"
        
        # Adjust based on emotion
        emotion_type = emotion.get("primary_emotion", "neutral")
        response_style = emotion.get("suggested_response_style", "neutral")
        
        if emotion_type == "sad" or emotion_type == "frustrated":
            style["tone"] = "empathetic"
            style["encouragement_level"] = "high"
        elif emotion_type == "happy" or emotion_type == "excited":
            style["tone"] = "enthusiastic"
        elif emotion_type == "confused":
            style["tone"] = "explanatory"
        
        # Adjust based on intent
        intent_type = intent.get("primary_intent", "unknown")
        if intent_type == "question":
            style["should_answer"] = True
        elif intent_type == "greeting":
            style["should_greet_back"] = True
        
        return style
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all ML components."""
        self._initialize()
        
        return {
            "topic_classifier": self._topic_classifier is not None,
            "politeness_analyzer": self._politeness_analyzer is not None,
            "emotion_analyzer": self._emotion_analyzer is not None,
            "intent_analyzer": self._intent_analyzer is not None,
            "embedding_service": self._embedding_service is not None,
            "embedding_method": (
                self._embedding_service._model is not None 
                if self._embedding_service else False
            )
        }


# Singleton instance
ml_service = UnifiedMLService()


# ===========================================
# Helper Functions
# ===========================================

def analyze_text(
    text: str,
    target_role: str = None,
    avatar_formality: str = "polite"
) -> Dict[str, Any]:
    """
    Quick comprehensive analysis of text.
    
    Convenience function for common use case.
    """
    result = ml_service.analyze_comprehensive(
        text=text,
        target_role=target_role,
        avatar_formality=avatar_formality
    )
    return asdict(result)


def check_politeness(
    text: str,
    target_role: str,
    expected_formality: str = "polite"
) -> Dict[str, Any]:
    """
    Quick politeness check.
    
    Returns whether text is appropriate for target.
    """
    result = ml_service.analyze_politeness(text, target_role)
    
    return {
        "is_appropriate": result.get("is_appropriate", True),
        "detected_level": result.get("level"),
        "score": result.get("score", 50),
        "feedback": result.get("feedback_ko", "")
    }


def detect_topic(text: str) -> Dict[str, Any]:
    """
    Quick topic detection.
    
    Returns primary topic and confidence.
    """
    result = ml_service.analyze_topic(text)
    
    return {
        "topic": result.get("primary_topic"),
        "topic_name": result.get("primary_topic_ko"),
        "confidence": result.get("confidence", 0)
    }
