# Docker Database Upgrade - Quick Start

This is a quick reference for upgrading your Docker container while preserving the database.

## TL;DR - Just Want to Upgrade?

```bash
# Run this one command:
./scripts/docker_upgrade_inplace.sh
```

That's it! The script handles everything automatically.

---

## What Happens?

1. ✅ Backs up your current database (safety)
2. ✅ Rebuilds Docker image with your latest code
3. ✅ Recreates container with new image
4. ✅ **Automatically preserves database** (lives in Docker volume)
5. ✅ Verifies everything works

**Time**: ~2-5 minutes
**Downtime**: ~30 seconds
**Data Loss Risk**: Zero (backup created first)

---

## Two Main Scenarios

### Scenario 1: Update API in Same Container ⭐ RECOMMENDED

**When**: You just want to update your code

```bash
./scripts/docker_upgrade_inplace.sh
```

**Why it works**: Your database lives in a Docker volume (not in the container). When the container rebuilds, the volume automatically reattaches.

---

### Scenario 2: Migrate to New Container

**When**: You're moving to a completely different setup

```bash
./scripts/docker_migrate_db.sh
```

**What it does**: Copies database from old container → new container

---

## Manual Backup/Restore

### Create Backup

```bash
# Backup database from running container
python scripts/docker_db_backup.py backup
```

Output: `./backups/ai_code_reviewer_YYYYMMDD_HHMMSS.db`

### Restore Backup

```bash
# Restore database to running container
python scripts/docker_db_restore.py restore --file ./backups/ai_code_reviewer_20250106_120000.db
```

### List Backups

```bash
python scripts/docker_db_backup.py list
```

---

## Common Tasks

### Check Database Content

```bash
# View database statistics
docker-compose -f docker/docker-compose.yml exec ai-code-reviewer python scripts/db_helper.py stats

# Or shorter version:
python scripts/db_helper.py stats  # (if container is configured)
```

### View Container Logs

```bash
docker-compose -f docker/docker-compose.yml logs -f ai-code-reviewer
```

### Rebuild and Restart

```bash
# Stop container
docker-compose -f docker/docker-compose.yml down

# Rebuild image
docker-compose -f docker/docker-compose.yml build --no-cache

# Start container (database automatically restored)
docker-compose -f docker/docker-compose.yml up -d
```

---

## Why Database Survives Rebuilds?

### Your Docker Setup

```yaml
# docker-compose.yml
services:
  ai-code-reviewer:
    volumes:
      - db_data:/app/data    # ← This is the magic!

volumes:
  db_data:  # ← Persistent storage (survives container removal)
```

### What This Means

```
Container Rebuild:
  ❌ Container deleted
  ❌ Application code removed
  ✅ db_data volume preserved
  ✅ Database survives!

When new container starts:
  ✅ Same db_data volume attached
  ✅ Database appears exactly as before
```

---

## Troubleshooting

### "Container not found"

```bash
# Check if container is running
docker-compose -f docker/docker-compose.yml ps

# Start it
docker-compose -f docker/docker-compose.yml up -d
```

### "Database is empty after upgrade"

```bash
# Restore from backup
python scripts/docker_db_restore.py restore --file ./backups/latest_backup.db
```

### "Permission denied"

```bash
# Fix permissions
docker-compose -f docker/docker-compose.yml exec ai-code-reviewer chown -R app:app /app/data
```

---

## Best Practices

1. **Always backup before upgrades**
   ```bash
   python scripts/docker_db_backup.py backup --backup-dir ./backups/pre_upgrade
   ```

2. **Test in non-production first**
   - Copy backup to test environment
   - Run upgrade script
   - Verify everything works
   - Then upgrade production

3. **Keep multiple backups**
   ```bash
   # Daily backups (add to crontab)
   0 2 * * * cd /path/to/ai_code_reviewer && python scripts/docker_db_backup.py backup
   ```

4. **Never delete volumes without backup**
   ```bash
   # Safe: Stops container, keeps volume
   docker-compose down

   # DANGER: Deletes volume and data!
   docker-compose down -v  # ⚠️ Only do this if you have backups!
   ```

---

## Need More Details?

See the complete guide: [DOCKER_DATABASE_MANAGEMENT.md](./DOCKER_DATABASE_MANAGEMENT.md)

---

## Quick Command Reference

```bash
# UPGRADE (Scenario 1 - Most Common)
./scripts/docker_upgrade_inplace.sh

# MIGRATE (Scenario 2 - New Container)
./scripts/docker_migrate_db.sh

# BACKUP
python scripts/docker_db_backup.py backup

# RESTORE
python scripts/docker_db_restore.py restore --file <backup-file>

# LIST BACKUPS
python scripts/docker_db_backup.py list

# DATABASE STATS
python scripts/db_helper.py stats

# CONTAINER LOGS
docker-compose -f docker/docker-compose.yml logs -f ai-code-reviewer

# REBUILD CONTAINER
docker-compose -f docker/docker-compose.yml up -d --force-recreate

# CHECK VOLUME
docker volume ls | grep db_data
```

---

## Summary

**For most cases**: Just run `./scripts/docker_upgrade_inplace.sh`

Your database is safe because:
- ✅ Stored in Docker volume (not container)
- ✅ Volume survives container rebuilds
- ✅ Backup created before upgrade
- ✅ Scripts handle everything automatically

**Result**: Updated API + Same database data 🎉
