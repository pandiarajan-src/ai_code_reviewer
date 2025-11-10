# Database Management Guide

Guide for managing the AI Code Reviewer database in both development and production environments.

## Overview

**Database Engine**: SQLite with async support (aiosqlite)
**Schema Management**: Alembic migrations
**Tables**:
- `review_records` - Successful code reviews
- `review_failure_logs` - Failed review attempts

## Database Locations

### Local Development

```
./ai_code_reviewer.db
```

When running `python -m ai_code_reviewer.api.main`

### Docker Production

```
Docker Volume: docker_db_data
Container Path: /app/data/ai_code_reviewer.db
```

When running `make docker-run`

### Docker Development

```
./data/ai_code_reviewer_dev.db
```

When running `make docker-run-dev`

## Schema Migrations

### Automatic Migrations

Migrations run automatically on application startup:

```python
# In app.py lifespan
run_migrations()  # Runs Alembic upgrade head
init_db()         # Creates tables if needed
```

### Manual Migrations

```bash
# Run migrations manually
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Current version
alembic current
```

### Migration Files

Located in `alembic/versions/`:
```
20250107_0001_initial_schema.py  # Initial schema
```

## Database Operations

### Local Development

```bash
# Create/initialize database
python scripts/db_helper.py create

# Reset database (drop and recreate)
python scripts/db_helper.py reset

# Clean all records
python scripts/db_helper.py clean

# View statistics
python scripts/db_helper.py stats

# Seed test data
python scripts/db_helper.py seed

# List recent reviews
python scripts/db_helper.py list

# Backup
python scripts/db_helper.py backup

# Restore
python scripts/db_helper.py restore --file backup.db
```

### Docker Production

```bash
# Backup database from container
make docker-backup
# Saves to: ./backups/ai_code_reviewer_YYYYMMDD_HHMMSS.db

# Restore database to container
docker cp backup.db <container>:/app/data/ai_code_reviewer.db
docker-compose -f docker/docker-compose.yml restart

# Access database via container
docker exec -it <container> sqlite3 /app/data/ai_code_reviewer.db

# Export database from container
docker cp <container>:/app/data/ai_code_reviewer.db ./production_db.db
```

## Schema

### review_records Table

Stores successful code reviews:

```sql
CREATE TABLE review_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Review metadata
    review_type VARCHAR(50) NOT NULL,      -- 'auto' or 'manual'
    trigger_type VARCHAR(50) NOT NULL,     -- 'commit' or 'pull_request'

    -- Repository info
    project_key VARCHAR(255) NOT NULL,
    repo_slug VARCHAR(255) NOT NULL,

    -- Commit/PR info
    commit_id VARCHAR(255),
    pr_id INTEGER,

    -- Author info
    author_name VARCHAR(255),
    author_email VARCHAR(255),

    -- Review content
    diff_content TEXT NOT NULL,
    review_feedback TEXT NOT NULL,

    -- Email info
    email_recipients JSON,
    email_sent BOOLEAN DEFAULT FALSE,

    -- LLM info
    llm_provider VARCHAR(50),
    llm_model VARCHAR(100)
);

-- Indexes
CREATE INDEX ix_review_records_project_key ON review_records(project_key);
CREATE INDEX ix_review_records_repo_slug ON review_records(repo_slug);
CREATE INDEX ix_review_records_commit_id ON review_records(commit_id);
CREATE INDEX ix_review_records_pr_id ON review_records(pr_id);
CREATE INDEX ix_review_records_author_email ON review_records(author_email);
```

### review_failure_logs Table

Stores failed review attempts for troubleshooting:

```sql
CREATE TABLE review_failure_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Request context
    event_type VARCHAR(50) NOT NULL,       -- 'webhook' or 'manual'
    event_key VARCHAR(100),
    request_payload JSON,

    -- Repository info
    project_key VARCHAR(255),
    repo_slug VARCHAR(255),
    commit_id VARCHAR(255),
    pr_id INTEGER,

    -- Author info
    author_name VARCHAR(255),
    author_email VARCHAR(255),

    -- Failure details
    failure_stage VARCHAR(100) NOT NULL,   -- Where it failed
    error_type VARCHAR(255) NOT NULL,
    error_message TEXT NOT NULL,
    error_stacktrace TEXT,

    -- Resolution tracking
    retry_count INTEGER DEFAULT 0,
    resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT
);

-- Indexes
CREATE INDEX ix_review_failure_logs_event_type ON review_failure_logs(event_type);
CREATE INDEX ix_review_failure_logs_project_key ON review_failure_logs(project_key);
CREATE INDEX ix_review_failure_logs_repo_slug ON review_failure_logs(repo_slug);
CREATE INDEX ix_review_failure_logs_failure_stage ON review_failure_logs(failure_stage);
CREATE INDEX ix_review_failure_logs_resolved ON review_failure_logs(resolved);
```

## Backup Strategies

### Development

```bash
# Simple file copy
cp ai_code_reviewer.db ai_code_reviewer.backup.db

# Using db_helper
python scripts/db_helper.py backup
```

