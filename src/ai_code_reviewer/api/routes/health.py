"""Health check endpoints."""

from datetime import datetime

from fastapi import APIRouter

from ai_code_reviewer.api.dependencies import get_bitbucket_client, get_llm_client
from ai_code_reviewer.core.config import Config


router = APIRouter()


@router.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Code Reviewer is running", "status": "healthy"}


@router.get("/health")
async def health_check():
    """Basic health check - lightweight for container health checks"""
    try:
        # Only validate configuration (no external API calls)
        Config.validate_config()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "config": {
                "bitbucket_url": Config.BITBUCKET_URL,
                "llm_provider": Config.LLM_PROVIDER,
                "llm_model": Config.LLM_MODEL,
            },
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@router.get("/health/detailed")
async def detailed_health_check():
    """Comprehensive health check with external API validation"""
    try:
        # Validate configuration
        Config.validate_config()

        # Get clients
        bitbucket_client = get_bitbucket_client()
        llm_client = get_llm_client()

        # Test Bitbucket connection
        bitbucket_status = await bitbucket_client.test_connection()

        # Test LLM connection
        llm_status = await llm_client.test_connection()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "bitbucket": bitbucket_status,
            "llm": llm_status,
            "config": {
                "bitbucket_url": Config.BITBUCKET_URL,
                "llm_provider": Config.LLM_PROVIDER,
                "llm_model": Config.LLM_MODEL,
            },
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
