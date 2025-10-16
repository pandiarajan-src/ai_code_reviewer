"""Health check endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter

from ai_code_reviewer.api.dependencies import get_bitbucket_client, get_llm_client
from ai_code_reviewer.core.config import Config


router = APIRouter()

# Version from pyproject.toml
API_VERSION = "1.0.0"


@router.get("/")
async def root():
    """Root endpoint with basic API information"""
    return {
        "message": "AI Code Reviewer",
        "status": "healthy",
        "version": API_VERSION,
        "datetime": datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"),
    }


@router.get("/health")
async def health_check():
    """Basic health check - lightweight for container health checks"""
    return {
        "status": "healthy",
        "datetime": datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"),
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """Comprehensive health check with external API validation"""
    health_status = {
        "status": "healthy",
        "datetime": datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"),
        "services": {},
    }

    # Test Bitbucket connection
    try:
        bitbucket_client = get_bitbucket_client()
        bitbucket_result = await bitbucket_client.test_connection()
        is_connected = bitbucket_result.get("status") == "connected"
        health_status["services"]["bitbucket"] = {
            "status": "healthy" if is_connected else "unhealthy",
            "url": Config.BITBUCKET_URL,
        }
        if is_connected:
            health_status["services"]["bitbucket"]["message"] = bitbucket_result.get("message", "Connection successful")
        else:
            health_status["services"]["bitbucket"]["error"] = bitbucket_result.get("message", "Connection failed")
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["bitbucket"] = {
            "status": "unhealthy",
            "url": Config.BITBUCKET_URL,
            "error": str(e),
        }

    # Test LLM connection
    try:
        llm_client = get_llm_client()
        llm_result = await llm_client.test_connection()
        is_connected = llm_result.get("status") == "connected"
        health_status["services"]["llm"] = {
            "status": "healthy" if is_connected else "unhealthy",
            "provider": Config.LLM_PROVIDER,
        }
        if is_connected:
            health_status["services"]["llm"]["message"] = llm_result.get("message", "Connection successful")
        else:
            health_status["services"]["llm"]["error"] = llm_result.get("message", "Connection failed")
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["llm"] = {
            "status": "unhealthy",
            "provider": Config.LLM_PROVIDER,
            "error": str(e),
        }

    # Update overall status if any service is unhealthy
    if any(service.get("status") == "unhealthy" for service in health_status["services"].values()):
        health_status["status"] = "unhealthy"

    return health_status
