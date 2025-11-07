#!/bin/bash
# Docker database migration script
# This script migrates database from one Docker container to a new container.
#
# Use cases:
# - Moving to a new Docker setup
# - Migrating between different environments
# - Creating a fresh container with existing data

set -e  # Exit on error

COMPOSE_FILE="${COMPOSE_FILE:-docker/docker-compose.yml}"
BACKUP_DIR="./backups/migration"
OLD_CONTAINER=""
NEW_CONTAINER=""
DB_PATH="/app/data/ai_code_reviewer.db"

echo "====================================================="
echo "🚀 Docker Database Migration (Container to Container)"
echo "====================================================="
echo ""

# Function to get container name
get_container_name() {
    local service_name=$1
    local compose_file=$2

    container_id=$(docker-compose -f "$compose_file" ps -q "$service_name" 2>/dev/null || echo "")
    if [ -z "$container_id" ]; then
        echo ""
        return 1
    fi

    container_name=$(docker inspect --format '{{.Name}}' "$container_id" | sed 's/^\///')
    echo "$container_name"
    return 0
}

# Function to check if container is running
check_container() {
    local container=$1
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        return 0
    fi
    return 1
}

# Step 1: Identify source container
echo "Step 1: Identifying source container with database..."
echo ""
echo "Option 1: Auto-detect from docker-compose"
echo "Option 2: Specify container name manually"
echo ""
read -p "Auto-detect source container? [Y/n]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    OLD_CONTAINER=$(get_container_name "ai-code-reviewer" "$COMPOSE_FILE")
    if [ -z "$OLD_CONTAINER" ]; then
        echo "❌ Could not auto-detect container"
        exit 1
    fi
    echo "Found source container: $OLD_CONTAINER"
else
    read -p "Enter source container name: " OLD_CONTAINER
fi

if ! check_container "$OLD_CONTAINER"; then
    echo "❌ Source container '$OLD_CONTAINER' is not running"
    exit 1
fi
echo "✅ Source container verified: $OLD_CONTAINER"
echo ""

# Step 2: Backup database from old container
echo "Step 2: Backing up database from source container..."
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/migration_$(date +%Y%m%d_%H%M%S).db"

echo "Copying database: $OLD_CONTAINER:$DB_PATH -> $BACKUP_FILE"
docker cp "$OLD_CONTAINER:$DB_PATH" "$BACKUP_FILE"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup failed: file not created"
    exit 1
fi

BACKUP_SIZE=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE" 2>/dev/null)
echo "✅ Database backed up successfully"
echo "   File: $BACKUP_FILE"
echo "   Size: $BACKUP_SIZE bytes"
echo ""

# Step 3: Get database statistics
echo "Step 3: Analyzing database content..."
python3 -c "
import sqlite3
import sys

try:
    conn = sqlite3.connect('$BACKUP_FILE')
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM review_records')
    reviews = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM review_failure_logs')
    failures = cursor.fetchone()[0]

    print(f'📊 Database contains:')
    print(f'   - {reviews} review records')
    print(f'   - {failures} failure logs')

    conn.close()
except Exception as e:
    print(f'⚠️  Could not analyze database: {e}')
    sys.exit(0)  # Don't fail, just warn
"
echo ""

# Step 4: Build new Docker image
echo "Step 4: Building new Docker image..."
echo ""
read -p "Rebuild Docker image with latest code? [Y/n]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "Building new image..."
    docker-compose -f "$COMPOSE_FILE" build --no-cache ai-code-reviewer
    echo "✅ New image built"
else
    echo "⏭️  Skipping image build"
fi
echo ""

# Step 5: Stop old container (optional)
echo "Step 5: Container management..."
echo ""
read -p "Stop source container '$OLD_CONTAINER'? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Stopping source container..."
    docker stop "$OLD_CONTAINER"
    echo "✅ Source container stopped"
else
    echo "⏭️  Source container still running"
fi
echo ""

# Step 6: Create and start new container
echo "Step 6: Creating new container..."
echo ""
read -p "Start new container now? [Y/n]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    # Remove existing container if any
    docker-compose -f "$COMPOSE_FILE" down ai-code-reviewer 2>/dev/null || true

    # Start new container
    docker-compose -f "$COMPOSE_FILE" up -d ai-code-reviewer

    # Wait for container to be ready
    echo "Waiting for container to start..."
    sleep 5

    NEW_CONTAINER=$(get_container_name "ai-code-reviewer" "$COMPOSE_FILE")
    if [ -z "$NEW_CONTAINER" ]; then
        echo "❌ New container failed to start"
        exit 1
    fi
    echo "✅ New container started: $NEW_CONTAINER"
else
    echo "⏭️  Skipping container start"
    echo "You can start it later with: docker-compose -f $COMPOSE_FILE up -d"
    exit 0
fi
echo ""

# Step 7: Stop new container to restore database
echo "Step 7: Restoring database to new container..."
docker-compose -f "$COMPOSE_FILE" stop ai-code-reviewer

# Copy database to new container
echo "Copying database: $BACKUP_FILE -> $NEW_CONTAINER:$DB_PATH"
docker cp "$BACKUP_FILE" "$NEW_CONTAINER:$DB_PATH"

# Set permissions
echo "Setting file permissions..."
docker exec "$NEW_CONTAINER" chown app:app "$DB_PATH"

# Start container
docker-compose -f "$COMPOSE_FILE" start ai-code-reviewer
echo "✅ Database restored and container started"
echo ""

# Step 8: Verify migration
echo "Step 8: Verifying migration..."
sleep 5

# Check container status
echo "Container status:"
docker-compose -f "$COMPOSE_FILE" ps ai-code-reviewer
echo ""

# Verify database in new container
echo "Verifying database in new container..."
docker-compose -f "$COMPOSE_FILE" exec -T ai-code-reviewer python -c "
import sys
sys.path.insert(0, '/app/src')
import asyncio
from ai_code_reviewer.api.db.database import init_db, close_db
from ai_code_reviewer.api.db.repository import ReviewRepository, FailureLogRepository
from sqlalchemy.ext.asyncio import AsyncSession
from ai_code_reviewer.api.db.database import engine

async def verify():
    try:
        await init_db()
        async with AsyncSession(engine) as session:
            review_repo = ReviewRepository(session)
            failure_repo = FailureLogRepository(session)

            reviews = await review_repo.count_total_reviews()
            failures = await failure_repo.count_total_failures(unresolved_only=False)

            print(f'✅ Database verified in new container:')
            print(f'   - {reviews} review records')
            print(f'   - {failures} failure logs')
        await close_db()
    except Exception as e:
        print(f'❌ Database verification failed: {e}')
        sys.exit(1)

asyncio.run(verify())
" 2>&1
echo ""

# Summary
echo "====================================================="
echo "✅ Migration Complete!"
echo "====================================================="
echo ""
echo "Summary:"
echo "  - Source container: $OLD_CONTAINER"
echo "  - New container: $NEW_CONTAINER"
echo "  - Database backup: $BACKUP_FILE"
echo "  - Database restored to new container"
echo ""
echo "Next steps:"
echo "  - Access frontend: http://localhost:3000"
echo "  - Access API docs: http://localhost:8000/docs"
echo "  - View logs: docker-compose -f $COMPOSE_FILE logs -f ai-code-reviewer"
echo "  - Verify data: python scripts/db_helper.py stats"
echo ""
echo "If you stopped the old container, you can remove it:"
echo "  docker rm $OLD_CONTAINER"
echo ""
echo "Database backup is kept at: $BACKUP_FILE"
echo ""
