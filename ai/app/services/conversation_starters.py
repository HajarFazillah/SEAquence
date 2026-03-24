"""
Smart Conversation Starters Service

Generates context-aware conversation openers based on:
1. Time of day (아침/점심/저녁/밤)
2. Avatar's interests & personality
3. Past conversations (memory)
4. User's interests
5. Relationship type
6. Situation/context
7. Speech level
8. Day of week (주말/평일)
9. Season/weather
10. Recent events
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from app.services.clova_service import clova_service, Message
from app.schemas.avatar import SpeechLevel, get_speech_levels_for_role, get_role_label


# ============================================================================
# Models
# ============================================================================

class TimeOfDay(str, Enum):
    MORNING = "morning"      # 6-11
    AFTERNOON = "afternoon"  # 12-17
    EVENING = "evening"      # 18-21
    NIGHT = "night"          # 22-5


class StarterCategory(str, Enum):
    GREETING = "greeting"           # 기본 인사
    SMALL_TALK = "small_talk"       # 일상 대화
    INTEREST = "interest"           # 관심사 기반
    MEMORY = "memory"               # 과거 대화 기반
    SITUATION = "situation"         # 상황 기반
    QUESTION = "question"           # 질문형
    COMPLIMENT = "compliment"       # 칭찬
    NEWS = "news"                   # 최근 소식


class ConversationStarter(BaseModel):
    """Single conversation starter"""
    text: str = Field(..., description="대화 시작 문장")
    category: StarterCategory = Field(..., description="카테고리")
    speech_level: SpeechLevel = Field(..., description="말투 레벨")
    follow_up_hint: Optional[str] = Field(None, description="이어서 할 수 있는 말")
    context: Optional[str] = Field(None, description="어떤 상황에서 사용")


class StarterRequest(BaseModel):
    """Request for conversation starters"""
    # Avatar info
    avatar_name: str
    avatar_role: str
    avatar_interests: List[str] = []
    avatar_personality: List[str] = []
    
    # User info
    user_name: Optional[str] = None
    user_interests: List[str] = []
    
    # Context
    situation: Optional[str] = None
    
    # Memory from past conversations
    past_topics: List[str] = []
    last_conversation_summary: Optional[str] = None
    
    # Settings
    count: int = 5  # How many starters to generate


class StarterResponse(BaseModel):
    """Response with conversation starters"""
    starters: List[ConversationStarter]
    time_of_day: TimeOfDay
    speech_level: SpeechLevel
    greeting: str  # Basic greeting for this time


# ============================================================================
# Time-based Greetings
# ============================================================================

TIME_GREETINGS = {
    TimeOfDay.MORNING: {
        SpeechLevel.FORMAL: ["안녕하십니까", "좋은 아침입니다"],
        SpeechLevel.POLITE: ["안녕하세요", "좋은 아침이에요"],
        SpeechLevel.INFORMAL: ["안녕", "좋은 아침"],
    },
    TimeOfDay.AFTERNOON: {
        SpeechLevel.FORMAL: ["안녕하십니까"],
        SpeechLevel.POLITE: ["안녕하세요"],
        SpeechLevel.INFORMAL: ["안녕", "야"],
    },
    TimeOfDay.EVENING: {
        SpeechLevel.FORMAL: ["안녕하십니까", "좋은 저녁입니다"],
        SpeechLevel.POLITE: ["안녕하세요", "좋은 저녁이에요"],
        SpeechLevel.INFORMAL: ["안녕", "야"],
    },
    TimeOfDay.NIGHT: {
        SpeechLevel.FORMAL: ["안녕하십니까", "이 시간에 안녕하십니까"],
        SpeechLevel.POLITE: ["안녕하세요", "이렇게 늦은 시간에요"],
        SpeechLevel.INFORMAL: ["안녕", "아직 안 잤어?"],
    },
}


# ============================================================================
# Template-based Starters (Fallback / Quick)
# ============================================================================

TEMPLATE_STARTERS = {
    TimeOfDay.MORNING: {
        SpeechLevel.FORMAL: [
            ("오늘 아침은 어떠십니까?", StarterCategory.GREETING),
            ("오늘 일정은 어떻게 되십니까?", StarterCategory.SMALL_TALK),
            ("좋은 하루 되시길 바랍니다.", StarterCategory.GREETING),
        ],
        SpeechLevel.POLITE: [
            ("오늘 아침은 어때요?", StarterCategory.GREETING),
            ("잘 주무셨어요?", StarterCategory.GREETING),
            ("아침 드셨어요?", StarterCategory.SMALL_TALK),
            ("오늘 뭐 할 거예요?", StarterCategory.QUESTION),
        ],
        SpeechLevel.INFORMAL: [
            ("잘 잤어?", StarterCategory.GREETING),
            ("아침 먹었어?", StarterCategory.SMALL_TALK),
            ("오늘 뭐 해?", StarterCategory.QUESTION),
            ("일찍 일어났네!", StarterCategory.COMPLIMENT),
        ],
    },
    TimeOfDay.AFTERNOON: {
        SpeechLevel.FORMAL: [
            ("점심은 드셨습니까?", StarterCategory.SMALL_TALK),
            ("오후 일정은 어떻게 되십니까?", StarterCategory.QUESTION),
        ],
        SpeechLevel.POLITE: [
            ("점심 먹었어요?", StarterCategory.SMALL_TALK),
            ("오늘 하루 어때요?", StarterCategory.GREETING),
            ("요즘 바빠요?", StarterCategory.QUESTION),
        ],
        SpeechLevel.INFORMAL: [
            ("밥 먹었어?", StarterCategory.SMALL_TALK),
            ("뭐 하고 있었어?", StarterCategory.QUESTION),
            ("오늘 어때?", StarterCategory.GREETING),
        ],
    },
    TimeOfDay.EVENING: {
        SpeechLevel.FORMAL: [
            ("오늘 하루 어떠셨습니까?", StarterCategory.GREETING),
            ("저녁은 드셨습니까?", StarterCategory.SMALL_TALK),
        ],
        SpeechLevel.POLITE: [
            ("오늘 하루 어땠어요?", StarterCategory.GREETING),
            ("저녁 먹었어요?", StarterCategory.SMALL_TALK),
            ("퇴근했어요?", StarterCategory.QUESTION),
            ("오늘 피곤해요?", StarterCategory.SMALL_TALK),
        ],
        SpeechLevel.INFORMAL: [
            ("오늘 어땠어?", StarterCategory.GREETING),
            ("저녁 먹었어?", StarterCategory.SMALL_TALK),
            ("피곤해?", StarterCategory.QUESTION),
            ("오늘 뭐 했어?", StarterCategory.QUESTION),
        ],
    },
    TimeOfDay.NIGHT: {
        SpeechLevel.FORMAL: [
            ("늦은 시간에 실례합니다.", StarterCategory.GREETING),
        ],
        SpeechLevel.POLITE: [
            ("아직 안 주무셨어요?", StarterCategory.QUESTION),
            ("늦게까지 뭐 하세요?", StarterCategory.QUESTION),
        ],
        SpeechLevel.INFORMAL: [
            ("아직 안 잤어?", StarterCategory.QUESTION),
            ("뭐 해? 잠 안 와?", StarterCategory.QUESTION),
            ("야, 안 자?", StarterCategory.GREETING),
        ],
    },
}

# Interest-based templates
INTEREST_TEMPLATES = {
    SpeechLevel.FORMAL: "최근에 {interest} 관련해서 재미있는 일이 있으셨습니까?",
    SpeechLevel.POLITE: "요즘 {interest} 어때요? 재미있는 거 있어요?",
    SpeechLevel.INFORMAL: "요즘 {interest} 어때? 뭐 재밌는 거 있어?",
}

# Memory-based templates
MEMORY_TEMPLATES = {
    SpeechLevel.FORMAL: "지난번에 말씀하신 {topic}은(는) 어떻게 되었습니까?",
    SpeechLevel.POLITE: "지난번에 얘기한 {topic}은(는) 어떻게 됐어요?",
    SpeechLevel.INFORMAL: "저번에 말한 {topic} 어떻게 됐어?",
}


# ============================================================================
# Service
# ============================================================================

class ConversationStarterService:
    """Service for generating smart conversation starters"""
    
    def get_time_of_day(self, hour: Optional[int] = None) -> TimeOfDay:
        """Get current time of day"""
        if hour is None:
            hour = datetime.now().hour
        
        if 6 <= hour < 12:
            return TimeOfDay.MORNING
        elif 12 <= hour < 18:
            return TimeOfDay.AFTERNOON
        elif 18 <= hour < 22:
            return TimeOfDay.EVENING
        else:
            return TimeOfDay.NIGHT
    
    def get_basic_greeting(
        self,
        time_of_day: TimeOfDay,
        speech_level: SpeechLevel
    ) -> str:
        """Get basic greeting for time and speech level"""
        greetings = TIME_GREETINGS.get(time_of_day, {}).get(speech_level, ["안녕하세요"])
        return greetings[0]
    
    def get_template_starters(
        self,
        time_of_day: TimeOfDay,
        speech_level: SpeechLevel,
        avatar_interests: List[str] = [],
        user_interests: List[str] = [],
        past_topics: List[str] = [],
        count: int = 5,
    ) -> List[ConversationStarter]:
        """Get template-based starters (no AI, fast)"""
        
        starters = []
        
        # 1. Time-based starters
        templates = TEMPLATE_STARTERS.get(time_of_day, {}).get(speech_level, [])
        for text, category in templates[:2]:
            starters.append(ConversationStarter(
                text=text,
                category=category,
                speech_level=speech_level,
            ))
        
        # 2. Interest-based starters
        all_interests = list(set(avatar_interests + user_interests))[:3]
        template = INTEREST_TEMPLATES.get(speech_level, INTEREST_TEMPLATES[SpeechLevel.POLITE])
        for interest in all_interests[:2]:
            starters.append(ConversationStarter(
                text=template.format(interest=interest),
                category=StarterCategory.INTEREST,
                speech_level=speech_level,
                context=f"{interest} 관심사 기반",
            ))
        
        # 3. Memory-based starters
        template = MEMORY_TEMPLATES.get(speech_level, MEMORY_TEMPLATES[SpeechLevel.POLITE])
        for topic in past_topics[:1]:
            starters.append(ConversationStarter(
                text=template.format(topic=topic),
                category=StarterCategory.MEMORY,
                speech_level=speech_level,
                context="이전 대화 기반",
            ))
        
        return starters[:count]
    
    async def generate_ai_starters(
        self,
        request: StarterRequest,
        speech_level: SpeechLevel,
        time_of_day: TimeOfDay,
    ) -> List[ConversationStarter]:
        """Generate AI-powered contextual starters using CLOVA"""
        
        prompt = self._build_starter_prompt(request, speech_level, time_of_day)
        
        result = await clova_service.analyze_json(prompt, temperature=0.8, max_tokens=1024)
        
        if not result or "starters" not in result:
            # Fallback to templates
            return self.get_template_starters(
                time_of_day=time_of_day,
                speech_level=speech_level,
                avatar_interests=request.avatar_interests,
                user_interests=request.user_interests,
                past_topics=request.past_topics,
                count=request.count,
            )
        
        starters = []
        for s in result.get("starters", []):
            try:
                starters.append(ConversationStarter(
                    text=s.get("text", ""),
                    category=StarterCategory(s.get("category", "greeting")),
                    speech_level=speech_level,
                    follow_up_hint=s.get("follow_up_hint"),
                    context=s.get("context"),
                ))
            except (ValueError, KeyError):
                continue
        
        return starters[:request.count]
    
    def _build_starter_prompt(
        self,
        request: StarterRequest,
        speech_level: SpeechLevel,
        time_of_day: TimeOfDay,
    ) -> str:
        """Build prompt for AI starter generation"""
        
        time_korean = {
            TimeOfDay.MORNING: "아침",
            TimeOfDay.AFTERNOON: "오후",
            TimeOfDay.EVENING: "저녁",
            TimeOfDay.NIGHT: "밤",
        }
        
        speech_korean = {
            SpeechLevel.FORMAL: "합쇼체 (격식체, -습니다)",
            SpeechLevel.POLITE: "해요체 (존댓말, -어요)",
            SpeechLevel.INFORMAL: "반말 (-어, -야)",
        }
        
        # Build context
        context_parts = []
        
        if request.avatar_interests:
            context_parts.append(f"- {request.avatar_name}의 관심사: {', '.join(request.avatar_interests)}")
        
        if request.avatar_personality:
            context_parts.append(f"- {request.avatar_name}의 성격: {', '.join(request.avatar_personality)}")
        
        if request.user_name:
            context_parts.append(f"- 사용자 이름: {request.user_name}")
        
        if request.user_interests:
            context_parts.append(f"- 사용자의 관심사: {', '.join(request.user_interests)}")
        
        if request.past_topics:
            context_parts.append(f"- 이전 대화 주제: {', '.join(request.past_topics)}")
        
        if request.last_conversation_summary:
            context_parts.append(f"- 마지막 대화 요약: {request.last_conversation_summary}")
        
        if request.situation:
            context_parts.append(f"- 상황: {request.situation}")
        
        context = "\n".join(context_parts) if context_parts else "(추가 정보 없음)"
        
        return f"""한국어 대화 시작 문장을 생성해주세요.

