"""
Personalized Recommendation Service
Generates practice recommendations based on user's progress and weaknesses
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from app.schemas.user_schemas import (
    UserContext,
    UserProgress,
    UserSkills,
    UserErrors,
    PracticeRecommendation,
    UserRecommendations,
)
from app.core.constants import AVATARS, TOPIC_TAXONOMY, get_safe_topics

logger = logging.getLogger(__name__)


# ===========================================
# Skill to Avatar/Topic Mapping
# ===========================================

SKILL_AVATAR_MAP = {
    "formal_speech": ["professor_kim", "manager_lee"],
    "polite_speech": ["minsu_senior"],
    "informal_speech": ["sujin_friend", "jiwon_junior"],
    "honorifics": ["professor_kim", "manager_lee", "minsu_senior"],
}

SKILL_TOPIC_MAP = {
    "formal_speech": ["professor_meeting", "career_future"],
    "polite_speech": ["campus_life", "part_time_job"],
    "informal_speech": ["daily_life", "cafe_food", "kpop", "drama_movie"],
    "honorifics": ["professor_meeting", "part_time_job"],
}

ERROR_FOCUS_MAP = {
    "ending_mismatch": {
        "skill": "formal_speech",
        "tip_ko": "문장 끝을 '-습니다/-습니까'로 마무리하는 연습을 해보세요.",
        "tip_en": "Practice ending sentences with -습니다/-습니까."
    },
    "honorific_missing": {
        "skill": "honorifics",
        "tip_ko": "'드리다', '여쭙다', '계시다' 같은 높임말을 사용해보세요.",
        "tip_en": "Try using honorific verbs like 드리다, 여쭙다, 계시다."
    },
    "formality_mixed": {
        "skill": "formal_speech",
        "tip_ko": "한 문장 안에서 말투를 섞지 않도록 주의하세요.",
        "tip_en": "Be careful not to mix speech levels within a sentence."
    },
    "word_choice": {
        "skill": "vocabulary",
        "tip_ko": "'밥' 대신 '식사', '나' 대신 '저'처럼 격식 있는 단어를 선택하세요.",
        "tip_en": "Choose formal words like 식사 instead of 밥, 저 instead of 나."
    },
}


# ===========================================
# Motivation Messages
# ===========================================

MOTIVATION_MESSAGES = {
    "improving": {
        "ko": "열심히 하고 있어요! 실력이 늘고 있습니다 💪",
        "en": "Great job! Your skills are improving! 💪"
    },
    "stable": {
        "ko": "꾸준히 연습하고 있네요. 조금만 더 힘내세요! 🌟",
        "en": "You're practicing consistently. Keep it up! 🌟"
    },
    "declining": {
        "ko": "조금 어려워하고 있는 것 같아요. 기초부터 다시 연습해볼까요? 📚",
        "en": "Looks like you're struggling a bit. Let's review the basics? 📚"
    },
    "new_user": {
        "ko": "환영해요! 함께 한국어를 연습해봐요 🎉",
        "en": "Welcome! Let's practice Korean together 🎉"
    },
    "streak": {
        "ko": "{days}일 연속 연습 중! 대단해요! 🔥",
        "en": "{days} day streak! Amazing! 🔥"
    }
}


class RecommendationService:
    """
    Service for generating personalized practice recommendations.
    
    Analyzes user's:
    - Weak skills
    - Common errors
    - Learning goals
    - Interests
    - Progress trend
    
    To recommend:
    - Best avatar to practice with
    - Best topic to discuss
    - Specific skills to focus on
    - Personalized tips
    """
    
    def generate_recommendations(
        self,
        user_context: UserContext,
        skills: Optional[UserSkills] = None,
        errors: Optional[UserErrors] = None,
        progress: Optional[UserProgress] = None,
        num_recommendations: int = 3
    ) -> UserRecommendations:
        """
        Generate personalized recommendations for a user.
        
        Args:
            user_context: User's current context
            skills: User's skill levels (optional)
            errors: User's error history (optional)
            progress: User's progress data (optional)
            num_recommendations: Number of practice recommendations
            
        Returns:
            UserRecommendations with personalized suggestions
        """
        recommendations = []
        
        # 1. Recommendation based on weakest skill
        if user_context.weak_skills:
            weak_rec = self._recommend_for_skill(
                skill=user_context.weak_skills[0],
                priority=1,
                reason="weakest_skill"
            )
            if weak_rec:
                recommendations.append(weak_rec)
        
        # 2. Recommendation based on common errors
        if user_context.common_errors:
            error_rec = self._recommend_for_error(
                error_type=user_context.common_errors[0],
                priority=1,
                reason="common_error"
            )
            if error_rec and error_rec.recommended_avatar not in [r.recommended_avatar for r in recommendations]:
                recommendations.append(error_rec)
        
        # 3. Recommendation based on learning goals
        if user_context.learning_goals:
            goal_rec = self._recommend_for_goal(
                goal=user_context.learning_goals[0],
                priority=2,
                reason="learning_goal"
            )
            if goal_rec and goal_rec.recommended_avatar not in [r.recommended_avatar for r in recommendations]:
                recommendations.append(goal_rec)
        
        # 4. Recommendation based on interests (fun practice)
        if user_context.interests:
            fun_rec = self._recommend_for_interest(
                interest=user_context.interests[0],
                korean_level=user_context.korean_level,
                priority=3,
                reason="interest"
            )
            if fun_rec and fun_rec.recommended_avatar not in [r.recommended_avatar for r in recommendations]:
                recommendations.append(fun_rec)
        
        # 5. Fill with default recommendations if needed
        while len(recommendations) < num_recommendations:
            default_rec = self._get_default_recommendation(
                korean_level=user_context.korean_level,
                exclude_avatars=[r.recommended_avatar for r in recommendations],
                priority=3
            )
            if default_rec:
                recommendations.append(default_rec)
            else:
                break
        
        # Generate daily goals
        daily_goals = self._generate_daily_goals(user_context, progress)
        
        # Generate personalized tips
        tips = self._generate_tips(user_context)
        
        # Generate motivation message
        motivation_ko, motivation_en = self._generate_motivation(user_context, progress)
        
        return UserRecommendations(
            user_id=user_context.user_id,
            generated_at=datetime.now().isoformat(),
            recommended_practices=recommendations[:num_recommendations],
            daily_goals=daily_goals,
            personalized_tips=tips,
            motivation_message_ko=motivation_ko,
            motivation_message_en=motivation_en
        )
    
    def _recommend_for_skill(
        self,
        skill: str,
        priority: int,
        reason: str
    ) -> Optional[PracticeRecommendation]:
        """Generate recommendation to improve a specific skill."""
        avatars = SKILL_AVATAR_MAP.get(skill, [])
        topics = SKILL_TOPIC_MAP.get(skill, [])
        
        if not avatars or not topics:
            return None
        
        avatar_id = avatars[0]
        topic_id = topics[0]
        
        avatar = AVATARS.get(avatar_id, {})
        topic = TOPIC_TAXONOMY.get(topic_id, {})
        
        skill_names = {
            "formal_speech": ("격식체", "formal speech"),
            "polite_speech": ("존댓말", "polite speech"),
            "informal_speech": ("반말", "informal speech"),
            "honorifics": ("높임말", "honorifics"),
        }
        
        skill_ko, skill_en = skill_names.get(skill, (skill, skill))
        
        return PracticeRecommendation(
            recommended_avatar=avatar_id,
            avatar_name_ko=avatar.get("name_ko", avatar_id),
            recommended_topic=topic_id,
            topic_name_ko=topic.get("name_ko", topic_id),
            reason_ko=f"{skill_ko} 연습이 필요해요. {avatar.get('name_ko', '')}와 대화해보세요.",
            reason_en=f"You need to practice {skill_en}. Try talking with {avatar.get('name_en', '')}.",
            focus_skill=skill,
            focus_errors=[],
            difficulty=avatar.get("difficulty", "medium"),
            estimated_duration_minutes=10,
            priority=priority
        )
    
    def _recommend_for_error(
        self,
        error_type: str,
        priority: int,
        reason: str
    ) -> Optional[PracticeRecommendation]:
        """Generate recommendation to fix a specific error."""
        error_info = ERROR_FOCUS_MAP.get(error_type)
        if not error_info:
            return None
        
        skill = error_info["skill"]
        avatars = SKILL_AVATAR_MAP.get(skill, [])
        topics = SKILL_TOPIC_MAP.get(skill, [])
        
        if not avatars or not topics:
            return None
        
        avatar_id = avatars[0]
        topic_id = topics[0]
        
        avatar = AVATARS.get(avatar_id, {})
        topic = TOPIC_TAXONOMY.get(topic_id, {})
        
        return PracticeRecommendation(
            recommended_avatar=avatar_id,
            avatar_name_ko=avatar.get("name_ko", avatar_id),
            recommended_topic=topic_id,
            topic_name_ko=topic.get("name_ko", topic_id),
            reason_ko=f"자주 하는 실수를 고쳐봐요. {error_info['tip_ko']}",
            reason_en=f"Let's fix a common mistake. {error_info['tip_en']}",
            focus_skill=skill,
            focus_errors=[error_type],
            difficulty=avatar.get("difficulty", "medium"),
            estimated_duration_minutes=10,
            priority=priority
        )
    
    def _recommend_for_goal(
        self,
        goal: str,
        priority: int,
        reason: str
    ) -> Optional[PracticeRecommendation]:
        """Generate recommendation based on learning goal."""
        goal_map = {
            "formal_speech": ("professor_kim", "professor_meeting"),
            "polite_speech": ("minsu_senior", "campus_life"),
            "business_korean": ("manager_lee", "career_future"),
            "casual_conversation": ("sujin_friend", "daily_life"),
            "honorifics": ("professor_kim", "professor_meeting"),
        }
        
        if goal not in goal_map:
            return None
        
        avatar_id, topic_id = goal_map[goal]
        avatar = AVATARS.get(avatar_id, {})
        topic = TOPIC_TAXONOMY.get(topic_id, {})
        
        return PracticeRecommendation(
            recommended_avatar=avatar_id,
            avatar_name_ko=avatar.get("name_ko", avatar_id),
            recommended_topic=topic_id,
            topic_name_ko=topic.get("name_ko", topic_id),
            reason_ko=f"학습 목표에 맞는 연습이에요!",
            reason_en=f"This matches your learning goal!",
            focus_skill=goal,
            focus_errors=[],
            difficulty=avatar.get("difficulty", "medium"),
            estimated_duration_minutes=10,
            priority=priority
        )
    
    def _recommend_for_interest(
        self,
        interest: str,
        korean_level: str,
        priority: int,
        reason: str
    ) -> Optional[PracticeRecommendation]:
        """Generate fun recommendation based on interest."""
        if interest not in TOPIC_TAXONOMY:
            return None
        
        topic = TOPIC_TAXONOMY[interest]
        if topic.get("sensitive", False):
            return None
        
        # Match avatar to difficulty level
        difficulty_map = {
            "beginner": "sujin_friend",
            "intermediate": "minsu_senior",
            "advanced": "professor_kim"
        }
        avatar_id = difficulty_map.get(korean_level, "sujin_friend")
        avatar = AVATARS.get(avatar_id, {})
        
        return PracticeRecommendation(
            recommended_avatar=avatar_id,
            avatar_name_ko=avatar.get("name_ko", avatar_id),
            recommended_topic=interest,
            topic_name_ko=topic.get("name_ko", interest),
            reason_ko=f"좋아하는 주제로 재미있게 연습해요! 🎉",
            reason_en=f"Practice with a topic you enjoy! 🎉",
            focus_skill="general",
            focus_errors=[],
            difficulty=avatar.get("difficulty", "easy"),
            estimated_duration_minutes=10,
            priority=priority
        )
    
    def _get_default_recommendation(
        self,
        korean_level: str,
        exclude_avatars: List[str],
        priority: int
    ) -> Optional[PracticeRecommendation]:
        """Get a default recommendation."""
        # Find avatar not already recommended
        for avatar_id, avatar in AVATARS.items():
            if avatar_id not in exclude_avatars:
                topics = avatar.get("topics", ["daily_life"])
                topic_id = topics[0] if topics else "daily_life"
                topic = TOPIC_TAXONOMY.get(topic_id, {})
                
                return PracticeRecommendation(
                    recommended_avatar=avatar_id,
                    avatar_name_ko=avatar.get("name_ko", avatar_id),
                    recommended_topic=topic_id,
                    topic_name_ko=topic.get("name_ko", topic_id),
                    reason_ko="다양한 상황에서 연습해보세요!",
                    reason_en="Practice in different situations!",
                    focus_skill="general",
                    focus_errors=[],
                    difficulty=avatar.get("difficulty", "medium"),
                    estimated_duration_minutes=10,
                    priority=priority
                )
        return None
    
    def _generate_daily_goals(
        self,
        user_context: UserContext,
        progress: Optional[UserProgress]
    ) -> List[str]:
        """Generate personalized daily goals."""
        goals = []
        
        # Session goal
        sessions_today = 0  # Would track from progress
        if sessions_today == 0:
            goals.append("오늘 첫 대화 연습하기")
        elif sessions_today < 3:
            goals.append(f"오늘 {3 - sessions_today}번 더 연습하기")
        
        # Skill-specific goal
        if user_context.weak_skills:
            skill_names = {
                "formal_speech": "격식체(-습니다)",
                "polite_speech": "존댓말(-요)",
                "honorifics": "높임말",
            }
            weak = user_context.weak_skills[0]
            if weak in skill_names:
                goals.append(f"{skill_names[weak]} 3번 이상 사용하기")
        
        # Error-specific goal
        if user_context.common_errors:
            error_tips = {
                "ending_mismatch": "문장 끝 확인하고 말하기",
                "honorific_missing": "높임 표현 잊지 않기",
            }
            error = user_context.common_errors[0]
            if error in error_tips:
                goals.append(error_tips[error])
        
        # Score goal
        if progress and progress.overall_average_score > 0:
            target = min(100, int(progress.overall_average_score) + 5)
            goals.append(f"평균 점수 {target}점 이상 받기")
        
        return goals[:4]  # Max 4 goals
    
    def _generate_tips(self, user_context: UserContext) -> List[str]:
        """Generate personalized tips based on errors and weaknesses."""
        tips = []
        
        # Tips for common errors
        for error_type in user_context.common_errors[:2]:
            if error_type in ERROR_FOCUS_MAP:
                tips.append(ERROR_FOCUS_MAP[error_type]["tip_ko"])
        
        # Tips for weak skills
        skill_tips = {
            "formal_speech": "교수님이나 상사와 대화할 때는 '-습니다/-습니까'를 사용하세요.",
            "polite_speech": "선배나 처음 만난 사람에게는 '-요'를 붙이세요.",
            "honorifics": "'먹다→드시다', '있다→계시다'처럼 높임말을 연습해보세요.",
        }
        
        for skill in user_context.weak_skills[:2]:
            if skill in skill_tips and skill_tips[skill] not in tips:
                tips.append(skill_tips[skill])
        
        return tips[:4]  # Max 4 tips
    
    def _generate_motivation(
        self,
        user_context: UserContext,
        progress: Optional[UserProgress]
    ) -> tuple:
        """Generate motivational message."""
        if not progress or progress.total_sessions == 0:
            msg = MOTIVATION_MESSAGES["new_user"]
            return msg["ko"], msg["en"]
        
        # Check streak
        if progress.current_streak >= 3:
            msg = MOTIVATION_MESSAGES["streak"]
            return (
                msg["ko"].format(days=progress.current_streak),
                msg["en"].format(days=progress.current_streak)
            )
        
        # Based on trend
        trend = user_context.trend
        msg = MOTIVATION_MESSAGES.get(trend, MOTIVATION_MESSAGES["stable"])
        return msg["ko"], msg["en"]


# Singleton instance
recommendation_service = RecommendationService()
