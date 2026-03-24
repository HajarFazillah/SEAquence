"""
Speech Level Calculator v2 - Enhanced Edition

Sophisticated rule-based system for calculating Korean speech levels.

⚠️ THIS IS NOT MACHINE LEARNING ⚠️

This is a deterministic weighted scoring system based on Korean social norms.
Every decision can be explained - important for language learning!

Total Factors: 25

BASIC FACTORS (1-5):
1. Role/Relationship (관계)
2. Age Difference (나이 차이)
3. Closeness (친밀도)
4. Social Status (사회적 지위)
5. Context/Setting (상황)

RELATIONSHIP FACTORS (6-10):
6. First Meeting (첫 만남)
7. Years Known (알고 지낸 기간)
8. How You Met (만난 경위)
9. Relationship Trajectory (관계 변화)
10. Mutual Friends (공통 지인)

PROFESSIONAL FACTORS (11-15):
11. Position Level (직급)
12. Company Culture (회사 문화)
13. Industry Type (업계)
14. Client Relationship (갑을 관계)
15. Project Hierarchy (프로젝트 역할)

SITUATIONAL FACTORS (16-20):
16. Public vs Private (공공/사적)
17. Being Observed (관찰 상황)
18. Alcohol Context (술자리)
19. Online vs Offline (온라인/오프라인)
20. Topic Sensitivity (주제 민감도)

CULTURAL FACTORS (21-25):
21. Regional Culture (지역 문화)
22. Generation Gap (세대 차이)
23. Military Background (군대 경험)
24. Family Side (친가/외가)
25. Cultural Background (문화적 배경)
"""

from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from pydantic import BaseModel, Field
from dataclasses import dataclass


# ============================================================================
# Enums - All Factor Options
# ============================================================================

class SpeechLevel(str, Enum):
    """Korean speech levels (from most formal to least)"""
    FORMAL = "formal"      # 합쇼체 (-습니다, -습니까)
    POLITE = "polite"      # 해요체 (-어요, -아요)
    INFORMAL = "informal"  # 반말 (-어, -야)


class Closeness(str, Enum):
    """Factor 3: How close the relationship is (친밀도)"""
    JUST_MET = "just_met"           # 처음 만남
    STRANGER = "stranger"           # 모르는 사람
    ACQUAINTANCE = "acquaintance"   # 아는 사이
    FRIENDLY = "friendly"           # 친한 편
    CLOSE = "close"                 # 친함
    VERY_CLOSE = "very_close"       # 매우 친함 (반말 허용)
    INTIMATE = "intimate"           # 아주 가까움 (연인, 절친)


class SocialStatus(str, Enum):
    """Factor 4: Relative social status (사회적 지위)"""
    MUCH_LOWER = "much_lower"
    LOWER = "lower"
    EQUAL = "equal"
    HIGHER = "higher"
    MUCH_HIGHER = "much_higher"


class Context(str, Enum):
    """Factor 5: Social context/setting (상황)"""
    VERY_FORMAL = "very_formal"     # 면접, 공식 행사
    FORMAL = "formal"               # 회의, 업무
    PROFESSIONAL = "professional"   # 일반 직장
    NEUTRAL = "neutral"             # 보통 상황
    CASUAL = "casual"               # 편한 상황
    INTIMATE = "intimate"           # 사적인 공간


class HowMet(str, Enum):
    """Factor 8: How you met (만난 경위)"""
    INTRODUCED_FORMAL = "introduced_formal"   # 공식적으로 소개받음
    INTRODUCED_CASUAL = "introduced_casual"   # 친구 통해 소개
    WORK = "work"                             # 업무로 만남
    SCHOOL = "school"                         # 학교에서 만남
    ONLINE = "online"                         # 온라인에서 만남
    RANDOM = "random"                         # 우연히 만남
    FAMILY_EVENT = "family_event"             # 가족 행사


class RelationshipTrajectory(str, Enum):
    """Factor 9: How the relationship is changing (관계 변화)"""
    GETTING_CLOSER = "getting_closer"     # 점점 친해지는 중
    STABLE = "stable"                     # 안정적
    GETTING_DISTANT = "getting_distant"   # 멀어지는 중
    FORMAL_TO_CASUAL = "formal_to_casual" # 격식→친근
    CASUAL_TO_FORMAL = "casual_to_formal" # 친근→격식 (직장 내 승진 등)


class CompanyCulture(str, Enum):
    """Factor 12: Company culture (회사 문화)"""
    VERY_TRADITIONAL = "very_traditional"  # 대기업, 공기업
    TRADITIONAL = "traditional"            # 일반 한국 회사
    MODERATE = "moderate"                  # 보통
    CASUAL = "casual"                      # 스타트업
    VERY_CASUAL = "very_casual"            # 외국계, 매우 수평적


class IndustryType(str, Enum):
    """Factor 13: Industry type (업계)"""
    GOVERNMENT = "government"          # 공무원, 공기업
    FINANCE = "finance"                # 금융, 은행
    LAW = "law"                        # 법조계
    MEDICAL = "medical"                # 의료계
    EDUCATION = "education"            # 교육계
    CORPORATE = "corporate"            # 일반 대기업
    TECH = "tech"                      # IT, 스타트업
    CREATIVE = "creative"              # 광고, 미디어
    SERVICE = "service"                # 서비스업
    OTHER = "other"


class AlcoholContext(str, Enum):
    """Factor 18: Drinking together (술자리)"""
    NONE = "none"                      # 술 없음
    LIGHT = "light"                    # 가볍게 한 잔
    MODERATE = "moderate"              # 적당히 마심
    HEAVY = "heavy"                    # 많이 마심
    COMPANY_DINNER = "company_dinner"  # 회식


class OnlineOffline(str, Enum):
    """Factor 19: Online vs Offline (온라인/오프라인)"""
    OFFLINE_FORMAL = "offline_formal"      # 오프라인 공식
    OFFLINE_CASUAL = "offline_casual"      # 오프라인 비공식
    VIDEO_CALL = "video_call"              # 화상통화
    PHONE_CALL = "phone_call"              # 전화
    TEXT_MESSAGE = "text_message"          # 문자
    CHAT_APP = "chat_app"                  # 카톡 등
    EMAIL = "email"                        # 이메일
    SOCIAL_MEDIA = "social_media"          # SNS


