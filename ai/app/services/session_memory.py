"""
Session Memory Service
Maintains user learning context in memory for demo purposes.
In production, this should be handled by the backend.
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from threading import Lock

from app.schemas.context_schemas import UserLearningContext

logger = logging.getLogger(__name__)


class SessionMemory:
    """
    In-memory session storage for user learning contexts.
    
    Note: This is for demo/testing purposes only.
    In production, user context should be stored in the backend database
    and passed to the AI server with each request.
    """
    
    def __init__(self, max_sessions: int = 1000, session_ttl_hours: int = 24):
        self._sessions: Dict[str, UserLearningContext] = {}
        self._lock = Lock()
        self.max_sessions = max_sessions
        self.session_ttl = timedelta(hours=session_ttl_hours)
        
    def get_or_create(self, user_id: str) -> UserLearningContext:
        """
        Get existing session or create a new one.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            UserLearningContext for the user
        """
        with self._lock:
            # Clean expired sessions periodically
            self._cleanup_expired()
            
            if user_id in self._sessions:
                context = self._sessions[user_id]
                context.last_active = datetime.now()
                return context
            
            # Create new context
            context = UserLearningContext(user_id=user_id)
            self._sessions[user_id] = context
            logger.info(f"Created new session for user: {user_id}")
            return context
    
    def update(self, user_id: str, context: UserLearningContext) -> None:
        """Update user's learning context."""
        with self._lock:
            context.last_active = datetime.now()
            self._sessions[user_id] = context
    
    def get(self, user_id: str) -> Optional[UserLearningContext]:
        """Get user's context if exists."""
        with self._lock:
            return self._sessions.get(user_id)
    
    def delete(self, user_id: str) -> bool:
        """Delete user's session."""
        with self._lock:
            if user_id in self._sessions:
                del self._sessions[user_id]
                return True
            return False
    
    def _cleanup_expired(self) -> None:
        """Remove expired sessions."""
        now = datetime.now()
        expired = [
            uid for uid, ctx in self._sessions.items()
            if now - ctx.last_active > self.session_ttl
        ]
        for uid in expired:
            del self._sessions[uid]
            logger.debug(f"Cleaned up expired session: {uid}")
        
        # Also enforce max sessions (LRU-style)
        if len(self._sessions) > self.max_sessions:
            # Sort by last_active and remove oldest
            sorted_sessions = sorted(
                self._sessions.items(),
                key=lambda x: x[1].last_active
            )
            to_remove = len(self._sessions) - self.max_sessions
            for uid, _ in sorted_sessions[:to_remove]:
                del self._sessions[uid]
    
    def get_stats(self) -> Dict:
        """Get memory usage stats."""
        with self._lock:
            return {
                "active_sessions": len(self._sessions),
                "max_sessions": self.max_sessions,
                "session_ttl_hours": self.session_ttl.total_seconds() / 3600
            }


# Singleton instance
session_memory = SessionMemory()
