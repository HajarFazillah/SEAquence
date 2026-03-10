"""
Korean NLP Service
Comprehensive NLP capabilities for Korean language processing
Using Korean BERT, KoNLPy, and sentence transformers
"""

import logging
import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from functools import lru_cache

logger = logging.getLogger(__name__)

# ===========================================
# Check Available Libraries
# ===========================================

SENTENCE_TRANSFORMERS_AVAILABLE = False
TORCH_AVAILABLE = False
KONLPY_AVAILABLE = False
SKLEARN_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    import torch
    SENTENCE_TRANSFORMERS_AVAILABLE = True
    TORCH_AVAILABLE = True
except ImportError:
    pass

try:
    from konlpy.tag import Okt, Komoran
    KONLPY_AVAILABLE = True
except ImportError:
    pass

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    pass


# ===========================================
# Data Classes
# ===========================================

@dataclass
class MorphemeAnalysis:
    """Result of morpheme analysis."""
    text: str
    morphemes: List[Tuple[str, str]]  # (word, POS tag)
    nouns: List[str]
    verbs: List[str]
    adjectives: List[str]
    particles: List[str]
    endings: List[str]


@dataclass
class SimilarityResult:
    """Result of similarity calculation."""
    score: float
    method: str  # embedding, tfidf, character
    confidence: float


# ===========================================
# Korean Morpheme Analyzer
# ===========================================

class KoreanMorphemeAnalyzer:
    """
    Analyze Korean text into morphemes (smallest meaningful units).
    
    Uses KoNLPy (Okt/Komoran) when available, falls back to regex.
    """
    
    def __init__(self, engine: str = "okt"):
        self.engine = engine
        self._analyzer = None
        self._initialized = False
        
    def _initialize(self):
        """Initialize the morpheme analyzer."""
        if self._initialized:
            return
            
        if KONLPY_AVAILABLE:
            try:
                if self.engine == "okt":
                    self._analyzer = Okt()
                else:
                    self._analyzer = Komoran()
                logger.info(f"KoNLPy {self.engine} initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize KoNLPy: {e}")
        
        self._initialized = True
    
    def analyze(self, text: str) -> MorphemeAnalysis:
        """
        Analyze text into morphemes.
        
        Args:
            text: Korean text to analyze
            
        Returns:
            MorphemeAnalysis with morphemes and their parts of speech
        """
        self._initialize()
        
        if self._analyzer:
            return self._analyze_konlpy(text)
        else:
            return self._analyze_regex(text)
    
    def _analyze_konlpy(self, text: str) -> MorphemeAnalysis:
        """Analyze using KoNLPy."""
        morphemes = self._analyzer.pos(text)
        
        nouns = [word for word, pos in morphemes if pos.startswith('N')]
        verbs = [word for word, pos in morphemes if pos.startswith('V')]
        adjectives = [word for word, pos in morphemes if pos == 'Adjective' or pos.startswith('VA')]
        particles = [word for word, pos in morphemes if pos.startswith('J')]
        endings = [word for word, pos in morphemes if pos.startswith('E')]
        
        return MorphemeAnalysis(
            text=text,
            morphemes=morphemes,
            nouns=nouns,
            verbs=verbs,
            adjectives=adjectives,
            particles=particles,
            endings=endings
        )
    
    def _analyze_regex(self, text: str) -> MorphemeAnalysis:
        """Analyze using regex patterns (fallback)."""
        # Simple word tokenization
        words = re.findall(r'[가-힣]+', text)
        
        # Guess POS based on patterns
        nouns = []
        verbs = []
        adjectives = []
        particles = []
        endings = []
        
        verb_endings = ['다', '해', '하다', '되다', '가다', '오다']
        adj_endings = ['다운', '스러운', '적인']
        common_particles = ['은', '는', '이', '가', '을', '를', '에', '에서', '으로', '로']
        
        for word in words:
            if any(word.endswith(e) for e in verb_endings):
                verbs.append(word)
            elif any(word.endswith(e) for e in adj_endings):
                adjectives.append(word)
            elif word in common_particles:
                particles.append(word)
            else:
                nouns.append(word)
        
        return MorphemeAnalysis(
            text=text,
            morphemes=[(w, 'Unknown') for w in words],
            nouns=nouns,
            verbs=verbs,
            adjectives=adjectives,
            particles=particles,
            endings=endings
        )
    
    def extract_stems(self, text: str) -> List[str]:
        """Extract word stems from text."""
        self._initialize()
        
        if self._analyzer and hasattr(self._analyzer, 'morphs'):
            return self._analyzer.morphs(text)
        
        # Fallback: return unique Korean words
        return list(set(re.findall(r'[가-힣]+', text)))
    
    def extract_nouns(self, text: str) -> List[str]:
        """Extract nouns from text."""
        self._initialize()
        
        if self._analyzer and hasattr(self._analyzer, 'nouns'):
            return self._analyzer.nouns(text)
        
        analysis = self.analyze(text)
        return analysis.nouns


# ===========================================
# Korean Sentence Embedding Service
# ===========================================

