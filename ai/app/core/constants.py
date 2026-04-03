"""
Core constants for Talkativ AI
Topic taxonomy, formality levels, and mappings
"""

from typing import Dict, List, Any
from enum import Enum


# ===========================================
# Enums
# ===========================================

class FormailtyLevel(str, Enum):
    """Korean speech formality levels."""
    INFORMAL = "informal"       # 반말
    POLITE = "polite"          # 존댓말 (-요)
    VERY_POLITE = "very_polite" # 격식체 (-습니다)


class DifficultyLevel(str, Enum):
    """Conversation difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Role(str, Enum):
    """Social roles for hierarchy calculation."""
    JUNIOR = "junior"      # 후배
    FRIEND = "friend"      # 친구/동기
    SENIOR = "senior"      # 선배
    PROFESSOR = "professor" # 교수
    BOSS = "boss"          # 상사


# ===========================================
# Role Hierarchy
# ===========================================

ROLE_LEVELS: Dict[str, int] = {
    "junior": 0,
    "student": 0,
    "friend": 1,
    "peer": 1,
    "senior": 2,
    "professor": 3,
    "boss": 3,
}


# ===========================================
# Topic Taxonomy (15 categories)
# ===========================================

TOPIC_TAXONOMY: Dict[str, Dict[str, Any]] = {
    # Academic Topics
    "campus_life": {
        "name_ko": "대학생활",
        "name_en": "Campus Life",
        "keywords": ["학점", "중간고사", "기말고사", "동아리", "수강신청", "개강", "종강", "캠퍼스", "학생회", "축제", "MT"],
        "sensitive": False,
        "description": "General campus life and university activities"
    },
    "class_study": {
        "name_ko": "수업/과제",
        "name_en": "Class & Study",
        "keywords": ["과제", "레포트", "발표", "팀플", "조별과제", "수업", "강의", "시험", "공부", "필기", "출석"],
        "sensitive": False,
        "description": "Classes, assignments, and studying"
    },
    "professor_meeting": {
        "name_ko": "교수님 면담",
        "name_en": "Professor Meeting",
        "keywords": ["교수님", "면담", "상담", "연구실", "오피스아워", "추천서", "지도교수"],
        "sensitive": False,
        "description": "Meeting with professors"
    },
    
    # Work & Career Topics
    "part_time_job": {
        "name_ko": "아르바이트",
        "name_en": "Part-time Job",
        "keywords": ["알바", "시급", "근무", "사장님", "손님", "편의점", "카페알바", "과외"],
        "sensitive": False,
        "description": "Part-time work experiences"
    },
    "career_future": {
        "name_ko": "진로/취업",
        "name_en": "Career & Future",
        "keywords": ["취업", "진로", "인턴", "자소서", "면접", "이력서", "포트폴리오", "스펙"],
        "sensitive": False,
        "description": "Career planning and job hunting"
    },
    
    # Social Topics
    "friendship": {
        "name_ko": "친구관계",
        "name_en": "Friendship",
        "keywords": ["친구", "우정", "약속", "모임", "선배", "후배", "동기", "연락"],
        "sensitive": False,
        "description": "Friendships and social relationships"
    },
    "roommate": {
        "name_ko": "룸메이트/기숙사",
        "name_en": "Roommate & Dorm",
        "keywords": ["룸메", "룸메이트", "기숙사", "자취", "원룸", "층간소음", "청소"],
        "sensitive": False,
        "description": "Living arrangements and roommates"
    },
    
    # Daily Life Topics
    "daily_life": {
        "name_ko": "일상생활",
        "name_en": "Daily Life",
        "keywords": ["일상", "주말", "오늘", "어제", "내일", "요즘", "하루", "생활"],
        "sensitive": False,
        "description": "General daily life"
    },
    "weather": {
        "name_ko": "날씨",
        "name_en": "Weather",
        "keywords": ["날씨", "비", "눈", "더워", "추워", "햇살", "미세먼지", "장마"],
        "sensitive": False,
        "description": "Weather and seasons"
    },
    "cafe_food": {
        "name_ko": "카페/맛집",
        "name_en": "Cafe & Food",
        "keywords": ["카페", "맛집", "커피", "음식", "식당", "배달", "디저트", "브런치"],
        "sensitive": False,
        "description": "Food, cafes, and restaurants"
    },
    
    # Entertainment Topics
    "kpop": {
        "name_ko": "K-POP",
        "name_en": "K-POP",
        "keywords": ["아이돌", "컴백", "콘서트", "뮤비", "팬덤", "앨범", "팬미팅", "음방"],
        "sensitive": False,
        "description": "K-POP and idol culture"
    },
    "drama_movie": {
        "name_ko": "드라마/영화",
        "name_en": "Drama & Movie",
        "keywords": ["드라마", "영화", "넷플릭스", "시청", "배우", "예능", "유튜브"],
        "sensitive": False,
        "description": "TV shows and movies"
    },
    "museum_art": {
        "name_ko": "미술/전시",
        "name_en": "Museum & Art",
        "keywords": ["미술관", "전시", "갤러리", "작품", "예술", "사진전", "박물관"],
        "sensitive": False,
        "description": "Art and exhibitions"
    },
    
    # Sensitive Topics (to avoid)
    "politics": {
        "name_ko": "정치",
        "name_en": "Politics",
        "keywords": ["정치", "선거", "대통령", "국회", "여당", "야당"],
        "sensitive": True,
        "description": "Political topics - avoid"
    },
    "religion": {
        "name_ko": "종교",
        "name_en": "Religion",
        "keywords": ["종교", "교회", "절", "성당", "기도", "신앙"],
        "sensitive": True,
        "description": "Religious topics - avoid"
    },
}


# ===========================================
# Avatar Definitions
# ===========================================

AVATARS: Dict[str, Dict[str, Any]] = {
    "minsu_senior": {
        "id": "minsu_senior",
        "name_ko": "민수 선배",
        "name_en": "Minsu (Senior)",
        "role": "senior",
        "age": 26,
        "gender": "male",
        "personality": "친근하고 잘 도와주는 선배",
        "topics": ["campus_life", "class_study", "career_future", "friendship"],
        "difficulty": "medium",
        "formality": "polite",
        "greeting": "안녕! 오랜만이다. 요즘 어떻게 지내?",
        "voice_id": "nara",  # CLOVA Voice
    },
    "professor_kim": {
        "id": "professor_kim",
        "name_ko": "김 교수님",
        "name_en": "Professor Kim",
        "role": "professor",
        "age": 52,
        "gender": "male",
        "personality": "엄격하지만 학생들을 챙겨주시는 교수님",
        "topics": ["professor_meeting", "class_study", "career_future"],
        "difficulty": "hard",
        "formality": "very_polite",
        "greeting": "어서 오세요. 무슨 일로 왔나요?",
        "voice_id": "jinho",
    },
    "sujin_friend": {
        "id": "sujin_friend",
        "name_ko": "수진",
        "name_en": "Sujin (Friend)",
        "role": "friend",
        "age": 22,
        "gender": "female",
        "personality": "밝고 수다스러운 동기",
        "topics": ["daily_life", "cafe_food", "kpop", "drama_movie", "friendship"],
        "difficulty": "easy",
        "formality": "informal",
        "greeting": "야! 왔어? 뭐해?",
        "voice_id": "mijin",
    },
    "manager_lee": {
        "id": "manager_lee",
        "name_ko": "이 매니저님",
        "name_en": "Manager Lee",
        "role": "boss",
        "age": 35,
        "gender": "female",
        "personality": "바쁘지만 공정한 매니저",
        "topics": ["part_time_job", "career_future"],
        "difficulty": "hard",
        "formality": "very_polite",
        "greeting": "네, 무슨 일이에요?",
        "voice_id": "ara",
    },
    "jiwon_junior": {
        "id": "jiwon_junior",
        "name_ko": "지원",
        "name_en": "Jiwon (Junior)",
        "role": "junior",
        "age": 20,
        "gender": "male",
        "personality": "예의 바르고 질문이 많은 후배",
        "topics": ["campus_life", "class_study", "roommate"],
        "difficulty": "easy",
        "formality": "informal",
        "greeting": "선배님! 안녕하세요!",
        "voice_id": "nara",
    },
}


# ===========================================
# Formality Descriptions (for LLM prompts)
# ===========================================

FORMALITY_INSTRUCTIONS: Dict[str, str] = {
    "informal": """
