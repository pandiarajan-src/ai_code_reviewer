"""FastAPI application initialization and configuration."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_code_reviewer.api.db.database import close_db, init_db
from ai_code_reviewer.api.routes import failures, health, manual, reviews, webhook
from alembic import command
from alembic.config import Config


logger = logging.getLogger(__name__)


def run_migrations() -> None:
    """Run Alembic database migrations."""
    try:
        # Get the project root directory (where alembic.ini is located)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        alembic_ini_path = os.path.join(project_root, "alembic.ini")

        if not os.path.exists(alembic_ini_path):
            logger.warning(f"Alembic configuration not found at {alembic_ini_path}, skipping migrations")
            return

        logger.info(f"Running database migrations from {alembic_ini_path}...")
        alembic_cfg = Config(alembic_ini_path)
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Failed to run database migrations: {e}")
        # Don't raise - allow app to start with current schema
        # This allows graceful degradation if migrations fail


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Running database migrations...")
    run_migrations()

    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully")
    yield
    # Shutdown
    logger.info("Closing database connections...")
    await close_db()
    logger.info("Database connections closed")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="AI Code Reviewer",
        description="AI-powered code review agent for Bitbucket Enterprise Server",
        version="1.0.0",
        lifespan=lifespan,
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
    app.include_router(reviews.router, tags=["reviews"])
    app.include_router(failures.router, tags=["failures"])

    return app


# Create application instance
app = create_app()
