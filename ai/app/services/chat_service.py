"""
Chat Service - Handles avatar conversations with real-time correction

Features:
- Real-time grammar, speech level, and vocabulary correction
- Inline corrections with explanations
- Encouragement and positive reinforcement
- Adaptive hints based on mistake patterns
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

from app.schemas.avatar import AvatarBase, SpeechLevel, get_speech_levels_for_role, get_role_label
from app.schemas.user import UserProfile, KoreanLevel
from app.services.clova_service import clova_service, Message
from app.services.prompt_builder import (
    build_avatar_system_prompt,
    build_speech_correction_prompt,
    build_conversation_analysis_prompt,
    build_bio_generation_prompt,
    SPEECH_LEVEL_INFO,
)


# ============================================================================
# Enums & Models
# ============================================================================

class CorrectionType(str, Enum):
    SPEECH_LEVEL = "speech_level"  # 말투 (합쇼체/해요체/반말)
    GRAMMAR = "grammar"  # 문법 오류
    SPELLING = "spelling"  # 맞춤법
    VOCABULARY = "vocabulary"  # 어휘 선택
    EXPRESSION = "expression"  # 자연스러운 표현
    HONORIFIC = "honorific"  # 존칭/호칭


class CorrectionSeverity(str, Enum):
    INFO = "info"  # 참고 (괜찮지만 더 좋은 표현)
    WARNING = "warning"  # 주의 (조금 어색함)
    ERROR = "error"  # 오류 (명확한 실수)


class InlineCorrection(BaseModel):
    """Single correction with explanation"""
    original: str = Field(..., description="원래 표현")
    corrected: str = Field(..., description="수정된 표현")
    type: CorrectionType = Field(..., description="오류 유형")
    severity: CorrectionSeverity = Field(default=CorrectionSeverity.WARNING)
    explanation: str = Field(..., description="설명")
    tip: Optional[str] = Field(None, description="학습 팁")


class RealTimeCorrection(BaseModel):
    """Real-time correction feedback for user's message"""
    original_message: str
    corrected_message: Optional[str] = None  # Full corrected version
    has_errors: bool = False
    
    corrections: List[InlineCorrection] = []
    
    # Speech level feedback
    expected_speech_level: str
    detected_speech_level: Optional[str] = None
    speech_level_correct: bool = True
    
    # Scores (0-100)
    accuracy_score: int = 100
    
    # Encouragement
    encouragement: Optional[str] = None
    streak_bonus: bool = False  # True if no mistakes for 3+ messages


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None


class ChatResponse(BaseModel):
    """Enhanced chat response with real-time correction"""
    # Avatar's response
    message: str
    
    # Real-time correction (NEW)
    correction: Optional[RealTimeCorrection] = None
    
    # Avatar mood
    mood_change: int = 0
    current_mood: int = 100  # 0-100
    mood_emoji: str = "😊"
    
    # Help
    suggestions: List[str] = []
    hint: Optional[str] = None  # Contextual hint
    
    # Stats
    correct_streak: int = 0


class ConversationAnalysis(BaseModel):
    scores: Dict[str, int]
    mistakes: List[Dict[str, str]]
    vocabulary_to_learn: List[Dict[str, str]]
    phrases_to_learn: List[Dict[str, str]]
    overall_feedback: str


# ============================================================================
# Prompts for Real-Time Correction
# ============================================================================

