# Docker Database Management Guide

This guide explains how to manage your SQLite database when updating your Docker containers. Your database is stored in a persistent Docker volume (`db_data`), which means it survives container rebuilds by default.

## Overview

The AI Code Reviewer uses SQLite for data persistence. The database is stored in a Docker volume mounted at `/app/data` inside the container. This setup provides:

- **Data Persistence**: Database survives container restarts and rebuilds
- **Easy Backups**: Simple file-based backup and restore
- **Migration Support**: Move data between containers or environments

## Quick Reference

```bash
# Scenario 1: Update API in existing container (preserves database automatically)
./scripts/docker_upgrade_inplace.sh

# Scenario 2: Migrate database to new container
./scripts/docker_migrate_db.sh

# Manual backup
python scripts/docker_db_backup.py backup

# Manual restore
python scripts/docker_db_restore.py restore --file ./backups/backup.db

# List backups
python scripts/docker_db_backup.py list
```

---

## Scenario 1: In-Place Docker Upgrade (Recommended)

**Use Case**: You want to update your API code without losing database data.

### How It Works

1. **Database Volume**: Your database lives in Docker volume `db_data` (not in the container filesystem)
2. **Rebuild Image**: New image built with updated code
3. **Recreate Container**: Old container removed, new one created
4. **Volume Reattached**: Same `db_data` volume attached to new container
5. **Result**: Updated API + Original database ✅

### Usage

#### Automated Script (Recommended)

```bash
# Run the automated upgrade script
./scripts/docker_upgrade_inplace.sh
```

The script will:
1. ✅ Check current container status
2. 📦 Create database backup (safety net)
3. 🔄 Pull latest code from git (optional)
4. 🏗️ Rebuild Docker image
5. 🔁 Recreate container (preserving volumes)
6. ✅ Verify database connectivity
7. 📊 Show logs and status

#### Manual Steps

If you prefer manual control:

```bash
# 1. Backup current database (recommended)
python scripts/docker_db_backup.py backup --backup-dir ./backups/pre_upgrade

# 2. Pull latest code
git pull  # or update your code manually

# 3. Rebuild Docker image
docker-compose -f docker/docker-compose.yml build --no-cache ai-code-reviewer

# 4. Recreate container (preserves volumes)
docker-compose -f docker/docker-compose.yml up -d --force-recreate ai-code-reviewer

# 5. Verify
docker-compose -f docker/docker-compose.yml logs -f ai-code-reviewer
python scripts/db_helper.py stats
```

### Key Points

- ✅ **Safe**: Database volume is automatically preserved
- ✅ **Fast**: No manual database migration needed
- ✅ **Backup**: Script creates backup before upgrade
- ⚠️ **Volume Names**: Don't change volume name in docker-compose.yml

---

## Scenario 2: Migrate Database to New Container

**Use Case**:
- Moving to a completely new Docker setup
- Migrating between environments (dev → prod)
- Changing Docker compose configuration significantly

### How It Works

1. **Extract Database**: Copy database file from old container
2. **Create Backup**: Save database to host filesystem
3. **Build New Container**: Create new container with updated setup
4. **Inject Database**: Copy database into new container
5. **Result**: New container + Migrated database ✅

### Usage

#### Automated Script (Recommended)

```bash
# Run the automated migration script
./scripts/docker_migrate_db.sh
```

The script will:
1. 🔍 Identify source container (auto-detect or manual)
2. 📦 Backup database from old container
3. 📊 Analyze database content (review counts, etc.)
4. 🏗️ Build new Docker image (optional)
5. 🛑 Stop old container (optional)
6. 🚀 Create and start new container
7. 📥 Restore database to new container
8. ✅ Verify migration

#### Manual Steps

```bash
# 1. Backup database from old container
python scripts/docker_db_backup.py backup --backup-dir ./backups/migration

# This creates: ./backups/migration/ai_code_reviewer_YYYYMMDD_HHMMSS.db

# 2. Build new Docker image
docker-compose -f docker/docker-compose.yml build ai-code-reviewer

# 3. Stop old container (if needed)
docker stop <old-container-name>

# 4. Start new container
docker-compose -f docker/docker-compose.yml up -d ai-code-reviewer

# 5. Restore database to new container
python scripts/docker_db_restore.py restore --file ./backups/migration/ai_code_reviewer_YYYYMMDD_HHMMSS.db

# The restore script will:
# - Stop the container
# - Copy database file
# - Set proper permissions
# - Restart the container
```