class TopicSensitivity(str, Enum):
    """Factor 20: Topic sensitivity (주제 민감도)"""
    CASUAL = "casual"              # 일상적인 주제
    NEUTRAL = "neutral"            # 보통 주제
    PROFESSIONAL = "professional"  # 업무 관련
    SENSITIVE = "sensitive"        # 민감한 주제
    VERY_SENSITIVE = "very_sensitive"  # 매우 민감 (질병, 사망, 이혼 등)
    REQUESTING = "requesting"      # 부탁하는 상황
    APOLOGIZING = "apologizing"    # 사과하는 상황
    COMPLAINING = "complaining"    # 불만 표현


class RegionalCulture(str, Enum):
    """Factor 21: Regional culture (지역 문화)"""
    SEOUL = "seoul"                # 서울 (표준)
    GYEONGGI = "gyeonggi"          # 경기도
    BUSAN = "busan"                # 부산 (더 직접적)
    GYEONGSANG = "gyeongsang"      # 경상도
    JEOLLA = "jeolla"              # 전라도
    CHUNGCHEONG = "chungcheong"    # 충청도 (더 느긋)
    GANGWON = "gangwon"            # 강원도
    JEJU = "jeju"                  # 제주도
    STANDARD = "standard"          # 표준


class GenerationGap(str, Enum):
    """Factor 22: Generation gap awareness (세대 차이)"""
    SAME_GENERATION = "same_generation"        # 같은 세대
    ONE_GENERATION = "one_generation"          # 한 세대 차이 (부모-자녀)
    TWO_GENERATIONS = "two_generations"        # 두 세대 (조부모-손자)
    MZ_TO_OLDER = "mz_to_older"               # MZ세대 → 기성세대
    OLDER_TO_MZ = "older_to_mz"               # 기성세대 → MZ세대


class MilitaryBackground(str, Enum):
    """Factor 23: Military background (군대 경험)"""
    NONE = "none"                      # 군 경험 없음
    BOTH_SERVED = "both_served"        # 둘 다 군필
    SAME_UNIT = "same_unit"            # 같은 부대 출신
    SENIOR_JUNIOR = "senior_junior"    # 선임-후임 관계
    DIFFERENT_BRANCH = "different_branch"  # 다른 군종


class FamilySide(str, Enum):
    """Factor 24: Family side (친가/외가)"""
    PATERNAL = "paternal"              # 친가 (아버지 쪽)
    MATERNAL = "maternal"              # 외가 (어머니 쪽)
    IN_LAW = "in_law"                  # 시댁/처가
    NOT_APPLICABLE = "not_applicable"


class CulturalBackground(str, Enum):
    """Factor 25: Cultural background (문화적 배경)"""
    NATIVE_KOREAN = "native_korean"            # 한국 토박이
    KOREAN_AMERICAN = "korean_american"        # 재미교포
    KOREAN_RAISED_ABROAD = "korean_abroad"     # 해외 거주 경험
    FOREIGNER_FLUENT = "foreigner_fluent"      # 외국인 (한국어 유창)
    FOREIGNER_LEARNING = "foreigner_learning"  # 외국인 (학습 중)
    MULTICULTURAL = "multicultural"            # 다문화 가정


class RoleCategory(str, Enum):
    """Category of relationship"""
    FAMILY = "family"
    FRIEND = "friend"
    SCHOOL = "school"
    WORK = "work"
    SERVICE = "service"
    STRANGER = "stranger"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


# ============================================================================
# Role Configuration
# ============================================================================

@dataclass
class RoleConfig:
    """Configuration for each role"""
    category: RoleCategory
    base_avatar_to_user: SpeechLevel
    base_user_to_avatar: SpeechLevel
    is_authority: bool = False          # Never use 반말 regardless of closeness
    hierarchy_level: int = 0            # Higher = more senior (-5 to +5)
    allows_banmal_if_close: bool = True # Can become informal if very close
    age_sensitive: bool = True          # Age difference matters
    context_sensitive: bool = True      # Context affects speech level


