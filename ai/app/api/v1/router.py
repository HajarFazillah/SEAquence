"""
API Router - Combines all v1 endpoints
"""

from fastapi import APIRouter

from app.api.v1 import (
    chat, recommendation, compatibility, memory, vocabulary,
    starters, grammar, analytics,
    analysis, ml_router, topics, avatars, revision, progress,
    integrated, prompts,
)

router = APIRouter(prefix="/api/v1")

# Original routers
router.include_router(chat.router)
router.include_router(recommendation.router)
router.include_router(compatibility.router)
router.include_router(memory.router)
router.include_router(vocabulary.router)
router.include_router(starters.router)
router.include_router(grammar.router)
router.include_router(analytics.router)

# New routers
router.include_router(analysis.router)
router.include_router(ml_router.router)
router.include_router(topics.router)
router.include_router(avatars.router)
router.include_router(revision.router)
router.include_router(progress.router)
router.include_router(integrated.router)
router.include_router(prompts.router)
