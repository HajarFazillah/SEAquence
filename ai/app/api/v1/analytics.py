"""
Analytics API - User Korean Skills Dashboard

Provides comprehensive analytics for tracking Korean learning progress.

GET  /api/v1/analytics/{user_id} - Get complete analytics
GET  /api/v1/analytics/{user_id}/skills - Get skill breakdown
GET  /api/v1/analytics/{user_id}/progress - Get progress over time
GET  /api/v1/analytics/{user_id}/weak-areas - Get weak areas
GET  /api/v1/analytics/{user_id}/achievements - Get achievements
GET  /api/v1/analytics/{user_id}/streak - Get streak info
GET  /api/v1/analytics/{user_id}/recommendations - Get recommendations
POST /api/v1/analytics/{user_id}/record - Record learning activity
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.services.analytics_service import (
    analytics_service,
    UserAnalytics,
    SkillScore,
    WeakArea,
    Achievement,
    LearningStreak,
    DailyStats,
    SkillCategory,
    ProficiencyLevel,
)


router = APIRouter(prefix="/analytics", tags=["analytics"])


# ============================================================================
# Request Models
# ============================================================================

class RecordMessageRequest(BaseModel):
    """Record a user message"""
    has_error: bool = False
    error_types: List[str] = []
    original_text: str = ""


class RecordConversationRequest(BaseModel):
    """Record a completed conversation"""
    duration_minutes: int = 5


class RecordVocabularyRequest(BaseModel):
    """Record vocabulary learning"""
    learned: int = 0
    reviewed: int = 0


class RecordSkillRequest(BaseModel):
    """Record skill practice"""
    category: str
    correct: bool


# ============================================================================
# Response Models
# ============================================================================

class SkillBreakdown(BaseModel):
    """Skill scores breakdown for charts"""
    categories: List[str]
    scores: List[float]
    colors: List[str]


class ProgressChart(BaseModel):
    """Progress data for line chart"""
    dates: List[str]
    scores: List[float]
    messages: List[int]
    accuracy: List[float]


class DashboardSummary(BaseModel):
    """Quick summary for dashboard header"""
    overall_score: float
    proficiency_level: str
    proficiency_level_ko: str
    current_streak: int
    streak_emoji: str
    weekly_change: float
    total_vocabulary: int
    total_conversations: int


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/{user_id}", response_model=UserAnalytics)
async def get_user_analytics(user_id: str):
    """
    Get complete analytics for a user.
    
    Returns everything needed for the dashboard:
    - Overall score & proficiency level
    - Skill breakdown
    - Weak areas & recommendations  
    - Learning streak
    - Achievements
    - Daily statistics
    """
    
    return analytics_service.get_user_analytics(user_id)


@router.get("/{user_id}/summary", response_model=DashboardSummary)
async def get_dashboard_summary(user_id: str):
    """
    Get quick summary for dashboard header.
    
    Returns key metrics at a glance:
    - Overall score
    - Proficiency level
    - Current streak
    - Weekly change
    """
    
    analytics = analytics_service.get_user_analytics(user_id)
    
    # Calculate weekly change (mock for now)
    weekly_change = 0.0
    if len(analytics.daily_stats) >= 7:
        # Compare this week vs last week accuracy
        recent = analytics.daily_stats[-7:]
        total_recent = sum(s.correct_messages for s in recent)
        total_messages = sum(s.messages_sent for s in recent)
        if total_messages > 0:
            weekly_change = round((total_recent / total_messages - 0.7) * 100, 1)
    
    # Get proficiency level in Korean
    level_korean = {
        ProficiencyLevel.BEGINNER: "초급",
        ProficiencyLevel.ELEMENTARY: "초중급",
        ProficiencyLevel.INTERMEDIATE: "중급",
        ProficiencyLevel.UPPER_INT: "중상급",
        ProficiencyLevel.ADVANCED: "고급",
        ProficiencyLevel.NATIVE: "원어민급",
    }
    
    # Streak emoji
    streak = analytics.streak.current_streak
    if streak >= 30:
        streak_emoji = "🔥🔥🔥"
    elif streak >= 7:
        streak_emoji = "🔥🔥"
    elif streak >= 1:
        streak_emoji = "🔥"
    else:
        streak_emoji = "💤"
    
    return DashboardSummary(
        overall_score=analytics.overall_score,
        proficiency_level=analytics.proficiency_level.value,
        proficiency_level_ko=level_korean.get(analytics.proficiency_level, "초급"),
        current_streak=streak,
        streak_emoji=streak_emoji,
        weekly_change=weekly_change,
        total_vocabulary=analytics.total_vocabulary,
        total_conversations=analytics.total_conversations,
    )


@router.get("/{user_id}/skills", response_model=SkillBreakdown)
async def get_skill_breakdown(user_id: str):
    """
    Get skill scores breakdown for radar/bar chart.
    
    Returns:
    - Category names (Korean)
    - Scores (0-100)
    - Colors for chart
    """
    
    analytics = analytics_service.get_user_analytics(user_id)
    
    # Category names in Korean
    category_names = {
        SkillCategory.GRAMMAR: "문법",
        SkillCategory.SPEECH_LEVEL: "말투",
        SkillCategory.VOCABULARY: "어휘",
        SkillCategory.PARTICLES: "조사",
        SkillCategory.VERB_ENDINGS: "어미",
        SkillCategory.HONORIFICS: "존칭",
        SkillCategory.SPELLING: "맞춤법",
        SkillCategory.EXPRESSIONS: "표현",
    }
    
    # Colors for chart
    colors = [
        "#4CAF50",  # Green
        "#2196F3",  # Blue
        "#FF9800",  # Orange
        "#9C27B0",  # Purple
        "#F44336",  # Red
        "#00BCD4",  # Cyan
        "#FFEB3B",  # Yellow
        "#795548",  # Brown
    ]
    
    categories = []
    scores = []
    chart_colors = []
    
    for i, skill in enumerate(analytics.skill_scores):
        if skill.category in category_names:
            categories.append(category_names[skill.category])
            scores.append(skill.score)
            chart_colors.append(colors[i % len(colors)])
    
    return SkillBreakdown(
        categories=categories,
        scores=scores,
        colors=chart_colors,
    )


@router.get("/{user_id}/progress", response_model=ProgressChart)
async def get_progress_chart(
    user_id: str,
    days: int = Query(7, ge=1, le=30, description="Number of days"),
):
    """
    Get progress data for line chart.
    
    Returns daily data for:
    - Dates
    - Accuracy scores
    - Message counts
    """
    
    daily_stats = analytics_service.get_daily_stats(user_id, days)
    
    return ProgressChart(
        dates=[s.date for s in daily_stats],
        scores=[s.accuracy for s in daily_stats],
        messages=[s.messages_sent for s in daily_stats],
        accuracy=[s.accuracy for s in daily_stats],
    )


@router.get("/{user_id}/weak-areas", response_model=List[WeakArea])
async def get_weak_areas(user_id: str):
    """
    Get identified weak areas with suggestions.
    
    Returns top weak areas sorted by priority:
    - Category name
    - Score
    - Error count
    - Example mistakes
    - Improvement suggestion
    """
    
    return analytics_service.identify_weak_areas(user_id)


@router.get("/{user_id}/achievements", response_model=List[Achievement])
async def get_achievements(user_id: str):
    """
    Get all achievements with progress.
    
    Returns:
    - Earned achievements
    - In-progress achievements
    - Progress percentage
    """
    
    return analytics_service.check_achievements(user_id)


@router.get("/{user_id}/streak", response_model=LearningStreak)
async def get_streak(user_id: str):
    """
    Get learning streak information.
    
    Returns:
    - Current streak days
    - Longest streak
    - Recent active dates
    """
    
    analytics = analytics_service.get_user_analytics(user_id)
    return analytics.streak


@router.get("/{user_id}/recommendations")
async def get_recommendations(user_id: str):
    """
    Get personalized learning recommendations.
    
    Based on:
    - Weak areas
    - Learning patterns
    - Goals
    """
    
    recommendations = analytics_service.generate_recommendations(user_id)
    
    return {
        "recommendations": recommendations,
        "generated_at": datetime.now().isoformat(),
    }


@router.get("/{user_id}/daily-stats")
async def get_daily_stats(
    user_id: str,
    days: int = Query(7, ge=1, le=30),
):
    """
    Get daily learning statistics.
    """
    
    stats = analytics_service.get_daily_stats(user_id, days)
    
    return {
        "days": days,
        "stats": [s.dict() for s in stats],
    }


# ============================================================================
# Recording Endpoints
# ============================================================================

@router.post("/{user_id}/record/message")
async def record_message(user_id: str, request: RecordMessageRequest):
    """
    Record a user message for analytics.
    
    Called after each message is analyzed.
    """
    
    analytics_service.record_message(
        user_id=user_id,
        has_error=request.has_error,
        error_types=request.error_types,
        original_text=request.original_text,
    )
    
    return {"status": "recorded"}


@router.post("/{user_id}/record/conversation")
async def record_conversation(user_id: str, request: RecordConversationRequest):
    """
    Record a completed conversation.
    
    Called when user ends a conversation.
    """
    
    analytics_service.record_conversation(
        user_id=user_id,
        duration_minutes=request.duration_minutes,
    )
    
    return {"status": "recorded"}


@router.post("/{user_id}/record/vocabulary")
async def record_vocabulary(user_id: str, request: RecordVocabularyRequest):
    """
    Record vocabulary learning activity.
    
    Called during vocabulary review sessions.
    """
    
    analytics_service.record_vocabulary(
        user_id=user_id,
        learned=request.learned,
        reviewed=request.reviewed,
    )
    
    return {"status": "recorded"}


@router.post("/{user_id}/record/skill")
async def record_skill(user_id: str, request: RecordSkillRequest):
    """
    Record skill practice.
    
    Called during focused skill practice.
    """
    
    analytics_service.record_skill_practice(
        user_id=user_id,
        category=request.category,
        correct=request.correct,
    )
    
    return {"status": "recorded"}


# ============================================================================
# Chart Data Endpoints (Formatted for Charts)
# ============================================================================

@router.get("/{user_id}/chart/radar")
async def get_radar_chart_data(user_id: str):
    """
    Get data formatted for radar/spider chart.
    
    Shows skill distribution.
    """
    
    breakdown = await get_skill_breakdown(user_id)
    
    return {
        "labels": breakdown.categories,
        "datasets": [{
            "label": "스킬 점수",
            "data": breakdown.scores,
            "backgroundColor": "rgba(54, 162, 235, 0.2)",
            "borderColor": "rgb(54, 162, 235)",
        }]
    }


@router.get("/{user_id}/chart/progress")
async def get_progress_line_chart(
    user_id: str,
    days: int = Query(7, ge=1, le=30),
):
    """
    Get data formatted for line chart.
    
    Shows progress over time.
    """
    
    progress = await get_progress_chart(user_id, days)
    
    return {
        "labels": progress.dates,
        "datasets": [
            {
                "label": "정확도 (%)",
                "data": progress.accuracy,
                "borderColor": "#4CAF50",
                "fill": False,
            },
            {
                "label": "메시지 수",
                "data": progress.messages,
                "borderColor": "#2196F3",
                "fill": False,
            }
        ]
    }


@router.get("/{user_id}/chart/weak-areas")
async def get_weak_areas_bar_chart(user_id: str):
    """
    Get data formatted for bar chart.
    
    Shows weak areas comparison.
    """
    
    weak_areas = await get_weak_areas(user_id)
    
    return {
        "labels": [w.category for w in weak_areas],
        "datasets": [{
            "label": "점수",
            "data": [w.score for w in weak_areas],
            "backgroundColor": [
                "#F44336" if w.priority == "high" else
                "#FF9800" if w.priority == "medium" else
                "#4CAF50"
                for w in weak_areas
            ],
        }]
    }
