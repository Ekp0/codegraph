"""
CodeGraph Backend - Health Check Routes
"""
from fastapi import APIRouter
from app.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "providers": settings.get_available_providers(),
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness check for Kubernetes/Docker health probes."""
    # TODO: Add database and Redis connectivity checks
    return {"status": "ready"}
