"""
Chat Service - Handles avatar conversations with real-time correction
Features:
- Real-time grammar, speech level, and vocabulary correction
- Inline corrections with explanations
- Encouragement and positive reinforcement
- Adaptive hints based on mistake patterns
- Mood-based avatar response style
- Hybrid speech level detection: CLOVA + rule-based verification
- info-level corrections excluded from has_errors
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
    SPEECH_LEVEL = "speech_level"
    GRAMMAR      = "grammar"
    SPELLING     = "spelling"
    VOCABULARY   = "vocabulary"
    EXPRESSION   = "expression"
    HONORIFIC    = "honorific"


class CorrectionSeverity(str, Enum):
    INFO    = "info"
    WARNING = "warning"
    ERROR   = "error"


class InlineCorrection(BaseModel):
    original:    str                = Field(..., description="원래 표현")
    corrected:   str                = Field(..., description="수정된 표현")
    type:        CorrectionType     = Field(..., description="오류 유형")
    severity:    CorrectionSeverity = Field(default=CorrectionSeverity.WARNING)
    explanation: str                = Field(..., description="설명")
    tip:         Optional[str]      = Field(None, description="학습 팁")


class RealTimeCorrection(BaseModel):
    original_message:  str
    corrected_message: Optional[str] = None
    has_errors:        bool = False
    corrections:       List[InlineCorrection] = []

    expected_speech_level: str
    detected_speech_level: Optional[str] = None
    speech_level_correct:  bool = True

    accuracy_score: int           = 100
    encouragement:  Optional[str] = None
    streak_bonus:   bool          = False


class ChatMessage(BaseModel):
    role:      str
    content:   str
    timestamp: Optional[str] = None


class ChatResponse(BaseModel):
    message:    str
    correction: Optional[RealTimeCorrection] = None

    mood_change:  int = 0
    current_mood: int = 100
    mood_emoji:   str = "😊"

    suggestions:    List[str]    = []
    hint:           Optional[str] = None
    correct_streak: int           = 0


class ConversationAnalysis(BaseModel):
    scores:              Dict[str, int]
    mistakes:            List[Dict[str, str]]
    vocabulary_to_learn: List[Dict[str, str]]
    phrases_to_learn:    List[Dict[str, str]]
    overall_feedback:    str


# ============================================================================
# Correction prompt
# ============================================================================

def build_realtime_correction_prompt(
    user_message:          str,
    expected_speech_level: SpeechLevel,
    avatar_role:           str,
    user_level:            str = "intermediate",
) -> str:
    speech_info = SPEECH_LEVEL_INFO[expected_speech_level]
    level_guidance = {
        "beginner":     "초급 학습자입니다. 쉬운 설명과 기본적인 오류만 지적하세요.",
        "intermediate": "중급 학습자입니다. 주요 오류와 자연스러운 표현을 알려주세요.",
        "advanced":     "고급 학습자입니다. 미묘한 뉘앙스와 고급 표현도 피드백하세요.",
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
    "detected_speech_level": "formal / polite / informal 중 하나",
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

## 절대 규칙
- detected_speech_level 은 반드시 formal / polite / informal 세 값 중 하나만 사용하세요
- detected_speech_level 은 절대 null 이 되면 안 됩니다. 짧은 문장이어도 반드시 판단하세요
- severity 기준: error = 명확한 실수 / warning = 어색함 / info = 더 좋은 표현 제안
- 단순히 더 자연스러운 표현 제안은 info, 실제 문법/말투 오류는 error/warning 사용
- 오류가 없으면 corrections는 빈 배열, has_errors는 false
- 잘한 점이 있으면 반드시 encouragement에 언급"""


def build_contextual_hint_prompt(
    avatar:               AvatarBase,
    conversation_history: List[ChatMessage],
    user_level:           str,
) -> str:
    speech_levels = get_speech_levels_for_role(avatar.role)
    speech_info   = SPEECH_LEVEL_INFO[speech_levels["from_user"]]
    recent        = conversation_history[-4:] if conversation_history else []
    context       = "\n".join([
        f"{'사용자' if m.role == 'user' else avatar.name_ko}: {m.content}"
        for m in recent
    ])

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
# 말투 레벨 정규화 맵
# ============================================================================
LEVEL_MAP = {
    # 반말
    "반말":             "informal", "informal":          "informal",
    "비격식":           "informal", "casual":            "informal",
    "편한말":           "informal", "편한 말":           "informal",

    # 해요체
    "해요체":           "polite",   "polite":            "polite",
    "존댓말":           "polite",   "공손한 말투":       "polite",
    "공손한말투":       "polite",   "공손":              "polite",
    "공손한":           "polite",   "경어":              "polite",
    "정중한 말투":      "polite",   "정중한말투":        "polite",
    "정중":             "polite",   "높임말":            "polite",
    "높임":             "polite",   "존대":              "polite",

    # 합쇼체
    "합쇼체":           "formal",   "formal":            "formal",
    "격식체":           "formal",   "격식":              "formal",
    "격식적":           "formal",   "공식적":            "formal",
}