ROLE_CONFIGS: Dict[str, RoleConfig] = {
    # === 친구/동기 (Friends/Peers) ===
    "friend": RoleConfig(
        category=RoleCategory.FRIEND,
        base_avatar_to_user=SpeechLevel.INFORMAL,
        base_user_to_avatar=SpeechLevel.INFORMAL,
        hierarchy_level=0,
    ),
    "close_friend": RoleConfig(
        category=RoleCategory.FRIEND,
        base_avatar_to_user=SpeechLevel.INFORMAL,
        base_user_to_avatar=SpeechLevel.INFORMAL,
        hierarchy_level=0,
    ),
    "classmate": RoleConfig(
        category=RoleCategory.FRIEND,
        base_avatar_to_user=SpeechLevel.INFORMAL,
        base_user_to_avatar=SpeechLevel.INFORMAL,
        hierarchy_level=0,
    ),
    "roommate": RoleConfig(
        category=RoleCategory.FRIEND,
        base_avatar_to_user=SpeechLevel.INFORMAL,
        base_user_to_avatar=SpeechLevel.INFORMAL,
        hierarchy_level=0,
    ),
    "club_member": RoleConfig(
        category=RoleCategory.FRIEND,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.POLITE,
        hierarchy_level=0,
    ),
    
    # === 학교 (School) ===
    "junior": RoleConfig(
        category=RoleCategory.SCHOOL,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.INFORMAL,
        hierarchy_level=-2,
    ),
    "senior": RoleConfig(
        category=RoleCategory.SCHOOL,
        base_avatar_to_user=SpeechLevel.INFORMAL,
        base_user_to_avatar=SpeechLevel.POLITE,
        hierarchy_level=2,
    ),
    "professor": RoleConfig(
        category=RoleCategory.SCHOOL,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.FORMAL,
        is_authority=True,
        hierarchy_level=5,
        allows_banmal_if_close=False,
    ),
    "teacher": RoleConfig(
        category=RoleCategory.SCHOOL,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.FORMAL,
        is_authority=True,
        hierarchy_level=4,
        allows_banmal_if_close=False,
    ),
    "tutor": RoleConfig(
        category=RoleCategory.SCHOOL,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.POLITE,
        hierarchy_level=1,
    ),
    
    # === 가족 (Family) ===
    "younger_sibling": RoleConfig(
        category=RoleCategory.FAMILY,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.INFORMAL,
        hierarchy_level=-1,
        age_sensitive=False,
    ),
    "older_brother": RoleConfig(
        category=RoleCategory.FAMILY,
        base_avatar_to_user=SpeechLevel.INFORMAL,
        base_user_to_avatar=SpeechLevel.POLITE,
        hierarchy_level=2,
        age_sensitive=False,
    ),
    "older_sister": RoleConfig(
        category=RoleCategory.FAMILY,
        base_avatar_to_user=SpeechLevel.INFORMAL,
        base_user_to_avatar=SpeechLevel.POLITE,
        hierarchy_level=2,
        age_sensitive=False,
    ),
    "cousin": RoleConfig(
        category=RoleCategory.FAMILY,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.POLITE,
        hierarchy_level=0,
        age_sensitive=True,
    ),
    "parent": RoleConfig(
        category=RoleCategory.FAMILY,
        base_avatar_to_user=SpeechLevel.INFORMAL,
        base_user_to_avatar=SpeechLevel.FORMAL,
        is_authority=True,
        hierarchy_level=5,
        allows_banmal_if_close=False,
        age_sensitive=False,
    ),
    "grandparent": RoleConfig(
        category=RoleCategory.FAMILY,
        base_avatar_to_user=SpeechLevel.INFORMAL,
        base_user_to_avatar=SpeechLevel.FORMAL,
        is_authority=True,
        hierarchy_level=5,
        allows_banmal_if_close=False,
        age_sensitive=False,
    ),
    "uncle_aunt": RoleConfig(
        category=RoleCategory.FAMILY,
        base_avatar_to_user=SpeechLevel.INFORMAL,
        base_user_to_avatar=SpeechLevel.POLITE,
        hierarchy_level=3,
        allows_banmal_if_close=False,
    ),
    "in_law": RoleConfig(
        category=RoleCategory.FAMILY,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.FORMAL,
        hierarchy_level=3,
        allows_banmal_if_close=False,
    ),
    
    # === 직장 (Workplace) ===
    "intern": RoleConfig(
        category=RoleCategory.WORK,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.POLITE,
        hierarchy_level=-2,
    ),
    "colleague": RoleConfig(
        category=RoleCategory.WORK,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.POLITE,
        hierarchy_level=0,
    ),
    "teammate": RoleConfig(
        category=RoleCategory.WORK,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.POLITE,
        hierarchy_level=0,
    ),
    "team_leader": RoleConfig(
        category=RoleCategory.WORK,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.POLITE,
        hierarchy_level=2,
    ),
    "manager": RoleConfig(
        category=RoleCategory.WORK,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.FORMAL,
        hierarchy_level=3,
    ),
    "boss": RoleConfig(
        category=RoleCategory.WORK,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.FORMAL,
        is_authority=True,
        hierarchy_level=4,
        allows_banmal_if_close=False,
    ),
    "ceo": RoleConfig(
        category=RoleCategory.WORK,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.FORMAL,
        is_authority=True,
        hierarchy_level=5,
        allows_banmal_if_close=False,
    ),
    "client": RoleConfig(
        category=RoleCategory.WORK,
        base_avatar_to_user=SpeechLevel.FORMAL,
        base_user_to_avatar=SpeechLevel.FORMAL,
        hierarchy_level=3,
    ),
    "mentor": RoleConfig(
        category=RoleCategory.WORK,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.POLITE,
        hierarchy_level=2,
    ),
    
    # === 서비스/기타 (Service/Others) ===
    "staff": RoleConfig(
        category=RoleCategory.SERVICE,
        base_avatar_to_user=SpeechLevel.FORMAL,
        base_user_to_avatar=SpeechLevel.POLITE,
        hierarchy_level=-1,
    ),
    "customer": RoleConfig(
        category=RoleCategory.SERVICE,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.FORMAL,
        hierarchy_level=2,
    ),
    "stranger": RoleConfig(
        category=RoleCategory.STRANGER,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.POLITE,
        hierarchy_level=0,
    ),
    "neighbor": RoleConfig(
        category=RoleCategory.STRANGER,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.POLITE,
        hierarchy_level=0,
    ),
    "doctor": RoleConfig(
        category=RoleCategory.SERVICE,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.FORMAL,
        is_authority=True,
        hierarchy_level=4,
        allows_banmal_if_close=False,
    ),
    "delivery": RoleConfig(
        category=RoleCategory.SERVICE,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.POLITE,
        hierarchy_level=0,
    ),
    "taxi_driver": RoleConfig(
        category=RoleCategory.SERVICE,
        base_avatar_to_user=SpeechLevel.POLITE,
        base_user_to_avatar=SpeechLevel.POLITE,
        hierarchy_level=0,
    ),
}


# ============================================================================
# Input Model - All 25 Factors
# ============================================================================

