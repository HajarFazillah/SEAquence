"""
Conversation Memory Service

Remembers past conversations between user and avatars.
Extracts and stores key information for future reference.

Features:
- Extract important facts from conversations
- Track relationship development
- Remember user preferences
- Generate context-aware callbacks
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import json

from app.services.clova_service import clova_service, Message


# ============================================================================
# Models
# ============================================================================

class MemoryType(str, Enum):
    FACT = "fact"  # 사실 (이름, 나이, 직업 등)
    PREFERENCE = "preference"  # 선호 (좋아하는 것, 싫어하는 것)
    EVENT = "event"  # 이벤트 (여행 계획, 시험 등)
    EMOTION = "emotion"  # 감정 상태 (스트레스, 기쁨 등)
    TOPIC = "topic"  # 대화 주제
    RELATIONSHIP = "relationship"  # 관계 발전


class MemoryPriority(str, Enum):
    HIGH = "high"  # 중요 (이름, 직업 등)
    MEDIUM = "medium"  # 보통 (관심사, 계획)
    LOW = "low"  # 낮음 (일시적 감정)


class Memory(BaseModel):
    """Single memory item"""
    id: str
    user_id: str
    avatar_id: str
    
    type: MemoryType
    priority: MemoryPriority
    
    content: str  # The actual memory
    context: Optional[str] = None  # When/how it was mentioned
    
    # Timestamps
    created_at: datetime
    last_referenced: Optional[datetime] = None
    expires_at: Optional[datetime] = None  # For temporary memories
    
    # Usage tracking
    reference_count: int = 0
    
    # Source
    source_message: Optional[str] = None


class ConversationSummary(BaseModel):
    """Summary of a conversation"""
    user_id: str
    avatar_id: str
    conversation_id: str
    
    date: datetime
    duration_minutes: int
    message_count: int
    
    # Summary
    main_topics: List[str]
    mood: str  # How the conversation felt
    highlights: List[str]  # Key moments
    
    # Extracted memories
    new_memories: List[Memory] = []
    
    # For next conversation
    follow_up_topics: List[str] = []


class MemoryContext(BaseModel):
    """Context from memory for conversation"""
    relevant_memories: List[Memory]
    suggested_callbacks: List[str]  # Things to mention
    relationship_summary: str
    last_conversation_summary: Optional[str] = None


# ============================================================================
# Memory Storage (In-memory for now, replace with DB later)
# ============================================================================

class MemoryStorage:
    """Simple in-memory storage (replace with Redis/PostgreSQL)"""
    
    def __init__(self):
        self.memories: Dict[str, List[Memory]] = {}  # user_avatar_key -> memories
        self.summaries: Dict[str, List[ConversationSummary]] = {}
        self._id_counter = 0
    
    def _get_key(self, user_id: str, avatar_id: str) -> str:
        return f"{user_id}:{avatar_id}"
    
    def _generate_id(self) -> str:
        self._id_counter += 1
        return f"mem_{self._id_counter}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def add_memory(self, memory: Memory) -> Memory:
        key = self._get_key(memory.user_id, memory.avatar_id)
        if key not in self.memories:
            self.memories[key] = []
        
        memory.id = self._generate_id()
        self.memories[key].append(memory)
        return memory
    
    def get_memories(
        self, 
        user_id: str, 
        avatar_id: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 20,
    ) -> List[Memory]:
        key = self._get_key(user_id, avatar_id)
        memories = self.memories.get(key, [])
        
        # Filter by type if specified
        if memory_type:
            memories = [m for m in memories if m.type == memory_type]
        
        # Filter expired
        now = datetime.now()
        memories = [m for m in memories if not m.expires_at or m.expires_at > now]
        
        # Sort by priority and recency
        memories.sort(key=lambda m: (
            0 if m.priority == MemoryPriority.HIGH else 1 if m.priority == MemoryPriority.MEDIUM else 2,
            -m.created_at.timestamp()
        ))
        
        return memories[:limit]
    
    def add_summary(self, summary: ConversationSummary):
        key = self._get_key(summary.user_id, summary.avatar_id)
        if key not in self.summaries:
            self.summaries[key] = []
        self.summaries[key].append(summary)
    
    def get_last_summary(self, user_id: str, avatar_id: str) -> Optional[ConversationSummary]:
        key = self._get_key(user_id, avatar_id)
        summaries = self.summaries.get(key, [])
        if summaries:
            return summaries[-1]
        return None
    
    def update_reference(self, memory_id: str, user_id: str, avatar_id: str):
        key = self._get_key(user_id, avatar_id)
        for m in self.memories.get(key, []):
            if m.id == memory_id:
                m.reference_count += 1
                m.last_referenced = datetime.now()
                break


# Global storage instance
memory_storage = MemoryStorage()


# ============================================================================
# Memory Extraction Service
# ============================================================================

class MemoryService:
    """Service for managing conversation memory"""
    
    def __init__(self):
        self.storage = memory_storage
    
    async def extract_memories(
        self,
        user_id: str,
        avatar_id: str,
        messages: List[Dict[str, str]],
    ) -> List[Memory]:
        """
        Extract important information from conversation to store as memories.
        
        Uses AI to identify:
        - Facts about the user
        - Preferences and interests
        - Upcoming events/plans
        - Emotional states
        - Topics discussed
        """
        
        conversation = "\n".join([
            f"{'사용자' if m['role'] == 'user' else '아바타'}: {m['content']}"
            for m in messages
        ])
        
        prompt = f"""다음 대화에서 기억해야 할 중요한 정보를 추출하세요.

