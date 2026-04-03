"""
API Router Aggregation
Combines all v1 API endpoints
"""

from fastapi import APIRouter

# Core routes
from app.api.v1 import analysis, chat, avatars

# Phase 1: Enhanced Analysis
from app.api.v1 import enhanced_analysis

# Phase 2: Personalization
from app.api.v1 import progress, personalized_chat

# Multi-Avatar
from app.api.v1 import avatar_management

# Enhanced System Prompt
from app.api.v1 import prompt_preview

# Revision & Sample Reply
from app.api.v1 import revision, integrated_chat

# ML Analysis
from app.api.v1 import ml_analysis

# Native Comparison
from app.api.v1 import native_comparison

# Context-Aware Chat (Mistake Tracking)
from app.api.v1 import context_chat

# Situations
from app.api.v1 import situations

# Session-Aware Chat
from app.api.v1 import session_chat

# Emotion & Feedback
from app.api.v1 import emotion

# Sophisticated Speech Analysis
from app.api.v1 import speech_analysis

# Recommendation (Speech Level Before Chat)
from app.api.v1 import recommendation

# Compatibility (ML-based Interest Matching)
from app.api.v1 import compatibility

api_router = APIRouter()

# ===========================================
# Core Routes
# ===========================================

api_router.include_router(
    analysis.router,
    prefix="/analysis",
    tags=["Analysis"]
)

api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat"]
)

api_router.include_router(
    avatars.router,
    prefix="/avatars",
    tags=["Avatars"]
)

# ===========================================
# Phase 1: Enhanced Analysis
# ===========================================

api_router.include_router(
    enhanced_analysis.router,
    prefix="/analysis",
    tags=["Enhanced Analysis"]
)

# ===========================================
# Phase 2: Personalization
# ===========================================

api_router.include_router(
    progress.router,
    prefix="/progress",
    tags=["User Progress"]
)

api_router.include_router(
    personalized_chat.router,
    prefix="/chat/personalized",
    tags=["Personalized Chat"]
)

# ===========================================
# Multi-Avatar
# ===========================================

api_router.include_router(
    avatar_management.router,
    prefix="/avatars",
    tags=["Avatar Management"]
)

# ===========================================
# Enhanced System Prompt
# ===========================================

api_router.include_router(
    prompt_preview.router,
    prefix="/prompts",
    tags=["System Prompts"]
)

# ===========================================
# Revision & Sample Reply
# ===========================================

api_router.include_router(
    revision.router,
    prefix="/revision",
    tags=["Revision & Sample Reply"]
)

api_router.include_router(
    integrated_chat.router,
    prefix="/integrated",
    tags=["Integrated Chat"]
)

# ===========================================
# ML Analysis
# ===========================================

api_router.include_router(
    ml_analysis.router,
    prefix="/ml",
    tags=["ML Analysis"]
)

# ===========================================
# Native Comparison
# ===========================================

api_router.include_router(
    native_comparison.router,
    prefix="/native",
    tags=["Native Comparison"]
)

# ===========================================
# Context-Aware Chat (Mistake Tracking)
# ===========================================

api_router.include_router(
    context_chat.router,
    tags=["Context-Aware Chat"]
)

# ===========================================
# Situations (Conversation Scenarios)
# ===========================================

api_router.include_router(
    situations.router,
    tags=["Situations"]
)

# ===========================================
# Session-Aware Chat (For Backend Integration)
# ===========================================

api_router.include_router(
    session_chat.router,
    tags=["Session Chat"]
)

# ===========================================
# Emotion & Feedback
# ===========================================

api_router.include_router(
    emotion.router,
    tags=["Emotion & Feedback"]
)

# ===========================================
# Sophisticated Speech Level Analysis
# ===========================================

api_router.include_router(
    speech_analysis.router,
    tags=["Speech Level Analysis"]
)

# ===========================================
# Recommendation (Before Chat)
# ===========================================

api_router.include_router(
    recommendation.router,
    tags=["Recommendation"]
)

# ===========================================
# Compatibility (ML-based Interest Matching)
# ===========================================

api_router.include_router(
    compatibility.router,
    tags=["Compatibility"]
)