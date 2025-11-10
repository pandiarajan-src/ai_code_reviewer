#!/bin/bash
# Docker Database Restore Script
# Restores a database backup to a running Docker container

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/backups"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   AI Code Reviewer - Database Restore         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo

# Parse command line arguments
BACKUP_FILE=""
AUTO_CONFIRM=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --file)
            BACKUP_FILE="$2"
            shift 2
            ;;
        --yes|-y)
            AUTO_CONFIRM=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo
            echo "Options:"
            echo "  --file FILE    Path to backup file to restore"
            echo "  --yes, -y      Skip confirmation prompt"
            echo "  --help, -h     Show this help message"
            echo
            echo "Examples:"
            echo "  $0 --file backups/ai_code_reviewer_20251110_164931.db"
            echo "  $0  # Interactive mode - lists available backups"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Run '$0 --help' for usage information"
            exit 1
            ;;
    esac
done

# If no backup file specified, show available backups and prompt
if [ -z "$BACKUP_FILE" ]; then
    echo -e "${YELLOW}Available backups in $BACKUP_DIR:${NC}"
    echo

    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A "$BACKUP_DIR"/*.db 2>/dev/null)" ]; then
        echo -e "${RED}No backups found in $BACKUP_DIR${NC}"
        echo
        echo "Create a backup first with: make docker-backup"
        exit 1
    fi

    # List backups with numbers
    mapfile -t BACKUPS < <(ls -t "$BACKUP_DIR"/*.db 2>/dev/null)

    for i in "${!BACKUPS[@]}"; do
        BACKUP="${BACKUPS[$i]}"
        FILENAME=$(basename "$BACKUP")
        SIZE=$(ls -lh "$BACKUP" | awk '{print $5}')
        TIMESTAMP=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$BACKUP" 2>/dev/null || stat -c "%y" "$BACKUP" 2>/dev/null | cut -d. -f1)
        echo -e "  ${GREEN}[$((i+1))]${NC} $FILENAME (${SIZE}) - $TIMESTAMP"
    done

    echo
    read -p "Enter backup number to restore (or 'q' to quit): " CHOICE

    if [ "$CHOICE" = "q" ] || [ "$CHOICE" = "Q" ]; then
        echo "Restore cancelled"
        exit 0
    fi

    # Validate choice
    if ! [[ "$CHOICE" =~ ^[0-9]+$ ]] || [ "$CHOICE" -lt 1 ] || [ "$CHOICE" -gt "${#BACKUPS[@]}" ]; then
        echo -e "${RED}Invalid choice${NC}"
        exit 1
    fi

    BACKUP_FILE="${BACKUPS[$((CHOICE-1))]}"
fi

# Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

BACKUP_SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
echo -e "Selected backup: ${GREEN}$(basename "$BACKUP_FILE")${NC} (${BACKUP_SIZE})"
echo

# Find running container
CONTAINER_ID=$(docker ps --filter "ancestor=ai-code-reviewer" --format "{{.ID}}" | head -n 1)

if [ -z "$CONTAINER_ID" ]; then
    # Try to find by name
    CONTAINER_ID=$(docker ps --filter "name=ai-code-reviewer" --format "{{.ID}}" | head -n 1)
fi

if [ -z "$CONTAINER_ID" ]; then
    echo -e "${RED}Error: No running ai-code-reviewer container found${NC}"
    echo
    echo "Please start the container first:"
    echo "  make docker-run"
    exit 1
fi

echo -e "Found container: ${GREEN}$CONTAINER_ID${NC}"
echo

# Confirmation prompt
if [ "$AUTO_CONFIRM" = false ]; then
    echo -e "${YELLOW}⚠️  WARNING: This will replace the current database!${NC}"
    echo
    echo "Current database will be backed up automatically before restore."
    echo
    read -p "Do you want to continue? (yes/no): " CONFIRM

    if [ "$CONFIRM" != "yes" ] && [ "$CONFIRM" != "y" ]; then
        echo "Restore cancelled"
        exit 0
    fi
    echo
fi

# Step 1: Backup current database (safety measure)
echo -e "${YELLOW}[1/4]${NC} Creating safety backup of current database..."
SAFETY_BACKUP="$BACKUP_DIR/pre_restore_safety_$(date +%Y%m%d_%H%M%S).db"

if docker cp "$CONTAINER_ID:/app/data/ai_code_reviewer.db" "$SAFETY_BACKUP" 2>/dev/null; then
    SAFETY_SIZE=$(ls -lh "$SAFETY_BACKUP" | awk '{print $5}')
    echo -e "${GREEN}✓ Safety backup created: $(basename "$SAFETY_BACKUP") (${SAFETY_SIZE})${NC}"
else
    echo -e "${YELLOW}⚠️  No existing database found (this is normal for new containers)${NC}"
fi
echo

# Step 2: Stop the application processes
echo -e "${YELLOW}[2/4]${NC} Stopping application processes..."
# Check if supervisord is running
if docker exec "$CONTAINER_ID" test -S /var/run/supervisor.sock 2>/dev/null; then
    docker exec "$CONTAINER_ID" supervisorctl stop all > /dev/null 2>&1 || true
    sleep 2
    echo -e "${GREEN}✓ Processes stopped${NC}"
else
    echo -e "${YELLOW}⚠️  Supervisor not running, will restart container instead${NC}"
fi
echo

# Step 3: Copy backup to container
echo -e "${YELLOW}[3/4]${NC} Copying backup to container..."
if docker cp "$BACKUP_FILE" "$CONTAINER_ID:/app/data/ai_code_reviewer.db"; then
    echo -e "${GREEN}✓ Database restored${NC}"
else
    echo -e "${RED}✗ Failed to copy database${NC}"
    echo
    echo "Attempting to restart services..."
    docker exec "$CONTAINER_ID" supervisorctl start all > /dev/null 2>&1 || true
    exit 1
fi
echo

# Step 4: Restart application processes
echo -e "${YELLOW}[4/4]${NC} Restarting application..."

# Check if supervisord is running
if docker exec "$CONTAINER_ID" test -S /var/run/supervisor.sock 2>/dev/null; then
    # Supervisor is running, restart services
    docker exec "$CONTAINER_ID" supervisorctl start all > /dev/null 2>&1 || true
    sleep 3

    # Verify services are running
    BACKEND_STATUS=$(docker exec "$CONTAINER_ID" supervisorctl status backend 2>/dev/null | awk '{print $2}' || echo "UNKNOWN")
    NGINX_STATUS=$(docker exec "$CONTAINER_ID" supervisorctl status nginx 2>/dev/null | awk '{print $2}' || echo "UNKNOWN")

    if [ "$BACKEND_STATUS" = "RUNNING" ] && [ "$NGINX_STATUS" = "RUNNING" ]; then
        echo -e "${GREEN}✓ Application restarted successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  Services may still be starting up. Current status:${NC}"
        docker exec "$CONTAINER_ID" supervisorctl status || true
        echo
        echo -e "${YELLOW}Note: Services may take 5-10 seconds to fully start${NC}"
    fi
else
    # Supervisor not running, restart entire container
    echo -e "${YELLOW}Restarting container to apply changes...${NC}"
    docker restart "$CONTAINER_ID" > /dev/null 2>&1
    echo -e "${GREEN}✓ Container restarted${NC}"
    echo
    echo -e "${YELLOW}Note: Container may take 10-15 seconds to fully start${NC}"
fi
echo

# Verify database
echo "Verifying restored database..."
# Use Python to query the database since sqlite3 is not installed in the container
RECORD_COUNT=$(docker exec "$CONTAINER_ID" python -c "
import sqlite3
try:
    conn = sqlite3.connect('/app/data/ai_code_reviewer.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM review_records')
    count = cursor.fetchone()[0]
    conn.close()
    print(count)
except Exception as e:
    print('0')
" 2>/dev/null || echo "0")

# Ensure RECORD_COUNT is a number
if ! [[ "$RECORD_COUNT" =~ ^[0-9]+$ ]]; then
    RECORD_COUNT=0
fi

if [ "$RECORD_COUNT" -gt 0 ] 2>/dev/null; then
    echo -e "${GREEN}✓ Database verified: $RECORD_COUNT review records found${NC}"
else
    echo -e "${YELLOW}⚠️  Database verification skipped or no records found${NC}"
    echo -e "${YELLOW}   This is normal for a fresh installation${NC}"
fi
echo

echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Restore Complete! 🎉                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo
echo "Restored from: $(basename "$BACKUP_FILE")"
echo "Safety backup: $(basename "$SAFETY_BACKUP" 2>/dev/null || echo "N/A")"
echo
echo "Next steps:"
echo "  1. Verify data: curl http://localhost:8000/api/reviews/latest"
echo "  2. Check health: curl http://localhost:8000/health"
echo "  3. Test the UI: http://localhost:3000"
echo
echo "If something went wrong, restore the safety backup:"
echo "  $0 --file $SAFETY_BACKUP"

# Exit successfully
exit 0
