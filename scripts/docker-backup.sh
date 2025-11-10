#!/bin/bash
# Docker Database Backup Script
# Backs up the database from a running Docker container

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ai_code_reviewer_$TIMESTAMP.db"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== AI Code Reviewer - Database Backup ===${NC}"
echo

# Find running container
CONTAINER_ID=$(docker ps --filter "ancestor=ai-code-reviewer" --format "{{.ID}}" | head -n 1)

if [ -z "$CONTAINER_ID" ]; then
    # Try to find by name
    CONTAINER_ID=$(docker ps --filter "name=ai-code-reviewer" --format "{{.ID}}" | head -n 1)
fi

if [ -z "$CONTAINER_ID" ]; then
    echo -e "${RED}Error: No running ai-code-reviewer container found${NC}"
    echo "Please start the container first with: docker-compose up -d"
    exit 1
fi

echo -e "Found container: ${GREEN}$CONTAINER_ID${NC}"
echo

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Copy database from container
echo "Backing up database..."
if docker cp "$CONTAINER_ID:/app/data/ai_code_reviewer.db" "$BACKUP_FILE"; then
    FILE_SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
    echo -e "${GREEN}✓ Backup successful!${NC}"
    echo
    echo "Backup saved to: $BACKUP_FILE"
    echo "Size: $FILE_SIZE"
    echo

    # Show backup directory contents
    echo "Available backups in $BACKUP_DIR:"
    ls -lht "$BACKUP_DIR"/*.db 2>/dev/null | head -n 5 || echo "No backups found"
    echo

    # Cleanup old backups (keep last 10)
    BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/*.db 2>/dev/null | wc -l)
    if [ "$BACKUP_COUNT" -gt 10 ]; then
        echo -e "${YELLOW}Cleaning up old backups (keeping last 10)...${NC}"
        ls -t "$BACKUP_DIR"/*.db | tail -n +11 | xargs rm -f
        echo -e "${GREEN}✓ Cleanup complete${NC}"
    fi
else
    echo -e "${RED}✗ Backup failed${NC}"
    exit 1
fi
