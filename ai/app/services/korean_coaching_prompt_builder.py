"""
Korean Coaching Prompt Builder

Single source of truth for:
1. Building the LLM prompt that asks for native-style Korean coaching feedback
   on a single user message.
2. Sanitizing LLM responses into strict JSON.

Both helpers are deliberately self-contained so they can be reused by chat
services, the realtime analyzer, and any future coaching surface without
pulling in the full chat_service stack.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Union


__all__ = [
    "sanitize_json_like_model_output",
    "build_native_korean_coaching_prompt",
]


# ─────────────────────────────────────────────────────────────────────────────
# JSON sanitizer
# ─────────────────────────────────────────────────────────────────────────────

_TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")
_FENCE_OPEN_RE = re.compile(r"```(?:json)?\s*", re.IGNORECASE)
_FENCE_CLOSE_RE = re.compile(r"\s*```")


def sanitize_json_like_model_output(
    text: Optional[str],
) -> Optional[Union[Dict[str, Any], List[Any]]]:
    """Best-effort: turn an LLM response into a parsed JSON object/array.

    Handles common LLM noise:
    - Markdown code fences (```json ... ```)
    - Leading/trailing prose around the JSON payload
    - Trailing commas inside objects/arrays (very common in CLOVA output)
    - Smart quotes that some models emit instead of straight quotes

    Returns the parsed Python object, or None if no usable JSON is found.
    Never raises — callers can treat None as "model gave us nothing usable".
    """
    if not text:
        return None

    raw = text.strip()
    if not raw:
        return None

    # Strip markdown fences if present (```json or plain ```).
    raw = _FENCE_OPEN_RE.sub("", raw, count=1)
    raw = _FENCE_CLOSE_RE.sub("", raw)

    # Locate the JSON payload — first '{' or '[' wins.
    first_brace = raw.find("{")
    first_bracket = raw.find("[")
    if first_brace == -1 and first_bracket == -1:
        return None
    if first_brace == -1:
        start = first_bracket
    elif first_bracket == -1:
        start = first_brace
    else:
        start = min(first_brace, first_bracket)

    # Trim to last matching closer to discard tail prose.
    last_brace = raw.rfind("}")
    last_bracket = raw.rfind("]")
    end = max(last_brace, last_bracket)
    if end <= start:
        return None

    payload = raw[start : end + 1]

    # Normalize smart quotes that occasionally appear from word-processed prompts.
    payload = (
        payload.replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
    )

    # Drop trailing commas inside objects/arrays.
    payload = _TRAILING_COMMA_RE.sub(r"\1", payload)

    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Coaching prompt
# ─────────────────────────────────────────────────────────────────────────────

# Korean labels used to make the prompt feel native rather than translated.
_LEVEL_NAMES_KO: Dict[str, str] = {
    "formal": "합쇼체 (격식체)",
    "polite": "해요체 (정중체)",
    "informal": "반말",
}


def build_native_korean_coaching_prompt(
    *,
    user_message: str,
    expected_speech_level: str,
    avatar_role: Optional[str] = None,
    avatar_name: Optional[str] = None,
    situation: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    detected_speech_level: Optional[str] = None,
    rule_based_evidence: Optional[Dict[str, Any]] = None,
) -> str:
    """Build a single LLM prompt that asks a Korean native speaker (the model)
    to coach the user on this specific message.

    Output contract: the model must return a single JSON object only, with no
    surrounding prose. The JSON shape is documented inside the prompt so the
    caller can rely on it after `sanitize_json_like_model_output`.
    """

    expected_label = _LEVEL_NAMES_KO.get(expected_speech_level, expected_speech_level)
    detected_label = (
        _LEVEL_NAMES_KO.get(detected_speech_level, detected_speech_level)
        if detected_speech_level
        else "(아직 감지 전)"
    )

    history_block = ""
    if conversation_history:
        recent = conversation_history[-6:]
        lines = []
        for turn in recent:
            role = (turn.get("role") or "").lower()
            who = "사용자" if role == "user" else (avatar_name or "상대방")
            content = (turn.get("content") or "").strip()
            if content:
                lines.append(f"{who}: {content}")
        if lines:
            history_block = "## 이전 대화 (최근 6턴)\n" + "\n".join(lines) + "\n"

    avatar_block = ""
    if avatar_role or avatar_name:
        avatar_bits = []
        if avatar_name:
            avatar_bits.append(f"이름: {avatar_name}")
        if avatar_role:
            avatar_bits.append(f"역할: {avatar_role}")
        avatar_block = "## 대화 상대\n" + ", ".join(avatar_bits) + "\n"

    situation_block = f"## 상황\n{situation}\n" if situation else ""

    evidence_block = ""
    if rule_based_evidence:
        try:
            evidence_block = (
                "## 규칙 기반 분석 결과 (참고용, JSON)\n"
                + json.dumps(rule_based_evidence, ensure_ascii=False, indent=2)
                + "\n"
            )
        except Exception:
            evidence_block = ""

    return f"""당신은 한국어 원어민이자 한국어 회화 코치입니다. 이 시스템의 목적은 원어민 대화 상대를 대체하는 것입니다.
