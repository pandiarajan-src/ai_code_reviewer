"""Repository for managing review records in the database."""

import logging

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_code_reviewer.db.models import ReviewFailureLog, ReviewRecord


logger = logging.getLogger(__name__)


class ReviewRepository:
    """Repository for review record operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create_review_record(
        self,
        review_type: str,
        trigger_type: str,
        project_key: str,
        repo_slug: str,
        diff_content: str,
        review_feedback: str,
        commit_id: str | None = None,
        pr_id: int | None = None,
        author_name: str | None = None,
        author_email: str | None = None,
        email_recipients: list[str] | None = None,
        email_sent: bool = False,
        llm_provider: str | None = None,
        llm_model: str | None = None,
    ) -> ReviewRecord:
        """Create a new review record in the database."""
        try:
            # Convert email_recipients list to JSON-serializable format
            recipients_data = {"to": email_recipients or []} if email_recipients else None

            review_record = ReviewRecord(
                review_type=review_type,
                trigger_type=trigger_type,
                project_key=project_key,
                repo_slug=repo_slug,
                commit_id=commit_id,
                pr_id=pr_id,
                author_name=author_name,
                author_email=author_email,
                diff_content=diff_content,
                review_feedback=review_feedback,
                email_recipients=recipients_data,
                email_sent=email_sent,
                llm_provider=llm_provider,
                llm_model=llm_model,
            )

            self.session.add(review_record)
            await self.session.flush()
            await self.session.refresh(review_record)

            logger.info(f"Created review record with ID: {review_record.id}")
            return review_record

        except Exception as e:
            logger.error(f"Error creating review record: {str(e)}")
            raise

    async def get_review_by_id(self, review_id: int) -> ReviewRecord | None:
        """Get a review record by ID."""
        try:
            result = await self.session.execute(select(ReviewRecord).where(ReviewRecord.id == review_id))
            record: ReviewRecord | None = result.scalar_one_or_none()
            return record
        except Exception as e:
            logger.error(f"Error fetching review record {review_id}: {str(e)}")
            raise

    async def get_latest_reviews(self, limit: int = 10) -> list[ReviewRecord]:
        """Get the latest N review records ordered by creation date."""
        try:
            result = await self.session.execute(
                select(ReviewRecord).order_by(desc(ReviewRecord.created_at)).limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching latest reviews: {str(e)}")
            raise

    async def get_reviews_paginated(self, offset: int = 0, limit: int = 10) -> list[ReviewRecord]:
        """Get review records with pagination (offset and limit)."""
        try:
            result = await self.session.execute(
                select(ReviewRecord).order_by(desc(ReviewRecord.created_at)).offset(offset).limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching paginated reviews: {str(e)}")
            raise

    async def get_reviews_by_project(
        self, project_key: str, repo_slug: str | None = None, limit: int = 10
    ) -> list[ReviewRecord]:
        """Get review records for a specific project/repository."""
        try:
            query = select(ReviewRecord).where(ReviewRecord.project_key == project_key)

            if repo_slug:
                query = query.where(ReviewRecord.repo_slug == repo_slug)

            query = query.order_by(desc(ReviewRecord.created_at)).limit(limit)

            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching reviews for project {project_key}: {str(e)}")
            raise

    async def get_reviews_by_author(self, author_email: str, limit: int = 10) -> list[ReviewRecord]:
        """Get review records for a specific author."""
        try:
            result = await self.session.execute(
                select(ReviewRecord)
                .where(ReviewRecord.author_email == author_email)
                .order_by(desc(ReviewRecord.created_at))
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching reviews for author {author_email}: {str(e)}")
            raise

    async def get_reviews_by_commit(self, commit_id: str) -> list[ReviewRecord]:
        """Get review records for a specific commit."""
        try:
            result = await self.session.execute(
                select(ReviewRecord).where(ReviewRecord.commit_id == commit_id).order_by(desc(ReviewRecord.created_at))
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching reviews for commit {commit_id}: {str(e)}")
            raise

    async def get_reviews_by_pr(self, pr_id: int) -> list[ReviewRecord]:
        """Get review records for a specific pull request."""
        try:
            result = await self.session.execute(
                select(ReviewRecord).where(ReviewRecord.pr_id == pr_id).order_by(desc(ReviewRecord.created_at))
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching reviews for PR {pr_id}: {str(e)}")
            raise

    async def count_total_reviews(self) -> int:
        """Get total count of review records."""
        try:
            result = await self.session.execute(select(func.count(ReviewRecord.id)))
            count: int = result.scalar_one()
            return count
        except Exception as e:
            logger.error(f"Error counting reviews: {str(e)}")
            raise


class FailureLogRepository:
    """Repository for failure log operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create_failure_log(
        self,
        event_type: str,
        failure_stage: str,
        error_type: str,
        error_message: str,
        event_key: str | None = None,
        request_payload: dict | None = None,
        project_key: str | None = None,
        repo_slug: str | None = None,
        commit_id: str | None = None,
        pr_id: int | None = None,
        author_name: str | None = None,
        author_email: str | None = None,
        error_stacktrace: str | None = None,
        retry_count: int = 0,
    ) -> ReviewFailureLog:
        """Create a new failure log record in the database."""
        try:
            failure_log = ReviewFailureLog(
                event_type=event_type,
                event_key=event_key,
                request_payload=request_payload,
                project_key=project_key,
                repo_slug=repo_slug,
                commit_id=commit_id,
                pr_id=pr_id,
                author_name=author_name,
                author_email=author_email,
                failure_stage=failure_stage,
                error_type=error_type,
                error_message=error_message,
                error_stacktrace=error_stacktrace,
                retry_count=retry_count,
                resolved=False,
            )

            self.session.add(failure_log)
            await self.session.flush()
            await self.session.refresh(failure_log)

            logger.info(f"Created failure log with ID: {failure_log.id}")
            return failure_log

        except Exception as e:
            logger.error(f"Error creating failure log: {str(e)}")
            raise

    async def get_failure_by_id(self, failure_id: int) -> ReviewFailureLog | None:
        """Get a failure log by ID."""
        try:
            result = await self.session.execute(select(ReviewFailureLog).where(ReviewFailureLog.id == failure_id))
            record: ReviewFailureLog | None = result.scalar_one_or_none()
            return record
        except Exception as e:
            logger.error(f"Error fetching failure log {failure_id}: {str(e)}")
            raise

    async def get_unresolved_failures(self, limit: int = 50) -> list[ReviewFailureLog]:
        """Get unresolved failure logs ordered by creation date."""
        try:
            result = await self.session.execute(
                select(ReviewFailureLog)
                .where(ReviewFailureLog.resolved == False)  # noqa: E712
                .order_by(desc(ReviewFailureLog.created_at))
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching unresolved failures: {str(e)}")
            raise

    async def get_failures_by_stage(self, failure_stage: str, limit: int = 50) -> list[ReviewFailureLog]:
        """Get failure logs for a specific failure stage."""
        try:
            result = await self.session.execute(
                select(ReviewFailureLog)
                .where(ReviewFailureLog.failure_stage == failure_stage)
                .order_by(desc(ReviewFailureLog.created_at))
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching failures for stage {failure_stage}: {str(e)}")
            raise

    async def get_failures_by_project(
        self, project_key: str, repo_slug: str | None = None, limit: int = 50
    ) -> list[ReviewFailureLog]:
        """Get failure logs for a specific project/repository."""
        try:
            query = select(ReviewFailureLog).where(ReviewFailureLog.project_key == project_key)

            if repo_slug:
                query = query.where(ReviewFailureLog.repo_slug == repo_slug)

            query = query.order_by(desc(ReviewFailureLog.created_at)).limit(limit)

            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching failures for project {project_key}: {str(e)}")
            raise

    async def get_latest_failures(self, limit: int = 50) -> list[ReviewFailureLog]:
        """Get the latest N failure logs ordered by creation date."""
        try:
            result = await self.session.execute(
                select(ReviewFailureLog).order_by(desc(ReviewFailureLog.created_at)).limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching latest failures: {str(e)}")
            raise

    async def get_failures_paginated(self, offset: int = 0, limit: int = 10) -> list[ReviewFailureLog]:
        """Get failure logs with pagination (offset and limit)."""
        try:
            result = await self.session.execute(
                select(ReviewFailureLog).order_by(desc(ReviewFailureLog.created_at)).offset(offset).limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching paginated failures: {str(e)}")
            raise

    async def mark_failure_resolved(self, failure_id: int, resolution_notes: str | None = None) -> ReviewFailureLog:
        """Mark a failure log as resolved with optional notes."""
        try:
            result = await self.session.execute(select(ReviewFailureLog).where(ReviewFailureLog.id == failure_id))
            failure_log = result.scalar_one()

            failure_log.resolved = True
            failure_log.resolution_notes = resolution_notes

            await self.session.flush()
            await self.session.refresh(failure_log)

            logger.info(f"Marked failure log {failure_id} as resolved")
            return failure_log

        except Exception as e:
            logger.error(f"Error marking failure {failure_id} as resolved: {str(e)}")
            raise

    async def count_failures_by_stage(self) -> dict[str, int]:
        """Get count of failures grouped by stage."""
        try:
            result = await self.session.execute(
                select(ReviewFailureLog.failure_stage, func.count(ReviewFailureLog.id))
                .group_by(ReviewFailureLog.failure_stage)
                .order_by(desc(func.count(ReviewFailureLog.id)))
            )
            return {row[0]: row[1] for row in result.all()}
        except Exception as e:
            logger.error(f"Error counting failures by stage: {str(e)}")
            raise

    async def count_total_failures(self, unresolved_only: bool = False) -> int:
        """Get total count of failure logs."""
        try:
            query = select(func.count(ReviewFailureLog.id))
            if unresolved_only:
                query = query.where(ReviewFailureLog.resolved == False)  # noqa: E712

            result = await self.session.execute(query)
            count: int = result.scalar_one()
            return count
        except Exception as e:
            logger.error(f"Error counting failures: {str(e)}")
            raise


# Import func for count query
from sqlalchemy import func  # noqa: E402
