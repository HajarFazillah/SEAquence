"""
Sophisticated Politeness Analyzer
Combines rule-based patterns, ML classification, and semantic analysis
"""

import logging
import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class FormalityLevel(str, Enum):
    """Korean speech formality levels."""
    INFORMAL = "informal"       # 반말 (해체)
    POLITE = "polite"           # 해요체
    FORMAL = "formal"           # 하십시오체
    VERY_FORMAL = "very_formal" # 합쇼체
    MIXED = "mixed"             # 혼용


@dataclass
class TokenAnalysis:
    """Analysis result for a single token."""
    token: str
    position: int
    
    # Detected characteristics
    is_ending: bool = False
    ending_type: Optional[str] = None  # formal, polite, informal
    
    is_honorific: bool = False
    honorific_type: Optional[str] = None  # verb, noun, prefix
    
    is_humble: bool = False
    is_particle: bool = False
    
    # Correction info
    needs_correction: bool = False
    suggested_correction: Optional[str] = None
    correction_reason: Optional[str] = None


@dataclass
class SentenceAnalysis:
    """Analysis result for a sentence."""
    sentence: str
    
    # Detected level
    formality_level: FormalityLevel
    confidence: float
    
    # Score breakdown
    formal_score: float = 0.0
    polite_score: float = 0.0
    informal_score: float = 0.0
    
    # Features
    has_honorific_verb: bool = False
    has_honorific_noun: bool = False
    has_subject_honorific: bool = False  # -시-
    has_humble_form: bool = False
    
    # Token-level
    tokens: List[TokenAnalysis] = field(default_factory=list)
    
    # Issues found
    issues: List[str] = field(default_factory=list)


@dataclass
class PolitenessAnalysisResult:
    """Complete politeness analysis result."""
    text: str
    
    # Overall assessment
    overall_level: FormalityLevel
    overall_level_ko: str
    overall_confidence: float
    overall_score: int  # 0-100
    
    # Expected vs actual
    expected_level: Optional[FormalityLevel] = None
    is_appropriate: bool = True
    
    # Detailed breakdown
    score_breakdown: Dict[str, float] = field(default_factory=dict)
    feature_breakdown: Dict[str, bool] = field(default_factory=dict)
    
    # Per-sentence analysis
    sentences: List[SentenceAnalysis] = field(default_factory=list)
    
    # Corrections
    corrections: List[Dict[str, Any]] = field(default_factory=list)
    
    # Feedback
    feedback_ko: str = ""
    feedback_en: str = ""
    
    # Method info
    analysis_method: str = "hybrid"


