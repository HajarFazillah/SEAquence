"""
Compatibility API

POST /api/v1/compatibility/analyze - Calculate compatibility between user and avatar
POST /api/v1/compatibility/analyze-semantic - AI-powered semantic similarity analysis

Uses CLOVA X for semantic understanding of interests and topics.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import math

from app.schemas.avatar import AvatarCreate
from app.schemas.user import UserProfileCreate
from app.services.clova_service import clova_service, Message


router = APIRouter(prefix="/compatibility", tags=["compatibility"])


# ============================================================================
# Schemas
# ============================================================================

class CompatibilityRequest(BaseModel):
    """Request for compatibility analysis"""
    user_profile: UserProfileCreate
    avatar: AvatarCreate


class SemanticMatch(BaseModel):
    """A semantically related pair of interests"""
    user_interest: str
    avatar_interest: str
    similarity: int  # 0-100
    reason: str


class CompatibilityResult(BaseModel):
    """Compatibility analysis result"""
    overall_score: float  # 0-100
    interest_overlap: float
    topic_safety: float  # How much avatar avoids user's disliked topics
    difficulty_match: float
    shared_interests: List[str]
    semantic_matches: List[SemanticMatch] = []  # AI-found related interests
    potential_conflicts: List[str]
    suggested_topics: List[str] = []  # AI-suggested conversation topics
    recommendation: str


class BatchCompatibilityRequest(BaseModel):
    """Request for batch compatibility analysis"""
    user_profile: UserProfileCreate
    avatars: List[AvatarCreate]


class AvatarCompatibility(BaseModel):
    """Single avatar compatibility result"""
    avatar_id: Optional[str]
    avatar_name: str
    overall_score: float
    shared_interests: List[str]
    semantic_matches: List[SemanticMatch] = []
    recommendation: str


class BatchCompatibilityResult(BaseModel):
    """Batch compatibility results"""
    results: List[AvatarCompatibility]
    best_match: Optional[str]


# ============================================================================
# AI-Powered Semantic Analysis
# ============================================================================

async def analyze_semantic_similarity(
    user_interests: List[str],
    avatar_interests: List[str],
) -> Dict[str, Any]:
    """
    Use CLOVA X to find semantically similar interests.
    
    Examples:
    - "음악" ↔ "K-POP" → related (85%)
    - "여행" ↔ "해외 문화" → related (70%)
    - "운동" ↔ "헬스" → related (90%)
    """
    if not user_interests or not avatar_interests:
        return {"score": 50, "matches": [], "suggested_topics": []}
    
    prompt = f"""두 사람의 관심사를 비교하여 의미적으로 관련된 주제를 찾아주세요.

사용자 관심사: {', '.join(user_interests)}
아바타 관심사: {', '.join(avatar_interests)}

다음 JSON 형식으로 응답하세요:
{{
    "overall_similarity": 0-100 사이의 점수,
    "matches": [
        {{
            "user_interest": "사용자의 관심사",
            "avatar_interest": "아바타의 관련된 관심사",
            "similarity": 0-100 사이의 유사도,
            "reason": "관련된 이유 (한 문장)"
        }}
    ],
    "suggested_topics": ["두 사람이 함께 이야기하기 좋은 주제 3개"]
}}

예시:
- "음악"과 "K-POP"은 관련됨 (similarity: 85, reason: "K-POP은 음악의 한 장르입니다")
- "여행"과 "맛집"은 관련됨 (similarity: 70, reason: "여행 중 맛집 탐방을 함께 즐길 수 있습니다")
- "운동"과 "헬스"는 매우 관련됨 (similarity: 95, reason: "헬스는 운동의 한 종류입니다")