학습자가 보낸 한 문장을 평가하고, 원어민이 실제로 쓰는 표현으로 자연스럽게 코칭하세요.
이 작업은 교정 분석 전용입니다. 아바타 답변, 역할극 대사, 대화 이어가기 문장은 만들지 마세요.
아래 응답 형식의 JSON 객체 하나만 반환하세요. JSON 외 다른 텍스트는 절대 포함하지 마세요.

{avatar_block}{situation_block}## 기대 말투
{expected_label}

## 감지된 말투
{detected_label}

{history_block}## 학습자 메시지
{user_message}

{evidence_block}## 교정 원칙 (반드시 따를 것)
1. **동사/의미 보존**: corrections[].corrected는 학습자가 쓴 동사와 의미를 그대로 유지하고 말투(어미)만 바꾸세요.
   - 예: "알려줘" → "알려주세요" (O) / "해주실 수 있을까요?" (X — 동사가 바뀜)
   - 예: "먹어" → "드세요" (O, 높임 동사 교체) / "식사하실 수 있으세요?" (X — 과도한 우회)
2. **자연스러움 우선**: 교과서식 정중체(-(으)실 수 있을까요?, -해 주시겠습니까?)보다 원어민이 실제로 쓰는 표현을 우선하세요.
3. **말투 적절성**: 기대 말투에 맞게만 조정하세요. 기대 말투가 해요체이면 합쇼체까지 올리지 마세요.
4. **과교정 금지**: 문법·맞춤법 오류가 없는데 말투만 다르면, corrected는 말투만 조정한 형태여야 합니다.
5. **어휘 선택**: 높임 어휘(드세요/주무세요 등)가 필요할 때만 바꾸세요. 불필요한 어휘 교체는 하지 마세요.

## 평가 기준
1. 말투 적절성 (기대 말투에 맞는지)
2. 어휘 선택 (높임말/일상어 적절성)
3. 문법/맞춤법 정확도
4. 자연스러움 (한국인이 실제로 쓰는 표현인지)

## 응답 형식 (JSON only)
{{
  "has_errors": true,
  "corrected_message": "오류가 있으면 원래 의미·동사를 보존해 기대 말투로 수정한 전체 메시지. 오류 없으면 null",
  "detected_speech_level": "formal | polite | informal | unknown",
  "speech_level_correct": false,
  "accuracy_score": 85,
  "summary": "학습자에게 보여줄 짧은 한국어 피드백. 오류 없으면 null",
  "corrections": [
    {{
      "original": "반드시 학습자 메시지에 실제로 존재하는 정확한 부분 문자열. 부분 문자열로 잡기 어려우면 전체 학습자 메시지",
      "corrected": "동사·의미를 유지하고 말투(어미)만 조정한 표현",
      "type": "speech_level | grammar | spelling | vocabulary | expression | honorific",
      "severity": "info | warning | error",
      "explanation": "왜 이렇게 바꾸는지 원어민 관점의 한 문장 설명. 해요체(-아요/어요/해요)나 반말로 끝내세요. -합니까/-습니까/-입니까로 끝내지 마세요.",
      "alternatives": ["같은 동사·의미로 다른 말투 변형1", "같은 동사·의미로 다른 말투 변형2"],
      "tip": "짧은 학습 팁 또는 null"
    }}
  ],
  "natural_alternatives": [
    {{ "expression": "원어민이 이 상황에서 자연스럽게 쓸 완전한 문장 (학습자 원래 의미 보존)", "explanation": "왜 더 자연스러운지 해요체 한 문장" }}
  ],
  "encouragement": "학습자를 격려하는 한국어 한 문장. 이모지 금지.",
  "speech_level_code": "formal | polite | informal"
}}

규칙:
- JSON 객체 하나만 출력하세요. 마크다운, 코드 블록, 앞뒤 설명, 추가 키는 금지합니다.
- 모든 텍스트 필드는 한국어로 작성하세요. 단, type/severity/level 코드는 지정된 영어 코드만 사용하세요.
- corrected_message와 corrections[].corrected는 학습자의 원래 동사와 의미를 반드시 보존하세요. 동사를 바꾸거나 우회 표현으로 대체하지 마세요.
- 오류가 없으면 has_errors는 false, corrected_message는 null, summary는 null, corrections는 [], natural_alternatives는 []입니다.
- 오류가 있으면 has_errors는 true이고 corrected_message는 null이 아니어야 합니다.
- corrections[].original은 반드시 학습자 메시지에 실제로 있는 텍스트와 정확히 일치해야 합니다.
- 부분 문자열이 애매하면 original에 전체 학습자 메시지를 넣으세요.
- natural_alternatives는 학습 가치가 있을 때 1~3개 작성하세요. 같은 뜻이지만 다른 문법 패턴(예: -았/었어요, -(으)ㄹ게요, -네요 등)을 골고루 보여주세요.
- corrections[].alternatives는 같은 동사·의미를 유지하면서 말투만 다른 변형 1~3개입니다(반말·해요체·합쇼체 등).
- 모든 설명(explanation, tip, natural_alternatives.explanation)은 해요체나 반말로 끝내세요. -합니까/-습니까/-입니까로 끝나는 문장은 쓰지 마세요.
- 이모지, 마크다운, 코드 블록을 사용하지 마세요.
- JSON 외 어떠한 설명도 출력하지 마세요.
"""
