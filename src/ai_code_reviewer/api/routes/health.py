"""Health check endpoints."""

from datetime import UTC, datetime
from typing import Any

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
        "message": "AI Code Reviewer is running",
        "status": "healthy",
        "version": API_VERSION,
        "datetime": datetime.now(UTC).strftime("%a, %d %b %Y %H:%M:%S GMT"),
    }


@router.get("/health")
async def health_check():
    """Basic health check - lightweight for container health checks"""
    try:
        # Validate configuration
        Config.validate_config()
        return {
            "status": "healthy",
            "timestamp": datetime.now(UTC).strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "config": {
                "bitbucket_url": Config.BITBUCKET_URL,
                "llm_provider": Config.LLM_PROVIDER,
            },
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(UTC).strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "error": str(e),
        }


@router.get("/health/detailed")
async def detailed_health_check():
    """Comprehensive health check with external API validation"""
    health_status: dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.now(UTC).strftime("%a, %d %b %Y %H:%M:%S GMT"),
        "config": {
            "bitbucket_url": Config.BITBUCKET_URL,
            "llm_provider": Config.LLM_PROVIDER,
        },
    }

    # Test Bitbucket connection
    try:
        bitbucket_client = get_bitbucket_client()
        bitbucket_result = await bitbucket_client.test_connection()
        is_connected = bitbucket_result.get("status") == "connected"
        health_status["bitbucket"] = {
            "status": "healthy" if is_connected else "unhealthy",
            "url": Config.BITBUCKET_URL,
        }
        if is_connected:
            health_status["bitbucket"]["message"] = bitbucket_result.get("message", "Connection successful")
        else:
            health_status["bitbucket"]["error"] = bitbucket_result.get("message", "Connection failed")
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["bitbucket"] = {
            "status": "unhealthy",
            "url": Config.BITBUCKET_URL,
            "error": str(e),
        }

    # Test LLM connection
    try:
        llm_client = get_llm_client()
        llm_result = await llm_client.test_connection()
        is_connected = llm_result.get("status") == "connected"
        health_status["llm"] = {
            "status": "healthy" if is_connected else "unhealthy",
            "provider": Config.LLM_PROVIDER,
        }
        if is_connected:
            health_status["llm"]["message"] = llm_result.get("message", "Connection successful")
        else:
            health_status["llm"]["error"] = llm_result.get("message", "Connection failed")
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["llm"] = {
            "status": "unhealthy",
            "provider": Config.LLM_PROVIDER,
            "error": str(e),
        }

    # Update overall status if any service is unhealthy
    if (
        health_status.get("bitbucket", {}).get("status") == "unhealthy"
        or health_status.get("llm", {}).get("status") == "unhealthy"
    ):
        health_status["status"] = "unhealthy"

    return health_status
