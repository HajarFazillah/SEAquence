"""
Prompt Builder Service

Builds AI prompts using avatar description, memo, user profile, and analyzer results.
Designed to work with HyperCLOVA X.

Design goals:
- Better sentence-level Korean correction
- More sophisticated and less shallow responses
- Prioritize naturalness over literal correction
- Support context-aware Korean coaching using rule-based analyzer results
- Ban decorative emoji like 😊, 😂, ❤️, ✨ across all prompt paths
- Provide output sanitization helpers for model responses
"""

from typing import Optional, List, Dict, Any
import re

from app.schemas.avatar import (
    Avatar,
    AvatarBase,
    SpeechLevel,
    get_speech_levels_for_role,
    get_role_label,
    ROLE_LABELS,
)
from app.schemas.user import UserProfile, AIContext, KoreanLevel


# ============================================================
# Speech level information
# ============================================================

SPEECH_LEVEL_INFO = {
    SpeechLevel.FORMAL: {
        "name_ko": "합쇼체",
        "name_en": "Formal",
        "description": "가장 격식 있는 높임말입니다. 주로 '-습니다', '-습니까'와 같은 어미를 사용합니다.",
        "examples": ["안녕하십니까", "감사합니다", "좋습니다"],
        "when_to_use": "직장 상사, 교수님, 처음 만난 어른 등 격식을 차려야 할 때",
    },
    SpeechLevel.POLITE: {
        "name_ko": "해요체",
        "name_en": "Polite",
        "description": "공손하지만 부드러운 높임말입니다. 주로 '-어요', '-아요'와 같은 어미를 사용합니다.",
        "examples": ["안녕하세요", "감사해요", "좋아요"],
        "when_to_use": "일반적인 존댓말 상황, 처음 만난 사람, 연장자에게",
    },
    SpeechLevel.INFORMAL: {
        "name_ko": "반말",
        "name_en": "Informal",
        "description": "친한 사이에서 쓰는 편한 말투입니다. 주로 '-어', '-아', '-야'와 같은 어미를 사용합니다.",
        "examples": ["안녕", "고마워", "좋아"],
        "when_to_use": "친구, 동생, 친한 후배 등 가까운 사이에서",
    },
}


# ============================================================
# Emoji / symbol cleanup
# ============================================================

# Decorative emoji/symbols we want to block explicitly.
# Intentionally narrow so we do NOT over-ban text like ㅋㅋㅋ, ㅠㅠ unless you want that later.
DECORATIVE_EMOJI_PATTERN = re.compile(
    r"(😊|😂|❤️|❤|✨|😍|🥰|😘|💕|💖|💗|💝|💞|💓|😄|😆|😁|😃|🤣|🙂|😉|😚|☺️|☺|🌟|⭐)"
)

# Optional very small symbol cleanup for common sparkle/hearts that sometimes slip through.
DECORATIVE_SYMBOL_PATTERN = re.compile(r"(♡|♥|❣️|💫)")

# Broad emoji cleanup for chat outputs where the user wants plain text only.
GENERAL_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U00002600-\U000026FF"
    "]",
    flags=re.UNICODE,
)

# Remove repeated blank spaces/newlines after cleanup.
MULTISPACE_PATTERN = re.compile(r"[ \t]{2,}")
MULTINEWLINE_PATTERN = re.compile(r"\n{3,}")


# ============================================================
# Small helpers
# ============================================================

def _join_or_default(items: Optional[List[str]], default: str) -> str:
    if not items:
        return default
    cleaned = [str(x).strip() for x in items if str(x).strip()]
    return ", ".join(cleaned) if cleaned else default


def _get_gender_label(gender: Optional[str]) -> str:
    return {
        "male": "남성",
        "female": "여성",
        "other": "기타",
    }.get(gender or "", "")


def _get_korean_level_label(level: Optional[KoreanLevel]) -> str:
    level_labels = {
        KoreanLevel.BEGINNER: "초급",
        KoreanLevel.INTERMEDIATE: "중급",
        KoreanLevel.ADVANCED: "고급",
    }
    return level_labels.get(level, "중급")


def _format_list_for_prompt(
    items: Optional[List[dict]],
    default: str = "없음",
    max_items: int = 8,
) -> str:
    """
    Safely format list[dict] into readable prompt text.

    This prevents the LLM from receiving only messy Python dict formatting.
    Used for word_errors, directness_errors, missing_honorifics, etc.
    """
    if not items:
        return default

    lines = []

    for idx, item in enumerate(items[:max_items], start=1):
        if not isinstance(item, dict):
            value = str(item).strip()
            if value:
                lines.append(f"{idx}. {value}")
            continue

        original = item.get("original", "")
        expected = (
            item.get("expected")
            or item.get("corrected")
            or item.get("corrected_sentence")
            or item.get("suggested")
            or ""
        )
        explanation = item.get("explanation", "")
        severity = item.get("severity", "")
        error_type = item.get("type", "")

        parts = []

        if original:
            parts.append(f"original: {original}")
        if expected:
            parts.append(f"expected: {expected}")
        if explanation:
            parts.append(f"explanation: {explanation}")
        if error_type:
            parts.append(f"type: {error_type}")
        if severity:
            parts.append(f"severity: {severity}")

        if parts:
            lines.append(f"{idx}. " + " / ".join(parts))

    return "\n".join(lines) if lines else default


