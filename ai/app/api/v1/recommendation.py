"""
Recommendation API
Provides speech level recommendations before starting a conversation
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.core.constants import AVATARS, ROLE_LEVELS
from app.core.situations import SITUATIONS

router = APIRouter(prefix="/recommendation", tags=["Recommendation"])


# ===========================================
# EXAMPLE EXPRESSIONS BY FORMALITY
# ===========================================

EXAMPLE_EXPRESSIONS = {
    "formal": {
        "greetings": [
            {"expression": "안녕하십니까", "context": "인사"},
            {"expression": "처음 뵙겠습니다", "context": "첫 만남"},
        ],
        "questions": [
            {"expression": "질문이 있습니다", "context": "질문할 때"},
            {"expression": "시간이 괜찮으시면 여쭤봐도 될까요?", "context": "허락 구할 때"},
            {"expression": "어떻게 생각하십니까?", "context": "의견 물을 때"},
        ],
        "thanks": [
            {"expression": "감사합니다", "context": "감사 표현"},
            {"expression": "정말 감사드립니다", "context": "깊은 감사"},
        ],
        "apology": [
            {"expression": "죄송합니다", "context": "사과할 때"},
            {"expression": "실례가 되지 않는다면", "context": "조심스럽게"},
        ],
        "farewell": [
            {"expression": "안녕히 계십시오", "context": "작별 인사"},
            {"expression": "좋은 하루 되십시오", "context": "마무리"},
        ],
    },
    "polite": {
        "greetings": [
            {"expression": "안녕하세요", "context": "인사"},
            {"expression": "오랜만이에요", "context": "재회"},
        ],
        "questions": [
            {"expression": "질문 있어요", "context": "질문할 때"},
            {"expression": "시간 괜찮으세요?", "context": "허락 구할 때"},
            {"expression": "어떻게 생각하세요?", "context": "의견 물을 때"},
        ],
        "thanks": [
            {"expression": "감사해요", "context": "감사 표현"},
            {"expression": "고마워요", "context": "가벼운 감사"},
        ],
        "apology": [
            {"expression": "죄송해요", "context": "사과할 때"},
            {"expression": "미안해요", "context": "가벼운 사과"},
        ],
        "farewell": [
            {"expression": "안녕히 가세요", "context": "작별 인사"},
            {"expression": "또 봐요", "context": "다음에 만날 때"},
        ],
    },
    "informal": {
        "greetings": [
            {"expression": "야, 안녕!", "context": "인사"},
            {"expression": "오랜만이야!", "context": "재회"},
            {"expression": "뭐해?", "context": "안부"},
        ],
        "questions": [
            {"expression": "질문 있어", "context": "질문할 때"},
            {"expression": "시간 있어?", "context": "허락 구할 때"},
            {"expression": "어떻게 생각해?", "context": "의견 물을 때"},
        ],
        "thanks": [
            {"expression": "고마워!", "context": "감사 표현"},
            {"expression": "땡큐~", "context": "가벼운 감사"},
        ],
        "apology": [
            {"expression": "미안해", "context": "사과할 때"},
            {"expression": "내 잘못이야", "context": "인정할 때"},
        ],
        "farewell": [
            {"expression": "잘 가!", "context": "작별 인사"},
            {"expression": "나중에 보자!", "context": "다음에 만날 때"},
            {"expression": "바이~", "context": "가벼운 인사"},
        ],
    },
}


AVOID_EXPRESSIONS = {
    "formal": [
        {
            "wrong": "야, 뭐해?",
            "level": "informal",
            "reason": "반말은 이 상황에서 매우 부적절합니다"
        },
        {
            "wrong": "뭐 해요?",
            "level": "polite",
            "reason": "해요체보다 격식체를 사용하는 것이 좋습니다"
        },
    ],
    "polite": [
        {
            "wrong": "야, 뭐해?",
            "level": "informal",
            "reason": "반말은 적절하지 않습니다"
        },
        {
            "wrong": "뭐야?",
            "level": "informal",
            "reason": "존댓말을 사용해 주세요"
        },
    ],
    "informal": [
        # No expressions to avoid when informal is expected
    ],
}


# ===========================================
# SPEECH LEVEL DESCRIPTIONS
# ===========================================

SPEECH_LEVEL_INFO = {
    "formal": {
        "name_ko": "합쇼체",
        "name_en": "Formal",
        "description": "격식체 (-습니다, -습니까)",
        "when_to_use": "교수님, 상사, 공식적인 자리에서 사용",
        "endings": ["-습니다", "-습니까", "-십시오"],
        "honorifics": ["께서", "-시-", "님", "말씀", "여쭤보다", "뵙다"],
    },
    "polite": {
        "name_ko": "해요체",
        "name_en": "Polite",
        "description": "존댓말 (-요, -세요)",
        "when_to_use": "선배, 처음 만난 사람, 일반적인 상황에서 사용",
        "endings": ["-요", "-세요", "-해요"],
        "honorifics": ["-세요", "님"],
    },
    "informal": {
        "name_ko": "반말",
        "name_en": "Informal",
        "description": "반말 (-어, -아, -야)",
        "when_to_use": "친구, 후배, 친한 사이에서 사용",
        "endings": ["-어", "-아", "-야", "-지"],
        "honorifics": [],
    },
}


# ===========================================
# SCHEMAS
# ===========================================

class ExpressionExample(BaseModel):
    expression: str
    context: str


class AvoidExpression(BaseModel):
    wrong: str
    level: str
    reason: str


class RelationshipInfo(BaseModel):
    user_level: int = Field(description="User's hierarchy level (assumed 1 for student)")
    avatar_level: int = Field(description="Avatar's hierarchy level")
    level_difference: int = Field(description="Difference in levels")
    direction: str = Field(description="Relationship direction: higher/equal/lower")


class SpeechLevelInfo(BaseModel):
    name_ko: str
    name_en: str
    description: str
    when_to_use: str
    endings: List[str]
    honorifics: List[str]


class RecommendationResponse(BaseModel):
    """Response for speech level recommendation."""
    
    # Avatar info
    avatar_id: str
    avatar_name_ko: str
    avatar_role: str
    avatar_role_level: int
    
    # Situation info
    situation_id: str
    situation_name_ko: str
    situation_category: str
    
    # Recommendation
    recommended_level: str
    recommended_level_info: SpeechLevelInfo
    
    # Bidirectional formality
    user_to_avatar: str = Field(description="How user should speak to avatar")
    avatar_to_user: str = Field(description="How avatar will speak to user")
    
    # Relationship
    relationship: RelationshipInfo
    reason_ko: str
    reason_en: str
    
    # Example expressions
    example_expressions: Dict[str, List[ExpressionExample]]
    
    # Expressions to avoid
    avoid_expressions: List[AvoidExpression]
    
    # Tips
    tips: List[str]


# ===========================================
# API ENDPOINTS
# ===========================================

@router.get("/speech-level", response_model=RecommendationResponse)
async def get_speech_recommendation(
    avatar_id: str = Query(..., description="Avatar ID"),
    situation_id: str = Query(..., description="Situation ID")
):
    """
    Get speech level recommendation before starting a conversation.
    
    This endpoint provides:
    - Recommended speech level (formal/polite/informal)
    - Example expressions to use
    - Expressions to avoid
    - Relationship explanation
    - Tips for the conversation
    """
    
    # Get avatar
    avatar = AVATARS.get(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail=f"Avatar not found: {avatar_id}")
    
    # Get situation
    situation = SITUATIONS.get(situation_id)
    if not situation:
        raise HTTPException(status_code=404, detail=f"Situation not found: {situation_id}")
    
    # Get role levels
    avatar_role = avatar.get("role", "friend")
    avatar_level = ROLE_LEVELS.get(avatar_role, 1)
    user_level = 1  # Assume user is a college student (level 1)
    
    # Determine relationship direction
    level_diff = avatar_level - user_level
    if level_diff >= 2:
        direction = "much_higher"
    elif level_diff == 1:
        direction = "higher"
    elif level_diff == 0:
        direction = "equal"
    else:
        direction = "lower"
    
    # Get formality settings
    user_to_avatar = avatar.get("user_to_avatar_formality") or avatar.get("formality", "polite")
    avatar_to_user = avatar.get("avatar_to_user_formality", "polite")
    
    # Map formality to level
    formality_to_level = {
        "very_polite": "formal",
        "formal": "formal",
        "polite": "polite",
        "informal": "informal",
        "casual": "informal",
    }
    
    recommended_level = formality_to_level.get(user_to_avatar, "polite")
    
    # Get speech level info
    level_info = SPEECH_LEVEL_INFO.get(recommended_level, SPEECH_LEVEL_INFO["polite"])
    
    # Generate reason
    reason_ko = _generate_reason_ko(avatar, situation, direction, recommended_level)
    reason_en = _generate_reason_en(avatar, situation, direction, recommended_level)
    
    # Get example expressions
    examples = EXAMPLE_EXPRESSIONS.get(recommended_level, EXAMPLE_EXPRESSIONS["polite"])
    
    # Get expressions to avoid
    avoid = AVOID_EXPRESSIONS.get(recommended_level, [])
    
    # Generate tips
    tips = _generate_tips(avatar_role, recommended_level, situation)
    
    return RecommendationResponse(
        avatar_id=avatar_id,
        avatar_name_ko=avatar.get("name_ko", ""),
        avatar_role=avatar_role,
        avatar_role_level=avatar_level,
        situation_id=situation_id,
        situation_name_ko=situation.get("name_ko", ""),
        situation_category=situation.get("category", ""),
        recommended_level=recommended_level,
        recommended_level_info=SpeechLevelInfo(**level_info),
        user_to_avatar=user_to_avatar,
        avatar_to_user=avatar_to_user,
        relationship=RelationshipInfo(
            user_level=user_level,
            avatar_level=avatar_level,
            level_difference=level_diff,
            direction=direction
        ),
        reason_ko=reason_ko,
        reason_en=reason_en,
        example_expressions=examples,
        avoid_expressions=[AvoidExpression(**e) for e in avoid],
        tips=tips
    )


@router.get("/speech-levels")
async def get_all_speech_levels():
    """Get information about all speech levels."""
    return {
        "levels": [
            {
                "level": "formal",
                **SPEECH_LEVEL_INFO["formal"]
            },
            {
                "level": "polite",
                **SPEECH_LEVEL_INFO["polite"]
            },
            {
                "level": "informal",
                **SPEECH_LEVEL_INFO["informal"]
            }
        ]
    }


@router.get("/examples/{level}")
async def get_example_expressions(level: str):
    """Get example expressions for a specific speech level."""
    if level not in EXAMPLE_EXPRESSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid level: {level}. Must be formal/polite/informal"
        )
    
    return {
        "level": level,
        "level_info": SPEECH_LEVEL_INFO.get(level, {}),
        "expressions": EXAMPLE_EXPRESSIONS[level],
        "avoid": AVOID_EXPRESSIONS.get(level, [])
    }


# ===========================================
# HELPER FUNCTIONS
# ===========================================

def _generate_reason_ko(
    avatar: Dict,
    situation: Dict,
    direction: str,
    level: str
) -> str:
    """Generate Korean explanation for the recommendation."""
    
    role_names = {
        "professor": "교수님",
        "boss": "상사",
        "senior": "선배",
        "friend": "친구",
        "junior": "후배",
    }
    
    role = avatar.get("role", "friend")
    role_name = role_names.get(role, "상대방")
    situation_name = situation.get("name_ko", "대화")
    
    if direction == "much_higher":
        return (
            f"{role_name}은(는) 높은 지위의 분이시고, "
            f"'{situation_name}'은(는) 공식적인 상황이므로 "
            f"격식체(-습니다)를 사용해야 합니다."
        )
    elif direction == "higher":
        return (
            f"{role_name}은(는) 나보다 높은 위치에 있으므로 "
            f"존댓말(-요)을 사용하는 것이 좋습니다."
        )
    elif direction == "equal":
        return (
            f"{role_name}은(는) 친구/동기이므로 "
            f"반말을 사용해도 괜찮습니다. "
            f"편하게 대화해 보세요!"
        )
    else:  # lower
        return (
            f"{role_name}은(는) 후배이므로 "
            f"반말을 사용해도 괜찮습니다. "
            f"하지만 존댓말을 사용해도 좋아요."
        )


def _generate_reason_en(
    avatar: Dict,
    situation: Dict,
    direction: str,
    level: str
) -> str:
    """Generate English explanation for the recommendation."""
    
    role = avatar.get("role", "friend")
    situation_name = situation.get("name_en", "conversation")
    
    if direction == "much_higher":
        return (
            f"The {role} is of higher status, and "
            f"'{situation_name}' is a formal situation. "
            f"Formal speech (-습니다) is required."
        )
    elif direction == "higher":
        return (
            f"The {role} is of higher status than you. "
            f"Polite speech (-요) is recommended."
        )
    elif direction == "equal":
        return (
            f"The {role} is your peer/friend. "
            f"Informal speech is acceptable. "
            f"Feel free to speak casually!"
        )
    else:  # lower
        return (
            f"The {role} is of lower status. "
            f"Informal speech is acceptable, "
            f"but being polite is also fine."
        )


def _generate_tips(role: str, level: str, situation: Dict) -> List[str]:
    """Generate tips for the conversation."""
    
    tips = []
    
    # Level-specific tips
    if level == "formal":
        tips.extend([
            "격식체(-습니다)를 사용하세요",
            "존칭 어휘를 사용하세요 (말씀, 여쭤보다, 뵙다)",
            "높임 선어말어미 '-시-'를 사용하세요",
            "조사 '께서', '께'를 사용하면 더 공손합니다",
        ])
    elif level == "polite":
        tips.extend([
            "해요체(-요)를 사용하세요",
            "'-세요'로 존칭을 표현할 수 있습니다",
            "자연스럽게 대화하되 존댓말을 유지하세요",
        ])
    else:  # informal
        tips.extend([
            "반말(-어, -아)을 사용해도 괜찮아요",
            "친근하게 대화해 보세요",
            "감정을 자연스럽게 표현해 보세요",
        ])
    
    # Situation-specific tips
    situation_tips = situation.get("tips_ko", [])
    tips.extend(situation_tips[:2])  # Add up to 2 situation tips
    
    return tips[:5]  # Return max 5 tips
