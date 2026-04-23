"""
Chat Service - Handles avatar conversations with real-time correction
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


class NaturalAlternative(BaseModel):
    expression:  str = Field(..., description="더 자연스러운 표현")
    explanation: str = Field(..., description="왜 더 자연스러운지")


class RealTimeCorrection(BaseModel):
    original_message:  str
    corrected_message: Optional[str] = None
    has_errors:        bool = False
    corrections:       List[InlineCorrection] = []
    natural_alternatives: List[NaturalAlternative] = []

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
# 단답형 → 자연스러운 대안 맵
# ============================================================================

_SHORT_ALTERNATIVES: Dict[str, Dict[str, List[Dict[str, str]]]] = {
    "네": {
        "polite":   [
            {"expression": "네, 맞아요!", "explanation": "더 활기차고 자연스러운 동의 표현이에요"},
            {"expression": "네, 그렇군요!", "explanation": "상대방 말에 공감할 때 자주 써요"},
        ],
        "formal":   [
            {"expression": "네, 맞습니다.", "explanation": "격식 있는 동의 표현이에요"},
            {"expression": "그렇습니다.", "explanation": "격식체에서 자주 쓰는 동의 표현이에요"},
        ],
        "informal": [
            {"expression": "어, 맞아!", "explanation": "친한 사이에서 자연스러운 동의예요"},
            {"expression": "응, 그렇지!", "explanation": "캐주얼하게 동의할 때 써요"},
        ],
    },
    "넵": {
        "polite":   [
            {"expression": "네, 알겠어요!", "explanation": "더 적극적이고 자연스러운 대답이에요"},
            {"expression": "네, 그렇군요.", "explanation": "'넵'보다 조금 더 부드러운 표현이에요"},
        ],
        "formal":   [{"expression": "네, 알겠습니다.", "explanation": "격식 있는 상황에서 쓰는 표현이에요"}],
        "informal": [{"expression": "어, 알았어!", "explanation": "친한 사이에서 자연스러운 대답이에요"}],
    },
    "응": {
        "informal": [
            {"expression": "어, 맞아!", "explanation": "더 활기차고 자연스러운 동의예요"},
            {"expression": "그렇지!", "explanation": "확실히 동의할 때 쓰는 표현이에요"},
        ],
        "polite": [{"expression": "네, 그래요!", "explanation": "반말 '응' 대신 해요체로 바꾸면 이렇게요"}],
    },
    "어": {
        "informal": [
            {"expression": "맞아, 그렇네!", "explanation": "더 생동감 있는 반응이에요"},
            {"expression": "오, 그래?", "explanation": "관심과 놀라움을 표현할 때 써요"},
        ],
        "polite": [{"expression": "아, 그렇군요!", "explanation": "'어' 대신 해요체로 자연스럽게 반응하는 표현이에요"}],
    },
    "그래": {
        "informal": [
            {"expression": "맞아, 그렇지!", "explanation": "더 확신을 담은 동의 표현이에요"},
            {"expression": "어, 그러네!", "explanation": "가볍게 동의할 때 자연스러운 표현이에요"},
        ],
        "polite": [{"expression": "그렇군요, 맞아요!", "explanation": "해요체로 더 자연스럽게 바꾼 표현이에요"}],
    },
    "아니": {
        "informal": [
            {"expression": "아니, 그건 좀 달라!", "explanation": "더 구체적으로 반대 의견을 표현할 수 있어요"},
            {"expression": "음, 그건 아닌 것 같아.", "explanation": "부드럽게 반대할 때 쓰는 표현이에요"},
        ],
        "polite": [{"expression": "아니요, 그건 좀 달라요.", "explanation": "해요체로 정중하게 반대하는 표현이에요"}],
    },
    "아니요": {
        "polite": [
            {"expression": "아니요, 그렇지 않아요.", "explanation": "더 명확하게 부정하는 표현이에요"},
            {"expression": "음, 그건 좀 아닌 것 같아요.", "explanation": "부드럽게 반대할 때 써요"},
        ],
        "formal": [{"expression": "아닙니다, 그렇지 않습니다.", "explanation": "격식 있게 부정하는 표현이에요"}],
    },
    "맞아": {
        "informal": [
            {"expression": "맞아, 진짜 그렇지!", "explanation": "더 강하게 동의할 때 써요"},
            {"expression": "어, 완전 동감이야!", "explanation": "강한 공감을 표현할 때 자연스러운 표현이에요"},
        ],
        "polite": [{"expression": "맞아요, 정말 그렇네요!", "explanation": "해요체로 더 자연스럽게 동의하는 표현이에요"}],
    },
}


# ============================================================================
# ── 핵심 수정: context-aware correction prompt ─────────────────────────────
# ============================================================================

def build_realtime_correction_prompt(
    user_message:          str,
    expected_speech_level: SpeechLevel,
    avatar_role:           str,
    user_level:            str = "intermediate",
    conversation_history:  List[ChatMessage] = [],   # ← 추가
) -> str:
    speech_info = SPEECH_LEVEL_INFO[expected_speech_level]
    level_guidance = {
        "beginner":     "초급 학습자입니다. 쉬운 설명과 기본적인 오류만 지적하세요.",
        "intermediate": "중급 학습자입니다. 주요 오류와 자연스러운 표현을 알려주세요.",
        "advanced":     "고급 학습자입니다. 미묘한 뉘앙스와 고급 표현도 피드백하세요.",
    }

    # ── 최근 대화 3턴 추출 ────────────────────────────────────────────────
    recent = conversation_history[-3:] if conversation_history else []
    context_lines = "\n".join([
        f"{'사용자' if m.role == 'user' else '아바타'}: {m.content}"
        for m in recent
    ])
    context_section = f"""