# ── 규칙 기반 어미 목록 ─────────────────────────────────────────────────────
_FORMAL_ENDINGS   = ["습니다", "습니까", "십니까", "겠습니다", "십시오", "으십시오"]
_POLITE_ENDINGS   = ["어요", "아요", "이에요", "예요", "해요", "세요",
                     "네요", "군요", "죠", "나요", "가요", "래요",
                     "데요", "을게요", "ㄹ게요", "겠어요"]
_INFORMAL_ENDINGS = ["이야", "야", "이어", "어", "아", "지", "니",
                     "냐", "거야", "잖아", "이잖아", "구나", "군",
                     "을게", "ㄹ게", "자", "해", "래", "네"]


def verify_with_rules(text: str, clova_detected: str) -> str:
    """
    CLOVA 감지 결과를 어미 규칙으로 검증.
    어미로 명확히 판단되면 규칙 결과 사용,
    판단 불가하면 CLOVA 결과 신뢰.
    """
    text = text.strip()

    for e in _FORMAL_ENDINGS:
        if text.endswith(e):
            return "formal"
    for e in _POLITE_ENDINGS:
        if text.endswith(e):
            return "polite"
    for e in _INFORMAL_ENDINGS:
        if text.endswith(e):
            return "informal"

    # 판단 불가 → CLOVA 신뢰
    return clova_detected


# ============================================================================
# Chat Service
# ============================================================================

