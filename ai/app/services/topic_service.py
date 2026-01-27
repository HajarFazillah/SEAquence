"""
Topic Detection Service
Detect and recommend conversation topics
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from app.core.constants import (
    TOPIC_TAXONOMY,
    get_safe_topics,
    get_sensitive_topics
)

logger = logging.getLogger(__name__)


class TopicService:
    """
    Service for detecting and recommending conversation topics.
    
    Uses keyword matching with optional ML enhancement.
    """
    
    def __init__(self):
        self._keyword_index = self._build_keyword_index()
    
    def _build_keyword_index(self) -> Dict[str, List[str]]:
        """Build reverse index: keyword -> topic_ids."""
        index = defaultdict(list)
        for topic_id, info in TOPIC_TAXONOMY.items():
            for keyword in info.get("keywords", []):
                index[keyword.lower()].append(topic_id)
        return dict(index)
    
    def detect(
        self,
        text: str,
        top_k: int = 3,
        include_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Detect topics from text using keyword matching.
        
        Args:
            text: Input text to analyze
            top_k: Number of top topics to return
            include_sensitive: Whether to include sensitive topics
            
        Returns:
            List of topic results with id, name, confidence, is_sensitive
        """
        text_lower = text.lower()
        scores: Dict[str, float] = defaultdict(float)
        
        # Count keyword matches
        for keyword, topic_ids in self._keyword_index.items():
            if keyword in text_lower:
                for topic_id in topic_ids:
                    scores[topic_id] += 1
        
        # Normalize scores
        results = []
        for topic_id, score in scores.items():
            info = TOPIC_TAXONOMY[topic_id]
            
            # Skip sensitive if not requested
            if info["sensitive"] and not include_sensitive:
                continue
            
            # Normalize by keyword count
            keyword_count = len(info.get("keywords", []))
            confidence = min(score / max(keyword_count * 0.3, 1), 1.0)
            
            results.append({
                "topic_id": topic_id,
                "topic_name_ko": info["name_ko"],
                "topic_name_en": info["name_en"],
                "confidence": round(confidence, 3),
                "is_sensitive": info["sensitive"],
                "match_count": int(score)
            })
        
        # Sort by confidence
        results.sort(key=lambda x: x["confidence"], reverse=True)
        
        # If no matches, return default
        if not results:
            default_info = TOPIC_TAXONOMY["daily_life"]
            results = [{
                "topic_id": "daily_life",
                "topic_name_ko": default_info["name_ko"],
                "topic_name_en": default_info["name_en"],
                "confidence": 0.1,
                "is_sensitive": False,
                "match_count": 0
            }]
        
        return results[:top_k]
    
    def recommend(
        self,
        user_topics: List[str] = None,
        avatar_topics: List[str] = None,
        exclude_topics: List[str] = None,
        context: str = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Recommend topics based on user and avatar preferences.
        
        Args:
            user_topics: User's preferred topics
            avatar_topics: Avatar's conversation topics
            exclude_topics: Topics to exclude
            context: Optional context text to analyze
            top_k: Number of recommendations
            
        Returns:
            Dict with recommended_topics, common_topics, context_detected
        """
        user_topics = set(user_topics or [])
        avatar_topics = set(avatar_topics or [])
        exclude_topics = set(exclude_topics or [])
        
        # Always exclude sensitive topics
        exclude_topics.update(get_sensitive_topics())
        
        # Find common topics
        common = user_topics & avatar_topics - exclude_topics
        
        # Detect from context if provided
        context_detected = []
        if context:
            detected = self.detect(context, top_k=3)
            context_detected = [
                t["topic_id"] for t in detected 
                if not t["is_sensitive"]
            ]
        
        # Build recommendation list
        recommendations = []
        seen = set()
        
        # Priority 1: Context-detected topics that are in common
        for tid in context_detected:
            if tid in common and tid not in seen:
                recommendations.append(self._make_recommendation(tid, "context_common", 1.0))
                seen.add(tid)
        
        # Priority 2: Common topics
        for tid in common:
            if tid not in seen:
                recommendations.append(self._make_recommendation(tid, "common", 0.9))
                seen.add(tid)
        
        # Priority 3: Context-detected in avatar topics
        for tid in context_detected:
            if tid in avatar_topics and tid not in seen and tid not in exclude_topics:
                recommendations.append(self._make_recommendation(tid, "context_avatar", 0.8))
                seen.add(tid)
        
        # Priority 4: Avatar topics
        for tid in avatar_topics:
            if tid not in seen and tid not in exclude_topics:
                recommendations.append(self._make_recommendation(tid, "avatar", 0.6))
                seen.add(tid)
        
        # Priority 5: Safe topics
        for tid in get_safe_topics():
            if tid not in seen and len(recommendations) < top_k:
                recommendations.append(self._make_recommendation(tid, "safe", 0.3))
                seen.add(tid)
        
        return {
            "recommended_topics": recommendations[:top_k],
            "common_topics": list(common),
            "context_detected": context_detected
        }
    
    def _make_recommendation(
        self,
        topic_id: str,
        source: str,
        score: float
    ) -> Dict[str, Any]:
        """Create recommendation dict."""
        info = TOPIC_TAXONOMY.get(topic_id, {})
        return {
            "topic_id": topic_id,
            "topic_name_ko": info.get("name_ko", topic_id),
            "topic_name_en": info.get("name_en", topic_id),
            "score": score,
            "source": source,
            "is_sensitive": info.get("sensitive", False)
        }
    
    def is_sensitive(self, topic_id: str) -> bool:
        """Check if topic is sensitive."""
        return TOPIC_TAXONOMY.get(topic_id, {}).get("sensitive", False)
    
    def get_topic_keywords(self, topic_id: str) -> List[str]:
        """Get keywords for a topic."""
        return TOPIC_TAXONOMY.get(topic_id, {}).get("keywords", [])


# Singleton instance
topic_service = TopicService()
