"""
Vocabulary Spaced Repetition Service

SM-2 based spaced repetition system for Korean vocabulary learning.

Features:
- Track words and phrases learned
- Calculate optimal review intervals
- Track mastery levels
- Generate review sessions
- Integrate with chat for natural reinforcement
"""

from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import math
import random

from app.services.clova_service import clova_service, Message


# ============================================================================
# Models
# ============================================================================

class VocabType(str, Enum):
    WORD = "word"  # 단어
    PHRASE = "phrase"  # 표현/문장
    GRAMMAR = "grammar"  # 문법 패턴


class MasteryLevel(str, Enum):
    NEW = "new"  # 새로운 단어 (0-20%)
    LEARNING = "learning"  # 학습 중 (21-50%)
    REVIEWING = "reviewing"  # 복습 중 (51-80%)
    MASTERED = "mastered"  # 마스터 (81-100%)


class VocabItem(BaseModel):
    """Single vocabulary item"""
    id: str
    user_id: str
    
    type: VocabType
    
    # Content
    korean: str  # 한국어
    meaning: str  # 의미/번역
    pronunciation: Optional[str] = None  # 발음
    example: Optional[str] = None  # 예문
    example_translation: Optional[str] = None
    
    # Source
    source_avatar_id: Optional[str] = None
    source_avatar_name: Optional[str] = None
    source_conversation_id: Optional[str] = None
    
    # SM-2 Algorithm fields
    easiness_factor: float = 2.5  # E-Factor (1.3 ~ 2.5)
    interval_days: int = 1  # Current interval
    repetitions: int = 0  # Successful repetitions
    
    # Review tracking
    last_reviewed: Optional[datetime] = None
    next_review: datetime
    
    # Stats
    correct_count: int = 0
    incorrect_count: int = 0
    streak: int = 0  # Consecutive correct
    
    # Computed
    mastery_score: int = 0  # 0-100
    mastery_level: MasteryLevel = MasteryLevel.NEW
    
    created_at: datetime
    
    def calculate_mastery(self) -> Tuple[int, MasteryLevel]:
        """Calculate mastery score and level"""
        if self.correct_count + self.incorrect_count == 0:
            return 0, MasteryLevel.NEW
        
        # Base score from accuracy
        accuracy = self.correct_count / (self.correct_count + self.incorrect_count)
        
        # Bonus for repetitions and streak
        rep_bonus = min(self.repetitions * 5, 30)
        streak_bonus = min(self.streak * 3, 15)
        interval_bonus = min(self.interval_days * 2, 20)
        
        score = int(accuracy * 35 + rep_bonus + streak_bonus + interval_bonus)
        score = min(100, max(0, score))
        
        if score >= 80:
            level = MasteryLevel.MASTERED
        elif score >= 50:
            level = MasteryLevel.REVIEWING
        elif score >= 20:
            level = MasteryLevel.LEARNING
        else:
            level = MasteryLevel.NEW
        
        return score, level


class ReviewResult(BaseModel):
    """Result of a review"""
    vocab_id: str
    quality: int  # 0-5 (SM-2 quality rating)
    response_time_ms: Optional[int] = None
    user_answer: Optional[str] = None


class ReviewSession(BaseModel):
    """A review session"""
    id: str
    user_id: str
    
    items: List[VocabItem]
    total_items: int
    
    completed: int = 0
    correct: int = 0
    
    started_at: datetime
    completed_at: Optional[datetime] = None


class VocabStats(BaseModel):
    """User's vocabulary statistics"""
    user_id: str
    
    total_words: int = 0
    total_phrases: int = 0
    total_grammar: int = 0
    
    mastered_count: int = 0
    reviewing_count: int = 0
    learning_count: int = 0
    new_count: int = 0
    
    due_today: int = 0
    streak_days: int = 0
    
    words_learned_this_week: int = 0
    review_accuracy: float = 0.0


class ChatVocabSuggestion(BaseModel):
    """Vocabulary to naturally include in chat"""
    vocab_item: VocabItem
    suggested_usage: str  # How to use it in conversation
    is_review: bool  # True if this is a review word


