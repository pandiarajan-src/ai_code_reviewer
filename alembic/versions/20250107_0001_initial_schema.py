"""Initial schema with review_records and review_failure_logs tables.

Revision ID: 20250107_0001
Revises:
Create Date: 2025-01-07 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20250107_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create initial schema with review_records and review_failure_logs tables."""
    # Create review_records table
    op.create_table(
        "review_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("review_type", sa.String(length=50), nullable=False),
        sa.Column("trigger_type", sa.String(length=50), nullable=False),
        sa.Column("project_key", sa.String(length=255), nullable=False),
        sa.Column("repo_slug", sa.String(length=255), nullable=False),
        sa.Column("commit_id", sa.String(length=255), nullable=True),
        sa.Column("pr_id", sa.Integer(), nullable=True),
        sa.Column("author_name", sa.String(length=255), nullable=True),
        sa.Column("author_email", sa.String(length=255), nullable=True),
        sa.Column("diff_content", sa.Text(), nullable=False),
        sa.Column("review_feedback", sa.Text(), nullable=False),
        sa.Column("email_recipients", sa.JSON(), nullable=True),
        sa.Column("email_sent", sa.Boolean(), nullable=False, default=False),
        sa.Column("llm_provider", sa.String(length=50), nullable=True),
        sa.Column("llm_model", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for review_records
    with op.batch_alter_table("review_records", schema=None) as batch_op:
        batch_op.create_index("ix_review_records_project_key", ["project_key"], unique=False)
        batch_op.create_index("ix_review_records_repo_slug", ["repo_slug"], unique=False)
        batch_op.create_index("ix_review_records_commit_id", ["commit_id"], unique=False)
        batch_op.create_index("ix_review_records_pr_id", ["pr_id"], unique=False)
        batch_op.create_index("ix_review_records_author_email", ["author_email"], unique=False)

    # Create review_failure_logs table
    op.create_table(
        "review_failure_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("event_key", sa.String(length=100), nullable=True),
        sa.Column("request_payload", sa.JSON(), nullable=True),
        sa.Column("project_key", sa.String(length=255), nullable=True),
        sa.Column("repo_slug", sa.String(length=255), nullable=True),
        sa.Column("commit_id", sa.String(length=255), nullable=True),
        sa.Column("pr_id", sa.Integer(), nullable=True),
        sa.Column("author_name", sa.String(length=255), nullable=True),
        sa.Column("author_email", sa.String(length=255), nullable=True),
        sa.Column("failure_stage", sa.String(length=100), nullable=False),
        sa.Column("error_type", sa.String(length=255), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("error_stacktrace", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, default=0),
        sa.Column("resolved", sa.Boolean(), nullable=False, default=False),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for review_failure_logs
    with op.batch_alter_table("review_failure_logs", schema=None) as batch_op:
        batch_op.create_index("ix_review_failure_logs_event_type", ["event_type"], unique=False)
        batch_op.create_index("ix_review_failure_logs_project_key", ["project_key"], unique=False)
        batch_op.create_index("ix_review_failure_logs_repo_slug", ["repo_slug"], unique=False)
        batch_op.create_index("ix_review_failure_logs_commit_id", ["commit_id"], unique=False)
        batch_op.create_index("ix_review_failure_logs_pr_id", ["pr_id"], unique=False)
        batch_op.create_index("ix_review_failure_logs_author_email", ["author_email"], unique=False)
        batch_op.create_index("ix_review_failure_logs_failure_stage", ["failure_stage"], unique=False)
        batch_op.create_index("ix_review_failure_logs_resolved", ["resolved"], unique=False)


def downgrade() -> None:
    """Drop all tables (rollback to empty database)."""
    op.drop_table("review_failure_logs")
    op.drop_table("review_records")
