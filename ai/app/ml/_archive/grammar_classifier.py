"""
Grammar Error Classifier - Machine Learning Component

This is ACTUAL MACHINE LEARNING using:
- TF-IDF Vectorization for text features
- Multi-label Classification for error types
- Scikit-learn models (Logistic Regression / Random Forest)

Error Types Detected:
1. speech_level - 말투 오류 (반말/존댓말 혼용)
2. particle - 조사 오류 (은/는, 이/가, 을/를)
3. verb_ending - 어미 오류 (-아요/-어요, -ㅂ니다)
4. tense - 시제 오류 (과거/현재/미래)
5. honorific - 존칭 오류 (님, 시-)
6. spacing - 띄어쓰기 오류
7. spelling - 맞춤법 오류
8. pronoun - 대명사 오류 (나/저, 너/당신)
9. word_order - 어순 오류
10. expression - 어색한 표현

Architecture:
┌─────────────────────────────────────────────────────────────┐
│  Korean Text → TF-IDF → ML Model → Error Labels            │
│                  ↓          ↓                                │
│            Features    Probabilities                         │
│           (n-grams)    (per error type)                      │
└─────────────────────────────────────────────────────────────┘
"""

import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# ML Libraries
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import MultiLabelBinarizer

from pydantic import BaseModel, Field


# ============================================================================
# Error Types
# ============================================================================

class GrammarErrorType(str, Enum):
    SPEECH_LEVEL = "speech_level"    # 말투 오류
    PARTICLE = "particle"            # 조사 오류
    VERB_ENDING = "verb_ending"      # 어미 오류
    TENSE = "tense"                  # 시제 오류
    HONORIFIC = "honorific"          # 존칭 오류
    SPACING = "spacing"              # 띄어쓰기
    SPELLING = "spelling"            # 맞춤법
    PRONOUN = "pronoun"              # 대명사 오류
    WORD_ORDER = "word_order"        # 어순 오류
    EXPRESSION = "expression"        # 어색한 표현
    NONE = "none"                    # 오류 없음


ERROR_DESCRIPTIONS = {
    GrammarErrorType.SPEECH_LEVEL: "말투 오류 (존댓말/반말 혼용)",
    GrammarErrorType.PARTICLE: "조사 오류 (은/는, 이/가, 을/를 등)",
    GrammarErrorType.VERB_ENDING: "어미 오류 (-아요/-어요 등)",
    GrammarErrorType.TENSE: "시제 오류 (과거/현재/미래)",
    GrammarErrorType.HONORIFIC: "존칭 오류 (높임말)",
    GrammarErrorType.SPACING: "띄어쓰기 오류",
    GrammarErrorType.SPELLING: "맞춤법 오류",
    GrammarErrorType.PRONOUN: "대명사 오류 (나/저 등)",
    GrammarErrorType.WORD_ORDER: "어순 오류",
    GrammarErrorType.EXPRESSION: "어색한 표현",
    GrammarErrorType.NONE: "오류 없음",
}


# ============================================================================
# Training Data
# ============================================================================

