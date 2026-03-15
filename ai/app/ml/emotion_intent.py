"""
Emotion and Intent Analyzer
Detect user's emotional state and intent for adaptive responses
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Emotion(str, Enum):
    """Detected emotions."""
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    ANXIOUS = "anxious"
    EXCITED = "excited"
    CONFUSED = "confused"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"


class Intent(str, Enum):
    """User intents in conversation."""
    GREETING = "greeting"
    FAREWELL = "farewell"
    QUESTION = "question"
    ANSWER = "answer"
    REQUEST = "request"
    OPINION = "opinion"
    COMPLAINT = "complaint"
    COMPLIMENT = "compliment"
    SMALL_TALK = "small_talk"
    TOPIC_CHANGE = "topic_change"
    CLARIFICATION = "clarification"
    AGREEMENT = "agreement"
    DISAGREEMENT = "disagreement"
    UNKNOWN = "unknown"


@dataclass
class EmotionScore:
    """Score for an emotion."""
    emotion: Emotion
    score: float
    confidence: float
    indicators: List[str]


@dataclass
class EmotionAnalysisResult:
    """Complete emotion analysis result."""
    text: str
    primary_emotion: Emotion
    primary_score: float
    confidence: float
    
    # All emotion scores
    emotion_scores: Dict[str, float]
    
    # Sentiment
    sentiment: str  # positive, negative, neutral
    sentiment_score: float  # -1 to 1
    
    # Indicators found
    indicators: List[str]
    
    # Suggested response style
    suggested_response_style: str


@dataclass
class IntentAnalysisResult:
    """Complete intent analysis result."""
    text: str
    primary_intent: Intent
    confidence: float
    
    # All intent scores
    intent_scores: Dict[str, float]
    
    # Sub-intents
    sub_intents: List[Intent]
    
    # Extracted entities
    entities: Dict[str, Any]
    
    # Expected response type
    expected_response_type: str


class EmotionAnalyzer:
    """
    Analyze emotional content in Korean text.
    
    Detects:
    - Primary emotion (happy, sad, angry, etc.)
    - Sentiment polarity (positive/negative/neutral)
    - Emotional intensity
    
    Uses:
    - Keyword matching
    - Pattern detection
    - Emoji analysis
    - ML classification (when available)
    """
    
    # Emotion keywords
    EMOTION_KEYWORDS = {
        Emotion.HAPPY: {
            "keywords": ["행복", "기뻐", "좋아", "최고", "대박", "신나", "기쁘", "즐거", "웃겨", "ㅋㅋ", "ㅎㅎ"],
            "patterns": [r"ㅋ{2,}", r"ㅎ{2,}", r"[!]{2,}"],
            "emojis": ["😀", "😊", "🎉", "💕", "❤️", "👍", "🙌"]
        },
        Emotion.SAD: {
            "keywords": ["슬퍼", "우울", "힘들", "속상", "아쉬", "눈물", "울", "ㅠㅠ", "ㅜㅜ", "슬프"],
            "patterns": [r"ㅠ{2,}", r"ㅜ{2,}", r"\.{3,}"],
            "emojis": ["😢", "😭", "💔", "😞", "😔"]
        },
        Emotion.ANGRY: {
            "keywords": ["화나", "짜증", "열받", "분노", "빡쳤", "싫어", "미워", "죽겠", "킹받"],
            "patterns": [r"[!?]{3,}", r"ㅡㅡ", r";;"],
            "emojis": ["😠", "😤", "💢", "🤬"]
        },
        Emotion.ANXIOUS: {
            "keywords": ["걱정", "불안", "긴장", "떨려", "무서", "두려", "초조"],
            "patterns": [r"\.{4,}"],
            "emojis": ["😰", "😨", "😟", "😥"]
        },
        Emotion.EXCITED: {
            "keywords": ["설레", "기대", "신나", "두근", "와", "우와", "대박"],
            "patterns": [r"~{2,}", r"[!]{2,}"],
            "emojis": ["🤩", "✨", "💫", "🎊"]
        },
        Emotion.CONFUSED: {
            "keywords": ["모르", "헷갈", "어떻게", "왜", "이상", "뭐지", "응"],
            "patterns": [r"\?{2,}"],
            "emojis": ["🤔", "😕", "❓", "🤷"]
        },
        Emotion.FRUSTRATED: {
            "keywords": ["답답", "막막", "한숨", "에휴", "힘들", "지치"],
            "patterns": [r"ㅎ{3,}ㅠ", r"\.\.\."],
            "emojis": ["😩", "😫", "🤦"]
        }
    }
    
    # Sentiment keywords
    POSITIVE_KEYWORDS = ["좋", "행복", "감사", "기뻐", "최고", "대박", "사랑", "멋져", "잘했"]
    NEGATIVE_KEYWORDS = ["싫", "슬프", "화나", "짜증", "힘들", "아파", "미워", "최악"]
    
    def __init__(self):
        self._embedding_service = None
        self._initialized = False
    
    def _initialize(self):
        """Initialize analyzer."""
        if self._initialized:
            return
        
        try:
            from app.ml.korean_nlp import embedding_service
            self._embedding_service = embedding_service
            self._embedding_service.load()
        except:
            pass
        
        self._initialized = True
    
    def analyze(self, text: str) -> EmotionAnalysisResult:
        """
        Analyze emotions in text.
        
        Args:
            text: Korean text to analyze
            
        Returns:
            EmotionAnalysisResult with detected emotions
        """
        self._initialize()
        
        # Calculate emotion scores
        emotion_scores = {}
        all_indicators = []
        
        for emotion, data in self.EMOTION_KEYWORDS.items():
            score = 0.0
            indicators = []
            
            # Keyword matching
            for kw in data["keywords"]:
                if kw in text.lower():
                    score += 0.15
                    indicators.append(f"keyword:{kw}")
            
            # Pattern matching
            for pattern in data["patterns"]:
                if re.search(pattern, text):
                    score += 0.1
                    indicators.append(f"pattern:{pattern}")
            
            # Emoji matching
            for emoji in data["emojis"]:
                if emoji in text:
                    score += 0.2
                    indicators.append(f"emoji:{emoji}")
            
            emotion_scores[emotion.value] = min(1.0, score)
            all_indicators.extend(indicators)
        
        # Determine primary emotion
        if emotion_scores:
            primary = max(emotion_scores, key=emotion_scores.get)
            primary_emotion = Emotion(primary)
            primary_score = emotion_scores[primary]
        else:
            primary_emotion = Emotion.NEUTRAL
            primary_score = 0.5
        
        # Calculate confidence
        if primary_score > 0:
            total = sum(emotion_scores.values())
            confidence = primary_score / total if total > 0 else 0
        else:
            confidence = 0.3
        
        # Calculate sentiment
        sentiment, sentiment_score = self._analyze_sentiment(text)
        
        # Determine response style
        response_style = self._suggest_response_style(primary_emotion)
        
        return EmotionAnalysisResult(
            text=text,
            primary_emotion=primary_emotion,
            primary_score=primary_score,
            confidence=confidence,
            emotion_scores=emotion_scores,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            indicators=all_indicators,
            suggested_response_style=response_style
        )
    
    def _analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """Analyze overall sentiment."""
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in text)
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in text)
        
        score = (positive_count - negative_count) / (positive_count + negative_count + 1)
        
        if score > 0.2:
            return "positive", score
        elif score < -0.2:
            return "negative", score
        else:
            return "neutral", score
    
    def _suggest_response_style(self, emotion: Emotion) -> str:
        """Suggest appropriate response style based on emotion."""
        styles = {
            Emotion.HAPPY: "enthusiastic",
            Emotion.SAD: "empathetic",
            Emotion.ANGRY: "calm",
            Emotion.ANXIOUS: "reassuring",
            Emotion.EXCITED: "enthusiastic",
            Emotion.CONFUSED: "explanatory",
            Emotion.FRUSTRATED: "supportive",
            Emotion.NEUTRAL: "neutral"
        }
        return styles.get(emotion, "neutral")


class IntentAnalyzer:
    """
    Analyze user intent in Korean conversation.
    
    Detects:
    - Primary intent (question, request, greeting, etc.)
    - Sub-intents
    - Entities (names, times, places)
    """
    
    # Intent patterns
    INTENT_PATTERNS = {
        Intent.GREETING: {
            "keywords": ["안녕", "하이", "반가", "처음"],
            "patterns": [r"^안녕", r"오랜만"]
        },
        Intent.FAREWELL: {
            "keywords": ["잘가", "안녕", "바이", "다음에", "나중에"],
            "patterns": [r"잘\s*가", r"다음에\s*(보|봐)", r"끊을게"]
        },
        Intent.QUESTION: {
            "keywords": ["뭐", "왜", "어디", "언제", "어떻게", "누가", "몇"],
            "patterns": [r"\?$", r"(인가요|인가|인지|니까|ㄹ까)", r"(알아|알려)"]
        },
        Intent.REQUEST: {
            "keywords": ["해줘", "부탁", "해주세요", "줄래", "해줄래"],
            "patterns": [r"(해|하)[ ]?줘", r"(해|하)[ ]?주세요", r"부탁"]
        },
        Intent.OPINION: {
            "keywords": ["생각", "어때", "괜찮", "것 같", "느낌"],
            "patterns": [r"어때", r"괜찮", r"것\s*같아"]
        },
        Intent.COMPLAINT: {
            "keywords": ["싫어", "짜증", "왜이래", "진짜", "너무"],
            "patterns": [r"왜\s*이래", r"짜증", r"싫"]
        },
        Intent.COMPLIMENT: {
            "keywords": ["잘했", "멋져", "대단", "최고", "굿"],
            "patterns": [r"잘\s*했", r"멋져", r"대단"]
        },
        Intent.SMALL_TALK: {
            "keywords": ["뭐해", "밥", "날씨", "요즘"],
            "patterns": [r"뭐\s*해", r"요즘\s*어때"]
        },
        Intent.AGREEMENT: {
            "keywords": ["응", "어", "그래", "맞아", "알겠", "좋아", "네"],
            "patterns": [r"^(응|어|네)$", r"맞아", r"그래"]
        },
        Intent.DISAGREEMENT: {
            "keywords": ["아니", "아냐", "글쎄", "별로", "싫어"],
            "patterns": [r"^아니", r"글쎄", r"별로"]
        },
        Intent.CLARIFICATION: {
            "keywords": ["뭐라고", "다시", "무슨", "이게"],
            "patterns": [r"뭐라고", r"다시\s*(말|설명)"]
        },
        Intent.TOPIC_CHANGE: {
            "keywords": ["그런데", "근데", "그나저나", "참"],
            "patterns": [r"^(그런데|근데|그나저나)", r"^참"]
        }
    }
    
    def __init__(self):
        self._compiled_patterns = {}
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns."""
        for intent, data in self.INTENT_PATTERNS.items():
            self._compiled_patterns[intent] = [
                re.compile(p, re.IGNORECASE) for p in data.get("patterns", [])
            ]
    
    def analyze(self, text: str) -> IntentAnalysisResult:
        """
        Analyze intent in text.
        
        Args:
            text: Korean text to analyze
            
        Returns:
            IntentAnalysisResult with detected intents
        """
        # Calculate intent scores
        intent_scores = {}
        
        for intent, data in self.INTENT_PATTERNS.items():
            score = 0.0
            
            # Keyword matching
            keywords = data.get("keywords", [])
            for kw in keywords:
                if kw in text.lower():
                    score += 0.2
            
            # Pattern matching
            for pattern in self._compiled_patterns.get(intent, []):
                if pattern.search(text):
                    score += 0.3
            
            intent_scores[intent.value] = min(1.0, score)
        
        # Determine primary intent
        if intent_scores:
            primary = max(intent_scores, key=intent_scores.get)
            primary_intent = Intent(primary)
            primary_score = intent_scores[primary]
        else:
            primary_intent = Intent.UNKNOWN
            primary_score = 0
        
        # Calculate confidence
        total = sum(intent_scores.values())
        confidence = primary_score / total if total > 0 else 0.3
        
        # Find sub-intents (other high-scoring intents)
        sub_intents = [
            Intent(i) for i, s in intent_scores.items()
            if s > 0.3 and i != primary_intent.value
        ]
        
        # Extract entities
        entities = self._extract_entities(text)
        
        # Determine expected response type
        expected_response = self._expected_response_type(primary_intent)
        
        return IntentAnalysisResult(
            text=text,
            primary_intent=primary_intent,
            confidence=confidence,
            intent_scores=intent_scores,
            sub_intents=sub_intents,
            entities=entities,
            expected_response_type=expected_response
        )
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from text."""
        entities = {}
        
        # Time patterns
        time_pattern = r'(\d{1,2}시|\d{1,2}:\d{2}|오전|오후|아침|점심|저녁|밤)'
        times = re.findall(time_pattern, text)
        if times:
            entities["times"] = times
        
        # Date patterns
        date_pattern = r'(오늘|내일|어제|모레|이번\s*주|다음\s*주|\d{1,2}월|\d{1,2}일)'
        dates = re.findall(date_pattern, text)
        if dates:
            entities["dates"] = dates
        
        # Location patterns
        location_pattern = r'(학교|집|카페|도서관|식당|강의실|연구실)'
        locations = re.findall(location_pattern, text)
        if locations:
            entities["locations"] = locations
        
        return entities
    
    def _expected_response_type(self, intent: Intent) -> str:
        """Determine expected response type."""
        response_types = {
            Intent.GREETING: "greeting_response",
            Intent.FAREWELL: "farewell_response",
            Intent.QUESTION: "informative_answer",
            Intent.REQUEST: "action_confirmation",
            Intent.OPINION: "opinion_sharing",
            Intent.COMPLAINT: "empathetic_response",
            Intent.COMPLIMENT: "grateful_response",
            Intent.SMALL_TALK: "casual_response",
            Intent.AGREEMENT: "continuation",
            Intent.DISAGREEMENT: "clarification",
            Intent.CLARIFICATION: "explanation",
            Intent.TOPIC_CHANGE: "new_topic_response",
            Intent.UNKNOWN: "generic_response"
        }
        return response_types.get(intent, "generic_response")


# Singleton instances
emotion_analyzer = EmotionAnalyzer()
intent_analyzer = IntentAnalyzer()
