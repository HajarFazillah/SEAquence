"""
Enhanced Analysis API Endpoints
With word-level analysis, corrections, error categories
"""

from fastapi import APIRouter

from app.schemas.enhanced_schemas import (
    EnhancedPolitenessRequest,
    EnhancedPolitenessResponse,
    LevelBreakdown,
    WordAnalysisResult,
    CorrectionResult,
    ErrorDetail,
)
from app.services.enhanced_politeness_service import enhanced_politeness_service

router = APIRouter()


@router.post("/politeness/enhanced", response_model=EnhancedPolitenessResponse)
async def analyze_politeness_enhanced(request: EnhancedPolitenessRequest):
    """
    Enhanced politeness analysis with:
    - Word-level analysis (which words are wrong)
    - Specific correction suggestions
    - Error categorization
    - Level breakdown (% informal/polite/formal)
    
    Example:
    ```
    Input: "교수님 질문이 있어요"
    
    Output:
    - level: "polite" (but expected "very_polite")
    - word_analysis: [
        {word: "교수님", is_correct: true},
        {word: "있어요", is_correct: false, suggestion: "있습니다"}
      ]
    - corrections: [{original: "있어요", corrected: "있습니다", reason: "..."}]
    - errors: [{type: "ending_mismatch", count: 1}]
    ```
    """
    result = enhanced_politeness_service.analyze(
        text=request.text,
        target_role=request.target_role,
        target_age=request.target_age,
        user_age=request.user_age
    )
    
    # Convert to response model
    return EnhancedPolitenessResponse(
        level=result.level,
        level_ko=result.level_ko,
        level_en=result.level_en,
        score=result.score,
        is_appropriate=result.is_appropriate,
        level_breakdown=LevelBreakdown(**result.level_breakdown),
        word_analysis=[WordAnalysisResult(**w) for w in result.word_analysis],
        corrections=[CorrectionResult(**c) for c in result.corrections],
        errors=[ErrorDetail(**e) for e in result.errors],
        recommended_level=result.recommended_level,
        feedback_ko=result.feedback_ko,
        feedback_en=result.feedback_en,
        details=result.details
    )


@router.post("/politeness/quick")
async def analyze_politeness_quick(
    text: str,
    target_role: str = "senior"
):
    """
    Quick politeness check with minimal output.
    For real-time feedback during typing.
    
    Returns only:
    - level
    - is_appropriate
    - top 1 correction (if any)
    """
    result = enhanced_politeness_service.analyze(
        text=text,
        target_role=target_role
    )
    
    top_correction = None
    if result.corrections:
        c = result.corrections[0]
        top_correction = {
            "original": c["original"],
            "corrected": c["corrected"],
            "reason": c["reason_ko"]
        }
    
    return {
        "level": result.level,
        "level_ko": result.level_ko,
        "is_appropriate": result.is_appropriate,
        "score": result.score,
        "top_correction": top_correction
    }


@router.get("/error-categories")
async def list_error_categories():
    """
    List all error categories with descriptions.
    Useful for UI to explain errors.
    """
    from app.core.corrections import ERROR_CATEGORIES
    
    return {
        "categories": [
            {
                "type": key,
                "name_ko": val["name_ko"],
                "name_en": val["name_en"],
                "description": val["description"],
                "severity": val["severity"],
                "examples": val["examples"]
            }
            for key, val in ERROR_CATEGORIES.items()
        ]
    }


@router.get("/corrections/examples")
async def get_correction_examples():
    """
    Get example corrections for each formality transition.
    Useful for learning/documentation.
    """
    from app.core.corrections import (
        INFORMAL_TO_POLITE,
        POLITE_TO_FORMAL,
        HONORIFIC_VERBS,
        WORD_FORMALITY
    )
    
    return {
        "informal_to_polite": dict(list(INFORMAL_TO_POLITE.items())[:10]),
        "polite_to_formal": dict(list(POLITE_TO_FORMAL.items())[:10]),
        "honorific_verbs": dict(list(HONORIFIC_VERBS.items())[:10]),
        "formal_words": WORD_FORMALITY
    }
