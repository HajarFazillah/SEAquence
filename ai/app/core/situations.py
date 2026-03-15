"""
Situation Constants
Predefined conversation situations for Korean practice
"""

from typing import Dict, Any, List


# ===========================================
# Situation Categories
# ===========================================

SITUATION_CATEGORIES = {
    "casual": {
        "name_ko": "일상",
        "name_en": "Casual",
        "description": "일상적인 대화 상황"
    },
    "service": {
        "name_ko": "서비스",
        "name_en": "Service",
        "description": "주문, 요청 등 서비스 상황"
    },
    "academic": {
        "name_ko": "학교",
        "name_en": "Academic",
        "description": "학교, 학업 관련 상황"
    },
    "professional": {
        "name_ko": "직장",
        "name_en": "Professional",
        "description": "직장, 업무 관련 상황"
    },
    "social": {
        "name_ko": "사교",
        "name_en": "Social",
        "description": "모임, 파티 등 사교 상황"
    },
}


# ===========================================
# Predefined Situations
# ===========================================

SITUATIONS: Dict[str, Dict[str, Any]] = {
    
    # ===== CASUAL (일상) =====
    "cafe_chat": {
        "situation_id": "cafe_chat",
        "name_ko": "카페에서 친구와 수다",
        "name_en": "Chatting with Friend at Cafe",
        "description_ko": "카페에서 친구와 편하게 이야기하는 상황",
        "category": "casual",
        "expected_formality": "casual",
        "location_ko": "카페",
        "location_en": "Cafe",
        "context_ko": "오랜만에 만난 친구와 카페에서 이야기를 나눕니다.",
        "goals_ko": ["근황 나누기", "일상 이야기", "약속 잡기"],
        "key_vocabulary": ["요즘", "바쁘다", "심심하다", "재밌다"],
        "key_expressions": ["요즘 어때?", "뭐 해?", "언제 볼까?"],
        "difficulty": "easy",
        "related_topics": ["daily_life", "friendship"],
        "tips_ko": ["친한 친구라면 반말을 써도 돼요", "감정을 자연스럽게 표현해 보세요"],
    },
    
    "campus_meetup": {
        "situation_id": "campus_meetup",
        "name_ko": "캠퍼스에서 선배 만남",
        "name_en": "Meeting Senior on Campus",
        "description_ko": "학교 캠퍼스에서 우연히 선배를 만난 상황",
        "category": "casual",
        "expected_formality": "polite",
        "location_ko": "대학교 캠퍼스",
        "location_en": "University Campus",
        "context_ko": "수업 끝나고 캠퍼스를 걷다가 선배를 만났습니다.",
        "goals_ko": ["인사하기", "안부 묻기", "조언 구하기"],
        "key_vocabulary": ["수업", "과제", "시험", "동아리"],
        "key_expressions": ["선배 안녕하세요!", "요즘 어떻게 지내세요?", "조언 좀 해주세요"],
        "difficulty": "medium",
        "related_topics": ["campus_life", "class_study"],
        "tips_ko": ["선배에게는 해요체를 사용하세요", "존경을 표현하면서도 자연스럽게"],
    },
    
    # ===== SERVICE (서비스) =====
    "cafe_order": {
        "situation_id": "cafe_order",
        "name_ko": "카페에서 주문하기",
        "name_en": "Ordering at Cafe",
        "description_ko": "카페에서 음료를 주문하는 상황",
        "category": "service",
        "expected_formality": "polite",
        "location_ko": "카페",
        "location_en": "Cafe",
        "context_ko": "카페에 들어가서 바리스타에게 음료를 주문합니다.",
        "goals_ko": ["음료 주문하기", "옵션 요청하기", "결제하기"],
        "key_vocabulary": ["아메리카노", "라떼", "샷 추가", "테이크아웃", "매장"],
        "key_expressions": [
            "아메리카노 한 잔 주세요",
            "샷 추가해 주세요",
            "카드로 할게요",
            "포장이요 / 매장이요"
        ],
        "difficulty": "easy",
        "related_topics": ["cafe_food", "shopping"],
        "tips_ko": ["주문할 때 '~주세요'를 사용하세요", "'감사합니다'로 마무리하면 좋아요"],
    },
    
    "restaurant_order": {
        "situation_id": "restaurant_order",
        "name_ko": "식당에서 주문하기",
        "name_en": "Ordering at Restaurant",
        "description_ko": "식당에서 음식을 주문하는 상황",
        "category": "service",
        "expected_formality": "polite",
        "location_ko": "식당",
        "location_en": "Restaurant",
        "context_ko": "식당에 들어가서 자리에 앉아 음식을 주문합니다.",
        "goals_ko": ["메뉴 보기", "추천 받기", "주문하기", "추가 요청"],
        "key_vocabulary": ["메뉴판", "추천", "덜 맵게", "리필", "계산"],
        "key_expressions": [
            "메뉴판 주세요",
            "뭐가 맛있어요?",
            "이거 하나 주세요",
            "물 좀 더 주세요",
            "계산할게요"
        ],
        "difficulty": "easy",
        "related_topics": ["cafe_food"],
        "tips_ko": ["'여기요!'로 직원을 부를 수 있어요", "음식이 나오면 '잘 먹겠습니다'"],
    },
    
    "shopping": {
        "situation_id": "shopping",
        "name_ko": "옷 가게에서 쇼핑",
        "name_en": "Shopping for Clothes",
        "description_ko": "옷 가게에서 옷을 고르고 구매하는 상황",
        "category": "service",
        "expected_formality": "polite",
        "location_ko": "옷 가게",
        "location_en": "Clothing Store",
        "context_ko": "옷 가게에서 마음에 드는 옷을 찾고 있습니다.",
        "goals_ko": ["사이즈 문의", "피팅룸 이용", "가격 확인", "결제"],
        "key_vocabulary": ["사이즈", "피팅룸", "할인", "교환", "환불"],
        "key_expressions": [
            "이거 다른 사이즈 있어요?",
            "입어봐도 돼요?",
            "얼마예요?",
            "카드 돼요?"
        ],
        "difficulty": "medium",
        "related_topics": ["shopping"],
        "tips_ko": ["'이거'로 가리키면서 물어보세요", "사이즈는 S, M, L 또는 '스몰', '미디엄', '라지'"],
    },
    
    # ===== ACADEMIC (학교) =====
    "professor_office": {
        "situation_id": "professor_office",
        "name_ko": "교수님 연구실 방문",
        "name_en": "Visiting Professor's Office",
        "description_ko": "교수님 연구실에서 면담하는 상황",
        "category": "academic",
        "expected_formality": "formal",
        "location_ko": "교수 연구실",
        "location_en": "Professor's Office",
        "context_ko": "과제나 진로에 대해 교수님과 상담하러 연구실을 방문합니다.",
        "goals_ko": ["인사드리기", "질문하기", "조언 구하기", "감사 인사"],
        "key_vocabulary": ["교수님", "상담", "과제", "진로", "추천서"],
        "key_expressions": [
            "교수님, 안녕하세요. 면담 왔습니다.",
            "여쭤볼 게 있어서요...",
            "조언 부탁드립니다",
            "감사합니다, 교수님"
        ],
        "difficulty": "hard",
        "related_topics": ["professor_meeting", "career_future"],
        "tips_ko": [
            "격식체(-습니다)를 사용하세요",
            "'여쭤보다'는 '묻다'의 높임말이에요",
            "문을 노크하고 허락을 받고 들어가세요"
        ],
    },
    
    "group_project": {
        "situation_id": "group_project",
        "name_ko": "조별 과제 회의",
        "name_en": "Group Project Meeting",
        "description_ko": "조원들과 과제에 대해 회의하는 상황",
        "category": "academic",
        "expected_formality": "polite",
        "location_ko": "도서관 / 카페",
        "location_en": "Library / Cafe",
        "context_ko": "조별 과제를 위해 팀원들과 만나 역할을 나누고 계획을 세웁니다.",
        "goals_ko": ["역할 분담", "의견 제시", "일정 조율", "합의하기"],
        "key_vocabulary": ["역할", "분담", "마감", "자료", "발표"],
        "key_expressions": [
            "저는 이 부분 할게요",
            "이건 어떨까요?",
            "마감이 언제예요?",
            "다음에 언제 만날까요?"
        ],
        "difficulty": "medium",
        "related_topics": ["class_study"],
        "tips_ko": ["동기에게는 해요체, 선배에게는 더 공손하게", "의견을 부드럽게 제시하세요"],
    },
    
    # ===== PROFESSIONAL (직장) =====
    "job_interview": {
        "situation_id": "job_interview",
        "name_ko": "취업 면접",
        "name_en": "Job Interview",
        "description_ko": "회사 면접을 보는 상황",
        "category": "professional",
        "expected_formality": "formal",
        "location_ko": "회사 회의실",
        "location_en": "Company Meeting Room",
        "context_ko": "취업을 위해 회사 면접을 봅니다.",
        "goals_ko": ["자기소개", "경험 설명", "질문에 답변", "질문하기"],
        "key_vocabulary": ["지원", "경력", "강점", "약점", "목표"],
        "key_expressions": [
            "안녕하십니까, 저는 ~입니다",
            "~한 경험이 있습니다",
            "제 강점은 ~입니다",
            "질문이 있으신가요?"
        ],
        "difficulty": "hard",
        "related_topics": ["career_future"],
        "tips_ko": [
            "최대한 격식체를 사용하세요",
            "자신감 있게 말하되 겸손하게",
            "면접관의 눈을 보며 말하세요"
        ],
    },
    
    "office_meeting": {
        "situation_id": "office_meeting",
        "name_ko": "회사 회의",
        "name_en": "Office Meeting",
        "description_ko": "직장 동료들과 회의하는 상황",
        "category": "professional",
        "expected_formality": "formal",
        "location_ko": "회의실",
        "location_en": "Meeting Room",
        "context_ko": "팀 회의에서 의견을 발표하고 논의합니다.",
        "goals_ko": ["의견 발표", "질문하기", "동의/반대 표현", "결론 정리"],
        "key_vocabulary": ["안건", "제안", "검토", "승인", "진행"],
        "key_expressions": [
            "제 의견을 말씀드리겠습니다",
            "이 부분에 대해 어떻게 생각하십니까?",
            "동의합니다",
            "다른 의견이 있습니다"
        ],
        "difficulty": "hard",
        "related_topics": ["career_future"],
        "tips_ko": ["직급에 따라 높임말 수준을 조절하세요", "논리적으로 명확하게 말하세요"],
    },
    
    # ===== SOCIAL (사교) =====
    "first_meeting": {
        "situation_id": "first_meeting",
        "name_ko": "처음 만나는 사람과 인사",
        "name_en": "Meeting Someone New",
        "description_ko": "처음 만나는 사람과 인사하고 소개하는 상황",
        "category": "social",
        "expected_formality": "polite",
        "location_ko": "다양한 장소",
        "location_en": "Various Places",
        "context_ko": "친구의 친구를 소개받거나 새로운 사람을 만납니다.",
        "goals_ko": ["자기소개", "상대방 알아가기", "공통점 찾기"],
        "key_vocabulary": ["처음", "반갑다", "이름", "직업", "취미"],
        "key_expressions": [
            "안녕하세요, 처음 뵙겠습니다",
            "저는 ~이에요/입니다",
            "만나서 반가워요",
            "무슨 일 하세요?"
        ],
        "difficulty": "easy",
        "related_topics": ["greeting", "friendship"],
        "tips_ko": ["처음에는 해요체로 시작하세요", "상대방이 반말을 제안하면 따라해도 돼요"],
    },
    
    "party": {
        "situation_id": "party",
        "name_ko": "파티/모임에서",
        "name_en": "At a Party/Gathering",
        "description_ko": "친구 모임이나 파티에서 대화하는 상황",
        "category": "social",
        "expected_formality": "mixed",
        "location_ko": "파티장 / 집",
        "location_en": "Party Venue / Home",
        "context_ko": "생일 파티나 친구 모임에서 여러 사람과 대화합니다.",
        "goals_ko": ["분위기 맞추기", "이야기 나누기", "게임 참여"],
        "key_vocabulary": ["축하", "건배", "게임", "놀자", "재밌다"],
        "key_expressions": [
            "생일 축하해!",
            "건배!",
            "뭐 하고 놀까?",
            "진짜 재밌다!"
        ],
        "difficulty": "medium",
        "related_topics": ["friendship", "hobby_free_time"],
        "tips_ko": ["분위기에 따라 반말/존댓말을 섞어 써요", "에너지 넘치게 말해 보세요"],
    },
}