# Format: (sentence, [error_types], correction)
TRAINING_DATA = [
    # === SPEECH_LEVEL errors (반말 in formal context) ===
    ("선배 뭐해?", ["speech_level"], "선배 뭐 해요?"),
    ("교수님 나 질문 있어", ["speech_level", "pronoun"], "교수님 저 질문 있어요"),
    ("사장님 이거 뭐야?", ["speech_level"], "사장님 이거 뭐예요?"),
    ("선생님 나 배고파", ["speech_level", "pronoun"], "선생님 저 배고파요"),
    ("부장님 이거 했어", ["speech_level"], "부장님 이거 했어요"),
    ("언니 나 심심해", ["speech_level", "pronoun"], "언니 저 심심해요"),
    ("형 뭐 먹어?", ["speech_level"], "형 뭐 먹어요?"),
    ("선배님 같이 가", ["speech_level"], "선배님 같이 가요"),
    
    # === PARTICLE errors (조사) ===
    ("나는 사과가 먹고 싶어요", ["particle"], "나는 사과를 먹고 싶어요"),
    ("저는 영화를 좋아요", ["particle"], "저는 영화가 좋아요"),
    ("친구을 만났어요", ["particle"], "친구를 만났어요"),
    ("학교는 갔어요", ["particle"], "학교에 갔어요"),
    ("서울는 멀어요", ["particle"], "서울은 멀어요"),
    ("책이 읽었어요", ["particle"], "책을 읽었어요"),
    ("밥는 먹었어요", ["particle"], "밥은 먹었어요"),
    ("영화는 봤어요", ["particle"], "영화를 봤어요"),
    ("친구이 왔어요", ["particle"], "친구가 왔어요"),
    
    # === VERB_ENDING errors (어미) ===
    ("저는 먹어", ["verb_ending", "speech_level"], "저는 먹어요"),
    ("맛있다", ["verb_ending"], "맛있어요"),
    ("좋다", ["verb_ending"], "좋아요"),
    ("가다", ["verb_ending"], "가요"),
    ("알아", ["verb_ending"], "알아요"),
    ("오늘 바쁘다", ["verb_ending"], "오늘 바빠요"),
    ("배고프다", ["verb_ending"], "배고파요"),
    ("재미있다", ["verb_ending"], "재미있어요"),
    
    # === TENSE errors (시제) ===
    ("어제 학교에 가요", ["tense"], "어제 학교에 갔어요"),
    ("내일 영화를 봤어요", ["tense"], "내일 영화를 볼 거예요"),
    ("지난주에 친구를 만나요", ["tense"], "지난주에 친구를 만났어요"),
    ("작년에 한국에 와요", ["tense"], "작년에 한국에 왔어요"),
    ("내년에 졸업했어요", ["tense"], "내년에 졸업할 거예요"),
    
    # === HONORIFIC errors (존칭) ===
    ("할머니가 밥 먹었어요", ["honorific"], "할머니께서 진지 드셨어요"),
    ("선생님이 말했어요", ["honorific"], "선생님께서 말씀하셨어요"),
    ("사장님 있어요?", ["honorific"], "사장님 계세요?"),
    ("교수님 밥 먹었어요?", ["honorific"], "교수님 식사하셨어요?"),
    ("아버지가 왔어요", ["honorific"], "아버지께서 오셨어요"),
    
    # === SPACING errors (띄어쓰기) ===
    ("나는학교에갔어요", ["spacing"], "나는 학교에 갔어요"),
    ("오늘날씨가좋아요", ["spacing"], "오늘 날씨가 좋아요"),
    ("저는 한국어를공부해요", ["spacing"], "저는 한국어를 공부해요"),
    ("뭐먹을까요", ["spacing"], "뭐 먹을까요"),
    ("같이가요", ["spacing"], "같이 가요"),
    
    # === SPELLING errors (맞춤법) ===
    ("됬어요", ["spelling"], "됐어요"),
    ("안되요", ["spelling"], "안 돼요"),
    ("왠지", ["spelling"], "웬지"),
    ("몇일", ["spelling"], "며칠"),
    ("어의없어요", ["spelling"], "어이없어요"),
    ("오랫만이에요", ["spelling"], "오랜만이에요"),
    ("금새", ["spelling"], "금세"),
    ("어떻게 해", ["spelling"], "어떡해"),
    
    # === PRONOUN errors (대명사) ===
    ("교수님, 나 질문 있어요", ["pronoun"], "교수님, 저 질문 있어요"),
    ("사장님, 나 왔어요", ["pronoun"], "사장님, 저 왔어요"),
    ("선배님, 나 도와주세요", ["pronoun"], "선배님, 저 도와주세요"),
    ("선생님, 나 모르겠어요", ["pronoun"], "선생님, 저 모르겠어요"),
    
    # === WORD_ORDER errors (어순) ===
    ("먹었어요 밥을", ["word_order"], "밥을 먹었어요"),
    ("갔어요 학교에", ["word_order"], "학교에 갔어요"),
    ("좋아요 한국을", ["word_order"], "한국을 좋아요"),
    
    # === EXPRESSION errors (어색한 표현) ===
    ("나는 재미를 있어요", ["expression"], "나는 재미있어요"),
    ("저는 행복을 해요", ["expression"], "저는 행복해요"),
    ("날씨가 좋음이에요", ["expression"], "날씨가 좋아요"),
    ("공부하는 것을 해요", ["expression"], "공부해요"),
    
    # === CORRECT sentences (no errors) ===
    ("안녕하세요", ["none"], "안녕하세요"),
    ("저는 학생이에요", ["none"], "저는 학생이에요"),
    ("오늘 날씨가 좋아요", ["none"], "오늘 날씨가 좋아요"),
    ("한국어를 공부해요", ["none"], "한국어를 공부해요"),
    ("맛있게 드세요", ["none"], "맛있게 드세요"),
    ("감사합니다", ["none"], "감사합니다"),
    ("네, 알겠습니다", ["none"], "네, 알겠습니다"),
    ("좋은 하루 되세요", ["none"], "좋은 하루 되세요"),
    ("다음에 또 만나요", ["none"], "다음에 또 만나요"),
    ("잘 지내세요?", ["none"], "잘 지내세요?"),
    ("요즘 어떻게 지내세요?", ["none"], "요즘 어떻게 지내세요?"),
    ("저도 그렇게 생각해요", ["none"], "저도 그렇게 생각해요"),
    
    # === Multiple errors ===
    ("교수님 나 어제 숙제했어", ["speech_level", "pronoun"], "교수님 저 어제 숙제했어요"),
    ("선배 나는학교에갔어", ["speech_level", "spacing"], "선배 저는 학교에 갔어요"),
    ("할머니 나 밥먹었어", ["speech_level", "pronoun", "honorific"], "할머니 저 밥 먹었어요"),
]