정확한 일치가 아니어도 의미적으로 관련된 것을 모두 찾아주세요.
최소 유사도 50 이상인 것만 포함하세요."""

    result = await clova_service.analyze_json(prompt, temperature=0.3, max_tokens=1024)
    
    if not result:
        # Fallback to empty result
        return {"score": 50, "matches": [], "suggested_topics": []}
    
    return {
        "score": result.get("overall_similarity", 50),
        "matches": result.get("matches", []),
        "suggested_topics": result.get("suggested_topics", []),
    }


async def analyze_topic_conflicts(
    user_dislikes: List[str],
    avatar_interests: List[str],
) -> Dict[str, Any]:
    """
    Use CLOVA X to find potential topic conflicts semantically.
    
    Examples:
    - User dislikes "취업 스트레스" but avatar likes "커리어" → potential conflict
    - User dislikes "정치" but avatar likes "시사" → related conflict
    """
    if not user_dislikes or not avatar_interests:
        return {"safety_score": 100, "conflicts": []}
    
    prompt = f"""사용자가 피하고 싶은 주제와 아바타의 관심사 사이에 충돌이 있는지 분석해주세요.

사용자가 피하는 주제: {', '.join(user_dislikes)}
아바타 관심사: {', '.join(avatar_interests)}

다음 JSON 형식으로 응답하세요:
{{
    "safety_score": 0-100 (100은 완전히 안전, 0은 많은 충돌),
    "conflicts": [
        {{
            "user_dislike": "사용자가 피하는 주제",
            "avatar_interest": "관련된 아바타 관심사",
            "severity": "high/medium/low",
            "reason": "충돌 이유"
        }}
    ],
    "advice": "대화 시 주의할 점"
}}

예시:
- "취업 스트레스"를 피하는데 아바타가 "커리어"를 좋아함 → medium severity
- "정치"를 피하는데 아바타가 "시사"를 좋아함 → high severity
- "종교"를 피하는데 아바타가 "철학"을 좋아함 → low severity"""

    result = await clova_service.analyze_json(prompt, temperature=0.3, max_tokens=512)
    
    if not result:
        return {"safety_score": 100, "conflicts": [], "advice": ""}
    
    return result


async def generate_compatibility_recommendation(
    avatar_name: str,
    overall_score: float,
    semantic_matches: List[Dict],
    conflicts: List[Dict],
    suggested_topics: List[str],
) -> str:
    """
    Generate a natural, helpful recommendation using AI.
    """
    prompt = f"""다음 정보를 바탕으로 사용자에게 이 아바타와의 대화를 추천하는 짧은 문장을 작성하세요.

아바타: {avatar_name}
전체 점수: {overall_score}/100
공통 관심사: {[m.get('user_interest', '') for m in semantic_matches[:3]]}
주의할 주제: {[c.get('user_dislike', '') for c in conflicts[:2]]}
추천 대화 주제: {suggested_topics[:3]}

