"""
Enhanced API Schemas for Phase 1
Word-level analysis, corrections, error categories
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# ===========================================
# Enums
# ===========================================

class FormailtyLevel(str, Enum):
    INFORMAL = "informal"
    POLITE = "polite"
    VERY_POLITE = "very_polite"
    MIXED = "mixed"


class ErrorSeverity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ErrorType(str, Enum):
    ENDING_MISMATCH = "ending_mismatch"
    HONORIFIC_MISSING = "honorific_missing"
    FORMALITY_MIXED = "formality_mixed"
    WORD_CHOICE = "word_choice"
    SUBJECT_MARKER = "subject_marker"
    TONE_INAPPROPRIATE = "tone_inappropriate"


# ===========================================
# Word-Level Analysis
# ===========================================

class WordAnalysisResult(BaseModel):
    """Analysis of a single word."""
    word: str = Field(..., description="The analyzed word")
    position_start: int = Field(..., description="Start position in text")
    position_end: int = Field(..., description="End position in text")
    current_level: str = Field(..., description="Detected formality level")
    expected_level: Optional[str] = Field(None, description="Expected level for context")
    is_correct: bool = Field(..., description="Whether word matches expected level")
    suggestion: Optional[str] = Field(None, description="Suggested correction")
    error_type: Optional[str] = Field(None, description="Type of error if incorrect")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "word": "있어요",
                "position_start": 8,
                "position_end": 11,
                "current_level": "polite",
                "expected_level": "very_polite",
                "is_correct": False,
                "suggestion": "있습니다",
                "error_type": "ending_mismatch"
            }]
        }
    }


# ===========================================
# Corrections
# ===========================================

class CorrectionResult(BaseModel):
    """Suggested correction for an error."""
    original: str = Field(..., description="Original text")
    corrected: str = Field(..., description="Corrected text")
    reason_ko: str = Field(..., description="Reason in Korean")
    reason_en: str = Field(..., description="Reason in English")
    position_start: int = Field(..., description="Start position")
    position_end: int = Field(..., description="End position")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "original": "있어요",
                "corrected": "있습니다",
                "reason_ko": "존댓말 대신 격식체(-습니다)를 사용하세요",
                "reason_en": "Use formal speech (-습니다) instead of polite",
                "position_start": 8,
                "position_end": 11
            }]
        }
    }


# ===========================================
# Error Categories
# ===========================================

class ErrorDetail(BaseModel):
    """Categorized error details."""
    error_type: str = Field(..., description="Error category")
    name_ko: str = Field(..., description="Error name in Korean")
    name_en: str = Field(..., description="Error name in English")
    severity: str = Field(..., description="Error severity: high/medium/low")
    count: int = Field(..., description="Number of occurrences")
    examples: List[str] = Field(..., description="Example corrections")


# ===========================================
# Level Breakdown
# ===========================================

class LevelBreakdown(BaseModel):
    """Breakdown of formality levels in text."""
    informal: float = Field(0, ge=0, le=1, description="Ratio of informal speech")
    polite: float = Field(0, ge=0, le=1, description="Ratio of polite speech")
    very_polite: float = Field(0, ge=0, le=1, description="Ratio of formal speech")
    honorific: float = Field(0, ge=0, le=1, description="Ratio of honorific markers")


# ===========================================
# Enhanced Politeness Request/Response
# ===========================================

class EnhancedPolitenessRequest(BaseModel):
    """Request for enhanced politeness analysis."""
    text: str = Field(..., min_length=1, max_length=5000, description="Korean text to analyze")
    target_role: Optional[str] = Field(None, description="Role of person being addressed")
    target_age: Optional[int] = Field(None, ge=1, le=100, description="Age of person being addressed")
    user_age: int = Field(default=22, ge=1, le=100, description="Age of speaker")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "text": "교수님 질문이 있어요",
                "target_role": "professor",
                "target_age": 55,
                "user_age": 22
            }]
        }
    }


class EnhancedPolitenessResponse(BaseModel):
    """Enhanced politeness analysis response."""
    # Basic info
    level: str = Field(..., description="Dominant formality level")
    level_ko: str = Field(..., description="Level name in Korean")
    level_en: str = Field(..., description="Level name in English")
    score: int = Field(..., ge=0, le=100, description="Politeness score")
    is_appropriate: bool = Field(..., description="Whether level is appropriate for context")
    
    # Detailed breakdown
    level_breakdown: LevelBreakdown = Field(..., description="Ratio of each formality level")
    
    # Word-level analysis
    word_analysis: List[WordAnalysisResult] = Field(..., description="Analysis of each word")
    
    # Corrections
    corrections: List[CorrectionResult] = Field(..., description="Suggested corrections")
    
    # Error summary
    errors: List[ErrorDetail] = Field(..., description="Categorized errors")
    
    # Feedback
    recommended_level: Optional[str] = Field(None, description="Expected level for context")
    feedback_ko: Optional[str] = Field(None, description="Feedback in Korean")
    feedback_en: Optional[str] = Field(None, description="Feedback in English")
    
    # Meta
    details: Dict[str, Any] = Field(default={}, description="Additional details")


# ===========================================
# Chat with Enhanced Feedback
# ===========================================

class EnhancedMessageFeedback(BaseModel):
    """Enhanced feedback for a chat message."""
    # Basic scores
    level: str
    level_ko: str
    score: int
    is_appropriate: bool
    
    # Word-level highlights (for UI)
    word_highlights: List[WordAnalysisResult] = Field(
        default=[], 
        description="Words to highlight in UI"
    )
    
    # Top corrections (limited for chat)
    top_corrections: List[CorrectionResult] = Field(
        default=[],
        description="Top 3 corrections"
    )
    
    # Error summary
    error_summary: Dict[str, int] = Field(
        default={},
        description="Count by error type"
    )
    
    # Quick feedback
    feedback_ko: Optional[str] = None
    feedback_en: Optional[str] = None


class EnhancedChatMessageResponse(BaseModel):
    """Chat message response with enhanced feedback."""
    session_id: str
    
    user_message: Dict[str, Any] = Field(..., description="User message with feedback")
    avatar_response: Dict[str, Any] = Field(..., description="Avatar's response")
    
    # Enhanced feedback
    enhanced_feedback: Optional[EnhancedMessageFeedback] = Field(
        None,
        description="Detailed politeness feedback"
    )
    
    turn_count: int
    current_topic: Optional[str] = None


# ===========================================
# Analysis Summary (for session end)
# ===========================================

class SessionAnalysisSummary(BaseModel):
    """Summary of politeness analysis for entire session."""
    total_messages: int
    average_score: float
    
    # Level usage
    level_distribution: Dict[str, int] = Field(
        ...,
        description="Count of messages at each level"
    )
    
    # Error patterns
    common_errors: List[ErrorDetail] = Field(
        ...,
        description="Most common errors across session"
    )
    
    # Improvement
    score_trend: List[int] = Field(
        ...,
        description="Scores over time"
    )
    improvement_rate: float = Field(
        ...,
        description="Improvement percentage"
    )
    
    # Recommendations
    strengths: List[str] = Field(..., description="What user did well")
    areas_to_improve: List[str] = Field(..., description="What to practice")
    suggested_practice: List[str] = Field(..., description="Recommended exercises")
