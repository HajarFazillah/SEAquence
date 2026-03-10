"""
Native Comparison API Endpoints
Compare user's Korean with native speaker expressions
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


# ===========================================
# Request/Response Models
# ===========================================

class CompareRequest(BaseModel):
    """Request for native comparison."""
    sentence: str = Field(..., min_length=1, max_length=500)
    context: str = Field(default="")
    target_role: str = Field(default="friend")
    target_formality: str = Field(default="polite")
    include_cultural_notes: bool = Field(default=True)


class NativeExpressionResponse(BaseModel):
    """A native expression alternative."""
    expression: str
    formality: str
    naturalness: int
    situation: str
    nuance: str


class DifferenceResponse(BaseModel):
    """Difference between user and native expression."""
    category: str
    user_part: str
    native_part: str
    explanation_ko: str
    explanation_en: str


class CompareResponse(BaseModel):
    """Response for native comparison."""
    user_sentence: str
    user_formality: str
    native_expressions: List[NativeExpressionResponse]
    best_match: Optional[str]
    differences: List[DifferenceResponse]
    tips_ko: List[str]
    tips_en: List[str]
    naturalness_score: int
    cultural_note: Optional[str]


class QuickCompareRequest(BaseModel):
    """Quick comparison request."""
    sentence: str = Field(..., min_length=1)
    target_role: str = Field(default="friend")


class QuickCompareResponse(BaseModel):
    """Quick comparison response."""
    user_sentence: str
    native_alternative: str
    main_difference: str
    naturalness_score: int


# ===========================================
# Endpoints
# ===========================================

@router.post("/compare", response_model=CompareResponse)
async def compare_with_native(request: CompareRequest):
    """
    Compare user's Korean sentence with native expressions.
    
    Shows:
    - How native speakers would say the same thing
    - Differences in vocabulary, grammar, nuance
    - Tips for improvement
    - Cultural notes
    """
    from app.services.native_comparison_service import native_comparison_service
    
    result = await native_comparison_service.compare(
        user_sentence=request.sentence,
        context=request.context,
        target_role=request.target_role,
        target_formality=request.target_formality,
        include_cultural_notes=request.include_cultural_notes
    )
    
    return CompareResponse(
        user_sentence=result.user_sentence,
        user_formality=result.user_formality,
        native_expressions=[
            NativeExpressionResponse(
                expression=e.expression,
                formality=e.formality,
                naturalness=e.naturalness,
                situation=e.situation,
                nuance=e.nuance
            )
            for e in result.native_expressions
        ],
        best_match=result.best_match,
        differences=[
            DifferenceResponse(
                category=d.category,
                user_part=d.user_part,
                native_part=d.native_part,
                explanation_ko=d.explanation_ko,
                explanation_en=d.explanation_en
            )
            for d in result.differences
        ],
        tips_ko=result.tips_ko,
        tips_en=result.tips_en,
        naturalness_score=result.naturalness_score,
        cultural_note=result.cultural_note
    )


@router.post("/quick", response_model=QuickCompareResponse)
async def quick_compare(request: QuickCompareRequest):
    """
    Quick native comparison - minimal response for real-time feedback.
    """
    from app.services.native_comparison_service import native_comparison_service
    
    result = await native_comparison_service.compare(
        user_sentence=request.sentence,
        target_role=request.target_role,
        include_cultural_notes=False
    )
    
    main_diff = ""
    if result.differences:
        d = result.differences[0]
        main_diff = f"'{d.user_part}' → '{d.native_part}'"
    
    return QuickCompareResponse(
        user_sentence=result.user_sentence,
        native_alternative=result.best_match or result.user_sentence,
        main_difference=main_diff,
        naturalness_score=result.naturalness_score
    )


@router.get("/common-mistakes")
async def get_common_mistakes():
    """
    Get list of common mistakes non-native speakers make.
    """
    return {
        "common_mistakes": [
            {
                "category": "honorifics",
                "wrong": "교수님 밥 먹었어?",
                "correct": "교수님, 식사하셨어요?",
                "explanation_ko": "어른에게는 '밥' 대신 '식사', 반말 대신 존댓말 사용",
                "explanation_en": "Use '식사' instead of '밥' and polite speech for elders"
            },
            {
                "category": "formality",
                "wrong": "부탁이 있어요",
                "correct": "부탁드려도 될까요?",
                "explanation_ko": "'부탁드리다'가 더 공손한 표현",
                "explanation_en": "'부탁드리다' is more polite than '부탁이 있다'"
            },
            {
                "category": "expression",
                "wrong": "질문 있어요",
                "correct": "여쭤볼 게 있는데요",
                "explanation_ko": "'여쭤보다'는 '묻다'의 겸양어로 더 공손함",
                "explanation_en": "'여쭤보다' is humble form of '묻다', more respectful"
            },
            {
                "category": "softening",
                "wrong": "해 주세요",
                "correct": "해 주실 수 있을까요?",
                "explanation_ko": "질문형으로 바꾸면 더 부드러운 요청",
                "explanation_en": "Phrasing as question makes the request softer"
            },
            {
                "category": "vocabulary",
                "wrong": "이름이 뭐예요?",
                "correct": "성함이 어떻게 되세요?",
                "explanation_ko": "'이름' 대신 '성함', '뭐예요' 대신 '어떻게 되세요'",
                "explanation_en": "Use '성함' (honorific for name) with formal question form"
            },
            {
                "category": "ending",
                "wrong": "알았어요",
                "correct": "알겠습니다 / 네, 알겠습니다",
                "explanation_ko": "상사/교수님께는 '-습니다' 사용",
                "explanation_en": "Use '-습니다' ending with superiors"
            }
        ],
        "tips": [
            "한국어는 상대방에 따라 말투가 완전히 달라져요",
            "처음 만난 사람에게는 일단 존댓말을 쓰세요",
            "모르면 격식체(-습니다)가 안전해요",
            "'혹시'를 붙이면 더 부드러운 요청이 돼요"
        ]
    }


@router.get("/formality-guide/{role}")
async def get_formality_guide(role: str):
    """
    Get formality guide for specific role/relationship.
    
    Roles: professor, boss, senior, colleague, friend, junior
    """
    guides = {
        "professor": {
            "role": "professor",
            "role_ko": "교수님",
            "recommended_formality": "formal",
            "speech_level": "격식체 (-습니다/습니까)",
            "honorific_required": True,
            "examples": {
                "greeting": "안녕하십니까, 교수님",
                "question": "교수님, 여쭤볼 것이 있습니다",
                "request": "혹시 추천서를 부탁드려도 될까요?",
                "thanks": "감사합니다, 교수님",
                "goodbye": "먼저 가보겠습니다. 안녕히 계세요"
            },
            "avoid": ["반말", "너무 짧은 대답", "'네?' 대신 '예?'"],
            "tips": ["항상 '교수님' 호칭 사용", "'여쭤보다' 같은 겸양어 사용"]
        },
        "boss": {
            "role": "boss",
            "role_ko": "상사/팀장님",
            "recommended_formality": "formal",
            "speech_level": "격식체 (-습니다)",
            "honorific_required": True,
            "examples": {
                "greeting": "안녕하십니까, 팀장님",
                "question": "팀장님, 잠깐 여쭤봐도 될까요?",
                "request": "이 부분 확인 부탁드립니다",
                "thanks": "감사합니다",
                "goodbye": "먼저 퇴근하겠습니다. 수고하세요"
            },
            "avoid": ["반말", "개인적인 질문", "너무 친근한 표현"],
            "tips": ["보고할 때는 결론부터", "이메일에서는 더 격식체"]
        },
        "senior": {
            "role": "senior",
            "role_ko": "선배",
            "recommended_formality": "polite",
            "speech_level": "존댓말 (-요) 또는 격식체",
            "honorific_required": True,
            "examples": {
                "greeting": "안녕하세요, 선배님",
                "question": "선배님, 이거 여쭤봐도 돼요?",
                "request": "혹시 시간 되시면 도와주실 수 있어요?",
                "thanks": "선배님 감사해요!",
                "goodbye": "선배님 먼저 가세요~"
            },
            "avoid": ["처음부터 반말", "명령조"],
            "tips": ["친해지면 존댓말(-요)로 전환 OK", "선배가 반말하자고 하면 따라도 됨"]
        },
        "colleague": {
            "role": "colleague",
            "role_ko": "동기/동료",
            "recommended_formality": "polite_to_informal",
            "speech_level": "존댓말 (-요) → 친해지면 반말",
            "honorific_required": False,
            "examples": {
                "greeting": "안녕~ 또는 안녕하세요",
                "question": "이거 어떻게 해?",
                "request": "이거 좀 봐줄 수 있어?",
                "thanks": "고마워~",
                "goodbye": "수고~"
            },
            "avoid": ["처음부터 반말 (나이 확인 후)"],
            "tips": ["나이가 같으면 빨리 반말 전환", "나이 차이 있으면 조심"]
        },
        "friend": {
            "role": "friend",
            "role_ko": "친구",
            "recommended_formality": "informal",
            "speech_level": "반말",
            "honorific_required": False,
            "examples": {
                "greeting": "야~ 또는 ㅎㅇ",
                "question": "뭐해?",
                "request": "야 이거 좀 해줘",
                "thanks": "ㄱㅅ 또는 고마워",
                "goodbye": "ㅂㅂ 또는 나중에 봐"
            },
            "avoid": ["갑자기 존댓말 (어색함)"],
            "tips": ["편하게!", "인터넷 줄임말 OK"]
        },
        "junior": {
            "role": "junior",
            "role_ko": "후배",
            "recommended_formality": "informal_to_polite",
            "speech_level": "반말 또는 존댓말",
            "honorific_required": False,
            "examples": {
                "greeting": "안녕~",
                "question": "요즘 어때?",
                "request": "이거 좀 해줄 수 있어?",
                "thanks": "고마워~",
                "goodbye": "수고해~"
            },
            "avoid": ["너무 명령조", "무시하는 말투"],
            "tips": ["후배도 존중!", "격려해주기"]
        }
    }
    
    if role not in guides:
        raise HTTPException(status_code=404, detail=f"Guide not found for role: {role}")
    
    return guides[role]


# ===========================================
# Vocabulary Recommendation (CLOVA X)
# ===========================================

class VocabularyRequest(BaseModel):
    """Request for vocabulary recommendation."""
    sentence: str = Field(..., min_length=1, max_length=500)
    target_role: str = Field(default="friend")
    target_formality: str = Field(default="polite")
    context: str = Field(default="")


class SituationExpressionsRequest(BaseModel):
    """Request for situation-specific expressions."""
    situation: str = Field(..., min_length=1, description="Describe the situation in English or Korean")
    target_role: str = Field(default="friend")
    target_formality: str = Field(default="polite")


@router.post("/vocabulary/recommend")
async def recommend_vocabulary(request: VocabularyRequest):
    """
    🌟 CLOVA X Powered Vocabulary Recommendation
    
    Analyzes user's sentence and recommends:
    - Better vocabulary choices (honorifics, natural expressions)
    - Grammar improvements
    - Alternative expressions
    - Formality adjustments
    
    Example:
    - Input: "교수님 질문 있어요"
    - Output: Recommends "여쭤볼 것이 있습니다" with explanations
    """
    from app.services.native_comparison_service import native_comparison_service
    
    result = await native_comparison_service.recommend_vocabulary(
        user_sentence=request.sentence,
        target_role=request.target_role,
        target_formality=request.target_formality,
        context=request.context
    )
    
    return result


@router.post("/vocabulary/situation")
async def get_situation_expressions(request: SituationExpressionsRequest):
    """
    🌟 CLOVA X Powered Situation Expressions
    
    Get natural Korean expressions for a specific situation.
    
    Example situations:
    - "asking professor for a recommendation letter"
    - "apologizing for being late to work"
    - "ordering at a Korean cafe"
    - "introducing yourself to seniors"
    - "declining an invitation politely"
    
    Returns expressions with usage tips and cultural notes.
    """
    from app.services.native_comparison_service import native_comparison_service
    
    result = await native_comparison_service.get_expression_for_situation(
        situation=request.situation,
        target_role=request.target_role,
        target_formality=request.target_formality
    )
    
    return result


@router.get("/vocabulary/honorifics")
async def get_honorific_vocabulary():
    """
    Get list of common honorific vocabulary transformations.
    
    Essential vocabulary upgrades for formal/polite speech.
    """
    return {
        "honorific_vocabulary": [
            {
                "category": "verbs",
                "items": [
                    {"basic": "먹다", "honorific": "드시다", "humble": "먹다", "example": "교수님 점심 드셨어요?"},
                    {"basic": "자다", "honorific": "주무시다", "humble": "자다", "example": "안녕히 주무세요"},
                    {"basic": "있다", "honorific": "계시다", "humble": "있다", "example": "교수님 연구실에 계세요?"},
                    {"basic": "말하다", "honorific": "말씀하시다", "humble": "말씀드리다", "example": "말씀 드릴 게 있습니다"},
                    {"basic": "묻다", "honorific": "물으시다", "humble": "여쭙다/여쭤보다", "example": "여쭤봐도 될까요?"},
                    {"basic": "주다", "honorific": "주시다", "humble": "드리다", "example": "선물 드릴게요"},
                    {"basic": "보다", "honorific": "보시다", "humble": "뵙다", "example": "뵙게 되어 영광입니다"},
                    {"basic": "알다", "honorific": "아시다", "humble": "알다", "example": "아시겠지만..."},
                    {"basic": "죽다", "honorific": "돌아가시다", "humble": "죽다", "example": "할아버지께서 돌아가셨어요"}
                ]
            },
            {
                "category": "nouns",
                "items": [
                    {"basic": "이름", "honorific": "성함", "example": "성함이 어떻게 되세요?"},
                    {"basic": "나이", "honorific": "연세", "example": "연세가 어떻게 되세요?"},
                    {"basic": "집", "honorific": "댁", "example": "댁이 어디세요?"},
                    {"basic": "생일", "honorific": "생신", "example": "생신 축하드립니다"},
                    {"basic": "밥", "honorific": "진지/식사", "example": "진지 드셨어요?"},
                    {"basic": "말", "honorific": "말씀", "example": "말씀 감사합니다"},
                    {"basic": "아들", "honorific": "아드님", "example": "아드님이 참 잘생겼네요"},
                    {"basic": "딸", "honorific": "따님", "example": "따님이 몇 살이에요?"}
                ]
            },
            {
                "category": "endings",
                "items": [
                    {"basic": "-어/아", "polite": "-요", "formal": "-습니다", "example": "감사합니다"},
                    {"basic": "-냐?", "polite": "-요?", "formal": "-습니까?", "example": "괜찮으십니까?"},
                    {"basic": "-어라", "polite": "-세요", "formal": "-십시오", "example": "안녕히 가십시오"}
                ]
            }
        ],
        "tips": [
            "높임말 어휘는 상대방을 높일 때 사용",
            "겸양어(humble)는 자신을 낮출 때 사용",
            "교수님, 상사에게는 항상 높임말 어휘 사용",
            "'드리다'는 '주다'의 겸양어로 자주 사용됨"
        ]
    }
