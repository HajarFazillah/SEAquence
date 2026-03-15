"""
Mistake Tracking Service
Analyzes user Korean and tracks mistake patterns for personalized feedback
"""

import re
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict

from app.schemas.context_schemas import (
    MistakeRecord, MistakePattern, MistakeCategory, MistakeSeverity,
    UserLearningContext
)

logger = logging.getLogger(__name__)


class MistakeTracker:
    """
    Analyzes Korean text for mistakes and tracks patterns over time.
    """
    
    def __init__(self):
        # Mistake detection patterns
        self._init_detection_patterns()
        
    def _init_detection_patterns(self):
        """Initialize regex patterns for mistake detection."""
        
        # Formality mixing patterns
        self.formality_patterns = {
            # Mixing 반말 endings in polite context
            "informal_in_polite": [
                (r"(\w+)(해|해요)\s*[.?!]", "해 with 요 is redundant or inconsistent"),
                (r"(합니다|입니다).*(해|가|야)", "Mixing formal and informal"),
            ],
            # Missing 요 in polite speech
            "missing_yo": [
                (r"(\w+)(어|아|여)(?!\s*요)[.?!]?$", "Missing 요 for polite speech"),
            ],
        }
        
        # Common particle errors
        self.particle_patterns = [
            # Subject markers
            (r"저([가이])\s", r"저는/제가", MistakeCategory.PARTICLES, "저 + 가/이 usage"),
            (r"나([는은])\s", r"나는/내가", MistakeCategory.PARTICLES, "나 + 는/은 vs 가 usage"),
            
            # Object markers with vowel/consonant
            (r"([가-힣]+[아어오우이])을\s", None, MistakeCategory.PARTICLES, "을 after vowel should be 를"),
            (r"([가-힣]+[^아어오우이])를\s", None, MistakeCategory.PARTICLES, "를 after consonant should be 을"),
        ]
        
        # Common spelling/grammar errors (from corrections.py patterns)
        self.spelling_patterns = [
            (r"되요", "돼요", MistakeCategory.SPELLING, "되요 → 돼요"),
            (r"됬", "됐", MistakeCategory.SPELLING, "됬 → 됐"),
            (r"웬지", "왠지", MistakeCategory.SPELLING, "웬지 → 왠지"),
            (r"몇일", "며칠", MistakeCategory.SPELLING, "몇일 → 며칠"),
            (r"어떻게", None, MistakeCategory.SPELLING, None),  # This is correct, just checking
            (r"어떡게", "어떻게", MistakeCategory.SPELLING, "어떡게 → 어떻게"),
            (r"않해", "안 해", MistakeCategory.NEGATION, "않해 → 안 해"),
            (r"모해", "뭐 해", MistakeCategory.SPELLING, "모해 → 뭐 해"),
        ]
        
        # Honorific patterns
        self.honorific_patterns = [
            # Missing 시 in honorifics
            (r"(선생님|교수님|부장님|사장님).*(가|는|이)\s", None, MistakeCategory.HONORIFICS, 
             "Use honorific form with titles: 께서"),
            (r"(선생님|교수님).*(했어|했다)", None, MistakeCategory.HONORIFICS,
             "Use 하셨어요/하셨습니다 with teachers"),
        ]
        
        # Verb conjugation patterns
        self.conjugation_patterns = [
            # ㅂ irregular
            (r"(춥|덥|무겁|가볍)어", None, MistakeCategory.VERB_CONJUGATION, 
             "ㅂ irregular: 춥 → 추워, 덥 → 더워"),
            # ㄷ irregular  
            (r"(듣|걷|묻)어", None, MistakeCategory.VERB_CONJUGATION,
             "ㄷ irregular: 듣 → 들어, 걷 → 걸어"),
        ]
        
    def analyze_message(
        self, 
        message: str, 
        expected_formality: str = "polite",
        context: Optional[UserLearningContext] = None
    ) -> List[MistakeRecord]:
        """
        Analyze a message for Korean language mistakes.
        
        Args:
            message: User's Korean message
            expected_formality: Expected formality level
            context: User's learning context for pattern matching
            
        Returns:
            List of MistakeRecord objects
        """
        mistakes = []
        
        # Check spelling errors
        spelling_mistakes = self._check_spelling(message)
        mistakes.extend(spelling_mistakes)
        
        # Check particle usage
        particle_mistakes = self._check_particles(message)
        mistakes.extend(particle_mistakes)
        
        # Check formality consistency
        formality_mistakes = self._check_formality(message, expected_formality)
        mistakes.extend(formality_mistakes)
        
        # Check honorifics
        honorific_mistakes = self._check_honorifics(message)
        mistakes.extend(honorific_mistakes)
        
        # Check for patterns the user frequently gets wrong
        if context and context.mistake_patterns:
            pattern_mistakes = self._check_known_patterns(message, context)
            mistakes.extend(pattern_mistakes)
        
        return mistakes
    
    def _check_spelling(self, message: str) -> List[MistakeRecord]:
        """Check for common spelling mistakes."""
        mistakes = []
        
        for pattern, correction, category, explanation in self.spelling_patterns:
            if correction is None:
                continue
            matches = re.finditer(pattern, message)
            for match in matches:
                mistakes.append(MistakeRecord(
                    category=category,
                    severity=MistakeSeverity.MINOR,
                    original=match.group(),
                    corrected=correction,
                    explanation=explanation or f"'{match.group()}' → '{correction}'",
                    explanation_en=f"Spelling: '{match.group()}' should be '{correction}'",
                    context=message
                ))
        
        return mistakes
    
    def _check_particles(self, message: str) -> List[MistakeRecord]:
        """Check for particle usage errors."""
        mistakes = []
        
        # Check 을/를 with vowel/consonant
        # Korean vowels at the end of syllables
        # We need to check the final character's jongseong (받침)
        
        words = message.split()
        for i, word in enumerate(words):
            # Check for 을 after vowel-ending words
            if '을' in word and len(word) > 1:
                idx = word.index('을')
                if idx > 0:
                    prev_char = word[idx - 1]
                    # Check if previous character has no final consonant (받침)
                    if self._has_no_batchim(prev_char):
                        wrong = word[max(0, idx-2):idx+1]
                        correct = word[max(0, idx-2):idx] + '를'
                        mistakes.append(MistakeRecord(
                            category=MistakeCategory.PARTICLES,
                            severity=MistakeSeverity.MODERATE,
                            original=wrong,
                            corrected=correct,
                            explanation=f"받침이 없는 글자 뒤에는 '를'을 사용해요",
                            explanation_en=f"Use '를' after syllables without final consonant, not '을'",
                            context=message
                        ))
            
            # Check for 를 after consonant-ending words
            if '를' in word and len(word) > 1:
                idx = word.index('를')
                if idx > 0:
                    prev_char = word[idx - 1]
                    # Check if previous character has final consonant (받침)
                    if self._has_batchim(prev_char):
                        wrong = word[max(0, idx-2):idx+1]
                        correct = word[max(0, idx-2):idx] + '을'
                        mistakes.append(MistakeRecord(
                            category=MistakeCategory.PARTICLES,
                            severity=MistakeSeverity.MODERATE,
                            original=wrong,
                            corrected=correct,
                            explanation=f"받침이 있는 글자 뒤에는 '을'을 사용해요",
                            explanation_en=f"Use '을' after syllables with final consonant, not '를'",
                            context=message
                        ))
        
        return mistakes
    
    def _has_no_batchim(self, char: str) -> bool:
        """Check if a Korean character has no final consonant (받침)."""
        if not char or len(char) != 1:
            return False
        code = ord(char)
        # Korean syllable range
        if 0xAC00 <= code <= 0xD7A3:
            # (code - 0xAC00) % 28 == 0 means no batchim
            return (code - 0xAC00) % 28 == 0
        return False
    
    def _has_batchim(self, char: str) -> bool:
        """Check if a Korean character has a final consonant (받침)."""
        if not char or len(char) != 1:
            return False
        code = ord(char)
        # Korean syllable range
        if 0xAC00 <= code <= 0xD7A3:
            return (code - 0xAC00) % 28 != 0
        return False
    
    def _check_formality(self, message: str, expected: str) -> List[MistakeRecord]:
        """Check for formality level consistency."""
        mistakes = []
        
        # Detect current formality
        has_formal = bool(re.search(r'(습니다|입니다|습니까|ㅂ니다)', message))
        has_polite = bool(re.search(r'(어요|아요|여요|에요|죠|네요|군요)', message))
        has_informal = bool(re.search(r'(해|야|어|아|지|냐|니)(?:[.?!]|$)', message))
        
        # Check for mixing
        formality_count = sum([has_formal, has_polite, has_informal])
        
        if formality_count > 1:
            # Mixed formality detected
            detected = []
            if has_formal:
                detected.append("격식체(-습니다)")
            if has_polite:
                detected.append("해요체(-어요)")
            if has_informal:
                detected.append("반말(-해)")
            
            mistakes.append(MistakeRecord(
                category=MistakeCategory.FORMALITY,
                severity=MistakeSeverity.MODERATE,
                original=message,
                corrected="(consistent formality needed)",
                explanation=f"말투가 섞여 있어요: {', '.join(detected)}. 하나로 통일해 주세요.",
                explanation_en=f"Mixed speech levels detected: {', '.join(detected)}. Keep consistent.",
                context=message
            ))
        
        # Check if formality matches expected
        if expected == "formal" and not has_formal and (has_polite or has_informal):
            mistakes.append(MistakeRecord(
                category=MistakeCategory.FORMALITY,
                severity=MistakeSeverity.MAJOR,
                original=message,
                corrected="(use -습니다/입니다)",
                explanation="이 상황에서는 격식체(-습니다)를 사용하세요",
                explanation_en="Use formal speech (-습니다) in this situation",
                context=message
            ))
        elif expected == "polite" and has_informal and not has_polite:
            mistakes.append(MistakeRecord(
                category=MistakeCategory.FORMALITY,
                severity=MistakeSeverity.MODERATE,
                original=message,
                corrected="(add -요)",
                explanation="'-요'를 붙여서 존댓말로 말해 주세요",
                explanation_en="Add '-요' to make it polite speech",
                context=message
            ))
        
        return mistakes
    
    def _check_honorifics(self, message: str) -> List[MistakeRecord]:
        """Check for honorific usage."""
        mistakes = []
        
        # Check if mentioning someone who needs honorifics
        honorific_titles = ['선생님', '교수님', '부장님', '사장님', '할머니', '할아버지', '어머니', '아버지']
        
        for title in honorific_titles:
            if title in message:
                # Check if proper honorific verb form is used
                # This is simplified - would need NLP for full analysis
                if re.search(rf'{title}.*(?:했어|갔어|왔어|먹어)(?:[요])?', message):
                    mistakes.append(MistakeRecord(
                        category=MistakeCategory.HONORIFICS,
                        severity=MistakeSeverity.MAJOR,
                        original=message,
                        corrected="(use -시- honorific)",
                        explanation=f"'{title}'에 대해 말할 때는 '-시-'를 사용하세요 (하셨어요, 가셨어요)",
                        explanation_en=f"Use honorific '-시-' when talking about {title}",
                        context=message
                    ))
        
        return mistakes
    
    def _check_known_patterns(
        self, 
        message: str, 
        context: UserLearningContext
    ) -> List[MistakeRecord]:
        """Check for patterns the user has struggled with before."""
        mistakes = []
        
        # Get user's frequent mistake categories
        frequent_categories = sorted(
            context.mistake_patterns.items(),
            key=lambda x: x[1].count,
            reverse=True
        )[:3]
        
        for category_name, pattern in frequent_categories:
            if pattern.count >= 3:  # User has made this mistake 3+ times
                # Extra vigilant checking for this category
                # Add targeted feedback
                pass
        
        return mistakes
    
    def update_context(
        self,
        context: UserLearningContext,
        new_mistakes: List[MistakeRecord],
        message: str
    ) -> UserLearningContext:
        """
        Update user context with new mistakes and patterns.
        
        Args:
            context: Current user context
            new_mistakes: Mistakes found in current message
            message: The message that was analyzed
            
        Returns:
            Updated UserLearningContext
        """
        now = datetime.now()
        
        # Update basic stats
        context.total_messages += 1
        context.total_mistakes += len(new_mistakes)
        context.last_active = now
        
        # Add new mistakes to history (keep last 100)
        context.mistake_history.extend(new_mistakes)
        if len(context.mistake_history) > 100:
            context.mistake_history = context.mistake_history[-100:]
        
        # Update patterns
        for mistake in new_mistakes:
            category = mistake.category.value
            if category in context.mistake_patterns:
                pattern = context.mistake_patterns[category]
                pattern.count += 1
                pattern.last_seen = now
                pattern.examples.append(mistake.original)
                if len(pattern.examples) > 5:
                    pattern.examples = pattern.examples[-5:]
            else:
                context.mistake_patterns[category] = MistakePattern(
                    category=mistake.category,
                    count=1,
                    examples=[mistake.original],
                    first_seen=now,
                    last_seen=now
                )
        
        # Check for improvements (no mistakes in category for last 5 messages)
        # This is a simplified check
        recent_categories = set(m.category.value for m in context.mistake_history[-5:])
        for category, pattern in context.mistake_patterns.items():
            if category not in recent_categories and pattern.count >= 3:
                pattern.improving = True
                pattern.recent_correct += 1
        
        return context
    
    def generate_personalized_tips(
        self,
        context: UserLearningContext,
        current_mistakes: List[MistakeRecord]
    ) -> List[str]:
        """
        Generate personalized learning tips based on user's history.
        
        Returns tips in Korean with focus on recurring issues.
        """
        tips = []
        
        # Get top problem areas
        problem_areas = sorted(
            context.mistake_patterns.items(),
            key=lambda x: x[1].count,
            reverse=True
        )[:3]
        
        tip_templates = {
            MistakeCategory.FORMALITY.value: [
                "💡 말투 일관성: 대화할 때 하나의 말투(해요체/합니다체/반말)를 선택해서 끝까지 유지해 보세요!",
                "💡 Tip: 처음 만나는 사람에게는 '-요'를 붙이는 것이 안전해요.",
            ],
            MistakeCategory.PARTICLES.value: [
                "💡 조사 팁: '을/를'은 받침 유무로 구분해요. 받침 있으면 '을', 없으면 '를'!",
                "💡 '은/는'은 주제, '이/가'는 주어를 나타내요. 새로운 정보에는 '이/가'를 써 보세요.",
            ],
            MistakeCategory.HONORIFICS.value: [
                "💡 높임말 팁: 어른이나 선생님에 대해 말할 때는 동사에 '-시-'를 넣어 주세요 (가다 → 가시다).",
                "💡 '드리다', '여쭙다' 같은 특별 높임말도 연습해 보세요!",
            ],
            MistakeCategory.SPELLING.value: [
                "💡 자주 틀리는 맞춤법을 정리해 두면 도움이 돼요!",
                "💡 '되다/돼다' 구분: '되어'를 넣어서 자연스러우면 '돼'를 써요.",
            ],
            MistakeCategory.VERB_CONJUGATION.value: [
                "💡 불규칙 동사 팁: ㅂ불규칙(춥→추워), ㄷ불규칙(듣→들어)을 따로 외워 두세요!",
            ],
        }
        
        # Add tips for problem areas
        for category, pattern in problem_areas:
            if pattern.count >= 2:
                if category in tip_templates:
                    tips.append(tip_templates[category][0])
        
        # Add encouragement for improvements
        improving = [cat for cat, p in context.mistake_patterns.items() if p.improving]
        if improving:
            tips.append(f"🎉 잘하고 있어요! {improving[0]} 실력이 늘고 있어요!")
        
        # Limit to 3 tips
        return tips[:3]
    
    def generate_summary(self, context: UserLearningContext) -> Dict[str, Any]:
        """Generate a summary of user's learning progress."""
        
        # Calculate accuracy
        accuracy = 0
        if context.total_messages > 0:
            # Simplified: assume average 1 potential mistake per message
            accuracy = max(0, 100 - (context.total_mistakes / context.total_messages * 20))
        
        # Get problem categories
        problem_categories = sorted(
            context.mistake_patterns.items(),
            key=lambda x: x[1].count,
            reverse=True
        )
        
        # Generate recommendations
        recommendations = []
        for category, pattern in problem_categories[:3]:
            if pattern.count >= 3:
                rec = self._get_recommendation(category, pattern)
                if rec:
                    recommendations.append(rec)
        
        return {
            "total_messages": context.total_messages,
            "total_mistakes": context.total_mistakes,
            "accuracy_rate": round(accuracy, 1),
            "top_problem_categories": [
                {
                    "category": cat,
                    "count": p.count,
                    "improving": p.improving,
                    "examples": p.examples[-3:]
                }
                for cat, p in problem_categories[:5]
            ],
            "recommendations": recommendations,
            "strengths": context.strengths,
            "estimated_level": context.estimated_level
        }
    
    def _get_recommendation(self, category: str, pattern: MistakePattern) -> Optional[str]:
        """Get learning recommendation for a category."""
        recommendations = {
            MistakeCategory.FORMALITY.value: "격식체(-습니다)와 해요체(-어요) 구분 연습을 해 보세요.",
            MistakeCategory.PARTICLES.value: "조사(은/는, 이/가, 을/를) 문법 복습을 추천해요.",
            MistakeCategory.HONORIFICS.value: "높임말 표현 연습: '-시-', '드리다', '께서' 등을 연습해 보세요.",
            MistakeCategory.VERB_CONJUGATION.value: "불규칙 동사 활용표를 만들어 외워 보세요.",
            MistakeCategory.SPELLING.value: "자주 틀리는 단어 목록을 만들어 복습하세요.",
        }
        return recommendations.get(category)


# Singleton instance
mistake_tracker = MistakeTracker()
