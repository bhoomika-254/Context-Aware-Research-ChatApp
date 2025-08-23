"""Main application entry point."""

from fastapi import FastAPI
from app.config import settings

# This will be implemented in Phase 5

from app.routes.briefs import router as briefs_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Context-aware research brief generator using LangGraph and LangChain",
    debug=settings.debug
)
app.include_router(briefs_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Context-Aware Research Assistant API",
        "version": settings.app_version,
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": "2025-08-19T00:00:00Z"
    }