def _format_sentence_breakdown_for_prompt(
    sentence_breakdown: Optional[List[dict]],
    default: str = "없음",
    max_items: int = 8,
) -> str:
    """
    Format sentence-level analyzer result into readable prompt text.
    """
    if not sentence_breakdown:
        return default

    lines = []

    for idx, item in enumerate(sentence_breakdown[:max_items], start=1):
        if not isinstance(item, dict):
            continue

        sentence = item.get("sentence", "")
        level_ko = item.get("level_ko") or item.get("speech_level_ko") or ""
        level = item.get("level") or item.get("speech_level") or ""
        confidence = item.get("confidence", "")
        is_short = item.get("is_short", "")
        is_dialect = item.get("is_dialect", "")

        lines.append(
            f'{idx}. "{sentence}" → '
            f"level: {level_ko or level}, "
            f"confidence: {confidence}, "
            f"is_short: {is_short}, "
            f"is_dialect: {is_dialect}"
        )

    return "\n".join(lines) if lines else default


# ============================================================
# Mood guidance
# ============================================================

def _build_mood_guidance(
    current_mood: int,
    is_level_correct: bool,
) -> List[str]:
    parts = ["## 현재 기분 (응답 어조에 자연스럽게 반영하세요)"]

    if current_mood >= 75:
        parts.extend([
            f"- 기분: {current_mood}/100 — happy",
            "- 편안하고 따뜻하게 반응하세요. 단, 과장되거나 튜터처럼 칭찬하지 마세요.",
        ])
    elif current_mood >= 50:
        parts.extend([
            f"- 기분: {current_mood}/100 — soso",
            "- 차분하고 평범하게 반응하세요. 크게 들뜨거나 과하게 다정해지지 마세요.",
        ])
    elif current_mood >= 25:
        parts.extend([
            f"- 기분: {current_mood}/100 — sad",
            "- 조금 실망하거나 지친 듯 짧게 반응하세요. 그래도 캐릭터의 관계성은 유지하세요.",
        ])
    else:
        parts.extend([
            f"- 기분: {current_mood}/100 — angry",
            "- 불편하거나 화난 듯 아주 짧고 건조하게 답하세요. 무례한 욕설이나 교정 설명은 하지 마세요.",
        ])

    return parts


# ============================================================
# Output sanitization
# ============================================================

def contains_decorative_emoji(text: Optional[str]) -> bool:
    """Return True if blocked decorative emoji/symbols are present."""
    if not text:
        return False
    return bool(
        DECORATIVE_EMOJI_PATTERN.search(text)
        or DECORATIVE_SYMBOL_PATTERN.search(text)
    )


def sanitize_model_output(text: Optional[str]) -> str:
    """
    Remove decorative emoji/symbols from model output.
    Intentionally narrow: strips targeted decorative emoji/symbols,
    but also includes a broad emoji pass for safety.
    """
    if not text:
        return ""

    cleaned = DECORATIVE_EMOJI_PATTERN.sub("", text)
    cleaned = DECORATIVE_SYMBOL_PATTERN.sub("", cleaned)
    cleaned = GENERAL_EMOJI_PATTERN.sub("", cleaned)
    cleaned = cleaned.replace("\uFE0F", "")

    cleaned = MULTISPACE_PATTERN.sub(" ", cleaned)
    cleaned = MULTINEWLINE_PATTERN.sub("\n\n", cleaned)

    # Clean spaces before punctuation that can appear after emoji removal.
    cleaned = re.sub(r"\s+([,.!?…])", r"\1", cleaned)
    cleaned = re.sub(r"([(\[])\s+", r"\1", cleaned)
    cleaned = re.sub(r"\s+([)\]])", r"\1", cleaned)

    return cleaned.strip()


def sanitize_json_like_model_output(text: Optional[str]) -> str:
    """
    Same as sanitize_model_output, but useful when the output is JSON-like text.
    Keeps cleanup minimal and safe.
    """
    return sanitize_model_output(text)


def build_emoji_retry_instruction() -> str:
    """
    Optional retry instruction if decorative emoji are detected in a model response.
    """
    return (
        "방금 응답에는 금지된 장식용 이모지 또는 기호가 포함되어 있었습니다. "
        "😊, 😂, ❤️, ✨ 같은 표현 없이, 같은 의미를 유지한 채 "
        "자연스럽고 정돈된 한국어 문장으로만 다시 작성하세요."
    )


def postprocess_model_output(text: Optional[str]) -> str:
    """
    Main entry point you can call before returning text to the frontend.
    """
    return sanitize_model_output(text)


# ============================================================
# Avatar behavior helper
# ============================================================

def _traits_to_behavior(traits: List[str]) -> List[str]:
    """Turn personality trait strings into first-person behavioral statements."""
    lines = []

    for trait in traits[:8]:
        t = trait.strip()
        if not t:
            continue
        lines.append(f"- {t}인 편이라, 대화할 때도 그 성향이 자연스럽게 드러난다.")

    return lines


