"""FastAPI application initialization and configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_code_reviewer.api.routes import health, manual, webhook


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="AI Code Reviewer",
        description="AI-powered code review agent for Bitbucket Enterprise Server",
        version="1.0.0",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, tags=["health"])
    app.include_router(webhook.router, tags=["webhook"])
    app.include_router(manual.router, tags=["manual"])

    return app
