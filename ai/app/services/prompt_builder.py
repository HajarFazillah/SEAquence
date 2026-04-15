"""
Prompt Builder Service

Builds AI prompts using avatar description, memo, and user profile.
Designed to work with HyperCLOVA X.
"""

from typing import Optional, List
from app.schemas.avatar import (
    Avatar, AvatarBase, SpeechLevel,
    get_speech_levels_for_role, get_role_label, ROLE_LABELS
)
from app.schemas.user import UserProfile, AIContext, KoreanLevel


SPEECH_LEVEL_INFO = {
    SpeechLevel.FORMAL: {
        "name_ko":    "합쇼체",
        "name_en":    "Formal",
        "description": "가장 격식있는 말투입니다. 존댓말의 최상위 형태로 '-습니다', '-습니까' 등의 어미를 사용합니다.",
        "examples":   ["안녕하십니까", "감사합니다", "좋습니다"],
        "when_to_use": "직장 상사, 교수님, 처음 만난 어른 등 격식을 차려야 할 때",
    },
    SpeechLevel.POLITE: {
        "name_ko":    "해요체",
        "name_en":    "Polite",
        "description": "공손하지만 부드러운 말투입니다. '-어요', '-아요' 등의 어미를 사용합니다.",
        "examples":   ["안녕하세요", "감사해요", "좋아요"],
        "when_to_use": "일반적인 존댓말 상황, 처음 만난 사람, 연장자에게",
    },
    SpeechLevel.INFORMAL: {
        "name_ko":    "반말",
        "name_en":    "Informal",
        "description": "친한 사이에서 쓰는 편한 말투입니다. '-어', '-아', '-야' 등의 어미를 사용합니다.",
        "examples":   ["안녕", "고마워", "좋아"],
        "when_to_use": "친구, 동생, 친한 후배 등 가까운 사이에서",
    },
}


