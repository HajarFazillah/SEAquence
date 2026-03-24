"""
Revision API
POST /api/v1/revision/revise          - Revise a sentence to correct formality
POST /api/v1/revision/sample-replies  - Get sample replies for a situation
GET  /api/v1/revision/formality-examples/{level} - Get formality examples
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.services.revision_service import revision_service

router = APIRouter(prefix="/revision", tags=["revision"])


class ReviseRequest(BaseModel):
    sentence: str
    target_role: Optional[str] = None
    target_formality: str = "polite"  # formal / polite / informal
    user_age: int = 22
    target_age: Optional[int] = None


class SampleRepliesRequest(BaseModel):
    situation: str
    target_role: Optional[str] = None
    target_formality: str = "polite"
    count: int = 3


@router.post("/revise")
async def revise_sentence(request: ReviseRequest):
    """
    Revise a Korean sentence to match the expected formality.
    Returns original, revised, and explanation.
    """
    try:
        result = await revision_service.revise(
            sentence=request.sentence,
            target_role=request.target_role,
            target_formality=request.target_formality,
            user_age=request.user_age,
            target_age=request.target_age,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sample-replies")
async def get_sample_replies(request: SampleRepliesRequest):
    """
    Generate sample Korean replies for a situation.
    """
    try:
        result = await revision_service.generate_samples(
            situation=request.situation,
            target_role=request.target_role,
            target_formality=request.target_formality,
            count=request.count,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formality-examples/{level}")
async def get_formality_examples(level: str):
    """
    Get example sentences for a formality level.
    level: formal / polite / informal
    """
    examples = {
        "formal": {
            "level": "formal",
            "name_ko": "격식체 (합쇼체)",
            "endings": ["-습니다", "-습니까", "-십시오"],
            "examples": [
                {"situation": "인사", "sentence": "안녕하십니까?"},
                {"situation": "감사", "sentence": "감사합니다."},
                {"situation": "질문", "sentence": "여쭤봐도 되겠습니까?"},
                {"situation": "부탁", "sentence": "도와주십시오."},
            ],
        },
        "polite": {
            "level": "polite",
            "name_ko": "존댓말 (해요체)",
            "endings": ["-어요", "-아요", "-세요"],
            "examples": [
                {"situation": "인사", "sentence": "안녕하세요?"},
                {"situation": "감사", "sentence": "감사해요."},
                {"situation": "질문", "sentence": "여쭤봐도 돼요?"},
                {"situation": "부탁", "sentence": "도와주세요."},
            ],
        },
        "informal": {
            "level": "informal",
            "name_ko": "반말",
            "endings": ["-어", "-아", "-야"],
            "examples": [
                {"situation": "인사", "sentence": "안녕?"},
                {"situation": "감사", "sentence": "고마워."},
                {"situation": "질문", "sentence": "물어봐도 돼?"},
                {"situation": "부탁", "sentence": "도와줘."},
            ],
        },
    }
    if level not in examples:
        raise HTTPException(status_code=404, detail=f"Level '{level}' not found. Use: formal, polite, informal")
    return examples[level]
