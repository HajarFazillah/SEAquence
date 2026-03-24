"""
Talkativ AI Server - Main Application

Korean conversation coaching AI powered by HyperCLOVA X.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_router
from app.core.config import settings


app = FastAPI(
    title="Talkativ AI Server",
    description="Korean conversation coaching AI for language learners",
    version="2.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "name": "Talkativ AI Server",
        "version": "2.0.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    from app.services.clova_service import clova_service
    
    return {
        "status": "healthy",
        "clova_configured": clova_service.is_configured,
    }
