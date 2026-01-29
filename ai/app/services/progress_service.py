"""
Progress Tracking Service
Tracks user progress, errors, and skill development over time
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict

from app.schemas.user_schemas import (
    UserProfile,
    UserSkills,
    SkillLevel,
    UserErrors,
    ErrorRecord,
    UserProgress,
    SessionSummary,
    UserContext,
)

logger = logging.getLogger(__name__)


class ProgressService:
    """
    Service for tracking and analyzing user progress.
    
    In production, this would connect to a database.
    For now, uses in-memory storage for demonstration.
    """
    
    def __init__(self):
        # In-memory storage (replace with DB in production)
        self._profiles: Dict[str, UserProfile] = {}
        self._skills: Dict[str, UserSkills] = {}
        self._errors: Dict[str, UserErrors] = {}
        self._progress: Dict[str, UserProgress] = {}
        self._sessions: Dict[str, List[SessionSummary]] = defaultdict(list)
    
    # ===========================================
    # Profile Management
    # ===========================================
    
    def create_profile(
        self,
        user_id: str,
        native_language: str = "English",
        korean_level: str = "intermediate",
        interests: List[str] = None,
        learning_goals: List[str] = None
    ) -> UserProfile:
        """Create a new user profile."""
        now = datetime.now().isoformat()
        
        profile = UserProfile(
            user_id=user_id,
            native_language=native_language,
            korean_level=korean_level,
            interests=interests or ["daily_life", "cafe_food"],
            learning_goals=learning_goals or ["polite_speech"],
            created_at=now,
            updated_at=now
        )
        
        self._profiles[user_id] = profile
        
        # Initialize related data
        self._init_user_data(user_id, korean_level)
        
        return profile
    
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile."""
        return self._profiles.get(user_id)
    
    def update_profile(
        self,
        user_id: str,
        **updates
    ) -> Optional[UserProfile]:
        """Update user profile."""
        profile = self._profiles.get(user_id)
        if not profile:
            return None
        
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        profile.updated_at = datetime.now().isoformat()
        return profile
    
    def _init_user_data(self, user_id: str, korean_level: str):
        """Initialize user's skills, errors, and progress."""
        # Set initial skill levels based on Korean level
        base_level = {"beginner": 1, "intermediate": 2, "advanced": 4}.get(korean_level, 2)
        
        self._skills[user_id] = UserSkills(
            user_id=user_id,
            informal_speech=SkillLevel(skill_type="informal_speech", level=base_level + 1),
            polite_speech=SkillLevel(skill_type="polite_speech", level=base_level),
            formal_speech=SkillLevel(skill_type="formal_speech", level=base_level - 1 if base_level > 1 else 1),
            honorifics=SkillLevel(skill_type="honorifics", level=base_level - 1 if base_level > 1 else 1),
            vocabulary=SkillLevel(skill_type="vocabulary", level=base_level),
            grammar=SkillLevel(skill_type="grammar", level=base_level),
        )
        
        self._errors[user_id] = UserErrors(user_id=user_id, errors={})
        
        self._progress[user_id] = UserProgress(
            user_id=user_id,
            total_sessions=0,
            total_messages=0,
            overall_average_score=0.0,
        )
    
    # ===========================================
    # Skill Management
    # ===========================================
    
    def get_skills(self, user_id: str) -> Optional[UserSkills]:
        """Get user's skill levels."""
        return self._skills.get(user_id)
    
    def update_skill(
        self,
        user_id: str,
        skill_type: str,
        score: int,
        practiced: bool = True
    ):
        """Update a specific skill based on practice."""
        skills = self._skills.get(user_id)
        if not skills:
            return
        
        skill = getattr(skills, skill_type, None)
        if not skill:
            return
        
        # Add score to recent scores
        skill.recent_scores.append(score)
        if len(skill.recent_scores) > 10:
            skill.recent_scores = skill.recent_scores[-10:]
        
        # Update practice count
        if practiced:
            skill.total_practice += 1
            skill.last_practiced = datetime.now().isoformat()
        
        # Calculate if improving
        if len(skill.recent_scores) >= 3:
            recent_avg = sum(skill.recent_scores[-3:]) / 3
            older_avg = sum(skill.recent_scores[:-3]) / max(len(skill.recent_scores) - 3, 1)
            skill.is_improving = recent_avg > older_avg
        
        # Adjust level based on performance
        avg_score = sum(skill.recent_scores) / len(skill.recent_scores)
        if avg_score >= 85 and skill.level < 5:
            skill.level = min(5, skill.level + 1)
        elif avg_score < 50 and skill.level > 1:
            skill.level = max(1, skill.level - 1)
    
    def get_weak_skills(self, user_id: str, n: int = 2) -> List[str]:
        """Get user's weakest skills."""
        skills = self._skills.get(user_id)
        if not skills:
            return ["formal_speech", "honorifics"]  # Default
        return skills.get_weakest_skills(n)
    
    def get_strong_skills(self, user_id: str, n: int = 2) -> List[str]:
        """Get user's strongest skills."""
        skills = self._skills.get(user_id)
        if not skills:
            return ["informal_speech"]  # Default
        return skills.get_strongest_skills(n)
    
    # ===========================================
    # Error Tracking
    # ===========================================
    
    def record_error(
        self,
        user_id: str,
        error_type: str,
        name_ko: str,
        name_en: str,
        context: str = None
    ):
        """Record an error occurrence."""
        errors = self._errors.get(user_id)
        if not errors:
            errors = UserErrors(user_id=user_id, errors={})
            self._errors[user_id] = errors
        
        if error_type not in errors.errors:
            errors.errors[error_type] = ErrorRecord(
                error_type=error_type,
                name_ko=name_ko,
                name_en=name_en
            )
        
        error = errors.errors[error_type]
        error.total_count += 1
        error.this_week_count += 1
        error.this_session_count += 1
        error.last_occurrence = datetime.now().isoformat()
        
        if context and context not in error.common_contexts:
            error.common_contexts.append(context)
            if len(error.common_contexts) > 5:
                error.common_contexts = error.common_contexts[-5:]
    
    def get_errors(self, user_id: str) -> Optional[UserErrors]:
        """Get user's error records."""
        return self._errors.get(user_id)
    
    def get_common_errors(self, user_id: str, n: int = 3) -> List[str]:
        """Get user's most common error types."""
        errors = self._errors.get(user_id)
        if not errors:
            return []
        
        common = errors.get_most_common_errors(n)
        return [e.error_type for e in common]
    
    def reset_session_errors(self, user_id: str):
        """Reset session error counts (call at session start)."""
        errors = self._errors.get(user_id)
        if errors:
            for error in errors.errors.values():
                error.this_session_count = 0
    
    def reset_weekly_errors(self, user_id: str):
        """Reset weekly error counts (call weekly)."""
        errors = self._errors.get(user_id)
        if errors:
            for error in errors.errors.values():
                # Check if improving
                if error.this_week_count < error.total_count / max(1, self._get_weeks_active(user_id)):
                    error.is_decreasing = True
                else:
                    error.is_decreasing = False
                error.this_week_count = 0
    
    def _get_weeks_active(self, user_id: str) -> int:
        """Get number of weeks user has been active."""
        profile = self._profiles.get(user_id)
        if not profile or not profile.created_at:
            return 1
        
        created = datetime.fromisoformat(profile.created_at)
        weeks = (datetime.now() - created).days // 7
        return max(1, weeks)
    
    # ===========================================
    # Progress Tracking
    # ===========================================
    
    def get_progress(self, user_id: str) -> Optional[UserProgress]:
        """Get user's overall progress."""
        return self._progress.get(user_id)
    
    def record_session(
        self,
        user_id: str,
        session_summary: SessionSummary
    ):
        """Record a completed session."""
        progress = self._progress.get(user_id)
        if not progress:
            progress = UserProgress(user_id=user_id)
            self._progress[user_id] = progress
        
        # Update totals
        progress.total_sessions += 1
        progress.total_messages += session_summary.total_messages
        progress.total_practice_minutes += session_summary.duration_seconds // 60
        
        # Update scores
        if session_summary.highest_score > progress.best_score:
            progress.best_score = session_summary.highest_score
        
        # Recalculate average
        old_total = progress.overall_average_score * (progress.total_sessions - 1)
        progress.overall_average_score = (old_total + session_summary.average_score) / progress.total_sessions
        
        # Add to recent sessions
        progress.recent_sessions.append(session_summary)
        if len(progress.recent_sessions) > 10:
            progress.recent_sessions = progress.recent_sessions[-10:]
        
        # Update score history
        today = datetime.now().strftime("%Y-%m-%d")
        progress.score_history.append({
            "date": today,
            "score": session_summary.average_score,
            "session_id": session_summary.session_id
        })
        if len(progress.score_history) > 30:
            progress.score_history = progress.score_history[-30:]
        
        # Calculate improvement trend
        self._calculate_trend(progress)
        
        # Update last practice date
        progress.last_practice_date = today
        
        # Store session
        self._sessions[user_id].append(session_summary)
    
    def _calculate_trend(self, progress: UserProgress):
        """Calculate improvement trend."""
        if len(progress.score_history) < 3:
            progress.trend = "stable"
            progress.improvement_rate = 0.0
            return
        
        recent = progress.score_history[-7:] if len(progress.score_history) >= 7 else progress.score_history
        older = progress.score_history[:-7] if len(progress.score_history) > 7 else []
        
        recent_avg = sum(s["score"] for s in recent) / len(recent)
        
        if older:
            older_avg = sum(s["score"] for s in older) / len(older)
            improvement = ((recent_avg - older_avg) / older_avg) * 100
            progress.improvement_rate = round(improvement, 1)
            
            if improvement > 5:
                progress.trend = "improving"
            elif improvement < -5:
                progress.trend = "declining"
            else:
                progress.trend = "stable"
        else:
            progress.trend = "stable"
            progress.improvement_rate = 0.0
    
    # ===========================================
    # User Context Generation
    # ===========================================
    
    def get_user_context(self, user_id: str) -> UserContext:
        """
        Generate user context for API requests.
        This is what Backend sends to AI server.
        """
        profile = self._profiles.get(user_id)
        skills = self._skills.get(user_id)
        errors = self._errors.get(user_id)
        progress = self._progress.get(user_id)
        
        # Defaults if user not found
        if not profile:
            return UserContext(
                user_id=user_id,
                korean_level="intermediate"
            )
        
        # Build context
        weak_skills = skills.get_weakest_skills(2) if skills else []
        strong_skills = skills.get_strongest_skills(2) if skills else []
        common_errors = self.get_common_errors(user_id, 3)
        
        # Get recent errors (from last session)
        recent_errors = []
        if errors:
            recent = errors.get_recent_errors(3)
            recent_errors = [e.error_type for e in recent if e.this_session_count > 0]
        
        return UserContext(
            user_id=user_id,
            korean_level=profile.korean_level,
            weak_skills=weak_skills,
            strong_skills=strong_skills,
            common_errors=common_errors,
            recent_errors=recent_errors,
            sessions_completed=progress.total_sessions if progress else 0,
            average_score=progress.overall_average_score if progress else 0.0,
            trend=progress.trend if progress else "stable",
            interests=profile.interests,
            learning_goals=profile.learning_goals,
            feedback_language=profile.feedback_language,
            show_hints=profile.show_hints
        )
    
    # ===========================================
    # Analytics
    # ===========================================
    
    def get_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for user."""
        profile = self._profiles.get(user_id)
        skills = self._skills.get(user_id)
        errors = self._errors.get(user_id)
        progress = self._progress.get(user_id)
        
        if not profile:
            return {"error": "User not found"}
        
        # Skill chart data
        skill_data = {}
        if skills:
            skill_data = {
                "informal_speech": skills.informal_speech.level,
                "polite_speech": skills.polite_speech.level,
                "formal_speech": skills.formal_speech.level,
                "honorifics": skills.honorifics.level,
            }
        
        # Error breakdown
        error_data = {}
        if errors:
            for error_type, record in errors.errors.items():
                error_data[error_type] = {
                    "total": record.total_count,
                    "this_week": record.this_week_count,
                    "is_decreasing": record.is_decreasing
                }
        
        return {
            "user_id": user_id,
            "korean_level": profile.korean_level,
            "days_active": self._get_weeks_active(user_id) * 7,
            "total_sessions": progress.total_sessions if progress else 0,
            "total_practice_minutes": progress.total_practice_minutes if progress else 0,
            "overall_score": progress.overall_average_score if progress else 0,
            "trend": progress.trend if progress else "stable",
            "improvement_rate": progress.improvement_rate if progress else 0,
            "skill_levels": skill_data,
            "error_breakdown": error_data,
            "score_history": progress.score_history if progress else [],
            "weak_areas": skills.get_weakest_skills(2) if skills else [],
            "strong_areas": skills.get_strongest_skills(2) if skills else [],
        }


# Singleton instance
progress_service = ProgressService()
