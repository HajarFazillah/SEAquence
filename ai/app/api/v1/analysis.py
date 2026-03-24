"""
Analysis API
POST /api/v1/analysis/politeness - Basic politeness analysis
POST /api/v1/analysis/enhanced  - Word-level enhanced analysis
GET  /api/v1/analysis/quick     - Quick check
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List

from app.services.politeness_service import politeness_service
from app.schemas.enhanced_schemas import (
    EnhancedPolitenessRequest,
    EnhancedPolitenessResponse,
    WordAnalysisResult,
    CorrectionResult,
    ErrorDetail,
    LevelBreakdown,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])


class PolitenessRequest(BaseModel):
    text: str
    target_role: Optional[str] = None
    target_age: Optional[int] = None
    user_age: int = 22


@router.post("/politeness")
async def analyze_politeness(request: PolitenessRequest):
    """Basic politeness analysis."""
    result = politeness_service.analyze(
        text=request.text,
        target_role=request.target_role,
        target_age=request.target_age,
        user_age=request.user_age,
    )
    return result


@router.post("/enhanced", response_model=EnhancedPolitenessResponse)
async def analyze_enhanced(request: EnhancedPolitenessRequest):
    """
    Enhanced word-level politeness analysis.
    Returns per-word highlights, corrections, and error breakdown.
    """
    result = politeness_service.analyze(
        text=request.text,
        target_role=request.target_role,
        target_age=request.target_age,
        user_age=request.user_age,
    )

    level = result.get("level", "polite")
    score = result.get("score", 50)
    is_appropriate = result.get("is_appropriate", True)
    details = result.get("details", {})

    level_names = {
        "informal":   ("반말", "Informal"),
        "polite":     ("존댓말", "Polite"),
        "very_polite":("격식체", "Formal"),
    }
    name_ko, name_en = level_names.get(level, ("존댓말", "Polite"))

    return EnhancedPolitenessResponse(
        level=level,
        level_ko=name_ko,
        level_en=name_en,
        score=score,
        is_appropriate=is_appropriate,
        level_breakdown=LevelBreakdown(
            informal=0.3 if level == "informal" else 0.0,
            polite=0.7 if level == "polite" else 0.0,
            very_polite=0.9 if level == "very_polite" else 0.0,
            honorific=min(details.get("honorific_score", 0) / 20, 1.0),
        ),
        word_analysis=[],
        corrections=[
            CorrectionResult(
                original=c.get("original", ""),
                corrected=c.get("corrected", ""),
                reason_ko=c.get("explanation", ""),
                reason_en=c.get("explanation", ""),
                position_start=0,
                position_end=len(c.get("original", "")),
            )
            for c in details.get("corrections", [])
        ],
        errors=[],
        recommended_level=result.get("recommended_level"),
        feedback_ko=result.get("feedback_ko"),
        feedback_en=result.get("feedback_en"),
        details=details,
    )


@router.get("/quick")
async def quick_check(
    text: str = Query(...),
    target_role: Optional[str] = Query(None),
):
    """Quick one-line politeness check."""
    result = politeness_service.analyze(text=text, target_role=target_role)
    return {
        "level": result.get("level"),
        "score": result.get("score"),
        "is_appropriate": result.get("is_appropriate"),
        "feedback_ko": result.get("feedback_ko"),
    }
