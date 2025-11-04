"""Database models for storing review records."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class ReviewRecord(Base):
    """Model for storing code review records."""

    __tablename__ = "review_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Review metadata
    review_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "auto" or "manual"
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "commit" or "pull_request"

    # Repository information
    project_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    repo_slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Commit/PR information
    commit_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    pr_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    # Author information
    author_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # Review content
    diff_content: Mapped[str] = mapped_column(Text, nullable=False)
    review_feedback: Mapped[str] = mapped_column(Text, nullable=False)

    # Email information (stored as JSON array of email addresses)
    email_recipients: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    email_sent: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Additional metadata
    llm_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        """String representation of the review record."""
        return (
            f"<ReviewRecord(id={self.id}, type={self.review_type}, "
            f"trigger={self.trigger_type}, commit={self.commit_id}, pr={self.pr_id})>"
        )


class ReviewFailureLog(Base):
    """Model for logging failed review attempts for audit and troubleshooting."""

    __tablename__ = "review_failure_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Request context - how the review was triggered
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "webhook" or "manual"
    event_key: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # e.g., "pr:opened", "repo:refs_changed", "manual_review"
    request_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Full request payload for debugging

    # Repository and target information
    project_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    repo_slug: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    commit_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    pr_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    # Author information (if available before failure)
    author_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # Failure details
    failure_stage: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # Where it failed in the pipeline
    error_type: Mapped[str] = mapped_column(String(255), nullable=False)  # Exception class name
    error_message: Mapped[str] = mapped_column(Text, nullable=False)  # Human-readable error message
    error_stacktrace: Mapped[str | None] = mapped_column(Text, nullable=True)  # Full traceback for debugging

    # Audit and resolution tracking
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Number of retry attempts
    resolved: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)  # Whether issue was resolved
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # Admin notes on resolution

    def __repr__(self) -> str:
        """String representation of the failure log."""
        return (
            f"<ReviewFailureLog(id={self.id}, stage={self.failure_stage}, "
            f"error={self.error_type}, resolved={self.resolved})>"
        )
