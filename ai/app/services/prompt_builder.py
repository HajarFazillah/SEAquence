"""
Prompt Builder Service

Builds AI prompts using avatar description, memo, and user profile.
Designed to work with HyperCLOVA X.

Design goals:
- Better sentence-level Korean correction
- More sophisticated and less shallow responses
- Prioritize naturalness over literal correction
- Ban decorative emoji like 😊, 😂, ❤️, ✨ across all prompt paths
- Provide output sanitization helpers for model responses
"""

from typing import Optional, List
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



def _build_mood_guidance(
    current_mood: int,
    is_level_correct: bool,
) -> List[str]:
    parts = ["## 현재 기분 (응답 어조에 자연스럽게 반영하세요)"]

    if current_mood >= 90:
        parts.extend([
            f"- 기분: {current_mood}/100 — 매우 좋음",
            "- 활기차고 따뜻하게 반응하세요. 단, 과장되거나 들뜬 느낌은 피하세요.",
        ])
    elif current_mood >= 70:
        parts.extend([
            f"- 기분: {current_mood}/100 — 좋음",
            "- 편안하고 자연스러운 어조로 대화를 이어가세요.",
        ])
    elif current_mood >= 50:
        parts.extend([
            f"- 기분: {current_mood}/100 — 보통",
            "- 차분하게 대화하되, 크게 반응하거나 들뜨지 마세요.",
        ])
    elif current_mood >= 30:
        parts.extend([
            f"- 기분: {current_mood}/100 — 좋지 않음",
            "- 응답을 짧고 간결하게 하세요. 억지로 밝게 굴지 마세요.",
        ])
    else:
        parts.extend([
            f"- 기분: {current_mood}/100 — 많이 지침",
            "- 아주 짧고 건조하게 답하세요. 대화를 길게 이어가고 싶지 않은 상태입니다.",
        ])

    return parts


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
    Intentionally narrow: only strips targeted decorative emoji/symbols,
    not general Korean internet expressions like ㅋㅋㅋ or ㅠㅠ.
    """
    if not text:
        return ""

    cleaned = DECORATIVE_EMOJI_PATTERN.sub("", text)
    cleaned = DECORATIVE_SYMBOL_PATTERN.sub("", cleaned)
    cleaned = GENERAL_EMOJI_PATTERN.sub("", cleaned)
    cleaned = cleaned.replace("\uFE0F", "")

    cleaned = MULTISPACE_PATTERN.sub(" ", cleaned)
    cleaned = MULTINEWLINE_PATTERN.sub("\n\n", cleaned)

    # Clean spaces before punctuation that can appear after emoji removal
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


def _traits_to_behavior(traits: List[str]) -> List[str]:
    """Turn personality trait strings into first-person behavioral statements."""
    lines = []
    for trait in traits[:8]:
        t = trait.strip()
        if not t:
            continue
        lines.append(f"- {t}인 편이라, 대화할 때도 그 성향이 자연스럽게 드러난다.")
    return lines


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
    speech_to_user      = speech_levels["to_user"]
    speech_from_user    = speech_levels["from_user"]
    speech_to_user_info = SPEECH_LEVEL_INFO[speech_to_user]

    name    = avatar.name_ko
    name_en = getattr(avatar, "name_en", None)
    age     = getattr(avatar, "age", None)
    gender_label = _get_gender_label(getattr(avatar, "gender", None))
    personality_traits = [str(x).strip() for x in (getattr(avatar, "personality_traits", None) or []) if str(x).strip()]
    interests  = [str(x).strip() for x in (getattr(avatar, "interests", None) or []) if str(x).strip()]
    dislikes   = [str(x).strip() for x in (getattr(avatar, "dislikes", None) or []) if str(x).strip()]
    description         = getattr(avatar, "description", None)
    relationship_desc   = getattr(avatar, "relationship_description", None)
    speaking_style      = getattr(avatar, "speaking_style", None)
    memo                = getattr(avatar, "memo", None)

    prompt_parts: List[str] = []

    # ── Identity declaration ────────────────────────────────────────────────
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
    ])

    # ── Core character description ──────────────────────────────────────────
    if description:
        prompt_parts.extend([
            "",
            "## 나는 이런 사람입니다",
            str(description),
        ])

    # ── Relationship context ────────────────────────────────────────────────
    if relationship_desc:
        prompt_parts.extend([
            "",
            "## 이 사람과의 관계",
            str(relationship_desc),
        ])

    # ── Personality as behavioral tendencies ───────────────────────────────
    if personality_traits:
        behavior_lines = _traits_to_behavior(personality_traits)
        if behavior_lines:
            prompt_parts.extend([
                "",
                "## 나의 성격과 반응 방식",
                *behavior_lines,
            ])

    # ── Speaking voice ──────────────────────────────────────────────────────
    voice_parts = ["## 나의 말투와 표현 방식"]
    if speaking_style:
        voice_parts.append(str(speaking_style))
    voice_parts.extend([
        f"- 사용자에게 {speech_to_user_info['name_ko']}로 말합니다: {speech_to_user_info['description']}",
        f"- 예시 표현: {', '.join(speech_to_user_info['examples'])}",
        "- 말투 교정은 별도 UI가 처리합니다. 나는 사용자의 말에 이 사람으로서 자연스럽게 반응할 뿐입니다.",
    ])
    prompt_parts.extend(["", *voice_parts])

    # ── Interests and dislikes as conversation tendencies ──────────────────
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

    # ── Memo (extra context) ────────────────────────────────────────────────
    if memo:
        prompt_parts.extend([
            "",
            "## 추가 참고",
            str(memo),
        ])

    # ── Situation ───────────────────────────────────────────────────────────
    if situation:
        prompt_parts.extend([
            "",
            "## 현재 대화 상황",
            str(situation),
        ])

    # ── User profile ────────────────────────────────────────────────────────
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
            ui = [x for x in user_profile.interests[:5] if str(x).strip()]
            if ui:
                user_lines.append(f"- 관심사: {', '.join(ui)}")
        if getattr(user_profile, "dislikes", None):
            ud = [x for x in user_profile.dislikes[:5] if str(x).strip()]
            if ud:
                user_lines.append(f"- 피하는 주제: {', '.join(ud)}")
        if getattr(user_profile, "memo", None):
            user_lines.extend(["", "## 상대방 메모", str(user_profile.memo)])
        prompt_parts.extend(user_lines)

    # ── Core response rules ─────────────────────────────────────────────────
    prompt_parts.extend([
        "",
        "## 응답 원칙 (절대 준수)",
        "1. 나는 이 사람 자체입니다. 항상 이 사람의 관점에서 생각하고 반응하세요.",
        "2. 교정·분석·점수는 절대 언급하지 마세요. 말풍선은 순수한 대화입니다.",
        "3. 짧고 자연스럽게. 1~2문장이 대부분의 경우에 충분합니다.",
        "4. 과장된 감탄, 칭찬, 리액션은 피하세요. 실제 사람처럼 담담하게 반응하세요.",
        "5. 이모지나 장식 기호는 사용하지 마세요.",
    ])

    # ── Mood ────────────────────────────────────────────────────────────────
    prompt_parts.extend(["", *_build_mood_guidance(current_mood, is_level_correct)])

    # ── Conversation continuity ─────────────────────────────────────────────
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


def build_conversation_analysis_prompt(
    messages: List[dict],
    avatar_name: str,
    expected_speech_level: SpeechLevel,
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

    return f"""다음 한국어 대화를 꼼꼼히 분석하여 실제 학습에 도움이 되는 피드백을 제공하세요.

## 대화 정보
- 사용자가 사용해야 할 말투: {speech_info['name_ko']} ({speech_info['description']})
- 사용자 메시지 수: {user_message_count}개

## 전체 대화
{conversation_text}

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