class SpeechLevelInput(BaseModel):
    """Input for speech level calculation - All 25 factors"""
    
    # === BASIC FACTORS (1-5) ===
    role: str                                                    # Factor 1
    user_age: int                                                # Factor 2 (used for age_diff)
    avatar_age: int                                              # Factor 2 (used for age_diff)
    closeness: Closeness = Closeness.ACQUAINTANCE               # Factor 3
    social_status: SocialStatus = SocialStatus.EQUAL            # Factor 4
    context: Context = Context.NEUTRAL                          # Factor 5
    
    # === RELATIONSHIP FACTORS (6-10) ===
    is_first_meeting: bool = False                              # Factor 6
    years_known: int = 0                                        # Factor 7
    how_met: HowMet = HowMet.INTRODUCED_CASUAL                  # Factor 8
    relationship_trajectory: RelationshipTrajectory = RelationshipTrajectory.STABLE  # Factor 9
    has_mutual_friends: bool = False                            # Factor 10
    
    # === PROFESSIONAL FACTORS (11-15) ===
    user_position_level: int = 0                                # Factor 11 (0-10)
    avatar_position_level: int = 0                              # Factor 11 (0-10)
    company_culture: CompanyCulture = CompanyCulture.MODERATE   # Factor 12
    industry_type: IndustryType = IndustryType.OTHER            # Factor 13
    is_client_relationship: bool = False                        # Factor 14 (갑을 관계)
    is_project_lead: bool = False                               # Factor 15
    
    # === SITUATIONAL FACTORS (16-20) ===
    is_public_setting: bool = False                             # Factor 16
    is_being_observed: bool = False                             # Factor 17
    alcohol_context: AlcoholContext = AlcoholContext.NONE       # Factor 18
    communication_medium: OnlineOffline = OnlineOffline.OFFLINE_CASUAL  # Factor 19
    topic_sensitivity: TopicSensitivity = TopicSensitivity.CASUAL       # Factor 20
    
    # === CULTURAL FACTORS (21-25) ===
    regional_culture: RegionalCulture = RegionalCulture.STANDARD        # Factor 21
    generation_gap: GenerationGap = GenerationGap.SAME_GENERATION       # Factor 22
    military_background: MilitaryBackground = MilitaryBackground.NONE   # Factor 23
    family_side: FamilySide = FamilySide.NOT_APPLICABLE                 # Factor 24
    cultural_background: CulturalBackground = CulturalBackground.NATIVE_KOREAN  # Factor 25
    
    # === ADDITIONAL ===
    user_gender: Optional[Gender] = None
    avatar_gender: Optional[Gender] = None


# ============================================================================
# Result Model
# ============================================================================

class SpeechLevelResult(BaseModel):
    """Result of speech level calculation"""
    avatar_to_user: SpeechLevel
    user_to_avatar: SpeechLevel
    
    # Explanation
    explanation: str
    factors_applied: List[str]
    
    # Confidence
    confidence: float  # 0-100
    
    # Examples
    avatar_example: str
    user_example: str
    
    # Tips
    tips: List[str]
    common_mistakes: List[str]
    
    # Factor breakdown (for UI display)
    factor_details: Dict[str, Any]


# ============================================================================
# The Calculator
# ============================================================================

