"""
ML-Based Compatibility Service
Uses Korean sentence embeddings for semantic similarity matching
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


# ===========================================
# TRY TO LOAD SENTENCE TRANSFORMERS
# ===========================================

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMER_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMER_AVAILABLE = False
    logger.warning("sentence-transformers not available, using fallback")


# ===========================================
# DATA CLASSES
# ===========================================

@dataclass
class CompatibilityResult:
    """Result of ML-based compatibility analysis."""
    score: float                      # 0-100
    chemistry_level: str              # excellent/good/okay/low
    
    # Detailed matching
    common_interests: List[Dict[str, Any]]   # Semantically similar pairs
    suggested_topics: List[str]              # Best topics to discuss
    avoid_topics: List[str]                  # Topics to avoid
    
    # Personality match
    personality_match: float          # 0-100
    
    # Explanations
    summary_ko: str
    summary_en: str
    match_reasons: List[str]          # Why they match


# ===========================================
# ML COMPATIBILITY ANALYZER
# ===========================================

class MLCompatibilityAnalyzer:
    """
    ML-based compatibility analyzer using Korean sentence embeddings.
    
    Uses jhgan/ko-sroberta-multitask for semantic similarity.
    Falls back to keyword matching if ML not available.
    """
    
    def __init__(self):
        self.model = None
        self.embedding_cache: Dict[str, np.ndarray] = {}
        self._load_model()
    
    def _load_model(self):
        """Load the Korean sentence transformer model."""
        if not SENTENCE_TRANSFORMER_AVAILABLE:
            logger.warning("Using fallback similarity (no ML)")
            return
        
        try:
            # Use Korean SBERT model
            self.model = SentenceTransformer('jhgan/ko-sroberta-multitask')
            logger.info("Loaded ko-sroberta for compatibility analysis")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
    
    @property
    def is_ml_available(self) -> bool:
        return self.model is not None
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text with caching."""
        if text in self.embedding_cache:
            return self.embedding_cache[text]
        
        if self.model is None:
            # Return zero vector as fallback
            return np.zeros(768)
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        self.embedding_cache[text] = embedding
        return embedding
    
    def get_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for multiple texts."""
        if not texts:
            return np.array([])
            
        if self.model is None:
            return np.zeros((len(texts), 768))
        
        # Check cache first
        uncached = [t for t in texts if t not in self.embedding_cache]
        
        if uncached:
            embeddings = self.model.encode(uncached, convert_to_numpy=True)
            for text, emb in zip(uncached, embeddings):
                self.embedding_cache[text] = emb
        
        return np.array([self.embedding_cache[t] for t in texts])
    
    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    def find_semantic_matches(
        self,
        list_a: List[str],
        list_b: List[str],
        threshold: float = 0.65
    ) -> List[Dict[str, Any]]:
        """
        Find semantically similar items between two lists.
        
        Returns pairs with similarity >= threshold.
        """
        if not list_a or not list_b:
            return []
        
        matches = []
        
        # If ML available, use embeddings
        if self.model is not None:
            embeddings_a = self.get_embeddings_batch(list_a)
            embeddings_b = self.get_embeddings_batch(list_b)
            
            for i, (text_a, emb_a) in enumerate(zip(list_a, embeddings_a)):
                for j, (text_b, emb_b) in enumerate(zip(list_b, embeddings_b)):
                    similarity = self.cosine_similarity(emb_a, emb_b)
                    
                    if similarity >= threshold:
                        matches.append({
                            "item_a": text_a,
                            "item_b": text_b,
                            "similarity": round(similarity, 3),
                            "is_exact": text_a.lower() == text_b.lower()
                        })
        else:
            # Fallback: simple string matching
            for text_a in list_a:
                for text_b in list_b:
                    # Check for exact match or substring
                    if text_a.lower() == text_b.lower():
                        matches.append({
                            "item_a": text_a,
                            "item_b": text_b,
                            "similarity": 1.0,
                            "is_exact": True
                        })
                    elif text_a.lower() in text_b.lower() or text_b.lower() in text_a.lower():
                        matches.append({
                            "item_a": text_a,
                            "item_b": text_b,
                            "similarity": 0.7,
                            "is_exact": False
                        })
        
        # Sort by similarity
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Remove duplicates (keep highest similarity)
        seen = set()
        unique_matches = []
        for m in matches:
            key = (m["item_a"], m["item_b"])
            if key not in seen:
                seen.add(key)
                unique_matches.append(m)
        
        return unique_matches
    
    def analyze_compatibility(
        self,
        user_likes: List[str],
        user_dislikes: List[str],
        avatar_likes: List[str],
        avatar_dislikes: List[str],
        user_traits: List[str] = None,
        avatar_traits: List[str] = None
    ) -> CompatibilityResult:
        """
        Analyze compatibility using ML embeddings.
        
        Considers:
        1. Semantic similarity between likes
        2. Shared dislikes
        3. Conflicts (user likes what avatar dislikes)
        4. Personality trait compatibility
        """
        user_traits = user_traits or []
        avatar_traits = avatar_traits or []
        
        # ===========================================
        # 1. INTEREST MATCHING (Likes)
        # ===========================================
        like_matches = self.find_semantic_matches(
            user_likes, avatar_likes, threshold=0.65
        )
        
        # Score: More matches = higher score
        like_score = min(100, len(like_matches) * 20)
        
        # ===========================================
        # 2. SHARED DISLIKES (Bonding over shared dislikes)
        # ===========================================
        dislike_matches = self.find_semantic_matches(
            user_dislikes, avatar_dislikes, threshold=0.7
        )
        
        dislike_score = min(30, len(dislike_matches) * 10)
        
        # ===========================================
        # 3. CONFLICT DETECTION
        # ===========================================
        # User likes what avatar dislikes? Bad!
        conflicts_1 = self.find_semantic_matches(
            user_likes, avatar_dislikes, threshold=0.75
        )
        
        # Avatar likes what user dislikes? Also bad!
        conflicts_2 = self.find_semantic_matches(
            avatar_likes, user_dislikes, threshold=0.75
        )
        
        conflict_penalty = min(40, (len(conflicts_1) + len(conflicts_2)) * 15)
        
        # ===========================================
        # 4. PERSONALITY MATCHING
        # ===========================================
        personality_match = 50.0  # Default
        
        if user_traits and avatar_traits:
            trait_matches = self.find_semantic_matches(
                user_traits, avatar_traits, threshold=0.6
            )
            personality_match = min(100, 50 + len(trait_matches) * 15)
        
        # ===========================================
        # 5. CALCULATE FINAL SCORE
        # ===========================================
        base_score = 50.0
        
        final_score = (
            base_score +
            (like_score * 0.4) +           # 40% weight on likes
            (dislike_score * 0.15) +        # 15% weight on shared dislikes
            (personality_match * 0.15) -    # 15% weight on personality
            conflict_penalty                 # Penalty for conflicts
        )
        
        final_score = max(0, min(100, final_score))
        
        # ===========================================
        # 6. DETERMINE CHEMISTRY LEVEL
        # ===========================================
        if final_score >= 80:
            chemistry_level = "excellent"
        elif final_score >= 60:
            chemistry_level = "good"
        elif final_score >= 40:
            chemistry_level = "okay"
        else:
            chemistry_level = "low"
        
        # ===========================================
        # 7. SUGGEST TOPICS
        # ===========================================
        suggested_topics = []
        for match in like_matches[:5]:
            if match["item_a"] not in suggested_topics:
                suggested_topics.append(match["item_a"])
            if match["item_b"] not in suggested_topics:
                suggested_topics.append(match["item_b"])
        
        # Avoid topics = dislikes from either side
        avoid_topics = list(set(user_dislikes) | set(avatar_dislikes))
        
        # ===========================================
        # 8. GENERATE EXPLANATIONS
        # ===========================================
        match_reasons = self._generate_match_reasons(
            like_matches, dislike_matches, personality_match
        )
        
        summary_ko = self._generate_summary_ko(
            final_score, chemistry_level, like_matches, suggested_topics
        )
        
        summary_en = self._generate_summary_en(
            final_score, chemistry_level, like_matches
        )
        
        return CompatibilityResult(
            score=round(final_score, 1),
            chemistry_level=chemistry_level,
            common_interests=like_matches,
            suggested_topics=suggested_topics[:5],
            avoid_topics=avoid_topics,
            personality_match=round(personality_match, 1),
            summary_ko=summary_ko,
            summary_en=summary_en,
            match_reasons=match_reasons
        )
    
    def _generate_match_reasons(
        self,
        like_matches: List[Dict],
        dislike_matches: List[Dict],
        personality_match: float
    ) -> List[str]:
        """Generate human-readable match reasons."""
        reasons = []
        
        if like_matches:
            top_match = like_matches[0]
            if top_match["is_exact"]:
                reasons.append(f"둘 다 '{top_match['item_a']}'을(를) 좋아해요!")
            else:
                reasons.append(
                    f"'{top_match['item_a']}'와(과) '{top_match['item_b']}'에 "
                    f"관심이 있어요 (유사도: {int(top_match['similarity']*100)}%)"
                )
        
        if len(like_matches) > 1:
            reasons.append(f"총 {len(like_matches)}개의 공통 관심사가 있어요!")
        
        if dislike_matches:
            reasons.append(f"싫어하는 것도 비슷해요!")
        
        if personality_match >= 70:
            reasons.append("성격이 잘 맞아요! 😊")
        
        return reasons
    
    def _generate_summary_ko(
        self,
        score: float,
        chemistry_level: str,
        matches: List[Dict],
        topics: List[str]
    ) -> str:
        """Generate Korean summary."""
        
        level_emoji = {
            "excellent": "🎉",
            "good": "😊",
            "okay": "👍",
            "low": "🤔"
        }
        
        level_text = {
            "excellent": "아주 잘 맞아요!",
            "good": "잘 맞는 편이에요!",
            "okay": "대화할 주제가 있어요.",
            "low": "새로운 주제를 발견해 보세요."
        }
        
        emoji = level_emoji.get(chemistry_level, "")
        text = level_text.get(chemistry_level, "")
        
        summary = f"{emoji} 궁합 {int(score)}점! {text}"
        
        if topics:
            summary += f" 추천 주제: {', '.join(topics[:3])}"
        
        return summary
    
    def _generate_summary_en(
        self,
        score: float,
        chemistry_level: str,
        matches: List[Dict]
    ) -> str:
        """Generate English summary."""
        
        level_text = {
            "excellent": "Excellent match!",
            "good": "Good compatibility!",
            "okay": "Some common ground.",
            "low": "Different interests."
        }
        
        text = level_text.get(chemistry_level, "")
        
        return f"Compatibility: {int(score)}% - {text}"


# ===========================================
# SINGLETON INSTANCE
# ===========================================

_analyzer: Optional[MLCompatibilityAnalyzer] = None


def get_compatibility_analyzer() -> MLCompatibilityAnalyzer:
    """Get or create the compatibility analyzer."""
    global _analyzer
    if _analyzer is None:
        _analyzer = MLCompatibilityAnalyzer()
    return _analyzer


def analyze_compatibility(
    user_likes: List[str],
    user_dislikes: List[str],
    avatar_likes: List[str],
    avatar_dislikes: List[str],
    user_traits: List[str] = None,
    avatar_traits: List[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to analyze compatibility.
    
    Returns dict with score, matches, suggestions, etc.
    """
    analyzer = get_compatibility_analyzer()
    result = analyzer.analyze_compatibility(
        user_likes, user_dislikes,
        avatar_likes, avatar_dislikes,
        user_traits, avatar_traits
    )
    
    return {
        "score": result.score,
        "chemistry_level": result.chemistry_level,
        "common_interests": result.common_interests,
        "suggested_topics": result.suggested_topics,
        "avoid_topics": result.avoid_topics,
        "personality_match": result.personality_match,
        "summary_ko": result.summary_ko,
        "summary_en": result.summary_en,
        "match_reasons": result.match_reasons,
        "ml_available": analyzer.is_ml_available
    }