---

## Database Backup and Restore Tools

### Backup Database

Extract database from running Docker container to host filesystem.

```bash
# Basic backup
python scripts/docker_db_backup.py backup

# Custom backup location
python scripts/docker_db_backup.py backup --backup-dir /path/to/backups

# Specific container
python scripts/docker_db_backup.py backup --container my-container-name

# List all backups
python scripts/docker_db_backup.py list
```

**Output**: `./backups/ai_code_reviewer_YYYYMMDD_HHMMSS.db`

### Restore Database

Inject database backup into running Docker container.

```bash
# Basic restore
python scripts/docker_db_restore.py restore --file ./backups/ai_code_reviewer_20250106_120000.db

# Skip pre-restore backup
python scripts/docker_db_restore.py restore --file backup.db --no-backup

# Specific container
python scripts/docker_db_restore.py restore --file backup.db --container my-container
```

**Safety Features**:
- ✅ Creates backup of current database before restore
- ✅ Stops container during restore (ensures data integrity)
- ✅ Sets proper file permissions
- ✅ Restarts container automatically

---

## Database Management Commands

Once you have shell access to the container, you can use these commands:

```bash
# Enter container shell
docker-compose -f docker/docker-compose.yml exec ai-code-reviewer bash

# Inside container, use db_helper.py
cd /app
python scripts/db_helper.py stats      # Show database statistics
python scripts/db_helper.py list       # List recent reviews
python scripts/db_helper.py backup     # Backup database (inside container)
python scripts/db_helper.py seed       # Add test data
```

Or run directly from host:

```bash
# Run db_helper commands without entering container
docker-compose -f docker/docker-compose.yml exec ai-code-reviewer python scripts/db_helper.py stats
docker-compose -f docker/docker-compose.yml exec ai-code-reviewer python scripts/db_helper.py list
```

---

## Understanding Docker Volumes

### What is a Docker Volume?

A Docker volume is a persistent storage location that exists **outside** the container filesystem. Think of it as an external hard drive that can be plugged into different containers.

```
Host Machine:
  /var/lib/docker/volumes/db_data/

Container:
  /app/data/ai_code_reviewer.db  →  (mapped to)  →  db_data volume

When container is removed:
  ❌ Container filesystem deleted
  ✅ Volume data preserved
```

### Your Volume Configuration

In `docker-compose.yml`:

```yaml
services:
  ai-code-reviewer:
    volumes:
      - db_data:/app/data    # Maps volume 'db_data' to /app/data in container

volumes:
  db_data:  # Persistent volume (survives container rebuilds)
```

### Volume Operations

```bash
# List volumes
docker volume ls

# Inspect volume (see where it's stored on host)
docker volume inspect ai-code-reviewer_db_data

# Remove volume (⚠️ CAUTION: Deletes all data!)
docker volume rm ai-code-reviewer_db_data

# Remove container but keep volume
docker-compose -f docker/docker-compose.yml down

# Remove container AND volume (⚠️ CAUTION: Data loss!)
docker-compose -f docker/docker-compose.yml down -v
```

---

## Troubleshooting

### Database Not Found After Upgrade

**Symptom**: Container starts but database is empty.

**Possible Causes**:
1. Volume was accidentally deleted
2. Database path changed in environment variables

**Solution**:
```bash
# Check if volume exists
docker volume ls | grep db_data

# If volume missing, restore from backup
python scripts/docker_db_restore.py restore --file ./backups/latest_backup.db

# Verify DATABASE_URL in .env file
grep DATABASE_URL .env
# Should be: DATABASE_URL=sqlite+aiosqlite:////app/data/ai_code_reviewer.db
```

### Permission Errors

**Symptom**: Container can't write to database.

**Solution**:
```bash
# Fix permissions inside container
docker-compose -f docker/docker-compose.yml exec ai-code-reviewer chown -R app:app /app/data

# Or rebuild container
docker-compose -f docker/docker-compose.yml up -d --force-recreate
```

### Backup Script Can't Find Container

**Symptom**: `Container 'ai-code-reviewer' is not running`

**Solution**:
```bash
# Check container status
docker-compose -f docker/docker-compose.yml ps

# If container is stopped, start it
docker-compose -f docker/docker-compose.yml up -d

# If container has different name, use --container flag
docker ps  # Find actual container name
python scripts/docker_db_backup.py backup --container <actual-name>
```