# ============================================================================
# Models
# ============================================================================

class ErrorPrediction(BaseModel):
    """Single error prediction"""
    error_type: str
    confidence: float
    description: str


class ClassificationResult(BaseModel):
    """Result of grammar error classification"""
    text: str
    has_error: bool
    error_predictions: List[ErrorPrediction]
    suggested_correction: Optional[str] = None
    model_confidence: float
    
    # ML metadata
    model_version: str = "1.0"
    vectorizer_features: int = 0


class ModelMetrics(BaseModel):
    """Model performance metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_samples: int
    test_samples: int
    error_types: List[str]


# ============================================================================
# Grammar Error Classifier (ML)
# ============================================================================

class GrammarErrorClassifier:
    """
    Machine Learning based Grammar Error Classifier
    
    Uses:
    - TF-IDF for text vectorization (character n-grams)
    - Multi-label classification (one sentence can have multiple errors)
    - Logistic Regression with OneVsRest strategy
    
    This is REAL ML that can be:
    - Trained on data
    - Evaluated with metrics
    - Saved/loaded
    - Explained to professor
    """
    
    def __init__(self, model_dir: str = "./models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        # ML Components
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.classifier: Optional[OneVsRestClassifier] = None
        self.label_binarizer: Optional[MultiLabelBinarizer] = None
        
        # Training data
        self.training_data = TRAINING_DATA
        
        # Model state
        self.is_trained = False
        self.metrics: Optional[ModelMetrics] = None
        
        # Correction mapping (for suggestions)
        self.corrections: Dict[str, str] = {
            text: correction for text, _, correction in TRAINING_DATA
        }
    
    def train(self, test_size: float = 0.2) -> ModelMetrics:
        """
        Train the classifier on the training data.
        
        Returns metrics showing model performance.
        """
        
        # Prepare data
        texts = [item[0] for item in self.training_data]
        labels = [item[1] for item in self.training_data]
        
        # Binarize labels (multi-label)
        self.label_binarizer = MultiLabelBinarizer()
        y = self.label_binarizer.fit_transform(labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            texts, y, test_size=test_size, random_state=42
        )
        
        # Create TF-IDF vectorizer
        # Using character n-grams to capture Korean morphology
        self.vectorizer = TfidfVectorizer(
            analyzer='char',
            ngram_range=(1, 3),  # 1 to 3 character n-grams
            max_features=5000,
            min_df=1,
        )
        
        # Fit vectorizer and transform training data
        X_train_tfidf = self.vectorizer.fit_transform(X_train)
        X_test_tfidf = self.vectorizer.transform(X_test)
        
        # Create and train classifier
        base_classifier = LogisticRegression(
            max_iter=1000,
            class_weight='balanced',
            random_state=42,
        )
        self.classifier = OneVsRestClassifier(base_classifier)
        self.classifier.fit(X_train_tfidf, y_train)
        
        # Evaluate
        y_pred = self.classifier.predict(X_test_tfidf)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        
        # Get per-class metrics
        report = classification_report(
            y_test, y_pred,
            target_names=self.label_binarizer.classes_,
            output_dict=True,
            zero_division=0,
        )
        
        # Average metrics
        precision = report.get('weighted avg', {}).get('precision', 0)
        recall = report.get('weighted avg', {}).get('recall', 0)
        f1 = report.get('weighted avg', {}).get('f1-score', 0)
        
        self.metrics = ModelMetrics(
            accuracy=round(accuracy, 4),
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            training_samples=len(X_train),
            test_samples=len(X_test),
            error_types=list(self.label_binarizer.classes_),
        )
        
        self.is_trained = True
        
        print(f"✅ Model trained!")
        print(f"   Accuracy: {self.metrics.accuracy:.2%}")
        print(f"   F1 Score: {self.metrics.f1_score:.2%}")
        print(f"   Training samples: {self.metrics.training_samples}")
        print(f"   Error types: {self.metrics.error_types}")
        
        return self.metrics
    
    def predict(self, text: str) -> ClassificationResult:
        """
        Predict grammar errors in text.
        
        Returns classification result with error types and confidence.
        """
        
        if not self.is_trained:
            # Auto-train if not trained
            self.train()
        
        # Vectorize input
        X = self.vectorizer.transform([text])
        
        # Get probabilities
        probas = self.classifier.predict_proba(X)[0]
        
        # Get predictions
        predictions = self.classifier.predict(X)[0]
        
        # Build error predictions
        error_predictions = []
        for idx, (label, proba, pred) in enumerate(
            zip(self.label_binarizer.classes_, probas, predictions)
        ):
            if proba > 0.3 or pred == 1:  # Threshold or predicted
                error_type = GrammarErrorType(label) if label in [e.value for e in GrammarErrorType] else None
                if error_type and error_type != GrammarErrorType.NONE:
                    error_predictions.append(ErrorPrediction(
                        error_type=label,
                        confidence=round(float(proba), 4),
                        description=ERROR_DESCRIPTIONS.get(error_type, label),
                    ))
        
        # Sort by confidence
        error_predictions.sort(key=lambda x: x.confidence, reverse=True)
        
        # Check if "none" has highest probability
        none_idx = list(self.label_binarizer.classes_).index("none") if "none" in self.label_binarizer.classes_ else -1
        none_proba = probas[none_idx] if none_idx >= 0 else 0
        
        has_error = len(error_predictions) > 0 and (none_proba < 0.5 or error_predictions[0].confidence > 0.5)
        
        # Get suggested correction if available
        suggested_correction = self.corrections.get(text)
        
        # Model confidence (average of top predictions)
        if error_predictions:
            model_confidence = sum(e.confidence for e in error_predictions[:3]) / min(3, len(error_predictions))
        else:
            model_confidence = none_proba
        
        return ClassificationResult(
            text=text,
            has_error=has_error,
            error_predictions=error_predictions,
            suggested_correction=suggested_correction if has_error else None,
            model_confidence=round(model_confidence, 4),
            vectorizer_features=len(self.vectorizer.get_feature_names_out()) if self.vectorizer else 0,
        )
    
    def predict_batch(self, texts: List[str]) -> List[ClassificationResult]:
        """Predict errors for multiple texts"""
        return [self.predict(text) for text in texts]
    
    def add_training_data(self, text: str, errors: List[str], correction: str):
        """Add new training example"""
        self.training_data.append((text, errors, correction))
        self.corrections[text] = correction
        # Mark as needing retraining
        self.is_trained = False
    
    def save_model(self, name: str = "grammar_classifier"):
        """Save trained model to disk"""
        if not self.is_trained:
            raise ValueError("Model not trained yet!")
        
        model_path = self.model_dir / f"{name}.pkl"
        
        data = {
            "vectorizer": self.vectorizer,
            "classifier": self.classifier,
            "label_binarizer": self.label_binarizer,
            "corrections": self.corrections,
            "metrics": self.metrics.dict() if self.metrics else None,
        }
        
        with open(model_path, "wb") as f:
            pickle.dump(data, f)
        
        print(f"✅ Model saved to {model_path}")
    
    def load_model(self, name: str = "grammar_classifier") -> bool:
        """Load trained model from disk"""
        model_path = self.model_dir / f"{name}.pkl"
        
        if not model_path.exists():
            return False
        
        try:
            with open(model_path, "rb") as f:
                data = pickle.load(f)
            
            self.vectorizer = data["vectorizer"]
            self.classifier = data["classifier"]
            self.label_binarizer = data["label_binarizer"]
            self.corrections = data.get("corrections", {})
            
            if data.get("metrics"):
                self.metrics = ModelMetrics(**data["metrics"])
            
            self.is_trained = True
            print(f"✅ Model loaded from {model_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            return False
    
    def get_feature_importance(self, error_type: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """Get most important features for an error type"""
        if not self.is_trained:
            return []
        
        try:
            idx = list(self.label_binarizer.classes_).index(error_type)
            coefficients = self.classifier.estimators_[idx].coef_[0]
            feature_names = self.vectorizer.get_feature_names_out()
            
            # Get top features
            top_indices = np.argsort(np.abs(coefficients))[-top_n:][::-1]
            
            return [
                (feature_names[i], round(coefficients[i], 4))
                for i in top_indices
            ]
        except (IndexError, AttributeError):
            return []


# ============================================================================
# Global Instance
# ============================================================================

grammar_classifier = GrammarErrorClassifier()


# ============================================================================
# Simple API Functions
# ============================================================================

def classify_grammar_errors(text: str) -> Dict[str, Any]:
    """
    Simple function to classify grammar errors in text.
    
    Returns dict with error types and confidence scores.
    """
    result = grammar_classifier.predict(text)
    return result.dict()


def train_classifier() -> Dict[str, Any]:
    """Train the classifier and return metrics"""
    metrics = grammar_classifier.train()
    return metrics.dict()


def get_model_info() -> Dict[str, Any]:
    """Get information about the current model"""
    return {
        "is_trained": grammar_classifier.is_trained,
        "metrics": grammar_classifier.metrics.dict() if grammar_classifier.metrics else None,
        "training_samples": len(grammar_classifier.training_data),
        "error_types": [e.value for e in GrammarErrorType if e != GrammarErrorType.NONE],
    }