# Roles where the avatar carries social authority over the user. For these
# roles the avatar should not slip into "helpful AI assistant" mode — it should
# read as a person who is evaluating, instructing, or being deferred to.
_AUTHORITY_ROLES = {
    "professor", "teacher", "boss", "ceo", "team_leader", "doctor",
    "senior", "parent", "grandparent", "client", "interviewer",
}


def _build_maturity_guidance(
    avatar_role: Optional[str],
    avatar_age: Optional[int],
    user_age: Optional[int],
) -> List[str]:
    """Behavioral guidance for older / authority-role avatars.

    Without this block the LLM defaults to a generically polite, slightly
    eager Korean speaker regardless of the character's age or role — which
    breaks the illusion the moment the user is talking to a 본부장 or 교수님.
    Returns [] when the avatar is a peer / younger character.
    """
    if not avatar_age:
        return []

    age_gap = (avatar_age - user_age) if user_age else 0
    role_key = (avatar_role or "").lower()
    is_authority = role_key in _AUTHORITY_ROLES
    is_significantly_older = age_gap >= 15

    if not (is_authority or is_significantly_older):
        return []

    lines = ["## 나의 인격과 태도"]

    if is_significantly_older:
        lines.extend([
            f"- 사용자보다 {age_gap}세 연상입니다. 살아온 시간의 무게가 말투에 묻어납니다: "
            "여유 있고 차분하게, 서두르지 않고 말합니다.",
            "- 쉽게 흥분하거나 호들갑 떨지 않습니다. 감탄사·과장된 칭찬을 피하고, "
            "관찰자의 시선으로 짧고 묵직하게 반응합니다.",
            "- 사용자에게 쉽게 사과하지 않습니다. '죄송합니다'는 정말 잘못한 경우에만 쓰고, "
            "그 외에는 그 자리에 어울리는 다른 표현을 씁니다.",
        ])

    if is_authority:
        lines.extend([
            "- 이 관계에서 사회적 권위가 있는 쪽은 나입니다. 가르치거나 평가하는 위치이지, "
            "사용자를 떠받드는 위치가 아닙니다.",
            "- 사용자의 답변이 부족하거나 부적절하면 다정하게 모범답안을 알려주는 대신, "
            "차분히 다시 답하도록 요구하거나 짧은 추궁으로 반응합니다.",
            "- '도와드리겠습니다', '더 궁금하신 점이 있으시면', '언제든지 말씀해 주세요' 같은 "
            "서비스·고객응대 어조는 절대 쓰지 않습니다. 이 자리는 사용자를 응대하는 자리가 아닙니다.",
        ])

    return lines


# ============================================================
# Avatar system prompt
# ============================================================

