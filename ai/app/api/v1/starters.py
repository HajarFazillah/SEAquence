"""
Conversation Starters API

GET  /api/v1/starters - Get smart conversation starters
POST /api/v1/starters/generate - Generate AI-powered starters
"""

from fastapi import APIRouter, Query
from typing import Optional, List

from app.services.conversation_starters import (
    starter_service,
    StarterRequest,
    StarterResponse,
    ConversationStarter,
    TimeOfDay,
)
from app.schemas.avatar import SpeechLevel, get_speech_levels_for_role


router = APIRouter(prefix="/starters", tags=["conversation-starters"])


# ============================================================================
# Quick Starters (Template-based, Fast)
# ============================================================================

@router.get("/quick", response_model=StarterResponse)
async def get_quick_starters(
    role: str = Query(..., description="Avatar role (e.g., 'friend', 'senior', 'professor')"),
    avatar_name: str = Query("친구", description="Avatar's Korean name"),
    interests: Optional[str] = Query(None, description="Comma-separated interests"),
    hour: Optional[int] = Query(None, description="Hour (0-23) for testing, defaults to current"),
    count: int = Query(5, description="Number of starters to generate", ge=1, le=10),
):
    """
    Get quick conversation starters (no AI, fast).
    
    Uses templates based on:
    - Time of day
    - Speech level for role
    - Provided interests
    
    ## Example
    ```
    GET /api/v1/starters/quick?role=senior&avatar_name=민수&interests=게임,음악
    ```
    """
    
    interest_list = interests.split(",") if interests else []
    
    request = StarterRequest(
        avatar_name=avatar_name,
        avatar_role=role,
        avatar_interests=interest_list,
        count=count,
    )
    
    return await starter_service.get_starters(
        request=request,
        use_ai=False,
        hour=hour,
    )


# ============================================================================
# AI-Powered Starters
# ============================================================================

@router.post("/generate", response_model=StarterResponse)
async def generate_ai_starters(
    request: StarterRequest,
    hour: Optional[int] = Query(None, description="Hour override for testing"),
):
    """
    Generate AI-powered conversation starters using CLOVA.
    
    Considers:
    - Time of day
    - Avatar's interests & personality
    - User's interests
    - Past conversation topics (memory)
    - Situation/context
    - Appropriate speech level
    
    ## Example Request
    ```json
    {
      "avatar_name": "이민수",
      "avatar_role": "senior",
      "avatar_interests": ["게임", "코딩", "음악"],
      "avatar_personality": ["친절함", "유머러스"],
      "user_name": "나린",
      "user_interests": ["K-POP", "영화"],
      "past_topics": ["지난주 시험", "새로운 게임"],
      "situation": "카페에서 만남",
      "count": 5
    }
    ```
    
    ## Example Response
    ```json
    {
      "starters": [
        {
          "text": "안녕! 요즘 새 게임 해봤어?",
          "category": "interest",
          "follow_up_hint": "어떤 게임인지 물어보세요",
          "context": "게임 관심사 기반"
        }
      ],
      "time_of_day": "afternoon",
      "speech_level": "polite",
      "greeting": "안녕하세요"
    }
    ```
    """
    
    return await starter_service.get_starters(
        request=request,
        use_ai=True,
        hour=hour,
    )


# ============================================================================
# Starters with Memory Integration
# ============================================================================

@router.get("/with-memory", response_model=StarterResponse)
async def get_starters_with_memory(
    role: str = Query(..., description="Avatar role"),
    avatar_name: str = Query(..., description="Avatar's Korean name"),
    avatar_id: str = Query(..., description="Avatar ID for memory lookup"),
    user_id: str = Query(..., description="User ID for memory lookup"),
    interests: Optional[str] = Query(None, description="Comma-separated avatar interests"),
    user_interests: Optional[str] = Query(None, description="Comma-separated user interests"),
    situation: Optional[str] = Query(None, description="Current situation"),
    hour: Optional[int] = Query(None, description="Hour override"),
    count: int = Query(5, ge=1, le=10),
):
    """
    Get conversation starters with memory integration.
    
    Fetches past conversation topics from memory service
    and uses them to generate relevant starters.
    """
    
    # Get memory context
    past_topics = []
    last_summary = None
    
    try:
        from app.services.memory_service import memory_service
        
        # Get recent memories
        memories = memory_service.get_memories(user_id, avatar_id)
        
        # Extract topics from memories
        for memory in memories[:5]:
            if memory.memory_type == "topic":
                past_topics.append(memory.content)
        
        # Get last conversation summary if available
        context = memory_service.get_context_for_chat(user_id, avatar_id)
        if context and "relationship_summary" in context:
            last_summary = context["relationship_summary"]
            
    except Exception as e:
        print(f"Memory lookup error: {e}")
    
    interest_list = interests.split(",") if interests else []
    user_interest_list = user_interests.split(",") if user_interests else []
    
    request = StarterRequest(
        avatar_name=avatar_name,
        avatar_role=role,
        avatar_interests=interest_list,
        user_interests=user_interest_list,
        past_topics=past_topics,
        last_conversation_summary=last_summary,
        situation=situation,
        count=count,
    )
    
    return await starter_service.get_starters(
        request=request,
        use_ai=True,
        hour=hour,
    )


# ============================================================================
# Time-based Greetings (Simple)
# ============================================================================

@router.get("/greeting")
async def get_greeting(
    role: str = Query(..., description="Avatar role"),
    hour: Optional[int] = Query(None, description="Hour (0-23)"),
):
    """
    Get appropriate greeting for time of day and role.
    
    Simple endpoint that returns just a greeting.
    """
    
    time_of_day = starter_service.get_time_of_day(hour)
    speech_levels = get_speech_levels_for_role(role)
    speech_level = speech_levels["from_user"]
    greeting = starter_service.get_basic_greeting(time_of_day, speech_level)
    
    time_korean = {
        TimeOfDay.MORNING: "아침",
        TimeOfDay.AFTERNOON: "오후",
        TimeOfDay.EVENING: "저녁",
        TimeOfDay.NIGHT: "밤",
    }
    
    return {
        "greeting": greeting,
        "time_of_day": time_of_day.value,
        "time_korean": time_korean[time_of_day],
        "speech_level": speech_level.value,
    }
