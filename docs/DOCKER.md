# Docker Deployment Guide

Comprehensive guide for Docker deployment of AI Code Reviewer.

## Overview

The application runs in a single Docker container with:
- **Frontend**: nginx serving React (port 3000)
- **Backend**: FastAPI/uvicorn (port 8000)
- **Database**: SQLite with persistent volume
- **Process Manager**: supervisord

## Quick Start

```bash
# 1. Setup environment
cp .env.example .env
vim .env  # Configure your settings

# 2. Build and run
make docker-build
make docker-run

# 3. Access
#   - Frontend: http://localhost:3000
#   - Backend: http://localhost:8000
#   - API Docs: http://localhost:8000/docs
```

## Deployment Modes

### Production Mode (Recommended)

Uses Docker named volume for database:

```bash
make docker-run
```

**Database Location**: Docker volume `docker_db_data`
- Isolated from workspace
- Best performance
- Survives container recreations
- Access via `docker cp` when needed

### Development Mode

Uses bind mount for easy database access:

```bash
make docker-run-dev
```

**Database Location**: `./data/ai_code_reviewer_dev.db` (workspace)
- Directly accessible
- Easy debugging
- Can open with SQLite Browser

## Database Management

### Automatic Migrations

Alembic migrations run automatically on container startup:
```
Running database migrations...
Database migrations completed successfully
```

### Backup and Restore

**Backup:**
```bash
# Create backup of running container's database
make docker-backup
# Saves to: ./backups/ai_code_reviewer_YYYYMMDD_HHMMSS.db
# Keeps last 10 backups automatically
```

**Restore:**
```bash
# Interactive mode - shows available backups
make docker-restore

# Non-interactive mode - restore specific file
bash scripts/docker-restore.sh --file backups/ai_code_reviewer_20251110_164931.db --yes

# The restore process:
# 1. ✓ Creates safety backup of current database
# 2. ✓ Stops application gracefully
# 3. ✓ Copies backup to container
# 4. ✓ Restarts application
# 5. ✓ Verifies database integrity
```

**Restore to Fresh Container:**

If you've cleaned everything and created a new container:

```bash
# 1. Start new container
make docker-build
make docker-run

# 2. Restore your data
make docker-restore
# Select backup from interactive list

# 3. Verify
curl http://localhost:8000/api/reviews/latest
```

**Safe Upgrade (Backup + Rebuild + Restore):**
```bash
make docker-upgrade
# Automatically: backup → rebuild → migrate → restart
```

## Logging

### Docker Native Logging (Recommended)

All logs go to Docker's logging system:

```bash
# View real-time
docker logs -f <container-id>

# Last 100 lines
docker logs --tail 100 <container-id>

# Since 1 hour ago
docker logs --since 1h <container-id>

# Export to file
make docker-logs-export
```

**Log Rotation**: Automatic (10MB max, 3 files, 30MB total)

### Why Docker Logs?

✅ Cross-platform consistency
✅ Automatic rotation
✅ Integration with log aggregation tools
✅ Works with Kubernetes
✅ No disk space management

## Upgrading

### Safe Upgrade Process

```bash
make docker-upgrade
```

This automatically:
1. Backs up current database
2. Pulls latest code (if git repo)
3. Rebuilds Docker image
4. Recreates container (preserves volume)
5. Runs database migrations
6. Verifies health

### Manual Upgrade

```bash
make docker-backup
git pull
make docker-build
docker-compose -f docker/docker-compose.yml up -d --force-recreate
```

## Environment Variables

All configuration via `.env` file:

```bash
# Bitbucket
BITBUCKET_URL=https://your-bitbucket.com
BITBUCKET_TOKEN=your_token

# LLM
LLM_PROVIDER=openai  # or local_ollama
LLM_API_KEY=your_api_key
LLM_MODEL=gpt-4o

# Email
LOGIC_APP_EMAIL_URL=https://your-logic-app
EMAIL_OPTOUT=false  # Set to false for production

# Database (optional - has smart defaults)
DATABASE_URL=sqlite+aiosqlite:////app/data/ai_code_reviewer.db
```

## Production Deployment

### Prerequisites

- Docker and Docker Compose
- Configured `.env` file
- Reverse proxy for HTTPS (recommended)

### Deployment Steps

```bash
# 1. Clone repository
git clone <repo-url>
cd ai_code_reviewer

# 2. Configure
cp .env.example .env
vim .env

# 3. Deploy
make docker-build
make docker-run

# 4. Verify
curl http://localhost:8000/health
```

