"""
Session-Aware Chat Service
Handles chat with full session context from Backend
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.services.clova_service import clova_service
from app.services.mistake_tracker import mistake_tracker
from app.services.politeness_service import politeness_service
from app.services.emotion_service import emotion_calculator
from app.core.situations import get_situation, get_avatar_situation, SITUATIONS
from app.core.constants import AVATARS
from app.schemas.session_schemas import (
    SessionChatRequest, SessionChatResponse,
    StartSessionRequest, StartSessionResponse,
    EndSessionRequest, EndSessionResponse, SessionSummary,
    SessionKey, ChatMessage, MessageRole
)

logger = logging.getLogger(__name__)


class SessionAwareChatService:
    """
    Chat service that works with session context from Backend.
    
    Key Principle: AI Server is STATELESS
    - Backend stores all session data
    - Backend sends context with each request
    - AI Server processes and returns results
    - Backend stores results
    """
    
    def __init__(self):
        self.clova = clova_service
        self.tracker = mistake_tracker
        
    async def start_session(
        self,
        request: StartSessionRequest
    ) -> StartSessionResponse:
        """
        Initialize a new session.
        Returns avatar's opening line and situation context.
        
        Backend should:
        1. Call this when user starts new conversation
        2. Create session record in DB
        3. Store the session_id
        """
        # Get avatar info
        avatar = AVATARS.get(request.avatar_id)
        if not avatar:
            raise ValueError(f"Avatar not found: {request.avatar_id}")
        
        # Get situation info
        situation = get_situation(request.situation_id)
        if not situation:
            raise ValueError(f"Situation not found: {request.situation_id}")
        
        # Get avatar-specific situation config
        avatar_situation = get_avatar_situation(request.avatar_id, request.situation_id)
        
        # Determine opening message
        if avatar_situation and avatar_situation.get("opening_line"):
            opening_message = avatar_situation["opening_line"]
        else:
            # Use avatar's default greeting
            opening_message = avatar.get("greeting", "안녕하세요!")
        
        # Generate session ID (Backend can override this)
        session_id = f"sess_{request.user_id}_{request.avatar_id}_{request.situation_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return StartSessionResponse(
            session_id=session_id,
            session_key=SessionKey(
                user_id=request.user_id,
                avatar_id=request.avatar_id,
                situation_id=request.situation_id
            ),
            opening_message=opening_message,
            situation_name=situation.get("name_ko", ""),
            situation_goals=situation.get("goals_ko", []),
            expected_formality=situation.get("expected_formality", "polite"),
            tips=situation.get("tips_ko", []),
            key_expressions=situation.get("key_expressions", []),
            status="success"
        )
    
    async def chat(
        self,
        request: SessionChatRequest
    ) -> SessionChatResponse:
        """
        Process a chat message with full session context.
        
        Backend should:
        1. Load session from DB
        2. Load recent message history
        3. Send to this endpoint
        4. Store response and analysis in DB
        5. Update session stats
        """
        session_info = request.session_info
        session_key = session_info.session_key
        
        # Get avatar and situation
        avatar = AVATARS.get(session_key.avatar_id, AVATARS.get("sujin_friend"))
        situation = get_situation(session_key.situation_id) or {}
        
        # Get expected formality from situation
        expected_formality = situation.get("expected_formality", avatar.get("formality", "polite"))
        
        # Analyze user's message
        mistakes = self.tracker.analyze_message(
            message=request.message,
            expected_formality=expected_formality
        )
        
        # Get politeness analysis
        politeness = politeness_service.analyze(request.message)
        
        # Calculate score (simple scoring)
        score = self._calculate_score(mistakes, politeness, expected_formality)
        
        # Check situation appropriateness
        situation_appropriate = self._check_situation_appropriate(
            request.message, 
            situation, 
            politeness
        )
        
        # Check if any goals were achieved
        goals_achieved = self._check_goals_achieved(
            request.message,
            situation.get("goals_ko", []),
            session_info.situation_goals_completed
        )
        
        # Build conversation for CLOVA
        clova_messages = self._build_clova_messages(
            current_message=request.message,
            history=request.history.messages if request.history else [],
            avatar=avatar,
            situation=situation,
            max_history=request.max_history_messages
        )
        
        # Get CLOVA response
        try:
            clova_response = await self.clova.chat(
                messages=clova_messages,
                avatar_id=session_key.avatar_id,
                topic=session_key.situation_id,
                max_tokens=256,
                temperature=0.7
            )
            
            if clova_response.get("status") == "success":
                response_text = clova_response.get("content", "")
            else:
                response_text = self._get_fallback_response(avatar, situation)
        except Exception as e:
            logger.error(f"CLOVA error: {e}")
            response_text = self._get_fallback_response(avatar, situation)
        
        # Generate personalized tips
        tips = []
        if request.include_tips and mistakes:
            tips = self._generate_tips(mistakes, situation)
        
        # Check for improvements (compare with user context)
        improvements = []
        if request.user_context:
            improvements = self._check_improvements(
                mistakes, 
                request.user_context.get("common_mistakes", [])
            )
        
        # Situation-specific feedback
        situation_feedback = None
        if not situation_appropriate:
            situation_feedback = self._get_formality_feedback(
                expected_formality, 
                politeness.get("level", "polite")
            )
        
        # 🆕 Calculate emotion feedback for UI
        emotion_feedback = None
        if request.include_emotion:
            # Get recent scores from history
            recent_scores = []
            if request.history and request.history.messages:
                for msg in request.history.messages:
                    if hasattr(msg, 'score') and msg.score:
                        recent_scores.append(msg.score)
                    elif isinstance(msg, dict) and msg.get('score'):
                        recent_scores.append(msg['score'])
            
            # Calculate total mistakes in session
            total_mistakes = len(mistakes)
            for msg in (request.history.messages if request.history else []):
                msg_mistakes = msg.mistakes if hasattr(msg, 'mistakes') else (msg.get('mistakes') if isinstance(msg, dict) else None)
                if msg_mistakes:
                    total_mistakes += len(msg_mistakes)
            
            # Calculate average score
            all_scores = recent_scores + [score]
            average_score = sum(all_scores) / len(all_scores) if all_scores else score
            
            # Get full emotion feedback
            emotion_result = emotion_calculator.calculate_full_feedback(
                current_score=score,
                mistakes=[m.dict() for m in mistakes],
                recent_scores=recent_scores,
                average_score=average_score,
                total_mistakes=total_mistakes,
                message_count=session_info.message_count + 1,
                goals_achieved=goals_achieved,
                expected_formality=expected_formality
            )
            
            emotion_feedback = {
                "avatar_emotion": {
                    "emotion": emotion_result.avatar_emotion.emotion.value,
                    "emoji": emotion_result.avatar_emotion.emoji,
                    "message_ko": emotion_result.avatar_emotion.message_ko,
                    "message_en": emotion_result.avatar_emotion.message_en,
                    "intensity": emotion_result.avatar_emotion.intensity
                },
                "conversation_status": {
                    "status": emotion_result.conversation_status.status.value,
                    "emoji": emotion_result.conversation_status.emoji,
                    "label_ko": emotion_result.conversation_status.label_ko,
                    "label_en": emotion_result.conversation_status.label_en,
                    "color": emotion_result.conversation_status.color,
                    "current_score": emotion_result.conversation_status.current_score,
                    "average_score": emotion_result.conversation_status.average_score,
                    "progress": emotion_result.conversation_status.progress
                },
                "warnings": [
                    {
                        "level": w.level.value,
                        "emoji": w.emoji,
                        "color": w.color,
                        "message_ko": w.message_ko,
                        "message_en": w.message_en,
                        "category": w.category,
                        "original": w.original,
                        "suggestion": w.suggestion,
                        "show_correction": w.show_correction
                    }
                    for w in emotion_result.warnings
                ],
                "encouragement": emotion_result.encouragement,
                "tips": emotion_result.tips
            }
        
        return SessionChatResponse(
            response=response_text,
            session_id=session_info.session_id,
            message_number=session_info.message_count + 1,
            analysis={
                "politeness": politeness,
                "formality_expected": expected_formality,
                "formality_detected": politeness.get("level")
            },
            mistakes_found=[m.dict() for m in mistakes],
            score=score,
            situation_appropriate=situation_appropriate,
            situation_feedback=situation_feedback,
            goals_achieved=goals_achieved,
            personalized_tips=tips,
            improvements_noticed=improvements,
            emotion_feedback=emotion_feedback,
            should_end_session=False,  # Could add logic to detect conversation end
            status="success"
        )
    
    async def end_session(
        self,
        request: EndSessionRequest,
        session_data: Dict[str, Any]  # From backend
    ) -> EndSessionResponse:
        """
        Generate session summary when session ends.
        
        Backend should:
        1. Call this when user ends session or times out
        2. Pass full session data from DB
        3. Store the summary
        4. Update user progress
        """
        # Calculate stats from session data
        messages = session_data.get("messages", [])
        total_messages = len([m for m in messages if m.get("role") == "user"])
        
        scores = [m.get("score", 0) for m in messages if m.get("score")]
        average_score = sum(scores) / len(scores) if scores else 0
        
        # Count mistakes by category
        mistake_breakdown = {}
        total_mistakes = 0
        for m in messages:
            for mistake in m.get("mistakes", []):
                category = mistake.get("category", "other")
                mistake_breakdown[category] = mistake_breakdown.get(category, 0) + 1
                total_mistakes += 1
        
        # Get goals info
        goals_completed = session_data.get("goals_completed", [])
        situation = get_situation(session_data.get("situation_id", ""))
        total_goals = len(situation.get("goals_ko", [])) if situation else 0
        
        # Generate summary text
        summary_text = self._generate_session_summary(
            messages=messages,
            situation=situation,
            goals_completed=goals_completed
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            mistake_breakdown=mistake_breakdown,
            average_score=average_score,
            situation_id=session_data.get("situation_id")
        )
        
        # Check for achievements
        achievements = self._check_achievements(
            total_messages=total_messages,
            average_score=average_score,
            goals_completed=len(goals_completed),
            total_goals=total_goals
        )
        
        summary = SessionSummary(
            session_id=request.session_id,
            session_key=SessionKey(
                user_id=session_data.get("user_id", ""),
                avatar_id=session_data.get("avatar_id", ""),
                situation_id=session_data.get("situation_id", "")
            ),
            total_messages=total_messages,
            duration_seconds=session_data.get("duration_seconds", 0),
            average_score=round(average_score, 1),
            total_mistakes=total_mistakes,
            mistake_breakdown=mistake_breakdown,
            goals_total=total_goals,
            goals_completed=len(goals_completed),
            goals_completed_list=goals_completed,
            achievements=achievements,
            conversation_summary=summary_text,
            recommendations=recommendations,
            suggested_practice=self._suggest_next_practice(mistake_breakdown)
        )
        
        return EndSessionResponse(
            session_id=request.session_id,
            summary=summary,
            status="success"
        )
    
    # ===========================================
    # Helper Methods
    # ===========================================
    
    def _calculate_score(
        self, 
        mistakes: list, 
        politeness: dict,
        expected_formality: str
    ) -> int:
        """Calculate score based on mistakes and appropriateness."""
        base_score = 100
        
        # Deduct for mistakes
        for m in mistakes:
            severity = m.severity.value if hasattr(m, 'severity') else 'minor'
            if severity == "major":
                base_score -= 15
            elif severity == "moderate":
                base_score -= 10
            else:
                base_score -= 5
        
        # Deduct for wrong formality
        detected = politeness.get("level", "polite")
        if detected != expected_formality:
            base_score -= 10
        
        return max(0, min(100, base_score))
    
    def _check_situation_appropriate(
        self,
        message: str,
        situation: dict,
        politeness: dict
    ) -> bool:
        """Check if message formality matches situation."""
        expected = situation.get("expected_formality", "polite")
        detected = politeness.get("level", "polite")
        
        # Map formality names
        formality_map = {
            "casual": "informal",
            "polite": "polite",
            "formal": "very_polite"
        }
        
        expected_mapped = formality_map.get(expected, expected)
        
        return detected == expected_mapped
    
    def _check_goals_achieved(
        self,
        message: str,
        all_goals: List[str],
        already_completed: List[str]
    ) -> List[str]:
        """Check if any new goals were achieved."""
        newly_achieved = []
        
        # Simple keyword matching for goals
        goal_keywords = {
            "음료 주문하기": ["주세요", "할게요", "아메리카노", "라떼"],
            "결제하기": ["카드", "현금", "계산"],
            "추가 요청하기": ["샷 추가", "시럽", "휘핑"],
            "인사하기": ["안녕", "반갑", "처음"],
            "조언 구하기": ["어떻게", "조언", "도와주"],
        }
        
        for goal in all_goals:
            if goal in already_completed:
                continue
            
            keywords = goal_keywords.get(goal, [])
            for kw in keywords:
                if kw in message:
                    newly_achieved.append(goal)
                    break
        
        return newly_achieved
    
    def _build_clova_messages(
        self,
        current_message: str,
        history: List[ChatMessage],
        avatar: dict,
        situation: dict,
        max_history: int = 10
    ) -> List[Dict[str, str]]:
        """Build messages array for CLOVA API."""
        messages = []
        
        # Add history (limited)
        recent_history = history[-max_history:] if len(history) > max_history else history
        
        for msg in recent_history:
            role = msg.role.value if hasattr(msg, 'role') else msg.get("role", "user")
            content = msg.content if hasattr(msg, 'content') else msg.get("content", "")
            messages.append({
                "role": role,
                "content": content
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": current_message
        })
        
        return messages
    
    def _get_fallback_response(self, avatar: dict, situation: dict) -> str:
        """Get fallback response when CLOVA fails."""
        formality = avatar.get("formality", "polite")
        
        responses = {
            "informal": ["응응, 그렇구나!", "오 진짜?", "아~ 그래!"],
            "polite": ["네, 알겠어요!", "아, 그렇군요!", "네~"],
            "very_polite": ["네, 알겠습니다.", "아, 그렇군요.", "네, 감사합니다."]
        }
        
        import random
        return random.choice(responses.get(formality, responses["polite"]))
    
    def _generate_tips(self, mistakes: list, situation: dict) -> List[str]:
        """Generate tips based on mistakes."""
        tips = []
        
        categories_seen = set()
        for m in mistakes:
            cat = m.category.value if hasattr(m, 'category') else "other"
            if cat not in categories_seen:
                categories_seen.add(cat)
                
                if cat == "particles":
                    tips.append("💡 조사 팁: 받침 있으면 '을', 없으면 '를'!")
                elif cat == "formality":
                    tips.append("💡 말투를 일관되게 유지해 보세요!")
                elif cat == "honorifics":
                    tips.append("💡 높임말에서는 '-시-'를 사용하세요!")
        
        # Add situation-specific tips
        if situation.get("tips_ko"):
            tips.extend(situation["tips_ko"][:2])
        
        return tips[:3]
    
    def _check_improvements(
        self,
        current_mistakes: list,
        historical_mistakes: List[str]
    ) -> List[str]:
        """Check if user is improving."""
        improvements = []
        
        current_categories = set(
            m.category.value if hasattr(m, 'category') else "other" 
            for m in current_mistakes
        )
        
        for hist_cat in historical_mistakes[:3]:  # Top 3 historical issues
            if hist_cat not in current_categories:
                improvements.append(f"🎉 {hist_cat} 실력이 늘고 있어요!")
        
        return improvements[:2]
    
    def _get_formality_feedback(self, expected: str, detected: str) -> str:
        """Get feedback about formality mismatch."""
        feedback_map = {
            ("formal", "polite"): "이 상황에서는 격식체(-습니다)를 사용해 보세요.",
            ("formal", "informal"): "이 상황에서는 격식체(-습니다)가 필요해요.",
            ("polite", "informal"): "'-요'를 붙여서 존댓말로 말해 주세요.",
            ("polite", "very_polite"): "조금 더 편하게 해요체(-어요)로 말해도 괜찮아요.",
            ("casual", "polite"): "친구니까 반말로 편하게 말해도 돼요!",
            ("casual", "very_polite"): "너무 딱딱해요! 반말로 편하게 말해 봐요.",
        }
        
        return feedback_map.get((expected, detected), "")
    
    def _generate_session_summary(
        self,
        messages: list,
        situation: dict,
        goals_completed: list
    ) -> str:
        """Generate a summary of the session."""
        situation_name = situation.get("name_ko", "대화")
        goals_count = len(goals_completed)
        msg_count = len([m for m in messages if m.get("role") == "user"])
        
        return f"{situation_name} 상황에서 {msg_count}개의 메시지를 연습했어요. {goals_count}개의 목표를 달성했습니다!"
    
    def _generate_recommendations(
        self,
        mistake_breakdown: dict,
        average_score: float,
        situation_id: str
    ) -> List[str]:
        """Generate recommendations based on session."""
        recommendations = []
        
        if mistake_breakdown:
            top_mistake = max(mistake_breakdown.items(), key=lambda x: x[1])
            recommendations.append(f"'{top_mistake[0]}' 부분을 더 연습해 보세요.")
        
        if average_score >= 80:
            recommendations.append("잘하고 있어요! 더 어려운 상황에 도전해 보세요.")
        elif average_score < 60:
            recommendations.append("이 상황을 몇 번 더 연습해 보세요!")
        
        return recommendations
    
    def _check_achievements(
        self,
        total_messages: int,
        average_score: float,
        goals_completed: int,
        total_goals: int
    ) -> List[str]:
        """Check for achievements earned in session."""
        achievements = []
        
        if total_messages >= 10:
            achievements.append("🎯 대화 10개 달성!")
        
        if average_score >= 90:
            achievements.append("⭐ 우수한 성적!")
        
        if goals_completed == total_goals and total_goals > 0:
            achievements.append("✅ 모든 목표 달성!")
        
        return achievements
    
    def _suggest_next_practice(self, mistake_breakdown: dict) -> Optional[str]:
        """Suggest next situation to practice."""
        if not mistake_breakdown:
            return None
        
        # Map mistakes to situations
        mistake_to_situation = {
            "formality": "cafe_chat",      # Practice casual formality
            "honorifics": "professor_office",  # Practice honorifics
            "particles": "cafe_order",     # Practice basic particles
        }
        
        top_mistake = max(mistake_breakdown.items(), key=lambda x: x[1])
        return mistake_to_situation.get(top_mistake[0])


# Singleton
session_chat_service = SessionAwareChatService()