# ============================================================================
# Vocabulary Storage (In-memory, replace with DB)
# ============================================================================

class VocabStorage:
    """Simple in-memory storage"""
    
    def __init__(self):
        self.items: Dict[str, Dict[str, VocabItem]] = {}  # user_id -> {vocab_id: item}
        self._id_counter = 0
    
    def _generate_id(self) -> str:
        self._id_counter += 1
        return f"vocab_{self._id_counter}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def add_item(self, item: VocabItem) -> VocabItem:
        if item.user_id not in self.items:
            self.items[item.user_id] = {}
        
        item.id = self._generate_id()
        self.items[item.user_id][item.id] = item
        return item
    
    def get_item(self, user_id: str, vocab_id: str) -> Optional[VocabItem]:
        return self.items.get(user_id, {}).get(vocab_id)
    
    def get_all_items(self, user_id: str) -> List[VocabItem]:
        return list(self.items.get(user_id, {}).values())
    
    def update_item(self, item: VocabItem):
        if item.user_id in self.items and item.id in self.items[item.user_id]:
            self.items[item.user_id][item.id] = item
    
    def delete_item(self, user_id: str, vocab_id: str) -> bool:
        if user_id in self.items and vocab_id in self.items[user_id]:
            del self.items[user_id][vocab_id]
            return True
        return False
    
    def get_due_items(self, user_id: str, limit: int = 20) -> List[VocabItem]:
        """Get items due for review"""
        now = datetime.now()
        items = self.get_all_items(user_id)
        due = [i for i in items if i.next_review <= now]
        due.sort(key=lambda x: x.next_review)
        return due[:limit]
    
    def get_items_by_level(self, user_id: str, level: MasteryLevel) -> List[VocabItem]:
        items = self.get_all_items(user_id)
        return [i for i in items if i.mastery_level == level]


# Global storage
vocab_storage = VocabStorage()


# ============================================================================
# SM-2 Algorithm
# ============================================================================

class SM2Algorithm:
    """
    SM-2 Spaced Repetition Algorithm
    
    Quality ratings:
    5 - perfect response
    4 - correct after hesitation
    3 - correct with difficulty
    2 - incorrect but easy to recall
    1 - incorrect, remembered after seeing answer
    0 - complete failure
    """
    
    @staticmethod
    def calculate_next_review(
        quality: int,
        repetitions: int,
        easiness_factor: float,
        interval_days: int,
    ) -> Tuple[int, int, float]:
        """
        Calculate next review interval using SM-2.
        
        Returns: (new_interval, new_repetitions, new_easiness_factor)
        """
        
        # Update easiness factor
        new_ef = easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        new_ef = max(1.3, new_ef)  # Minimum EF is 1.3
        
        if quality >= 3:  # Correct response
            if repetitions == 0:
                new_interval = 1
            elif repetitions == 1:
                new_interval = 6
            else:
                new_interval = int(interval_days * new_ef)
            
            new_repetitions = repetitions + 1
        else:  # Incorrect response
            new_interval = 1
            new_repetitions = 0
        
        # Cap interval at 365 days
        new_interval = min(365, new_interval)
        
        return new_interval, new_repetitions, new_ef
    
    @staticmethod
    def quality_from_response(
        correct: bool,
        response_time_ms: Optional[int] = None,
        hint_used: bool = False,
    ) -> int:
        """Convert response to SM-2 quality rating"""
        
        if not correct:
            return 1 if hint_used else 0
        
        # Base quality for correct
        quality = 4
        
        # Adjust based on response time
        if response_time_ms:
            if response_time_ms < 2000:  # Very fast
                quality = 5
            elif response_time_ms < 5000:  # Normal
                quality = 4
            elif response_time_ms < 10000:  # Slow
                quality = 3
            else:  # Very slow
                quality = 3
        
        # Penalty for using hint
        if hint_used:
            quality = max(3, quality - 1)
        
        return quality


# ============================================================================
# Vocabulary Service
# ============================================================================

