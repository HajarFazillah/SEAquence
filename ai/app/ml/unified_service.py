"""
Unified ML Service
Combines emotion, intent detection (Topic removed)
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


# ===========================================
# EMOTION DETECTION
# ===========================================

EMOTIONS = {
    "happy": {"ko": "기쁨", "keywords": ["좋아", "행복", "기뻐", "신나", "웃", "최고"]},
    "sad": {"ko": "슬픔", "keywords": ["슬퍼", "우울", "힘들", "눈물", "아프", "외로"]},
    "angry": {"ko": "화남", "keywords": ["화나", "짜증", "열받", "싫어", "미워", "빡"]},
    "surprised": {"ko": "놀람", "keywords": ["놀라", "헐", "대박", "진짜", "와", "오"]},
    "fearful": {"ko": "두려움", "keywords": ["무서", "걱정", "불안", "떨려", "두려"]},
    "neutral": {"ko": "중립", "keywords": []},
    "curious": {"ko": "궁금", "keywords": ["궁금", "뭐야", "왜", "어떻게", "알고"]},
    "grateful": {"ko": "감사", "keywords": ["고마", "감사", "땡큐", "덕분", "감솨"]},
}


INTENTS = {
    "greeting": {"ko": "인사", "keywords": ["안녕", "반가", "하이", "헬로"]},
    "question": {"ko": "질문", "keywords": ["뭐", "왜", "어디", "언제", "어떻게", "?"]},
    "request": {"ko": "요청", "keywords": ["해줘", "부탁", "해주", "해 줘", "주세요"]},
    "statement": {"ko": "진술", "keywords": []},
    "agreement": {"ko": "동의", "keywords": ["응", "네", "그래", "맞아", "좋아", "알겠"]},
    "disagreement": {"ko": "반대", "keywords": ["아니", "싫어", "안 돼", "별로"]},
    "apology": {"ko": "사과", "keywords": ["미안", "죄송", "잘못"]},
    "thanks": {"ko": "감사", "keywords": ["고마", "감사", "땡큐"]},
    "farewell": {"ko": "작별", "keywords": ["잘 가", "안녕", "바이", "다음에"]},
    "suggestion": {"ko": "제안", "keywords": ["하자", "할까", "어때", "가자"]},
    "complaint": {"ko": "불만", "keywords": ["짜증", "화나", "싫어", "별로"]},
    "praise": {"ko": "칭찬", "keywords": ["잘했", "대단", "멋져", "최고"]},
    "other": {"ko": "기타", "keywords": []},
}


def detect_emotion(text: str) -> Dict[str, Any]:
    """Detect emotion from text."""
    scores = {emotion: 0.0 for emotion in EMOTIONS}
    text_lower = text.lower()
    
    for emotion, data in EMOTIONS.items():
        for keyword in data["keywords"]:
            if keyword in text_lower:
                scores[emotion] += 0.3
    
    total = sum(scores.values())
    if total > 0:
        scores = {k: v / total for k, v in scores.items()}
    else:
        scores["neutral"] = 1.0
    
    top_emotion = max(scores, key=scores.get)
    
    return {
        "emotion": top_emotion,
        "emotion_ko": EMOTIONS[top_emotion]["ko"],
        "confidence": round(scores[top_emotion], 3),
    }


def detect_intent(text: str) -> Dict[str, Any]:
    """Detect intent from text."""
    scores = {intent: 0.0 for intent in INTENTS}
    text_lower = text.lower()
    
    for intent, data in INTENTS.items():
        for keyword in data["keywords"]:
            if keyword in text_lower:
                scores[intent] += 0.3
    
    total = sum(scores.values())
    if total > 0:
        scores = {k: v / total for k, v in scores.items()}
    else:
        scores["statement"] = 1.0
    
    top_intent = max(scores, key=scores.get)
    
    return {
        "intent": top_intent,
        "intent_ko": INTENTS[top_intent]["ko"],
        "confidence": round(scores[top_intent], 3),
    }


def analyze_text(text: str) -> Dict[str, Any]:
    """Full text analysis: emotion + intent."""
    return {
        "text": text,
        "emotion": detect_emotion(text),
        "intent": detect_intent(text),
    }


# ===========================================
# UNIFIED ML SERVICE CLASS
# ===========================================

class UnifiedMLService:
    """Unified service for all ML analysis."""
    
    def __init__(self):
        logger.info("UnifiedMLService initialized (topic detection removed)")
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze text for emotion and intent."""
        return analyze_text(text)
    
    def detect_emotion(self, text: str) -> Dict[str, Any]:
        return detect_emotion(text)
    
    def detect_intent(self, text: str) -> Dict[str, Any]:
        return detect_intent(text)


# Singleton instance
_service: Optional[UnifiedMLService] = None


def get_ml_service() -> UnifiedMLService:
    """Get or create ML service instance."""
    global _service
    if _service is None:
        _service = UnifiedMLService()
    return _service