class SpeechLevelCalculatorV2:
    """
    Enhanced Rule-Based Speech Level Calculator
    
    ⚠️ NOT MACHINE LEARNING ⚠️
    
    Uses explicit Korean social rules with weighted factors.
    Every decision can be explained!
    
    25 Factors total, grouped into 5 categories:
    - Basic (5)
    - Relationship (5)
    - Professional (5)
    - Situational (5)
    - Cultural (5)
    """
    
    # Weight distribution (sums to 100)
    CATEGORY_WEIGHTS = {
        "basic": 40,        # Most important
        "relationship": 20,
        "professional": 15,
        "situational": 15,
        "cultural": 10,
    }
    
    def calculate(self, input: SpeechLevelInput) -> SpeechLevelResult:
        """Main calculation entry point"""
        
        # Get role config
        role_config = ROLE_CONFIGS.get(input.role, RoleConfig(
            category=RoleCategory.STRANGER,
            base_avatar_to_user=SpeechLevel.POLITE,
            base_user_to_avatar=SpeechLevel.POLITE,
        ))
        
        # Start with base levels
        avatar_to_user = role_config.base_avatar_to_user
        user_to_avatar = role_config.base_user_to_avatar
        
        factors_applied = [f"기본 관계: {input.role}"]
        tips = []
        common_mistakes = []
        factor_details = {"base_role": input.role}
        
        age_diff = input.avatar_age - input.user_age
        
        # ===== APPLY ALL 25 FACTORS =====
        
        # --- BASIC FACTORS (1-5) ---
        
        # Factor 2: Age Difference
        if role_config.age_sensitive:
            result = self._apply_age_factor(user_to_avatar, avatar_to_user, age_diff, input.closeness, role_config)
            user_to_avatar, avatar_to_user = result["user"], result["avatar"]
            if result["applied"]: factors_applied.append(result["reason"])
            if result.get("tip"): tips.append(result["tip"])
            factor_details["age_diff"] = age_diff
        
        # Factor 3: Closeness
        result = self._apply_closeness_factor(user_to_avatar, avatar_to_user, input.closeness, role_config, age_diff)
        user_to_avatar, avatar_to_user = result["user"], result["avatar"]
        if result["applied"]: factors_applied.append(result["reason"])
        if result.get("tip"): tips.append(result["tip"])
        factor_details["closeness"] = input.closeness.value
        
        # Factor 4: Social Status
        result = self._apply_status_factor(user_to_avatar, avatar_to_user, input.social_status)
        user_to_avatar, avatar_to_user = result["user"], result["avatar"]
        if result["applied"]: factors_applied.append(result["reason"])
        factor_details["social_status"] = input.social_status.value
        
        # Factor 5: Context
        result = self._apply_context_factor(user_to_avatar, avatar_to_user, input.context, role_config)
        user_to_avatar, avatar_to_user = result["user"], result["avatar"]
        if result["applied"]: factors_applied.append(result["reason"])
        if result.get("tip"): tips.append(result["tip"])
        factor_details["context"] = input.context.value
        
        # --- RELATIONSHIP FACTORS (6-10) ---
        
        # Factor 6: First Meeting
        if input.is_first_meeting:
            result = self._apply_first_meeting_factor(user_to_avatar, avatar_to_user)
            user_to_avatar, avatar_to_user = result["user"], result["avatar"]
            if result["applied"]: 
                factors_applied.append("첫 만남 (더 공손하게)")
                tips.append("처음 만나는 사이에서는 더 공손한 말투를 사용하세요")
        
        # Factor 7: Years Known
        if input.years_known >= 5 and role_config.allows_banmal_if_close:
            result = self._apply_years_known_factor(user_to_avatar, input.years_known, input.closeness)
            user_to_avatar = result["user"]
            if result["applied"]: factors_applied.append(f"오래 알고 지냄 ({input.years_known}년)")
        factor_details["years_known"] = input.years_known
        
        # Factor 8: How Met
        result = self._apply_how_met_factor(user_to_avatar, avatar_to_user, input.how_met)
        user_to_avatar, avatar_to_user = result["user"], result["avatar"]
        if result["applied"]: factors_applied.append(result["reason"])
        
        # Factor 9: Relationship Trajectory
        result = self._apply_trajectory_factor(user_to_avatar, input.relationship_trajectory)
        user_to_avatar = result["user"]
        if result["applied"]: factors_applied.append(result["reason"])
        
        # Factor 10: Mutual Friends (can accelerate closeness)
        if input.has_mutual_friends and input.closeness == Closeness.ACQUAINTANCE:
            user_to_avatar = self._lower_level(user_to_avatar)
            factors_applied.append("공통 지인 있음")
        
        # --- PROFESSIONAL FACTORS (11-15) ---
        
        # Factor 11: Position Level
        if role_config.category == RoleCategory.WORK:
            position_diff = input.avatar_position_level - input.user_position_level
            result = self._apply_position_factor(user_to_avatar, avatar_to_user, position_diff)
            user_to_avatar, avatar_to_user = result["user"], result["avatar"]
            if result["applied"]: factors_applied.append(result["reason"])
        
        # Factor 12: Company Culture
        result = self._apply_company_culture_factor(user_to_avatar, input.company_culture, role_config)
        user_to_avatar = result["user"]
        if result["applied"]: factors_applied.append(result["reason"])
        factor_details["company_culture"] = input.company_culture.value
        
        # Factor 13: Industry Type
        result = self._apply_industry_factor(user_to_avatar, input.industry_type)
        user_to_avatar = result["user"]
        if result["applied"]: factors_applied.append(result["reason"])
        
        # Factor 14: Client Relationship (갑을)
        if input.is_client_relationship:
            user_to_avatar = SpeechLevel.FORMAL
            avatar_to_user = SpeechLevel.FORMAL
            factors_applied.append("갑을 관계 (클라이언트)")
            tips.append("클라이언트에게는 항상 격식체를 사용하세요")
        
        # Factor 15: Project Lead
        if input.is_project_lead:
            result = self._apply_project_lead_factor(user_to_avatar, avatar_to_user)
            user_to_avatar, avatar_to_user = result["user"], result["avatar"]
            if result["applied"]: factors_applied.append("프로젝트 리드 역할")
        
        # --- SITUATIONAL FACTORS (16-20) ---
        
        # Factor 16: Public Setting
        if input.is_public_setting and user_to_avatar == SpeechLevel.INFORMAL:
            user_to_avatar = SpeechLevel.POLITE
            factors_applied.append("공공장소")
            tips.append("공공장소에서는 반말을 삼가세요")
        
        # Factor 17: Being Observed
        if input.is_being_observed:
            result = self._apply_observed_factor(user_to_avatar, avatar_to_user)
            user_to_avatar, avatar_to_user = result["user"], result["avatar"]
            if result["applied"]: factors_applied.append("다른 사람이 보는 상황")
        
        # Factor 18: Alcohol Context
        result = self._apply_alcohol_factor(user_to_avatar, input.alcohol_context, role_config)
        user_to_avatar = result["user"]
        if result["applied"]: 
            factors_applied.append(result["reason"])
            tips.append(result.get("tip", ""))
        factor_details["alcohol"] = input.alcohol_context.value
        
        # Factor 19: Communication Medium
        result = self._apply_medium_factor(user_to_avatar, input.communication_medium)
        user_to_avatar = result["user"]
        if result["applied"]: factors_applied.append(result["reason"])
        factor_details["medium"] = input.communication_medium.value
        
        # Factor 20: Topic Sensitivity
        result = self._apply_topic_factor(user_to_avatar, input.topic_sensitivity)
        user_to_avatar = result["user"]
        if result["applied"]: factors_applied.append(result["reason"])
        
        # --- CULTURAL FACTORS (21-25) ---
        
        # Factor 21: Regional Culture
        result = self._apply_regional_factor(user_to_avatar, input.regional_culture)
        if result["applied"]: tips.append(result["tip"])
        factor_details["region"] = input.regional_culture.value
        
        # Factor 22: Generation Gap
        result = self._apply_generation_factor(user_to_avatar, input.generation_gap)
        user_to_avatar = result["user"]
        if result["applied"]: factors_applied.append(result["reason"])
        
        # Factor 23: Military Background
        result = self._apply_military_factor(user_to_avatar, avatar_to_user, input.military_background)
        user_to_avatar, avatar_to_user = result["user"], result["avatar"]
        if result["applied"]: factors_applied.append(result["reason"])
        
        # Factor 24: Family Side
        result = self._apply_family_side_factor(user_to_avatar, input.family_side, role_config)
        user_to_avatar = result["user"]
        if result["applied"]: factors_applied.append(result["reason"])
        
        # Factor 25: Cultural Background
        result = self._apply_cultural_background_factor(user_to_avatar, avatar_to_user, input.cultural_background)
        user_to_avatar, avatar_to_user = result["user"], result["avatar"]
        if result["applied"]: 
            factors_applied.append(result["reason"])
            if result.get("tip"): tips.append(result["tip"])
        
        # ===== GENERATE OUTPUT =====
        
        avatar_example = self._generate_example(avatar_to_user, is_avatar=True)
        user_example = self._generate_example(user_to_avatar, is_avatar=False)
        common_mistakes = self._generate_common_mistakes(user_to_avatar, input.role, role_config)
        explanation = self._generate_explanation(input, user_to_avatar, role_config, age_diff)
        confidence = self._calculate_confidence(input, role_config, len(factors_applied))
        
        # Filter empty tips
        tips = [t for t in tips if t]
        
        return SpeechLevelResult(
            avatar_to_user=avatar_to_user,
            user_to_avatar=user_to_avatar,
            explanation=explanation,
            factors_applied=factors_applied,
            confidence=confidence,
            avatar_example=avatar_example,
            user_example=user_example,
            tips=tips[:5],  # Max 5 tips
            common_mistakes=common_mistakes[:3],  # Max 3 mistakes
            factor_details=factor_details,
        )
    
    # ========================================================================
    # Factor Application Methods
    # ========================================================================
    
    def _apply_age_factor(self, user_lvl, avatar_lvl, age_diff, closeness, role_config):
        """Factor 2: Age difference"""
        applied = False
        reason = ""
        tip = None
        
        if age_diff >= 15:
            user_lvl = SpeechLevel.FORMAL
            applied = True
            reason = f"나이 차이 +{age_diff}세 (큰 차이)"
            tip = "15살 이상 차이나면 합쇼체가 안전해요"
        elif age_diff >= 10:
            user_lvl = self._raise_level(user_lvl)
            applied = True
            reason = f"나이 차이 +{age_diff}세"
            tip = "10살 이상 차이나면 더 공손하게"
        elif age_diff >= 5:
            if user_lvl == SpeechLevel.INFORMAL:
                user_lvl = SpeechLevel.POLITE
                applied = True
                reason = f"나이 차이 +{age_diff}세"
        elif -2 <= age_diff <= 2:
            if closeness in [Closeness.CLOSE, Closeness.VERY_CLOSE, Closeness.INTIMATE]:
                if role_config.allows_banmal_if_close and user_lvl != SpeechLevel.INFORMAL:
                    user_lvl = SpeechLevel.INFORMAL
                    applied = True
                    reason = "또래 + 친한 사이"
                    tip = "나이가 비슷하고 친하면 반말도 OK"
        elif age_diff <= -5:
            if avatar_lvl == SpeechLevel.INFORMAL:
                avatar_lvl = SpeechLevel.POLITE
                applied = True
                reason = f"내가 {-age_diff}세 더 많음"
        
        return {"user": user_lvl, "avatar": avatar_lvl, "applied": applied, "reason": reason, "tip": tip}
    
    def _apply_closeness_factor(self, user_lvl, avatar_lvl, closeness, role_config, age_diff):
        """Factor 3: Closeness"""
        applied = False
        reason = ""
        tip = None
        
        if closeness in [Closeness.JUST_MET, Closeness.STRANGER]:
            if user_lvl == SpeechLevel.INFORMAL:
                user_lvl = SpeechLevel.POLITE
                applied = True
                reason = "처음 만남/모르는 사이"
        elif closeness in [Closeness.VERY_CLOSE, Closeness.INTIMATE]:
            if role_config.allows_banmal_if_close and not role_config.is_authority:
                if abs(age_diff) <= 5 and user_lvl != SpeechLevel.INFORMAL:
                    user_lvl = SpeechLevel.INFORMAL
                    applied = True
                    reason = "매우 친한 사이"
                    tip = "친한 사이에서는 반말이 자연스러워요"
        
        return {"user": user_lvl, "avatar": avatar_lvl, "applied": applied, "reason": reason, "tip": tip}
    
    def _apply_status_factor(self, user_lvl, avatar_lvl, status):
        """Factor 4: Social status"""
        applied = False
        reason = ""
        
        if status == SocialStatus.MUCH_HIGHER:
            user_lvl = SpeechLevel.FORMAL
            applied = True
            reason = "사회적 지위 훨씬 높음"
        elif status == SocialStatus.HIGHER:
            user_lvl = self._raise_level(user_lvl)
            applied = True
            reason = "사회적 지위 높음"
        elif status == SocialStatus.LOWER:
            avatar_lvl = self._raise_level(avatar_lvl)
            applied = True
            reason = "상대방 지위 낮음"
        elif status == SocialStatus.MUCH_LOWER:
            avatar_lvl = SpeechLevel.FORMAL
            applied = True
            reason = "상대방 지위 훨씬 낮음"
        
        return {"user": user_lvl, "avatar": avatar_lvl, "applied": applied, "reason": reason}
    
    def _apply_context_factor(self, user_lvl, avatar_lvl, context, role_config):
        """Factor 5: Context"""
        applied = False
        reason = ""
        tip = None
        
        if context in [Context.VERY_FORMAL, Context.FORMAL]:
            user_lvl = self._raise_level(user_lvl)
            if role_config.context_sensitive:
                avatar_lvl = self._raise_level(avatar_lvl)
            applied = True
            reason = "공식적인 상황"
            tip = "공식적인 자리에서는 평소보다 더 공손하게"
        elif context == Context.INTIMATE and not role_config.is_authority:
            if user_lvl == SpeechLevel.FORMAL:
                user_lvl = SpeechLevel.POLITE
                applied = True
                reason = "사적인 공간"
        
        return {"user": user_lvl, "avatar": avatar_lvl, "applied": applied, "reason": reason, "tip": tip}
    
    def _apply_first_meeting_factor(self, user_lvl, avatar_lvl):
        """Factor 6: First meeting"""
        applied = False
        if user_lvl == SpeechLevel.INFORMAL:
            user_lvl = SpeechLevel.POLITE
            applied = True
        return {"user": user_lvl, "avatar": avatar_lvl, "applied": applied}
    
    def _apply_years_known_factor(self, user_lvl, years, closeness):
        """Factor 7: Years known"""
        applied = False
        if years >= 10 and closeness in [Closeness.CLOSE, Closeness.VERY_CLOSE]:
            if user_lvl == SpeechLevel.POLITE:
                user_lvl = SpeechLevel.INFORMAL
                applied = True
        return {"user": user_lvl, "applied": applied}
    
    def _apply_how_met_factor(self, user_lvl, avatar_lvl, how_met):
        """Factor 8: How you met"""
        applied = False
        reason = ""
        
        if how_met == HowMet.INTRODUCED_FORMAL:
            user_lvl = self._raise_level(user_lvl)
            applied = True
            reason = "공식적으로 소개받음"
        elif how_met == HowMet.ONLINE:
            # Online meetings tend to be slightly more casual
            pass
        
        return {"user": user_lvl, "avatar": avatar_lvl, "applied": applied, "reason": reason}
    
    def _apply_trajectory_factor(self, user_lvl, trajectory):
        """Factor 9: Relationship trajectory"""
        applied = False
        reason = ""
        
        if trajectory == RelationshipTrajectory.FORMAL_TO_CASUAL:
            user_lvl = self._lower_level(user_lvl)
            applied = True
            reason = "관계가 편해지는 중"
        elif trajectory == RelationshipTrajectory.CASUAL_TO_FORMAL:
            user_lvl = self._raise_level(user_lvl)
            applied = True
            reason = "관계가 격식화됨"
        
        return {"user": user_lvl, "applied": applied, "reason": reason}
    
    def _apply_position_factor(self, user_lvl, avatar_lvl, position_diff):
        """Factor 11: Position level"""
        applied = False
        reason = ""
        
        if position_diff >= 3:
            user_lvl = SpeechLevel.FORMAL
            applied = True
            reason = "직급 차이 큼 (3단계+)"
        elif position_diff >= 2:
            user_lvl = self._raise_level(user_lvl)
            applied = True
            reason = "직급 차이 있음"
        elif position_diff <= -3:
            avatar_lvl = SpeechLevel.FORMAL
            applied = True
            reason = "내 직급이 훨씬 높음"
        
        return {"user": user_lvl, "avatar": avatar_lvl, "applied": applied, "reason": reason}
    
    def _apply_company_culture_factor(self, user_lvl, culture, role_config):
        """Factor 12: Company culture"""
        applied = False
        reason = ""
        
        if culture == CompanyCulture.VERY_CASUAL and role_config.category == RoleCategory.WORK:
            if user_lvl == SpeechLevel.FORMAL:
                user_lvl = SpeechLevel.POLITE
                applied = True
                reason = "수평적 회사 문화"
        elif culture == CompanyCulture.VERY_TRADITIONAL:
            user_lvl = self._raise_level(user_lvl)
            applied = True
            reason = "보수적 회사 문화"
        
        return {"user": user_lvl, "applied": applied, "reason": reason}
    
    def _apply_industry_factor(self, user_lvl, industry):
        """Factor 13: Industry type"""
        applied = False
        reason = ""
        
        formal_industries = [IndustryType.GOVERNMENT, IndustryType.FINANCE, IndustryType.LAW]
        if industry in formal_industries:
            user_lvl = self._raise_level(user_lvl)
            applied = True
            reason = f"{industry.value} 업계 (격식 중시)"
        
        return {"user": user_lvl, "applied": applied, "reason": reason}
    
    def _apply_project_lead_factor(self, user_lvl, avatar_lvl):
        """Factor 15: Project lead"""
        applied = False
        # Project lead gets more authority
        if avatar_lvl == SpeechLevel.INFORMAL:
            avatar_lvl = SpeechLevel.POLITE
            applied = True
        return {"user": user_lvl, "avatar": avatar_lvl, "applied": applied}
    
    def _apply_observed_factor(self, user_lvl, avatar_lvl):
        """Factor 17: Being observed"""
        applied = False
        if user_lvl == SpeechLevel.INFORMAL:
            user_lvl = SpeechLevel.POLITE
            applied = True
        return {"user": user_lvl, "avatar": avatar_lvl, "applied": applied}
    
    def _apply_alcohol_factor(self, user_lvl, alcohol, role_config):
        """Factor 18: Alcohol context"""
        applied = False
        reason = ""
        tip = ""
        
        if alcohol in [AlcoholContext.MODERATE, AlcoholContext.HEAVY]:
            if role_config.allows_banmal_if_close and not role_config.is_authority:
                user_lvl = self._lower_level(user_lvl)
                applied = True
                reason = "술자리 (더 편하게)"
                tip = "술자리에서도 윗사람에게는 존댓말을 유지하세요"
        elif alcohol == AlcoholContext.COMPANY_DINNER:
            # 회식 is formal even with alcohol
            pass
        
        return {"user": user_lvl, "applied": applied, "reason": reason, "tip": tip}
    
    def _apply_medium_factor(self, user_lvl, medium):
        """Factor 19: Communication medium"""
        applied = False
        reason = ""
        
        if medium == OnlineOffline.EMAIL:
            user_lvl = self._raise_level(user_lvl)
            applied = True
            reason = "이메일 (격식체)"
        elif medium in [OnlineOffline.CHAT_APP, OnlineOffline.SOCIAL_MEDIA]:
            # Can be slightly more casual
            pass
        
        return {"user": user_lvl, "applied": applied, "reason": reason}
    
    def _apply_topic_factor(self, user_lvl, topic):
        """Factor 20: Topic sensitivity"""
        applied = False
        reason = ""
        
        if topic in [TopicSensitivity.REQUESTING, TopicSensitivity.APOLOGIZING]:
            user_lvl = self._raise_level(user_lvl)
            applied = True
            reason = "부탁/사과 상황 (더 공손하게)"
        elif topic == TopicSensitivity.VERY_SENSITIVE:
            user_lvl = self._raise_level(user_lvl)
            applied = True
            reason = "민감한 주제"
        
        return {"user": user_lvl, "applied": applied, "reason": reason}
    
    def _apply_regional_factor(self, user_lvl, region):
        """Factor 21: Regional culture"""
        applied = False
        tip = ""
        
        if region == RegionalCulture.BUSAN or region == RegionalCulture.GYEONGSANG:
            applied = True
            tip = "경상도 사투리는 더 직접적으로 들릴 수 있어요"
        elif region == RegionalCulture.CHUNGCHEONG:
            applied = True
            tip = "충청도는 느긋하고 부드러운 말투가 특징이에요"
        
        return {"applied": applied, "tip": tip}
    
    def _apply_generation_factor(self, user_lvl, gap):
        """Factor 22: Generation gap"""
        applied = False
        reason = ""
        
        if gap == GenerationGap.TWO_GENERATIONS:
            user_lvl = SpeechLevel.FORMAL
            applied = True
            reason = "두 세대 차이"
        elif gap == GenerationGap.MZ_TO_OLDER:
            user_lvl = self._raise_level(user_lvl)
            applied = True
            reason = "MZ세대 → 기성세대"
        
        return {"user": user_lvl, "applied": applied, "reason": reason}
    
    def _apply_military_factor(self, user_lvl, avatar_lvl, military):
        """Factor 23: Military background"""
        applied = False
        reason = ""
        
        if military == MilitaryBackground.SENIOR_JUNIOR:
            user_lvl = SpeechLevel.FORMAL
            avatar_lvl = SpeechLevel.INFORMAL
            applied = True
            reason = "군대 선후임 관계"
        elif military == MilitaryBackground.SAME_UNIT:
            # Can be closer due to shared experience
            pass
        
        return {"user": user_lvl, "avatar": avatar_lvl, "applied": applied, "reason": reason}
    
    def _apply_family_side_factor(self, user_lvl, side, role_config):
        """Factor 24: Family side"""
        applied = False
        reason = ""
        
        if side == FamilySide.IN_LAW and role_config.category == RoleCategory.FAMILY:
            user_lvl = self._raise_level(user_lvl)
            applied = True
            reason = "시댁/처가 (더 공손하게)"
        
        return {"user": user_lvl, "applied": applied, "reason": reason}
    
    def _apply_cultural_background_factor(self, user_lvl, avatar_lvl, background):
        """Factor 25: Cultural background"""
        applied = False
        reason = ""
        tip = ""
        
        if background == CulturalBackground.FOREIGNER_LEARNING:
            applied = True
            reason = "외국어 학습자"
            tip = "학습 중이라면 약간의 실수는 이해받을 수 있어요"
        elif background == CulturalBackground.KOREAN_AMERICAN:
            applied = True
            reason = "재외교포"
            tip = "교포는 말투가 약간 다를 수 있어요"
        
        return {"user": user_lvl, "avatar": avatar_lvl, "applied": applied, "reason": reason, "tip": tip}
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _raise_level(self, level: SpeechLevel) -> SpeechLevel:
        if level == SpeechLevel.INFORMAL:
            return SpeechLevel.POLITE
        elif level == SpeechLevel.POLITE:
            return SpeechLevel.FORMAL
        return level
    
    def _lower_level(self, level: SpeechLevel) -> SpeechLevel:
        if level == SpeechLevel.FORMAL:
            return SpeechLevel.POLITE
        elif level == SpeechLevel.POLITE:
            return SpeechLevel.INFORMAL
        return level
    
    def _generate_example(self, level: SpeechLevel, is_avatar: bool) -> str:
        examples = {
            SpeechLevel.FORMAL: {
                "avatar": "안녕하십니까? 오늘 어떻게 지내셨습니까?",
                "user": "안녕하십니까? 잘 지내셨습니까?",
            },
            SpeechLevel.POLITE: {
                "avatar": "안녕하세요! 오늘 뭐 했어요?",
                "user": "안녕하세요! 잘 지냈어요?",
            },
            SpeechLevel.INFORMAL: {
                "avatar": "야, 뭐해? 오늘 뭐 했어?",
                "user": "안녕! 나 잘 지냈어~",
            },
        }
        key = "avatar" if is_avatar else "user"
        return examples[level][key]
    
    def _generate_common_mistakes(self, user_lvl, role, role_config):
        mistakes = []
        
        if user_lvl == SpeechLevel.FORMAL:
            mistakes.append("'뭐해?' 대신 '뭐 하십니까?'를 사용하세요")
            mistakes.append("'나' 대신 '저'를 사용하세요")
            mistakes.append("문장 끝에 '-습니다'를 붙이세요")
        elif user_lvl == SpeechLevel.POLITE:
            mistakes.append("문장 끝에 '-요'를 빼먹지 마세요")
            mistakes.append("'뭐해?'가 아니라 '뭐 해요?'입니다")
        
        if role_config.is_authority:
            mistakes.append(f"이 관계에서는 절대 반말을 사용하면 안 됩니다")
        
        return mistakes
    
    def _generate_explanation(self, input, user_lvl, role_config, age_diff):
        level_names = {
            SpeechLevel.FORMAL: "합쇼체 (격식체)",
            SpeechLevel.POLITE: "해요체",
            SpeechLevel.INFORMAL: "반말",
        }
        
        parts = [f"이 관계에서는 {level_names[user_lvl]}를 사용하세요."]
        
        if age_diff > 5:
            parts.append(f"상대방이 {age_diff}살 많습니다.")
        if role_config.is_authority:
            parts.append("항상 존댓말을 유지해야 하는 관계입니다.")
        if input.closeness in [Closeness.VERY_CLOSE, Closeness.INTIMATE]:
            if role_config.allows_banmal_if_close:
                parts.append("친한 사이라 편하게 말해도 됩니다.")
        
        return " ".join(parts)
    
    def _calculate_confidence(self, input, role_config, num_factors):
        confidence = 100.0
        
        if input.role not in ROLE_CONFIGS:
            confidence -= 15
        
        age_diff = abs(input.avatar_age - input.user_age)
        if 3 <= age_diff <= 7:
            confidence -= 10  # Ambiguous age range
        
        if input.closeness == Closeness.VERY_CLOSE and role_config.is_authority:
            confidence -= 10  # Tricky situation
        
        # More factors applied = more complex = slightly less confident
        if num_factors > 10:
            confidence -= 5
        
        return max(50, min(100, confidence))


# ============================================================================
# Global Instance
# ============================================================================

speech_calculator = SpeechLevelCalculatorV2()


# ============================================================================
# Simple API Function
# ============================================================================

def calculate_speech_levels(
    role: str,
    user_age: int,
    avatar_age: int,
    **kwargs
) -> Dict[str, Any]:
    """Simple function to calculate speech levels"""
    
    # Build input with provided kwargs
    input_data = SpeechLevelInput(
        role=role,
        user_age=user_age,
        avatar_age=avatar_age,
        **{k: v for k, v in kwargs.items() if v is not None}
    )
    
    result = speech_calculator.calculate(input_data)
    
    return {
        "avatar_to_user": result.avatar_to_user.value,
        "user_to_avatar": result.user_to_avatar.value,
        "explanation": result.explanation,
        "factors_applied": result.factors_applied,
        "confidence": result.confidence,
        "tips": result.tips,
        "common_mistakes": result.common_mistakes,
        "examples": {
            "avatar": result.avatar_example,
            "user": result.user_example,
        },
        "factor_details": result.factor_details,
    }