class SophisticatedPolitenessAnalyzer:
    """
    Advanced politeness analyzer for Korean text.
    
    Combines multiple analysis methods:
    1. **Rule-based Pattern Matching** - Sentence endings, particles
    2. **Morphological Analysis** - Using KoNLPy when available
    3. **Semantic Analysis** - Using embeddings
    4. **Context Awareness** - Considering conversation flow
    
    Features detected:
    - Sentence endings (formal: -습니다, polite: -요, informal: -어/아)
    - Honorific verbs (드리다, 여쭙다, 계시다)
    - Honorific nouns (말씀, 진지, 댁)
    - Subject honorific marker (-시-)
    - Humble forms (저, 저희)
    - Formal particles (께서, 께)
    """
    
    # ===========================================
    # Linguistic Patterns
    # ===========================================
    
    # Sentence endings by formality
    ENDINGS = {
        "formal": {
            "patterns": [
                r"습니다[.?!]?$",
                r"습니까[.?!]?$",
                r"십시오[.?!]?$",
                r"옵니다[.?!]?$",
                r"셨습니다[.?!]?$",
                r"겠습니다[.?!]?$",
                r"였습니다[.?!]?$",
            ],
            "examples": ["합니다", "입니다", "하십시오"]
        },
        "polite": {
            "patterns": [
                r"[아어]요[.?!]?$",
                r"세요[.?!]?$",
                r"죠[.?!]?$",
                r"네요[.?!]?$",
                r"군요[.?!]?$",
                r"거든요[.?!]?$",
                r"잖아요[.?!]?$",
                r"래요[.?!]?$",
                r"ㄹ게요[.?!]?$",
                r"ㄹ까요[.?!]?$",
            ],
            "examples": ["해요", "가요", "하세요"]
        },
        "informal": {
            "patterns": [
                r"[아어][.?!]?$",
                r"지[.?!]?$",
                r"냐[.?!]?$",
                r"야[.?!]?$",
                r"거든[.?!]?$",
                r"잖아[.?!]?$",
                r"래[.?!]?$",
                r"자[.?!]?$",
                r"ㄹ게[.?!]?$",
                r"ㄹ까[.?!]?$",
            ],
            "examples": ["해", "가", "먹어", "뭐야"]
        }
    }
    
    # Honorific verbs (높임말 동사)
    HONORIFIC_VERBS = {
        "드리다": {"base": "주다", "type": "humble", "explanation": "주다의 겸양어"},
        "여쭙다": {"base": "묻다", "type": "humble", "explanation": "묻다의 겸양어"},
        "여쭤보다": {"base": "물어보다", "type": "humble", "explanation": "물어보다의 겸양어"},
        "뵙다": {"base": "보다/만나다", "type": "humble", "explanation": "만나다의 겸양어"},
        "계시다": {"base": "있다", "type": "honorific", "explanation": "있다의 높임말"},
        "주무시다": {"base": "자다", "type": "honorific", "explanation": "자다의 높임말"},
        "잡수시다": {"base": "먹다", "type": "honorific", "explanation": "먹다의 높임말"},
        "드시다": {"base": "먹다/마시다", "type": "honorific", "explanation": "먹다의 높임말"},
        "돌아가시다": {"base": "죽다", "type": "honorific", "explanation": "죽다의 높임말"},
        "편찮으시다": {"base": "아프다", "type": "honorific", "explanation": "아프다의 높임말"},
        "말씀하시다": {"base": "말하다", "type": "honorific", "explanation": "말하다의 높임말"},
    }
    
    # Honorific nouns (높임말 명사)
    HONORIFIC_NOUNS = {
        "말씀": {"base": "말", "explanation": "말의 높임말"},
        "진지": {"base": "밥", "explanation": "밥의 높임말"},
        "댁": {"base": "집", "explanation": "집의 높임말"},
        "성함": {"base": "이름", "explanation": "이름의 높임말"},
        "연세": {"base": "나이", "explanation": "나이의 높임말"},
        "생신": {"base": "생일", "explanation": "생일의 높임말"},
        "병환": {"base": "병", "explanation": "병의 높임말"},
        "춘추": {"base": "나이", "explanation": "나이의 높임말 (문어체)"},
    }
    
    # Humble pronouns
    HUMBLE_PRONOUNS = ["저", "저희", "소인", "소생"]
    
    # Formal particles
    FORMAL_PARTICLES = ["께서", "께", "님"]
    
    # Level names
    LEVEL_NAMES = {
        FormalityLevel.INFORMAL: ("반말", "Informal"),
        FormalityLevel.POLITE: ("존댓말", "Polite"),
        FormalityLevel.FORMAL: ("격식체", "Formal"),
        FormalityLevel.VERY_FORMAL: ("극존칭", "Very Formal"),
        FormalityLevel.MIXED: ("혼용", "Mixed"),
    }
    
    def __init__(self):
        self._compiled_patterns = {}
        self._embedding_service = None
        self._morpheme_analyzer = None
        self._formality_embeddings = {}
        self._initialized = False
    
    def _initialize(self):
        """Initialize the analyzer."""
        if self._initialized:
            return
        
        # Compile regex patterns
        for level, data in self.ENDINGS.items():
            self._compiled_patterns[level] = [
                re.compile(p) for p in data["patterns"]
            ]
        
        # Try to load ML services
        try:
            from app.ml.korean_nlp import embedding_service, morpheme_analyzer
            self._embedding_service = embedding_service
            self._morpheme_analyzer = morpheme_analyzer
            self._embedding_service.load()
            
            # Pre-compute formality embeddings
            self._compute_formality_embeddings()
            
        except Exception as e:
            logger.warning(f"ML services not available: {e}")
        
        self._initialized = True
    
    def _compute_formality_embeddings(self):
        """Pre-compute embeddings for formality levels."""
        if not self._embedding_service:
            return
        
        examples = {
            "formal": "안녕하십니까 감사합니다 무엇을 도와드릴까요 알겠습니다",
            "polite": "안녕하세요 감사해요 뭐 도와드릴까요 알겠어요",
            "informal": "안녕 고마워 뭐 도와줄까 알았어",
        }
        
        for level, text in examples.items():
            self._formality_embeddings[level] = self._embedding_service.encode(text)
    
    def analyze(
        self,
        text: str,
        target_role: Optional[str] = None,
        target_age: Optional[int] = None,
        user_age: int = 22,
        context: List[str] = None
    ) -> PolitenessAnalysisResult:
        """
        Perform comprehensive politeness analysis.
        
        Args:
            text: Korean text to analyze
            target_role: Role of person being addressed (junior, friend, senior, professor, boss)
            target_age: Age of target person
            user_age: Age of speaker
            context: Previous conversation messages
            
        Returns:
            PolitenessAnalysisResult with detailed analysis
        """
        self._initialize()
        
        # Split into sentences
        sentences = self._split_sentences(text)
        
        # Analyze each sentence
        sentence_analyses = [
            self._analyze_sentence(s) for s in sentences
        ]
        
        # Aggregate results
        overall_level, overall_confidence = self._aggregate_levels(sentence_analyses)
        
        # Calculate overall score
        overall_score = self._calculate_score(sentence_analyses, overall_level)
        
        # Check appropriateness
        expected_level = self._determine_expected_level(target_role, target_age, user_age)
        is_appropriate = self._check_appropriateness(overall_level, expected_level)
        
        # Generate corrections
        corrections = self._generate_corrections(
            text, sentence_analyses, expected_level
        )
        
        # Generate feedback
        feedback_ko, feedback_en = self._generate_feedback(
            overall_level, expected_level, is_appropriate, corrections
        )
        
        # Build score breakdown
        score_breakdown = self._build_score_breakdown(sentence_analyses)
        
        # Build feature breakdown
        feature_breakdown = self._build_feature_breakdown(sentence_analyses)
        
        level_ko, level_en = self.LEVEL_NAMES.get(
            overall_level, ("알 수 없음", "Unknown")
        )
        
        return PolitenessAnalysisResult(
            text=text,
            overall_level=overall_level,
            overall_level_ko=level_ko,
            overall_confidence=overall_confidence,
            overall_score=overall_score,
            expected_level=expected_level,
            is_appropriate=is_appropriate,
            score_breakdown=score_breakdown,
            feature_breakdown=feature_breakdown,
            sentences=sentence_analyses,
            corrections=corrections,
            feedback_ko=feedback_ko,
            feedback_en=feedback_en,
            analysis_method="hybrid" if self._embedding_service else "rule-based"
        )
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Split by sentence-ending punctuation
        sentences = re.split(r'([.?!]+)', text)
        
        # Recombine with punctuation
        result = []
        i = 0
        while i < len(sentences):
            s = sentences[i].strip()
            if s:
                if i + 1 < len(sentences) and re.match(r'^[.?!]+$', sentences[i + 1]):
                    s += sentences[i + 1]
                    i += 1
                result.append(s)
            i += 1
        
        # If no splits, return original
        if not result:
            result = [text.strip()]
        
        return result
    
    def _analyze_sentence(self, sentence: str) -> SentenceAnalysis:
        """Analyze a single sentence."""
        # Detect ending type
        formal_score, polite_score, informal_score = self._score_endings(sentence)
        
        # Detect honorific features
        has_hon_verb = any(hv in sentence for hv in self.HONORIFIC_VERBS)
        has_hon_noun = any(hn in sentence for hn in self.HONORIFIC_NOUNS)
        has_subj_hon = bool(re.search(r'[으시|시]', sentence))
        has_humble = any(hp in sentence for hp in self.HUMBLE_PRONOUNS)
        
        # Boost scores based on features
        if has_hon_verb or has_hon_noun:
            formal_score += 0.2
        if has_subj_hon:
            formal_score += 0.1
            polite_score += 0.05
        if has_humble:
            formal_score += 0.1
        
        # Determine level
        formality_level, confidence = self._determine_sentence_level(
            formal_score, polite_score, informal_score
        )
        
        # Token analysis
        tokens = self._analyze_tokens(sentence, formality_level)
        
        # Find issues
        issues = self._find_issues(sentence, formality_level, tokens)
        
        return SentenceAnalysis(
            sentence=sentence,
            formality_level=formality_level,
            confidence=confidence,
            formal_score=formal_score,
            polite_score=polite_score,
            informal_score=informal_score,
            has_honorific_verb=has_hon_verb,
            has_honorific_noun=has_hon_noun,
            has_subject_honorific=has_subj_hon,
            has_humble_form=has_humble,
            tokens=tokens,
            issues=issues
        )
    
    def _score_endings(self, sentence: str) -> Tuple[float, float, float]:
        """Score sentence endings."""
        formal_score = 0.0
        polite_score = 0.0
        informal_score = 0.0
        
        for pattern in self._compiled_patterns.get("formal", []):
            if pattern.search(sentence):
                formal_score += 0.5
                break
        
        for pattern in self._compiled_patterns.get("polite", []):
            if pattern.search(sentence):
                polite_score += 0.5
                break
        
        for pattern in self._compiled_patterns.get("informal", []):
            if pattern.search(sentence):
                informal_score += 0.5
                break
        
        # Use semantic analysis if available
        if self._embedding_service and self._formality_embeddings:
            semantic_scores = self._semantic_formality_scores(sentence)
            
            formal_score = 0.6 * formal_score + 0.4 * semantic_scores.get("formal", 0)
            polite_score = 0.6 * polite_score + 0.4 * semantic_scores.get("polite", 0)
            informal_score = 0.6 * informal_score + 0.4 * semantic_scores.get("informal", 0)
        
        return formal_score, polite_score, informal_score
    
    def _semantic_formality_scores(self, text: str) -> Dict[str, float]:
        """Calculate formality scores using semantic similarity."""
        if not self._embedding_service or not self._formality_embeddings:
            return {}
        
        text_emb = self._embedding_service.encode(text)
        
        scores = {}
        for level, level_emb in self._formality_embeddings.items():
            sim = self._embedding_service.similarity(text, " ").score
            # Use dot product as similarity
            scores[level] = max(0, float(np.dot(text_emb, level_emb)))
        
        # Normalize
        total = sum(scores.values()) + 1e-6
        scores = {k: v / total for k, v in scores.items()}
        
        return scores
    
    def _determine_sentence_level(
        self,
        formal: float,
        polite: float,
        informal: float
    ) -> Tuple[FormalityLevel, float]:
        """Determine formality level from scores."""
        scores = {
            FormalityLevel.FORMAL: formal,
            FormalityLevel.POLITE: polite,
            FormalityLevel.INFORMAL: informal
        }
        
        # Check for mixed
        non_zero = sum(1 for s in scores.values() if s > 0.2)
        if non_zero >= 2:
            max_score = max(scores.values())
            second_max = sorted(scores.values())[-2]
            if second_max / (max_score + 1e-6) > 0.5:
                return FormalityLevel.MIXED, 0.7
        
        # Get dominant
        dominant = max(scores, key=scores.get)
        confidence = scores[dominant] / (sum(scores.values()) + 1e-6)
        
        return dominant, min(1.0, confidence)
    
    def _analyze_tokens(
        self,
        sentence: str,
        expected_level: FormalityLevel
    ) -> List[TokenAnalysis]:
        """Analyze individual tokens."""
        tokens = []
        words = sentence.split()
        
        for pos, word in enumerate(words):
            token = TokenAnalysis(token=word, position=pos)
            
            # Check if it's a sentence-ending word
            if pos == len(words) - 1 or re.search(r'[.?!]$', word):
                token.is_ending = True
                token.ending_type = self._detect_ending_type(word)
            
            # Check for honorific verb
            for hon_verb, info in self.HONORIFIC_VERBS.items():
                if hon_verb in word:
                    token.is_honorific = True
                    token.honorific_type = info["type"]
                    break
            
            # Check for honorific noun
            for hon_noun in self.HONORIFIC_NOUNS:
                if hon_noun in word:
                    token.is_honorific = True
                    token.honorific_type = "noun"
                    break
            
            # Check for humble pronoun
            if word in self.HUMBLE_PRONOUNS:
                token.is_humble = True
            
            # Check if correction needed
            if token.is_ending and token.ending_type:
                if not self._is_ending_appropriate(token.ending_type, expected_level):
                    token.needs_correction = True
                    token.suggested_correction = self._suggest_ending_correction(
                        word, expected_level
                    )
                    token.correction_reason = f"{expected_level.value} 어미를 사용하세요"
            
            tokens.append(token)
        
        return tokens
    
    def _detect_ending_type(self, word: str) -> Optional[str]:
        """Detect the type of sentence ending."""
        for level, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(word):
                    return level
        return None
    
    def _is_ending_appropriate(
        self,
        ending_type: str,
        expected_level: FormalityLevel
    ) -> bool:
        """Check if ending type matches expected level."""
        mapping = {
            FormalityLevel.FORMAL: ["formal"],
            FormalityLevel.POLITE: ["formal", "polite"],
            FormalityLevel.INFORMAL: ["informal", "polite"],
            FormalityLevel.MIXED: ["formal", "polite", "informal"],
        }
        
        allowed = mapping.get(expected_level, ["polite"])
        return ending_type in allowed
    
    def _suggest_ending_correction(
        self,
        word: str,
        expected_level: FormalityLevel
    ) -> str:
        """Suggest a correction for wrong ending."""
        # Simple replacements
        if expected_level == FormalityLevel.FORMAL:
            corrections = {
                "해요": "합니다",
                "가요": "갑니다",
                "있어요": "있습니다",
                "해": "합니다",
                "가": "갑니다",
            }
        elif expected_level == FormalityLevel.POLITE:
            corrections = {
                "합니다": "해요",
                "갑니다": "가요",
                "해": "해요",
                "가": "가요",
            }
        else:
            corrections = {}
        
        for wrong, right in corrections.items():
            if word.endswith(wrong):
                return word[:-len(wrong)] + right
        
        return word
    
    def _find_issues(
        self,
        sentence: str,
        level: FormalityLevel,
        tokens: List[TokenAnalysis]
    ) -> List[str]:
        """Find issues in the sentence."""
        issues = []
        
        # Check for level mixing
        ending_types = [t.ending_type for t in tokens if t.is_ending and t.ending_type]
        if len(set(ending_types)) > 1:
            issues.append("한 문장에서 여러 격식 수준이 혼용되었습니다")
        
        # Check for missing honorifics in formal context
        if level == FormalityLevel.FORMAL:
            has_honorific = any(t.is_honorific for t in tokens)
            if not has_honorific and "교수" in sentence or "사장" in sentence:
                issues.append("높임 표현이 필요할 수 있습니다")
        
        return issues
    
    def _aggregate_levels(
        self,
        analyses: List[SentenceAnalysis]
    ) -> Tuple[FormalityLevel, float]:
        """Aggregate sentence-level results."""
        if not analyses:
            return FormalityLevel.POLITE, 0.5
        
        # Count levels
        level_counts = {}
        total_confidence = 0
        
        for analysis in analyses:
            level = analysis.formality_level
            level_counts[level] = level_counts.get(level, 0) + 1
            total_confidence += analysis.confidence
        
        # Check for mixing
        if len(level_counts) > 1:
            return FormalityLevel.MIXED, 0.7
        
        # Return dominant
        dominant = max(level_counts, key=level_counts.get)
        avg_confidence = total_confidence / len(analyses)
        
        return dominant, avg_confidence
    
    def _calculate_score(
        self,
        analyses: List[SentenceAnalysis],
        overall_level: FormalityLevel
    ) -> int:
        """Calculate overall score (0-100)."""
        if not analyses:
            return 50
        
        base_score = 70
        
        # Penalty for mixing
        if overall_level == FormalityLevel.MIXED:
            base_score -= 15
        
        # Bonus for consistency
        levels = [a.formality_level for a in analyses]
        if len(set(levels)) == 1:
            base_score += 10
        
        # Bonus for honorifics in formal context
        if overall_level in [FormalityLevel.FORMAL, FormalityLevel.POLITE]:
            has_honorific = any(a.has_honorific_verb or a.has_honorific_noun for a in analyses)
            if has_honorific:
                base_score += 10
        
        # Penalty for issues
        total_issues = sum(len(a.issues) for a in analyses)
        base_score -= total_issues * 5
        
        return max(0, min(100, base_score))
    
    def _determine_expected_level(
        self,
        target_role: Optional[str],
        target_age: Optional[int],
        user_age: int
    ) -> Optional[FormalityLevel]:
        """Determine expected formality level based on context."""
        if not target_role:
            return None
        
        role_levels = {
            "junior": FormalityLevel.INFORMAL,
            "friend": FormalityLevel.INFORMAL,
            "acquaintance": FormalityLevel.POLITE,
            "senior": FormalityLevel.POLITE,
            "professor": FormalityLevel.FORMAL,
            "boss": FormalityLevel.FORMAL,
            "customer": FormalityLevel.FORMAL,
        }
        
        expected = role_levels.get(target_role, FormalityLevel.POLITE)
        
        # Age adjustment
        if target_age:
            age_diff = target_age - user_age
            if age_diff > 20:
                expected = FormalityLevel.FORMAL
            elif age_diff < -10:
                expected = FormalityLevel.INFORMAL
        
        return expected
    
    def _check_appropriateness(
        self,
        actual: FormalityLevel,
        expected: Optional[FormalityLevel]
    ) -> bool:
        """Check if actual level is appropriate."""
        if not expected:
            return True
        
        # Acceptable combinations
        acceptable = {
            FormalityLevel.FORMAL: [FormalityLevel.FORMAL, FormalityLevel.VERY_FORMAL],
            FormalityLevel.POLITE: [FormalityLevel.POLITE, FormalityLevel.FORMAL],
            FormalityLevel.INFORMAL: [FormalityLevel.INFORMAL, FormalityLevel.POLITE],
        }
        
        return actual in acceptable.get(expected, [expected])
    
    def _generate_corrections(
        self,
        text: str,
        analyses: List[SentenceAnalysis],
        expected: Optional[FormalityLevel]
    ) -> List[Dict[str, Any]]:
        """Generate correction suggestions."""
        corrections = []
        
        for analysis in analyses:
            for token in analysis.tokens:
                if token.needs_correction:
                    corrections.append({
                        "original": token.token,
                        "corrected": token.suggested_correction,
                        "reason_ko": token.correction_reason,
                        "reason_en": f"Use {expected.value} form" if expected else "Check formality",
                        "position": token.position
                    })
        
        return corrections
    
    def _generate_feedback(
        self,
        actual: FormalityLevel,
        expected: Optional[FormalityLevel],
        is_appropriate: bool,
        corrections: List[Dict]
    ) -> Tuple[str, str]:
        """Generate feedback messages."""
        actual_ko, actual_en = self.LEVEL_NAMES.get(actual, ("알 수 없음", "Unknown"))
        
        if is_appropriate:
            if actual == FormalityLevel.FORMAL:
                return (
                    f"잘했어요! {actual_ko}를 올바르게 사용했습니다. 👏",
                    f"Good job! You correctly used {actual_en}. 👏"
                )
            elif actual == FormalityLevel.POLITE:
                return (
                    f"좋아요! {actual_ko}를 잘 사용했어요.",
                    f"Nice! You used {actual_en} well."
                )
            else:
                return (
                    f"{actual_ko}를 사용했어요.",
                    f"You used {actual_en}."
                )
        else:
            expected_ko, expected_en = self.LEVEL_NAMES.get(
                expected, ("존댓말", "Polite")
            )
            
            if corrections:
                first_correction = corrections[0]
                return (
                    f"{expected_ko}가 더 적절해요. '{first_correction['original']}' 대신 '{first_correction['corrected']}'를 사용해보세요.",
                    f"{expected_en} would be more appropriate. Try '{first_correction['corrected']}' instead of '{first_correction['original']}'."
                )
            else:
                return (
                    f"{expected_ko}를 사용하는 것이 좋겠어요. 현재 {actual_ko}를 사용하고 있어요.",
                    f"You should use {expected_en}. Currently using {actual_en}."
                )
    
    def _build_score_breakdown(
        self,
        analyses: List[SentenceAnalysis]
    ) -> Dict[str, float]:
        """Build score breakdown."""
        if not analyses:
            return {}
        
        return {
            "formal_avg": sum(a.formal_score for a in analyses) / len(analyses),
            "polite_avg": sum(a.polite_score for a in analyses) / len(analyses),
            "informal_avg": sum(a.informal_score for a in analyses) / len(analyses),
            "confidence_avg": sum(a.confidence for a in analyses) / len(analyses),
        }
    
    def _build_feature_breakdown(
        self,
        analyses: List[SentenceAnalysis]
    ) -> Dict[str, bool]:
        """Build feature breakdown."""
        return {
            "has_honorific_verb": any(a.has_honorific_verb for a in analyses),
            "has_honorific_noun": any(a.has_honorific_noun for a in analyses),
            "has_subject_honorific": any(a.has_subject_honorific for a in analyses),
            "has_humble_form": any(a.has_humble_form for a in analyses),
            "is_consistent": len(set(a.formality_level for a in analyses)) <= 1,
        }


# Singleton instance
politeness_analyzer = SophisticatedPolitenessAnalyzer()
