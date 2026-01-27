"""
Chat Service
Orchestrates conversation flow with avatars
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.core.constants import AVATARS, get_safe_topics
from app.services.clova_service import clova_service
from app.services.topic_service import topic_service
from app.services.politeness_service import politeness_service

logger = logging.getLogger(__name__)


class ChatSession:
    """Represents an active chat session."""
    
    def __init__(
        self,
        session_id: str,
        user_id: str,
        avatar_id: str,
        topic: Optional[str] = None
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.avatar_id = avatar_id
        self.topic = topic
        self.messages: List[Dict[str, Any]] = []
        self.scores: List[int] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_message(
        self,
        role: str,
        content: str,
        feedback: Optional[Dict[str, Any]] = None
    ):
        """Add a message to the session."""
        self.messages.append({
            "role": role,
            "content": content,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
        
        if feedback and "score" in feedback:
            self.scores.append(feedback["score"])
    
    def get_history(self, max_turns: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation history for LLM context."""
        recent = self.messages[-(max_turns * 2):]
        return [{"role": m["role"], "content": m["content"]} for m in recent]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get session summary."""
        duration = (self.updated_at - self.created_at).seconds
        avg_score = sum(self.scores) / len(self.scores) if self.scores else 0
        
        return {
            "session_id": self.session_id,
            "avatar_id": self.avatar_id,
            "total_turns": len([m for m in self.messages if m["role"] == "user"]),
            "duration_seconds": duration,
            "average_score": round(avg_score, 1),
            "started_at": self.created_at.isoformat(),
            "ended_at": self.updated_at.isoformat(),
        }


class ChatService:
    """
    Service for managing chat conversations with avatars.
    
    Handles:
    - Session management
    - Message processing
    - Avatar response generation
    - Politeness feedback
    """
    
    def __init__(self):
        # In-memory session storage (use Redis in production)
        self._sessions: Dict[str, ChatSession] = {}
    
    async def start_session(
        self,
        user_id: str,
        avatar_id: str,
        topic: Optional[str] = None,
        korean_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Start a new chat session.
        
        Args:
            user_id: User identifier
            avatar_id: Avatar to chat with
            topic: Initial conversation topic
            korean_level: User's Korean proficiency
            
        Returns:
            Session info with greeting
        """
        # Validate avatar
        avatar = AVATARS.get(avatar_id)
        if not avatar:
            avatar_id = "sujin_friend"
            avatar = AVATARS[avatar_id]
        
        # Validate topic
        if topic and topic_service.is_sensitive(topic):
            topic = None  # Reset sensitive topic
        
        # Create session
        session_id = str(uuid.uuid4())[:12]
        session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            avatar_id=avatar_id,
            topic=topic
        )
        
        self._sessions[session_id] = session
        
        # Get greeting
        greeting = avatar.get("greeting", "안녕하세요!")
        
        # Add greeting to history
        session.add_message("assistant", greeting)
        
        return {
            "session_id": session_id,
            "avatar_id": avatar_id,
            "avatar_name_ko": avatar["name_ko"],
            "avatar_name_en": avatar["name_en"],
            "greeting": greeting,
            "recommended_formality": avatar["formality"],
            "difficulty": avatar["difficulty"],
            "avatar_topics": avatar["topics"],
            "created_at": session.created_at.isoformat()
        }
    
    async def send_message(
        self,
        session_id: str,
        message: str,
        include_feedback: bool = True,
        include_audio: bool = False
    ) -> Dict[str, Any]:
        """
        Send a message and get avatar response.
        
        Args:
            session_id: Chat session ID
            message: User's message
            include_feedback: Whether to include politeness feedback
            include_audio: Whether to include TTS audio
            
        Returns:
            Dict with user_message, avatar_response, feedback, audio
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        avatar = AVATARS.get(session.avatar_id)
        
        # Detect topic from message if not set
        if not session.topic:
            detected = topic_service.detect(message, top_k=1)
            if detected and detected[0]["confidence"] > 0.3:
                session.topic = detected[0]["topic_id"]
        
        # Analyze politeness
        feedback = None
        if include_feedback:
            analysis = politeness_service.analyze(
                text=message,
                target_role=avatar["role"],
                target_age=avatar["age"]
            )
            feedback = {
                "level": analysis["level"],
                "level_ko": analysis["level_ko"],
                "score": analysis["score"],
                "is_appropriate": analysis["is_appropriate"],
                "feedback_ko": analysis["feedback_ko"],
                "feedback_en": analysis["feedback_en"]
            }
        
        # Add user message to session
        session.add_message("user", message, feedback)
        
        # Generate avatar response
        history = session.get_history(max_turns=5)
        
        try:
            avatar_response = await clova_service.generate_avatar_response(
                user_message=message,
                avatar_id=session.avatar_id,
                conversation_history=history[:-1],  # Exclude current message
                topic=session.topic
            )
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            # Fallback response
            avatar_response = self._get_fallback_response(avatar["formality"])
        
        # Add avatar response to session
        session.add_message("assistant", avatar_response)
        
        result = {
            "session_id": session_id,
            "user_message": {
                "content": message,
                "feedback": feedback
            },
            "avatar_response": {
                "content": avatar_response,
                "avatar_name": avatar["name_ko"]
            },
            "turn_count": len([m for m in session.messages if m["role"] == "user"]),
            "current_topic": session.topic
        }
        
        # Add TTS audio if requested
        if include_audio:
            from app.services.speech_service import voice_service
            audio_result = await voice_service.synthesize_for_avatar(
                text=avatar_response,
                avatar_id=session.avatar_id
            )
            if audio_result["status"] == "success":
                result["avatar_response"]["audio"] = audio_result["audio"]
                result["avatar_response"]["audio_format"] = audio_result["format"]
        
        return result
    
    async def end_session(self, session_id: str) -> Dict[str, Any]:
        """
        End a chat session and return summary.
        
        Args:
            session_id: Session to end
            
        Returns:
            Session summary with statistics
        """
        session = self._sessions.pop(session_id, None)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        summary = session.get_summary()
        
        # Calculate politeness breakdown
        level_counts = {"informal": 0, "polite": 0, "very_polite": 0}
        for msg in session.messages:
            if msg["role"] == "user" and msg.get("feedback"):
                level = msg["feedback"].get("level", "polite")
                level_counts[level] = level_counts.get(level, 0) + 1
        
        summary["politeness_breakdown"] = level_counts
        
        # Generate improvement suggestions
        summary["suggestions"] = self._generate_suggestions(
            session.scores,
            level_counts,
            AVATARS[session.avatar_id]["formality"]
        )
        
        return summary
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get session by ID."""
        return self._sessions.get(session_id)
    
    def _get_fallback_response(self, formality: str) -> str:
        """Get fallback response based on formality level."""
        fallbacks = {
            "informal": "응? 다시 말해줘!",
            "polite": "죄송해요, 잘 못 들었어요. 다시 말씀해 주시겠어요?",
            "very_polite": "죄송합니다, 다시 한번 말씀해 주시겠습니까?",
        }
        return fallbacks.get(formality, "네?")
    
    def _generate_suggestions(
        self,
        scores: List[int],
        level_counts: Dict[str, int],
        recommended: str
    ) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        if avg_score < 50:
            suggestions.append("말투 수준을 높여보세요")
        
        if recommended == "very_polite" and level_counts.get("informal", 0) > 0:
            suggestions.append("격식체(-습니다)를 더 사용해보세요")
        
        if recommended == "polite" and level_counts.get("informal", 0) > level_counts.get("polite", 0):
            suggestions.append("존댓말(-요)을 더 사용해보세요")
        
        if avg_score >= 70:
            suggestions.append("잘하고 있어요! 계속 연습하세요 👍")
        
        if not suggestions:
            suggestions.append("다양한 상황에서 연습해보세요")
        
        return suggestions


# Singleton instance
chat_service = ChatService()
