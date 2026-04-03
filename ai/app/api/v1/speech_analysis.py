"""
Sophisticated Speech Level Analysis API
Advanced Korean honorific system analysis
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.services.sophisticated_speech_analyzer import (
    analyze_speech_level,
    check_appropriateness,
    get_analyzer,
    SpeechLevel,
)

router = APIRouter(prefix="/speech-analysis", tags=["Speech Level Analysis"])


# ===========================================
# Request/Response Models
# ===========================================

class AnalysisRequest(BaseModel):
    """Request for speech level analysis"""
    text: str = Field(..., description="Korean text to analyze", min_length=1)
    context: Optional[Dict[str, Any]] = Field(
        None, 
        description="Optional context (speaker, addressee, situation)"
    )


class AppropriatenessRequest(BaseModel):
    """Request for appropriateness check"""
    text: str = Field(..., description="Korean text to check")
    expected_level: str = Field(
        ..., 
        description="Expected level: FORMAL, POLITE, or INFORMAL"
    )
    situation_id: Optional[str] = Field(
        None,
        description="Optional situation ID for context"
    )


class BatchAnalysisRequest(BaseModel):
    """Request for batch analysis"""
    texts: List[str] = Field(..., description="List of texts to analyze")
    compare: bool = Field(False, description="Compare formality levels")


# ===========================================
# Endpoints
# ===========================================

@router.post("/analyze")
async def analyze_text(request: AnalysisRequest):
    """
    Comprehensive Korean speech level analysis.
    
    Analyzes:
    - **7 Speech Levels** (하소서체 → 해체)
    - **Subject Honorification** (주체 높임법): -시-, 계시다, 께서
    - **Object Honorification** (객체 높임법): 드리다, 여쭙다, 께
    - **Pragmatic Markers**: hedging, softening, face-saving
    - **Consistency**: checks for mixed speech levels
    
    **Example:**
    ```json
    {"text": "교수님께서 말씀하셨습니다. 감사드립니다."}
    ```
    
    **Returns:**
    - Primary speech level with confidence
    - Formality score (0-100)
    - Politeness score (0-100)
    - Detailed honorific analysis
    - Pragmatic markers found
    - Consistency check
    - Feature vector for ML
    """
    try:
        result = analyze_speech_level(request.text)
        return {
            "status": "success",
            "analysis": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-appropriateness")
async def check_text_appropriateness(request: AppropriatenessRequest):
    """
    Check if speech level is appropriate for expected context.
    
    **Expected Levels:**
    - `FORMAL`: 격식체 (합쇼체/하소서체) - 습니다, 십시오
    - `POLITE`: 해요체 - 어요, 세요
    - `INFORMAL`: 반말 (해체/해라체) - 어, 야
    
    **Example:**
    ```json
    {
        "text": "커피 한 잔 주세요",
        "expected_level": "POLITE"
    }
    ```
    
    **Returns:**
    - Whether text is appropriate
    - Detected vs expected level
    - Feedback in Korean and English
    """
    try:
        result = check_appropriateness(
            request.text,
            request.expected_level,
            request.situation_id
        )
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-analyze")
async def batch_analyze(request: BatchAnalysisRequest):
    """
    Analyze multiple texts at once.
    
    Useful for:
    - Comparing user messages over time
    - Analyzing conversation consistency
    - Evaluating improvement
    
    **Example:**
    ```json
    {
        "texts": [
            "안녕하세요",
            "뭐해?",
            "감사합니다"
        ],
        "compare": true
    }
    ```
    """
    try:
        results = []
        for text in request.texts:
            analysis = analyze_speech_level(text)
            results.append({
                "text": text,
                "level": analysis["primary_level"],
                "level_korean": analysis["primary_level_korean"],
                "formality_score": analysis["scores"]["formality"],
                "politeness_score": analysis["scores"]["politeness"],
            })
        
        comparison = None
        if request.compare and len(results) > 1:
            formality_scores = [r["formality_score"] for r in results]
            levels = [r["level"] for r in results]
            unique_levels = set(levels)
            
            comparison = {
                "is_consistent": len(unique_levels) == 1,
                "unique_levels": list(unique_levels),
                "formality_range": {
                    "min": min(formality_scores),
                    "max": max(formality_scores),
                    "average": sum(formality_scores) / len(formality_scores)
                },
                "most_common_level": max(set(levels), key=levels.count)
            }
        
        return {
            "status": "success",
            "results": results,
            "comparison": comparison
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/speech-levels")
async def get_speech_levels():
    """
    Get information about Korean speech levels.
    
    Returns all 7 traditional Korean speech levels with:
    - Korean and English names
    - Example endings
    - Usage context
    - Formality ranking
    """
    return {
        "speech_levels": [
            {
                "level": "HASOSEO",
                "korean_name": "하소서체",
                "english_name": "Hasoseo-che",
                "formality_rank": 7,
                "example_endings": ["-나이다", "-소서", "-사옵니다"],
                "usage": "Archaic, used in prayers, historical dramas",
                "is_modern": False
            },
            {
                "level": "HAPSYO",
                "korean_name": "합쇼체",
                "english_name": "Hapsyo-che (Formal polite)",
                "formality_rank": 6,
                "example_endings": ["-습니다", "-습니까", "-십시오"],
                "usage": "Business, formal situations, news, public speaking",
                "is_modern": True
            },
            {
                "level": "HAO",
                "korean_name": "하오체",
                "english_name": "Hao-che",
                "formality_rank": 5,
                "example_endings": ["-오", "-구려", "-시오"],
                "usage": "Older generation, historical dramas",
                "is_modern": False
            },
            {
                "level": "HAGE",
                "korean_name": "하게체",
                "english_name": "Hage-che",
                "formality_rank": 4,
                "example_endings": ["-게", "-네", "-나"],
                "usage": "Older speaker to younger, semi-formal",
                "is_modern": False
            },
            {
                "level": "HAERA",
                "korean_name": "해라체",
                "english_name": "Haera-che (Plain form)",
                "formality_rank": 3,
                "example_endings": ["-다", "-느냐", "-아라"],
                "usage": "Written form, newspapers, books, diaries",
                "is_modern": True
            },
            {
                "level": "HAEYO",
                "korean_name": "해요체",
                "english_name": "Haeyo-che (Informal polite)",
                "formality_rank": 2,
                "example_endings": ["-어요", "-세요", "-죠"],
                "usage": "Most common polite form, daily conversations",
                "is_modern": True
            },
            {
                "level": "HAE",
                "korean_name": "해체 (반말)",
                "english_name": "Hae-che (Casual/Banmal)",
                "formality_rank": 1,
                "example_endings": ["-어", "-야", "-지"],
                "usage": "Close friends, family, children, same-age peers",
                "is_modern": True
            },
        ],
        "honorific_types": [
            {
                "type": "subject",
                "korean_name": "주체 높임법",
                "description": "Honoring the subject of the sentence",
                "markers": ["-시-", "께서", "계시다", "주무시다"]
            },
            {
                "type": "object",
                "korean_name": "객체 높임법",
                "description": "Humbling oneself or honoring the object",
                "markers": ["드리다", "여쭙다", "뵙다", "께"]
            },
            {
                "type": "addressee",
                "korean_name": "상대 높임법",
                "description": "Sentence endings based on listener relationship",
                "markers": ["Sentence endings determine this"]
            },
        ],
        "pragmatic_functions": [
            {"function": "hedging", "korean": "완곡 표현", "example": "아마, 것 같아요"},
            {"function": "softening", "korean": "완화 표현", "example": "혹시, 좀"},
            {"function": "face_saving", "korean": "체면 유지", "example": "죄송하지만, 실례지만"},
            {"function": "solidarity", "korean": "친밀감", "example": "우리, 같이"},
            {"function": "distance", "korean": "거리감", "example": "저, 저희, 귀사"},
        ]
    }


@router.get("/honorific-vocabulary")
async def get_honorific_vocabulary():
    """
    Get list of honorific vocabulary.
    
    Returns:
    - Humble verbs (겸양어)
    - Honorific verbs (존경어)
    - Honorific nouns
    - Honorific particles
    """
    analyzer = get_analyzer()
    db = analyzer.db
    
    return {
        "subject_honorification": {
            "verb_replacements": {
                plain: {"honorific": hon, "meaning": meaning}
                for plain, (hon, meaning) in db.SUBJECT_HONORIFIC["verb_replacements"].items()
            },
            "particles": {
                p: {"description": desc, "points": pts}
                for p, (desc, pts) in db.SUBJECT_HONORIFIC["particles"].items()
            },
        },
        "object_honorification": {
            "humble_verbs": {
                verb: {"description": desc, "replaces": plain}
                for verb, (desc, plain) in db.OBJECT_HONORIFIC["humble_verbs"].items()
            },
            "particles": {
                p: {"description": desc, "points": pts}
                for p, (desc, pts) in db.OBJECT_HONORIFIC["particles"].items()
            },
            "honorific_nouns": {
                noun: {"meaning": meaning, "plain_form": plain}
                for noun, (meaning, plain) in db.OBJECT_HONORIFIC["nouns"].items()
            },
        },
        "examples": {
            "높임말 동사": {
                "있다 → 계시다": "선생님이 교실에 계세요",
                "먹다 → 드시다": "아버지가 식사를 드세요",
                "자다 → 주무시다": "할머니께서 주무세요",
            },
            "겸양어 동사": {
                "주다 → 드리다": "선물을 드려요",
                "묻다 → 여쭙다": "한 가지 여쭤봐도 될까요?",
                "보다 → 뵙다": "다음에 뵙겠습니다",
            },
            "높임말 명사": {
                "나이 → 연세": "연세가 어떻게 되세요?",
                "이름 → 성함": "성함이 어떻게 되세요?",
                "밥 → 진지": "진지 드셨어요?",
            },
        }
    }


@router.post("/detailed-breakdown")
async def detailed_breakdown(request: AnalysisRequest):
    """
    Get detailed sentence-by-sentence breakdown.
    
    Useful for:
    - Understanding exactly what was detected
    - Debugging speech level issues
    - Learning Korean honorific patterns
    """
    try:
        analyzer = get_analyzer()
        result = analyzer.analyze(request.text)
        
        sentence_details = []
        for i, sent_analysis in enumerate(result.sentence_analyses):
            sentence_details.append({
                "index": i + 1,
                "text": sent_analysis.text,
                "detected_level": sent_analysis.speech_level.name,
                "confidence": sent_analysis.confidence,
                "endings_found": sent_analysis.endings,
                "honorific_markers": sent_analysis.honorific_markers,
                "pragmatic_markers": sent_analysis.pragmatic_markers,
            })
        
        return {
            "status": "success",
            "overall": {
                "primary_level": result.primary_level.name,
                "primary_level_korean": result.primary_level_name,
                "is_consistent": result.is_consistent,
                "consistency_issues": result.consistency_issues,
            },
            "scores": {
                "formality": result.formality_score,
                "politeness": result.politeness_score,
                "honorific_density": result.honorific_density,
            },
            "sentences": sentence_details,
            "summary_ko": result.summary_ko,
            "summary_en": result.summary_en,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
