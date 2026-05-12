"""
Speech Analysis Service

Unified entry point for analyzing a single user Korean message. Wraps the
rule-based `simple_speech_analyzer` and exposes a stable, dict-based contract
that callers (chat_service, realtime, API endpoints) can depend on without
importing analyzer internals.

Design goals:
- Single function (`analyze_user_korean_message`) covers the common path.
- Output is JSON-serializable so it can be embedded in LLM prompts or sent
  over the wire untouched.
- No external network calls; this is the deterministic layer that runs before
  any optional LLM coaching pass.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.simple_speech_analyzer import (
    ConversationContext,
    NativeSpeechAnalyzer,
    analyzer as _default_analyzer,
    infer_intent,
    detect_spelling,
    normalize_text,
    _result_to_dict,  # type: ignore
)


__all__ = [
    "analyze_user_korean_message",
    "analyze_politeness_compat",
]


def _conversation_context_from(
    *,
    avatar_role: Optional[str],
    situation: Optional[str],
    inferred_intent: Optional[str],
    relationship: Optional[str],
    closeness: Optional[int],
    age_gap: Optional[int],
    is_public: bool,
    user_goal: Optional[str],
) -> ConversationContext:
    return ConversationContext(
        avatar_role=avatar_role,
        relationship=relationship,
        situation=situation,
        speech_act=inferred_intent,
        age_gap=age_gap,
        closeness=closeness if closeness is not None else 3,
        is_public=is_public,
        user_goal=user_goal,
    )


def analyze_user_korean_message(
    *,
    message: str,
    expected_speech_level: Optional[str] = None,
    avatar_role: Optional[str] = None,
    situation: Optional[str] = None,
    relationship: Optional[str] = None,
    closeness: Optional[int] = None,
    age_gap: Optional[int] = None,
    is_public: bool = False,
    user_goal: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    analyzer: Optional[NativeSpeechAnalyzer] = None,
) -> Dict[str, Any]:
    """Run the full deterministic analysis on `message`.

    Returns a dict with:
    - `normalized`: whitespace-collapsed text (also useful for downstream LLM input)
    - `inferred_intent`: heuristically inferred speech act (request/apology/...)
    - `spelling`: list of spelling/typo hits with original/expected pairs
    - `analysis`: full appropriateness report (level, errors, suggestions, score)

    `conversation_history` is currently used only to enrich the inferred intent
    (e.g. distinguishing a follow-up answer from a new request). Pass the most
    recent ~6 turns for best results.
    """
    if not message or not message.strip():
        return {
            "normalized": "",
            "inferred_intent": None,
            "spelling": [],
            "analysis": None,
        }

    active_analyzer = analyzer or _default_analyzer

    normalized = normalize_text(message)
    intent = infer_intent(normalized, conversation_history=conversation_history)
    spelling_hits = detect_spelling(normalized)

    context = _conversation_context_from(
        avatar_role=avatar_role,
        situation=situation,
        inferred_intent=intent,
        relationship=relationship,
        closeness=closeness,
        age_gap=age_gap,
        is_public=is_public,
        user_goal=user_goal,
    )

    raw_result = active_analyzer.check_contextual_appropriateness(normalized, context)

    if expected_speech_level:
        # Normalize "very_polite" alias used elsewhere in the system.
        raw_result.expected_level = expected_speech_level.replace("very_polite", "formal")

    analysis_dict = _result_to_dict(raw_result)
    # Surface the helpers' findings on the unified result too, so callers don't
    # need to re-run them.
    analysis_dict["normalized"] = normalized
    analysis_dict["inferred_intent"] = intent
    analysis_dict["spelling"] = spelling_hits

    return {
        "normalized": normalized,
        "inferred_intent": intent,
        "spelling": spelling_hits,
        "analysis": analysis_dict,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Backwards-compat shim for the retired politeness_service
# ─────────────────────────────────────────────────────────────────────────────
#
# The legacy `politeness_service.analyze(...)` returned a flat dict with these
# keys: level, level_ko, level_en, score, is_appropriate, recommended_level,
# feedback_ko, feedback_en, details. Several API endpoints and one service
# consume that exact shape, so we expose an adapter that uses the new analyzer
# under the hood while preserving the old contract.

_LEVEL_TO_LEGACY: Dict[str, str] = {
    "formal": "very_polite",
    "polite": "polite",
    "informal": "informal",
    "unknown": "polite",
}

_LEGACY_LEVEL_NAMES: Dict[str, tuple] = {
    "informal":    ("반말",   "Informal"),
    "polite":      ("존댓말", "Polite"),
    "very_polite": ("격식체", "Formal/Very Polite"),
}


def analyze_politeness_compat(
    text: str,
    target_role: Optional[str] = None,
    target_age: Optional[int] = None,
    user_age: int = 22,
) -> Dict[str, Any]:
    """Drop-in replacement for the legacy ``politeness_service.analyze``.

    Returns a dict with the same keys old callers expect. Powered by the new
    `analyze_user_korean_message` so we don't duplicate analysis logic.
    """
    age_gap = (target_age - user_age) if (target_age is not None) else None

    result = analyze_user_korean_message(
        message=text,
        avatar_role=target_role,
        age_gap=age_gap,
    )

    analysis = result.get("analysis") or {}
    detected_level = analysis.get("speech_level") or "unknown"
    legacy_level = _LEVEL_TO_LEGACY.get(detected_level, "polite")
    name_ko, name_en = _LEGACY_LEVEL_NAMES.get(legacy_level, ("존댓말", "Polite"))

    expected_level = analysis.get("expected_level") or "polite"
    legacy_recommended = _LEVEL_TO_LEGACY.get(expected_level, expected_level)

    return {
        "level": legacy_level,
        "level_ko": name_ko,
        "level_en": name_en,
        "score": int(analysis.get("score") or 0),
        "is_appropriate": analysis.get("is_appropriate"),
        "recommended_level": legacy_recommended if target_role else None,
        "feedback_ko": analysis.get("feedback_ko"),
        "feedback_en": analysis.get("feedback_en"),
        "details": {
            "level_counts": {legacy_level: 1},
            "endings_found": [],
            "honorifics_found": [],
            "honorific_score": 0,
            "inferred_intent": result.get("inferred_intent"),
            "spelling": result.get("spelling") or [],
            "word_errors": analysis.get("word_errors") or [],
            "missing_honorifics": analysis.get("missing_honorifics") or [],
            "directness_errors": analysis.get("directness_errors") or [],
            "corrections": [
                {
                    "original": item.get("original", ""),
                    "corrected": item.get("expected") or item.get("corrected", ""),
                    "explanation": item.get("explanation", ""),
                }
                for item in (analysis.get("word_errors") or []) + (analysis.get("missing_honorifics") or [])
            ],
        },
    }