## 최근 대화 맥락 (교정 시 반드시 참고하세요)
{context_lines if context_lines else "(대화 시작)"}

⚠️ 중요: 위 대화 맥락을 반드시 고려하세요.
- 앞 대화에서 나온 주제나 단어를 사용하는 것은 자연스러운 표현입니다.
- 문맥상 자연스러운 표현은 오류로 처리하지 마세요.
- 예: 앞서 봄축제 얘기를 했다면 "봄축제야"는 정상적인 표현입니다.
""" if recent else ""

    return f"""사용자의 한국어 메시지를 분석하여 실시간 교정 피드백을 제공하세요.

## 대화 상황
- 대화 상대: {avatar_role}
- 사용해야 할 말투: **{speech_info['name_ko']}** ({speech_info['name_en']})
- {speech_info['description']}
- 올바른 예시: {', '.join(speech_info['examples'])}

## 사용자 수준
{level_guidance.get(user_level, level_guidance['intermediate'])}
{context_section}
## 분석할 사용자 메시지
"{user_message}"

## 응답 형식 (JSON)
{{
    "has_errors": true/false,
    "corrected_message": "반드시 {speech_info['name_ko']}로 수정된 전체 메시지. 오류 없으면 null",
    "detected_speech_level": "formal / polite / informal 중 하나",
    "speech_level_correct": true/false,
    "accuracy_score": 0-100,
    "corrections": [
        {{
            "original": "반드시 사용자 메시지에 실제로 존재하는 표현만",
            "corrected": "올바른 {speech_info['name_ko']} 표현",
            "type": "speech_level/grammar/spelling/vocabulary/expression/honorific",
            "severity": "info/warning/error",
            "explanation": "왜 틀렸는지 한국어로 설명",
            "tip": "기억하기 쉬운 팁 (선택사항)"
        }}
    ],
    "natural_alternatives": [
        {{
            "expression": "이렇게도 말할 수 있어요 — 더 자연스러운 {speech_info['name_ko']} 표현",
            "explanation": "왜 이 표현이 더 자연스러운지 한 줄로"
        }}
    ],
    "encouragement": "잘한 점을 언급한 긍정적인 피드백 (1문장)"
}}

## natural_alternatives 규칙
- 오류가 없어도 반드시 1~2개 제안하세요
- 같은 의미지만 더 자연스럽고 세련된 {speech_info['name_ko']} 표현으로
- 원어민이 실제로 쓰는 표현으로
- 대화 맥락에 맞는 표현을 제안하세요

