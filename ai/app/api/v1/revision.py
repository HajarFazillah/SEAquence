"""
Revision & Sample Reply API Endpoints
Correct user's Korean and provide sample replies using HyperCLOVA X
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


# ===========================================
# Request/Response Models
# ===========================================

class RevisionRequest(BaseModel):
    """Request to revise a Korean sentence."""
    sentence: str = Field(..., min_length=1, max_length=500, description="Korean sentence to revise")
    target_role: str = Field(default="senior", description="Who user is talking to")
    target_formality: str = Field(default="polite", description="Expected formality level")
    context: Optional[str] = Field(None, description="Conversation context")
    user_level: str = Field(default="intermediate", description="User's Korean level")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "sentence": "교수님 질문 있어요",
                "target_role": "professor",
                "target_formality": "very_polite",
                "context": "교수님 연구실 방문",
                "user_level": "intermediate"
            }]
        }
    }


class ErrorDetail(BaseModel):
    """Details about an error found."""
    type: str
    original_part: str
    corrected_part: str
    explanation_ko: str
    explanation_en: str


class RevisionResponse(BaseModel):
    """Response with revised sentence and explanation."""
    original: str
    has_error: bool
    revised: str
    sample_replies: List[str]
    errors: List[ErrorDetail]
    alternatives: List[str]
    tips: List[str]
    formality_score: int


class SampleRequest(BaseModel):
    """Request for sample Korean replies."""
    situation: str = Field(..., description="What you want to say (in any language)")
    target_role: str = Field(default="senior")
    target_formality: str = Field(default="polite")
    num_samples: int = Field(default=3, ge=1, le=5)
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "situation": "I want to ask my professor a question about the assignment",
                "target_role": "professor",
                "target_formality": "very_polite",
                "num_samples": 3
            }]
        }
    }


class SampleReply(BaseModel):
    """A sample Korean reply."""
    korean: str
    formality: str
    romanization: Optional[str] = None
    literal_meaning: Optional[str] = None
    usage_note: Optional[str] = None


class SampleResponse(BaseModel):
    """Response with sample Korean replies."""
    situation: str
    target_role: str
    recommended_formality: str
    samples: List[SampleReply]
    common_mistakes: List[str]
    cultural_note: Optional[str] = None


class CompareRequest(BaseModel):
    """Request to compare two sentences."""
    sentence1: str = Field(..., description="First Korean sentence")
    sentence2: str = Field(..., description="Second Korean sentence")


# ===========================================
# Endpoints
# ===========================================

@router.post("/revise", response_model=RevisionResponse)
async def revise_sentence(request: RevisionRequest):
    """
    Revise a Korean sentence and provide corrections.
    
    This endpoint:
    1. Analyzes the user's Korean sentence
    2. Identifies grammar and formality errors
    3. Provides the corrected version
    4. Explains what was wrong
    5. Suggests sample replies
    
    Example:
    - Input: "교수님 질문 있어요" (polite, but should be formal)
    - Output: 
      - revised: "교수님, 질문이 있습니다"
      - errors: [{"type": "ending_mismatch", "explanation": "..."}]
      - sample_replies: ["교수님, 여쭤볼 것이 있습니다", ...]
    """
    from app.services.revision_service import revision_service
    
    result = await revision_service.revise_and_sample(
        user_sentence=request.sentence,
        target_role=request.target_role,
        target_formality=request.target_formality,
        context=request.context,
        user_level=request.user_level
    )
    
    # Convert to response model
    errors = []
    for err in result.get("errors", []):
        errors.append(ErrorDetail(
            type=err.get("type", "unknown"),
            original_part=err.get("original_part", ""),
            corrected_part=err.get("corrected_part", ""),
            explanation_ko=err.get("explanation_ko", ""),
            explanation_en=err.get("explanation_en", "")
        ))
    
    return RevisionResponse(
        original=result.get("original", request.sentence),
        has_error=result.get("has_error", False),
        revised=result.get("revised", request.sentence),
        sample_replies=result.get("sample_replies", []),
        errors=errors,
        alternatives=result.get("alternatives", []),
        tips=result.get("tips", []),
        formality_score=result.get("formality_score", 50)
    )


@router.post("/sample-replies", response_model=SampleResponse)
async def get_sample_replies(request: SampleRequest):
    """
    Get sample Korean replies for a given situation.
    
    Describe what you want to say (in any language), and get
    natural Korean expressions for that situation.
    
    Example:
    - Input: "I want to ask if the professor has time to meet"
    - Output: 
      - samples: [
          "교수님, 시간 되시면 면담 가능할까요?",
          "교수님, 잠시 뵐 수 있을까요?",
          ...
        ]
    """
    from app.services.revision_service import revision_service
    
    result = await revision_service.get_sample_reply(
        situation=request.situation,
        target_role=request.target_role,
        target_formality=request.target_formality,
        num_samples=request.num_samples
    )
    
    # Convert to response model
    samples = []
    for s in result.get("samples", []):
        samples.append(SampleReply(
            korean=s.get("korean", ""),
            formality=s.get("formality", request.target_formality),
            romanization=s.get("romanization"),
            literal_meaning=s.get("literal_meaning"),
            usage_note=s.get("usage_note")
        ))
    
    return SampleResponse(
        situation=result.get("situation", request.situation),
        target_role=result.get("target_role", request.target_role),
        recommended_formality=result.get("recommended_formality", request.target_formality),
        samples=samples,
        common_mistakes=result.get("common_mistakes", []),
        cultural_note=result.get("cultural_note")
    )


@router.post("/compare")
async def compare_sentences(request: CompareRequest):
    """
    Compare two Korean sentences and explain the differences.
    
    Useful for understanding:
    - Formality level differences
    - Nuance differences
    - When to use each expression
    
    Example:
    - sentence1: "밥 먹었어?"
    - sentence2: "식사하셨습니까?"
    - Result: Explains formality and usage differences
    """
    from app.services.revision_service import revision_service
    
    result = await revision_service.explain_difference(
        sentence1=request.sentence1,
        sentence2=request.sentence2
    )
    
    return result


@router.post("/quick-fix")
async def quick_fix(
    sentence: str,
    target_formality: str = "polite"
):
    """
    Quick fix for a Korean sentence - minimal response.
    
    Returns only:
    - Original sentence
    - Fixed sentence
    - Was there an error?
    
    Good for real-time feedback while typing.
    """
    from app.services.revision_service import revision_service
    
    result = await revision_service.revise_and_sample(
        user_sentence=sentence,
        target_formality=target_formality,
        user_level="intermediate"
    )
    
    return {
        "original": sentence,
        "revised": result.get("revised", sentence),
        "has_error": result.get("has_error", False),
        "formality_score": result.get("formality_score", 50)
    }


@router.get("/formality-examples/{formality}")
async def get_formality_examples(formality: str):
    """
    Get example sentences for a specific formality level.
    
    Useful for showing users what each level looks like.
    """
    examples = {
        "informal": {
            "name_ko": "반말",
            "name_en": "Informal",
            "use_with": ["친구", "동기", "후배", "가족"],
            "examples": [
                {"situation": "인사", "korean": "야, 안녕!", "english": "Hey, hi!"},
                {"situation": "질문", "korean": "뭐 해?", "english": "What are you doing?"},
                {"situation": "부탁", "korean": "이거 좀 해줘", "english": "Do this for me"},
                {"situation": "감사", "korean": "고마워!", "english": "Thanks!"},
                {"situation": "사과", "korean": "미안해", "english": "Sorry"},
            ]
        },
        "polite": {
            "name_ko": "존댓말",
            "name_en": "Polite",
            "use_with": ["선배", "처음 만난 사람", "가게 직원"],
            "examples": [
                {"situation": "인사", "korean": "안녕하세요!", "english": "Hello!"},
                {"situation": "질문", "korean": "뭐 해요?", "english": "What are you doing?"},
                {"situation": "부탁", "korean": "이거 좀 해주세요", "english": "Please do this"},
                {"situation": "감사", "korean": "감사해요!", "english": "Thank you!"},
                {"situation": "사과", "korean": "죄송해요", "english": "I'm sorry"},
            ]
        },
        "very_polite": {
            "name_ko": "격식체",
            "name_en": "Formal",
            "use_with": ["교수님", "상사", "공식적 상황", "고객"],
            "examples": [
                {"situation": "인사", "korean": "안녕하십니까?", "english": "Hello (formal)"},
                {"situation": "질문", "korean": "무엇을 하고 계십니까?", "english": "What are you doing?"},
                {"situation": "부탁", "korean": "이것 좀 해주시겠습니까?", "english": "Could you do this?"},
                {"situation": "감사", "korean": "감사합니다", "english": "Thank you"},
                {"situation": "사과", "korean": "죄송합니다", "english": "I apologize"},
            ]
        }
    }
    
    if formality not in examples:
        raise HTTPException(
            status_code=404,
            detail=f"Formality '{formality}' not found. Use: informal, polite, very_polite"
        )
    
    return examples[formality]


@router.post("/batch-revise")
async def batch_revise(
    sentences: List[str],
    target_formality: str = "polite"
):
    """
    Revise multiple sentences at once.
    
    Useful for checking a whole conversation or text.
    """
    from app.services.revision_service import revision_service
    
    results = []
    for sentence in sentences[:10]:  # Limit to 10 sentences
        result = await revision_service.revise_and_sample(
            user_sentence=sentence,
            target_formality=target_formality
        )
        results.append({
            "original": sentence,
            "revised": result.get("revised", sentence),
            "has_error": result.get("has_error", False),
            "score": result.get("formality_score", 50)
        })
    
    # Calculate overall score
    total_score = sum(r["score"] for r in results) / len(results) if results else 0
    error_count = sum(1 for r in results if r["has_error"])
    
    return {
        "results": results,
        "summary": {
            "total_sentences": len(results),
            "sentences_with_errors": error_count,
            "average_score": round(total_score, 1)
        }
    }
