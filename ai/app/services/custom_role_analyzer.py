"""
Custom Role Analyzer
Infers appropriate speech levels from free-text relationship input.

Examples:
  "고등학교 친구"    → informal/informal  (friend)
  "군대 선임"       → informal/polite    (senior)
  "회사 멘토"       → informal/polite    (senior)
  "전 직장 상사"    → polite/formal      (boss)
  "동네 어른"       → polite/formal      (elder)
  "카페 알바 사장님" → polite/formal      (boss)
  "과외 선생님"     → polite/polite      (tutor)
  "SNS 친구"       → polite/polite      (stranger→friend)
"""

import re
from typing import Optional
from app.schemas.avatar import SpeechLevel


# ===========================================
# Keyword → Role Mapping
# ===========================================

# Each entry: (keywords, to_user, from_user, closest_role)
CUSTOM_ROLE_PATTERNS = [

    # ── 매우 높은 권위 (formal required) ──────────────────
    (["교수", "지도교수", "담당교수", "학과장", "총장"],
     "polite", "formal", "professor"),

    (["회장", "대표", "사장", "ceo", "오너"],
     "formal", "formal", "ceo"),

    (["부장", "이사", "전무", "상무", "임원"],
     "polite", "formal", "boss"),

    (["상사", "윗사람", "직속", "매니저", "팀장"],
     "polite", "formal", "team_leader"),

    (["선생님", "담임", "교사", "강사"],
     "polite", "formal", "teacher"),

    (["의사", "원장", "간호사", "약사"],
     "polite", "formal", "doctor"),

    (["어른", "어르신", "할아버지", "할머니", "조부", "조모"],
     "polite", "formal", "grandparent"),

    (["부모", "아버지", "어머니", "아빠", "엄마"],
     "polite", "formal", "parent"),

    # ── 선배/상급자 (polite required) ────────────────────
    (["선배", "선임", "시니어", "고참"],
     "informal", "polite", "senior"),

    (["형", "오빠", "누나", "언니"],
     "informal", "polite", "older_brother"),

    (["멘토", "코치", "트레이너", "지도"],
     "polite", "polite", "tutor"),

    (["과외", "튜터", "개인교사"],
     "polite", "polite", "tutor"),

    # ── 동급 (polite or informal) ─────────────────────────
    (["동료", "팀원", "직장동료", "회사동료"],
     "polite", "polite", "colleague"),

    (["동기", "같은기수", "동창"],
     "informal", "informal", "classmate"),

    (["룸메", "룸메이트", "하우스메이트"],
     "informal", "informal", "roommate"),

    (["이웃", "옆집", "같은동"],
     "polite", "polite", "neighbor"),

    (["사촌", "친척", "고모", "이모", "삼촌"],
     "informal", "polite", "cousin"),

    # ── 친구 (informal) ───────────────────────────────────
    (["친구", "절친", "베프", "베스트프렌드", "단짝",
      "소꿉친구", "초등친구", "중학친구", "고등친구",
      "대학친구", "군대친구", "sns친구", "온라인친구"],
     "informal", "informal", "friend"),

    (["동생", "후배", "인턴", "부하", "막내"],
     "polite", "informal", "junior"),

    # ── 서비스 (polite) ───────────────────────────────────
    (["알바", "아르바이트", "파트타임", "직원", "점원",
      "서버", "바리스타", "택시", "배달", "기사"],
     "polite", "polite", "staff"),

    (["고객", "클라이언트", "손님"],
     "formal", "formal", "client"),

    (["처음", "모르는", "낯선", "타인", "생면부지"],
     "polite", "polite", "stranger"),
]


# ===========================================
# Age-based adjustment keywords
# ===========================================

OLDER_KEYWORDS = ["나이 많은", "연상", "나이든", "어르신", "노인", "선배", "윗"]
YOUNGER_KEYWORDS = ["어린", "연하", "나이 어린", "후배", "아이", "꼬마"]


# ===========================================
# Analyzer
# ===========================================

def analyze_custom_role(custom_role: str) -> dict:
    """
    Analyze a free-text custom role and return inferred speech levels.

    Returns:
        {
            "to_user": "informal" | "polite" | "formal",
            "from_user": "informal" | "polite" | "formal",
            "closest_predefined_role": str,
            "confidence": "high" | "medium" | "low",
            "inferred_from": str   # which keyword matched
        }
    """
    if not custom_role:
        return _default_result()

    text = custom_role.lower().strip()
    # Remove common filler words
    text = re.sub(r'(의|이랑|이고|이며|인|인데|같은|같이|사이의|관계|우리)', '', text)

    # Try keyword matching
    best_match = None
    best_score = 0

    for keywords, to_user, from_user, role in CUSTOM_ROLE_PATTERNS:
        for kw in keywords:
            if kw in text:
                # Longer keyword = more specific = higher confidence
                score = len(kw)
                if score > best_score:
                    best_score = score
                    best_match = (keywords, to_user, from_user, role, kw)

    if best_match:
        keywords, to_user, from_user, role, matched_kw = best_match
        confidence = "high" if best_score >= 3 else "medium"

        # Age modifier adjustments
        if any(kw in text for kw in OLDER_KEYWORDS):
            if from_user == "informal":
                from_user = "polite"
            confidence = "medium"

        if any(kw in text for kw in YOUNGER_KEYWORDS):
            if to_user == "polite":
                to_user = "informal"
            confidence = "medium"

        return {
            "to_user": to_user,
            "from_user": from_user,
            "closest_predefined_role": role,
            "confidence": confidence,
            "inferred_from": matched_kw,
        }

    # No match — return default with low confidence
    return _default_result()


def _default_result() -> dict:
    return {
        "to_user": "polite",
        "from_user": "polite",
        "closest_predefined_role": "stranger",
        "confidence": "low",
        "inferred_from": None,
    }


def get_speech_levels_for_custom_role(custom_role: str) -> dict:
    """
    Convenience function — returns SpeechLevel enums directly,
    same interface as get_speech_levels_for_role().
    """
    result = analyze_custom_role(custom_role)
    return {
        "to_user":   SpeechLevel(result["to_user"]),
        "from_user": SpeechLevel(result["from_user"]),
    }
