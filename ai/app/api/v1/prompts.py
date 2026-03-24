"""
Prompts API
POST /api/v1/prompts/preview        - Preview system prompt for avatar
GET  /api/v1/prompts/teaching-modes - List teaching modes
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List

from app.core.constants import AVATARS, FORMALITY_INSTRUCTIONS

router = APIRouter(prefix="/prompts", tags=["prompts"])


class PreviewRequest(BaseModel):
    avatar_id: str
    topic: Optional[str] = None
    situation: Optional[str] = None
    user_context: Optional[dict] = None


@router.post("/preview")
async def preview_prompt(request: PreviewRequest):
    """Preview the system prompt that would be sent to CLOVA for a given avatar."""
    avatar = AVATARS.get(request.avatar_id)
    if not avatar:
        return {"error": f"Avatar '{request.avatar_id}' not found"}

    formality = avatar.get("formality", "polite")
    formality_instruction = FORMALITY_INSTRUCTIONS.get(formality, "")

    # Build user context section
    ctx = request.user_context or {}
    user_section = ""
    if ctx:
        level = ctx.get("korean_level", "intermediate")
        weak = ", ".join(ctx.get("weak_skills", []))
        errors = ", ".join(ctx.get("common_errors", []))
        score = ctx.get("average_score", "N/A")
        sessions = ctx.get("sessions_completed", 0)

        user_section = f"""
## 학습자 정보
- 한국어 수준: {level}
- 취약 스킬: {weak or "없음"}
- 자주 하는 실수: {errors or "없음"}
- 평균 점수: {score}
- 완료한 세션: {sessions}회

위 정보를 참고하여 학습자 수준에 맞게 대화하고,
취약한 부분을 자연스럽게 교정해주세요.
"""

    topic_section = f"\n## 대화 주제\n{request.topic}" if request.topic else ""
    situation_section = f"\n## 상황\n{request.situation}" if request.situation else ""

    system_prompt = f"""당신은 '{avatar["name_ko"]}'입니다.
역할: {avatar["role"]}
성격: {avatar["personality"]}
관심사: {", ".join(avatar.get("topics", []))}

## 말투 규칙
{formality_instruction.strip()}
{user_section}{topic_section}{situation_section}

## 대화 지침
1. 캐릭터를 일관되게 유지하세요.
2. 사용자 수준에 맞게 말하세요.
3. 말투 실수는 자연스럽게 교정해주세요.
"""

    return {
        "avatar_id": request.avatar_id,
        "avatar_name": avatar["name_ko"],
        "system_prompt": system_prompt,
        "char_count": len(system_prompt),
        "formality": formality,
    }


@router.get("/teaching-modes")
async def get_teaching_modes():
    """Get available teaching/correction modes."""
    return {
        "modes": [
            {
                "id": "natural",
                "name_ko": "자연스러운 교정",
                "description": "아바타가 대화 중 자연스럽게 올바른 표현을 보여줌",
                "strictness": "low",
            },
            {
                "id": "explicit",
                "name_ko": "명시적 교정",
                "description": "실수를 바로 지적하고 올바른 표현을 알려줌",
                "strictness": "high",
            },
            {
                "id": "hint",
                "name_ko": "힌트 방식",
                "description": "직접 교정 대신 힌트를 주어 스스로 고치도록 유도",
                "strictness": "medium",
            },
            {
                "id": "silent",
                "name_ko": "교정 없음",
                "description": "교정 없이 자유롭게 대화 연습",
                "strictness": "none",
            },
        ]
    }