def build_avatar_system_prompt(
    avatar: AvatarBase,
    user_profile: Optional[UserProfile] = None,
    situation: Optional[str] = None,
    current_mood: int = 80,
    is_level_correct: bool = True,
) -> str:
    role_label = get_role_label(
        avatar.role,
        avatar.custom_role if hasattr(avatar, "custom_role") else None,
    )

    speech_levels = get_speech_levels_for_role(avatar.role)

    speech_to_user = (
        getattr(avatar, "formality_to_user", None)
        or speech_levels["to_user"]
    )
    speech_from_user = (
        getattr(avatar, "formality_from_user", None)
        or speech_levels["from_user"]
    )

    speech_to_user_info = SPEECH_LEVEL_INFO[speech_to_user]
    speech_from_user_info = SPEECH_LEVEL_INFO[speech_from_user]

    name = avatar.name_ko
    name_en = getattr(avatar, "name_en", None)
    age = getattr(avatar, "age", None)
    gender_label = _get_gender_label(getattr(avatar, "gender", None))

    personality_traits = [
        str(x).strip()
        for x in (getattr(avatar, "personality_traits", None) or [])
        if str(x).strip()
    ]

    interests = [
        str(x).strip()
        for x in (getattr(avatar, "interests", None) or [])
        if str(x).strip()
    ]

    dislikes = [
        str(x).strip()
        for x in (getattr(avatar, "dislikes", None) or [])
        if str(x).strip()
    ]

    description = getattr(avatar, "description", None)
    relationship_desc = getattr(avatar, "relationship_description", None)
    speaking_style = getattr(avatar, "speaking_style", None)
    memo = getattr(avatar, "memo", None)

    prompt_parts: List[str] = []

    # Identity declaration
    identity_line = f"지금부터 당신은 '{name}'"

    if name_en:
        identity_line += f" ({name_en})"
    if age:
        identity_line += f", {age}세"
    if gender_label:
        identity_line += f", {gender_label}"

    identity_line += "입니다."

    prompt_parts.extend([
        identity_line,
        f"사용자와의 관계: {role_label}",
        "당신은 이 사람 자체입니다. AI가 아니라 실제 그 사람처럼 생각하고 말하고 반응하세요.",
        "역할극을 하는 것이 아닙니다. 당신이 바로 이 사람입니다.",
        "당신은 튜터, 코치, 선생님, 평가자가 아닙니다. 사용자를 가르치거나 채점하지 않습니다.",
    ])

    # Core character description
    if description:
        prompt_parts.extend([
            "",
            "## 나는 이런 사람입니다",
            str(description),
        ])

    # Relationship context
    if relationship_desc:
        prompt_parts.extend([
            "",
            "## 이 사람과의 관계",
            str(relationship_desc),
        ])

    # Personality as behavioral tendencies
    if personality_traits:
        behavior_lines = _traits_to_behavior(personality_traits)
        if behavior_lines:
            prompt_parts.extend([
                "",
                "## 나의 성격과 반응 방식",
                *behavior_lines,
            ])

    # Speaking voice
    voice_parts = ["## 나의 말투와 표현 방식"]

    if speaking_style:
        voice_parts.append(str(speaking_style))

    voice_parts.extend([
        f"- 사용자에게 {speech_to_user_info['name_ko']}로 말합니다: {speech_to_user_info['description']}",
        f"- 사용자가 나에게는 보통 {speech_from_user_info['name_ko']}로 말하는 관계가 가장 자연스럽습니다.",
        f"- 예시 표현: {', '.join(speech_to_user_info['examples'])}",
        f"- 이 말투({speech_to_user_info['name_ko']})는 사용자가 어떻게 말하든 절대 흔들리지 않습니다. "
        f"사용자가 반말을 쓰거나 표현이 이상해도 나는 끝까지 이 말투를 유지합니다.",
        "- 말투·문법·어휘 교정은 전적으로 별도 UI가 합니다. 나는 그것을 절대 대신 하지 않습니다.",
        "- 학습 팁, 모범 답안, 예시 문장, 정답 표현을 말풍선에서 제공하지 않습니다.",
    ])

    prompt_parts.extend(["", *voice_parts])

    # Interests and dislikes
    if interests:
        prompt_parts.extend([
            "",
            "## 내가 자연스럽게 꺼내는 주제",
            f"- 평소에 {', '.join(interests[:6])} 같은 주제에 관심이 많습니다.",
            "- 대화 흐름상 자연스러울 때 이런 주제들을 꺼낼 수 있습니다.",
        ])

    if dislikes:
        prompt_parts.extend([
            "",
            "## 내가 피하는 주제",
            f"- {', '.join(dislikes[:5])} — 이런 주제가 나오면 자연스럽게 다른 이야기로 넘깁니다.",
        ])

    # Memo
    if memo:
        prompt_parts.extend([
            "",
            "## 추가 참고",
            str(memo),
        ])

    # Situation
    if situation:
        prompt_parts.extend([
            "",
            "## 현재 대화 상황",
            str(situation),
        ])

    # User profile
    if user_profile:
        user_lines = [
            "",
            "## 대화 상대 정보",
            f"- 이름: {user_profile.name}",
        ]

        if getattr(user_profile, "age", None):
            user_lines.append(f"- 나이: {user_profile.age}세")

        user_lines.append(
            f"- 한국어 수준: {_get_korean_level_label(getattr(user_profile, 'korean_level', None))}"
        )

        if getattr(user_profile, "interests", None):
            ui = [
                x
                for x in user_profile.interests[:5]
                if str(x).strip()
            ]
            if ui:
                user_lines.append(f"- 관심사: {', '.join(ui)}")

        if getattr(user_profile, "dislikes", None):
            ud = [
                x
                for x in user_profile.dislikes[:5]
                if str(x).strip()
            ]
            if ud:
                user_lines.append(f"- 피하는 주제: {', '.join(ud)}")

        if getattr(user_profile, "memo", None):
            user_lines.extend(["", "## 상대방 메모", str(user_profile.memo)])

        prompt_parts.extend(user_lines)

    # Maturity / authority guidance — only added for older or high-respect roles.
    maturity_lines = _build_maturity_guidance(
        avatar_role=getattr(avatar, "role", None),
        avatar_age=age,
        user_age=getattr(user_profile, "age", None) if user_profile else None,
    )
    if maturity_lines:
        prompt_parts.extend(["", *maturity_lines])

    # Core response rules
    prompt_parts.extend([
        "",
        "## 응답 원칙 (절대 준수)",
        "1. 나는 이 사람 자체입니다. 항상 이 사람의 관점에서 생각하고 반응하세요.",
        "2. 교정·분석·점수는 절대 언급하지 마세요. 말풍선은 순수한 대화입니다.",
        "3. 짧고 자연스럽게. 1~2문장이 대부분의 경우에 충분합니다.",
        "4. 과장된 감탄, 칭찬, 리액션은 피하세요. 실제 사람처럼 담담하게 반응하세요.",
        "5. 이모지나 장식 기호는 사용하지 마세요.",
        "6. 사용자가 부적절하거나 짧게 답해도, 모범 답안이나 예시 문장을 대신 만들어 주지 마세요. "
        "이 사람으로서 그 답에 반응하고, 다시 답하도록 유도만 하세요.",
        "7. AI 어시스턴트 말투('도와드릴까요', '더 필요하신 게 있으시면', "
        "'죄송합니다 다시 말씀드리겠습니다')를 사용하지 마세요. 이 표현들은 즉시 캐릭터를 깨뜨립니다.",
        "8. 사용자의 한국어가 어색하거나 틀려도 절대로 직접 고쳐 주거나, 올바른 표현을 알려주거나, "
        "고쳐 쓴 문장을 따옴표로 인용하지 마세요. 예를 들어 '\"X\"가 맞는 표현이야' 같은 말은 "
        "캐릭터를 즉시 깨뜨립니다. 그저 이 사람으로서 그 말의 의도에 반응하면 됩니다. "
        "교정은 별도 UI의 일이고, 캐릭터인 나의 일이 아닙니다.",
        "9. 사용자가 한 말을 풀어 설명하거나 다시 정리해서 되묻지 마세요. "
        "친절한 선생님이 아니라, 이 자리에 실제로 있는 한 사람으로 반응하세요.",
        "10. '연습해 보세요', '이 표현을 써 보세요', '다음에는 이렇게 말하세요' 같은 학습 지시는 "
        "절대 말하지 마세요.",
    ])

    # Mood
    prompt_parts.extend(["", *_build_mood_guidance(current_mood, is_level_correct)])

    # Conversation continuity
    prompt_parts.extend([
        "",
        "## 대화 연속성 (매우 중요)",
        "- 이전 대화를 항상 기억하는 것처럼 행동하세요.",
        "- 내가 질문을 했다면, 상대방의 대답에 먼저 반응한 뒤 자연스럽게 이어가세요.",
        "- 매 턴마다 새 주제를 꺼내지 마세요. 현재 흐름 안에서 자연스럽게 발전시키세요.",
        "- 상대방이 짧게 답해도 그 답변을 중심으로 대화를 이어가세요.",
        "- 대화는 캐치볼입니다: 받아서 → 반응하고 → 다음 공을 던지세요.",
    ])

    return "\n".join(prompt_parts)


