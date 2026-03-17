"""
System Prompt Preview & Testing API
Useful for debugging and testing prompts
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


# ===========================================
# Request/Response Models
# ===========================================

class UserContextInput(BaseModel):
    """User context for personalization."""
    korean_level: str = Field(default="intermediate", description="beginner/intermediate/advanced")
    weak_skills: List[str] = Field(default=[], description="Skills that need practice")
    common_errors: List[str] = Field(default=[], description="Common error types")
    sessions_completed: int = Field(default=0)
    average_score: float = Field(default=0.0)


class SystemPromptRequest(BaseModel):
    """Request for system prompt preview."""
    avatar_id: str = Field(..., description="Avatar ID")
    topic: Optional[str] = Field(None, description="Conversation topic")
    user_context: Optional[UserContextInput] = None
    custom_instruction: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "avatar_id": "professor_kim",
                "topic": "professor_meeting",
                "user_context": {
                    "korean_level": "intermediate",
                    "weak_skills": ["formal_speech", "honorifics"],
                    "common_errors": ["ending_mismatch"],
                    "sessions_completed": 10,
                    "average_score": 72.5
                }
            }]
        }
    }


class SystemPromptResponse(BaseModel):
    """Response with system prompt preview."""
    avatar_id: str
    avatar_name: str
    formality: str
    topic: Optional[str]
    system_prompt: str
    prompt_length: int
    sections: Dict[str, bool]


class TestChatRequest(BaseModel):
    """Request to test chat with specific prompt."""
    avatar_id: str
    message: str
    topic: Optional[str] = None
    user_context: Optional[UserContextInput] = None
    conversation_history: List[Dict[str, str]] = Field(default=[])


# ===========================================
# Endpoints
# ===========================================

@router.post("/preview", response_model=SystemPromptResponse)
async def preview_system_prompt(request: SystemPromptRequest):
    """
    Preview the system prompt that would be sent to HyperCLOVA X.
    
    Useful for:
    - Debugging prompt generation
    - Testing personalization
    - Understanding what the AI sees
    """
    from app.services.enhanced_clova_service import enhanced_clova_service
    from app.core.constants import AVATARS
    
    avatar = AVATARS.get(request.avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail=f"Avatar not found: {request.avatar_id}")
    
    # Convert user context to dict
    user_context_dict = None
    if request.user_context:
        user_context_dict = request.user_context.model_dump()
    
    # Generate prompt
    prompt = enhanced_clova_service.build_system_prompt(
        avatar_id=request.avatar_id,
        topic=request.topic,
        user_context=user_context_dict,
        custom_instruction=request.custom_instruction
    )
    
    # Check which sections are present
    sections = {
        "character_info": "캐릭터 정보" in prompt,
        "user_info": "학습자 정보" in prompt,
        "formality_guide": "말투 지침" in prompt,
        "teaching_mode": "교정 방식" in prompt,
        "error_correction": "자주 하는 실수" in prompt,
        "conversation_rules": "대화 규칙" in prompt,
        "topic_context": "현재 대화 주제" in prompt
    }
    
    return SystemPromptResponse(
        avatar_id=request.avatar_id,
        avatar_name=avatar.get("name_ko", request.avatar_id),
        formality=avatar.get("formality", "polite"),
        topic=request.topic,
        system_prompt=prompt,
        prompt_length=len(prompt),
        sections=sections
    )


@router.post("/test-chat")
async def test_chat_with_prompt(request: TestChatRequest):
    """
    Test chat with the enhanced system prompt.
    
    Returns both the system prompt used and the avatar's response.
    """
    from app.services.enhanced_clova_service import enhanced_clova_service
    from app.core.constants import AVATARS
    
    avatar = AVATARS.get(request.avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail=f"Avatar not found: {request.avatar_id}")
    
    # Convert user context
    user_context_dict = None
    if request.user_context:
        user_context_dict = request.user_context.model_dump()
    
    # Get system prompt preview
    system_prompt = enhanced_clova_service.build_system_prompt(
        avatar_id=request.avatar_id,
        topic=request.topic,
        user_context=user_context_dict
    )
    
    # Generate response
    response = await enhanced_clova_service.generate_avatar_response(
        user_message=request.message,
        avatar_id=request.avatar_id,
        conversation_history=request.conversation_history,
        topic=request.topic,
        user_context=user_context_dict
    )
    
    return {
        "avatar_id": request.avatar_id,
        "avatar_name": avatar.get("name_ko"),
        "user_message": request.message,
        "avatar_response": response,
        "system_prompt_preview": system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt,
        "full_prompt_length": len(system_prompt),
        "api_status": "configured" if enhanced_clova_service.is_configured else "fallback"
    }


@router.get("/formality-guide/{formality}")
async def get_formality_guide(formality: str):
    """
    Get detailed formality guide for a speech level.
    
    Useful for frontend to show tips to users.
    """
    from app.services.enhanced_clova_service import FORMALITY_INSTRUCTIONS_DETAILED
    
    if formality not in FORMALITY_INSTRUCTIONS_DETAILED:
        raise HTTPException(
            status_code=404, 
            detail=f"Formality not found. Use: informal, polite, very_polite"
        )
    
    guide = FORMALITY_INSTRUCTIONS_DETAILED[formality]
    
    return {
        "formality": formality,
        "name_ko": guide["name_ko"],
        "name_en": guide["name_en"],
        "instruction": guide["instruction"],
        "examples": guide["examples"],
        "endings": guide["endings"]
    }


@router.get("/teaching-modes")
async def get_teaching_modes():
    """
    Get available teaching modes for different user levels.
    """
    from app.services.enhanced_clova_service import TEACHING_PROMPTS
    
    return {
        "modes": [
            {"level": "beginner", "description": "친절한 교정, 많은 격려"},
            {"level": "intermediate", "description": "자연스러운 모델링, 가끔 팁 제공"},
            {"level": "advanced", "description": "미묘한 뉘앙스 설명, 관용구 소개"}
        ],
        "prompts": TEACHING_PROMPTS
    }


@router.get("/error-corrections")
async def get_error_correction_prompts():
    """
    Get error correction prompts for common mistakes.
    """
    from app.services.enhanced_clova_service import ERROR_CORRECTION_PROMPTS
    
    return {
        "error_types": list(ERROR_CORRECTION_PROMPTS.keys()),
        "corrections": ERROR_CORRECTION_PROMPTS
    }


@router.post("/compare-prompts")
async def compare_prompts(
    avatar_id: str,
    topic: Optional[str] = None
):
    """
    Compare system prompt with and without personalization.
    
    Shows how user context changes the prompt.
    """
    from app.services.enhanced_clova_service import enhanced_clova_service
    
    # Without personalization
    prompt_basic = enhanced_clova_service.build_system_prompt(
        avatar_id=avatar_id,
        topic=topic,
        user_context=None
    )
    
    # With personalization (example user)
    example_context = {
        "korean_level": "intermediate",
        "weak_skills": ["formal_speech", "honorifics"],
        "common_errors": ["ending_mismatch", "honorific_missing"],
        "sessions_completed": 15,
        "average_score": 68.5
    }
    
    prompt_personalized = enhanced_clova_service.build_system_prompt(
        avatar_id=avatar_id,
        topic=topic,
        user_context=example_context
    )
    
    return {
        "avatar_id": avatar_id,
        "topic": topic,
        "basic_prompt": {
            "content": prompt_basic,
            "length": len(prompt_basic)
        },
        "personalized_prompt": {
            "content": prompt_personalized,
            "length": len(prompt_personalized),
            "user_context_used": example_context
        },
        "difference": {
            "length_increase": len(prompt_personalized) - len(prompt_basic),
            "has_user_info": "학습자 정보" in prompt_personalized,
            "has_teaching_mode": "교정 방식" in prompt_personalized,
            "has_error_correction": "자주 하는 실수" in prompt_personalized
        }
    }