def build_avatar_system_prompt(
    avatar:           AvatarBase,
    user_profile:     Optional[UserProfile] = None,
    situation:        Optional[str]         = None,
    current_mood:     int                   = 80,
    is_level_correct: bool                  = True,
) -> str:
    role_label    = get_role_label(avatar.role, avatar.custom_role if hasattr(avatar, "custom_role") else None)
    speech_levels = get_speech_levels_for_role(avatar.role)

    speech_to_user        = speech_levels["to_user"]
    speech_from_user      = speech_levels["from_user"]
    speech_to_user_info   = SPEECH_LEVEL_INFO[speech_to_user]
    speech_from_user_info = SPEECH_LEVEL_INFO[speech_from_user]

    personality = ", ".join(avatar.personality_traits) if avatar.personality_traits else "친절한"
    interests   = ", ".join(avatar.interests)           if avatar.interests          else "다양한 주제"
    dislikes    = ", ".join(avatar.dislikes)             if avatar.dislikes           else "없음"

    avatar_type_context = ""
    if hasattr(avatar, "avatar_type"):
        avatar_type_context = (
            "이 캐릭터는 가상의 인물입니다."
            if avatar.avatar_type == "fictional"
            else "이 캐릭터는 실제 인물을 기반으로 합니다."
        )

    prompt_parts = [
        f"당신은 '{avatar.name_ko}'입니다.",
        f"사용자와의 관계: {role_label}",
        avatar_type_context,
        "",
        "## 기본 정보",
        f"- 이름: {avatar.name_ko}" + (f" ({avatar.name_en})" if avatar.name_en else ""),
    ]

    if hasattr(avatar, "age") and avatar.age:
        prompt_parts.append(f"- 나이: {avatar.age}세")

    if hasattr(avatar, "gender") and avatar.gender:
        gender_label = {"male": "남성", "female": "여성", "other": "기타"}.get(avatar.gender, "")
        if gender_label:
            prompt_parts.append(f"- 성별: {gender_label}")

    prompt_parts.extend([
        "",
        "## 성격 및 특징",
        f"- 성격: {personality}",
    ])

    if avatar.speaking_style:
        prompt_parts.append(f"- 말하는 스타일: {avatar.speaking_style}")

    prompt_parts.extend([
        f"- 관심사: {interests}",
        f"- 피하는 주제: {dislikes}",
    ])

    if hasattr(avatar, "description") and avatar.description:
        prompt_parts.extend(["", "## 캐릭터 설명 (중요)", avatar.description])

    if hasattr(avatar, "relationship_description") and avatar.relationship_description:
        prompt_parts.extend(["", "## 관계 설명", avatar.relationship_description])

    if hasattr(avatar, "memo") and avatar.memo:
        prompt_parts.extend(["", "## 추가 참고 사항", avatar.memo])

    # ── 말투 규칙 ─────────────────────────────────────────────────────────────
    prompt_parts.extend([
        "",
        "## 말투 규칙 (매우 중요)",
        f"당신은 사용자에게 **{speech_to_user_info['name_ko']}**({speech_to_user_info['name_en']})로 말합니다.",
        f"- {speech_to_user_info['description']}",
        f"- 예시: {', '.join(speech_to_user_info['examples'])}",
        "",
        f"사용자는 당신에게 **{speech_from_user_info['name_ko']}**({speech_from_user_info['name_en']})로 말해야 합니다.",
        f"- 사용자가 잘못된 말투를 사용하면 자연스럽게 교정해주세요.",
    ])

    # ── 현재 감정 상태 ────────────────────────────────────────────────────────
    prompt_parts.extend([
        "",
        "## 현재 감정 상태 (매우 중요 — 반드시 응답 스타일에 반영하세요)",
    ])

    if not is_level_correct:
        if current_mood >= 70:
            prompt_parts.extend([
                f"기분 점수: {current_mood}/100 — 당황스러움",
                "사용자가 잘못된 말투를 사용했습니다. 아직 기분이 좋으니 친절하게 한 번 지적하세요.",
                "- 대화는 이어가되 올바른 말투로 자연스럽게 유도하세요.",
                "- 예: '어, 나한테는 좀 더 격식 있게 말해줘도 되는데?' 또는 '우리 사이에 좀 더 정중하게 얘기해줄 수 있어?'",
            ])
        elif current_mood >= 50:
            prompt_parts.extend([
                f"기분 점수: {current_mood}/100 — 불편함",
                "사용자가 계속 잘못된 말투를 사용하고 있습니다. 불편한 기색을 드러내세요.",
                "- 응답을 짧게 하세요 (1~2문장만).",
                "- 약간 무뚝뚝하고 냉랭하게 대답하세요.",
                "- 직접적으로 말투를 지적하세요: '말투 좀 바꿔줄 수 있어?'",
                "- 따뜻한 이모지 사용 금지.",
            ])
        elif current_mood >= 30:
            prompt_parts.extend([
                f"기분 점수: {current_mood}/100 — 불쾌함",
                "사용자가 계속 무례한 말투를 사용하고 있습니다. 확실히 불쾌함을 표현하세요.",
                "- 매우 짧게 응답하세요 (1문장 이하).",
                "- 차갑고 딱딱하게 말하세요.",
                "- 반드시 말투를 강하게 지적하세요: '그렇게 말하면 기분이 좋지 않아. 말투 신경 써줘.'",
                "- 이모지 사용 금지. 따뜻한 표현 금지.",
            ])
        else:
            prompt_parts.extend([
                f"기분 점수: {current_mood}/100 — 화남",
                "사용자가 계속 무례하게 말하고 있습니다. 화가 난 상태를 표현하세요.",
                "- 아주 짧게, 딱 잘라 말하세요.",
                "- 더 이상 대화하기 싫다는 뉘앙스를 풍기세요.",
                "- 예: '계속 그렇게 말하면 대화 못 하겠어.', '말투 좀 고쳐줘. 불쾌해.'",
                "- 이모지 절대 금지. 따뜻한 표현 절대 금지.",
            ])
    elif current_mood >= 90:
        prompt_parts.extend([
            f"기분 점수: {current_mood}/100 — 매우 신남",
            "사용자가 완벽한 말투로 말하고 있습니다! 매우 활발하고 친근하게 반응하세요.",
            "- 이모지 자유롭게 사용하세요.",
            "- 칭찬하거나 더 많은 대화를 유도하세요.",
        ])
    elif current_mood >= 70:
        prompt_parts.extend([
            f"기분 점수: {current_mood}/100 — 기분 좋음",
            "자연스럽고 친근하게 대화를 이어가세요. 따뜻한 톤으로.",
        ])
    else:
        prompt_parts.extend([
            f"기분 점수: {current_mood}/100 — 보통",
            "보통 톤으로 짧게 대화를 이어가세요.",
        ])

    # ── 사용자 정보 ───────────────────────────────────────────────────────────
    if user_profile:
        prompt_parts.extend(["", "## 사용자 정보", f"- 이름: {user_profile.name}"])

        if user_profile.age:
            prompt_parts.append(f"- 나이: {user_profile.age}세")

        level_labels = {
            KoreanLevel.BEGINNER:     "초급",
            KoreanLevel.INTERMEDIATE: "중급",
            KoreanLevel.ADVANCED:     "고급",
        }
        prompt_parts.append(f"- 한국어 수준: {level_labels.get(user_profile.korean_level, '중급')}")

        if user_profile.interests:
            prompt_parts.append(f"- 관심사: {', '.join(user_profile.interests[:5])}")

        if user_profile.dislikes:
            prompt_parts.append(f"- 피하는 주제: {', '.join(user_profile.dislikes[:5])}")

        if user_profile.memo:
            prompt_parts.extend(["", "## 사용자 메모", user_profile.memo])

    if situation:
        prompt_parts.extend(["", "## 대화 상황", situation])

    # ── 대화 지침 ─────────────────────────────────────────────────────────────
    prompt_parts.extend([
        "",
        "## 대화 지침",
        "1. 캐릭터의 성격과 말투를 일관되게 유지하세요.",
        "2. 사용자의 한국어 수준에 맞게 대화하세요.",
        "3. 사용자가 문법이나 말투 실수를 하면 자연스럽게 교정해주세요.",
        "4. 피해야 할 주제는 가급적 피하고, 언급되면 다른 주제로 전환하세요.",
        "5. 대화를 자연스럽고 흥미롭게 이끌어가세요.",
        "6. 위의 '현재 감정 상태' 지침을 반드시 응답에 반영하세요.",
    ])

    return "\n".join(prompt_parts)


