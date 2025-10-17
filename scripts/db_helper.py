#!/usr/bin/env python3
"""Database helper script for development, testing, and maintenance.

This script provides utilities to:
- Create/initialize the database
- Clean/reset the database
- Seed test data
- Show database statistics
- Backup/restore database
"""

import argparse
import asyncio
import logging
import os
import shutil
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path


# Add src to path to import application modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from ai_code_reviewer.core.config import Config
from ai_code_reviewer.db.database import close_db, engine, init_db
from ai_code_reviewer.db.models import Base, ReviewFailureLog, ReviewRecord
from ai_code_reviewer.db.repository import FailureLogRepository, ReviewRepository


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def create_database():
    """Create and initialize the database."""
    try:
        logger.info("Creating database tables...")
        await init_db()
        logger.info("✅ Database created successfully")
        await show_stats()
    except Exception as e:
        logger.error(f"❌ Error creating database: {e}")
        raise


async def drop_database():
    """Drop all database tables."""
    try:
        logger.info("Dropping all database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("✅ All tables dropped successfully")
    except Exception as e:
        logger.error(f"❌ Error dropping database: {e}")
        raise


async def reset_database():
    """Reset the database (drop and recreate all tables)."""
    try:
        logger.info("Resetting database...")
        await drop_database()
        await create_database()
        logger.info("✅ Database reset complete")
    except Exception as e:
        logger.error(f"❌ Error resetting database: {e}")
        raise


async def clean_database():
    """Remove all data from tables without dropping the schema."""
    try:
        logger.info("Cleaning database (removing all records)...")
        async with AsyncSession(engine) as session:
            await session.execute(delete(ReviewFailureLog))
            await session.execute(delete(ReviewRecord))
            await session.commit()
        logger.info("✅ All records deleted")
        await show_stats()
    except Exception as e:
        logger.error(f"❌ Error cleaning database: {e}")
        raise


async def show_stats():
    """Show database statistics."""
    try:
        async with AsyncSession(engine) as session:
            review_repo = ReviewRepository(session)
            failure_repo = FailureLogRepository(session)

            total_reviews = await review_repo.count_total_reviews()
            total_failures = await failure_repo.count_total_failures(unresolved_only=False)
            unresolved_failures = await failure_repo.count_total_failures(unresolved_only=True)

            logger.info("\n" + "=" * 60)
            logger.info("📊 Database Statistics")
            logger.info("=" * 60)
            logger.info(f"Total review records: {total_reviews}")
            logger.info(f"Total failure logs: {total_failures}")
            logger.info(f"  - Unresolved: {unresolved_failures}")
            logger.info(f"  - Resolved: {total_failures - unresolved_failures}")

            if total_reviews > 0:
                # Get latest reviews
                latest = await review_repo.get_latest_reviews(limit=5)
                logger.info(f"\nLatest reviews ({len(latest)}):")
                for record in latest:
                    logger.info(
                        f"  - ID {record.id}: {record.review_type} {record.trigger_type} "
                        f"({record.project_key}/{record.repo_slug}) at {record.created_at}"
                    )

            if unresolved_failures > 0:
                # Get latest unresolved failures
                latest_failures = await failure_repo.get_unresolved_failures(limit=5)
                logger.info(f"\nLatest unresolved failures ({len(latest_failures)}):")
                for failure in latest_failures:
                    logger.info(
                        f"  - ID {failure.id}: {failure.failure_stage} - {failure.error_type} at {failure.created_at}"
                    )

            logger.info("=" * 60)
    except Exception as e:
        logger.error(f"❌ Error showing stats: {e}")
        raise


async def seed_test_data():
    """Seed the database with test data for development."""
    try:
        logger.info("Seeding test data...")

        test_records = [
            {
                "review_type": "auto",
                "trigger_type": "commit",
                "project_key": "TEST",
                "repo_slug": "test-repo",
                "commit_id": "abc123def456",
                "author_name": "John Doe",
                "author_email": "john.doe@example.com",
                "diff_content": "diff --git a/test.py b/test.py\n+print('Hello World')",
                "review_feedback": "Code looks good. No issues found.",
                "email_recipients": {"to": ["john.doe@example.com"]},
                "email_sent": True,
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
            },
            {
                "review_type": "manual",
                "trigger_type": "pull_request",
                "project_key": "TEST",
                "repo_slug": "test-repo",
                "pr_id": 42,
                "author_name": "Jane Smith",
                "author_email": "jane.smith@example.com",
                "diff_content": "diff --git a/main.py b/main.py\n+def hello():\n+    return 'world'",
                "review_feedback": "Consider adding docstrings to the new function.",
                "email_recipients": {"to": ["jane.smith@example.com"]},
                "email_sent": True,
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
            },
            {
                "review_type": "auto",
                "trigger_type": "commit",
                "project_key": "PROJ",
                "repo_slug": "my-service",
                "commit_id": "789xyz123abc",
                "author_name": "Bob Developer",
                "author_email": "bob@example.com",
                "diff_content": "diff --git a/api.py b/api.py\n+async def get_data():\n+    return data",
                "review_feedback": "Security: Consider input validation for the data parameter.",
                "email_recipients": {"to": ["bob@example.com"]},
                "email_sent": True,
                "llm_provider": "local_ollama",
                "llm_model": "qwen-coder",
            },
            {
                "review_type": "manual",
                "trigger_type": "diff_upload",
                "project_key": "MANUAL",
                "repo_slug": "diff-upload",
                "commit_id": None,
                "pr_id": None,
                "author_name": "Alice Developer",
                "author_email": "alice@example.com",
                "diff_content": "# Description: Local changes for review\n\ndiff --git a/utils.py b/utils.py\n+def validate_input(data):\n+    if not data:\n+        raise ValueError('Empty data')\n+    return True",
                "review_feedback": "Good: Added input validation. Consider also checking data type.",
                "email_recipients": None,
                "email_sent": False,
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
            },
        ]

        async with AsyncSession(engine) as session:
            for i, data in enumerate(test_records, 1):
                # Create with staggered timestamps
                record = ReviewRecord(**data)
                record.created_at = datetime.now(UTC) - timedelta(hours=48 - (i * 10))
                session.add(record)

            await session.commit()

        logger.info(f"✅ Seeded {len(test_records)} test records (including diff_upload example)")
        await show_stats()
    except Exception as e:
        logger.error(f"❌ Error seeding test data: {e}")
        raise


async def backup_database(backup_path: str | None = None):
    """Backup the database file (SQLite only)."""
    if "sqlite" not in Config.DATABASE_URL.lower():
        logger.error("❌ Backup is only supported for SQLite databases")
        return

    try:
        # Extract database file path from URL
        db_file = Config.DATABASE_URL.split("///")[-1]

        if not os.path.exists(db_file):
            logger.error(f"❌ Database file not found: {db_file}")
            return

        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{db_file}.backup_{timestamp}"

        logger.info(f"Backing up database to {backup_path}...")
        shutil.copy2(db_file, backup_path)
        logger.info(f"✅ Database backed up successfully to {backup_path}")
    except Exception as e:
        logger.error(f"❌ Error backing up database: {e}")
        raise


async def restore_database(backup_path: str):
    """Restore the database from a backup file (SQLite only)."""
    if "sqlite" not in Config.DATABASE_URL.lower():
        logger.error("❌ Restore is only supported for SQLite databases")
        return

    try:
        if not os.path.exists(backup_path):
            logger.error(f"❌ Backup file not found: {backup_path}")
            return

        # Extract database file path from URL
        db_file = Config.DATABASE_URL.split("///")[-1]

        logger.info(f"Restoring database from {backup_path}...")
        shutil.copy2(backup_path, db_file)
        logger.info(f"✅ Database restored successfully from {backup_path}")
        await show_stats()
    except Exception as e:
        logger.error(f"❌ Error restoring database: {e}")
        raise


async def list_reviews(limit: int = 10):
    """List recent reviews."""
    try:
        async with AsyncSession(engine) as session:
            repo = ReviewRepository(session)
            reviews = await repo.get_latest_reviews(limit=limit)

            logger.info(f"\n📋 Latest {limit} reviews:")
            logger.info("=" * 100)
            for record in reviews:
                logger.info(
                    f"ID: {record.id:4d} | {record.created_at} | {record.review_type:6s} | "
                    f"{record.trigger_type:13s} | {record.project_key}/{record.repo_slug}"
                )
                if record.commit_id:
                    logger.info(f"  Commit: {record.commit_id[:12]}")
                if record.pr_id:
                    logger.info(f"  PR: #{record.pr_id}")
                logger.info(f"  Author: {record.author_name} <{record.author_email}>")
                logger.info(f"  Email sent: {record.email_sent}")
                logger.info(
                    f"  Review: {record.review_feedback[:80]}{'...' if len(record.review_feedback) > 80 else ''}"
                )
                logger.info("-" * 100)
    except Exception as e:
        logger.error(f"❌ Error listing reviews: {e}")
        raise


async def list_failures(limit: int = 10, unresolved_only: bool = False):
    """List recent failure logs."""
    try:
        async with AsyncSession(engine) as session:
            repo = FailureLogRepository(session)

            if unresolved_only:
                failures = await repo.get_unresolved_failures(limit=limit)
                logger.info(f"\n❌ Latest {limit} unresolved failures:")
            else:
                failures = await repo.get_latest_failures(limit=limit)
                logger.info(f"\n❌ Latest {limit} failures:")

            logger.info("=" * 100)
            for failure in failures:
                status = "❌ UNRESOLVED" if not failure.resolved else "✅ RESOLVED"
                logger.info(
                    f"ID: {failure.id:4d} | {failure.created_at} | {status} | "
                    f"{failure.event_type:8s} | {failure.failure_stage}"
                )
                logger.info(f"  Error: {failure.error_type} - {failure.error_message[:100]}")
                if failure.project_key:
                    location = f"{failure.project_key}/{failure.repo_slug}"
                    if failure.commit_id:
                        location += f" (commit: {failure.commit_id[:12]})"
                    if failure.pr_id:
                        location += f" (PR #{failure.pr_id})"
                    logger.info(f"  Location: {location}")
                if failure.author_email:
                    logger.info(f"  Author: {failure.author_name} <{failure.author_email}>")
                if failure.retry_count > 0:
                    logger.info(f"  Retries: {failure.retry_count}")
                if failure.resolved and failure.resolution_notes:
                    logger.info(f"  Resolution: {failure.resolution_notes[:100]}")
                logger.info("-" * 100)
    except Exception as e:
        logger.error(f"❌ Error listing failures: {e}")
        raise


async def show_failure_details(failure_id: int):
    """Show detailed information about a specific failure log."""
    try:
        async with AsyncSession(engine) as session:
            repo = FailureLogRepository(session)
            failure = await repo.get_failure_by_id(failure_id)

            if not failure:
                logger.error(f"❌ Failure log {failure_id} not found")
                return

            logger.info(f"\n🔍 Failure Log Details (ID: {failure_id})")
            logger.info("=" * 100)
            logger.info(f"Created: {failure.created_at}")
            logger.info(f"Event Type: {failure.event_type}")
            logger.info(f"Event Key: {failure.event_key}")
            logger.info(f"Failure Stage: {failure.failure_stage}")
            logger.info(f"Error Type: {failure.error_type}")
            logger.info(f"Error Message: {failure.error_message}")

            if failure.project_key:
                logger.info(f"\nRepository: {failure.project_key}/{failure.repo_slug}")
            if failure.commit_id:
                logger.info(f"Commit: {failure.commit_id}")
            if failure.pr_id:
                logger.info(f"PR: #{failure.pr_id}")
            if failure.author_email:
                logger.info(f"Author: {failure.author_name} <{failure.author_email}>")

            logger.info(f"\nRetry Count: {failure.retry_count}")
            logger.info(f"Resolved: {'Yes' if failure.resolved else 'No'}")
            if failure.resolved and failure.resolution_notes:
                logger.info(f"Resolution Notes: {failure.resolution_notes}")

            if failure.error_stacktrace:
                logger.info(f"\nStacktrace:\n{failure.error_stacktrace}")

            if failure.request_payload:
                import json

                logger.info(f"\nRequest Payload:\n{json.dumps(failure.request_payload, indent=2)}")

            logger.info("=" * 100)
    except Exception as e:
        logger.error(f"❌ Error showing failure details: {e}")
        raise


async def resolve_failure(failure_id: int, notes: str | None = None):
    """Mark a failure log as resolved."""
    try:
        async with AsyncSession(engine) as session:
            repo = FailureLogRepository(session)
            await repo.mark_failure_resolved(failure_id, notes)
            logger.info(f"✅ Failure log {failure_id} marked as resolved")
            if notes:
                logger.info(f"   Resolution notes: {notes}")
    except Exception as e:
        logger.error(f"❌ Error resolving failure {failure_id}: {e}")
        raise


async def main():
    """Main entry point for the database helper script."""
    parser = argparse.ArgumentParser(
        description="Database helper for AI Code Reviewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create/initialize database
  python scripts/db_helper.py create

  # Reset database (drop and recreate)
  python scripts/db_helper.py reset

  # Clean all records
  python scripts/db_helper.py clean

  # Show statistics
  python scripts/db_helper.py stats

  # Seed test data
  python scripts/db_helper.py seed

  # List recent reviews
  python scripts/db_helper.py list --limit 20

  # List recent failure logs
  python scripts/db_helper.py failures --limit 20

  # List only unresolved failures
  python scripts/db_helper.py failures --unresolved-only

  # Show detailed failure log
  python scripts/db_helper.py failure 123

  # Mark failure as resolved
  python scripts/db_helper.py resolve 123 --notes "Fixed by restarting LLM service"

  # Backup database
  python scripts/db_helper.py backup

  # Restore from backup
  python scripts/db_helper.py restore --file backup.db
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create command
    subparsers.add_parser("create", help="Create and initialize database tables")

    # Reset command
    subparsers.add_parser("reset", help="Drop and recreate all database tables")

    # Clean command
    subparsers.add_parser("clean", help="Remove all records from database")

    # Stats command
    subparsers.add_parser("stats", help="Show database statistics")

    # Seed command
    subparsers.add_parser("seed", help="Seed database with test data")

    # List command
    list_parser = subparsers.add_parser("list", help="List recent reviews")
    list_parser.add_argument("--limit", type=int, default=10, help="Number of reviews to show (default: 10)")

    # List failures command
    failures_parser = subparsers.add_parser("failures", help="List recent failure logs")
    failures_parser.add_argument("--limit", type=int, default=10, help="Number of failures to show (default: 10)")
    failures_parser.add_argument("--unresolved-only", action="store_true", help="Show only unresolved failures")

    # Show failure details command
    show_failure_parser = subparsers.add_parser("failure", help="Show detailed information about a failure log")
    show_failure_parser.add_argument("id", type=int, help="Failure log ID")

    # Resolve failure command
    resolve_parser = subparsers.add_parser("resolve", help="Mark a failure log as resolved")
    resolve_parser.add_argument("id", type=int, help="Failure log ID")
    resolve_parser.add_argument("--notes", type=str, help="Resolution notes")

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Backup database (SQLite only)")
    backup_parser.add_argument("--file", type=str, help="Backup file path (default: auto-generated)")

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore database from backup (SQLite only)")
    restore_parser.add_argument("--file", type=str, required=True, help="Backup file path to restore from")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        logger.info(f"Database URL: {Config.DATABASE_URL}\n")

        if args.command == "create":
            await create_database()
        elif args.command == "reset":
            await reset_database()
        elif args.command == "clean":
            await clean_database()
        elif args.command == "stats":
            await show_stats()
        elif args.command == "seed":
            await seed_test_data()
        elif args.command == "list":
            await list_reviews(limit=args.limit)
        elif args.command == "failures":
            await list_failures(limit=args.limit, unresolved_only=args.unresolved_only)
        elif args.command == "failure":
            await show_failure_details(args.id)
        elif args.command == "resolve":
            await resolve_failure(args.id, args.notes)
        elif args.command == "backup":
            await backup_database(args.file)
        elif args.command == "restore":
            await restore_database(args.file)

    except Exception as e:
        logger.error(f"\n❌ Operation failed: {e}")
        sys.exit(1)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