def build_realtime_correction_prompt(
    user_message: str,
    expected_speech_level: SpeechLevel,
    avatar_role: str,
    user_level: str = "intermediate",
) -> str:
    """Build comprehensive real-time correction prompt"""
    
    speech_info = SPEECH_LEVEL_INFO[expected_speech_level]
    
    level_guidance = {
        "beginner": "초급 학습자입니다. 쉬운 설명과 기본적인 오류만 지적하세요.",
        "intermediate": "중급 학습자입니다. 주요 오류와 자연스러운 표현을 알려주세요.",
        "advanced": "고급 학습자입니다. 미묘한 뉘앙스와 고급 표현도 피드백하세요.",
    }
    
    return f"""사용자의 한국어 메시지를 분석하여 실시간 교정 피드백을 제공하세요.

## 대화 상황
- 대화 상대: {avatar_role}
- 사용해야 할 말투: **{speech_info['name_ko']}** ({speech_info['name_en']})
- {speech_info['description']}
- 올바른 예시: {', '.join(speech_info['examples'])}

## 사용자 수준
{level_guidance.get(user_level, level_guidance['intermediate'])}

## 사용자 메시지
"{user_message}"

## 분석 항목
1. **말투 (speech_level)**: {speech_info['name_ko']}를 사용했는지
2. **문법 (grammar)**: 조사, 어미, 시제 등
3. **맞춤법 (spelling)**: 띄어쓰기, 철자
4. **어휘 (vocabulary)**: 적절한 단어 선택
5. **표현 (expression)**: 자연스러운 한국어 표현
6. **존칭 (honorific)**: 적절한 호칭 사용

## 응답 형식 (JSON)
{{
    "has_errors": true/false,
    "corrected_message": "전체 수정된 메시지 (오류 없으면 null)",
    "detected_speech_level": "formal/polite/informal",
    "speech_level_correct": true/false,
    "accuracy_score": 0-100,
    "corrections": [
        {{
            "original": "틀린 부분",
            "corrected": "올바른 표현",
            "type": "speech_level/grammar/spelling/vocabulary/expression/honorific",
            "severity": "info/warning/error",
            "explanation": "왜 틀렸는지 한국어로 설명",
            "tip": "기억하기 쉬운 팁 (선택사항)"
        }}
    ],
    "encouragement": "긍정적인 피드백 메시지 (잘한 점 언급)"
}}

## 중요
- 오류가 없으면 corrections는 빈 배열, has_errors는 false
- 잘한 점이 있으면 반드시 encouragement에 언급
- severity는 학습에 중요한 오류일수록 error
- 자연스러운 대안이 있으면 info로 제안"""


def build_contextual_hint_prompt(
    avatar: AvatarBase,
    conversation_history: List[ChatMessage],
    user_level: str,
) -> str:
    """Build prompt for contextual conversation hints"""
    
    speech_levels = get_speech_levels_for_role(avatar.role)
    speech_info = SPEECH_LEVEL_INFO[speech_levels["from_user"]]
    
    recent_messages = conversation_history[-4:] if conversation_history else []
    context = "\n".join([f"{'사용자' if m.role == 'user' else avatar.name_ko}: {m.content}" for m in recent_messages])
    
    return f"""대화 맥락을 보고 사용자에게 도움이 될 힌트를 제공하세요.

## 아바타 정보
- 이름: {avatar.name_ko}
- 관계: {get_role_label(avatar.role, None)}
- 관심사: {', '.join(avatar.interests[:3]) if avatar.interests else '다양한 주제'}

## 사용해야 할 말투
{speech_info['name_ko']}: {speech_info['description']}

## 최근 대화
{context if context else "(대화 시작)"}

## 사용자 수준
{user_level}

다음 JSON 형식으로 응답하세요:
{{
    "hint": "지금 상황에서 사용할 수 있는 자연스러운 표현 1-2개",
    "example_responses": ["응답 예시 1", "응답 예시 2", "응답 예시 3"],
    "grammar_tip": "이 상황에서 유용한 문법 포인트 (선택사항)"
}}"""


# ============================================================================
# Chat Service
# ============================================================================