## 절대 규칙
- detected_speech_level 은 formal / polite / informal 중 하나 (null 불가)
- corrected_message 는 반드시 {speech_info['name_ko']} 말투로
- corrections original 은 사용자 메시지에 실제 존재하는 표현만
- 맥락상 자연스러운 표현은 오류 처리 금지
- 오류 없으면 corrections 빈 배열, has_errors false"""


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
    "반말":             "informal", "informal":          "informal",
    "비격식":           "informal", "casual":            "informal",
    "편한말":           "informal", "편한 말":           "informal",
    "해요체":           "polite",   "polite":            "polite",
    "존댓말":           "polite",   "공손한 말투":       "polite",
    "공손한말투":       "polite",   "공손":              "polite",
    "공손한":           "polite",   "경어":              "polite",
    "정중한 말투":      "polite",   "정중한말투":        "polite",
    "정중":             "polite",   "높임말":            "polite",
    "높임":             "polite",   "존대":              "polite",
    "합쇼체":           "formal",   "formal":            "formal",
    "격식체":           "formal",   "격식":              "formal",
    "격식적":           "formal",   "공식적":            "formal",
}

_FORMAL_ENDINGS   = ["습니다", "습니까", "십니까", "겠습니다", "십시오", "으십시오"]
_POLITE_ENDINGS   = ["어요", "아요", "이에요", "예요", "해요", "세요",
                     "네요", "군요", "죠", "나요", "가요", "래요",
                     "데요", "을게요", "ㄹ게요", "겠어요"]
_INFORMAL_ENDINGS = ["이야", "야", "이어", "어", "아", "지", "니",
                     "냐", "거야", "잖아", "이잖아", "구나", "군",
                     "을게", "ㄹ게", "자", "해", "래", "네"]

_SHORT_RESPONSES = {
    "응", "어", "네", "넵", "넹", "예", "아니", "아니요", "ㅇ", "ㅇㅇ",
    "ㄴㄴ", "ㄴ", "그래", "응응", "오", "아", "음", "흠", "헐", "와",
    "오케이", "ok", "OK", "ㅋㅋ", "ㅎㅎ", "맞아", "맞아요", "그렇구나",
}

_INFORMAL_TO_POLITE = {
    "이야": "이에요", "거야": "거예요", "잖아": "잖아요", "구나": "군요",
    "거든": "거든요", "지만": "지만요", "는데": "는데요", "ㄴ데": "ㄴ데요",
    "을게": "을게요", "ㄹ게": "ㄹ게요", "을래": "을래요", "ㄹ래": "ㄹ래요",
    "을까": "을까요", "ㄹ까": "ㄹ까요", "싶음": "싶어요", "없음": "없어요",
    "있음": "있어요", "함": "해요", "임": "이에요", "음": "어요",
    "야": "요", "해": "해요", "어": "어요", "아": "아요",
    "지": "지요", "군": "군요", "네": "네요", "래": "래요", "자": "시죠",
}

_INFORMAL_TO_FORMAL = {
    "이야": "입니다", "거야": "겁니다", "싶음": "싶습니다",
    "없음": "없습니다", "있음": "있습니다", "함": "합니다",
    "임": "입니다", "음": "습니다", "야": "습니다",
    "해": "합니다", "어": "습니다", "아": "습니다",
    "지": "지요", "군": "군요", "네": "네요",
}


def simple_convert_to_level(text: str, target: str) -> Optional[str]:
    text  = text.strip()
    table = _INFORMAL_TO_POLITE if target == "polite" else _INFORMAL_TO_FORMAL
    for informal, formal in sorted(table.items(), key=lambda x: -len(x[0])):
        if text.endswith(informal):
            return text[: -len(informal)] + formal
    return None


def verify_with_rules(text: str, clova_detected: str) -> str:
    text = text.strip()
    for e in _FORMAL_ENDINGS:
        if text.endswith(e): return "formal"
    for e in _POLITE_ENDINGS:
        if text.endswith(e): return "polite"
    for e in _INFORMAL_ENDINGS:
        if text.endswith(e): return "informal"
    return clova_detected


def get_short_response_alternatives(
    text: str,
    expected_norm: str,
) -> List[NaturalAlternative]:
    text     = text.strip()
    alts_map = _SHORT_ALTERNATIVES.get(text, {})
    alts     = alts_map.get(expected_norm, [])
    if not alts:
        for level in ["polite", "informal", "formal"]:
            alts = alts_map.get(level, [])
            if alts: break
    return [
        NaturalAlternative(expression=a["expression"], explanation=a["explanation"])
        for a in alts
    ]


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

        # ── 핵심: conversation_history 전달 ───────────────────────────────
        correction = await self._analyze_realtime(
            user_message=user_message,
            expected_speech_level=expected_level,
            avatar_role=get_role_label(avatar.role, None),
            user_level=user_level,
            conversation_history=conversation_history,   # ← 추가
        )

        mood_key     = f"{user_id}_{avatar.name_ko}"
        current_mood = self.user_moods.get(mood_key, 80)

        system_prompt = build_avatar_system_prompt(
            avatar=avatar,
            user_profile=user_profile,
            situation=situation,
            current_mood=current_mood,
            is_level_correct=correction.speech_level_correct,
        )

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

        streak                  = self._update_streak(user_id, correction.has_errors)
        correction.streak_bonus = streak >= 3

        mood_change = self._calculate_mood_change(correction)
        new_mood    = self._update_mood(mood_key, mood_change)
        mood_emoji  = self._get_mood_emoji(new_mood)

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
        conversation_history:  List[ChatMessage] = [],   # ← 추가
    ) -> RealTimeCorrection:

        msg_stripped  = user_message.strip()
        expected_norm = LEVEL_MAP.get(
            SPEECH_LEVEL_INFO[expected_speech_level]["name_ko"].lower(),
            expected_speech_level.value.lower(),
        )

        # ── 단답형 스킵 ──────────────────────────────────────────────────────
        is_short = (
            len(msg_stripped) <= 3
            or msg_stripped in _SHORT_RESPONSES
            or msg_stripped.lower() in _SHORT_RESPONSES
        )
        if is_short:
            detected_norm    = verify_with_rules(msg_stripped, "")
            is_level_correct = (detected_norm == expected_norm) or (detected_norm == "")
            alternatives     = get_short_response_alternatives(msg_stripped, expected_norm)
            return RealTimeCorrection(
                original_message=user_message,
                expected_speech_level=SPEECH_LEVEL_INFO[expected_speech_level]["name_ko"],
                detected_speech_level=detected_norm or expected_norm,
                speech_level_correct=is_level_correct,
                accuracy_score=100 if is_level_correct else 60,
                natural_alternatives=alternatives,
                encouragement="좋아요! 계속해서 대화해 보세요! 👍",
            )

        # ── 대화 기록 포함하여 프롬프트 생성 ─────────────────────────────────
        prompt = build_realtime_correction_prompt(
            user_message=user_message,
            expected_speech_level=expected_speech_level,
            avatar_role=avatar_role,
            user_level=user_level,
            conversation_history=conversation_history,   # ← 추가
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

        # ── corrections 파싱 + 필터링 ─────────────────────────────────────────
        corrections = []
        for c in result.get("corrections", []):
            try:
                original  = (c.get("original",  "") or "").strip()
                corrected = (c.get("corrected", "") or "").strip()
                if not original or not corrected:  continue
                if original == corrected:          continue
                if original not in user_message:
                    print(f"[ChatService] ⚠️ Hallucination skip: '{original}' not in '{user_message}'")
                    continue
                corrections.append(InlineCorrection(
                    original=original,
                    corrected=corrected,
                    type=CorrectionType(c.get("type", "grammar")),
                    severity=CorrectionSeverity(c.get("severity", "warning")),
                    explanation=c.get("explanation", ""),
                    tip=c.get("tip"),
                ))
            except (ValueError, KeyError):
                continue

        # ── natural_alternatives 파싱 ─────────────────────────────────────────
        natural_alternatives = []
        for a in result.get("natural_alternatives", []):
            try:
                expression  = (a.get("expression",  "") or "").strip()
                explanation = (a.get("explanation", "") or "").strip()
                if not expression:                      continue
                if expression == user_message.strip():  continue
                natural_alternatives.append(NaturalAlternative(
                    expression=expression,
                    explanation=explanation,
                ))
            except Exception:
                continue

        # ── 하이브리드 발화 레벨 감지 ──────────────────────────────────────────
        clova_raw        = (result.get("detected_speech_level") or "").strip().lower()
        clova_norm       = LEVEL_MAP.get(clova_raw, clova_raw)
        detected_norm    = verify_with_rules(user_message, clova_norm)
        is_level_correct = (detected_norm == expected_norm) or (detected_norm == "")

        # ── has_errors — info 제외 ────────────────────────────────────────────
        real_errors = [
            c for c in corrections
            if c.severity in (CorrectionSeverity.ERROR, CorrectionSeverity.WARNING)
        ]
        has_errors     = (len(real_errors) > 0) or not is_level_correct
        accuracy_score = result.get("accuracy_score", 100)

        if not has_errors and corrections:
            accuracy_score = max(accuracy_score, 90)

        # ── 말투 오류 시 corrected 검증 ──────────────────────────────────────
        if not is_level_correct:
            accuracy_score = min(accuracy_score, 55)
            expected_name  = SPEECH_LEVEL_INFO[expected_speech_level]["name_ko"]
            example        = SPEECH_LEVEL_INFO[expected_speech_level]["examples"][0]

            clova_corrected      = (result.get("corrected_message") or "").strip()
            clova_corrected_norm = verify_with_rules(clova_corrected, "") if clova_corrected else ""

            if clova_corrected and clova_corrected_norm == expected_norm:
                best_corrected = clova_corrected
            else:
                rule_corrected = simple_convert_to_level(user_message, expected_norm)
                if rule_corrected and verify_with_rules(rule_corrected, "") == expected_norm:
                    best_corrected = rule_corrected
                else:
                    best_corrected = example

            corrections.insert(0, InlineCorrection(
                original=user_message,
                corrected=best_corrected,
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
            natural_alternatives=natural_alternatives,
            expected_speech_level=SPEECH_LEVEL_INFO[expected_speech_level]["name_ko"],
            detected_speech_level=detected_norm or clova_raw or expected_norm,
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
        error_count   = sum(1 for c in correction.corrections if c.severity == CorrectionSeverity.ERROR)
        warning_count = sum(1 for c in correction.corrections if c.severity == CorrectionSeverity.WARNING)
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