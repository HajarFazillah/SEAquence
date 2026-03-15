"""
Avatar Management Service
CRUD operations for avatars and user-avatar progress tracking
"""

import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.schemas.avatar_schemas import (
    Avatar,
    AvatarCreate,
    AvatarUpdate,
    AvatarRole,
    AvatarDifficulty,
    AvatarFormality,
    UserAvatarProgress,
    UserAvatarSummary,
    EnhancedUserProfile,
)

logger = logging.getLogger(__name__)


# ===========================================
# Default System Avatars
# ===========================================

DEFAULT_AVATARS = {
    "minsu_senior": {
        "avatar_id": "minsu_senior",
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
        "voice_id": "nara",
        "is_system": True,
    },
    "professor_kim": {
        "avatar_id": "professor_kim",
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
        "is_system": True,
    },
    "sujin_friend": {
        "avatar_id": "sujin_friend",
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
        "is_system": True,
    },
    "manager_lee": {
        "avatar_id": "manager_lee",
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
        "is_system": True,
    },
    "jiwon_junior": {
        "avatar_id": "jiwon_junior",
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
        "is_system": True,
    },
}


class AvatarService:
    """
    Service for managing avatars.
    
    Features:
    - CRUD operations for avatars
    - System default avatars
    - Custom user-created avatars
    - User-avatar progress tracking
    """
    
    def __init__(self):
        # In-memory storage (replace with DB in production)
        self._avatars: Dict[str, Avatar] = {}
        self._user_profiles: Dict[str, EnhancedUserProfile] = {}
        self._user_avatar_progress: Dict[str, Dict[str, UserAvatarProgress]] = {}
        
        # Initialize system avatars
        self._init_system_avatars()
    
    def _init_system_avatars(self):
        """Initialize default system avatars."""
        now = datetime.now().isoformat()
        
        for avatar_id, data in DEFAULT_AVATARS.items():
            self._avatars[avatar_id] = Avatar(
                **data,
                created_at=now,
                updated_at=now,
                total_sessions=0,
                total_users=0
            )
    
    # ===========================================
    # Avatar CRUD
    # ===========================================
    
    def create_avatar(
        self,
        data: AvatarCreate,
        created_by: Optional[str] = None
    ) -> Avatar:
        """Create a new custom avatar."""
        now = datetime.now().isoformat()
        
        # Generate ID if not provided
        avatar_id = data.avatar_id or f"avatar_{uuid.uuid4().hex[:8]}"
        
        # Check if ID exists
        if avatar_id in self._avatars:
            raise ValueError(f"Avatar ID already exists: {avatar_id}")
        
        avatar = Avatar(
            avatar_id=avatar_id,
            name_ko=data.name_ko,
            name_en=data.name_en,
            role=data.role,
            age=data.age,
            gender=data.gender,
            personality=data.personality,
            formality=data.formality,
            difficulty=data.difficulty,
            topics=data.topics,
            greeting=data.greeting,
            voice_id=data.voice_id,
            is_system=False,
            created_by=created_by or data.created_by,
            created_at=now,
            updated_at=now
        )
        
        self._avatars[avatar_id] = avatar
        
        # Add to user's custom avatars list
        if created_by:
            profile = self._user_profiles.get(created_by)
            if profile:
                profile.custom_avatars.append(avatar_id)
        
        logger.info(f"Created avatar: {avatar_id} by {created_by}")
        return avatar
    
    def get_avatar(self, avatar_id: str) -> Optional[Avatar]:
        """Get avatar by ID."""
        return self._avatars.get(avatar_id)
    
    def update_avatar(
        self,
        avatar_id: str,
        data: AvatarUpdate,
        user_id: Optional[str] = None
    ) -> Optional[Avatar]:
        """Update an avatar."""
        avatar = self._avatars.get(avatar_id)
        if not avatar:
            return None
        
        # Only allow updating custom avatars (not system avatars)
        if avatar.is_system:
            raise ValueError("Cannot modify system avatars")
        
        # Check ownership
        if user_id and avatar.created_by != user_id:
            raise ValueError("You don't own this avatar")
        
        # Update fields
        if data.name_ko is not None:
            avatar.name_ko = data.name_ko
        if data.name_en is not None:
            avatar.name_en = data.name_en
        if data.personality is not None:
            avatar.personality = data.personality
        if data.topics is not None:
            avatar.topics = data.topics
        if data.greeting is not None:
            avatar.greeting = data.greeting
        if data.difficulty is not None:
            avatar.difficulty = data.difficulty
        if data.voice_id is not None:
            avatar.voice_id = data.voice_id
        
        avatar.updated_at = datetime.now().isoformat()
        
        return avatar
    
    def delete_avatar(
        self,
        avatar_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """Delete a custom avatar."""
        avatar = self._avatars.get(avatar_id)
        if not avatar:
            return False
        
        if avatar.is_system:
            raise ValueError("Cannot delete system avatars")
        
        if user_id and avatar.created_by != user_id:
            raise ValueError("You don't own this avatar")
        
        del self._avatars[avatar_id]
        
        # Remove from user's custom avatars
        if avatar.created_by:
            profile = self._user_profiles.get(avatar.created_by)
            if profile and avatar_id in profile.custom_avatars:
                profile.custom_avatars.remove(avatar_id)
        
        logger.info(f"Deleted avatar: {avatar_id}")
        return True
    
    def list_avatars(
        self,
        include_system: bool = True,
        include_custom: bool = True,
        created_by: Optional[str] = None,
        difficulty: Optional[str] = None,
        role: Optional[str] = None
    ) -> List[Avatar]:
        """List avatars with optional filters."""
        avatars = []
        
        for avatar in self._avatars.values():
            # Filter by type
            if avatar.is_system and not include_system:
                continue
            if not avatar.is_system and not include_custom:
                continue
            
            # Filter by creator
            if created_by and avatar.created_by != created_by:
                if not avatar.is_system:  # Always include system avatars
                    continue
            
            # Filter by difficulty
            if difficulty and avatar.difficulty != difficulty:
                continue
            
            # Filter by role
            if role and avatar.role != role:
                continue
            
            avatars.append(avatar)
        
        return avatars
    
    def get_system_avatars(self) -> List[Avatar]:
        """Get only system avatars."""
        return self.list_avatars(include_system=True, include_custom=False)
    
    def get_user_custom_avatars(self, user_id: str) -> List[Avatar]:
        """Get avatars created by a specific user."""
        return self.list_avatars(
            include_system=False,
            include_custom=True,
            created_by=user_id
        )
    
    # ===========================================
    # User Profile Management
    # ===========================================
    
    def create_user_profile(
        self,
        user_id: str,
        username: Optional[str] = None,
        native_language: str = "English",
        korean_level: str = "intermediate",
        interests: List[str] = None,
        learning_goals: List[str] = None
    ) -> EnhancedUserProfile:
        """Create enhanced user profile."""
        now = datetime.now().isoformat()
        
        profile = EnhancedUserProfile(
            user_id=user_id,
            username=username,
            native_language=native_language,
            korean_level=korean_level,
            interests=interests or [],
            learning_goals=learning_goals or [],
            created_at=now,
            updated_at=now,
            last_active=now
        )
        
        self._user_profiles[user_id] = profile
        self._user_avatar_progress[user_id] = {}
        
        return profile
    
    def get_user_profile(self, user_id: str) -> Optional[EnhancedUserProfile]:
        """Get user profile."""
        return self._user_profiles.get(user_id)
    
    def update_user_profile(
        self,
        user_id: str,
        **updates
    ) -> Optional[EnhancedUserProfile]:
        """Update user profile."""
        profile = self._user_profiles.get(user_id)
        if not profile:
            return None
        
        for key, value in updates.items():
            if hasattr(profile, key) and value is not None:
                setattr(profile, key, value)
        
        profile.updated_at = datetime.now().isoformat()
        return profile
    
    # ===========================================
    # User-Avatar Progress
    # ===========================================
    
    def get_user_avatar_progress(
        self,
        user_id: str,
        avatar_id: str
    ) -> Optional[UserAvatarProgress]:
        """Get progress for specific user-avatar pair."""
        user_progress = self._user_avatar_progress.get(user_id, {})
        return user_progress.get(avatar_id)
    
    def update_user_avatar_progress(
        self,
        user_id: str,
        avatar_id: str,
        session_score: float,
        messages_count: int,
        duration_minutes: int
    ) -> UserAvatarProgress:
        """Update progress after a chat session."""
        # Ensure user profile exists
        profile = self._user_profiles.get(user_id)
        if not profile:
            profile = self.create_user_profile(user_id)
        
        # Get or create avatar progress
        if user_id not in self._user_avatar_progress:
            self._user_avatar_progress[user_id] = {}
        
        user_progress = self._user_avatar_progress[user_id]
        
        avatar = self._avatars.get(avatar_id)
        avatar_name = avatar.name_ko if avatar else avatar_id
        
        if avatar_id not in user_progress:
            now = datetime.now().isoformat()
            user_progress[avatar_id] = UserAvatarProgress(
                user_id=user_id,
                avatar_id=avatar_id,
                avatar_name=avatar_name,
                first_chat=now
            )
            
            # Update avatar stats
            if avatar:
                avatar.total_users += 1
            
            # Add to user's used avatars
            if avatar_id not in profile.avatars_used:
                profile.avatars_used.append(avatar_id)
        
        progress = user_progress[avatar_id]
        
        # Update session stats
        progress.total_sessions += 1
        progress.total_messages += messages_count
        progress.total_time_minutes += duration_minutes
        progress.last_chat = datetime.now().isoformat()
        
        # Update scores
        progress.recent_scores.append(int(session_score))
        if len(progress.recent_scores) > 20:
            progress.recent_scores = progress.recent_scores[-20:]
        
        progress.average_score = sum(progress.recent_scores) / len(progress.recent_scores)
        progress.best_score = max(progress.best_score, int(session_score))
        
        # Update friendship (gamification)
        progress.friendship_points += int(session_score / 10) + messages_count
        progress.friendship_level = min(10, 1 + progress.friendship_points // 100)
        
        # Update user's overall stats
        profile.total_sessions += 1
        profile.total_messages += messages_count
        profile.total_practice_minutes += duration_minutes
        profile.last_active = datetime.now().isoformat()
        
        # Recalculate overall average
        all_scores = []
        for ap in user_progress.values():
            all_scores.extend(ap.recent_scores)
        if all_scores:
            profile.overall_average_score = sum(all_scores) / len(all_scores)
        
        # Store progress in profile
        profile.avatar_progress[avatar_id] = progress
        
        # Update avatar stats
        if avatar:
            avatar.total_sessions += 1
        
        return progress
    
    def get_user_avatar_summary(self, user_id: str) -> UserAvatarSummary:
        """Get summary of user's interactions with all avatars."""
        user_progress = self._user_avatar_progress.get(user_id, {})
        
        progress_list = list(user_progress.values())
        
        # Find favorite avatar (most sessions)
        favorite = None
        if progress_list:
            favorite = max(progress_list, key=lambda p: p.total_sessions).avatar_id
        
        return UserAvatarSummary(
            user_id=user_id,
            total_avatars_used=len(progress_list),
            favorite_avatar=favorite,
            avatar_progress=progress_list
        )
    
    def get_recommended_avatar(self, user_id: str) -> Optional[str]:
        """Get recommended avatar for user based on their progress."""
        profile = self._user_profiles.get(user_id)
        if not profile:
            return "sujin_friend"  # Default for new users
        
        # Get user's weak skills (from progress service if available)
        korean_level = profile.korean_level
        
        # Recommend based on level
        if korean_level == "beginner":
            # Easy avatars for beginners
            candidates = ["sujin_friend", "jiwon_junior"]
        elif korean_level == "advanced":
            # Hard avatars for advanced
            candidates = ["professor_kim", "manager_lee"]
        else:
            # Medium for intermediate
            candidates = ["minsu_senior"]
        
        # Find least practiced avatar from candidates
        user_progress = self._user_avatar_progress.get(user_id, {})
        
        for avatar_id in candidates:
            if avatar_id not in user_progress:
                return avatar_id  # New avatar to try
        
        # Return least practiced
        min_sessions = float('inf')
        recommended = candidates[0]
        for avatar_id in candidates:
            if avatar_id in user_progress:
                sessions = user_progress[avatar_id].total_sessions
                if sessions < min_sessions:
                    min_sessions = sessions
                    recommended = avatar_id
        
        return recommended


# Singleton instance
avatar_service = AvatarService()