## 대화 내용
{conversation}

## 추출할 정보 유형
1. **fact**: 사용자에 대한 사실 (이름, 나이, 직업, 가족 등)
2. **preference**: 좋아하는 것, 싫어하는 것
3. **event**: 계획, 예정된 일, 중요한 날짜
4. **emotion**: 현재 감정 상태, 고민
5. **topic**: 대화 주제, 관심사

## 응답 형식 (JSON)
{{
    "memories": [
        {{
            "type": "fact/preference/event/emotion/topic",
            "priority": "high/medium/low",
            "content": "기억할 내용 (한국어)",
            "context": "언제/어떻게 언급되었는지",
            "expires_days": null 또는 숫자 (임시 정보의 경우)
        }}
    ],
    "follow_up_topics": ["다음 대화에서 물어볼 수 있는 주제"]
}}

## 예시
- "제주도 여행 간다" → {{"type": "event", "content": "제주도 여행 계획 중", "expires_days": 30}}
- "고양이 두 마리 키워요" → {{"type": "fact", "content": "고양이 두 마리를 키움", "priority": "high"}}
- "요즘 취업 준비로 스트레스" → {{"type": "emotion", "content": "취업 준비 스트레스", "expires_days": 14}}

중요한 정보만 추출하세요. 너무 사소한 것은 제외합니다."""

        result = await clova_service.analyze_json(prompt, temperature=0.3, max_tokens=1024)
        
        if not result:
            return []
        
        memories = []
        now = datetime.now()
        
        for m in result.get("memories", []):
            try:
                expires_at = None
                if m.get("expires_days"):
                    expires_at = now + timedelta(days=m["expires_days"])
                
                memory = Memory(
                    id="",  # Will be set by storage
                    user_id=user_id,
                    avatar_id=avatar_id,
                    type=MemoryType(m.get("type", "topic")),
                    priority=MemoryPriority(m.get("priority", "medium")),
                    content=m.get("content", ""),
                    context=m.get("context"),
                    created_at=now,
                    expires_at=expires_at,
                )
                
                saved = self.storage.add_memory(memory)
                memories.append(saved)
                
            except (ValueError, KeyError) as e:
                print(f"Error parsing memory: {e}")
                continue
        
        return memories
    
    async def get_conversation_context(
        self,
        user_id: str,
        avatar_id: str,
        avatar_name: str,
    ) -> MemoryContext:
        """
        Get relevant memories and suggestions for starting a conversation.
        
        Returns context that can be injected into the system prompt.
        """
        
        # Get all memories
        memories = self.storage.get_memories(user_id, avatar_id, limit=15)
        
        # Get last conversation summary
        last_summary = self.storage.get_last_summary(user_id, avatar_id)
        
        if not memories and not last_summary:
            return MemoryContext(
                relevant_memories=[],
                suggested_callbacks=[],
                relationship_summary="첫 대화입니다.",
                last_conversation_summary=None,
            )
        
        # Generate callbacks using AI
        memory_text = "\n".join([
            f"- [{m.type.value}] {m.content}" + (f" (언급: {m.context})" if m.context else "")
            for m in memories
        ])
        
        last_topics = ""
        if last_summary:
            last_topics = f"마지막 대화 주제: {', '.join(last_summary.main_topics)}"
        
        prompt = f"""사용자에 대한 기억을 바탕으로 자연스러운 대화 시작 문구를 만들어주세요.

## 기억된 정보
{memory_text if memory_text else "없음"}

## {last_topics if last_topics else "이전 대화 없음"}

## 응답 형식 (JSON)
{{
    "callbacks": [
        "이전 대화를 자연스럽게 이어가는 문구 (2-3개)"
    ],
    "relationship_summary": "사용자와의 관계를 한 문장으로 요약",
    "conversation_tip": "이 대화에서 활용할 수 있는 팁"
}}

## 예시 callbacks
- "지난번에 말했던 제주도 여행은 잘 다녀왔어?"
- "요즘 취업 준비는 어떻게 돼가?"
- "고양이들은 잘 있어?"

