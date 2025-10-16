"""Failure log retrieval endpoints."""

import logging

from fastapi import APIRouter, HTTPException

from ai_code_reviewer.db.database import get_db_session
from ai_code_reviewer.db.repository import FailureLogRepository


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/failures/latest")
async def get_latest_failures(limit: int = 50):
    """Get the latest failure logs.

    Args:
        limit: Maximum number of failures to return (default: 50, max: 100)

    Returns:
        List of failure log records
    """
    try:
        if limit > 100:
            limit = 100

        async with get_db_session() as session:
            repo = FailureLogRepository(session)
            failures = await repo.get_latest_failures(limit=limit)

            return {
                "count": len(failures),
                "failures": [
                    {
                        "id": f.id,
                        "created_at": f.created_at.isoformat(),
                        "event_type": f.event_type,
                        "event_key": f.event_key,
                        "failure_stage": f.failure_stage,
                        "error_type": f.error_type,
                        "error_message": f.error_message,
                        "project_key": f.project_key,
                        "repo_slug": f.repo_slug,
                        "commit_id": f.commit_id,
                        "pr_id": f.pr_id,
                        "author_name": f.author_name,
                        "author_email": f.author_email,
                        "retry_count": f.retry_count,
                        "resolved": f.resolved,
                        "resolution_notes": f.resolution_notes,
                    }
                    for f in failures
                ],
            }
    except Exception as e:
        logger.error(f"Error fetching latest failures: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/failures/stats")
async def get_failure_stats():
    """Get failure statistics including counts by stage.

    Returns:
        Statistics about failure logs
    """
    try:
        async with get_db_session() as session:
            repo = FailureLogRepository(session)
            total_failures = await repo.count_total_failures(unresolved_only=False)
            unresolved_failures = await repo.count_total_failures(unresolved_only=True)
            by_stage = await repo.count_failures_by_stage()

            return {
                "total_failures": total_failures,
                "unresolved_failures": unresolved_failures,
                "resolved_failures": total_failures - unresolved_failures,
                "by_stage": by_stage,
            }
    except Exception as e:
        logger.error(f"Error fetching failure stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/failures")
async def get_failures_paginated(offset: int = 0, limit: int = 10):
    """Get failure logs with pagination.

    Args:
        offset: Number of records to skip (default: 0)
        limit: Maximum number of failures to return (default: 10, max: 100)

    Returns:
        Paginated list of failure log records
    """
    try:
        if limit > 100:
            limit = 100

        async with get_db_session() as session:
            repo = FailureLogRepository(session)
            failures = await repo.get_failures_paginated(offset=offset, limit=limit)
            total = await repo.count_total_failures(unresolved_only=False)

            return {
                "total": total,
                "offset": offset,
                "limit": limit,
                "count": len(failures),
                "failures": [
                    {
                        "id": f.id,
                        "created_at": f.created_at.isoformat(),
                        "event_type": f.event_type,
                        "event_key": f.event_key,
                        "failure_stage": f.failure_stage,
                        "error_type": f.error_type,
                        "error_message": f.error_message,
                        "project_key": f.project_key,
                        "repo_slug": f.repo_slug,
                        "commit_id": f.commit_id,
                        "pr_id": f.pr_id,
                        "author_name": f.author_name,
                        "author_email": f.author_email,
                        "retry_count": f.retry_count,
                        "resolved": f.resolved,
                    }
                    for f in failures
                ],
            }
    except Exception as e:
        logger.error(f"Error fetching paginated failures: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/failures/{failure_id}")
async def get_failure_by_id(failure_id: int):
    """Get a specific failure log by ID with full details including stacktrace.

    Args:
        failure_id: The failure log ID

    Returns:
        Complete failure log record
    """
    try:
        async with get_db_session() as session:
            repo = FailureLogRepository(session)
            failure = await repo.get_failure_by_id(failure_id)

            if not failure:
                raise HTTPException(status_code=404, detail=f"Failure log {failure_id} not found")

            return {
                "id": failure.id,
                "created_at": failure.created_at.isoformat(),
                "event_type": failure.event_type,
                "event_key": failure.event_key,
                "request_payload": failure.request_payload,
                "project_key": failure.project_key,
                "repo_slug": failure.repo_slug,
                "commit_id": failure.commit_id,
                "pr_id": failure.pr_id,
                "author_name": failure.author_name,
                "author_email": failure.author_email,
                "failure_stage": failure.failure_stage,
                "error_type": failure.error_type,
                "error_message": failure.error_message,
                "error_stacktrace": failure.error_stacktrace,
                "retry_count": failure.retry_count,
                "resolved": failure.resolved,
                "resolution_notes": failure.resolution_notes,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching failure {failure_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
