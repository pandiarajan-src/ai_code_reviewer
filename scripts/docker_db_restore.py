#!/usr/bin/env python3
"""Docker database restore script.

This script restores a SQLite database backup to a Docker container.
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run_command(command: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(  # noqa: S603
            command,
            capture_output=True,
            text=True,
            check=check,
        )
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(command)}")
        logger.error(f"Error: {e.stderr}")
        raise


def get_container_name(compose_file: str = "docker/docker-compose.yml") -> str:
    """Get the container name from docker-compose."""
    logger.info("Finding container name...")
    result = run_command(["docker-compose", "-f", compose_file, "ps", "-q", "ai-code-reviewer"])

    container_id = result.stdout.strip()
    if not container_id:
        raise RuntimeError("Container 'ai-code-reviewer' is not running")

    # Get full container name
    result = run_command(["docker", "inspect", "--format", "{{.Name}}", container_id])

    container_name = result.stdout.strip().lstrip("/")
    logger.info(f"Found container: {container_name}")
    return container_name


def restore_database(
    backup_file: str, container_name: str, db_path: str = "/app/data/ai_code_reviewer.db", create_backup: bool = True
) -> None:
    """Restore database from backup file to Docker container.

    Args:
        backup_file: Path to backup file on host
        container_name: Docker container name
        db_path: Path to database inside container
        create_backup: Create backup of current database before restore
    """
    backup_path = Path(backup_file)

    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_file}")

    file_size = backup_path.stat().st_size
    if file_size == 0:
        raise ValueError(f"Backup file is empty: {backup_file}")

    logger.info(f"Restoring database to container '{container_name}'...")
    logger.info(f"Source: {backup_file} ({file_size:,} bytes)")
    logger.info(f"Destination: {db_path}")

    # Create backup of current database if requested
    if create_backup:
        logger.info("\n📦 Creating backup of current database before restore...")
        try:
            import docker_db_backup

            current_backup = docker_db_backup.backup_database(
                container_name=container_name, backup_dir="./backups/pre_restore", db_path=db_path
            )
            logger.info(f"✅ Current database backed up to: {current_backup}")
        except Exception as e:
            logger.warning(f"⚠️  Could not backup current database: {e}")
            response = input("\nContinue with restore anyway? [y/N]: ")
            if response.lower() != "y":
                logger.info("Restore cancelled")
                return

    # Stop the application to ensure clean restore
    logger.info("\n🛑 Stopping application container...")
    run_command(["docker-compose", "-f", "docker/docker-compose.yml", "stop", "ai-code-reviewer"])

    try:
        # Copy backup file to container
        logger.info("📥 Copying backup file to container...")
        run_command(["docker", "cp", str(backup_path), f"{container_name}:{db_path}"])

        # Set proper permissions
        logger.info("🔐 Setting file permissions...")
        run_command(["docker", "exec", container_name, "chown", "app:app", db_path])

        logger.info("✅ Database restored successfully!")

    finally:
        # Restart the container
        logger.info("\n🚀 Starting application container...")
        run_command(["docker-compose", "-f", "docker/docker-compose.yml", "start", "ai-code-reviewer"])

    logger.info("\n✅ Restore complete! Container is running.")
    logger.info("💡 Use 'python scripts/db_helper.py stats' to verify the data")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Restore SQLite database to Docker container",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Restore from backup file
  python scripts/docker_db_restore.py restore --file ./backups/ai_code_reviewer_20250106_120000.db

  # Restore without creating pre-restore backup
  python scripts/docker_db_restore.py restore --file backup.db --no-backup

  # Restore to specific container
  python scripts/docker_db_restore.py restore --file backup.db --container my-container
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore database to container")
    restore_parser.add_argument("--file", type=str, required=True, help="Backup file path to restore from")
    restore_parser.add_argument("--container", type=str, help="Container name (auto-detected if not specified)")
    restore_parser.add_argument(
        "--db-path",
        type=str,
        default="/app/data/ai_code_reviewer.db",
        help="Database path inside container (default: /app/data/ai_code_reviewer.db)",
    )
    restore_parser.add_argument(
        "--no-backup", action="store_true", help="Skip backup of current database before restore"
    )
    restore_parser.add_argument(
        "--compose-file",
        type=str,
        default="docker/docker-compose.yml",
        help="Docker compose file path (default: docker/docker-compose.yml)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "restore":
            # Auto-detect container name if not provided
            container = args.container
            if not container:
                container = get_container_name(args.compose_file)

            restore_database(
                backup_file=args.file, container_name=container, db_path=args.db_path, create_backup=not args.no_backup
            )

    except Exception as e:
        logger.error(f"\n❌ Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