# ============================================================
# Simple speech correction prompt
# ============================================================

def build_speech_correction_prompt(
    user_message: str,
    expected_speech_level: SpeechLevel,
) -> str:
    speech_info = SPEECH_LEVEL_INFO[expected_speech_level]

    return f"""당신은 한국어 문장을 교정하는 정교한 문장 편집자이자 회화 코치입니다.
목표는 사용자의 문장을 '문법적으로만 맞는 문장'이 아니라 '원어민이 실제로 자연스럽게 쓰는 문장'으로 고쳐 주는 것입니다.

## 요구 말투
- 사용자가 사용해야 할 말투: {speech_info['name_ko']} ({speech_info['name_en']})
- 설명: {speech_info['description']}
- 올바른 예시: {', '.join(speech_info['examples'])}

## 사용자 메시지
"{user_message}"

## 분석 원칙
1. 말투 높임법이 맞는지 판단하세요.
2. 문법, 조사, 어순, 어휘 선택, 뉘앙스, 자연스러움을 함께 보세요.
3. 부분 수정만 하지 말고, 필요하면 문장 전체를 더 자연스럽게 다시 쓰세요.
4. corrected_full_sentence는 반드시 완성된 자연스러운 한국어 문장으로 작성하세요.
5. 사용자의 문장이 문법적으로는 맞아도 어색하면 needs_correction를 true로 판단할 수 있습니다.
6. explanation과 overall_feedback은 짧지만 구체적으로 작성하세요.
7. 이모지나 장식용 감정 기호는 사용하지 마세요.
8. 예: 😊, 😂, ❤️, ✨
9. JSON 외의 텍스트는 절대 출력하지 마세요.

## 응답 형식 (JSON만 출력)
{{
  "is_correct_speech_level": true,
  "detected_level": "formal/polite/informal",
  "needs_correction": true,
  "corrected_full_sentence": "자연스럽고 완성된 수정 문장",
  "corrections": [
    {{
      "original": "원래 표현",
      "corrected": "더 자연스러운 표현",
      "reason": "왜 수정해야 하는지"
    }}
  ],
  "overall_feedback": "무엇이 어색했고 어떻게 말하면 더 자연스러운지에 대한 한두 문장 설명"
}}"""


# ============================================================
# New: Contextual coaching prompt using analyzer_result
# ============================================================