### Database Locked During Restore

**Symptom**: `database is locked` error

**Solution**:
```bash
# Stop all connections to database
docker-compose -f docker/docker-compose.yml stop ai-code-reviewer

# Then retry restore
python scripts/docker_db_restore.py restore --file backup.db
```

---

## Best Practices

### Regular Backups

```bash
# Create cron job for daily backups
# Add to crontab (crontab -e):
0 2 * * * cd /path/to/ai_code_reviewer && python scripts/docker_db_backup.py backup --backup-dir ./backups/daily

# Backup rotation script
#!/bin/bash
# Keep only last 7 days of backups
find ./backups/daily -name "ai_code_reviewer_*.db" -mtime +7 -delete
```

### Before Major Changes

Always backup before:
- Upgrading Docker image
- Changing database schema
- Modifying docker-compose.yml
- Updating environment variables

```bash
# Pre-change backup
python scripts/docker_db_backup.py backup --backup-dir ./backups/before_upgrade
```

### Testing Upgrades

Test in non-production environment first:

```bash
# 1. Backup production database
python scripts/docker_db_backup.py backup --backup-dir ./backups/prod

# 2. Copy to test environment
scp ./backups/prod/latest.db test-server:/path/to/backups/

# 3. Test upgrade on test environment
ssh test-server
cd /path/to/ai_code_reviewer
./scripts/docker_upgrade_inplace.sh

# 4. Verify test environment
python scripts/db_helper.py stats

# 5. If successful, upgrade production
```

### Disaster Recovery

Keep backups in multiple locations:

```bash
# Backup to multiple destinations
python scripts/docker_db_backup.py backup --backup-dir ./backups/local
cp ./backups/local/latest.db /mnt/network-share/backups/
aws s3 cp ./backups/local/latest.db s3://my-bucket/backups/
```

---

## Migration Scenarios

### Scenario: Local Development → Production

```bash
# On local machine (development)
python scripts/docker_db_backup.py backup --backup-dir ./backups/to_prod

# Copy to production server
scp ./backups/to_prod/latest.db prod-server:/path/to/backups/

# On production server
cd /path/to/ai_code_reviewer
python scripts/docker_db_restore.py restore --file /path/to/backups/latest.db
```

### Scenario: Changing Docker Compose Setup

If you need to change volume configuration:

```bash
# 1. Backup current database
python scripts/docker_db_backup.py backup

# 2. Stop and remove containers and volumes
docker-compose -f docker/docker-compose.yml down -v

# 3. Update docker-compose.yml
# (make your changes)

# 4. Start new setup
docker-compose -f docker/docker-compose.yml up -d

# 5. Restore database
python scripts/docker_db_restore.py restore --file ./backups/latest.db
```

### Scenario: Moving to Different Database

If migrating from SQLite to PostgreSQL:

```bash
# 1. Backup current SQLite database
python scripts/docker_db_backup.py backup

# 2. Export data from SQLite
python scripts/db_helper.py list --limit 10000 > reviews_export.json

# 3. Update DATABASE_URL in .env
# DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname

# 4. Initialize new database
python scripts/db_helper.py create

# 5. Import data (requires custom script)
# python scripts/import_from_sqlite.py reviews_export.json
```

---

## Summary

### For Scenario 1 (In-Place Upgrade):
✅ **Simplest approach** - Volume is automatically preserved
✅ **Use**: `./scripts/docker_upgrade_inplace.sh`
✅ **Result**: Updated API + Same database

### For Scenario 2 (New Container):
✅ **Complete migration** - Full database transfer
✅ **Use**: `./scripts/docker_migrate_db.sh`
✅ **Result**: New container + Migrated database

### Key Takeaways:
- 📦 Database lives in Docker volume (not container)
- 🔄 Volume survives container rebuilds automatically
- 💾 Always backup before major changes
- 🛠️ Use provided scripts for automation
- ✅ Test upgrades in non-production first

---

## Support

For issues or questions:
- Check logs: `docker-compose -f docker/docker-compose.yml logs -f`
- Verify database: `python scripts/db_helper.py stats`
- Review Docker volumes: `docker volume ls`
- Check container status: `docker-compose -f docker/docker-compose.yml ps`
