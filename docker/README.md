# Docker Quick Start Guide

This guide provides quick commands to get started with Docker deployment.

## Prerequisites

- Docker and Docker Compose installed
- `.env` file configured (copy from `.env.example`)

## Quick Commands

### Production Deployment

```bash
# Build the Docker image
make docker-build

# Start the container
make docker-run

# View logs
make docker-logs

# Stop the container
make docker-stop
```

### Development Deployment

For development with easy database access:

```bash
# Start in development mode (database accessible at ./data/)
make docker-run-dev

# Database will be at: ./data/ai_code_reviewer_dev.db
# You can open it with SQLite Browser or VS Code
```

### Database Management

```bash
# Backup database
make docker-backup

# Restore database from backup (interactive - shows available backups)
make docker-restore

# Restore specific backup file
bash scripts/docker-restore.sh --file backups/ai_code_reviewer_20251110_164931.db

# Safe upgrade with automatic backup
make docker-upgrade

# Export logs to file
make docker-logs-export
```

### Cleanup

```bash
# Stop containers (keeps database)
make docker-stop

# Clean everything including volumes (⚠️  DELETES DATABASE)
make docker-clean
```

## Environment Setup

1. **Create .env file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit .env** with your configuration:
   - `BITBUCKET_URL` - Your Bitbucket server URL
   - `BITBUCKET_TOKEN` - Access token for Bitbucket API
   - `LLM_PROVIDER` - `openai` or `local_ollama`
   - `LLM_API_KEY` - API key for OpenAI (if using OpenAI)
   - Other configuration as needed

## Container Architecture

The Docker container runs:
- **Frontend**: nginx serving React app on port 3000
- **Backend**: FastAPI application on port 8000
- **Database**: SQLite in persistent Docker volume
- **Process Manager**: supervisord managing both processes

## Access Points

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Database Persistence

### Production Mode (`make docker-run`)
- Database stored in Docker named volume `db_data`
- Survives container restarts and recreations
- Not directly accessible from workspace
- Access via: `docker cp <container>:/app/data/ai_code_reviewer.db ./backup.db`

### Development Mode (`make docker-run-dev`)
- Database stored in `./data/ai_code_reviewer_dev.db` (workspace)
- Directly accessible with SQLite tools
- Easy to inspect, backup, and restore
- Useful for debugging

## Logging Strategy

Logs are sent to Docker's logging system (stdout/stderr):

```bash
# View real-time logs
docker logs -f <container-id>

# Export logs to file
make docker-logs-export
```

Log rotation is automatic (10MB max, 3 rotations).

## Common Workflows

### First Time Setup

```bash
# 1. Create environment file
cp .env.example .env
vim .env  # Edit with your settings

# 2. Build and run
make docker-build
make docker-run

# 3. Verify it's working
curl http://localhost:8000/health
```

### Upgrading to New Version

```bash
# Safe upgrade with automatic backup
make docker-upgrade

# Or manual upgrade:
make docker-backup          # Backup first
git pull                     # Get latest code
make docker-build            # Rebuild image
make docker-stop             # Stop old container
make docker-run              # Start new container
```

### Debugging Issues

```bash
# Check container logs
make docker-logs

# Check health
curl http://localhost:8000/health

# Export logs for analysis
make docker-logs-export

# Access container shell
docker exec -it <container-id> /bin/bash

# Check database inside container
docker exec -it <container-id> sqlite3 /app/data/ai_code_reviewer.db ".tables"
```

### Backup and Restore

```bash
# Backup database
make docker-backup
# Saves to: ./backups/ai_code_reviewer_YYYYMMDD_HHMMSS.db

# Restore from backup (interactive mode - lists available backups)
make docker-restore

# Restore specific backup (non-interactive)
bash scripts/docker-restore.sh --file backups/ai_code_reviewer_20251110_164931.db --yes

# What the restore script does:
# 1. Creates safety backup of current database
# 2. Stops application processes
# 3. Copies backup file to container
# 4. Restarts application
# 5. Verifies database integrity
```

**Example: Restore to Fresh Container**

If you cleaned up everything and created a new container:

```bash
# 1. Build new container
make docker-build
make docker-run

# 2. Wait for container to start (5-10 seconds)
sleep 10

# 3. Restore your backup
make docker-restore
# Select your backup from the list

# 4. Verify data was restored
curl http://localhost:8000/api/reviews/latest
```

## Database Migrations

Database schema migrations run automatically on container startup using Alembic.

Migration logs appear in container startup:
```
Running database migrations...
Database migrations completed successfully
```

## Troubleshooting

### Container won't start
```bash
# Check logs for errors
make docker-logs

# Verify .env file exists and is valid
cat .env

# Rebuild without cache
docker build --no-cache -f docker/Dockerfile -t ai-code-reviewer .
```

### Database is empty
```bash
# Check if database file exists
docker exec <container-id> ls -la /app/data/

# Check database connection in logs
make docker-logs | grep -i database
```

### Can't access frontend
```bash
# Verify nginx is running
docker exec <container-id> supervisorctl status

# Check nginx logs
docker exec <container-id> cat /var/log/nginx/error.log
```

### Port already in use
```bash
# Change ports in .env file
FRONTEND_PORT=3001
BACKEND_PORT=8001

# Or stop conflicting services
lsof -i :3000  # Find process using port 3000
```

## Advanced Usage

### Running with Local Ollama LLM

```bash
make docker-run-local
```

This starts both the application and Ollama containers.

### Manual Docker Compose Commands

```bash
# Production
docker-compose -f docker/docker-compose.yml up -d

# Development
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up -d

# With Ollama
docker-compose -f docker/docker-compose.yml --profile local-llm up -d
```

### Inspect Docker Volume

```bash
# Get volume details
docker volume inspect docker_db_data

# List files in volume (via container)
docker exec <container-id> ls -la /app/data/
```

## Cross-Platform Notes

This Docker setup works identically on:
- macOS (Intel and Apple Silicon)
- Linux (Ubuntu, Debian, RHEL, etc.)
- Windows (with WSL2 or Docker Desktop)

**Windows Users**:
- Ensure line endings are LF (not CRLF) - handled automatically by `.gitattributes`
- Use PowerShell or WSL2 terminal for best compatibility

## Production Deployment Checklist

- [ ] `.env` file configured with production values
- [ ] `EMAIL_OPTOUT=false` to enable email notifications
- [ ] `LOG_LEVEL=INFO` for production logging
- [ ] `DATABASE_URL` pointing to production database path
- [ ] Regular backups scheduled (use `make docker-backup`)
- [ ] Health checks configured in orchestration tool
- [ ] Reverse proxy (nginx/Caddy) for HTTPS termination
- [ ] Firewall rules allowing only necessary ports

## Need Help?

- **Documentation**: See [docs/DOCKER.md](../docs/DOCKER.md) for comprehensive guide
- **Database**: See [docs/DATABASE.md](../docs/DATABASE.md) for database management
- **Issues**: Check container logs with `make docker-logs`
- **Community**: Open an issue on GitHub