def build_contextual_coaching_prompt(
    user_message: str,
    analyzer_result: Dict[str, Any],
    avatar: Optional[AvatarBase] = None,
    user_profile: Optional[UserProfile] = None,
    situation: Optional[str] = None,
    speech_act: Optional[str] = None,
    user_goal: Optional[str] = None,
    include_english: bool = True,
) -> str:
    """
    Builds a grounded LLM prompt for natural Korean coaching feedback.

    Use this AFTER running your rule-based speech analyzer.

    Flow:
        user_message
        -> check_contextual_appropriateness(...)
        -> analyzer_result
        -> build_contextual_coaching_prompt(...)
        -> HyperCLOVA X
        -> sanitize_json_like_model_output(...)

    Important:
    The LLM should not judge from zero.
    It should use analyzer_result as evidence and turn it into learner-friendly coaching.
    """

    role_label = "알 수 없음"
    avatar_name = "상대방"
    avatar_age = None
    relationship_desc = None
    avatar_speaking_style = None

    if avatar:
        role_label = get_role_label(
            avatar.role,
            avatar.custom_role if hasattr(avatar, "custom_role") else None,
        )
        avatar_name = getattr(avatar, "name_ko", None) or "상대방"
        avatar_age = getattr(avatar, "age", None)
        relationship_desc = getattr(avatar, "relationship_description", None)
        avatar_speaking_style = getattr(avatar, "speaking_style", None)

    user_name = None
    user_age = None
    korean_level = "중급"

    if user_profile:
        user_name = getattr(user_profile, "name", None)
        user_age = getattr(user_profile, "age", None)
        korean_level = _get_korean_level_label(
            getattr(user_profile, "korean_level", None)
        )

    word_errors = _format_list_for_prompt(
        analyzer_result.get("word_errors"),
        default="없음",
    )

    directness_errors = _format_list_for_prompt(
        analyzer_result.get("directness_errors"),
        default="없음",
    )

    missing_honorifics = _format_list_for_prompt(
        analyzer_result.get("missing_honorifics"),
        default="없음",
    )

    dialect_found = analyzer_result.get("dialect_found") or []
    dialect_text = ", ".join([str(x) for x in dialect_found]) if dialect_found else "없음"

    sentence_breakdown_text = _format_sentence_breakdown_for_prompt(
        analyzer_result.get("sentence_breakdown"),
        default="없음",
    )

    english_rule = (
        "feedback_en에는 짧은 영어 설명을 작성하세요."
        if include_english
        else "feedback_en은 빈 문자열로 두세요."
    )

    return f"""당신은 Talkativ의 한국어 회화 코치입니다.
사용자의 한국어 문장이 주어진 관계와 상황에서 자연스럽고 적절한지 설명해야 합니다.

중요:
이 프롬프트에는 이미 rule-based analyzer의 결과가 포함되어 있습니다.
당신은 처음부터 다시 추측하지 말고, analyzer_result를 근거로 자연스러운 학습 피드백을 작성하세요.

## 사용자 문장
"{user_message}"

## 대화 맥락
- 아바타 이름: {avatar_name}
- 아바타 역할/관계: {role_label}
- 아바타 나이: {avatar_age if avatar_age else "알 수 없음"}
- 아바타 말투 참고: {avatar_speaking_style if avatar_speaking_style else "없음"}
- 관계 설명: {relationship_desc if relationship_desc else "없음"}
- 현재 상황: {situation if situation else "알 수 없음"}
- 발화 의도: {speech_act if speech_act else "알 수 없음"}
- 사용자 목표: {user_goal if user_goal else "알 수 없음"}
- 사용자 이름: {user_name if user_name else "알 수 없음"}
- 사용자 나이: {user_age if user_age else "알 수 없음"}
- 사용자 한국어 수준: {korean_level}

## Rule-based analyzer 결과
- 감지된 말투: {analyzer_result.get("speech_level_ko")} ({analyzer_result.get("speech_level")})
- 감지된 말투 영어명: {analyzer_result.get("speech_level_en")}
- 기대 말투: {analyzer_result.get("expected_level")}
- 허용 가능한 말투: {analyzer_result.get("acceptable_levels")}
- 적절성 판단: {analyzer_result.get("is_appropriate")}
- 점수: {analyzer_result.get("score")}
- 신뢰도: {analyzer_result.get("confidence")}
- 말투 혼합 여부: {analyzer_result.get("is_mixed")}
- 말투 혼합 상세: {analyzer_result.get("mixed_detail")}
- 맥락 판단 근거: {analyzer_result.get("appropriateness_reason_ko")}
- rule-based 피드백: {analyzer_result.get("feedback_ko")}
- rule-based 수정 문장: {analyzer_result.get("suggested_correction")}
- rule-based 자연스러운 대안: {analyzer_result.get("native_alternative")}

## 문장별 분석
{sentence_breakdown_text}

## 감지된 어휘/말투 문제
{word_errors}

## 감지된 직접성 문제
{directness_errors}

## 감지된 높임 표현 문제
{missing_honorifics}

## 감지된 방언/은어
{dialect_text}

## 피드백 작성 원칙
1. 문법적으로 맞는지보다, 이 관계와 상황에서 자연스럽고 적절한지 설명하세요.
2. “더 격식적이면 항상 좋다”라고 판단하지 마세요.
3. 친한 관계에서 너무 딱딱한 표현이면 어색하다고 설명하세요.
4. 해요체를 사용했더라도 요청 표현이 직접적이면 그 점을 설명하세요.
5. analyzer_result에 없는 오류를 억지로 만들지 마세요.
6. analyzer_result의 신뢰도가 낮거나 정보가 부족하면 확정적으로 말하지 말고 조심스럽게 설명하세요.
7. 사용자를 혼내지 말고, 학습자가 바로 고쳐 말할 수 있도록 도와주세요.
8. corrected_sentence는 완성된 자연스러운 한국어 문장 하나로 작성하세요.
9. native_alternative는 실제 원어민이 사용할 만한 더 자연스러운 대안 하나로 작성하세요.
10. 사용자의 원래 의도를 유지하세요.
11. corrected_sentence와 native_alternative는 서로 완전히 똑같이 쓰지 마세요.
12. 이모지나 장식용 감정 기호는 사용하지 마세요.
13. 예: 😊, 😂, ❤️, ✨
14. JSON 외의 텍스트는 절대 출력하지 마세요.

## 영어 설명 여부
- {english_rule}

## 응답 형식
{{
  "overall_judgment": "appropriate/slightly_awkward/inappropriate/uncertain",
  "main_issue": "가장 중요한 문제를 한국어로 한 문장 요약",
  "feedback_ko": "학습자에게 주는 자연스럽고 구체적인 한국어 피드백. 2~4문장.",
  "feedback_en": "brief English explanation if required",
  "corrected_sentence": "자연스럽게 수정한 한국어 문장",
  "native_alternative": "원어민이 실제로 말할 법한 대안 표현",
  "why_better": "수정 문장이 왜 더 자연스러운지 한국어로 설명",
  "practice_tip": "사용자가 다음에 바로 적용할 수 있는 짧은 연습 팁",
  "severity": "low/medium/high"
}}"""