반말을 사용하세요. 친한 친구나 후배와 대화하는 것처럼 편하게 말하세요.
- 문장 끝: ~어/아, ~지, ~냐, ~야
- 예: "뭐해?", "밥 먹었어?", "같이 가자"
""",
    "polite": """
존댓말(-요)을 사용하세요. 예의 바르지만 친근하게 말하세요.
- 문장 끝: ~요, ~세요, ~죠
- 예: "뭐 해요?", "밥 먹었어요?", "같이 가요"
""",
    "very_polite": """
격식체(-습니다)를 사용하세요. 매우 공손하게 말하세요.
- 문장 끝: ~습니다, ~습니까, ~십시오
- 높임말: 드리다, 여쭙다, 말씀, 뵙다
- 예: "무엇을 하십니까?", "식사하셨습니까?", "같이 가시겠습니까?"
""",
}


# ===========================================
# Politeness Detection Patterns
# ===========================================

ENDING_PATTERNS: Dict[str, List[str]] = {
    "very_polite": [
        r"습니다[.?!]?$",
        r"습니까[.?!]?$",
        r"십니다[.?!]?$",
        r"십시오[.?!]?$",
        r"옵니다[.?!]?$",
    ],
    "polite": [
        r"[아어]요[.?!]?$",
        r"세요[.?!]?$",
        r"죠[.?!]?$",
        r"네요[.?!]?$",
        r"군요[.?!]?$",
        r"거든요[.?!]?$",
    ],
    "informal": [
        r"[아어][.?!]?$",
        r"지[.?!]?$",
        r"냐[.?!]?$",
        r"니[.?!]?$",
        r"야[.?!]?$",
        r"래[.?!]?$",
    ],
}

HONORIFIC_WORDS: Dict[str, int] = {
    "드리다": 10, "여쭙다": 10, "여쭤": 10, "말씀": 10,
    "뵙다": 10, "뵈다": 10, "계시다": 10, "주무시다": 10,
    "혹시": 5, "실례": 5, "죄송": 5, "감사": 5,
}


# ===========================================
# Helper Functions
# ===========================================

def get_safe_topics() -> List[str]:
    """Return list of non-sensitive topic IDs."""
    return [tid for tid, info in TOPIC_TAXONOMY.items() if not info["sensitive"]]


def get_sensitive_topics() -> List[str]:
    """Return list of sensitive topic IDs."""
    return [tid for tid, info in TOPIC_TAXONOMY.items() if info["sensitive"]]


def get_avatar(avatar_id: str) -> Dict[str, Any]:
    """Get avatar by ID."""
    return AVATARS.get(avatar_id)


def get_formality_instruction(level: str) -> str:
    """Get formality instruction for LLM prompts."""
    return FORMALITY_INSTRUCTIONS.get(level, FORMALITY_INSTRUCTIONS["polite"])