class KoreanEmbeddingService:
    """
    Generate Korean sentence embeddings.
    
    Uses:
    1. Korean SBERT (jhgan/ko-sroberta-multitask) - Best quality
    2. Multilingual MiniLM - Good fallback
    3. TF-IDF - Basic fallback
    4. Character-based hash - Minimal fallback
    """
    
    # Model options
    MODELS = {
        "ko-sroberta": "jhgan/ko-sroberta-multitask",
        "ko-sbert-sts": "jhgan/ko-sbert-sts",
        "multilingual": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "klue": "klue/roberta-base"
    }
    
    def __init__(self, model_name: str = "ko-sroberta"):
        self.model_name = model_name
        self._model = None
        self._tfidf = None
        self._morpheme_analyzer = KoreanMorphemeAnalyzer()
        self._embedding_dim = 768
        self._is_loaded = False
        self._use_fallback = False
        
        # Cache for pre-computed embeddings
        self._embedding_cache: Dict[str, np.ndarray] = {}
        
    @property
    def is_available(self) -> bool:
        return SENTENCE_TRANSFORMERS_AVAILABLE
    
    @property
    def embedding_dim(self) -> int:
        return self._embedding_dim
    
    def load(self) -> bool:
        """Load the embedding model."""
        if self._is_loaded:
            return not self._use_fallback
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                model_id = self.MODELS.get(self.model_name, self.model_name)
                logger.info(f"Loading embedding model: {model_id}")
                
                self._model = SentenceTransformer(model_id)
                self._embedding_dim = self._model.get_sentence_embedding_dimension()
                self._is_loaded = True
                
                logger.info(f"Model loaded. Embedding dim: {self._embedding_dim}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
        
        # Setup fallback
        self._setup_fallback()
        return False
    
    def _setup_fallback(self):
        """Setup TF-IDF based fallback."""
        self._use_fallback = True
        self._is_loaded = True
        
        if SKLEARN_AVAILABLE:
            self._tfidf = TfidfVectorizer(
                analyzer='char_wb',
                ngram_range=(2, 4),
                max_features=768,
                lowercase=False
            )
            self._embedding_dim = 768
            logger.info("Using TF-IDF fallback")
        else:
            self._embedding_dim = 256
            logger.info("Using basic character fallback")
    
    def encode(
        self,
        text: Union[str, List[str]],
        normalize: bool = True
    ) -> np.ndarray:
        """
        Encode text(s) to embedding vectors.
        
        Args:
            text: Single text or list of texts
            normalize: Whether to L2 normalize
            
        Returns:
            Embedding array of shape (n, embedding_dim)
        """
        if not self._is_loaded:
            self.load()
        
        if isinstance(text, str):
            texts = [text]
            single = True
        else:
            texts = text
            single = False
        
        # Check cache
        cache_key = hash(tuple(texts))
        if cache_key in self._embedding_cache:
            embeddings = self._embedding_cache[cache_key]
        else:
            embeddings = self._encode_impl(texts, normalize)
            # Cache if small batch
            if len(texts) <= 10:
                self._embedding_cache[cache_key] = embeddings
        
        return embeddings[0] if single else embeddings
    
    def _encode_impl(self, texts: List[str], normalize: bool) -> np.ndarray:
        """Internal encoding implementation."""
        if self._model:
            embeddings = self._model.encode(
                texts,
                normalize_embeddings=normalize,
                show_progress_bar=False
            )
            return np.array(embeddings)
        
        elif self._tfidf:
            try:
                embeddings = self._tfidf.fit_transform(texts).toarray()
            except:
                embeddings = np.zeros((len(texts), self._embedding_dim))
            
            if normalize:
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                embeddings = embeddings / (norms + 1e-8)
            
            return embeddings
        
        else:
            # Basic fallback
            embeddings = np.array([self._char_encode(t) for t in texts])
            return embeddings
    
    def _char_encode(self, text: str) -> np.ndarray:
        """Character-based encoding fallback."""
        vec = np.zeros(self._embedding_dim)
        
        for i, char in enumerate(text):
            idx = ord(char) % self._embedding_dim
            vec[idx] += 1.0 / (i + 1)  # Weighted by position
        
        # Normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        
        return vec
    
    def similarity(self, text1: str, text2: str) -> SimilarityResult:
        """
        Calculate semantic similarity between two texts.
        
        Returns:
            SimilarityResult with score and metadata
        """
        emb1 = self.encode(text1)
        emb2 = self.encode(text2)
        
        score = float(np.dot(emb1, emb2))
        
        method = "embedding" if self._model else ("tfidf" if self._tfidf else "character")
        confidence = 0.9 if self._model else (0.6 if self._tfidf else 0.3)
        
        return SimilarityResult(
            score=score,
            method=method,
            confidence=confidence
        )
    
    def find_most_similar(
        self,
        query: str,
        candidates: List[str],
        top_k: int = 5
    ) -> List[Tuple[str, float, int]]:
        """
        Find most similar texts to query.
        
        Returns:
            List of (text, score, original_index) tuples
        """
        query_emb = self.encode(query)
        candidate_embs = self.encode(candidates)
        
        # Compute similarities
        similarities = np.dot(candidate_embs, query_emb)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append((
                candidates[idx],
                float(similarities[idx]),
                int(idx)
            ))
        
        return results
    
    def cluster(
        self,
        texts: List[str],
        n_clusters: int = 5
    ) -> Dict[int, List[str]]:
        """
        Cluster texts by semantic similarity.
        
        Returns:
            Dict mapping cluster_id to list of texts
        """
        if not SKLEARN_AVAILABLE:
            return {0: texts}
        
        from sklearn.cluster import KMeans
        
        embeddings = self.encode(texts)
        
        n_clusters = min(n_clusters, len(texts))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        
        clusters = {}
        for idx, label in enumerate(labels):
            label = int(label)
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(texts[idx])
        
        return clusters


# ===========================================
# Singleton Instances
# ===========================================

morpheme_analyzer = KoreanMorphemeAnalyzer()
embedding_service = KoreanEmbeddingService()
