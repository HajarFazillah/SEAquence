"""
Compatibility API

POST /api/v1/compatibility/analyze        - Semantic (ko-sroberta) + CLOVA recommendation
POST /api/v1/compatibility/analyze-simple - Rule-based fallback (no ML, no AI)

Keyword/interest similarity is calculated using ko-sroberta sentence embeddings.
CLOVA X is used only for the final natural-language recommendation text.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import math

from app.schemas.avatar import AvatarCreate
from app.schemas.user import UserProfileCreate
from app.services.clova_service import clova_service, Message
from app.ml.compatibility_service import get_compatibility_analyzer


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
# STH-Based Semantic Analysis (ko-sroberta)
# ============================================================================

def analyze_semantic_similarity_sth(
    user_interests: List[str],
    avatar_interests: List[str],
    threshold: float = 0.55,
) -> Dict[str, Any]:
    """
    Use ko-sroberta embeddings to find semantically similar interests.
    Falls back to exact string matching if model is unavailable.
    """
    if not user_interests or not avatar_interests:
        return {"score": 50, "matches": [], "suggested_topics": []}

    analyzer = get_compatibility_analyzer()
    raw_matches = analyzer.find_semantic_matches(user_interests, avatar_interests, threshold=threshold)

    matches = [
        {
            "user_interest":   m["item_a"],
            "avatar_interest": m["item_b"],
            "similarity":      int(m["similarity"] * 100),
            "reason": (
                f"'{m['item_a']}'와 '{m['item_b']}'은 의미적으로 연관돼 있어요."
                if not m["is_exact"]
                else f"'{m['item_a']}'에 대한 관심사가 같아요."
            ),
        }
        for m in raw_matches
    ]

    overall = min(100, len(matches) * 20) if matches else 0
    suggested_topics = list({m["user_interest"] for m in matches})[:3]

    return {"score": overall, "matches": matches, "suggested_topics": suggested_topics}


def analyze_topic_conflicts_sth(
    user_dislikes: List[str],
    avatar_interests: List[str],
    threshold: float = 0.65,
) -> Dict[str, Any]:
    """
    Use ko-sroberta embeddings to detect semantic conflicts between
    user dislikes and avatar interests.
    """
    if not user_dislikes or not avatar_interests:
        return {"safety_score": 100, "conflicts": []}

    analyzer = get_compatibility_analyzer()
    raw_conflicts = analyzer.find_semantic_matches(user_dislikes, avatar_interests, threshold=threshold)

    conflicts = [
        {
            "user_dislike":    m["item_a"],
            "avatar_interest": m["item_b"],
            "severity": "high" if m["similarity"] >= 0.85 else "medium" if m["similarity"] >= 0.70 else "low",
        }
        for m in raw_conflicts
    ]

    penalty = sum({"high": 30, "medium": 15, "low": 8}[c["severity"]] for c in conflicts)
    safety_score = max(0, 100 - penalty)

    return {"safety_score": safety_score, "conflicts": conflicts}


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
    Compatibility analysis using ko-sroberta for semantic similarity
    and CLOVA X only for the final recommendation text.
    """
    user = request.user_profile
    avatar = request.avatar

    # 1. Semantic interest similarity — ko-sroberta (sync, fast)
    semantic_result = analyze_semantic_similarity_sth(
        user.interests or [],
        avatar.interests or [],
    )
    semantic_score = semantic_result["score"]
    semantic_matches = [
        SemanticMatch(
            user_interest=m["user_interest"],
            avatar_interest=m["avatar_interest"],
            similarity=m["similarity"],
            reason=m["reason"],
        )
        for m in semantic_result["matches"]
    ]
    suggested_topics = semantic_result["suggested_topics"]

    # 2. Exact-match overlap (rule-based, for shared_interests list)
    exact_score, exact_shared = calculate_interest_overlap_simple(
        user.interests or [],
        avatar.interests or [],
    )

    # Combine: 30% exact, 70% semantic embedding
    combined_interest_score = (exact_score * 0.3) + (semantic_score * 0.7)

    # 3. Topic conflict detection — ko-sroberta (sync, fast)
    conflict_result = analyze_topic_conflicts_sth(
        user.dislikes or [],
        avatar.interests or [],
    )
    sth_safety_score = conflict_result["safety_score"]
    sth_conflicts = conflict_result["conflicts"]

    exact_safety, exact_conflicts = calculate_topic_safety_simple(
        user.dislikes or [],
        avatar.interests or [],
    )
    combined_safety_score = (exact_safety * 0.3) + (sth_safety_score * 0.7)
    all_conflicts = list(set(
        exact_conflicts + [c["user_dislike"] for c in sth_conflicts]
    ))

    # 4. Difficulty match (rule-based)
    difficulty_score = calculate_difficulty_match(
        user.korean_level.value if hasattr(user.korean_level, "value") else str(user.korean_level),
        avatar.difficulty.value if hasattr(avatar.difficulty, "value") else str(avatar.difficulty),
    )

    # 5. Final score  — Interest 40%, Safety 30%, Difficulty 30%
    overall = (
        combined_interest_score * 0.4
        + combined_safety_score  * 0.3
        + difficulty_score       * 0.3
    )

    # 6. CLOVA X — recommendation text only (1 call)
    recommendation = await generate_compatibility_recommendation(
        avatar_name=avatar.name_ko,
        overall_score=overall,
        semantic_matches=[m.dict() for m in semantic_matches],
        conflicts=sth_conflicts,
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
