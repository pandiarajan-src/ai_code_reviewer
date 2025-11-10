#!/bin/bash
# Docker Safe Upgrade Script
# Performs a safe upgrade with automatic backup

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   AI Code Reviewer - Safe Docker Upgrade      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo

# Step 1: Backup existing database
echo -e "${YELLOW}[1/5]${NC} Backing up current database..."
if bash "$SCRIPT_DIR/docker-backup.sh"; then
    echo -e "${GREEN}✓ Backup complete${NC}"
else
    echo -e "${RED}✗ Backup failed. Aborting upgrade.${NC}"
    exit 1
fi
echo

# Step 2: Pull latest code (if git repository)
if [ -d "$PROJECT_ROOT/.git" ]; then
    echo -e "${YELLOW}[2/5]${NC} Pulling latest code from repository..."
    cd "$PROJECT_ROOT"

    # Stash any local changes
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}Warning: Local changes detected. Stashing...${NC}"
        git stash push -m "Auto-stash before upgrade $(date +%Y%m%d_%H%M%S)"
    fi

    # Pull latest
    git pull || echo -e "${YELLOW}Warning: Could not pull latest changes${NC}"
    echo -e "${GREEN}✓ Code update complete${NC}"
else
    echo -e "${YELLOW}[2/5]${NC} Skipping git pull (not a git repository)"
fi
echo

# Step 3: Rebuild Docker image
echo -e "${YELLOW}[3/5]${NC} Rebuilding Docker image..."
cd "$PROJECT_ROOT"
if docker-compose -f docker/docker-compose.yml build --no-cache; then
    echo -e "${GREEN}✓ Build complete${NC}"
else
    echo -e "${RED}✗ Build failed. Container not restarted.${NC}"
    exit 1
fi
echo

# Step 4: Recreate container (keeps volume)
echo -e "${YELLOW}[4/5]${NC} Recreating container with new image..."
echo -e "${BLUE}Note: Database volume will be preserved${NC}"
if docker-compose -f docker/docker-compose.yml up -d --force-recreate; then
    echo -e "${GREEN}✓ Container recreated${NC}"
else
    echo -e "${RED}✗ Container recreation failed${NC}"
    exit 1
fi
echo

# Step 5: Verify container is running
echo -e "${YELLOW}[5/5]${NC} Verifying container health..."
sleep 5  # Give container time to start

CONTAINER_ID=$(docker ps --filter "ancestor=ai-code-reviewer" --format "{{.ID}}" | head -n 1)
if [ -z "$CONTAINER_ID" ]; then
    CONTAINER_ID=$(docker ps --filter "name=ai-code-reviewer" --format "{{.ID}}" | head -n 1)
fi

if [ -n "$CONTAINER_ID" ]; then
    echo -e "${GREEN}✓ Container is running (ID: $CONTAINER_ID)${NC}"
    echo
    echo "Checking logs for migration status..."
    docker logs --tail 20 "$CONTAINER_ID" | grep -i "migration\|database" || true
    echo
    echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           Upgrade Complete! 🎉                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
    echo
    echo "Next steps:"
    echo "  1. Check container logs: docker logs -f $CONTAINER_ID"
    echo "  2. Verify health: curl http://localhost:8000/health"
    echo "  3. Test the application: http://localhost:3000"
else
    echo -e "${RED}✗ Container not running after upgrade${NC}"
    echo
    echo "Troubleshooting:"
    echo "  1. Check logs: docker-compose -f docker/docker-compose.yml logs"
    echo "  2. Manual start: docker-compose -f docker/docker-compose.yml up -d"
    exit 1
fi
