"""
Semantic Topic Classifier
Uses embeddings + keywords + context for accurate topic detection
"""

import logging
import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class TopicScore:
    """Score for a single topic."""
    topic_id: str
    name_ko: str
    name_en: str
    
    # Individual scores
    semantic_score: float = 0.0
    keyword_score: float = 0.0
    context_score: float = 0.0
    
    # Combined
    final_score: float = 0.0
    confidence: float = 0.0
    rank: int = 0


@dataclass
class TopicClassificationResult:
    """Complete topic classification result."""
    text: str
    primary_topic: TopicScore
    secondary_topics: List[TopicScore]
    all_scores: Dict[str, float]
    is_sensitive: bool
    method_weights: Dict[str, float]


class SemanticTopicClassifier:
    """
    Multi-method topic classifier combining:
    
    1. **Semantic Similarity** - Using Korean BERT embeddings
    2. **Keyword Matching** - Pattern and keyword detection
    3. **Context Analysis** - Conversation history consideration
    4. **Learned Patterns** - From training data (future)
    
    Topics:
    - campus_life, class_study, professor_meeting
    - part_time_job, career_future, friendship
    - roommate, daily_life, weather, cafe_food
    - kpop, drama_movie, museum_art
    - politics, religion (sensitive - filtered by default)
    """
    
    # Topic definitions with rich metadata
    TOPICS = {
        "campus_life": {
            "name_ko": "대학 생활",
            "name_en": "Campus Life",
            "description": "대학교 캠퍼스 생활, 동아리, 축제, 학교 시설",
            "keywords": [
                "학교", "캠퍼스", "도서관", "학생회관", "동아리", "축제", "MT", 
                "학생", "대학", "대학교", "강의실", "학생식당", "교내", "교환학생"
            ],
            "patterns": [r"학교에서", r"캠퍼스", r"동아리", r"학생회"],
            "related_topics": ["class_study", "friendship"],
            "formality_hint": "polite",
            "sensitive": False
        },
        "class_study": {
            "name_ko": "수업/공부",
            "name_en": "Class/Study",
            "description": "수업, 강의, 과제, 시험, 공부 관련",
            "keywords": [
                "수업", "강의", "과제", "시험", "레포트", "공부", "중간고사", 
                "기말고사", "학점", "성적", "출석", "과목", "전공", "교양",
                "퀴즈", "발표", "팀플", "조별과제"
            ],
            "patterns": [r"수업이?", r"시험[이을]?", r"과제[가를]?", r"공부"],
            "related_topics": ["campus_life", "professor_meeting"],
            "formality_hint": "polite",
            "sensitive": False
        },
        "professor_meeting": {
            "name_ko": "교수님 면담",
            "name_en": "Professor Meeting",
            "description": "교수님과의 상담, 면담, 질문",
            "keywords": [
                "교수님", "상담", "면담", "연구실", "오피스아워", "추천서",
                "조교", "연구", "논문", "지도교수", "학과사무실"
            ],
            "patterns": [r"교수님", r"면담", r"연구실", r"상담"],
            "related_topics": ["class_study", "career_future"],
            "formality_hint": "very_polite",
            "sensitive": False
        },
        "part_time_job": {
            "name_ko": "아르바이트",
            "name_en": "Part-time Job",
            "description": "아르바이트, 파트타임 일자리",
            "keywords": [
                "알바", "아르바이트", "시급", "편의점", "카페알바", "과외",
                "근무", "사장님", "월급", "주급", "야간", "주말알바"
            ],
            "patterns": [r"알바", r"아르바이트", r"시급", r"근무"],
            "related_topics": ["daily_life", "career_future"],
            "formality_hint": "polite",
            "sensitive": False
        },
        "career_future": {
            "name_ko": "진로/취업",
            "name_en": "Career/Future",
            "description": "취업, 진로, 미래 계획",
            "keywords": [
                "취업", "진로", "인턴", "면접", "이력서", "자소서", "자기소개서",
                "회사", "직장", "대기업", "스타트업", "공무원", "대학원"
            ],
            "patterns": [r"취업", r"진로", r"면접", r"회사"],
            "related_topics": ["professor_meeting", "part_time_job"],
            "formality_hint": "polite",
            "sensitive": False
        },
        "friendship": {
            "name_ko": "친구 관계",
            "name_en": "Friendship",
            "description": "친구와의 관계, 약속, 만남",
            "keywords": [
                "친구", "약속", "만나다", "놀다", "우정", "절친", "베프",
                "동기", "선후배", "만남", "모임", "술자리"
            ],
            "patterns": [r"친구[가와랑]?", r"약속", r"같이"],
            "related_topics": ["daily_life", "cafe_food"],
            "formality_hint": "informal",
            "sensitive": False
        },
        "roommate": {
            "name_ko": "룸메이트",
            "name_en": "Roommate",
            "description": "룸메이트, 기숙사, 자취 생활",
            "keywords": [
                "룸메", "룸메이트", "기숙사", "자취", "방", "원룸", "하숙",
                "월세", "보증금", "관리비", "이웃"
            ],
            "patterns": [r"룸메", r"기숙사", r"자취", r"같이\s*살"],
            "related_topics": ["daily_life", "campus_life"],
            "formality_hint": "informal",
            "sensitive": False
        },
        "daily_life": {
            "name_ko": "일상생활",
            "name_en": "Daily Life",
            "description": "일상적인 생활, 하루 일과",
            "keywords": [
                "오늘", "어제", "내일", "아침", "점심", "저녁", "주말",
                "일상", "하루", "생활", "잠", "휴식", "쉬다"
            ],
            "patterns": [r"오늘", r"뭐해", r"어제", r"주말"],
            "related_topics": ["weather", "cafe_food", "friendship"],
            "formality_hint": "informal",
            "sensitive": False
        },
        "weather": {
            "name_ko": "날씨",
            "name_en": "Weather",
            "description": "날씨, 기온, 계절",
            "keywords": [
                "날씨", "비", "눈", "더워", "추워", "맑다", "흐리다",
                "미세먼지", "태풍", "장마", "여름", "겨울", "봄", "가을"
            ],
            "patterns": [r"날씨", r"[비눈]가?\s*(와|온다)", r"덥|춥"],
            "related_topics": ["daily_life"],
            "formality_hint": "neutral",
            "sensitive": False
        },
        "cafe_food": {
            "name_ko": "카페/음식",
            "name_en": "Cafe/Food",
            "description": "카페, 음식, 맛집",
            "keywords": [
                "카페", "커피", "밥", "점심", "저녁", "맛집", "배달",
                "치킨", "피자", "라면", "식당", "메뉴", "디저트", "브런치"
            ],
            "patterns": [r"카페", r"밥\s*먹", r"맛집", r"배달"],
            "related_topics": ["daily_life", "friendship"],
            "formality_hint": "informal",
            "sensitive": False
        },
        "kpop": {
            "name_ko": "K-POP",
            "name_en": "K-POP",
            "description": "케이팝, 아이돌, 음악",
            "keywords": [
                "아이돌", "콘서트", "앨범", "팬", "뮤비", "방탄", "BTS",
                "블랙핑크", "노래", "가수", "음악", "덕질", "최애", "컴백"
            ],
            "patterns": [r"아이돌", r"콘서트", r"팬", r"최애"],
            "related_topics": ["drama_movie"],
            "formality_hint": "informal",
            "sensitive": False
        },
        "drama_movie": {
            "name_ko": "드라마/영화",
            "name_en": "Drama/Movie",
            "description": "드라마, 영화, OTT",
            "keywords": [
                "드라마", "영화", "넷플릭스", "봤어", "재밌다", "배우",
                "시청", "극장", "웨이브", "왓챠", "디즈니", "시리즈"
            ],
            "patterns": [r"드라마", r"영화", r"넷플릭스", r"봤어"],
            "related_topics": ["kpop", "daily_life"],
            "formality_hint": "informal",
            "sensitive": False
        },
        "museum_art": {
            "name_ko": "미술관/전시",
            "name_en": "Museum/Art",
            "description": "미술관, 박물관, 전시회",
            "keywords": [
                "미술관", "전시", "그림", "작품", "갤러리", "예술",
                "박물관", "전시회", "작가", "현대미술"
            ],
            "patterns": [r"미술관", r"전시", r"갤러리"],
            "related_topics": ["daily_life"],
            "formality_hint": "polite",
            "sensitive": False
        },
        "politics": {
            "name_ko": "정치",
            "name_en": "Politics",
            "description": "정치, 선거, 정당",
            "keywords": [
                "정치", "대통령", "선거", "정당", "국회", "의원",
                "투표", "정책", "여당", "야당"
            ],
            "patterns": [r"정치", r"대통령", r"선거"],
            "related_topics": [],
            "formality_hint": "polite",
            "sensitive": True
        },
        "religion": {
            "name_ko": "종교",
            "name_en": "Religion",
            "description": "종교, 신앙",
            "keywords": [
                "종교", "교회", "절", "기도", "신", "믿음",
                "성당", "사찰", "불교", "기독교", "천주교"
            ],
            "patterns": [r"종교", r"교회", r"절에"],
            "related_topics": [],
            "formality_hint": "polite",
            "sensitive": True
        },
    }
    
    # Method weights (can be adjusted)
    DEFAULT_WEIGHTS = {
        "semantic": 0.4,
        "keyword": 0.35,
        "pattern": 0.15,
        "context": 0.1
    }
    
    def __init__(self):
        self._embedding_service = None
        self._topic_embeddings: Dict[str, np.ndarray] = {}
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        self._initialized = False
        
    def _initialize(self):
        """Initialize the classifier."""
        if self._initialized:
            return
        
        # Compile regex patterns
        for topic_id, info in self.TOPICS.items():
            patterns = info.get("patterns", [])
            self._compiled_patterns[topic_id] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
        
        # Try to load embedding service
        try:
            from app.ml.korean_nlp import embedding_service
            self._embedding_service = embedding_service
            self._embedding_service.load()
            
            # Pre-compute topic embeddings
            self._compute_topic_embeddings()
            
        except Exception as e:
            logger.warning(f"Could not load embedding service: {e}")
        
        self._initialized = True
    
    def _compute_topic_embeddings(self):
        """Pre-compute embeddings for all topics."""
        if not self._embedding_service:
            return
        
        for topic_id, info in self.TOPICS.items():
            # Combine topic info into embedding text
            text_parts = [
                info.get("name_ko", ""),
                info.get("description", ""),
                " ".join(info.get("keywords", [])[:15])
            ]
            topic_text = " ".join(filter(None, text_parts))
            
            self._topic_embeddings[topic_id] = self._embedding_service.encode(topic_text)
        
        logger.info(f"Pre-computed embeddings for {len(self._topic_embeddings)} topics")
    
    def classify(
        self,
        text: str,
        conversation_history: List[str] = None,
        weights: Dict[str, float] = None,
        include_sensitive: bool = False,
        top_k: int = 3
    ) -> TopicClassificationResult:
        """
        Classify the topic of given text.
        
        Args:
            text: Text to classify
            conversation_history: Previous messages for context
            weights: Custom weights for different methods
            include_sensitive: Include sensitive topics (politics, religion)
            top_k: Number of top topics to return
            
        Returns:
            TopicClassificationResult with detailed scores
        """
        self._initialize()
        
        weights = weights or self.DEFAULT_WEIGHTS
        
        # Calculate scores using different methods
        semantic_scores = self._semantic_scores(text)
        keyword_scores = self._keyword_scores(text)
        pattern_scores = self._pattern_scores(text)
        context_scores = self._context_scores(text, conversation_history)
        
        # Combine scores
        all_scores = {}
        for topic_id in self.TOPICS:
            if not include_sensitive and self.TOPICS[topic_id].get("sensitive", False):
                continue
            
            combined = (
                weights["semantic"] * semantic_scores.get(topic_id, 0) +
                weights["keyword"] * keyword_scores.get(topic_id, 0) +
                weights["pattern"] * pattern_scores.get(topic_id, 0) +
                weights["context"] * context_scores.get(topic_id, 0)
            )
            all_scores[topic_id] = combined
        
        # Sort by score
        sorted_topics = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Build results
        topic_scores = []
        for rank, (topic_id, score) in enumerate(sorted_topics[:top_k + 1]):
            info = self.TOPICS[topic_id]
            
            # Calculate confidence
            confidence = min(1.0, score * 1.5) if score > 0 else 0
            
            topic_scores.append(TopicScore(
                topic_id=topic_id,
                name_ko=info["name_ko"],
                name_en=info["name_en"],
                semantic_score=semantic_scores.get(topic_id, 0),
                keyword_score=keyword_scores.get(topic_id, 0),
                context_score=context_scores.get(topic_id, 0),
                final_score=score,
                confidence=confidence,
                rank=rank + 1
            ))
        
        # Check for sensitive topics
        is_sensitive = any(
            self.TOPICS[tid].get("sensitive", False)
            for tid, _ in sorted_topics[:3]
            if _ > 0.3
        )
        
        return TopicClassificationResult(
            text=text,
            primary_topic=topic_scores[0] if topic_scores else None,
            secondary_topics=topic_scores[1:top_k],
            all_scores=all_scores,
            is_sensitive=is_sensitive,
            method_weights=weights
        )
    
    def _semantic_scores(self, text: str) -> Dict[str, float]:
        """Calculate semantic similarity scores."""
        scores = {}
        
        if not self._embedding_service or not self._topic_embeddings:
            return scores
        
        text_emb = self._embedding_service.encode(text)
        
        for topic_id, topic_emb in self._topic_embeddings.items():
            sim = float(np.dot(text_emb, topic_emb))
            scores[topic_id] = max(0, sim)  # Clamp negative similarities
        
        return scores
    
    def _keyword_scores(self, text: str) -> Dict[str, float]:
        """Calculate keyword matching scores."""
        scores = {}
        text_lower = text.lower()
        
        for topic_id, info in self.TOPICS.items():
            keywords = info.get("keywords", [])
            matches = sum(1 for kw in keywords if kw in text_lower)
            
            if matches > 0:
                # Normalize by sqrt of keyword count for balanced scoring
                scores[topic_id] = min(1.0, matches / (len(keywords) ** 0.5))
            else:
                scores[topic_id] = 0
        
        return scores
    
    def _pattern_scores(self, text: str) -> Dict[str, float]:
        """Calculate regex pattern matching scores."""
        scores = {}
        
        for topic_id, patterns in self._compiled_patterns.items():
            matches = sum(1 for p in patterns if p.search(text))
            
            if matches > 0:
                scores[topic_id] = min(1.0, matches / len(patterns))
            else:
                scores[topic_id] = 0
        
        return scores
    
    def _context_scores(
        self,
        text: str,
        history: List[str] = None
    ) -> Dict[str, float]:
        """Calculate context-aware scores from conversation history."""
        scores = {tid: 0.0 for tid in self.TOPICS}
        
        if not history:
            return scores
        
        # Classify recent history
        recent = history[-3:]  # Last 3 messages
        
        topic_counts = Counter()
        for msg in recent:
            msg_keywords = self._keyword_scores(msg)
            for tid, score in msg_keywords.items():
                if score > 0.2:
                    topic_counts[tid] += 1
        
        # Boost related topics
        for tid, count in topic_counts.items():
            # Direct boost
            scores[tid] += count * 0.2
            
            # Related topic boost
            related = self.TOPICS[tid].get("related_topics", [])
            for rel_tid in related:
                if rel_tid in scores:
                    scores[rel_tid] += count * 0.1
        
        # Normalize
        max_score = max(scores.values()) if scores else 1
        if max_score > 0:
            scores = {k: v / max_score for k, v in scores.items()}
        
        return scores
    
    def get_topic_info(self, topic_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a topic."""
        return self.TOPICS.get(topic_id)
    
    def suggest_transition(
        self,
        current_topic: str,
        exclude: List[str] = None
    ) -> List[Tuple[str, float]]:
        """
        Suggest natural topic transitions.
        
        Returns list of (topic_id, relevance_score) tuples.
        """
        exclude = set(exclude or [])
        exclude.add(current_topic)
        
        current_info = self.TOPICS.get(current_topic, {})
        related = current_info.get("related_topics", [])
        
        suggestions = []
        
        # Related topics get highest scores
        for tid in related:
            if tid not in exclude and not self.TOPICS[tid].get("sensitive", False):
                suggestions.append((tid, 0.8))
        
        # Other non-sensitive topics
        for tid in self.TOPICS:
            if tid not in exclude and tid not in related:
                if not self.TOPICS[tid].get("sensitive", False):
                    suggestions.append((tid, 0.3))
        
        return sorted(suggestions, key=lambda x: x[1], reverse=True)[:5]


# Singleton instance
topic_classifier = SemanticTopicClassifier()