자연스럽고 긍정적인 톤으로 2-3문장으로 작성하세요.
점수가 낮더라도 긍정적인 면을 찾아주세요."""

    response = await clova_service.chat(
        [Message(role="user", content=prompt)],
        temperature=0.7,
        max_tokens=150,
    )
    
    return response.content if response.content else f"{avatar_name}님과 대화해보세요!"


# ============================================================================
# Rule-Based Calculations (Fallback)
# ============================================================================

def calculate_interest_overlap_simple(
    user_interests: List[str], 
    avatar_interests: List[str]
) -> tuple[float, List[str]]:
    """Simple exact-match overlap calculation (fallback)"""
    if not user_interests or not avatar_interests:
        return 50.0, []
    
    user_set = set(i.lower().strip() for i in user_interests)
    avatar_set = set(i.lower().strip() for i in avatar_interests)
    
    shared = user_set.intersection(avatar_set)
    total = user_set.union(avatar_set)
    
    if not total:
        return 50.0, []
    
    overlap = len(shared) / len(total) * 100
    shared_list = [i for i in user_interests if i.lower().strip() in shared]
    
    return overlap, shared_list


def calculate_topic_safety_simple(
    user_dislikes: List[str], 
    avatar_interests: List[str]
) -> tuple[float, List[str]]:
    """Simple exact-match safety calculation (fallback)"""
    if not user_dislikes:
        return 100.0, []
    
    if not avatar_interests:
        return 100.0, []
    
    user_dislike_set = set(d.lower().strip() for d in user_dislikes)
    avatar_interest_set = set(i.lower().strip() for i in avatar_interests)
    
    conflicts = user_dislike_set.intersection(avatar_interest_set)
    conflict_list = [d for d in user_dislikes if d.lower().strip() in conflicts]
    
    if not conflicts:
        return 100.0, []
    
    safety = max(0, 100 - (len(conflicts) / len(user_dislikes) * 100))
    return safety, conflict_list


def calculate_difficulty_match(user_level: str, avatar_difficulty: str) -> float:
    """Calculate difficulty match score"""
    level_map = {"beginner": 1, "intermediate": 2, "advanced": 3}
    diff_map = {"easy": 1, "medium": 2, "hard": 3}
    
    user_val = level_map.get(str(user_level).lower(), 2)
    avatar_val = diff_map.get(str(avatar_difficulty).lower(), 2)
    
    diff = abs(user_val - avatar_val)
    
    if diff == 0:
        return 100.0
    elif diff == 1:
        return 70.0
    else:
        return 40.0


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/analyze", response_model=CompatibilityResult)
async def analyze_compatibility(request: CompatibilityRequest):
    """
    Calculate compatibility with AI-powered semantic similarity.
    
    Uses CLOVA X to:
    1. Find semantically related interests (e.g., "음악" ↔ "K-POP")
    2. Detect potential topic conflicts
    3. Suggest conversation topics
    4. Generate personalized recommendations
    """
    user = request.user_profile
    avatar = request.avatar
    
    # 1. Semantic interest analysis (AI)
    semantic_result = await analyze_semantic_similarity(
        user.interests or [],
        avatar.interests or [],
    )
    
    semantic_score = semantic_result.get("score", 50)
    semantic_matches = [
        SemanticMatch(
            user_interest=m.get("user_interest", ""),
            avatar_interest=m.get("avatar_interest", ""),
            similarity=m.get("similarity", 0),
            reason=m.get("reason", ""),
        )
        for m in semantic_result.get("matches", [])
    ]
    suggested_topics = semantic_result.get("suggested_topics", [])
    
    # 2. Also get exact matches
    exact_score, exact_shared = calculate_interest_overlap_simple(
        user.interests or [],
        avatar.interests or [],
    )
    
    # Combine exact + semantic (weighted: 30% exact, 70% semantic)
    combined_interest_score = (exact_score * 0.3) + (semantic_score * 0.7)
    
    # 3. Topic safety analysis (AI)
    conflict_result = await analyze_topic_conflicts(
        user.dislikes or [],
        avatar.interests or [],
    )
    
    ai_safety_score = conflict_result.get("safety_score", 100)
    ai_conflicts = conflict_result.get("conflicts", [])
    
    # Also get exact conflicts
    exact_safety, exact_conflicts = calculate_topic_safety_simple(
        user.dislikes or [],
        avatar.interests or [],
    )
    
    # Combine (30% exact, 70% AI)
    combined_safety_score = (exact_safety * 0.3) + (ai_safety_score * 0.7)
    
    # Get conflict list (merge exact + AI)
    all_conflicts = list(set(exact_conflicts + [c.get("user_dislike", "") for c in ai_conflicts]))
    
    # 4. Difficulty match (rule-based)
    difficulty_score = calculate_difficulty_match(
        user.korean_level.value if hasattr(user.korean_level, 'value') else str(user.korean_level),
        avatar.difficulty.value if hasattr(avatar.difficulty, 'value') else str(avatar.difficulty),
    )
    
    # 5. Calculate overall score
    # Weights: Interest 40%, Safety 30%, Difficulty 30%
    overall = (combined_interest_score * 0.4) + (combined_safety_score * 0.3) + (difficulty_score * 0.3)
    
    # 6. Generate AI recommendation
    recommendation = await generate_compatibility_recommendation(
        avatar_name=avatar.name_ko,
        overall_score=overall,
        semantic_matches=[m.dict() for m in semantic_matches],
        conflicts=ai_conflicts,
        suggested_topics=suggested_topics,
    )
    
    return CompatibilityResult(
        overall_score=round(overall, 1),
        interest_overlap=round(combined_interest_score, 1),
        topic_safety=round(combined_safety_score, 1),
        difficulty_match=round(difficulty_score, 1),
        shared_interests=exact_shared,
        semantic_matches=semantic_matches,
        potential_conflicts=all_conflicts,
        suggested_topics=suggested_topics,
        recommendation=recommendation,
    )


@router.post("/analyze-simple", response_model=CompatibilityResult)
async def analyze_compatibility_simple(request: CompatibilityRequest):
    """
    Simple rule-based compatibility (no AI, faster).
    
    Use this for quick checks or when AI is unavailable.
    """
    user = request.user_profile
    avatar = request.avatar
    
    # Calculate metrics (simple exact-match)
    interest_score, shared = calculate_interest_overlap_simple(
        user.interests or [],
        avatar.interests or [],
    )
    
    safety_score, conflicts = calculate_topic_safety_simple(
        user.dislikes or [],
        avatar.interests or [],
    )
    
    difficulty_score = calculate_difficulty_match(
        user.korean_level.value if hasattr(user.korean_level, 'value') else str(user.korean_level),
        avatar.difficulty.value if hasattr(avatar.difficulty, 'value') else str(avatar.difficulty),
    )
    
    # Overall score
    overall = (interest_score * 0.4 + safety_score * 0.3 + difficulty_score * 0.3)
    
    # Simple recommendation
    if overall >= 80:
        rec = f"{avatar.name_ko}님과 대화하기 매우 좋습니다! 관심사가 많이 겹치고 난이도도 적당합니다."
    elif overall >= 60:
        rec = f"{avatar.name_ko}님과 대화해보세요. 몇 가지 공통 관심사가 있습니다."
    else:
        rec = f"{avatar.name_ko}님과 대화하면 새로운 주제를 배울 수 있습니다."
    
    return CompatibilityResult(
        overall_score=round(overall, 1),
        interest_overlap=round(interest_score, 1),
        topic_safety=round(safety_score, 1),
        difficulty_match=round(difficulty_score, 1),
        shared_interests=shared,
        semantic_matches=[],
        potential_conflicts=conflicts,
        suggested_topics=[],
        recommendation=rec,
    )


@router.post("/batch", response_model=BatchCompatibilityResult)
async def analyze_batch_compatibility(request: BatchCompatibilityRequest):
    """
    Calculate compatibility for multiple avatars with AI analysis.
    
    Returns sorted list with best match and semantic matches.
    """
    results = []
    
    for avatar in request.avatars:
        single_req = CompatibilityRequest(
            user_profile=request.user_profile,
            avatar=avatar,
        )
        
        try:
            result = await analyze_compatibility(single_req)
            
            results.append(AvatarCompatibility(
                avatar_id=getattr(avatar, 'id', None),
                avatar_name=avatar.name_ko,
                overall_score=result.overall_score,
                shared_interests=result.shared_interests,
                semantic_matches=result.semantic_matches,
                recommendation=result.recommendation,
            ))
        except Exception as e:
            print(f"Error analyzing {avatar.name_ko}: {e}")
            continue
    
    # Sort by score
    results.sort(key=lambda x: x.overall_score, reverse=True)
    
    best_match = results[0].avatar_name if results else None
    
    return BatchCompatibilityResult(
        results=results,
        best_match=best_match,
    )


@router.post("/batch-simple", response_model=BatchCompatibilityResult)
async def analyze_batch_compatibility_simple(request: BatchCompatibilityRequest):
    """
    Calculate compatibility for multiple avatars (simple, no AI).
    
    Faster but less accurate than /batch.
    """
    results = []
    
    for avatar in request.avatars:
        single_req = CompatibilityRequest(
            user_profile=request.user_profile,
            avatar=avatar,
        )
        
        try:
            result = await analyze_compatibility_simple(single_req)
            
            results.append(AvatarCompatibility(
                avatar_id=getattr(avatar, 'id', None),
                avatar_name=avatar.name_ko,
                overall_score=result.overall_score,
                shared_interests=result.shared_interests,
                semantic_matches=[],
                recommendation=result.recommendation,
            ))
        except Exception:
            continue
    
    # Sort by score
    results.sort(key=lambda x: x.overall_score, reverse=True)
    
    best_match = results[0].avatar_name if results else None
    
    return BatchCompatibilityResult(
        results=results,
        best_match=best_match,
    )
