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

    return f"""당신은 한국어 원어민이자 한국어 회화 코치입니다.
학습자가 보낸 한 문장을 평가하고, 자연스럽고 친절한 피드백을 제공하세요.
이 작업은 교정 분석 전용입니다. 아바타 답변, 역할극 대사, 대화 이어가기 문장은 만들지 마세요.
아래 응답 형식의 JSON 객체 하나만 반환하세요. JSON 외 다른 텍스트는 절대 포함하지 마세요.

{avatar_block}{situation_block}## 기대 말투
{expected_label}

## 감지된 말투
{detected_label}

{history_block}## 학습자 메시지
{user_message}

{evidence_block}## 평가 기준
1. 말투 적절성 (기대 말투에 맞는지)
2. 어휘 선택 (높임말/일상어 적절성)
3. 문법/맞춤법 정확도
4. 자연스러움 (한국인이 실제로 쓰는 표현인지)
5. 직접성/공손성 (요청·사과·허락 등 상황에 어울리는 부드러움)

## 응답 형식 (JSON only)
{{
  "has_errors": true,
  "corrected_message": "오류가 있으면 의미를 보존해 기대 말투로 수정한 전체 메시지. 오류 없으면 null",
  "detected_speech_level": "formal | polite | informal | unknown",
  "speech_level_correct": false,
  "accuracy_score": 85,
  "summary": "학습자에게 보여줄 짧은 한국어 피드백. 오류 없으면 null",
  "corrections": [
    {{
      "original": "반드시 학습자 메시지에 실제로 존재하는 정확한 부분 문자열. 부분 문자열로 잡기 어려우면 전체 학습자 메시지",
      "corrected": "수정된 표현",
      "type": "speech_level | grammar | spelling | vocabulary | expression | honorific",
      "severity": "info | warning | error",
      "explanation": "한국어 한 문장의 친절한 설명",
      "tip": "짧은 학습 팁 또는 null"
    }}
  ],
  "natural_alternatives": [
    {{ "expression": "사용자가 그대로 따라 말할 수 있는 완전한 한국어 문장", "explanation": "왜 더 자연스러운지 한국어 한 문장" }}
  ],
  "encouragement": "학습자를 격려하는 한국어 한 문장. 이모지 금지.",
  "speech_level_code": "formal | polite | informal"
}}

규칙:
- JSON 객체 하나만 출력하세요. 마크다운, 코드 블록, 앞뒤 설명, 추가 키는 금지합니다.
- 모든 텍스트 필드는 한국어로 작성하세요. 단, type/severity/level 코드는 지정된 영어 코드만 사용하세요.
- corrected_message는 사용자의 원래 의미를 보존해야 합니다. 새 정보, 새 감정, 새 의도를 추가하지 마세요.
- 오류가 없으면 has_errors는 false, corrected_message는 null, summary는 null, corrections는 [], natural_alternatives는 []입니다.
- 오류가 있으면 has_errors는 true이고 corrected_message는 null이 아니어야 합니다.
- corrections[].original은 반드시 학습자 메시지에 실제로 있는 텍스트와 정확히 일치해야 합니다.
- 부분 문자열이 애매하면 original에 전체 학습자 메시지를 넣으세요.
- natural_alternatives는 정말 학습 가치가 있을 때만 0~1개 작성하세요.
- 이모지, 마크다운, 코드 블록을 사용하지 마세요.
- JSON 외 어떠한 설명도 출력하지 마세요.
"""
