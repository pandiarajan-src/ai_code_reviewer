"""API endpoints for retrieving review records."""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ai_code_reviewer.db.database import get_db_session
from ai_code_reviewer.db.repository import ReviewRepository


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
async def get_reviews_paginated(
    offset: int = Query(default=0, ge=0, description="Starting record number (0-indexed)"),
    limit: int = Query(default=10, ge=1, le=100, description="Number of records to retrieve"),
):
    """Get review records with pagination (offset and limit)."""
    try:
        async with get_db_session() as session:
            repo = ReviewRepository(session)
            records = await repo.get_reviews_paginated(offset=offset, limit=limit)
            total = await repo.count_total_reviews()

            return ReviewListResponse(
                total=total,
                offset=offset,
                limit=limit,
                records=[ReviewRecordResponse.model_validate(record) for record in records],
            )

    except Exception as e:
        logger.error(f"Error retrieving paginated reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving reviews: {str(e)}")


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


@router.get("/reviews/project/{project_key}", response_model=list[ReviewRecordResponse])
async def get_reviews_by_project(
    project_key: str,
    repo_slug: str | None = Query(default=None, description="Optional repository slug to filter by"),
    limit: int = Query(default=10, ge=1, le=100, description="Number of reviews to retrieve"),
):
    """Get review records for a specific project/repository."""
    try:
        async with get_db_session() as session:
            repo = ReviewRepository(session)
            records = await repo.get_reviews_by_project(project_key=project_key, repo_slug=repo_slug, limit=limit)

            return [ReviewRecordResponse.model_validate(record) for record in records]

    except Exception as e:
        logger.error(f"Error retrieving reviews for project {project_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving reviews: {str(e)}")


@router.get("/reviews/author/{author_email}", response_model=list[ReviewRecordResponse])
async def get_reviews_by_author(
    author_email: str, limit: int = Query(default=10, ge=1, le=100, description="Number of reviews to retrieve")
):
    """Get review records for a specific author."""
    try:
        async with get_db_session() as session:
            repo = ReviewRepository(session)
            records = await repo.get_reviews_by_author(author_email=author_email, limit=limit)

            return [ReviewRecordResponse.model_validate(record) for record in records]

    except Exception as e:
        logger.error(f"Error retrieving reviews for author {author_email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving reviews: {str(e)}")


@router.get("/reviews/commit/{commit_id}", response_model=list[ReviewRecordResponse])
async def get_reviews_by_commit(commit_id: str):
    """Get review records for a specific commit."""
    try:
        async with get_db_session() as session:
            repo = ReviewRepository(session)
            records = await repo.get_reviews_by_commit(commit_id=commit_id)

            return [ReviewRecordResponse.model_validate(record) for record in records]

    except Exception as e:
        logger.error(f"Error retrieving reviews for commit {commit_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving reviews: {str(e)}")


@router.get("/reviews/pr/{pr_id}", response_model=list[ReviewRecordResponse])
async def get_reviews_by_pr(pr_id: int):
    """Get review records for a specific pull request."""
    try:
        async with get_db_session() as session:
            repo = ReviewRepository(session)
            records = await repo.get_reviews_by_pr(pr_id=pr_id)

            return [ReviewRecordResponse.model_validate(record) for record in records]

    except Exception as e:
        logger.error(f"Error retrieving reviews for PR {pr_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving reviews: {str(e)}")
