"""
Context-Aware Chat Service
Combines CLOVA chat with mistake tracking for personalized learning
"""

import logging
from typing import Optional, List, Dict, Any

from app.services.clova_service import clova_service
from app.services.mistake_tracker import mistake_tracker, MistakeTracker
from app.services.session_memory import session_memory
from app.services.politeness_service import politeness_service
from app.core.constants import AVATARS
from app.schemas.context_schemas import (
    UserLearningContext, MistakeRecord, 
    ContextAwareChatRequest, ContextAwareChatResponse
)

logger = logging.getLogger(__name__)


class ContextAwareChatService:
    """
    Chat service with context awareness and personalized feedback.
    
    Features:
    - Tracks user mistakes over time
    - Provides personalized tips based on mistake patterns
    - Remembers user's strengths and weaknesses
    - Encourages improvements
    """
    
    def __init__(self):
        self.clova = clova_service
        self.tracker = mistake_tracker
        
    async def chat(
        self,
        request: ContextAwareChatRequest
    ) -> ContextAwareChatResponse:
        """
        Process chat with context awareness.
        
        Args:
            request: Chat request with optional user context
            
        Returns:
            ContextAwareChatResponse with personalized feedback
        """
        # Get or create user context
        user_id = request.user_id or request.session_id or "anonymous"
        
        if request.user_context:
            # Use provided context (from backend)
            context = request.user_context
        else:
            # Use session memory (for demo)
            context = session_memory.get_or_create(user_id)
        
        # Get avatar info for expected formality
        avatar = AVATARS.get(request.avatar_id, AVATARS["sujin_friend"])
        expected_formality = avatar.get("formality", "polite")
        
        # Analyze user's message for mistakes
        mistakes = self.tracker.analyze_message(
            message=request.message,
            expected_formality=expected_formality,
            context=context
        )
        
        # Also get politeness analysis
        politeness = politeness_service.analyze(request.message)
        
        # Update context with new findings
        context = self.tracker.update_context(context, mistakes, request.message)
        
        # Track topic and avatar usage
        if request.topic and request.topic not in context.topics_practiced:
            context.topics_practiced.append(request.topic)
        if request.avatar_id not in context.avatars_used:
            context.avatars_used.append(request.avatar_id)
        
        # Generate personalized tips
        tips = []
        if request.include_mistake_feedback and mistakes:
            tips = self.tracker.generate_personalized_tips(context, mistakes)
        
        # Check for improvements
        improvements = self._check_improvements(context, mistakes)
        
        # Build enhanced system prompt with context
        enhanced_prompt = self._build_context_aware_prompt(
            avatar_id=request.avatar_id,
            context=context,
            recent_mistakes=mistakes
        )
        
        # Get CLOVA response
        messages = [{"role": "user", "content": request.message}]
        
        try:
            response_content = await self.clova.chat(
                messages=messages,
                avatar_id=request.avatar_id,
                topic=request.topic,
                max_tokens=256,
                temperature=0.7
            )
            
            if response_content["status"] == "success":
                response_text = response_content["content"]
            else:
                response_text = self._get_fallback_response(avatar, mistakes)
        except Exception as e:
            logger.error(f"CLOVA chat error: {e}")
            response_text = self._get_fallback_response(avatar, mistakes)
        
        # Update session memory
        session_memory.update(user_id, context)
        
        return ContextAwareChatResponse(
            response=response_text,
            avatar_id=request.avatar_id,
            politeness_analysis=politeness,
            mistakes_found=mistakes,
            personalized_tips=tips,
            improvements_noticed=improvements,
            updated_context=context,
            status="success"
        )
    
    def _build_context_aware_prompt(
        self,
        avatar_id: str,
        context: UserLearningContext,
        recent_mistakes: List[MistakeRecord]
    ) -> str:
        """Build system prompt with user context awareness."""
        
        # Get base avatar info
        avatar = AVATARS.get(avatar_id, AVATARS["sujin_friend"])
        
        # Build context-aware additions
        context_additions = []
        
        # User level awareness
        context_additions.append(f"사용자 레벨: {context.estimated_level}")
        
        # Common mistakes to gently correct
        if context.mistake_patterns:
            top_issues = sorted(
                context.mistake_patterns.items(),
                key=lambda x: x[1].count,
                reverse=True
            )[:2]
            
            if top_issues:
                issues_str = ", ".join([cat for cat, _ in top_issues])
                context_additions.append(
                    f"사용자가 자주 틀리는 부분: {issues_str}. "
                    "자연스럽게 올바른 표현을 보여주되, 직접적인 교정은 피하세요."
                )
        
        # Recent mistakes in this message
        if recent_mistakes:
            context_additions.append(
                "이번 메시지에서 약간의 실수가 있지만, 대화를 자연스럽게 이어가세요."
            )
        
        # Encouragement for improvements
        improving = [cat for cat, p in context.mistake_patterns.items() if p.improving]
        if improving:
            context_additions.append(
                f"사용자가 {improving[0]}에서 발전하고 있어요! 격려해 주세요."
            )
        
        return "\n".join(context_additions)
    
    def _check_improvements(
        self, 
        context: UserLearningContext,
        current_mistakes: List[MistakeRecord]
    ) -> List[str]:
        """Check if user is improving in any areas."""
        improvements = []
        
        current_categories = set(m.category.value for m in current_mistakes)
        
        for category, pattern in context.mistake_patterns.items():
            # If user used to make this mistake but didn't this time
            if pattern.count >= 3 and category not in current_categories:
                if pattern.improving:
                    improvements.append(
                        f"🎉 {self._category_to_korean(category)} 실력이 늘고 있어요!"
                    )
        
        return improvements[:2]  # Max 2 improvements
    
    def _category_to_korean(self, category: str) -> str:
        """Convert category to Korean name."""
        names = {
            "formality": "말투",
            "particles": "조사",
            "honorifics": "높임말",
            "verb_conjugation": "동사 활용",
            "spelling": "맞춤법",
            "vocabulary": "어휘",
            "tense": "시제",
        }
        return names.get(category, category)
    
    def _get_fallback_response(
        self, 
        avatar: Dict, 
        mistakes: List[MistakeRecord]
    ) -> str:
        """Get fallback response when CLOVA fails."""
        formality = avatar.get("formality", "polite")
        
        base_responses = {
            "informal": [
                "응응, 그렇구나!",
                "오 진짜? 재밌다!",
                "아~ 그렇구나!"
            ],
            "polite": [
                "네, 알겠어요!",
                "아, 그렇군요!",
                "네, 재미있네요!"
            ],
            "very_polite": [
                "네, 알겠습니다.",
                "아, 그렇군요.",
                "네, 흥미롭습니다."
            ]
        }
        
        import random
        responses = base_responses.get(formality, base_responses["polite"])
        return random.choice(responses)
    
    def get_user_summary(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get learning summary for a user."""
        context = session_memory.get(user_id)
        if not context:
            return None
        
        return self.tracker.generate_summary(context)
    
    def reset_user_context(self, user_id: str) -> bool:
        """Reset user's learning context."""
        return session_memory.delete(user_id)


# Singleton instance
context_aware_chat = ContextAwareChatService()