class ChatService:
    """Service for managing avatar conversations with real-time correction"""
    
    def __init__(self):
        self.user_streaks: Dict[str, int] = {}  # user_id -> correct streak
        self.user_moods: Dict[str, int] = {}  # avatar_id -> current mood
    
    async def generate_response(
        self,
        avatar: AvatarBase,
        user_message: str,
        conversation_history: List[ChatMessage],
        user_profile: Optional[UserProfile] = None,
        situation: Optional[str] = None,
        user_id: str = "default",
        use_memory: bool = True,
    ) -> ChatResponse:
        """
        Generate avatar response with real-time correction.
        
        Returns:
        - Avatar's response message
        - Real-time correction feedback
        - Mood changes
        - Contextual hints
        
        Features:
        - Integrates conversation memory for context
        - Tracks vocabulary for spaced repetition
        """
        
        # Get speech level info
        speech_levels = get_speech_levels_for_role(avatar.role)
        expected_level = speech_levels["from_user"]
        user_level = user_profile.korean_level.value if user_profile and hasattr(user_profile.korean_level, 'value') else "intermediate"
        
        # 1. Real-time correction analysis (parallel with response)
        correction = await self._analyze_realtime(
            user_message=user_message,
            expected_speech_level=expected_level,
            avatar_role=get_role_label(avatar.role, None),
            user_level=user_level,
        )
        
        # 2. Build system prompt with memory context
        system_prompt = build_avatar_system_prompt(
            avatar=avatar,
            user_profile=user_profile,
            situation=situation,
        )
        
        # Add memory context if available
        if use_memory:
            try:
                from app.services.memory_service import memory_service
                avatar_id = getattr(avatar, 'id', avatar.name_ko)
                memory_section = memory_service.build_memory_prompt_section(user_id, avatar_id)
                if memory_section:
                    system_prompt += "\n" + memory_section
            except Exception as e:
                print(f"Memory integration error: {e}")
        
        history = [
            Message(role=msg.role, content=msg.content)
            for msg in conversation_history[-10:]
        ]
        
        response = await clova_service.generate_with_system_prompt(
            system_prompt=system_prompt,
            user_message=user_message,
            conversation_history=history,
            temperature=0.8,
        )
        
        # 3. Update streak
        streak = self._update_streak(user_id, correction.has_errors)
        correction.streak_bonus = streak >= 3
        
        # 4. Calculate mood
        mood_change = self._calculate_mood_change(correction)
        current_mood = self._update_mood(f"{user_id}_{avatar.name_ko}", mood_change)
        mood_emoji = self._get_mood_emoji(current_mood)
        
        # 5. Get suggestions if needed
        suggestions = []
        hint = None
        if len(user_message) < 15 or correction.has_errors:
            hint_result = await self._get_contextual_hint(
                avatar=avatar,
                conversation_history=conversation_history,
                user_level=user_level,
            )
            suggestions = hint_result.get("example_responses", [])
            hint = hint_result.get("hint")
        
        return ChatResponse(
            message=response.content,
            correction=correction,
            mood_change=mood_change,
            current_mood=current_mood,
            mood_emoji=mood_emoji,
            suggestions=suggestions,
            hint=hint,
            correct_streak=streak,
        )
    
    async def _analyze_realtime(
        self,
        user_message: str,
        expected_speech_level: SpeechLevel,
        avatar_role: str,
        user_level: str,
    ) -> RealTimeCorrection:
        """Analyze user message and provide real-time correction"""
        
        prompt = build_realtime_correction_prompt(
            user_message=user_message,
            expected_speech_level=expected_speech_level,
            avatar_role=avatar_role,
            user_level=user_level,
        )
        
        result = await clova_service.analyze_json(prompt, temperature=0.2, max_tokens=1024)
        
        if not result:
            # Fallback: no errors detected
            return RealTimeCorrection(
                original_message=user_message,
                expected_speech_level=SPEECH_LEVEL_INFO[expected_speech_level]["name_ko"],
                speech_level_correct=True,
                accuracy_score=100,
                encouragement="좋아요! 계속해서 대화해 보세요! 👍",
            )
        
        # Parse corrections
        corrections = []
        for c in result.get("corrections", []):
            try:
                corrections.append(InlineCorrection(
                    original=c.get("original", ""),
                    corrected=c.get("corrected", ""),
                    type=CorrectionType(c.get("type", "grammar")),
                    severity=CorrectionSeverity(c.get("severity", "warning")),
                    explanation=c.get("explanation", ""),
                    tip=c.get("tip"),
                ))
            except (ValueError, KeyError):
                continue
        
        return RealTimeCorrection(
            original_message=user_message,
            corrected_message=result.get("corrected_message"),
            has_errors=result.get("has_errors", False),
            corrections=corrections,
            expected_speech_level=SPEECH_LEVEL_INFO[expected_speech_level]["name_ko"],
            detected_speech_level=result.get("detected_speech_level"),
            speech_level_correct=result.get("speech_level_correct", True),
            accuracy_score=result.get("accuracy_score", 100),
            encouragement=result.get("encouragement"),
        )
    
    async def _get_contextual_hint(
        self,
        avatar: AvatarBase,
        conversation_history: List[ChatMessage],
        user_level: str,
    ) -> Dict[str, Any]:
        """Get contextual hints for the user"""
        
        prompt = build_contextual_hint_prompt(
            avatar=avatar,
            conversation_history=conversation_history,
            user_level=user_level,
        )
        
        result = await clova_service.analyze_json(prompt, temperature=0.5, max_tokens=300)
        
        if not result:
            # Fallback suggestions
            speech_levels = get_speech_levels_for_role(avatar.role)
            level = speech_levels["from_user"]
            
            if level == SpeechLevel.FORMAL:
                return {"example_responses": ["네, 알겠습니다.", "감사합니다.", "그렇군요."]}
            elif level == SpeechLevel.POLITE:
                return {"example_responses": ["그렇군요!", "더 알려주세요.", "저도 그래요."]}
            else:
                return {"example_responses": ["그래?", "진짜?", "나도!"]}
        
        return result
    
    def _update_streak(self, user_id: str, has_errors: bool) -> int:
        """Update correct answer streak"""
        if has_errors:
            self.user_streaks[user_id] = 0
        else:
            self.user_streaks[user_id] = self.user_streaks.get(user_id, 0) + 1
        return self.user_streaks[user_id]
    
    def _calculate_mood_change(self, correction: RealTimeCorrection) -> int:
        """Calculate mood change based on correction"""
        if not correction.has_errors:
            if correction.streak_bonus:
                return 8  # Streak bonus!
            return 3  # Correct
        
        # Count severity
        error_count = sum(1 for c in correction.corrections if c.severity == CorrectionSeverity.ERROR)
        warning_count = sum(1 for c in correction.corrections if c.severity == CorrectionSeverity.WARNING)
        
        if error_count >= 2:
            return -10
        elif error_count == 1:
            return -5
        elif warning_count >= 2:
            return -3
        else:
            return -1
    
    def _update_mood(self, avatar_key: str, change: int) -> int:
        """Update and return current mood"""
        current = self.user_moods.get(avatar_key, 80)
        new_mood = max(0, min(100, current + change))
        self.user_moods[avatar_key] = new_mood
        return new_mood
    
    def _get_mood_emoji(self, mood: int) -> str:
        """Get emoji for mood level"""
        if mood >= 90:
            return "😄"
        elif mood >= 70:
            return "😊"
        elif mood >= 50:
            return "😐"
        elif mood >= 30:
            return "😕"
        else:
            return "😢"
    
    async def analyze_conversation(
        self, avatar: AvatarBase, conversation_history: List[ChatMessage]
    ) -> ConversationAnalysis:
        """Analyze completed conversation"""
        speech_levels = get_speech_levels_for_role(avatar.role)
        expected_level = speech_levels["from_user"]
        
        prompt = build_conversation_analysis_prompt(
            messages=[{"role": m.role, "content": m.content} for m in conversation_history],
            avatar_name=avatar.name_ko,
            expected_speech_level=expected_level,
        )
        
        result = await clova_service.analyze_json(prompt, temperature=0.3, max_tokens=2048)
        
        if not result:
            return ConversationAnalysis(
                scores={"speech_accuracy": 80, "vocabulary": 75, "naturalness": 78},
                mistakes=[],
                vocabulary_to_learn=[],
                phrases_to_learn=[],
                overall_feedback="대화를 잘 진행하셨습니다!",
            )
        
        return ConversationAnalysis(**result)
    
    async def generate_avatar_bio(self, avatar: AvatarBase) -> str:
        """Generate AI bio for avatar"""
        prompt = build_bio_generation_prompt(avatar)
        response = await clova_service.chat(
            [Message(role="user", content=prompt)],
            temperature=0.7,
            max_tokens=500,
        )
        return response.content


# Global service instance
chat_service = ChatService()
