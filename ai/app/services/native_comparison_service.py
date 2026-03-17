"""
Native Comparison Service
Compares user's Korean with how native speakers would say it
"""

import logging
import re
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NativeExpression:
    """A native Korean expression alternative."""
    expression: str
    formality: str  # informal, polite, formal
    naturalness: int  # 1-5 (5 = most natural)
    situation: str  # when to use this
    nuance: str  # subtle meaning/feeling


@dataclass
class Difference:
    """Difference between user's expression and native expression."""
    category: str  # vocabulary, grammar, nuance, formality, expression
    user_part: str
    native_part: str
    explanation_ko: str
    explanation_en: str


@dataclass 
class NativeComparisonResult:
    """Complete native comparison result."""
    user_sentence: str
    user_formality: str
    native_expressions: List[NativeExpression]
    best_match: Optional[str]
    differences: List[Difference]
    tips_ko: List[str]
    tips_en: List[str]
    naturalness_score: int  # 1-100
    cultural_note: Optional[str] = None


class NativeComparisonService:
    """
    Service to compare user's Korean with native expressions.
    """
    
    # Common expression patterns (user input → native alternatives)
    EXPRESSION_DATABASE = {
        # Greetings
        "안녕": {
            "informal": ["안녕~", "ㅎㅇ", "하이"],
            "polite": ["안녕하세요", "안녕하세요~"],
            "formal": ["안녕하십니까"]
        },
        "잘 지내": {
            "informal": ["잘 지내?", "잘 지냈어?", "요즘 어때?"],
            "polite": ["잘 지내세요?", "잘 지내셨어요?", "요즘 어떠세요?"],
            "formal": ["안녕히 지내셨습니까?", "그간 평안하셨습니까?"]
        },
        
        # Questions
        "질문 있어": {
            "informal": ["물어볼 거 있어", "이거 좀 물어봐도 돼?"],
            "polite": ["질문이 있는데요", "여쭤볼 게 있어요", "물어봐도 될까요?"],
            "formal": ["질문이 있습니다", "여쭤볼 것이 있습니다", "질문 드려도 되겠습니까?"]
        },
        
        # Thanks
        "고마워": {
            "informal": ["고마워~", "땡큐", "ㄱㅅ"],
            "polite": ["감사해요", "고마워요", "감사합니다"],
            "formal": ["감사합니다", "감사드립니다", "진심으로 감사드립니다"]
        },
        
        # Sorry
        "미안": {
            "informal": ["미안~", "쏘리", "ㅁㅇ"],
            "polite": ["미안해요", "죄송해요", "죄송합니다"],
            "formal": ["죄송합니다", "사과드립니다", "송구합니다"]
        },
        
        # Requests
        "해줘": {
            "informal": ["해줘~", "해줄래?", "이거 좀"],
            "polite": ["해주세요", "해주실래요?", "해주시겠어요?"],
            "formal": ["해주십시오", "해주시겠습니까?", "부탁드립니다"]
        },
        
        # Understanding
        "알았어": {
            "informal": ["알았어", "ㅇㅋ", "웅"],
            "polite": ["알겠어요", "네, 알겠습니다"],
            "formal": ["알겠습니다", "네, 알겠습니다", "숙지하겠습니다"]
        },
        
        # Eating
        "밥 먹었어": {
            "informal": ["밥 먹었어?", "밥 먹음?", "뭐 먹었어?"],
            "polite": ["식사하셨어요?", "밥 드셨어요?"],
            "formal": ["식사하셨습니까?", "진지 드셨습니까?"]
        }
    }
    
    # Vocabulary upgrades for honorifics
    VOCABULARY_UPGRADES = {
        "주다": {"honorific": "드리다"},
        "먹다": {"honorific": "드시다", "humble": "먹다"},
        "자다": {"honorific": "주무시다"},
        "말하다": {"honorific": "말씀하시다", "humble": "말씀드리다"},
        "보다": {"honorific": "보시다", "humble": "뵙다"},
        "묻다": {"honorific": "물으시다", "humble": "여쭙다"},
        "이름": {"honorific": "성함"},
        "나이": {"honorific": "연세"},
        "집": {"honorific": "댁"},
        "생일": {"honorific": "생신"},
        "밥": {"honorific": "진지", "polite": "식사"},
        "말": {"honorific": "말씀"},
    }
    
    def __init__(self):
        self._clova_service = None
        self._initialized = False
    
    def _initialize(self):
        """Initialize with CLOVA service."""
        if self._initialized:
            return
        
        try:
            from app.services.clova_service import clova_service
            self._clova_service = clova_service
        except Exception as e:
            logger.warning(f"CLOVA service not available: {e}")
        
        self._initialized = True
    
    async def compare(
        self,
        user_sentence: str,
        context: str = "",
        target_role: str = "friend",
        target_formality: str = "polite",
        include_cultural_notes: bool = True
    ) -> NativeComparisonResult:
        """
        Compare user's sentence with native expressions.
        """
        self._initialize()
        
        # Analyze user's formality
        user_formality = self._detect_formality(user_sentence)
        
        # Try CLOVA first for best results
        if self._clova_service and self._clova_service.is_configured:
            try:
                return await self._compare_with_clova(
                    user_sentence, context, target_role, 
                    target_formality, user_formality, include_cultural_notes
                )
            except Exception as e:
                logger.warning(f"CLOVA comparison failed: {e}")
        
        # Fallback to rule-based
        return self._compare_rule_based(
            user_sentence, target_role, target_formality, 
            user_formality, include_cultural_notes
        )
    
    async def _compare_with_clova(
        self,
        user_sentence: str,
        context: str,
        target_role: str,
        target_formality: str,
        user_formality: str,
        include_cultural_notes: bool
    ) -> NativeComparisonResult:
        """Use CLOVA to generate native comparisons."""
        
        prompt = f"""당신은 한국어 원어민 표현 전문가입니다.

외국인 학습자가 다음 문장을 말했습니다:
"{user_sentence}"

상황: {target_role}에게 말하는 상황
필요한 격식: {target_formality}

다음 JSON 형식으로 답변해주세요:

{{
    "native_expressions": [
        {{
            "expression": "원어민이 자연스럽게 쓰는 표현",
            "formality": "informal/polite/formal",
            "naturalness": 5,
            "situation": "이 표현을 쓰는 상황",
            "nuance": "미묘한 뉘앙스 설명"
        }}
    ],
    "best_match": "가장 추천하는 표현",
    "differences": [
        {{
            "category": "vocabulary/grammar/nuance/formality/expression",
            "user_part": "학습자가 쓴 부분",
            "native_part": "원어민 표현",
            "explanation_ko": "한국어 설명",
            "explanation_en": "English explanation"
        }}
    ],
    "tips_ko": ["한국어 팁 1", "한국어 팁 2"],
    "tips_en": ["English tip 1", "English tip 2"],
    "naturalness_score": 75,
    "cultural_note": "문화적 배경 설명 (있으면)"
}}

3개의 자연스러운 원어민 표현을 제시하고, 학습자 표현과의 차이점을 친절하게 설명해주세요."""

        response = await self._clova_service.chat(
            user_message=prompt,
            system_message="You are a Korean native expression expert helping language learners.",
            temperature=0.7
        )
        
        # Parse JSON response
        return self._parse_clova_response(response, user_sentence, user_formality)
    
    def _parse_clova_response(
        self,
        response: str,
        user_sentence: str,
        user_formality: str
    ) -> NativeComparisonResult:
        """Parse CLOVA JSON response."""
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                
                native_expressions = [
                    NativeExpression(
                        expression=expr.get("expression", ""),
                        formality=expr.get("formality", "polite"),
                        naturalness=expr.get("naturalness", 4),
                        situation=expr.get("situation", ""),
                        nuance=expr.get("nuance", "")
                    )
                    for expr in data.get("native_expressions", [])
                ]
                
                differences = [
                    Difference(
                        category=diff.get("category", "expression"),
                        user_part=diff.get("user_part", ""),
                        native_part=diff.get("native_part", ""),
                        explanation_ko=diff.get("explanation_ko", ""),
                        explanation_en=diff.get("explanation_en", "")
                    )
                    for diff in data.get("differences", [])
                ]
                
                return NativeComparisonResult(
                    user_sentence=user_sentence,
                    user_formality=user_formality,
                    native_expressions=native_expressions,
                    best_match=data.get("best_match"),
                    differences=differences,
                    tips_ko=data.get("tips_ko", []),
                    tips_en=data.get("tips_en", []),
                    naturalness_score=data.get("naturalness_score", 70),
                    cultural_note=data.get("cultural_note")
                )
        except Exception as e:
            logger.error(f"Failed to parse CLOVA response: {e}")
        
        return self._compare_rule_based(
            user_sentence, "friend", "polite", user_formality, True
        )
    
    def _compare_rule_based(
        self,
        user_sentence: str,
        target_role: str,
        target_formality: str,
        user_formality: str,
        include_cultural_notes: bool
    ) -> NativeComparisonResult:
        """Rule-based native comparison."""
        
        native_expressions = []
        differences = []
        
        # Find matching patterns in database
        for pattern, alternatives in self.EXPRESSION_DATABASE.items():
            if pattern in user_sentence.lower():
                for formality, expressions in alternatives.items():
                    for expr in expressions[:2]:
                        native_expressions.append(NativeExpression(
                            expression=expr,
                            formality=formality,
                            naturalness=4 if formality == target_formality else 3,
                            situation=self._get_situation_desc(formality, target_role),
                            nuance=self._get_nuance_desc(formality)
                        ))
        
        # Check vocabulary upgrades
        for word, upgrades in self.VOCABULARY_UPGRADES.items():
            if isinstance(upgrades, dict) and word in user_sentence:
                if target_formality in ["formal", "very_polite"]:
                    if "honorific" in upgrades:
                        differences.append(Difference(
                            category="vocabulary",
                            user_part=word,
                            native_part=upgrades["honorific"],
                            explanation_ko=f"높임말로 '{upgrades['honorific']}'을 쓰세요",
                            explanation_en=f"Use honorific form '{upgrades['honorific']}'"
                        ))
        
        # Generate tips
        tips_ko, tips_en = self._generate_tips(
            user_sentence, target_role, target_formality, user_formality
        )
        
        # Calculate naturalness
        naturalness = self._calculate_naturalness(
            user_sentence, target_formality, user_formality, len(differences)
        )
        
        # Get best match
        best_match = None
        matching_formality = [e for e in native_expressions if e.formality == target_formality]
        if matching_formality:
            best_match = max(matching_formality, key=lambda x: x.naturalness).expression
        elif native_expressions:
            best_match = native_expressions[0].expression
        
        # Add fallback expressions if none found
        if not native_expressions:
            native_expressions = self._generate_fallback_expressions(user_sentence, target_formality)
            if native_expressions:
                best_match = native_expressions[0].expression
        
        # Cultural note
        cultural_note = None
        if include_cultural_notes:
            cultural_note = self._get_cultural_note(target_role, target_formality)
        
        return NativeComparisonResult(
            user_sentence=user_sentence,
            user_formality=user_formality,
            native_expressions=native_expressions,
            best_match=best_match,
            differences=differences,
            tips_ko=tips_ko,
            tips_en=tips_en,
            naturalness_score=naturalness,
            cultural_note=cultural_note
        )
    
    def _detect_formality(self, sentence: str) -> str:
        """Detect formality level of sentence."""
        if re.search(r'(습니다|습니까|십시오)[\.\?\!]?$', sentence):
            return "formal"
        elif re.search(r'(요|세요|죠|네요)[\.\?\!]?$', sentence):
            return "polite"
        else:
            return "informal"
    
    def _get_situation_desc(self, formality: str, target_role: str) -> str:
        """Get situation description."""
        descriptions = {
            "informal": "친한 친구나 후배와 대화할 때",
            "polite": "일반적인 상황, 처음 만난 사람과 대화할 때",
            "formal": "교수님, 직장 상사, 공식적인 자리에서"
        }
        return descriptions.get(formality, "일반적인 상황")
    
    def _get_nuance_desc(self, formality: str) -> str:
        """Get nuance description."""
        nuances = {
            "informal": "친근하고 편한 느낌",
            "polite": "예의 바르지만 딱딱하지 않은 느낌",
            "formal": "매우 공손하고 격식 있는 느낌"
        }
        return nuances.get(formality, "")
    
    def _generate_tips(
        self,
        sentence: str,
        target_role: str,
        target_formality: str,
        user_formality: str
    ) -> tuple:
        """Generate helpful tips."""
        tips_ko = []
        tips_en = []
        
        if user_formality != target_formality:
            if target_formality == "formal":
                tips_ko.append("문장 끝을 '-습니다/-습니까'로 바꿔보세요")
                tips_en.append("Try ending sentences with '-습니다/-습니까'")
            elif target_formality == "polite":
                tips_ko.append("문장 끝에 '-요'를 붙여보세요")
                tips_en.append("Try adding '-요' at the end")
        
        if target_role == "professor":
            tips_ko.append("'여쭤보다', '말씀' 같은 높임말 어휘를 사용해보세요")
            tips_en.append("Try using honorific vocabulary like '여쭤보다', '말씀'")
        
        if "주세요" in sentence:
            tips_ko.append("'~해 주실 수 있을까요?'처럼 부드럽게 요청하면 더 자연스러워요")
            tips_en.append("Softening requests like '~해 주실 수 있을까요?' sounds more natural")
        
        return tips_ko, tips_en
    
    def _calculate_naturalness(
        self,
        sentence: str,
        target_formality: str,
        user_formality: str,
        num_differences: int
    ) -> int:
        """Calculate naturalness score (0-100)."""
        score = 80
        
        if user_formality == target_formality:
            score += 10
        else:
            score -= 15
        
        score -= num_differences * 5
        
        if len(sentence) > 10:
            score += 5
        
        return max(0, min(100, score))
    
    def _generate_fallback_expressions(
        self,
        sentence: str,
        target_formality: str
    ) -> List[NativeExpression]:
        """Generate fallback expressions when no patterns match."""
        expressions = []
        
        if target_formality == "formal":
            if sentence.endswith("요"):
                new_expr = re.sub(r'요[\.\?\!]?$', '습니다', sentence)
                expressions.append(NativeExpression(
                    expression=new_expr,
                    formality="formal",
                    naturalness=4,
                    situation="공식적인 상황에서",
                    nuance="격식 있는 표현"
                ))
        elif target_formality == "polite":
            if not sentence.endswith("요"):
                expressions.append(NativeExpression(
                    expression=sentence + "요",
                    formality="polite",
                    naturalness=3,
                    situation="일반적인 대화에서",
                    nuance="예의 바른 표현"
                ))
        
        return expressions
    
    def _get_cultural_note(self, target_role: str, target_formality: str) -> Optional[str]:
        """Get relevant cultural note."""
        notes = {
            ("professor", "formal"): "한국에서 교수님께는 항상 격식체를 사용하고, '교수님'이라는 호칭을 빠뜨리지 않는 것이 중요해요.",
            ("senior", "polite"): "선배에게는 처음에 격식체를 쓰다가, 친해지면 존댓말(-요)로 바꾸는 게 자연스러워요.",
            ("boss", "formal"): "직장에서는 상사에게 항상 격식체를 사용하고, 보고할 때는 더 공손한 표현을 써요.",
        }
        return notes.get((target_role, target_formality))
    
    async def recommend_vocabulary(
        self,
        user_sentence: str,
        target_role: str = "friend",
        target_formality: str = "polite",
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Recommend better vocabulary using CLOVA X.
        
        Returns vocabulary upgrades, alternatives, and explanations.
        """
        self._initialize()
        
        # Use CLOVA X for smart recommendations
        if self._clova_service and self._clova_service.is_configured:
            try:
                return await self._recommend_with_clova(
                    user_sentence, target_role, target_formality, context
                )
            except Exception as e:
                logger.warning(f"CLOVA vocabulary recommendation failed: {e}")
        
        # Fallback to rule-based
        return self._recommend_rule_based(user_sentence, target_role, target_formality)
    
    async def _recommend_with_clova(
        self,
        user_sentence: str,
        target_role: str,
        target_formality: str,
        context: str
    ) -> Dict[str, Any]:
        """Use CLOVA X for vocabulary recommendations."""
        
        role_desc = {
            "professor": "교수님 (매우 공손하게)",
            "boss": "직장 상사 (격식체)",
            "senior": "선배 (존댓말)",
            "colleague": "동료 (편하게)",
            "friend": "친구 (반말)",
            "junior": "후배 (편하게)"
        }
        
        prompt = f"""당신은 한국어 어휘 전문가입니다.

학습자 문장: "{user_sentence}"
대화 상대: {role_desc.get(target_role, target_role)}
필요한 격식: {target_formality}
{f'상황: {context}' if context else ''}

다음 JSON 형식으로 어휘 추천을 해주세요:

{{
    "original_sentence": "학습자 원문",
    "improved_sentence": "개선된 문장 (가장 자연스러운 버전)",
    "vocabulary_changes": [
        {{
            "original": "원래 단어/표현",
            "recommended": "추천 단어/표현",
            "type": "honorific/politeness/natural/formal",
            "reason_ko": "한국어로 이유 설명",
            "reason_en": "English explanation",
            "examples": ["예문1", "예문2"]
        }}
    ],
    "grammar_changes": [
        {{
            "original": "원래 문법",
            "recommended": "추천 문법",
            "reason_ko": "설명"
        }}
    ],
    "alternative_expressions": [
        {{
            "expression": "대체 표현",
            "nuance": "뉘앙스 설명",
            "when_to_use": "언제 사용하는지"
        }}
    ],
    "formality_check": {{
        "current_level": "현재 격식 수준",
        "required_level": "필요한 격식 수준",
        "is_appropriate": true/false,
        "suggestion": "제안사항"
    }},
    "naturalness_score": 75,
    "key_tip": "가장 중요한 팁 한 줄"
}}

특히 다음을 확인해주세요:
1. 높임말 어휘 (예: 묻다→여쭙다, 주다→드리다)
2. 격식체 문법 (예: -요→-습니다)
3. 더 자연스러운 표현
4. 상황에 맞는 어휘 선택"""

        response = await self._clova_service.chat(
            user_message=prompt,
            system_message="You are a Korean vocabulary expert helping language learners choose the right words.",
            temperature=0.7
        )
        
        return self._parse_vocabulary_response(response, user_sentence)
    
    def _parse_vocabulary_response(
        self,
        response: str,
        user_sentence: str
    ) -> Dict[str, Any]:
        """Parse CLOVA vocabulary recommendation response."""
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return {
                    "success": True,
                    "source": "clova",
                    **data
                }
        except Exception as e:
            logger.error(f"Failed to parse CLOVA response: {e}")
        
        # Return basic structure on failure
        return {
            "success": False,
            "source": "fallback",
            "original_sentence": user_sentence,
            "improved_sentence": user_sentence,
            "vocabulary_changes": [],
            "error": "Failed to parse CLOVA response"
        }
    
    def _recommend_rule_based(
        self,
        user_sentence: str,
        target_role: str,
        target_formality: str
    ) -> Dict[str, Any]:
        """Rule-based vocabulary recommendations."""
        
        vocabulary_changes = []
        improved_sentence = user_sentence
        
        # Check for vocabulary upgrades
        for word, upgrades in self.VOCABULARY_UPGRADES.items():
            if isinstance(upgrades, dict) and word in user_sentence:
                if target_formality in ["formal", "very_polite"] and "honorific" in upgrades:
                    vocabulary_changes.append({
                        "original": word,
                        "recommended": upgrades["honorific"],
                        "type": "honorific",
                        "reason_ko": f"'{word}' 대신 높임말 '{upgrades['honorific']}'을 사용하세요",
                        "reason_en": f"Use honorific '{upgrades['honorific']}' instead of '{word}'",
                        "examples": []
                    })
                    improved_sentence = improved_sentence.replace(word, upgrades["honorific"])
        
        # Check grammar (ending)
        grammar_changes = []
        if target_formality == "formal":
            if re.search(r'어요[\.\?\!]?$', user_sentence):
                grammar_changes.append({
                    "original": "-어요",
                    "recommended": "-습니다",
                    "reason_ko": "격식체가 필요한 상황입니다"
                })
                improved_sentence = re.sub(r'어요([\.\?\!]?)$', r'습니다\1', improved_sentence)
            elif re.search(r'아요[\.\?\!]?$', user_sentence):
                grammar_changes.append({
                    "original": "-아요",
                    "recommended": "-습니다",
                    "reason_ko": "격식체가 필요한 상황입니다"
                })
                improved_sentence = re.sub(r'아요([\.\?\!]?)$', r'습니다\1', improved_sentence)
            elif re.search(r'요[\.\?\!]?$', user_sentence):
                grammar_changes.append({
                    "original": "-요",
                    "recommended": "-습니다",
                    "reason_ko": "격식체가 필요한 상황입니다"
                })
                # Handle common patterns
                improved_sentence = re.sub(r'있어요([\.\?\!]?)$', r'있습니다\1', improved_sentence)
                improved_sentence = re.sub(r'해요([\.\?\!]?)$', r'합니다\1', improved_sentence)
                improved_sentence = re.sub(r'요([\.\?\!]?)$', r'습니다\1', improved_sentence)
        
        # Determine naturalness
        naturalness = 80
        if vocabulary_changes:
            naturalness -= len(vocabulary_changes) * 10
        if grammar_changes:
            naturalness -= len(grammar_changes) * 10
        
        return {
            "success": True,
            "source": "rule_based",
            "original_sentence": user_sentence,
            "improved_sentence": improved_sentence,
            "vocabulary_changes": vocabulary_changes,
            "grammar_changes": grammar_changes,
            "alternative_expressions": [],
            "formality_check": {
                "current_level": self._detect_formality(user_sentence),
                "required_level": target_formality,
                "is_appropriate": self._detect_formality(user_sentence) == target_formality,
                "suggestion": "격식을 맞춰주세요" if self._detect_formality(user_sentence) != target_formality else "적절합니다"
            },
            "naturalness_score": max(0, naturalness),
            "key_tip": "CLOVA API를 연결하면 더 정확한 추천을 받을 수 있습니다"
        }
    
    async def get_expression_for_situation(
        self,
        situation: str,
        target_role: str = "friend",
        target_formality: str = "polite"
    ) -> Dict[str, Any]:
        """
        Get recommended expressions for a specific situation using CLOVA X.
        
        Example situations:
        - "asking for a recommendation letter"
        - "apologizing for being late"
        - "ordering coffee at a cafe"
        """
        self._initialize()
        
        if self._clova_service and self._clova_service.is_configured:
            try:
                return await self._get_situation_expressions_clova(
                    situation, target_role, target_formality
                )
            except Exception as e:
                logger.warning(f"CLOVA situation expressions failed: {e}")
        
        return self._get_situation_expressions_fallback(situation, target_role)
    
    async def _get_situation_expressions_clova(
        self,
        situation: str,
        target_role: str,
        target_formality: str
    ) -> Dict[str, Any]:
        """Get situation expressions using CLOVA X."""
        
        prompt = f"""상황: {situation}
대화 상대: {target_role}
격식 수준: {target_formality}

이 상황에서 한국어 원어민이 자연스럽게 사용하는 표현들을 알려주세요.

JSON 형식:
{{
    "situation": "상황 설명",
    "expressions": [
        {{
            "expression": "자연스러운 표현",
            "literal_meaning": "직역",
            "usage": "사용 상황",
            "formality": "격식 수준",
            "tip": "사용 팁"
        }}
    ],
    "vocabulary_to_know": [
        {{
            "word": "단어",
            "meaning": "의미",
            "usage_example": "예문"
        }}
    ],
    "common_mistakes": [
        {{
            "wrong": "틀린 표현",
            "correct": "올바른 표현",
            "explanation": "설명"
        }}
    ],
    "cultural_note": "문화적 배경 (있으면)"
}}

최소 3개의 자연스러운 표현을 제시해주세요."""

        response = await self._clova_service.chat(
            user_message=prompt,
            system_message="You are a Korean language expert helping learners with natural expressions.",
            temperature=0.8
        )
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return {"success": True, "source": "clova", **data}
        except:
            pass
        
        return {"success": False, "source": "fallback", "raw_response": response}
    
    def _get_situation_expressions_fallback(
        self,
        situation: str,
        target_role: str
    ) -> Dict[str, Any]:
        """Fallback situation expressions."""
        
        # Common situations database
        situations = {
            "professor": [
                {"expression": "교수님, 잠깐 여쭤봐도 될까요?", "usage": "질문할 때"},
                {"expression": "교수님, 혹시 시간 괜찮으시면...", "usage": "부탁할 때"},
                {"expression": "감사합니다, 교수님", "usage": "감사 인사"},
                {"expression": "죄송합니다, 교수님", "usage": "사과할 때"},
            ],
            "senior": [
                {"expression": "선배님, 혹시 잠깐 시간 되세요?", "usage": "말 걸 때"},
                {"expression": "선배님 덕분이에요", "usage": "감사할 때"},
            ],
            "friend": [
                {"expression": "야, 뭐해?", "usage": "일상 인사"},
                {"expression": "오늘 시간 돼?", "usage": "약속 잡을 때"},
            ]
        }
        
        return {
            "success": True,
            "source": "fallback",
            "situation": situation,
            "expressions": situations.get(target_role, situations["friend"]),
            "note": "CLOVA API를 연결하면 상황에 맞는 더 정확한 표현을 받을 수 있습니다"
        }


# Singleton instance
native_comparison_service = NativeComparisonService()