class VocabularyService:
    """Service for vocabulary management and spaced repetition"""
    
    def __init__(self):
        self.storage = vocab_storage
        self.sm2 = SM2Algorithm()
    
    async def add_vocabulary(
        self,
        user_id: str,
        korean: str,
        meaning: str,
        vocab_type: VocabType = VocabType.WORD,
        example: Optional[str] = None,
        source_avatar_id: Optional[str] = None,
        source_avatar_name: Optional[str] = None,
    ) -> VocabItem:
        """Add new vocabulary item"""
        
        now = datetime.now()
        
        # Check for duplicate
        existing = self.storage.get_all_items(user_id)
        for item in existing:
            if item.korean.lower() == korean.lower():
                return item  # Already exists
        
        item = VocabItem(
            id="",
            user_id=user_id,
            type=vocab_type,
            korean=korean,
            meaning=meaning,
            example=example,
            source_avatar_id=source_avatar_id,
            source_avatar_name=source_avatar_name,
            next_review=now,  # Review immediately
            created_at=now,
        )
        
        return self.storage.add_item(item)
    
    async def add_from_conversation(
        self,
        user_id: str,
        conversation_messages: List[Dict[str, str]],
        avatar_id: str,
        avatar_name: str,
    ) -> List[VocabItem]:
        """
        Extract vocabulary from conversation and add to user's list.
        
        Uses AI to identify useful vocabulary.
        """
        
        conversation = "\n".join([
            f"{'사용자' if m['role'] == 'user' else '아바타'}: {m['content']}"
            for m in conversation_messages
        ])
        
        prompt = f"""다음 대화에서 한국어 학습자에게 유용한 단어와 표현을 추출하세요.

## 대화
{conversation}

## 추출 기준
1. 일상에서 자주 쓰이는 단어/표현
2. 대화에서 새로 등장한 어휘
3. 학습자가 틀렸거나 어려워한 표현
4. 자연스러운 한국어 표현

## 응답 형식 (JSON)
{{
    "vocabulary": [
        {{
            "korean": "한국어 단어/표현",
            "meaning": "의미 설명 (한국어)",
            "type": "word/phrase/grammar",
            "example": "예문",
            "difficulty": "easy/medium/hard"
        }}
    ]
}}

5-10개 정도 추출하세요. 너무 기본적인 단어는 제외합니다."""

        result = await clova_service.analyze_json(prompt, temperature=0.3, max_tokens=800)
        
        added_items = []
        
        if result:
            for v in result.get("vocabulary", []):
                try:
                    item = await self.add_vocabulary(
                        user_id=user_id,
                        korean=v.get("korean", ""),
                        meaning=v.get("meaning", ""),
                        vocab_type=VocabType(v.get("type", "word")),
                        example=v.get("example"),
                        source_avatar_id=avatar_id,
                        source_avatar_name=avatar_name,
                    )
                    added_items.append(item)
                except Exception as e:
                    print(f"Error adding vocab: {e}")
                    continue
        
        return added_items
    
    def record_review(
        self,
        user_id: str,
        vocab_id: str,
        correct: bool,
        response_time_ms: Optional[int] = None,
        hint_used: bool = False,
    ) -> Optional[VocabItem]:
        """Record a review result and update spacing"""
        
        item = self.storage.get_item(user_id, vocab_id)
        if not item:
            return None
        
        # Calculate quality
        quality = self.sm2.quality_from_response(correct, response_time_ms, hint_used)
        
        # Update with SM-2
        new_interval, new_reps, new_ef = self.sm2.calculate_next_review(
            quality=quality,
            repetitions=item.repetitions,
            easiness_factor=item.easiness_factor,
            interval_days=item.interval_days,
        )
        
        # Update item
        item.interval_days = new_interval
        item.repetitions = new_reps
        item.easiness_factor = new_ef
        item.last_reviewed = datetime.now()
        item.next_review = datetime.now() + timedelta(days=new_interval)
        
        if correct:
            item.correct_count += 1
            item.streak += 1
        else:
            item.incorrect_count += 1
            item.streak = 0
        
        # Update mastery
        item.mastery_score, item.mastery_level = item.calculate_mastery()
        
        self.storage.update_item(item)
        
        return item
    
    def get_due_reviews(self, user_id: str, limit: int = 20) -> List[VocabItem]:
        """Get vocabulary items due for review"""
        return self.storage.get_due_items(user_id, limit)
    
    def get_review_session(self, user_id: str, count: int = 10) -> ReviewSession:
        """Create a review session"""
        
        due_items = self.get_due_reviews(user_id, limit=count * 2)
        
        # Prioritize: overdue > low mastery > random
        due_items.sort(key=lambda x: (
            x.next_review,
            x.mastery_score,
        ))
        
        selected = due_items[:count]
        
        # Shuffle for variety
        random.shuffle(selected)
        
        return ReviewSession(
            id=f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            user_id=user_id,
            items=selected,
            total_items=len(selected),
            started_at=datetime.now(),
        )
    
    def get_stats(self, user_id: str) -> VocabStats:
        """Get user's vocabulary statistics"""
        
        items = self.storage.get_all_items(user_id)
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        
        # Count by type
        words = len([i for i in items if i.type == VocabType.WORD])
        phrases = len([i for i in items if i.type == VocabType.PHRASE])
        grammar = len([i for i in items if i.type == VocabType.GRAMMAR])
        
        # Count by level
        mastered = len([i for i in items if i.mastery_level == MasteryLevel.MASTERED])
        reviewing = len([i for i in items if i.mastery_level == MasteryLevel.REVIEWING])
        learning = len([i for i in items if i.mastery_level == MasteryLevel.LEARNING])
        new = len([i for i in items if i.mastery_level == MasteryLevel.NEW])
        
        # Due today
        due = len([i for i in items if i.next_review <= now])
        
        # Learned this week
        this_week = len([i for i in items if i.created_at >= week_ago])
        
        # Accuracy
        total_correct = sum(i.correct_count for i in items)
        total_incorrect = sum(i.incorrect_count for i in items)
        accuracy = total_correct / (total_correct + total_incorrect) if (total_correct + total_incorrect) > 0 else 0
        
        return VocabStats(
            user_id=user_id,
            total_words=words,
            total_phrases=phrases,
            total_grammar=grammar,
            mastered_count=mastered,
            reviewing_count=reviewing,
            learning_count=learning,
            new_count=new,
            due_today=due,
            words_learned_this_week=this_week,
            review_accuracy=round(accuracy, 2),
        )
    
    def get_chat_vocab_suggestions(
        self,
        user_id: str,
        avatar_interests: List[str],
        count: int = 3,
    ) -> List[ChatVocabSuggestion]:
        """
        Get vocabulary to naturally include in chat.
        
        Returns items that are due for review or recently learned.
        """
        
        # Get due items
        due_items = self.get_due_reviews(user_id, limit=5)
        
        # Get recently learned
        all_items = self.storage.get_all_items(user_id)
        recent = sorted(all_items, key=lambda x: x.created_at, reverse=True)[:5]
        
        suggestions = []
        
        for item in due_items[:2]:
            suggestions.append(ChatVocabSuggestion(
                vocab_item=item,
                suggested_usage=f"'{item.korean}'를 사용하여 대화해보세요",
                is_review=True,
            ))
        
        for item in recent[:1]:
            if item not in due_items:
                suggestions.append(ChatVocabSuggestion(
                    vocab_item=item,
                    suggested_usage=f"새로 배운 '{item.korean}'를 연습해보세요",
                    is_review=False,
                ))
        
        return suggestions[:count]
    
    def get_all_vocabulary(self, user_id: str) -> List[VocabItem]:
        """Get all vocabulary for a user"""
        return self.storage.get_all_items(user_id)
    
    def delete_vocabulary(self, user_id: str, vocab_id: str) -> bool:
        """Delete a vocabulary item"""
        return self.storage.delete_item(user_id, vocab_id)
    
    def get_vocabulary_by_level(self, user_id: str, level: MasteryLevel) -> List[VocabItem]:
        """Get vocabulary by mastery level"""
        return self.storage.get_items_by_level(user_id, level)


# Global service instance
vocabulary_service = VocabularyService()