# ===========================================
# Avatar-Situation Mappings
# ===========================================

AVATAR_SITUATIONS: Dict[str, List[Dict[str, Any]]] = {
    "sujin_friend": [
        {
            "situation_id": "cafe_chat",
            "avatar_role_ko": "오랜 친구",
            "avatar_role_en": "Old Friend",
            "opening_line": "야, 오랜만이야! 요즘 어떻게 지내?",
            "example_dialogues": [
                {"user": "수진아, 안녕! 나 요즘 너무 바빠.", "avatar": "왜? 무슨 일 있어?"},
                {"user": "과제가 너무 많아...", "avatar": "에이, 힘내! 같이 카페 가서 하자."}
            ]
        },
        {
            "situation_id": "party",
            "avatar_role_ko": "파티 친구",
            "avatar_role_en": "Party Friend",
            "opening_line": "왔어? 늦었잖아! 빨리 와!",
        },
    ],
    
    "minsu_senior": [
        {
            "situation_id": "campus_meetup",
            "avatar_role_ko": "캠퍼스에서 만난 선배",
            "avatar_role_en": "Senior on Campus",
            "opening_line": "어, 안녕! 수업 끝났어?",
            "example_dialogues": [
                {"user": "선배, 안녕하세요! 네, 방금 끝났어요.", "avatar": "그래? 나도 방금 끝났어. 커피 한 잔 할까?"},
            ]
        },
        {
            "situation_id": "group_project",
            "avatar_role_ko": "조별 과제 선배",
            "avatar_role_en": "Group Project Senior",
            "opening_line": "다 왔어? 그럼 시작하자. 역할 분담부터 하자.",
        },
    ],
    
    "professor_kim": [
        {
            "situation_id": "professor_office",
            "avatar_role_ko": "지도 교수님",
            "avatar_role_en": "Advisor Professor",
            "opening_line": "어서 오세요. 앉으세요. 무슨 일로 왔나요?",
            "example_dialogues": [
                {"user": "교수님, 안녕하세요. 진로 상담 때문에 왔습니다.", "avatar": "그래요. 어떤 고민이 있나요?"},
            ]
        },
    ],
    
    "hyunwoo_barista": [
        {
            "situation_id": "cafe_order",
            "avatar_role_ko": "친절한 바리스타",
            "avatar_role_en": "Friendly Barista",
            "opening_line": "어서 오세요! 주문하시겠어요?",
            "example_dialogues": [
                {"user": "아메리카노 한 잔 주세요.", "avatar": "네! 뜨거운 거요, 아이스요?"},
                {"user": "아이스로 할게요.", "avatar": "네, 아이스 아메리카노요. 4,500원입니다."},
            ]
        },
    ],
    
    "eunji_junior": [
        {
            "situation_id": "campus_meetup",
            "avatar_role_ko": "캠퍼스에서 만난 후배",
            "avatar_role_en": "Junior on Campus",
            "opening_line": "선배! 안녕하세요! 오랜만이에요!",
        },
        {
            "situation_id": "group_project",
            "avatar_role_ko": "조별 과제 후배",
            "avatar_role_en": "Group Project Junior",
            "opening_line": "선배, 저 이 부분 잘 모르겠어요. 도와주세요!",
        },
    ],
}


# ===========================================
# Helper Functions
# ===========================================

def get_situation(situation_id: str) -> Dict[str, Any]:
    """Get situation by ID."""
    return SITUATIONS.get(situation_id)


def get_situations_by_category(category: str) -> List[Dict[str, Any]]:
    """Get all situations in a category."""
    return [s for s in SITUATIONS.values() if s.get("category") == category]


def get_situations_for_avatar(avatar_id: str) -> List[Dict[str, Any]]:
    """Get all situations available for an avatar."""
    avatar_situations = AVATAR_SITUATIONS.get(avatar_id, [])
    return [
        {**SITUATIONS.get(s["situation_id"], {}), **s}
        for s in avatar_situations
        if s["situation_id"] in SITUATIONS
    ]


def get_avatar_situation(avatar_id: str, situation_id: str) -> Dict[str, Any]:
    """Get specific avatar-situation configuration."""
    avatar_situations = AVATAR_SITUATIONS.get(avatar_id, [])
    for s in avatar_situations:
        if s["situation_id"] == situation_id:
            return {**SITUATIONS.get(situation_id, {}), **s}
    return None