## 상황
- 시간: {time_korean[time_of_day]}
- 대화 상대: {request.avatar_name} ({get_role_label(request.avatar_role, None)})
- 말투: {speech_korean[speech_level]}

## 맥락 정보
{context}

## 요구사항
- {request.count}개의 대화 시작 문장을 생성하세요
- 모든 문장은 **{speech_korean[speech_level]}**로 작성
- 자연스럽고 실제 한국인이 사용하는 표현으로
- 다양한 카테고리로 (인사, 일상, 관심사, 질문 등)

## 카테고리
- greeting: 기본 인사
- small_talk: 일상 대화
- interest: 관심사 기반
- memory: 이전 대화 기반
- situation: 상황 기반
- question: 질문형
- compliment: 칭찬

## 응답 형식 (JSON)
{{
    "starters": [
        {{
            "text": "대화 시작 문장",
            "category": "카테고리",
            "follow_up_hint": "이어서 할 수 있는 말 (선택)",
            "context": "어떤 상황에서 사용하면 좋은지 (선택)"
        }}
    ]
}}"""
    
    async def get_starters(
        self,
        request: StarterRequest,
        use_ai: bool = True,
        hour: Optional[int] = None,
    ) -> StarterResponse:
        """
        Main method to get conversation starters.
        
        Args:
            request: Starter request with avatar/user info
            use_ai: Whether to use AI (CLOVA) for generation
            hour: Override hour for testing
        
        Returns:
            StarterResponse with starters
        """
        
        # Get time and speech level
        time_of_day = self.get_time_of_day(hour)
        speech_levels = get_speech_levels_for_role(request.avatar_role)
        speech_level = speech_levels["from_user"]
        
        # Get basic greeting
        greeting = self.get_basic_greeting(time_of_day, speech_level)
        
        # Generate starters
        if use_ai and clova_service.is_configured:
            starters = await self.generate_ai_starters(request, speech_level, time_of_day)
        else:
            starters = self.get_template_starters(
                time_of_day=time_of_day,
                speech_level=speech_level,
                avatar_interests=request.avatar_interests,
                user_interests=request.user_interests,
                past_topics=request.past_topics,
                count=request.count,
            )
        
        return StarterResponse(
            starters=starters,
            time_of_day=time_of_day,
            speech_level=speech_level,
            greeting=greeting,
        )


# Global service instance
starter_service = ConversationStarterService()
