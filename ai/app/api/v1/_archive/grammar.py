"""
Grammar Classifier API - Machine Learning Endpoints

This provides ML-based grammar error classification.

POST /api/v1/grammar/classify - Classify errors in text
POST /api/v1/grammar/classify-batch - Classify multiple texts
POST /api/v1/grammar/train - Train/retrain the model
GET  /api/v1/grammar/model-info - Get model information
GET  /api/v1/grammar/error-types - List all error types
POST /api/v1/grammar/add-training - Add training data
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from app.ml.grammar_classifier import (
    grammar_classifier,
    ClassificationResult,
    ModelMetrics,
    GrammarErrorType,
    ERROR_DESCRIPTIONS,
)


router = APIRouter(prefix="/grammar", tags=["grammar-ml"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ClassifyRequest(BaseModel):
    text: str = Field(..., description="Korean text to analyze")
    
    class Config:
        json_schema_extra = {
            "example": {"text": "선배 뭐해? 나 심심해"}
        }


class BatchClassifyRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to analyze")
    
    class Config:
        json_schema_extra = {
            "example": {"texts": ["선배 뭐해?", "안녕하세요", "나는 학교가 갔어요"]}
        }


class AddTrainingRequest(BaseModel):
    text: str = Field(..., description="Incorrect text")
    errors: List[str] = Field(..., description="Error types")
    correction: str = Field(..., description="Corrected text")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "교수님 나 숙제 했어",
                "errors": ["speech_level", "pronoun"],
                "correction": "교수님 저 숙제 했어요"
            }
        }


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/classify", response_model=ClassificationResult)
async def classify_grammar(request: ClassifyRequest):
    """
    Classify grammar errors in Korean text using ML.
    
    ## How it works
    
    1. Text is vectorized using TF-IDF (character n-grams)
    2. Multi-label classifier predicts error types
    3. Returns confidence scores for each error type
    
    ## Error Types Detected
    
    - **speech_level**: 말투 오류 (반말/존댓말)
    - **particle**: 조사 오류 (은/는, 이/가)
    - **verb_ending**: 어미 오류
    - **tense**: 시제 오류
    - **honorific**: 존칭 오류
    - **spacing**: 띄어쓰기
    - **spelling**: 맞춤법
    - **pronoun**: 대명사 오류 (나/저)
    - **word_order**: 어순 오류
    - **expression**: 어색한 표현
    
    ## Example
    
    Input: `"선배 뭐해? 나 심심해"`
    
    Output:
    ```json
    {
      "text": "선배 뭐해? 나 심심해",
      "has_error": true,
      "error_predictions": [
        {"error_type": "speech_level", "confidence": 0.94},
        {"error_type": "pronoun", "confidence": 0.87}
      ],
      "suggested_correction": "선배 뭐 해요? 저 심심해요"
    }
    ```
    """
    
    try:
        result = grammar_classifier.predict(request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify-batch")
async def classify_batch(request: BatchClassifyRequest):
    """
    Classify grammar errors in multiple texts.
    
    Useful for analyzing conversation history or batch processing.
    """
    
    try:
        results = grammar_classifier.predict_batch(request.texts)
        return {
            "count": len(results),
            "results": [r.dict() for r in results],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train", response_model=ModelMetrics)
async def train_model(test_size: float = 0.2):
    """
    Train or retrain the grammar classifier.
    
    ## ML Details
    
    - **Algorithm**: Logistic Regression with OneVsRest
    - **Vectorization**: TF-IDF with character n-grams (1-3)
    - **Multi-label**: Can detect multiple errors per sentence
    
    Returns training metrics:
    - Accuracy
    - Precision
    - Recall  
    - F1 Score
    """
    
    try:
        metrics = grammar_classifier.train(test_size=test_size)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-info")
async def get_model_info():
    """
    Get information about the current ML model.
    
    Returns:
    - Whether model is trained
    - Performance metrics
    - Training data size
    - Supported error types
    """
    
    return {
        "is_trained": grammar_classifier.is_trained,
        "metrics": grammar_classifier.metrics.dict() if grammar_classifier.metrics else None,
        "training_samples": len(grammar_classifier.training_data),
        "model_type": "LogisticRegression + TF-IDF",
        "vectorizer": "TF-IDF (char n-grams 1-3)",
        "classification": "Multi-label (OneVsRest)",
        "error_types": [e.value for e in GrammarErrorType if e != GrammarErrorType.NONE],
    }


@router.get("/error-types")
async def get_error_types():
    """
    Get all supported grammar error types.
    """
    
    return {
        "error_types": [
            {
                "type": e.value,
                "description_ko": ERROR_DESCRIPTIONS[e],
            }
            for e in GrammarErrorType if e != GrammarErrorType.NONE
        ]
    }


@router.post("/add-training")
async def add_training_data(request: AddTrainingRequest):
    """
    Add new training data to the classifier.
    
    After adding data, you need to retrain the model
    with POST /train for changes to take effect.
    
    ## Example
    
    ```json
    {
      "text": "교수님 나 숙제 했어",
      "errors": ["speech_level", "pronoun"],
      "correction": "교수님 저 숙제 했어요"
    }
    ```
    """
    
    # Validate error types
    valid_types = [e.value for e in GrammarErrorType]
    for error in request.errors:
        if error not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid error type: {error}. Valid types: {valid_types}"
            )
    
    grammar_classifier.add_training_data(
        text=request.text,
        errors=request.errors,
        correction=request.correction,
    )
    
    return {
        "status": "success",
        "message": "Training data added. Call POST /train to retrain model.",
        "total_samples": len(grammar_classifier.training_data),
    }


@router.post("/save")
async def save_model(name: str = "grammar_classifier"):
    """Save the trained model to disk."""
    
    if not grammar_classifier.is_trained:
        raise HTTPException(status_code=400, detail="Model not trained yet!")
    
    try:
        grammar_classifier.save_model(name)
        return {"status": "success", "message": f"Model saved as {name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load")
async def load_model(name: str = "grammar_classifier"):
    """Load a saved model from disk."""
    
    success = grammar_classifier.load_model(name)
    
    if success:
        return {"status": "success", "message": f"Model {name} loaded"}
    else:
        raise HTTPException(status_code=404, detail=f"Model {name} not found")


@router.get("/feature-importance/{error_type}")
async def get_feature_importance(error_type: str, top_n: int = 10):
    """
    Get most important features for an error type.
    
    Shows which character patterns the model uses to detect each error.
    """
    
    if not grammar_classifier.is_trained:
        raise HTTPException(status_code=400, detail="Model not trained yet!")
    
    features = grammar_classifier.get_feature_importance(error_type, top_n)
    
    if not features:
        raise HTTPException(status_code=404, detail=f"Error type {error_type} not found")
    
    return {
        "error_type": error_type,
        "top_features": [
            {"feature": f, "weight": w} for f, w in features
        ]
    }
