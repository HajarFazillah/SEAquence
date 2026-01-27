"""
API Router Aggregation
Combines all v1 API endpoints
"""

from fastapi import APIRouter

from app.api.v1 import topics, analysis, chat, avatars, enhanced_analysis

api_router = APIRouter()

# Include all v1 routes
api_router.include_router(
    topics.router,
    prefix="/topics",
    tags=["Topics"]
)

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

api_router.include_router(
    enhanced_analysis.router,
    prefix="/analysis",
    tags=["Enhanced Analysis"]
)
