#!/bin/bash
# In-place Docker upgrade script
# This script updates the API service in the existing Docker container while preserving the database.
#
# The database is stored in a Docker volume 'db_data' which persists across container rebuilds.

set -e  # Exit on error

COMPOSE_FILE="${COMPOSE_FILE:-docker/docker-compose.yml}"
BACKUP_DIR="./backups/pre_upgrade"

echo "=================================================="
echo "🔄 Docker In-Place Upgrade (Preserving Database)"
echo "=================================================="
echo ""

# Function to show status
show_status() {
    echo ""
    echo "📊 Current container status:"
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
}

# Function to check if container is running
check_container() {
    if ! docker-compose -f "$COMPOSE_FILE" ps -q ai-code-reviewer | grep -q .; then
        echo "⚠️  Container 'ai-code-reviewer' is not running"
        return 1
    fi
    return 0
}

# Step 1: Check current status
echo "Step 1: Checking current container status..."
show_status

# Step 2: Create backup of current database (optional but recommended)
echo "Step 2: Creating database backup..."
if check_container; then
    mkdir -p "$BACKUP_DIR"
    python3 scripts/docker_db_backup.py backup --backup-dir "$BACKUP_DIR"
    echo "✅ Backup created in $BACKUP_DIR"
else
    echo "⚠️  Container not running, skipping backup"
fi
echo ""

# Step 3: Pull latest code changes
echo "Step 3: Checking for code updates..."
if [ -d .git ]; then
    echo "Git repository detected. Current status:"
    git status --short
    echo ""
    read -p "Do you want to pull latest changes from git? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git pull
        echo "✅ Code updated from git"
    else
        echo "⏭️  Skipping git pull"
    fi
else
    echo "⏭️  Not a git repository, skipping code update"
fi
echo ""

# Step 4: Rebuild Docker image
echo "Step 4: Rebuilding Docker image with updated code..."
echo "This will build a new image but preserve the database volume."
echo ""
docker-compose -f "$COMPOSE_FILE" build --no-cache ai-code-reviewer
echo "✅ Image rebuilt successfully"
echo ""

# Step 5: Recreate container (preserving volumes)
echo "Step 5: Recreating container with new image..."
echo "The database volume 'db_data' will be preserved."
echo ""
docker-compose -f "$COMPOSE_FILE" up -d --force-recreate ai-code-reviewer
echo "✅ Container recreated"
echo ""

# Step 6: Wait for container to be healthy
echo "Step 6: Waiting for container to start..."
sleep 5

# Check health status
for i in {1..30}; do
    if docker-compose -f "$COMPOSE_FILE" ps ai-code-reviewer | grep -q "healthy\|Up"; then
        echo "✅ Container is healthy and running"
        break
    fi
    echo "Waiting for container to be healthy... ($i/30)"
    sleep 2
done
echo ""

# Step 7: Verify upgrade
echo "Step 7: Verifying upgrade..."
show_status

# Check database connectivity
echo "Checking database connectivity..."
if docker-compose -f "$COMPOSE_FILE" exec -T ai-code-reviewer python -c "
import sys
sys.path.insert(0, '/app/src')
import asyncio
from ai_code_reviewer.api.db.database import init_db, close_db
from ai_code_reviewer.api.db.repository import ReviewRepository
from sqlalchemy.ext.asyncio import AsyncSession
from ai_code_reviewer.api.db.database import engine

async def check():
    try:
        await init_db()
        async with AsyncSession(engine) as session:
            repo = ReviewRepository(session)
            count = await repo.count_total_reviews()
            print(f'✅ Database accessible. Total reviews: {count}')
        await close_db()
    except Exception as e:
        print(f'❌ Database check failed: {e}')
        sys.exit(1)

asyncio.run(check())
" 2>&1; then
    echo "✅ Database connectivity verified"
else
    echo "⚠️  Database check had issues (see above)"
fi
echo ""

# Step 8: Show logs
echo "Step 8: Recent container logs:"
echo "=================================================="
docker-compose -f "$COMPOSE_FILE" logs --tail=50 ai-code-reviewer
echo "=================================================="
echo ""

# Summary
echo "✅ Upgrade complete!"
echo ""
echo "Summary:"
echo "  - Docker image rebuilt with updated code"
echo "  - Container recreated with new image"
echo "  - Database volume 'db_data' preserved"
echo "  - Backup available in: $BACKUP_DIR"
echo ""
echo "Next steps:"
echo "  - Access frontend: http://localhost:3000"
echo "  - Access API docs: http://localhost:8000/docs"
echo "  - View logs: docker-compose -f $COMPOSE_FILE logs -f ai-code-reviewer"
echo "  - Check database: python scripts/db_helper.py stats"
echo ""
echo "If something went wrong, restore from backup:"
echo "  python scripts/docker_db_restore.py restore --file $BACKUP_DIR/<backup-file>"
echo ""
