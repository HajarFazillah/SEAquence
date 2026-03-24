"""
Speech Level Recommendation API

Sophisticated multi-factor speech level calculation.

GET /api/v1/recommendation/speech-level - Simple lookup
POST /api/v1/recommendation/speech-level/calculate - Multi-factor calculation
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.services.speech_calculator import (
    speech_calculator,
    SpeechLevelInput,
    SpeechLevelResult,
    Closeness,
    SocialStatus,
    Context,
    ROLE_CONFIGS,
)


router = APIRouter(prefix="/recommendation", tags=["recommendation"])


# ============================================================================
# Request/Response Models
# ============================================================================

class SpeechLevelRequest(BaseModel):
    """Request for sophisticated speech level calculation"""
    role: str
    user_age: int
    avatar_age: int
    
    # Optional factors
    closeness: str = "acquaintance"   # just_met/stranger/acquaintance/friendly/close/very_close/intimate
    social_status: str = "equal"      # much_lower/lower/equal/higher/much_higher
    context: str = "neutral"          # very_formal/formal/professional/neutral/casual/intimate
    
    # Additional factors
    years_known: int = 0
    is_first_meeting: bool = False
    user_position_level: int = 0      # 0-10 (job level)
    avatar_position_level: int = 0
    is_public_setting: bool = False
    is_being_observed: bool = False


class SpeechLevelResponse(BaseModel):
    """Response with calculated speech levels"""
    # Calculated levels
    avatar_to_user: str
    user_to_avatar: str
    
    # Korean names
    avatar_to_user_ko: str
    user_to_avatar_ko: str
    
    # Explanation
    explanation: str
    factors_applied: List[str]
    confidence: float
    
    # Examples
    avatar_example: str
    user_example: str
    
    # Tips
    tips: List[str]
    common_mistakes: List[str]


class SimpleRoleResponse(BaseModel):
    """Simple response for basic role lookup"""
    role: str
    role_label: str
    to_user: Dict[str, Any]
    from_user: Dict[str, Any]


class RoleInfo(BaseModel):
    """Information about a role"""
    role_id: str
    name_ko: str
    category: str
    is_authority: bool
    default_avatar_to_user: str
    default_user_to_avatar: str
    allows_banmal_if_close: bool
    age_sensitive: bool


# ============================================================================
# Constants
# ============================================================================

LEVEL_NAMES = {
    "formal": {
        "ko": "합쇼체", 
        "en": "Formal", 
        "endings": "-습니다, -습니까",
        "description": "가장 격식있는 말투입니다. '-습니다', '-습니까' 등의 어미를 사용합니다.",
        "examples": ["안녕하십니까", "감사합니다", "어디 가십니까?"],
    },
    "polite": {
        "ko": "해요체", 
        "en": "Polite", 
        "endings": "-어요, -아요",
        "description": "공손하지만 부드러운 말투입니다. '-어요', '-아요' 등의 어미를 사용합니다.",
        "examples": ["안녕하세요", "감사해요", "어디 가요?"],
    },
    "informal": {
        "ko": "반말", 
        "en": "Informal", 
        "endings": "-어, -야",
        "description": "친근한 말투입니다. '-어', '-아', '-야' 등의 어미를 사용합니다.",
        "examples": ["안녕", "고마워", "어디 가?"],
    },
}

ROLE_NAMES_KO = {
    "friend": "친구",
    "close_friend": "절친",
    "classmate": "반 친구",
    "roommate": "룸메이트",
    "club_member": "동아리 멤버",
    "junior": "후배",
    "senior": "선배",
    "professor": "교수님",
    "teacher": "선생님",
    "tutor": "과외 선생님",
    "younger_sibling": "동생",
    "older_brother": "형/오빠",
    "older_sister": "누나/언니",
    "cousin": "사촌",
    "parent": "부모님",
    "grandparent": "조부모님",
    "uncle_aunt": "삼촌/이모",
    "in_law": "시댁/처가 어른",
    "intern": "인턴",
    "colleague": "동료",
    "teammate": "팀원",
    "team_leader": "팀장",
    "manager": "매니저",
    "boss": "사장님",
    "ceo": "대표님",
    "client": "고객/클라이언트",
    "mentor": "멘토",
    "staff": "직원",
    "customer": "손님",
    "stranger": "모르는 사람",
    "neighbor": "이웃",
    "doctor": "의사 선생님",
    "delivery": "배달원",
    "taxi_driver": "택시 기사님",
}


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/speech-level/calculate", response_model=SpeechLevelResponse)
async def calculate_speech_level(request: SpeechLevelRequest):
    """
    Calculate speech levels with sophisticated multi-factor analysis.
    
    ## Factors Considered (10 total)
    
    1. **Role (관계)** - Base relationship type
    2. **Age Difference (나이 차이)** - How much older/younger
    3. **Closeness (친밀도)** - How close the relationship is
    4. **Social Status (사회적 지위)** - Professional/social hierarchy
    5. **Context (상황)** - Formal vs casual setting
    6. **First Meeting (첫 만남)** - Just met vs ongoing
    7. **Position Level (직급)** - Workplace hierarchy
    8. **Years Known (알고 지낸 기간)** - Duration of relationship
    9. **Public Setting (공공장소)** - In public or private
    10. **Being Observed (관찰 상황)** - Others watching?
    
    ## Example Request
    
    ```json
    {
      "role": "senior",
      "user_age": 22,
      "avatar_age": 28,
      "closeness": "close",
      "context": "casual"
    }
    ```
    """
    try:
        input_data = SpeechLevelInput(
            role=request.role,
            user_age=request.user_age,
            avatar_age=request.avatar_age,
            closeness=Closeness(request.closeness),
            social_status=SocialStatus(request.social_status),
            context=Context(request.context),
            years_known=request.years_known,
            is_first_meeting=request.is_first_meeting,
            user_position_level=request.user_position_level,
            avatar_position_level=request.avatar_position_level,
            is_public_setting=request.is_public_setting,
            is_being_observed=request.is_being_observed,
        )
        
        result = speech_calculator.calculate(input_data)
        
        return SpeechLevelResponse(
            avatar_to_user=result.avatar_to_user.value,
            user_to_avatar=result.user_to_avatar.value,
            avatar_to_user_ko=LEVEL_NAMES[result.avatar_to_user.value]["ko"],
            user_to_avatar_ko=LEVEL_NAMES[result.user_to_avatar.value]["ko"],
            explanation=result.explanation,
            factors_applied=result.factors_applied,
            confidence=result.confidence,
            avatar_example=result.avatar_example,
            user_example=result.user_example,
            tips=result.tips,
            common_mistakes=result.common_mistakes,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/speech-level", response_model=SimpleRoleResponse)
async def get_speech_level_simple(
    role: str = Query(..., description="Role ID (e.g., 'senior', 'professor')"),
):
    """
    Get default speech levels for a role (simple lookup).
    
    For sophisticated calculation with age/closeness factors,
    use POST /speech-level/calculate instead.
    """
    role_config = ROLE_CONFIGS.get(role)
    
    if not role_config:
        raise HTTPException(status_code=404, detail=f"Role '{role}' not found")
    
    role_label = ROLE_NAMES_KO.get(role, role)
    to_user_level = role_config.base_avatar_to_user.value
    from_user_level = role_config.base_user_to_avatar.value
    
    return SimpleRoleResponse(
        role=role,
        role_label=role_label,
        to_user={
            "level": to_user_level,
            "name_ko": LEVEL_NAMES[to_user_level]["ko"],
            "name_en": LEVEL_NAMES[to_user_level]["en"],
            "endings": LEVEL_NAMES[to_user_level]["endings"],
            "description": LEVEL_NAMES[to_user_level]["description"],
            "examples": LEVEL_NAMES[to_user_level]["examples"],
        },
        from_user={
            "level": from_user_level,
            "name_ko": LEVEL_NAMES[from_user_level]["ko"],
            "name_en": LEVEL_NAMES[from_user_level]["en"],
            "endings": LEVEL_NAMES[from_user_level]["endings"],
            "description": LEVEL_NAMES[from_user_level]["description"],
            "examples": LEVEL_NAMES[from_user_level]["examples"],
        },
    )


@router.get("/roles", response_model=Dict[str, List[RoleInfo]])
async def get_all_roles():
    """
    Get all available roles grouped by category.
    
    Categories:
    - friend: 친구/동기
    - school: 학교
    - family: 가족
    - work: 직장
    - service: 서비스/기타
    - stranger: 처음 보는 사람
    """
    categorized: Dict[str, List[RoleInfo]] = {
        "friend": [],
        "school": [],
        "family": [],
        "work": [],
        "service": [],
        "stranger": [],
    }
    
    for role_id, config in ROLE_CONFIGS.items():
        role_info = RoleInfo(
            role_id=role_id,
            name_ko=ROLE_NAMES_KO.get(role_id, role_id),
            category=config.category.value,
            is_authority=config.is_authority,
            default_avatar_to_user=config.base_avatar_to_user.value,
            default_user_to_avatar=config.base_user_to_avatar.value,
            allows_banmal_if_close=config.allows_banmal_if_close,
            age_sensitive=config.age_sensitive,
        )
        categorized[config.category.value].append(role_info)
    
    return categorized


@router.get("/closeness-options")
async def get_closeness_options():
    """Get all closeness level options"""
    return {
        "options": [
            {"id": "just_met", "name_ko": "처음 만남", "name_en": "Just met", "description": "오늘 처음 만났어요"},
            {"id": "stranger", "name_ko": "모르는 사이", "name_en": "Stranger", "description": "서로 잘 몰라요"},
            {"id": "acquaintance", "name_ko": "아는 사이", "name_en": "Acquaintance", "description": "알지만 친하진 않아요"},
            {"id": "friendly", "name_ko": "친한 편", "name_en": "Friendly", "description": "가끔 만나요"},
            {"id": "close", "name_ko": "친함", "name_en": "Close", "description": "자주 만나고 친해요"},
            {"id": "very_close", "name_ko": "매우 친함", "name_en": "Very close", "description": "반말해도 될 정도로 친해요"},
            {"id": "intimate", "name_ko": "아주 가까움", "name_en": "Intimate", "description": "가족처럼 가까워요"},
        ]
    }


@router.get("/context-options")
async def get_context_options():
    """Get all context/setting options"""
    return {
        "options": [
            {"id": "very_formal", "name_ko": "매우 공식적", "name_en": "Very formal", "examples": ["면접", "공식 행사", "발표"]},
            {"id": "formal", "name_ko": "공식적", "name_en": "Formal", "examples": ["회의", "업무 미팅"]},
            {"id": "professional", "name_ko": "업무", "name_en": "Professional", "examples": ["사무실", "일반 업무"]},
            {"id": "neutral", "name_ko": "보통", "name_en": "Neutral", "examples": ["일상 대화"]},
            {"id": "casual", "name_ko": "편한", "name_en": "Casual", "examples": ["카페", "식사", "산책"]},
            {"id": "intimate", "name_ko": "사적인", "name_en": "Intimate", "examples": ["집", "개인 공간"]},
        ]
    }


@router.get("/social-status-options")
async def get_social_status_options():
    """Get all social status options"""
    return {
        "options": [
            {"id": "much_lower", "name_ko": "훨씬 낮음", "name_en": "Much lower"},
            {"id": "lower", "name_ko": "낮음", "name_en": "Lower"},
            {"id": "equal", "name_ko": "동등", "name_en": "Equal"},
            {"id": "higher", "name_ko": "높음", "name_en": "Higher"},
            {"id": "much_higher", "name_ko": "훨씬 높음", "name_en": "Much higher"},
        ]
    }


@router.get("/examples")
async def get_speech_level_examples():
    """
    Get example calculations showing how factors affect speech levels.
    """
    examples = []
    
    # Example 1: Close senior, same generation
    input1 = SpeechLevelInput(
        role="senior",
        user_age=22,
        avatar_age=24,
        closeness=Closeness.VERY_CLOSE,
        context=Context.CASUAL,
    )
    result1 = speech_calculator.calculate(input1)
    examples.append({
        "title": "친한 선배 (나이 비슷)",
        "description": "2살 차이, 매우 친함, 카페에서",
        "input": {"role": "senior", "user_age": 22, "avatar_age": 24, "closeness": "very_close"},
        "result": {
            "user_to_avatar": result1.user_to_avatar.value,
            "user_to_avatar_ko": LEVEL_NAMES[result1.user_to_avatar.value]["ko"],
            "explanation": result1.explanation,
        }
    })
    
    # Example 2: Senior with big age gap
    input2 = SpeechLevelInput(
        role="senior",
        user_age=22,
        avatar_age=35,
        closeness=Closeness.ACQUAINTANCE,
    )
    result2 = speech_calculator.calculate(input2)
    examples.append({
        "title": "나이 많은 선배",
        "description": "13살 차이, 아는 사이",
        "input": {"role": "senior", "user_age": 22, "avatar_age": 35, "closeness": "acquaintance"},
        "result": {
            "user_to_avatar": result2.user_to_avatar.value,
            "user_to_avatar_ko": LEVEL_NAMES[result2.user_to_avatar.value]["ko"],
            "explanation": result2.explanation,
        }
    })
    
    # Example 3: Professor (always formal)
    input3 = SpeechLevelInput(
        role="professor",
        user_age=22,
        avatar_age=55,
        closeness=Closeness.CLOSE,
    )
    result3 = speech_calculator.calculate(input3)
    examples.append({
        "title": "친한 교수님",
        "description": "친해도 항상 존댓말 (권위자)",
        "input": {"role": "professor", "user_age": 22, "avatar_age": 55, "closeness": "close"},
        "result": {
            "user_to_avatar": result3.user_to_avatar.value,
            "user_to_avatar_ko": LEVEL_NAMES[result3.user_to_avatar.value]["ko"],
            "explanation": result3.explanation,
        }
    })
    
    # Example 4: Same-age friend
    input4 = SpeechLevelInput(
        role="friend",
        user_age=22,
        avatar_age=22,
        closeness=Closeness.CLOSE,
    )
    result4 = speech_calculator.calculate(input4)
    examples.append({
        "title": "동갑 친구",
        "description": "같은 나이, 친한 친구",
        "input": {"role": "friend", "user_age": 22, "avatar_age": 22, "closeness": "close"},
        "result": {
            "user_to_avatar": result4.user_to_avatar.value,
            "user_to_avatar_ko": LEVEL_NAMES[result4.user_to_avatar.value]["ko"],
            "explanation": result4.explanation,
        }
    })
    
    # Example 5: Formal context changes things
    input5 = SpeechLevelInput(
        role="colleague",
        user_age=28,
        avatar_age=30,
        closeness=Closeness.CLOSE,
        context=Context.FORMAL,
    )
    result5 = speech_calculator.calculate(input5)
    examples.append({
        "title": "회의 중인 친한 동료",
        "description": "평소엔 편하게 해도 회의에선 존댓말",
        "input": {"role": "colleague", "user_age": 28, "avatar_age": 30, "closeness": "close", "context": "formal"},
        "result": {
            "user_to_avatar": result5.user_to_avatar.value,
            "user_to_avatar_ko": LEVEL_NAMES[result5.user_to_avatar.value]["ko"],
            "explanation": result5.explanation,
        }
    })
    
    return {"examples": examples}
