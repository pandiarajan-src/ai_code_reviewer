#!/usr/bin/env python3
"""Docker database backup script.

This script backs up the SQLite database from a running Docker container
to the host machine.
"""

import argparse
import logging
import subprocess
import sys
from datetime import datetime
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


def backup_database(
    container_name: str, backup_dir: str = "./backups", db_path: str = "/app/data/ai_code_reviewer.db"
) -> str:
    """Backup database from Docker container to host.

    Args:
        container_name: Docker container name
        backup_dir: Directory to store backups on host
        db_path: Path to database inside container

    Returns:
        Path to the backup file
    """
    # Create backup directory
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_path / f"ai_code_reviewer_{timestamp}.db"

    logger.info(f"Backing up database from container '{container_name}'...")
    logger.info(f"Source: {db_path}")
    logger.info(f"Destination: {backup_file}")

    # Copy database from container to host
    run_command(["docker", "cp", f"{container_name}:{db_path}", str(backup_file)])

    # Verify backup file exists and has content
    if not backup_file.exists():
        raise RuntimeError(f"Backup file not created: {backup_file}")

    file_size = backup_file.stat().st_size
    if file_size == 0:
        raise RuntimeError(f"Backup file is empty: {backup_file}")

    logger.info("✅ Backup successful!")
    logger.info(f"   File: {backup_file}")
    logger.info(f"   Size: {file_size:,} bytes")

    return str(backup_file)


def list_backups(backup_dir: str = "./backups") -> list[Path]:
    """List all database backups."""
    backup_path = Path(backup_dir)
    if not backup_path.exists():
        logger.info(f"No backup directory found: {backup_dir}")
        return []

    backups = sorted(backup_path.glob("ai_code_reviewer_*.db"), reverse=True)

    if not backups:
        logger.info(f"No backups found in {backup_dir}")
        return []

    logger.info(f"\n📦 Available backups in {backup_dir}:")
    logger.info("=" * 80)
    for backup in backups:
        size = backup.stat().st_size
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        logger.info(f"  {backup.name}")
        logger.info(f"    Size: {size:,} bytes | Modified: {mtime}")
        logger.info("-" * 80)

    return backups


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Backup SQLite database from Docker container",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Backup database from running container
  python scripts/docker_db_backup.py backup

  # Backup to custom directory
  python scripts/docker_db_backup.py backup --backup-dir /path/to/backups

  # List available backups
  python scripts/docker_db_backup.py list

  # Backup from specific container
  python scripts/docker_db_backup.py backup --container my-container
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Backup database from container")
    backup_parser.add_argument("--container", type=str, help="Container name (auto-detected if not specified)")
    backup_parser.add_argument(
        "--backup-dir", type=str, default="./backups", help="Backup directory on host (default: ./backups)"
    )
    backup_parser.add_argument(
        "--db-path",
        type=str,
        default="/app/data/ai_code_reviewer.db",
        help="Database path inside container (default: /app/data/ai_code_reviewer.db)",
    )
    backup_parser.add_argument(
        "--compose-file",
        type=str,
        default="docker/docker-compose.yml",
        help="Docker compose file path (default: docker/docker-compose.yml)",
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List available backups")
    list_parser.add_argument(
        "--backup-dir", type=str, default="./backups", help="Backup directory on host (default: ./backups)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "backup":
            # Auto-detect container name if not provided
            container = args.container
            if not container:
                container = get_container_name(args.compose_file)

            backup_file = backup_database(container_name=container, backup_dir=args.backup_dir, db_path=args.db_path)

            logger.info("\n💡 To restore this backup later, use:")
            logger.info(f"   python scripts/docker_db_restore.py restore --file {backup_file}")

        elif args.command == "list":
            list_backups(args.backup_dir)

    except Exception as e:
        logger.error(f"\n❌ Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