### Production (Docker)

```bash
# Automated backup script
make docker-backup

# Manual backup
docker cp <container>:/app/data/ai_code_reviewer.db \
  ./backups/backup_$(date +%Y%m%d_%H%M%S).db
```

### Automated Backups

Create cron job for daily backups:

```bash
# /etc/cron.daily/ai-code-reviewer-backup
#!/bin/bash
cd /path/to/ai_code_reviewer
/usr/bin/make docker-backup >> /var/log/ai-code-reviewer-backup.log 2>&1
```

## Data Retention

### Cleanup Old Records

```python
# Custom script to clean old reviews (example)
from datetime import datetime, timedelta
from ai_code_reviewer.api.db.database import get_session
from ai_code_reviewer.api.db.models import ReviewRecord

async def cleanup_old_reviews(days=90):
    """Delete reviews older than 90 days."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    async with get_session() as session:
        result = await session.execute(
            delete(ReviewRecord).where(ReviewRecord.created_at < cutoff)
        )
        await session.commit()
        return result.rowcount
```

## Querying Data

### Via API Endpoints

```bash
# Get latest reviews
curl http://localhost:8000/api/reviews/latest

# Get reviews by project
curl http://localhost:8000/api/reviews/by-project/PROJECT_KEY

# Get reviews by author
curl http://localhost:8000/api/reviews/by-author/email@example.com

# Get specific review
curl http://localhost:8000/api/reviews/123
```

### Via SQLite CLI

```bash
# Open database
sqlite3 ai_code_reviewer.db

# List tables
.tables

# View schema
.schema review_records

# Query reviews
SELECT project_key, repo_slug, author_email, created_at
FROM review_records
ORDER BY created_at DESC
LIMIT 10;

# Count reviews by project
SELECT project_key, COUNT(*) as count
FROM review_records
GROUP BY project_key
ORDER BY count DESC;

# Find failed reviews
SELECT failure_stage, error_type, COUNT(*)
FROM review_failure_logs
WHERE resolved = FALSE
GROUP BY failure_stage, error_type;
```

### Via Python

```python
from ai_code_reviewer.api.db.database import get_session
from ai_code_reviewer.api.db.models import ReviewRecord

async def get_recent_reviews(limit=10):
    async with get_session() as session:
        result = await session.execute(
            select(ReviewRecord)
            .order_by(ReviewRecord.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
```

## Database Performance

### Indexes

Indexes are automatically created on:
- `project_key`, `repo_slug` (for filtering by repository)
- `commit_id`, `pr_id` (for filtering by commit/PR)
- `author_email` (for filtering by author)
- `failure_stage`, `resolved` (for failure analysis)

### Query Optimization

```sql
-- Use EXPLAIN QUERY PLAN to analyze queries
EXPLAIN QUERY PLAN
SELECT * FROM review_records WHERE project_key = 'PROJ';

-- Add indexes if needed
CREATE INDEX idx_custom ON review_records(column_name);
```

### Database Size Management

```bash
# Check database size
ls -lh ai_code_reviewer.db

# Vacuum to reclaim space
sqlite3 ai_code_reviewer.db "VACUUM;"

# Analyze for query optimization
sqlite3 ai_code_reviewer.db "ANALYZE;"
```

## Troubleshooting

### Database Locked

SQLite can lock during concurrent writes:

```python
# Already handled with aiosqlite (async writes)
# If issues persist, check:
# 1. Multiple processes accessing DB
# 2. Long-running transactions
# 3. Disk I/O issues
```

### Corrupted Database

```bash
# Check integrity
sqlite3 ai_code_reviewer.db "PRAGMA integrity_check;"

# If corrupted, restore from backup
cp ./backups/latest_backup.db ./ai_code_reviewer.db
```

### Migration Failures

```bash
# Check current version
alembic current

# View migration history
alembic history

# Manually upgrade/downgrade
alembic upgrade head
alembic downgrade -1

# Reset migrations (⚠️ DELETES DATA)
python scripts/db_helper.py reset
```

## Migration to PostgreSQL

For production at scale, consider PostgreSQL:

```python
# Update DATABASE_URL in .env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/ai_code_reviewer

# Install asyncpg
pip install asyncpg

# Run migrations
alembic upgrade head
```

Benefits:
- Better concurrent write performance
- Advanced querying capabilities
- Better for multiple backend instances
- Industry standard for production

## Best Practices

1. **Backup before upgrades**: Use `make docker-upgrade`
2. **Regular backups**: Daily automated backups via cron
3. **Monitor database size**: Set up alerts for disk usage
4. **Test migrations**: Test in development before production
5. **Clean old data**: Implement retention policy
6. **Use indexes**: Check query performance regularly
7. **Document schema changes**: Write clear migration messages

## Support

- **Docker Guide**: [docs/DOCKER.md](./DOCKER.md)
- **API Endpoints**: http://localhost:8000/docs
- **Database Helper**: `python scripts/db_helper.py --help`
