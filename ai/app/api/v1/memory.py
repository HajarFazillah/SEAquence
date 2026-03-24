"""
Memory API Endpoints

Conversation memory management.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.services.memory_service import (
    memory_service,
    Memory,
    MemoryType,
    MemoryContext,
    ConversationSummary,
)


router = APIRouter(prefix="/memory", tags=["memory"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ExtractMemoriesRequest(BaseModel):
    """Request to extract memories from conversation"""
    user_id: str
    avatar_id: str
    messages: List[dict]  # [{"role": "user/assistant", "content": "..."}]


class GetContextRequest(BaseModel):
    """Request for conversation context"""
    user_id: str
    avatar_id: str
    avatar_name: str


class SummarizeRequest(BaseModel):
    """Request to summarize conversation"""
    user_id: str
    avatar_id: str
    conversation_id: str
    messages: List[dict]
    duration_minutes: int = 0


class MemoryResponse(BaseModel):
    """Single memory response"""
    id: str
    type: str
    priority: str
    content: str
    context: Optional[str]
    created_at: datetime
    reference_count: int


class MemoryListResponse(BaseModel):
    """List of memories"""
    memories: List[MemoryResponse]
    total: int


class ContextResponse(BaseModel):
    """Conversation context response"""
    suggested_callbacks: List[str]
    relationship_summary: str
    last_conversation_summary: Optional[str]
    memory_count: int


class SummaryResponse(BaseModel):
    """Conversation summary response"""
    conversation_id: str
    date: datetime
    duration_minutes: int
    message_count: int
    main_topics: List[str]
    mood: str
    highlights: List[str]
    follow_up_topics: List[str]
    new_memories_count: int


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/extract", response_model=MemoryListResponse)
async def extract_memories(request: ExtractMemoriesRequest):
    """
    Extract and store memories from a conversation.
    
    Analyzes the conversation to identify:
    - Facts about the user
    - Preferences
    - Upcoming events/plans
    - Emotional states
    """
    try:
        memories = await memory_service.extract_memories(
            user_id=request.user_id,
            avatar_id=request.avatar_id,
            messages=request.messages,
        )
        
        return MemoryListResponse(
            memories=[
                MemoryResponse(
                    id=m.id,
                    type=m.type.value,
                    priority=m.priority.value,
                    content=m.content,
                    context=m.context,
                    created_at=m.created_at,
                    reference_count=m.reference_count,
                )
                for m in memories
            ],
            total=len(memories),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context", response_model=ContextResponse)
async def get_conversation_context(request: GetContextRequest):
    """
    Get context for starting a conversation.
    
    Returns:
    - Suggested callbacks to previous conversations
    - Relationship summary
    - Last conversation summary
    """
    try:
        context = await memory_service.get_conversation_context(
            user_id=request.user_id,
            avatar_id=request.avatar_id,
            avatar_name=request.avatar_name,
        )
        
        return ContextResponse(
            suggested_callbacks=context.suggested_callbacks,
            relationship_summary=context.relationship_summary,
            last_conversation_summary=context.last_conversation_summary,
            memory_count=len(context.relevant_memories),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize", response_model=SummaryResponse)
async def summarize_conversation(request: SummarizeRequest):
    """
    Summarize a completed conversation.
    
    Creates a summary and extracts memories for future reference.
    Call this when a conversation ends.
    """
    try:
        summary = await memory_service.summarize_conversation(
            user_id=request.user_id,
            avatar_id=request.avatar_id,
            conversation_id=request.conversation_id,
            messages=request.messages,
            duration_minutes=request.duration_minutes,
        )
        
        return SummaryResponse(
            conversation_id=summary.conversation_id,
            date=summary.date,
            duration_minutes=summary.duration_minutes,
            message_count=summary.message_count,
            main_topics=summary.main_topics,
            mood=summary.mood,
            highlights=summary.highlights,
            follow_up_topics=summary.follow_up_topics,
            new_memories_count=len(summary.new_memories),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/{avatar_id}", response_model=MemoryListResponse)
async def get_memories(
    user_id: str,
    avatar_id: str,
    memory_type: Optional[str] = None,
):
    """
    Get all memories for a user-avatar pair.
    
    Optionally filter by memory type:
    - fact: 사실
    - preference: 선호
    - event: 이벤트
    - emotion: 감정
    - topic: 주제
    """
    try:
        type_filter = None
        if memory_type:
            type_filter = MemoryType(memory_type)
        
        memories = memory_service.get_memories(
            user_id=user_id,
            avatar_id=avatar_id,
            memory_type=type_filter,
        )
        
        return MemoryListResponse(
            memories=[
                MemoryResponse(
                    id=m.id,
                    type=m.type.value,
                    priority=m.priority.value,
                    content=m.content,
                    context=m.context,
                    created_at=m.created_at,
                    reference_count=m.reference_count,
                )
                for m in memories
            ],
            total=len(memories),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}/{avatar_id}/{memory_id}")
async def delete_memory(user_id: str, avatar_id: str, memory_id: str):
    """Delete a specific memory"""
    success = memory_service.delete_memory(memory_id, user_id, avatar_id)
    if success:
        return {"status": "deleted", "memory_id": memory_id}
    raise HTTPException(status_code=404, detail="Memory not found")


@router.delete("/{user_id}/{avatar_id}")
async def clear_memories(user_id: str, avatar_id: str):
    """Clear all memories for a user-avatar pair"""
    memory_service.clear_memories(user_id, avatar_id)
    return {"status": "cleared", "user_id": user_id, "avatar_id": avatar_id}


class PromptSectionResponse(BaseModel):
    """Memory section for system prompt"""
    prompt_section: str
    memory_count: int


@router.get("/{user_id}/{avatar_id}/prompt-section", response_model=PromptSectionResponse)
async def get_memory_prompt_section(user_id: str, avatar_id: str):
    """
    Get memory section to append to system prompt.
    
    Returns formatted text that can be added to the avatar's system prompt
    to give it context about the user.
    """
    section = memory_service.build_memory_prompt_section(user_id, avatar_id)
    memories = memory_service.get_memories(user_id, avatar_id)
    
    return PromptSectionResponse(
        prompt_section=section,
        memory_count=len(memories),
    )
