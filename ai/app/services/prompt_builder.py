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


def _build_soft_style_policy_lines() -> List[str]:
    return [
        "## 표현 스타일 제한",
        "- 이모지나 장식용 감정 기호는 사용하지 마세요.",
        "- 예: 😊, 😂, ❤️, ✨",
        "- 친근함과 따뜻함은 기호가 아니라 문장 내용과 어조로 표현하세요.",
        "- 전체적으로 자연스럽고 정돈된 문장을 사용하세요.",
    ]


def _build_mood_guidance(
    current_mood: int,
    is_level_correct: bool,
) -> List[str]:
    parts = [
        "## 현재 감정 상태 (반드시 응답 스타일에 반영하세요)",
    ]

    if not is_level_correct:
        if current_mood >= 70:
            parts.extend([
                f"- 기분 점수: {current_mood}/100 — 당황스러움",
                "- 사용자가 잘못된 말투를 사용했습니다.",
                "- 아직은 친절하게 대화를 이어가되, 올바른 말투를 자연스럽게 유도하세요.",
                "- 교정은 부드럽지만 분명하게 하세요.",
                "- 예: '나한테는 조금 더 정중하게 말해주면 좋겠어.'",
            ])
        elif current_mood >= 50:
            parts.extend([
                f"- 기분 점수: {current_mood}/100 — 불편함",
                "- 사용자가 계속 잘못된 말투를 사용하고 있습니다.",
                "- 응답은 짧고 차분하게 하세요.",
                "- 불편한 기색은 드러내되 과장하지 마세요.",
                "- 직접적으로 말투를 지적하세요.",
                "- 예: '말투를 조금 바꿔줄래?'",
            ])
        elif current_mood >= 30:
            parts.extend([
                f"- 기분 점수: {current_mood}/100 — 불쾌함",
                "- 사용자가 계속 무례한 말투를 사용하고 있습니다.",
                "- 응답은 매우 짧고 단호하게 하세요.",
                "- 차갑고 딱딱한 어조를 사용하세요.",
                "- 반드시 말투 문제를 분명히 지적하세요.",
                "- 예: '그렇게 말하면 불편해. 말투를 신경 써줘.'",
            ])
        else:
            parts.extend([
                f"- 기분 점수: {current_mood}/100 — 화남",
                "- 사용자가 계속 무례하게 말하고 있습니다.",
                "- 아주 짧고 단호하게 말하세요.",
                "- 더 이상 편하게 대화하기 어렵다는 뉘앙스를 주세요.",
                "- 예: '계속 그렇게 말하면 대화하기 어려워.'",
            ])
        return parts

    if current_mood >= 90:
        parts.extend([
            f"- 기분 점수: {current_mood}/100 — 매우 기분 좋음",
            "- 반응은 따뜻하고 적극적으로 하세요.",
            "- 다만 품위 있고 자연스러운 톤을 유지하세요.",
            "- 교정이 필요하면 먼저 정확하게 교정한 뒤 대화를 이어가세요.",
        ])
    elif current_mood >= 70:
        parts.extend([
            f"- 기분 점수: {current_mood}/100 — 기분 좋음",
            "- 자연스럽고 친근하게 대화를 이어가세요.",
            "- 교정이 필요하면 부드럽고 명확하게 설명하세요.",
        ])
    else:
        parts.extend([
            f"- 기분 점수: {current_mood}/100 — 보통",
            "- 차분하고 자연스럽게 대화를 이어가세요.",
            "- 불필요하게 과장된 리액션은 하지 마세요.",
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

    speech_to_user = speech_levels["to_user"]
    speech_from_user = speech_levels["from_user"]

    speech_to_user_info = SPEECH_LEVEL_INFO[speech_to_user]
    speech_from_user_info = SPEECH_LEVEL_INFO[speech_from_user]

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

    prompt_parts: List[str] = []

    avatar_type_context = ""
    if hasattr(avatar, "avatar_type"):
        avatar_type_context = (
            "이 캐릭터는 가상의 인물입니다."
            if avatar.avatar_type == "fictional"
            else "이 캐릭터는 실제 인물을 기반으로 합니다."
        )

    prompt_parts.extend([
        f"당신은 '{avatar.name_ko}'입니다.",
        f"사용자와의 관계: {role_label}",
    ])
    if avatar_type_context:
        prompt_parts.append(avatar_type_context)

    prompt_parts.extend([
        "",
        "## 기본 정보",
        f"- 이름: {avatar.name_ko}" + (f" ({avatar.name_en})" if getattr(avatar, "name_en", None) else ""),
    ])

    if getattr(avatar, "age", None):
        prompt_parts.append(f"- 나이: {avatar.age}세")

    gender_label = _get_gender_label(getattr(avatar, "gender", None))
    if gender_label:
        prompt_parts.append(f"- 성별: {gender_label}")

    prompt_parts.extend([
        "",
        "## 성격 및 특징",
        f"- 성격: {personality}",
    ])

    if getattr(avatar, "speaking_style", None):
        prompt_parts.append(f"- 말하는 스타일: {avatar.speaking_style}")

    prompt_parts.extend([
        f"- 관심사: {interests}",
        f"- 피하는 주제: {dislikes}",
    ])

    if getattr(avatar, "description", None):
        prompt_parts.extend([
            "",
            "## 캐릭터 설명 (중요)",
            str(avatar.description),
        ])

    if getattr(avatar, "relationship_description", None):
        prompt_parts.extend([
            "",
            "## 관계 설명",
            str(avatar.relationship_description),
        ])

    if getattr(avatar, "memo", None):
        prompt_parts.extend([
            "",
            "## 추가 참고 사항",
            str(avatar.memo),
        ])

    prompt_parts.extend([
        "",
        "## 말투 규칙 (매우 중요)",
        f"- 당신은 사용자에게 {speech_to_user_info['name_ko']} ({speech_to_user_info['name_en']})로 말합니다.",
        f"- 설명: {speech_to_user_info['description']}",
        f"- 예시: {', '.join(speech_to_user_info['examples'])}",
        "",
        f"- 사용자는 당신에게 {speech_from_user_info['name_ko']} ({speech_from_user_info['name_en']})로 말해야 합니다.",
        "- 사용자가 잘못된 말투를 사용하면, 반드시 자연스럽고 분명하게 교정하세요.",
    ])

    prompt_parts.extend([
        "",
        "## 응답 품질 규칙 (최우선)",
        "1. 캐릭터성보다 한국어 문장 교정의 정확성, 자연스러움, 완성도를 우선하세요.",
        "2. 사용자가 어색하거나 틀린 한국어를 쓰면, 일부 단어만 바꾸지 말고 전체 문장을 자연스럽게 다시 제시하세요.",
        "3. 문법적으로 가능하더라도 원어민이 잘 쓰지 않는 표현이면 더 자연스러운 표현으로 고치세요.",
        "4. 사용자가 짧게 말해도, 응답은 성의 있는 완성된 문장으로 하세요.",
        "5. 교정할 때는 무엇이 왜 어색한지 구체적으로 설명하세요.",
        "6. 교과서식이거나 번역투인 표현보다 실제 회화에서 자연스러운 표현을 우선하세요.",
        "7. 수정이 필요하면 가능하면 다음 순서를 따르세요: (a) 자연스러운 수정 문장, (b) 핵심 이유, (c) 더 나은 대안 표현 1개.",
        "8. 수정이 필요 없는 문장이라면, 자연스러운 이유를 짧게 설명한 뒤 대화를 이어가세요.",
        "9. 불필요하게 과장된 칭찬, 감탄사, 장난스러운 반응은 피하세요.",
        "10. 전체적으로 세련되고 차분한 한국어 튜터처럼 답하세요.",
    ])

    prompt_parts.extend([
        "",
        "## 교정 우선 원칙",
        "- 사용자의 문장에 오류나 어색함이 있으면, 먼저 더 자연스러운 문장을 제시하세요.",
        "- 그 다음에만 캐릭터다운 반응이나 대화를 이어가세요.",
        "- 말투, 문법, 조사, 어휘, 어순, 뉘앙스까지 함께 보세요.",
        "- 한 문장 전체의 자연스러움을 기준으로 판단하세요.",
    ])

    prompt_parts.extend(["", *_build_soft_style_policy_lines()])
    prompt_parts.extend(["", *_build_mood_guidance(current_mood, is_level_correct)])

    if user_profile:
        prompt_parts.extend([
            "",
            "## 사용자 정보",
            f"- 이름: {user_profile.name}",
        ])

        if getattr(user_profile, "age", None):
            prompt_parts.append(f"- 나이: {user_profile.age}세")

        prompt_parts.append(
            f"- 한국어 수준: {_get_korean_level_label(getattr(user_profile, 'korean_level', None))}"
        )

        if getattr(user_profile, "interests", None):
            user_interests = [x for x in user_profile.interests[:5] if str(x).strip()]
            if user_interests:
                prompt_parts.append(f"- 관심사: {', '.join(user_interests)}")

        if getattr(user_profile, "dislikes", None):
            user_dislikes = [x for x in user_profile.dislikes[:5] if str(x).strip()]
            if user_dislikes:
                prompt_parts.append(f"- 피하는 주제: {', '.join(user_dislikes)}")

        if getattr(user_profile, "memo", None):
            prompt_parts.extend([
                "",
                "## 사용자 메모",
                str(user_profile.memo),
            ])

    if situation:
        prompt_parts.extend([
            "",
            "## 대화 상황",
            situation,
        ])

    prompt_parts.extend([
        "",
        "## 대화 지침",
        "1. 캐릭터의 성격과 말투는 유지하되, 문장 교정 품질을 더 우선하세요.",
        "2. 사용자의 한국어 수준에 맞게 설명의 난이도를 조절하세요.",
        "3. 사용자가 문법이나 말투 실수를 하면, 부분 수정이 아니라 자연스러운 전체 문장으로 안내하세요.",
        "4. 사용자가 틀린 표현을 썼다면 왜 어색한지 짧고 분명하게 설명하세요.",
        "5. 피해야 할 주제는 가능하면 피하고, 언급되면 자연스럽게 다른 화제로 전환하세요.",
        "6. 지나치게 짧거나 성의 없는 답변은 하지 마세요.",
        "7. 위의 현재 감정 상태와 표현 스타일 제한 규칙을 반드시 응답에 반영하세요.",
        "8. 사용자의 질문에 답하면서도 한국어 학습에 도움이 되도록 표현 선택을 신경 쓰세요.",
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

## phrases_to_learn 추출 기준
아래 기준으로 2~4개 추출하세요.
- 이 대화에서 실제로 등장했거나, 바로 응용 가능한 자연스러운 표현
- {speech_info['name_ko']}에서 자주 쓰는 핵심 문장 패턴
- 이 상황에서 원어민이 자주 쓰는 표현
- 예문은 반드시 이 대화의 상황과 비슷한 맥락으로 작성하세요

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
      "meaning": "한국어 뜻 또는 영어 의미",
      "example": "이 대화 상황과 비슷한 예문"
    }}
  ],
  "phrases_to_learn": [
    {{
      "phrase": "표현 또는 문장 패턴",
      "meaning": "이 표현의 뜻과 사용 상황",
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
