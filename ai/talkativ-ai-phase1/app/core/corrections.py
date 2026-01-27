"""
Korean Politeness Corrections Database
Rules for converting between formality levels
"""

from typing import Dict, List, Tuple

# ===========================================
# Sentence Ending Corrections
# ===========================================

# Informal → Polite
INFORMAL_TO_POLITE: Dict[str, str] = {
    # 해요체 conversions
    "해": "해요",
    "가": "가요",
    "와": "와요",
    "봐": "봐요",
    "자": "자요",
    "먹어": "먹어요",
    "마셔": "마셔요",
    "있어": "있어요",
    "없어": "없어요",
    "알아": "알아요",
    "몰라": "몰라요",
    "좋아": "좋아요",
    "싫어": "싫어요",
    "했어": "했어요",
    "갔어": "갔어요",
    "왔어": "왔어요",
    "봤어": "봤어요",
    "먹었어": "먹었어요",
    "마셨어": "마셨어요",
    # Questions
    "뭐해": "뭐 해요",
    "어디가": "어디 가요",
    "왜": "왜요",
    "뭐야": "뭐예요",
    "누구야": "누구예요",
    # Imperatives
    "해줘": "해 주세요",
    "가줘": "가 주세요",
    "와줘": "와 주세요",
    "도와줘": "도와주세요",
}

# Polite → Formal (격식체)
POLITE_TO_FORMAL: Dict[str, str] = {
    # 합니다체 conversions
    "해요": "합니다",
    "가요": "갑니다",
    "와요": "옵니다",
    "봐요": "봅니다",
    "먹어요": "먹습니다",
    "마셔요": "마십니다",
    "있어요": "있습니다",
    "없어요": "없습니다",
    "알아요": "압니다",
    "몰라요": "모릅니다",
    "좋아요": "좋습니다",
    "싫어요": "싫습니다",
    "했어요": "했습니다",
    "갔어요": "갔습니다",
    "왔어요": "왔습니다",
    "봤어요": "봤습니다",
    "먹었어요": "먹었습니다",
    "마셨어요": "마셨습니다",
    # Questions
    "뭐 해요": "무엇을 하십니까",
    "어디 가요": "어디 가십니까",
    "뭐예요": "무엇입니까",
    "있어요?": "있습니까?",
    "없어요?": "없습니까?",
    # Requests
    "해 주세요": "해 주십시오",
    "가 주세요": "가 주십시오",
    "도와주세요": "도와주십시오",
    "알려주세요": "알려주십시오",
}

# Informal → Formal (direct)
INFORMAL_TO_FORMAL: Dict[str, str] = {
    "해": "합니다",
    "가": "갑니다",
    "와": "옵니다",
    "먹어": "먹습니다",
    "마셔": "마십니다",
    "있어": "있습니다",
    "없어": "없습니다",
    "알아": "압니다",
    "몰라": "모릅니다",
    "했어": "했습니다",
    "갔어": "갔습니다",
    "왔어": "왔습니다",
    "뭐해": "무엇을 하십니까",
    "해줘": "해 주십시오",
}

# ===========================================
# Honorific Verb Pairs
# ===========================================

# Regular verb → Honorific verb (when talking about/to superior)
HONORIFIC_VERBS: Dict[str, str] = {
    "먹다": "드시다/잡수시다",
    "먹어요": "드세요",
    "먹습니다": "드십니다",
    "마시다": "드시다",
    "마셔요": "드세요",
    "자다": "주무시다",
    "자요": "주무세요",
    "있다": "계시다",
    "있어요": "계세요",
    "있습니다": "계십니다",
    "말하다": "말씀하시다",
    "말해요": "말씀하세요",
    "주다": "드리다",
    "줘요": "드려요",
    "줍니다": "드립니다",
    "보다": "뵙다",
    "봐요": "뵈요",
    "봅니다": "뵙습니다",
    "묻다": "여쭙다",
    "물어요": "여쭤요",
    "물어봐요": "여쭤봐요",
    "죽다": "돌아가시다",
    "아프다": "편찮으시다",
}

# ===========================================
# Word Choice Corrections
# ===========================================

# Casual word → Formal/Polite word
WORD_FORMALITY: Dict[str, Dict[str, str]] = {
    "밥": {"polite": "식사", "formal": "진지"},
    "나이": {"polite": "연세", "formal": "연세"},
    "집": {"polite": "댁", "formal": "댁"},
    "말": {"polite": "말씀", "formal": "말씀"},
    "이름": {"polite": "성함", "formal": "성함"},
    "사람": {"polite": "분", "formal": "분"},
    "아빠": {"polite": "아버지", "formal": "아버님"},
    "엄마": {"polite": "어머니", "formal": "어머님"},
    "나": {"polite": "저", "formal": "저"},
    "우리": {"polite": "저희", "formal": "저희"},
}

# ===========================================
# Error Categories
# ===========================================

ERROR_CATEGORIES = {
    "ending_mismatch": {
        "name_ko": "어미 불일치",
        "name_en": "Ending Mismatch",
        "description": "Sentence ending doesn't match expected formality level",
        "severity": "high",
        "examples": ["있어요 → 있습니다 (to professor)"]
    },
    "honorific_missing": {
        "name_ko": "높임 표현 누락",
        "name_en": "Missing Honorific",
        "description": "Missing honorific marker (-시-) or honorific verb",
        "severity": "high",
        "examples": ["가요 → 가세요", "먹어요 → 드세요"]
    },
    "formality_mixed": {
        "name_ko": "격식 혼용",
        "name_en": "Mixed Formality",
        "description": "Mixing different formality levels in same sentence",
        "severity": "medium",
        "examples": ["교수님 뭐해? (honorific + informal)"]
    },
    "word_choice": {
        "name_ko": "단어 선택",
        "name_en": "Word Choice",
        "description": "Using casual word when formal word is expected",
        "severity": "low",
        "examples": ["밥 → 식사/진지", "나 → 저"]
    },
    "subject_marker": {
        "name_ko": "주격 조사",
        "name_en": "Subject Marker",
        "description": "Using wrong subject marker for politeness",
        "severity": "low",
        "examples": ["내가 → 제가"]
    },
    "tone_inappropriate": {
        "name_ko": "어조 부적절",
        "name_en": "Inappropriate Tone",
        "description": "Overall tone doesn't match the situation",
        "severity": "medium",
        "examples": ["Too casual with professor"]
    }
}

# ===========================================
# Helper Functions
# ===========================================

def get_correction(word: str, from_level: str, to_level: str) -> str:
    """Get corrected form of a word."""
    if from_level == "informal" and to_level == "polite":
        return INFORMAL_TO_POLITE.get(word)
    elif from_level == "polite" and to_level == "very_polite":
        return POLITE_TO_FORMAL.get(word)
    elif from_level == "informal" and to_level == "very_polite":
        return INFORMAL_TO_FORMAL.get(word)
    return None


def get_honorific_form(word: str) -> str:
    """Get honorific form of a verb."""
    return HONORIFIC_VERBS.get(word)


def get_formal_word(word: str, level: str = "polite") -> str:
    """Get more formal version of a word."""
    if word in WORD_FORMALITY:
        return WORD_FORMALITY[word].get(level)
    return None


def get_error_info(error_type: str) -> dict:
    """Get error category information."""
    return ERROR_CATEGORIES.get(error_type, {})
