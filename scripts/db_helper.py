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
from datetime import datetime, timedelta
from pathlib import Path


# Add src to path to import application modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from ai_code_reviewer.core.config import Config
from ai_code_reviewer.db.database import close_db, engine, init_db
from ai_code_reviewer.db.models import Base, ReviewRecord
from ai_code_reviewer.db.repository import ReviewRepository


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
            repo = ReviewRepository(session)
            total = await repo.count_total_reviews()

            logger.info("\n" + "=" * 50)
            logger.info("📊 Database Statistics")
            logger.info("=" * 50)
            logger.info(f"Total review records: {total}")

            if total > 0:
                # Get latest reviews
                latest = await repo.get_latest_reviews(limit=5)
                logger.info(f"\nLatest reviews ({len(latest)}):")
                for record in latest:
                    logger.info(
                        f"  - ID {record.id}: {record.review_type} {record.trigger_type} "
                        f"({record.project_key}/{record.repo_slug}) at {record.created_at}"
                    )
            logger.info("=" * 50)
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
        ]

        async with AsyncSession(engine) as session:
            for i, data in enumerate(test_records, 1):
                # Create with staggered timestamps
                record = ReviewRecord(**data)
                record.created_at = datetime.now(datetime.UTC) - timedelta(hours=24 - i)  # type: ignore
                session.add(record)

            await session.commit()

        logger.info(f"✅ Seeded {len(test_records)} test records")
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