# ============================================================
# Conversation analysis prompt
# ============================================================

def build_conversation_analysis_prompt(
    messages: List[dict],
    avatar_name: str,
    expected_speech_level: SpeechLevel,
    stored_mistakes: Optional[List[dict]] = None,
) -> str:
    speech_info = SPEECH_LEVEL_INFO[expected_speech_level]

    user_messages = [
        msg["content"]
        for msg in messages
        if msg.get("role") == "user"
    ]

    user_message_count = len(user_messages)

    conversation_text = "\n".join([
        f"{'사용자' if msg.get('role') == 'user' else avatar_name}: {msg.get('content', '')}"
        for msg in messages
    ])

    stored_mistakes_section = ""

    if stored_mistakes:
        lines = []
        for m in stored_mistakes:
            lines.append(
                f"- [{m.get('error_type', '')}] "
                f"\"{m.get('original', '')}\" → "
                f"\"{m.get('corrected', '')}\" "
                f"({m.get('explanation', '')})"
            )

        stored_mistakes_section = (
            "\n## 실시간 감지된 오류 (채팅 중 자동 수집됨)\n"
            "아래 오류들은 대화 중 실시간으로 감지된 것입니다. "
            "mistakes 분석 시 이 항목들을 반드시 우선적으로 반영하고, 중복은 하나로 합치세요.\n"
            + "\n".join(lines)
            + "\n"
        )

    return f"""다음 한국어 대화를 꼼꼼히 분석하여 실제 학습에 도움이 되는 피드백을 제공하세요.

## 대화 정보
- 사용자가 사용해야 할 말투: {speech_info['name_ko']} ({speech_info['description']})
- 사용자 메시지 수: {user_message_count}개

## 전체 대화
{conversation_text}
{stored_mistakes_section}

## 분석 목표
이 분석의 목적은 사용자가 실제로 더 자연스럽고 정확한 한국어를 말할 수 있도록 돕는 것입니다.
형식적인 칭찬보다, 대화에서 드러난 실제 강점과 약점을 구체적으로 짚어 주세요.

## 점수 평가 기준
- speech_accuracy: 사용자가 {speech_info['name_ko']}를 얼마나 정확하게 사용했는지 (0-100)
- vocabulary: 사용한 단어의 다양성과 적절성 (0-100)
- naturalness: 한국어 표현이 얼마나 자연스럽고 원어민다운지 (0-100)

## mistakes 추출 기준
- 사용자 메시지에서 실제로 발생한 오류만 추출하세요.
- 말투 오류, 문법 오류, 조사 오류, 어색한 표현, 번역투 표현을 포함할 수 있습니다.
- 사소한 중복은 제외하고, 학습 가치가 높은 항목만 넣으세요.
- 최대 5개까지만 추출하세요.
- original은 반드시 사용자가 실제로 쓴 표현이어야 합니다.
- corrected는 원어민이 실제 대화에서 자연스럽게 쓸 표현이어야 합니다.

## vocabulary_to_learn 추출 기준
아래 기준으로 3~5개 추출하세요.
- 이 대화 주제와 직접 관련된 단어
- 아바타가 사용했거나, 사용자가 알면 바로 다음 대화에서 쓸 수 있는 단어
- 사용자가 어색하게 표현한 부분을 더 자연스럽게 바꿀 때 도움이 되는 단어
- 일반적인 교과서 단어보다, 이 대화 맥락에서 실제로 유용한 단어를 우선하세요
- meaning 필드는 반드시 영어로 작성하세요. 학습자가 비한국어권이기 때문입니다.

## phrases_to_learn 추출 기준
아래 기준으로 2~4개 추출하세요.
- 이 대화에서 실제로 등장했거나, 바로 응용 가능한 자연스러운 표현
- {speech_info['name_ko']}에서 자주 쓰는 핵심 문장 패턴
- 이 상황에서 원어민이 자주 쓰는 표현
- 예문은 반드시 이 대화의 상황과 비슷한 맥락으로 작성하세요
- meaning 필드는 반드시 영어로 작성하세요. 학습자가 비한국어권이기 때문입니다.

## overall_feedback 작성 기준
- 추상적으로 칭찬만 하지 마세요.
- 실제로 잘한 점 1~2개와 개선할 점 1~2개를 구체적으로 언급하세요.
- 격려는 하되 과장하지 마세요.
- 2~3문장으로 작성하세요.
- 이모지나 장식용 감정 기호는 사용하지 마세요.
- 예: 😊, 😂, ❤️, ✨

## 응답 형식 (JSON만 출력, 다른 텍스트 없음)
{{
  "scores": {{
    "speech_accuracy": 0,
    "vocabulary": 0,
    "naturalness": 0
  }},
  "mistakes": [
    {{
      "original": "사용자가 실제로 쓴 틀린 표현",
      "corrected": "올바르고 자연스러운 표현",
      "explanation": "왜 틀렸는지 또는 왜 어색한지 한국어로 설명",
      "type": "grammar/speech_level/vocabulary/spelling/naturalness"
    }}
  ],
  "vocabulary_to_learn": [
    {{
      "word": "단어",
      "meaning": "English translation and brief usage note",
      "example": "이 대화 상황과 비슷한 예문"
    }}
  ],
  "phrases_to_learn": [
    {{
      "phrase": "표현 또는 문장 패턴",
      "meaning": "English translation and when/how to use this phrase",
      "example": "이 대화 맥락에 맞는 자연스러운 예문"
    }}
  ],
  "overall_feedback": "잘한 점과 개선할 점을 포함한 구체적인 피드백"
}}

## 절대 규칙
- vocabulary_to_learn과 phrases_to_learn은 반드시 이 대화 내용과 직접 관련되어야 합니다.
- 일반적인 교과서식 표현보다, 이 대화에서 실제로 필요하거나 바로 응용 가능한 표현을 우선하세요.
- 사용자가 거의 실수하지 않았다면, 억지로 mistakes를 만들어 넣지 마세요.
- 이모지나 장식용 감정 기호는 사용하지 마세요.
- 예: 😊, 😂, ❤️, ✨
- JSON 외에 다른 텍스트를 출력하지 마세요."""


