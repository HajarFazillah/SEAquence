"""
ML Analysis API
Emotion and Intent classification (Topic removed)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

router = APIRouter()


# ===========================================
# SCHEMAS
# ===========================================

class TextInput(BaseModel):
    text: str = Field(..., description="Korean text to analyze")


class EmotionResult(BaseModel):
    emotion: str
    emotion_ko: str
    confidence: float
    all_scores: Dict[str, float]


class IntentResult(BaseModel):
    intent: str
    intent_ko: str
    confidence: float
    all_scores: Dict[str, float]


class FullAnalysisResult(BaseModel):
    text: str
    emotion: EmotionResult
    intent: IntentResult


# ===========================================
# EMOTION DEFINITIONS
# ===========================================

EMOTIONS = {
    "happy": {"ko": "기쁨", "keywords": ["좋아", "행복", "기뻐", "신나", "웃"]},
    "sad": {"ko": "슬픔", "keywords": ["슬퍼", "우울", "힘들", "눈물", "아프"]},
    "angry": {"ko": "화남", "keywords": ["화나", "짜증", "열받", "싫어", "미워"]},
    "surprised": {"ko": "놀람", "keywords": ["놀라", "헐", "대박", "진짜", "와"]},
    "fearful": {"ko": "두려움", "keywords": ["무서", "걱정", "불안", "떨려"]},
    "neutral": {"ko": "중립", "keywords": []},
    "curious": {"ko": "궁금", "keywords": ["궁금", "뭐야", "왜", "어떻게"]},
    "grateful": {"ko": "감사", "keywords": ["고마", "감사", "땡큐", "덕분"]},
}


# ===========================================
# INTENT DEFINITIONS
# ===========================================

INTENTS = {
    "greeting": {"ko": "인사", "keywords": ["안녕", "반가", "하이", "헬로"]},
    "question": {"ko": "질문", "keywords": ["뭐", "왜", "어디", "언제", "어떻게", "?"]},
    "request": {"ko": "요청", "keywords": ["해줘", "부탁", "해주", "해 줘"]},
    "statement": {"ko": "진술", "keywords": []},
    "agreement": {"ko": "동의", "keywords": ["응", "네", "그래", "맞아", "좋아"]},
    "disagreement": {"ko": "반대", "keywords": ["아니", "싫어", "안 돼", "별로"]},
    "apology": {"ko": "사과", "keywords": ["미안", "죄송", "잘못"]},
    "thanks": {"ko": "감사", "keywords": ["고마", "감사", "땡큐"]},
    "farewell": {"ko": "작별", "keywords": ["잘 가", "안녕", "바이", "다음에"]},
    "suggestion": {"ko": "제안", "keywords": ["하자", "할까", "어때", "가자"]},
    "complaint": {"ko": "불만", "keywords": ["짜증", "화나", "싫어", "별로"]},
    "praise": {"ko": "칭찬", "keywords": ["잘했", "대단", "멋져", "최고"]},
    "other": {"ko": "기타", "keywords": []},
}


# ===========================================
# ANALYSIS FUNCTIONS
# ===========================================

def detect_emotion(text: str) -> EmotionResult:
    """Detect emotion from Korean text using keyword matching."""
    scores = {emotion: 0.0 for emotion in EMOTIONS}
    
    text_lower = text.lower()
    
    for emotion, data in EMOTIONS.items():
        for keyword in data["keywords"]:
            if keyword in text_lower:
                scores[emotion] += 0.3
    
    # Normalize scores
    total = sum(scores.values())
    if total > 0:
        scores = {k: v / total for k, v in scores.items()}
    else:
        scores["neutral"] = 1.0
    
    # Get top emotion
    top_emotion = max(scores, key=scores.get)
    
    return EmotionResult(
        emotion=top_emotion,
        emotion_ko=EMOTIONS[top_emotion]["ko"],
        confidence=round(scores[top_emotion], 3),
        all_scores={k: round(v, 3) for k, v in scores.items()}
    )


def detect_intent(text: str) -> IntentResult:
    """Detect intent from Korean text using keyword matching."""
    scores = {intent: 0.0 for intent in INTENTS}
    
    text_lower = text.lower()
    
    for intent, data in INTENTS.items():
        for keyword in data["keywords"]:
            if keyword in text_lower:
                scores[intent] += 0.3
    
    # Normalize scores
    total = sum(scores.values())
    if total > 0:
        scores = {k: v / total for k, v in scores.items()}
    else:
        scores["statement"] = 1.0
    
    # Get top intent
    top_intent = max(scores, key=scores.get)
    
    return IntentResult(
        intent=top_intent,
        intent_ko=INTENTS[top_intent]["ko"],
        confidence=round(scores[top_intent], 3),
        all_scores={k: round(v, 3) for k, v in scores.items()}
    )


# ===========================================
# API ENDPOINTS
# ===========================================

@router.post("/emotion", response_model=EmotionResult)
async def analyze_emotion(input_data: TextInput):
    """Detect emotion from Korean text."""
    return detect_emotion(input_data.text)


@router.post("/intent", response_model=IntentResult)
async def analyze_intent(input_data: TextInput):
    """Detect intent from Korean text."""
    return detect_intent(input_data.text)


@router.post("/analyze", response_model=FullAnalysisResult)
async def full_analysis(input_data: TextInput):
    """Full analysis: emotion + intent."""
    return FullAnalysisResult(
        text=input_data.text,
        emotion=detect_emotion(input_data.text),
        intent=detect_intent(input_data.text)
    )


@router.get("/emotions")
async def list_emotions():
    """List all detectable emotions."""
    return {
        "emotions": [
            {"id": k, "name_ko": v["ko"]}
            for k, v in EMOTIONS.items()
        ]
    }


@router.get("/intents")
async def list_intents():
    """List all detectable intents."""
    return {
        "intents": [
            {"id": k, "name_ko": v["ko"]}
            for k, v in INTENTS.items()
        ]
    }