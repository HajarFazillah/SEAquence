"""
Talkativ AI Server
Main FastAPI application entry point
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1.router import api_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.APP_DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan handler.
    Initialize resources on startup, cleanup on shutdown.
    """
    # Startup
    logger.info("🚀 Starting Talkativ AI Server...")
    logger.info(f"   Environment: {settings.APP_ENV}")
    logger.info(f"   Debug: {settings.APP_DEBUG}")
    logger.info(f"   CLOVA configured: {settings.has_clova}")
    logger.info(f"   Speech configured: {settings.has_speech}")
    logger.info(f"   Voice configured: {settings.has_voice}")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down Talkativ AI Server...")


# Create FastAPI application
app = FastAPI(
    title="Talkativ AI",
    description="""
🗣️ **AI-powered Korean Conversation Coaching API**

Talkativ AI helps Korean language learners practice real-world conversations 
with AI-powered avatars.

## Features

* **Topic Detection** - Identify conversation topics from Korean text
* **Topic Recommendation** - Get safe topic suggestions for conversations
* **Politeness Analysis** - Analyze Korean speech levels (반말/존댓말/격식체)
* **Chat Simulation** - Practice with AI avatars using HyperCLOVA X
* **Speech Services** - TTS and STT powered by CLOVA

## Avatars

| Avatar | Role | Formality |
|--------|------|-----------|
| 민수 선배 | Senior | Polite (-요) |
| 김 교수님 | Professor | Formal (-습니다) |
| 수진 | Friend | Informal (반말) |

## Quick Start

```python
import requests

# Start a chat session
response = requests.post(
    "http://localhost:8000/api/v1/chat/start",
    json={"user_id": "user123", "avatar_id": "sujin_friend"}
)
session = response.json()

# Send a message
response = requests.post(
    "http://localhost:8000/api/v1/chat/message",
    json={"session_id": session["session_id"], "message": "안녕! 뭐해?"}
)
```
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ===========================================
# Middleware
# ===========================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing."""
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    logger.info(
        f"{request.method} {request.url.path} "
        f"- {response.status_code} "
        f"- {duration:.3f}s"
    )
    
    response.headers["X-Process-Time"] = f"{duration:.3f}"
    return response


# ===========================================
# Routes
# ===========================================

# Include API v1 routes
app.include_router(api_router, prefix="/api/v1")


# Health check
@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint.
    
    Returns service status and API availability.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "services": {
            "clova_llm": settings.has_clova,
            "clova_speech": settings.has_speech,
            "clova_voice": settings.has_voice,
            "openai": settings.has_openai,
        }
    }


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": "Talkativ AI",
        "version": "1.0.0",
        "description": "AI-powered Korean conversation coaching",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "api_prefix": "/api/v1"
    }


# ===========================================
# Exception Handlers
# ===========================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "detail": str(exc) if settings.APP_DEBUG else None
        }
    )


# ===========================================
# CLI Entry Point
# ===========================================

def main():
    """CLI entry point for running the server."""
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
        log_level="debug" if settings.APP_DEBUG else "info"
    )


if __name__ == "__main__":
    main()
