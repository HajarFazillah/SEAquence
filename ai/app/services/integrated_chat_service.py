"""
Integrated Chat Service
Combines chat, analysis, revision, and sample reply in one flow
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.core.constants import AVATARS, TOPIC_TAXONOMY

logger = logging.getLogger(__name__)


class IntegratedChatService:
    """
    Integrated chat service that combines:
    1. Avatar chat response
    2. Politeness analysis
    3. Sentence revision
    4. Sample reply suggestions
    
    All powered by HyperCLOVA X
    """
    
    def __init__(self):
        # Import services
        from app.services.enhanced_clova_service import enhanced_clova_service
        from app.services.revision_service import revision_service
        from app.services.enhanced_politeness_service import enhanced_politeness_service
        
        self.clova = enhanced_clova_service
        self.revision = revision_service
        self.politeness = enhanced_politeness_service
        
        # Session storage
        self._sessions: Dict[str, Dict] = {}
    
    async def start_session(
        self,
        user_id: str,
        avatar_id: str,
        topic: Optional[str] = None,
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Start a new chat session."""
        import uuid
        
        session_id = str(uuid.uuid4())[:8]
        avatar = AVATARS.get(avatar_id, AVATARS.get("sujin_friend"))
        
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "avatar_id": avatar_id,
            "avatar": avatar,
            "topic": topic,
            "user_context": user_context or {},
            "messages": [],
            "scores": [],
            "revisions": [],
            "created_at": datetime.now().isoformat()
        }
        
        self._sessions[session_id] = session
        
        return {
            "session_id": session_id,
            "avatar_id": avatar_id,
            "avatar_name": avatar.get("name_ko"),
            "greeting": avatar.get("greeting", "안녕하세요!"),
            "recommended_formality": avatar.get("formality"),
            "topic": topic
        }
    
    async def send_message(
        self,
        session_id: str,
        message: str,
        include_revision: bool = True,
        include_samples: bool = True
    ) -> Dict[str, Any]:
        """
        Send a message and get comprehensive response.
        
        Returns:
        - Avatar's response
        - Politeness analysis
        - Revised sentence (if errors found)
        - Sample replies (how to say it better)
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")
        
        avatar = session["avatar"]
        avatar_id = session["avatar_id"]
        topic = session.get("topic")
        user_context = session.get("user_context", {})
        
        # 1. Analyze politeness
        analysis = self.politeness.analyze(
            text=message,
            target_role=avatar.get("role"),
            target_age=avatar.get("age")
        )
        
        # 2. Get revision if there are errors
        revision_result = None
        if include_revision and not analysis.is_appropriate:
            revision_result = await self.revision.revise_and_sample(
                user_sentence=message,
                target_role=avatar.get("role"),
                target_formality=avatar.get("formality"),
                context=topic,
                user_level=user_context.get("korean_level", "intermediate")
            )
        
        # 3. Generate avatar response
        conversation_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in session["messages"][-10:]  # Last 10 messages
        ]
        
        avatar_response = await self.clova.generate_avatar_response(
            user_message=message,
            avatar_id=avatar_id,
            conversation_history=conversation_history,
            topic=topic,
            user_context=user_context
        )
        
        # 4. Get sample replies if requested
        sample_replies = None
        if include_samples and not analysis.is_appropriate:
            # Generate sample of how user should have said it
            sample_replies = await self._generate_better_alternatives(
                original=message,
                target_formality=avatar.get("formality"),
                context=topic
            )
        
        # Store in session
        session["messages"].append({"role": "user", "content": message})
        session["messages"].append({"role": "assistant", "content": avatar_response})
        session["scores"].append(analysis.score)
        
        if revision_result:
            session["revisions"].append({
                "original": message,
                "revised": revision_result.get("revised"),
                "turn": len(session["scores"])
            })
        
        # Build response
        response = {
            "session_id": session_id,
            "turn": len(session["scores"]),
            
            # User's message analysis
            "user_message": {
                "content": message,
                "analysis": {
                    "level": analysis.level,
                    "level_ko": analysis.level_ko,
                    "score": analysis.score,
                    "is_appropriate": analysis.is_appropriate,
                    "expected_level": analysis.recommended_level,
                },
                "word_analysis": analysis.word_analysis[:5],  # Top 5 word issues
                "errors": analysis.errors[:3],  # Top 3 errors
            },
            
            # Avatar's response
            "avatar_response": {
                "content": avatar_response,
                "avatar_name": avatar.get("name_ko"),
                "formality": avatar.get("formality")
            },
            
            # Feedback
            "feedback": {
                "feedback_ko": analysis.feedback_ko,
                "feedback_en": analysis.feedback_en
            }
        }
        
        # Add revision if available
        if revision_result:
            response["revision"] = {
                "original": message,
                "revised": revision_result.get("revised"),
                "has_error": revision_result.get("has_error", False),
                "errors": revision_result.get("errors", []),
                "tips": revision_result.get("tips", [])
            }
        
        # Add sample replies if available
        if sample_replies:
            response["sample_replies"] = sample_replies
        
        return response
    
    async def _generate_better_alternatives(
        self,
        original: str,
        target_formality: str,
        context: Optional[str]
    ) -> List[Dict[str, str]]:
        """Generate better alternatives for user's message."""
        
        result = await self.revision.get_sample_reply(
            situation=f"User said: {original}",
            target_formality=target_formality,
            num_samples=2
        )
        
        samples = result.get("samples", [])
        return [
            {
                "korean": s.get("korean", ""),
                "formality": s.get("formality", target_formality),
                "note": s.get("usage_note", "")
            }
            for s in samples
        ]
    
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of the session with all revisions."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Calculate stats
        scores = session.get("scores", [])
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Get all revisions made
        revisions = session.get("revisions", [])
        
        return {
            "session_id": session_id,
            "avatar_id": session["avatar_id"],
            "avatar_name": session["avatar"]["name_ko"],
            "topic": session.get("topic"),
            
            # Stats
            "total_turns": len(scores),
            "average_score": round(avg_score, 1),
            "best_score": max(scores) if scores else 0,
            "worst_score": min(scores) if scores else 0,
            
            # Revisions made
            "total_revisions": len(revisions),
            "revisions": revisions,
            
            # Recommendations
            "improvement_areas": self._get_improvement_areas(session),
            "suggested_practice": self._get_practice_suggestions(session)
        }
    
    def _get_improvement_areas(self, session: Dict) -> List[str]:
        """Identify areas for improvement based on session."""
        areas = []
        
        revisions = session.get("revisions", [])
        if revisions:
            areas.append("문장 어미 사용 연습이 필요합니다")
        
        scores = session.get("scores", [])
        if scores and sum(scores) / len(scores) < 70:
            avatar = session.get("avatar", {})
            formality = avatar.get("formality", "polite")
            
            formality_names = {
                "informal": "반말",
                "polite": "존댓말",
                "very_polite": "격식체"
            }
            areas.append(f"{formality_names.get(formality, formality)} 연습이 더 필요합니다")
        
        return areas if areas else ["잘하고 있어요! 계속 연습하세요"]
    
    def _get_practice_suggestions(self, session: Dict) -> List[str]:
        """Get practice suggestions based on session."""
        avatar = session.get("avatar", {})
        formality = avatar.get("formality", "polite")
        
        suggestions = {
            "informal": [
                "친구와 일상 대화 연습을 더 해보세요",
                "~어/아 어미 사용을 연습하세요"
            ],
            "polite": [
                "선배와의 대화 연습을 더 해보세요",
                "~요 어미 사용을 익히세요"
            ],
            "very_polite": [
                "교수님/상사와의 대화 연습을 더 해보세요",
                "~습니다/~습니까 어미를 연습하세요",
                "높임말 (드리다, 여쭙다) 사용을 연습하세요"
            ]
        }
        
        return suggestions.get(formality, suggestions["polite"])


# Singleton instance
integrated_chat_service = IntegratedChatService()