### Health Checks

Built-in health endpoint:

```bash
curl http://localhost:8000/health
```

Returns status of:
- API server
- Database connectivity
- LLM provider
- Bitbucket connectivity

### Reverse Proxy Setup

#### nginx

```nginx
server {
    listen 443 ssl;
    server_name code-reviewer.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;  # For long LLM requests
    }
}
```

## Troubleshooting

### Container won't start

```bash
# Check logs
make docker-logs

# Verify .env
cat .env

# Rebuild without cache
docker build --no-cache -f docker/Dockerfile -t ai-code-reviewer .
```

### Database issues

```bash
# Check if DB exists
docker exec <container> ls -la /app/data/

# Check migrations
docker logs <container> | grep migration

# Manual migration
docker exec <container> alembic upgrade head
```

### Port conflicts

```bash
# Find process using port
lsof -i :3000
lsof -i :8000

# Change ports in .env
FRONTEND_PORT=3001
BACKEND_PORT=8001
```

## Cross-Platform Support

Works identically on:
- macOS (Intel/Apple Silicon)
- Linux (Ubuntu/Debian/RHEL)
- Windows (WSL2/Docker Desktop)

**Notes**:
- Line endings handled by `.gitattributes` (LF enforced)
- Single `docker-compose.yml` for all platforms
- No platform-specific workarounds needed

## Advanced Topics

### Running with Ollama

```bash
make docker-run-local
```

### Custom Docker Compose

```bash
# Create docker-compose.override.yml for local overrides
version: '3.8'
services:
  ai-code-reviewer:
    environment:
      - LOG_LEVEL=DEBUG
    ports:
      - "8001:8000"  # Different port
```

### Understanding Docker Volumes

Docker volumes are persistent storage that exists **outside** the container filesystem. Think of them as external storage that can be attached to different containers.

```
Host Machine:
  /var/lib/docker/volumes/docker_db_data/_data/

Container View:
  /app/data/ai_code_reviewer.db  →  (mapped to)  →  docker_db_data volume

When container is rebuilt:
  ❌ Container filesystem deleted
  ❌ Application code removed
  ✅ Volume data preserved
  ✅ Database survives!

When new container starts:
  ✅ Same volume automatically reattaches
  ✅ Database appears exactly as before
```

**Why database survives rebuilds:**
- Database lives in Docker volume (not container)
- Volume configured in docker-compose.yml: `db_data:/app/data`
- Volume survives `docker-compose down` and rebuilds
- Only deleted with `docker-compose down -v` (dangerous!)

### Inspecting Volumes

```bash
# Volume details
docker volume inspect docker_db_data

# List files
docker exec <container> ls -la /app/data/
```

### Performance Tuning

For high-traffic deployments:

```yaml
# docker-compose.yml
services:
  ai-code-reviewer:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

## Security Considerations

- Use strong `WEBHOOK_SECRET`
- Don't commit `.env` file
- Use HTTPS in production
- Regularly update dependencies
- Enable firewall rules
- Use reverse proxy for SSL termination

## Monitoring

### Logs

```bash
# Application logs
docker logs -f <container>

# Specific service (nginx/backend)
docker exec <container> supervisorctl status
```

### Metrics

Health endpoint provides:
- Response time
- Database status
- External API connectivity

### Alerts

Set up monitoring for:
- Container restarts
- Health check failures
- Disk space (for logs/database)
- Memory/CPU usage

## Backup Strategy

### Automated Backups

Create cron job:

```bash
# /etc/cron.daily/ai-code-reviewer-backup
#!/bin/bash
cd /path/to/ai_code_reviewer
make docker-backup
```

### Retention Policy

Default: Keep last 10 backups (handled by backup script)

Customize in `scripts/docker-backup.sh`:
```bash
# Keep last 30 backups instead of 10
ls -t "$BACKUP_DIR"/*.db | tail -n +31 | xargs rm -f
```

## Migration to Kubernetes

The Docker setup can be migrated to Kubernetes:

1. Convert docker-compose to k8s manifests
2. Use PersistentVolumeClaim for database
3. Add liveness/readiness probes
4. Configure Ingress for HTTPS

See `docs/deployment.md` for Kubernetes example.

## Support

- **Quick Start**: [docker/README.md](../docker/README.md)
- **Database Guide**: [docs/DATABASE.md](./DATABASE.md)
- **Development**: [docs/development.md](./development.md)
- **Issues**: GitHub Issues