class ChatService:

    def __init__(self):
        self.user_streaks: Dict[str, int] = {}
        self.user_moods:   Dict[str, int] = {}

    async def generate_response(
        self,
        avatar:               AvatarBase,
        user_message:         str,
        conversation_history: List[ChatMessage],
        user_profile:         Optional[UserProfile] = None,
        situation:            Optional[str]         = None,
        user_id:              str                   = "default",
        use_memory:           bool                  = True,
    ) -> ChatResponse:

        speech_levels  = get_speech_levels_for_role(avatar.role)
        expected_level = speech_levels["from_user"]
        user_level     = (
            user_profile.korean_level.value
            if user_profile and hasattr(user_profile.korean_level, "value")
            else "intermediate"
        )

        # 1. 실시간 교정 분석
        correction = await self._analyze_realtime(
            user_message=user_message,
            expected_speech_level=expected_level,
            avatar_role=get_role_label(avatar.role, None),
            user_level=user_level,
        )

        # 2. 현재 기분 조회
        mood_key     = f"{user_id}_{avatar.name_ko}"
        current_mood = self.user_moods.get(mood_key, 80)

        # 3. 시스템 프롬프트 구성
        system_prompt = build_avatar_system_prompt(
            avatar=avatar,
            user_profile=user_profile,
            situation=situation,
            current_mood=current_mood,
            is_level_correct=correction.speech_level_correct,
        )

        # 메모리 주입
        if use_memory:
            try:
                from app.services.memory_service import memory_service
                avatar_id      = getattr(avatar, "id", avatar.name_ko)
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

        # 4. 스트릭 업데이트
        streak                  = self._update_streak(user_id, correction.has_errors)
        correction.streak_bonus = streak >= 3

        # 5. 기분 업데이트
        mood_change = self._calculate_mood_change(correction)
        new_mood    = self._update_mood(mood_key, mood_change)
        mood_emoji  = self._get_mood_emoji(new_mood)

        # 6. 힌트/제안
        suggestions = []
        hint        = None
        if len(user_message) < 15 or correction.has_errors:
            hint_result = await self._get_contextual_hint(
                avatar=avatar,
                conversation_history=conversation_history,
                user_level=user_level,
            )
            suggestions = hint_result.get("example_responses", [])
            hint        = hint_result.get("hint")

        return ChatResponse(
            message=response.content,
            correction=correction,
            mood_change=mood_change,
            current_mood=new_mood,
            mood_emoji=mood_emoji,
            suggestions=suggestions,
            hint=hint,
            correct_streak=streak,
        )

    async def _analyze_realtime(
        self,
        user_message:          str,
        expected_speech_level: SpeechLevel,
        avatar_role:           str,
        user_level:            str,
    ) -> RealTimeCorrection:

        prompt = build_realtime_correction_prompt(
            user_message=user_message,
            expected_speech_level=expected_speech_level,
            avatar_role=avatar_role,
            user_level=user_level,
        )

        result = await clova_service.analyze_json(prompt, temperature=0.2, max_tokens=1024)

        if not result:
            return RealTimeCorrection(
                original_message=user_message,
                expected_speech_level=SPEECH_LEVEL_INFO[expected_speech_level]["name_ko"],
                speech_level_correct=True,
                accuracy_score=100,
                encouragement="좋아요! 계속해서 대화해 보세요! 👍",
            )

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

        # ── 하이브리드 발화 레벨 감지 ──────────────────────────────────────────
        # 1단계: CLOVA 결과 정규화
        clova_raw  = (result.get("detected_speech_level") or "").strip().lower()
        clova_norm = LEVEL_MAP.get(clova_raw, clova_raw)

        # 2단계: 규칙 기반 어미 검증 — CLOVA가 틀렸으면 보정
        detected_norm = verify_with_rules(user_message, clova_norm)

        # 3단계: 기대 레벨 정규화
        expected_norm = LEVEL_MAP.get(
            SPEECH_LEVEL_INFO[expected_speech_level]["name_ko"].lower(),
            expected_speech_level.value.lower(),
        )

        # 빈 detected = 판단 보류 (단답형)
        is_level_correct = (detected_norm == expected_norm) or (detected_norm == "")

        # ── has_errors 재계산 — info 레벨은 오류로 카운트하지 않음 ─────────────
        real_errors = [
            c for c in corrections
            if c.severity in (CorrectionSeverity.ERROR, CorrectionSeverity.WARNING)
        ]
        has_errors     = (len(real_errors) > 0) or not is_level_correct
        accuracy_score = result.get("accuracy_score", 100)

        # info 만 있는 경우 accuracy_score 조정 (100점 유지)
        if not has_errors and corrections:
            accuracy_score = max(accuracy_score, 90)

        if not is_level_correct:
            accuracy_score = min(accuracy_score, 55)
            expected_name  = SPEECH_LEVEL_INFO[expected_speech_level]["name_ko"]
            example        = SPEECH_LEVEL_INFO[expected_speech_level]["examples"][0]
            corrections.insert(0, InlineCorrection(
                original=user_message,
                corrected=result.get("corrected_message") or user_message,
                type=CorrectionType.SPEECH_LEVEL,
                severity=CorrectionSeverity.ERROR,
                explanation=f"{expected_name}를 사용해야 합니다. (감지된 말투: {detected_norm})",
                tip=f"예시: {example}",
            ))

        return RealTimeCorrection(
            original_message=user_message,
            corrected_message=result.get("corrected_message"),
            has_errors=has_errors,
            corrections=corrections,
            expected_speech_level=SPEECH_LEVEL_INFO[expected_speech_level]["name_ko"],
            detected_speech_level=detected_norm or clova_raw,
            speech_level_correct=is_level_correct,
            accuracy_score=accuracy_score,
            encouragement=result.get("encouragement"),
        )

    async def _get_contextual_hint(
        self,
        avatar:               AvatarBase,
        conversation_history: List[ChatMessage],
        user_level:           str,
    ) -> Dict[str, Any]:

        prompt = build_contextual_hint_prompt(
            avatar=avatar,
            conversation_history=conversation_history,
            user_level=user_level,
        )

        result = await clova_service.analyze_json(prompt, temperature=0.5, max_tokens=300)

        if not result:
            speech_levels = get_speech_levels_for_role(avatar.role)
            level         = speech_levels["from_user"]
            if level == SpeechLevel.FORMAL:
                return {"example_responses": ["네, 알겠습니다.", "감사합니다.", "그렇군요."]}
            elif level == SpeechLevel.POLITE:
                return {"example_responses": ["그렇군요!", "더 알려주세요.", "저도 그래요."]}
            else:
                return {"example_responses": ["그래?", "진짜?", "나도!"]}

        return result

    def _update_streak(self, user_id: str, has_errors: bool) -> int:
        if has_errors:
            self.user_streaks[user_id] = 0
        else:
            self.user_streaks[user_id] = self.user_streaks.get(user_id, 0) + 1
        return self.user_streaks[user_id]

    def _calculate_mood_change(self, correction: RealTimeCorrection) -> int:
        if not correction.has_errors:
            return 8 if correction.streak_bonus else 3

        error_count   = sum(1 for c in correction.corrections
                           if c.severity == CorrectionSeverity.ERROR)
        warning_count = sum(1 for c in correction.corrections
                           if c.severity == CorrectionSeverity.WARNING)

        if error_count >= 2:     return -10
        elif error_count == 1:   return -5
        elif warning_count >= 2: return -3
        else:                    return -1

    def _update_mood(self, avatar_key: str, change: int) -> int:
        current  = self.user_moods.get(avatar_key, 80)
        new_mood = max(0, min(100, current + change))
        self.user_moods[avatar_key] = new_mood
        return new_mood

    def _get_mood_emoji(self, mood: int) -> str:
        if mood >= 90:   return "😄"
        elif mood >= 70: return "😊"
        elif mood >= 50: return "😐"
        elif mood >= 30: return "😕"
        else:            return "😢"

    async def analyze_conversation(
        self,
        avatar:               AvatarBase,
        conversation_history: List[ChatMessage],
    ) -> ConversationAnalysis:
        speech_levels  = get_speech_levels_for_role(avatar.role)
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
        prompt   = build_bio_generation_prompt(avatar)
        response = await clova_service.chat(
            [Message(role="user", content=prompt)],
            temperature=0.7,
            max_tokens=500,
        )
        return response.content


# Global service instance
chat_service = ChatService()