자연스럽고 관심을 보여주는 톤으로 작성하세요."""

        result = await clova_service.analyze_json(prompt, temperature=0.6, max_tokens=400)
        
        callbacks = []
        relationship = "대화를 나눈 적이 있습니다."
        
        if result:
            callbacks = result.get("callbacks", [])
            relationship = result.get("relationship_summary", relationship)
        
        last_summary_text = None
        if last_summary:
            last_summary_text = f"{last_summary.date.strftime('%m월 %d일')}에 {', '.join(last_summary.main_topics[:3])}에 대해 이야기했습니다."
        
        return MemoryContext(
            relevant_memories=memories,
            suggested_callbacks=callbacks,
            relationship_summary=relationship,
            last_conversation_summary=last_summary_text,
        )
    
    async def summarize_conversation(
        self,
        user_id: str,
        avatar_id: str,
        conversation_id: str,
        messages: List[Dict[str, str]],
        duration_minutes: int = 0,
    ) -> ConversationSummary:
        """
        Create a summary of the conversation and extract memories.
        
        Called when conversation ends.
        """
        
        conversation = "\n".join([
            f"{'사용자' if m['role'] == 'user' else '아바타'}: {m['content']}"
            for m in messages
        ])
        
        prompt = f"""대화를 분석하고 요약해주세요.

## 대화 내용
{conversation}

## 응답 형식 (JSON)
{{
    "main_topics": ["주요 대화 주제 (2-4개)"],
    "mood": "대화 분위기 (예: 친근함, 진지함, 유쾌함)",
    "highlights": ["인상적인 순간이나 중요한 포인트 (2-3개)"],
    "follow_up_topics": ["다음 대화에서 이어갈 수 있는 주제 (2-3개)"]
}}"""

        result = await clova_service.analyze_json(prompt, temperature=0.3, max_tokens=500)
        
        # Extract memories
        memories = await self.extract_memories(user_id, avatar_id, messages)
        
        summary = ConversationSummary(
            user_id=user_id,
            avatar_id=avatar_id,
            conversation_id=conversation_id,
            date=datetime.now(),
            duration_minutes=duration_minutes,
            message_count=len(messages),
            main_topics=result.get("main_topics", []) if result else [],
            mood=result.get("mood", "보통") if result else "보통",
            highlights=result.get("highlights", []) if result else [],
            new_memories=memories,
            follow_up_topics=result.get("follow_up_topics", []) if result else [],
        )
        
        self.storage.add_summary(summary)
        
        return summary
    
    def build_memory_prompt_section(
        self,
        user_id: str,
        avatar_id: str,
    ) -> str:
        """
        Build a prompt section containing relevant memories.
        
        This can be appended to the system prompt.
        """
        
        memories = self.storage.get_memories(user_id, avatar_id, limit=10)
        
        if not memories:
            return ""
        
        sections = {
            MemoryType.FACT: [],
            MemoryType.PREFERENCE: [],
            MemoryType.EVENT: [],
            MemoryType.EMOTION: [],
            MemoryType.TOPIC: [],
        }
        
        for m in memories:
            sections[m.type].append(m.content)
        
        prompt_parts = ["\n## 사용자에 대해 기억하는 정보"]
        
        if sections[MemoryType.FACT]:
            prompt_parts.append(f"- 사실: {', '.join(sections[MemoryType.FACT])}")
        
        if sections[MemoryType.PREFERENCE]:
            prompt_parts.append(f"- 선호: {', '.join(sections[MemoryType.PREFERENCE])}")
        
        if sections[MemoryType.EVENT]:
            prompt_parts.append(f"- 계획/이벤트: {', '.join(sections[MemoryType.EVENT])}")
        
        if sections[MemoryType.EMOTION]:
            prompt_parts.append(f"- 최근 감정: {', '.join(sections[MemoryType.EMOTION])}")
        
        prompt_parts.append("\n이 정보를 자연스럽게 대화에 활용하되, 억지로 언급하지는 마세요.")
        
        return "\n".join(prompt_parts)
    
    def get_memories(
        self,
        user_id: str,
        avatar_id: str,
        memory_type: Optional[MemoryType] = None,
    ) -> List[Memory]:
        """Get memories for a user-avatar pair"""
        return self.storage.get_memories(user_id, avatar_id, memory_type)
    
    def delete_memory(self, memory_id: str, user_id: str, avatar_id: str) -> bool:
        """Delete a specific memory"""
        key = self.storage._get_key(user_id, avatar_id)
        memories = self.storage.memories.get(key, [])
        for i, m in enumerate(memories):
            if m.id == memory_id:
                memories.pop(i)
                return True
        return False
    
    def clear_memories(self, user_id: str, avatar_id: str):
        """Clear all memories for a user-avatar pair"""
        key = self.storage._get_key(user_id, avatar_id)
        self.storage.memories[key] = []
        self.storage.summaries[key] = []


# Global service instance
memory_service = MemoryService()