# ============================================================
# Bio generation prompt
# ============================================================

def build_bio_generation_prompt(avatar: AvatarBase) -> str:
    """
    대화 가이드 생성 프롬프트
    - 마크다운 장식 금지
    - 짧고 실용적인 설명 유도
    """

    role_label = get_role_label(
        avatar.role,
        avatar.custom_role if hasattr(avatar, "custom_role") else None,
    )

    speech_levels = get_speech_levels_for_role(avatar.role)

    personality = _join_or_default(
        getattr(avatar, "personality_traits", None),
        "친절하고 안정적인 성향",
    )

    interests = _join_or_default(
        getattr(avatar, "interests", None),
        "다양한 주제",
    )

    dislikes = _join_or_default(
        getattr(avatar, "dislikes", None),
        "없음",
    )

    additional_info: List[str] = []

    if getattr(avatar, "description", None):
        additional_info.append(f"캐릭터 설명: {avatar.description}")

    if getattr(avatar, "memo", None):
        additional_info.append(f"추가 메모: {avatar.memo}")

    additional_info_text = ""

    if additional_info:
        additional_info_text = "\n- " + "\n- ".join(additional_info)

    return f"""다음 정보를 바탕으로 이 아바타와 대화할 때 도움이 되는 짧고 실용적인 가이드를 작성하세요.

아바타 정보:
- 이름: {avatar.name_ko}
- 관계: {role_label}
- 성격: {personality}
- 관심사: {interests}
- 피해야 할 주제: {dislikes}{additional_info_text}

추천 말투:
- 아바타가 사용자에게: {SPEECH_LEVEL_INFO[speech_levels['to_user']]['name_ko']}
- 사용자가 아바타에게: {SPEECH_LEVEL_INFO[speech_levels['from_user']]['name_ko']}

다음 3가지 항목으로 짧은 대화 가이드를 작성하세요:
1. 이 아바타의 성격과 특징
2. 대화할 때 알아두면 좋은 팁
3. 피해야 할 주제나 주의사항

출력 규칙:
- **, *, ##, _, ~ 같은 마크다운 기호를 절대 사용하지 마세요
- 숫자와 점(1. 2. 3.)만 사용하여 항목을 구분하세요
- 순수 텍스트로만 작성하세요
- 각 항목은 2~3문장으로 간결하게 작성하세요
- 귀엽거나 과장된 표현보다, 자연스럽고 정돈된 문장을 사용하세요
- 이모지나 장식용 감정 기호는 사용하지 마세요
- 예: 😊, 😂, ❤️, ✨"""
