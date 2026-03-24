"""
User Analytics Service - Korean Skills Dashboard

Tracks and analyzes user's Korean language learning progress.

Features:
1. Overall proficiency score
2. Skill breakdown (grammar, speech level, vocabulary, etc.)
3. Progress over time
4. Weak areas identification
5. Learning streaks
6. Personalized recommendations
7. Achievement tracking
8. Comparison with goals

Data Sources:
- Chat conversations (corrections)
- Grammar classifier results
- Vocabulary spaced repetition
- Memory service (topics discussed)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import json

from pydantic import BaseModel, Field


# ============================================================================
# Enums & Models
# ============================================================================

class SkillCategory(str, Enum):
    """Korean language skill categories"""
    GRAMMAR = "grammar"              # 문법
    SPEECH_LEVEL = "speech_level"    # 말투 (존댓말/반말)
    VOCABULARY = "vocabulary"        # 어휘
    PARTICLES = "particles"          # 조사
    VERB_ENDINGS = "verb_endings"    # 어미
    HONORIFICS = "honorifics"        # 존칭
    SPELLING = "spelling"            # 맞춤법
    EXPRESSIONS = "expressions"      # 표현
    LISTENING = "listening"          # 듣기 (future)
    PRONUNCIATION = "pronunciation"  # 발음 (future)


class ProficiencyLevel(str, Enum):
    """Korean proficiency levels"""
    BEGINNER = "beginner"        # 초급 (0-30)
    ELEMENTARY = "elementary"    # 초중급 (31-50)
    INTERMEDIATE = "intermediate" # 중급 (51-70)
    UPPER_INT = "upper_intermediate"  # 중상급 (71-85)
    ADVANCED = "advanced"        # 고급 (86-95)
    NATIVE = "native"            # 원어민급 (96-100)


class TimeRange(str, Enum):
    """Time ranges for analytics"""
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    ALL_TIME = "all_time"


# ============================================================================
# Data Models
# ============================================================================

class SkillScore(BaseModel):
    """Score for a specific skill"""
    category: SkillCategory
    score: float  # 0-100
    total_attempts: int = 0
    correct_attempts: int = 0
    trend: str = "stable"  # "improving", "declining", "stable"
    trend_percent: float = 0.0
    last_practice: Optional[datetime] = None


class DailyStats(BaseModel):
    """Daily learning statistics"""
    date: str  # YYYY-MM-DD
    messages_sent: int = 0
    correct_messages: int = 0
    errors_made: int = 0
    vocabulary_learned: int = 0
    vocabulary_reviewed: int = 0
    practice_minutes: int = 0
    conversations: int = 0
    accuracy: float = 0.0


class WeakArea(BaseModel):
    """Identified weak area"""
    category: str
    score: float
    error_count: int
    examples: List[str] = []
    suggestion: str = ""
    priority: str = "medium"  # "high", "medium", "low"


class Achievement(BaseModel):
    """User achievement"""
    id: str
    name_ko: str
    name_en: str
    description: str
    icon: str
    earned: bool = False
    earned_date: Optional[str] = None
    progress: float = 0.0  # 0-100
    target: int = 0
    current: int = 0


class LearningStreak(BaseModel):
    """Learning streak information"""
    current_streak: int = 0
    longest_streak: int = 0
    last_active: Optional[str] = None
    streak_dates: List[str] = []


class ProgressSnapshot(BaseModel):
    """Progress at a point in time"""
    date: str
    overall_score: float
    skill_scores: Dict[str, float]
    vocabulary_count: int
    conversations_count: int


class UserAnalytics(BaseModel):
    """Complete user analytics"""
    user_id: str
    
    # Overall
    overall_score: float = 0.0
    proficiency_level: ProficiencyLevel = ProficiencyLevel.BEGINNER
    
    # Skills breakdown
    skill_scores: List[SkillScore] = []
    
    # Weak areas
    weak_areas: List[WeakArea] = []
    strong_areas: List[str] = []
    
    # Progress
    daily_stats: List[DailyStats] = []
    progress_history: List[ProgressSnapshot] = []
    
    # Streaks
    streak: LearningStreak = LearningStreak()
    
    # Achievements
    achievements: List[Achievement] = []
    
    # Recommendations
    recommendations: List[str] = []
    next_goals: List[str] = []
    
    # Summary stats
    total_conversations: int = 0
    total_messages: int = 0
    total_vocabulary: int = 0
    total_practice_time: int = 0  # minutes
    
    # Dates
    joined_date: Optional[str] = None
    last_active: Optional[str] = None


# ============================================================================
# In-Memory Storage (Replace with DB in production)
# ============================================================================

@dataclass
class UserData:
    """User learning data storage"""
    user_id: str
    
    # Error tracking
    error_counts: Dict[str, int] = field(default_factory=dict)
    correct_counts: Dict[str, int] = field(default_factory=dict)
    
    # Daily data
    daily_stats: Dict[str, DailyStats] = field(default_factory=dict)
    
    # Progress snapshots
    snapshots: List[ProgressSnapshot] = field(default_factory=list)
    
    # Streak
    active_dates: List[str] = field(default_factory=list)
    
    # Achievements
    earned_achievements: List[str] = field(default_factory=list)
    
    # Examples of errors
    error_examples: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    
    # Timestamps
    joined: str = ""
    last_active: str = ""


# Global storage
user_data_store: Dict[str, UserData] = {}


# ============================================================================
# Achievements Definition
# ============================================================================

ACHIEVEMENTS = [
    Achievement(
        id="first_chat",
        name_ko="첫 대화",
        name_en="First Conversation",
        description="첫 번째 대화를 완료했습니다",
        icon="💬",
        target=1,
    ),
    Achievement(
        id="streak_7",
        name_ko="일주일 연속",
        name_en="7-Day Streak",
        description="7일 연속으로 학습했습니다",
        icon="🔥",
        target=7,
    ),
    Achievement(
        id="streak_30",
        name_ko="한 달 연속",
        name_en="30-Day Streak",
        description="30일 연속으로 학습했습니다",
        icon="🏆",
        target=30,
    ),
    Achievement(
        id="vocab_50",
        name_ko="어휘 50개",
        name_en="50 Words",
        description="50개의 단어를 학습했습니다",
        icon="📚",
        target=50,
    ),
    Achievement(
        id="vocab_100",
        name_ko="어휘 100개",
        name_en="100 Words",
        description="100개의 단어를 학습했습니다",
        icon="📖",
        target=100,
    ),
    Achievement(
        id="perfect_10",
        name_ko="완벽한 10개",
        name_en="Perfect 10",
        description="10개의 메시지를 연속으로 오류 없이 보냈습니다",
        icon="💯",
        target=10,
    ),
    Achievement(
        id="speech_master",
        name_ko="말투 마스터",
        name_en="Speech Level Master",
        description="말투 정확도 90% 이상 달성",
        icon="👑",
        target=90,
    ),
    Achievement(
        id="conversations_10",
        name_ko="대화 10회",
        name_en="10 Conversations",
        description="10번의 대화를 완료했습니다",
        icon="🗣️",
        target=10,
    ),
    Achievement(
        id="conversations_50",
        name_ko="대화 50회",
        name_en="50 Conversations",
        description="50번의 대화를 완료했습니다",
        icon="🎯",
        target=50,
    ),
    Achievement(
        id="grammar_master",
        name_ko="문법 마스터",
        name_en="Grammar Master",
        description="문법 정확도 90% 이상 달성",
        icon="✨",
        target=90,
    ),
]


# ============================================================================
# Analytics Service
# ============================================================================

class AnalyticsService:
    """Service for tracking and analyzing user's Korean learning progress"""
    
    def __init__(self):
        self.data_store = user_data_store
    
    def _get_user_data(self, user_id: str) -> UserData:
        """Get or create user data"""
        if user_id not in self.data_store:
            self.data_store[user_id] = UserData(
                user_id=user_id,
                joined=datetime.now().strftime("%Y-%m-%d"),
                last_active=datetime.now().strftime("%Y-%m-%d"),
            )
        return self.data_store[user_id]
    
    def _get_today(self) -> str:
        """Get today's date string"""
        return datetime.now().strftime("%Y-%m-%d")
    
    # ========================================================================
    # Data Recording
    # ========================================================================
    
    def record_message(
        self,
        user_id: str,
        has_error: bool,
        error_types: List[str] = [],
        original_text: str = "",
    ):
        """Record a user message and its analysis"""
        
        data = self._get_user_data(user_id)
        today = self._get_today()
        
        # Update last active
        data.last_active = today
        
        # Update active dates for streak
        if today not in data.active_dates:
            data.active_dates.append(today)
        
        # Get or create daily stats
        if today not in data.daily_stats:
            data.daily_stats[today] = DailyStats(date=today)
        
        stats = data.daily_stats[today]
        stats.messages_sent += 1
        
        if has_error:
            stats.errors_made += 1
            for error_type in error_types:
                data.error_counts[error_type] = data.error_counts.get(error_type, 0) + 1
                # Store example (max 5 per type)
                if len(data.error_examples[error_type]) < 5:
                    data.error_examples[error_type].append(original_text)
        else:
            stats.correct_messages += 1
            data.correct_counts["total"] = data.correct_counts.get("total", 0) + 1
        
        # Update accuracy
        if stats.messages_sent > 0:
            stats.accuracy = round(stats.correct_messages / stats.messages_sent * 100, 1)
    
    def record_conversation(self, user_id: str, duration_minutes: int = 5):
        """Record a completed conversation"""
        
        data = self._get_user_data(user_id)
        today = self._get_today()
        
        if today not in data.daily_stats:
            data.daily_stats[today] = DailyStats(date=today)
        
        stats = data.daily_stats[today]
        stats.conversations += 1
        stats.practice_minutes += duration_minutes
    
    def record_vocabulary(
        self,
        user_id: str,
        learned: int = 0,
        reviewed: int = 0,
    ):
        """Record vocabulary learning"""
        
        data = self._get_user_data(user_id)
        today = self._get_today()
        
        if today not in data.daily_stats:
            data.daily_stats[today] = DailyStats(date=today)
        
        stats = data.daily_stats[today]
        stats.vocabulary_learned += learned
        stats.vocabulary_reviewed += reviewed
    
    def record_skill_practice(
        self,
        user_id: str,
        category: str,
        correct: bool,
    ):
        """Record practice for a specific skill"""
        
        data = self._get_user_data(user_id)
        
        key = f"skill_{category}"
        if correct:
            data.correct_counts[key] = data.correct_counts.get(key, 0) + 1
        else:
            data.error_counts[key] = data.error_counts.get(key, 0) + 1
    
    # ========================================================================
    # Analytics Calculation
    # ========================================================================
    
    def calculate_skill_score(
        self,
        user_id: str,
        category: SkillCategory,
    ) -> SkillScore:
        """Calculate score for a specific skill"""
        
        data = self._get_user_data(user_id)
        
        key = f"skill_{category.value}"
        correct = data.correct_counts.get(key, 0)
        errors = data.error_counts.get(category.value, 0)
        total = correct + errors
        
        if total == 0:
            score = 50.0  # Default
        else:
            score = round(correct / total * 100, 1)
        
        # Calculate trend (compare last 7 days vs previous 7 days)
        trend = "stable"
        trend_percent = 0.0
        
        return SkillScore(
            category=category,
            score=score,
            total_attempts=total,
            correct_attempts=correct,
            trend=trend,
            trend_percent=trend_percent,
        )
    
    def calculate_overall_score(self, user_id: str) -> float:
        """Calculate overall proficiency score"""
        
        data = self._get_user_data(user_id)
        
        # Weighted average of different components
        weights = {
            "accuracy": 0.3,      # Message accuracy
            "vocabulary": 0.2,   # Vocabulary size
            "consistency": 0.2,  # Learning streak
            "skills": 0.3,       # Skill scores
        }
        
        # Calculate accuracy score
        total_messages = sum(s.messages_sent for s in data.daily_stats.values())
        correct_messages = sum(s.correct_messages for s in data.daily_stats.values())
        accuracy_score = (correct_messages / max(1, total_messages)) * 100
        
        # Calculate vocabulary score (capped at 100)
        total_vocab = sum(s.vocabulary_learned for s in data.daily_stats.values())
        vocab_score = min(100, total_vocab * 2)  # 50 words = 100%
        
        # Calculate consistency score
        streak = self._calculate_streak(user_id)
        consistency_score = min(100, streak.current_streak * 10)  # 10 days = 100%
        
        # Calculate average skill score
        skill_scores = []
        for category in [SkillCategory.GRAMMAR, SkillCategory.SPEECH_LEVEL, 
                         SkillCategory.VOCABULARY, SkillCategory.PARTICLES]:
            skill = self.calculate_skill_score(user_id, category)
            if skill.total_attempts > 0:
                skill_scores.append(skill.score)
        
        avg_skill_score = sum(skill_scores) / max(1, len(skill_scores)) if skill_scores else 50
        
        # Calculate weighted average
        overall = (
            weights["accuracy"] * accuracy_score +
            weights["vocabulary"] * vocab_score +
            weights["consistency"] * consistency_score +
            weights["skills"] * avg_skill_score
        )
        
        return round(overall, 1)
    
    def _calculate_streak(self, user_id: str) -> LearningStreak:
        """Calculate learning streak"""
        
        data = self._get_user_data(user_id)
        
        if not data.active_dates:
            return LearningStreak()
        
        # Sort dates
        sorted_dates = sorted(data.active_dates, reverse=True)
        
        # Calculate current streak
        current_streak = 0
        today = datetime.now().date()
        
        for i, date_str in enumerate(sorted_dates):
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            expected_date = today - timedelta(days=i)
            
            if date == expected_date:
                current_streak += 1
            elif date == expected_date - timedelta(days=1) and i == 0:
                # Allow 1 day gap for "yesterday was last active"
                continue
            else:
                break
        
        # Calculate longest streak
        longest_streak = current_streak
        temp_streak = 1
        
        for i in range(1, len(sorted_dates)):
            prev_date = datetime.strptime(sorted_dates[i-1], "%Y-%m-%d").date()
            curr_date = datetime.strptime(sorted_dates[i], "%Y-%m-%d").date()
            
            if (prev_date - curr_date).days == 1:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 1
        
        return LearningStreak(
            current_streak=current_streak,
            longest_streak=longest_streak,
            last_active=sorted_dates[0] if sorted_dates else None,
            streak_dates=sorted_dates[:7],  # Last 7 active dates
        )
    
    def identify_weak_areas(self, user_id: str) -> List[WeakArea]:
        """Identify user's weak areas"""
        
        data = self._get_user_data(user_id)
        weak_areas = []
        
        # Error type to category mapping
        error_categories = {
            "speech_level": ("말투", "존댓말과 반말을 상황에 맞게 사용하는 연습을 해보세요"),
            "particle": ("조사", "은/는, 이/가, 을/를 등의 조사 사용을 연습해보세요"),
            "verb_ending": ("어미", "동사와 형용사의 어미 변화를 연습해보세요"),
            "tense": ("시제", "과거, 현재, 미래 시제 표현을 연습해보세요"),
            "honorific": ("존칭", "높임말 사용을 연습해보세요"),
            "spelling": ("맞춤법", "자주 틀리는 맞춤법을 복습해보세요"),
            "pronoun": ("대명사", "상황에 맞는 대명사(나/저) 사용을 연습해보세요"),
        }
        
        for error_type, count in data.error_counts.items():
            if error_type.startswith("skill_"):
                continue
                
            if error_type in error_categories and count >= 2:
                category_name, suggestion = error_categories[error_type]
                
                # Calculate score for this category
                correct = data.correct_counts.get(f"skill_{error_type}", 0)
                total = correct + count
                score = (correct / total * 100) if total > 0 else 0
                
                # Determine priority
                if score < 50:
                    priority = "high"
                elif score < 70:
                    priority = "medium"
                else:
                    priority = "low"
                
                weak_areas.append(WeakArea(
                    category=category_name,
                    score=round(score, 1),
                    error_count=count,
                    examples=data.error_examples.get(error_type, [])[:3],
                    suggestion=suggestion,
                    priority=priority,
                ))
        
        # Sort by priority and error count
        priority_order = {"high": 0, "medium": 1, "low": 2}
        weak_areas.sort(key=lambda x: (priority_order[x.priority], -x.error_count))
        
        return weak_areas[:5]  # Top 5 weak areas
    
    def check_achievements(self, user_id: str) -> List[Achievement]:
        """Check and update achievements"""
        
        data = self._get_user_data(user_id)
        streak = self._calculate_streak(user_id)
        
        achievements = []
        
        for ach in ACHIEVEMENTS:
            achievement = Achievement(**ach.dict())
            
            # Calculate progress based on achievement type
            if ach.id == "first_chat":
                total_convos = sum(s.conversations for s in data.daily_stats.values())
                achievement.current = min(total_convos, ach.target)
                
            elif ach.id == "streak_7":
                achievement.current = min(streak.current_streak, ach.target)
                
            elif ach.id == "streak_30":
                achievement.current = min(streak.current_streak, ach.target)
                
            elif ach.id == "vocab_50" or ach.id == "vocab_100":
                total_vocab = sum(s.vocabulary_learned for s in data.daily_stats.values())
                achievement.current = min(total_vocab, ach.target)
                
            elif ach.id == "conversations_10" or ach.id == "conversations_50":
                total_convos = sum(s.conversations for s in data.daily_stats.values())
                achievement.current = min(total_convos, ach.target)
                
            elif ach.id == "speech_master":
                skill = self.calculate_skill_score(user_id, SkillCategory.SPEECH_LEVEL)
                achievement.current = int(skill.score)
                
            elif ach.id == "grammar_master":
                skill = self.calculate_skill_score(user_id, SkillCategory.GRAMMAR)
                achievement.current = int(skill.score)
            
            # Calculate progress percentage
            achievement.progress = round(achievement.current / ach.target * 100, 1)
            achievement.earned = achievement.current >= ach.target
            
            if achievement.earned and ach.id not in data.earned_achievements:
                achievement.earned_date = self._get_today()
                data.earned_achievements.append(ach.id)
            
            achievements.append(achievement)
        
        return achievements
    
    def get_daily_stats(
        self,
        user_id: str,
        days: int = 7,
    ) -> List[DailyStats]:
        """Get daily stats for the last N days"""
        
        data = self._get_user_data(user_id)
        
        result = []
        today = datetime.now().date()
        
        for i in range(days):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            if date in data.daily_stats:
                result.append(data.daily_stats[date])
            else:
                result.append(DailyStats(date=date))
        
        return list(reversed(result))
    
    def generate_recommendations(self, user_id: str) -> List[str]:
        """Generate personalized recommendations"""
        
        weak_areas = self.identify_weak_areas(user_id)
        streak = self._calculate_streak(user_id)
        data = self._get_user_data(user_id)
        
        recommendations = []
        
        # Streak-based recommendations
        if streak.current_streak == 0:
            recommendations.append("오늘 첫 대화를 시작해보세요! 매일 조금씩 연습하면 실력이 늘어요.")
        elif streak.current_streak < 7:
            recommendations.append(f"현재 {streak.current_streak}일 연속 학습 중! 7일 달성까지 {7 - streak.current_streak}일 남았어요.")
        
        # Weak area recommendations
        for weak in weak_areas[:2]:
            if weak.priority == "high":
                recommendations.append(f"'{weak.category}' 연습이 필요해요: {weak.suggestion}")
        
        # Vocabulary recommendations
        total_vocab = sum(s.vocabulary_learned for s in data.daily_stats.values())
        if total_vocab < 50:
            recommendations.append(f"어휘력을 늘려보세요! 현재 {total_vocab}개 학습, 50개까지 {50 - total_vocab}개 남았어요.")
        
        # Practice time recommendations
        today = self._get_today()
        today_stats = data.daily_stats.get(today)
        if not today_stats or today_stats.practice_minutes < 10:
            recommendations.append("오늘 10분만 더 연습해보세요! 짧은 시간이라도 매일 하는 것이 중요해요.")
        
        return recommendations[:5]
    
    def get_proficiency_level(self, score: float) -> ProficiencyLevel:
        """Get proficiency level from score"""
        
        if score >= 96:
            return ProficiencyLevel.NATIVE
        elif score >= 86:
            return ProficiencyLevel.ADVANCED
        elif score >= 71:
            return ProficiencyLevel.UPPER_INT
        elif score >= 51:
            return ProficiencyLevel.INTERMEDIATE
        elif score >= 31:
            return ProficiencyLevel.ELEMENTARY
        else:
            return ProficiencyLevel.BEGINNER
    
    # ========================================================================
    # Main Analytics Method
    # ========================================================================
    
    def get_user_analytics(self, user_id: str) -> UserAnalytics:
        """Get complete analytics for a user"""
        
        data = self._get_user_data(user_id)
        
        # Calculate overall score
        overall_score = self.calculate_overall_score(user_id)
        proficiency_level = self.get_proficiency_level(overall_score)
        
        # Calculate skill scores
        skill_scores = []
        for category in SkillCategory:
            if category not in [SkillCategory.LISTENING, SkillCategory.PRONUNCIATION]:
                skill_scores.append(self.calculate_skill_score(user_id, category))
        
        # Get weak and strong areas
        weak_areas = self.identify_weak_areas(user_id)
        strong_areas = [
            s.category.value for s in skill_scores 
            if s.score >= 80 and s.total_attempts >= 5
        ]
        
        # Get daily stats
        daily_stats = self.get_daily_stats(user_id, 7)
        
        # Get streak
        streak = self._calculate_streak(user_id)
        
        # Get achievements
        achievements = self.check_achievements(user_id)
        
        # Get recommendations
        recommendations = self.generate_recommendations(user_id)
        
        # Calculate totals
        total_conversations = sum(s.conversations for s in data.daily_stats.values())
        total_messages = sum(s.messages_sent for s in data.daily_stats.values())
        total_vocabulary = sum(s.vocabulary_learned for s in data.daily_stats.values())
        total_practice_time = sum(s.practice_minutes for s in data.daily_stats.values())
        
        return UserAnalytics(
            user_id=user_id,
            overall_score=overall_score,
            proficiency_level=proficiency_level,
            skill_scores=skill_scores,
            weak_areas=weak_areas,
            strong_areas=strong_areas,
            daily_stats=daily_stats,
            streak=streak,
            achievements=achievements,
            recommendations=recommendations,
            total_conversations=total_conversations,
            total_messages=total_messages,
            total_vocabulary=total_vocabulary,
            total_practice_time=total_practice_time,
            joined_date=data.joined,
            last_active=data.last_active,
        )


# ============================================================================
# Global Instance
# ============================================================================

analytics_service = AnalyticsService()