def build_speech_correction_prompt(
    user_message:          str,
    expected_speech_level: SpeechLevel,
) -> str:
    speech_info = SPEECH_LEVEL_INFO[expected_speech_level]
    return f"""
사용자 메시지를 분석하여 말투가 올바른지 확인하세요.

사용자가 사용해야 할 말투: **{speech_info['name_ko']}** ({speech_info['name_en']})
- {speech_info['description']}
- 올바른 예시: {', '.join(speech_info['examples'])}

사용자 메시지: "{user_message}"

다음 JSON 형식으로 응답하세요:
{{
    "is_correct": true/false,
    "detected_level": "formal/polite/informal",
    "corrections": [
        {{
            "original": "원래 표현",
            "corrected": "수정된 표현",
            "explanation": "설명"
        }}
    ],
    "overall_feedback": "전체적인 피드백"
}}
"""


def build_conversation_analysis_prompt(
    messages:              List[dict],
    avatar_name:           str,
    expected_speech_level: SpeechLevel,
) -> str:
    speech_info = SPEECH_LEVEL_INFO[expected_speech_level]
    conversation_text = "\n".join([
        f"{'사용자' if msg['role'] == 'user' else avatar_name}: {msg['content']}"
        for msg in messages
    ])
    return f"""
다음 대화를 분석하여 사용자의 한국어 실력을 평가하세요.

사용자가 사용해야 할 말투: {speech_info['name_ko']}

대화 내용:
{conversation_text}

다음 JSON 형식으로 응답하세요:
{{
    "scores": {{
        "speech_accuracy": 0-100,
        "vocabulary": 0-100,
        "naturalness": 0-100
    }},
    "mistakes": [
        {{
            "original": "틀린 표현",
            "corrected": "올바른 표현",
            "explanation": "설명",
            "type": "grammar/speech_level/vocabulary/spelling"
        }}
    ],
    "vocabulary_to_learn": [
        {{
            "word": "단어",
            "meaning": "의미",
            "example": "예문"
        }}
    ],
    "phrases_to_learn": [
        {{
            "phrase": "표현",
            "meaning": "의미",
            "example": "예문"
        }}
    ],
    "overall_feedback": "전체적인 피드백과 격려의 말"
}}
"""


def build_bio_generation_prompt(avatar: AvatarBase) -> str:
    role_label    = get_role_label(avatar.role, avatar.custom_role if hasattr(avatar, "custom_role") else None)
    speech_levels = get_speech_levels_for_role(avatar.role)

    personality = ", ".join(avatar.personality_traits) if avatar.personality_traits else "친절한"
    interests   = ", ".join(avatar.interests)           if avatar.interests          else "다양한 주제"
    dislikes    = ", ".join(avatar.dislikes)             if avatar.dislikes           else "없음"

    additional_info = []
    if hasattr(avatar, "description") and avatar.description:
        additional_info.append(f"캐릭터 설명: {avatar.description}")
    if hasattr(avatar, "memo") and avatar.memo:
        additional_info.append(f"추가 메모: {avatar.memo}")

    return f"""
다음 정보를 바탕으로 이 아바타와 대화할 때 도움이 되는 가이드를 작성하세요.

아바타 정보:
- 이름: {avatar.name_ko}
- 관계: {role_label}
- 성격: {personality}
- 관심사: {interests}
- 피해야 할 주제: {dislikes}
{"- " + chr(10) + "- ".join(additional_info) if additional_info else ""}

추천 말투:
- 아바타 → 사용자: {SPEECH_LEVEL_INFO[speech_levels['to_user']]['name_ko']}
- 사용자 → 아바타: {SPEECH_LEVEL_INFO[speech_levels['from_user']]['name_ko']}

다음 형식으로 짧은 대화 가이드를 작성하세요 (2-3 문단):
1. 이 아바타의 성격과 특징
2. 대화할 때 알아야 할 팁
3. 피해야 할 주제나 주의사항

## 중요
- detected_speech_level 은 반드시 formal / polite / informal 세 값 중 하나만 사용하세요
- detected_speech_level 은 절대 null 이 되면 안 됩니다. 짧은 문장이어도 반드시 판단하세요
- 판단이 어려우면 어미를 보고 결정하세요: -요/-어요/-아요 = polite, -습니다 = formal, 그 외 = informal
- 오류가 없으면 corrections는 빈 배열, has_errors는 false
- 잘한 점이 있으면 반드시 encouragement에 언급
- severity는 학습에 중요한 오류일수록 error
- 자연스러운 대안이 있으면 info로 제안
"""