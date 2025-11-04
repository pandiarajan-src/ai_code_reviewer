"""API endpoints for retrieving review records."""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ai_code_reviewer.api.db.database import get_db_session
from ai_code_reviewer.api.db.repository import ReviewRepository


logger = logging.getLogger(__name__)
router = APIRouter()


class ReviewRecordResponse(BaseModel):
    """Response model for review records."""

    id: int
    created_at: datetime
    review_type: str
    trigger_type: str
    project_key: str
    repo_slug: str
    commit_id: str | None = None
    pr_id: int | None = None
    author_name: str | None = None
    author_email: str | None = None
    diff_content: str
    review_feedback: str
    email_recipients: dict | None = None
    email_sent: bool
    llm_provider: str | None = None
    llm_model: str | None = None

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    """Response model for list of reviews."""

    total: int
    offset: int
    limit: int
    records: list[ReviewRecordResponse]


@router.get("/reviews/latest", response_model=list[ReviewRecordResponse])
async def get_latest_reviews(
    limit: int = Query(default=10, ge=1, le=100, description="Number of latest reviews to retrieve"),
):
    """Get the latest N review records ordered by creation date."""
    try:
        async with get_db_session() as session:
            repo = ReviewRepository(session)
            records = await repo.get_latest_reviews(limit=limit)

            return [ReviewRecordResponse.model_validate(record) for record in records]

    except Exception as e:
        logger.error(f"Error retrieving latest reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving reviews: {str(e)}")


@router.get("/reviews", response_model=ReviewListResponse)
async def get_reviews_filtered(
    offset: int = Query(default=0, ge=0, description="Starting record number (0-indexed)"),
    limit: int = Query(default=10, ge=1, le=100, description="Number of records to retrieve"),
    project_key: str | None = Query(default=None, description="Filter by project key"),
    repo_slug: str | None = Query(default=None, description="Filter by repository slug"),
    commit_id: str | None = Query(default=None, description="Filter by commit ID"),
    pr_id: int | None = Query(default=None, description="Filter by pull request ID"),
):
    """Get review records with optional filtering and pagination.

    Returns paginated reviews with optional filters for project, repository, commit, or pull request.
    Filters can be combined for more specific queries.
    """
    try:
        async with get_db_session() as session:
            repo = ReviewRepository(session)

            # Get filtered records
            records = await repo.get_reviews_filtered(
                offset=offset,
                limit=limit,
                project_key=project_key,
                repo_slug=repo_slug,
                commit_id=commit_id,
                pr_id=pr_id,
            )

            # Get count with same filters
            total = await repo.count_reviews_filtered(
                project_key=project_key,
                repo_slug=repo_slug,
                commit_id=commit_id,
                pr_id=pr_id,
            )

            return ReviewListResponse(
                total=total,
                offset=offset,
                limit=limit,
                records=[ReviewRecordResponse.model_validate(record) for record in records],
            )

    except Exception as e:
        logger.error(f"Error retrieving filtered reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving reviews: {str(e)}")


@router.get("/reviews/stats")
async def get_review_stats():
    """Get comprehensive review statistics.

    Returns statistics including:
    - Total review count
    - Breakdown by review type (auto/manual)
    - Breakdown by trigger type (commit/pull_request)
    - Email success rate
    - Breakdown by LLM provider
    """
    try:
        async with get_db_session() as session:
            repo = ReviewRepository(session)
            stats = await repo.get_review_stats()
            return stats

    except Exception as e:
        logger.error(f"Error retrieving review stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")


@router.get("/reviews/{review_id}", response_model=ReviewRecordResponse)
async def get_review_by_id(review_id: int):
    """Get a specific review record by ID."""
    try:
        async with get_db_session() as session:
            repo = ReviewRepository(session)
            record = await repo.get_review_by_id(review_id)

            if not record:
                raise HTTPException(status_code=404, detail=f"Review record {review_id} not found")

            return ReviewRecordResponse.model_validate(record)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving review {review_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving review: {str(e)}")
