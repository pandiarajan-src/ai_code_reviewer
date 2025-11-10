# Backup and Restore Guide

Complete guide for backing up and restoring your AI Code Reviewer database.

## Quick Reference

```bash
# Backup
make docker-backup

# Restore (interactive)
make docker-restore

# Restore (specific file)
bash scripts/docker-restore.sh --file backups/ai_code_reviewer_20251110_164931.db --yes
```

---

## Backup Operations

### Creating Backups

#### Automated Backup

```bash
make docker-backup
```

**What happens:**
1. Finds running container
2. Copies database to `./backups/ai_code_reviewer_YYYYMMDD_HHMMSS.db`
3. Shows backup size and location
4. Automatically keeps last 10 backups (deletes older ones)

**Example output:**
```
=== AI Code Reviewer - Database Backup ===

Found container: a4f918ab76f2
Backing up database...
✓ Backup successful!

Backup saved to: ./backups/ai_code_reviewer_20251110_164931.db
Size: 65K

Available backups in ./backups:
-rw-r--r--  1 user  staff   65K Nov 10 16:49 ai_code_reviewer_20251110_164931.db
-rw-r--r--  1 user  staff   62K Nov 10 15:30 ai_code_reviewer_20251110_153045.db
```

#### Scheduled Backups (Recommended for Production)

**Option 1: Cron (Linux/Mac)**

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /path/to/ai_code_reviewer && make docker-backup >> /var/log/ai-code-reviewer-backup.log 2>&1
```

**Option 2: Systemd Timer (Linux)**

```bash
# Create service: /etc/systemd/system/ai-code-reviewer-backup.service
[Unit]
Description=AI Code Reviewer Database Backup

[Service]
Type=oneshot
WorkingDirectory=/path/to/ai_code_reviewer
ExecStart=/usr/bin/make docker-backup

# Create timer: /etc/systemd/system/ai-code-reviewer-backup.timer
[Unit]
Description=Daily AI Code Reviewer Backup

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target

# Enable and start
sudo systemctl enable --now ai-code-reviewer-backup.timer
```

**Option 3: macOS LaunchAgent**

Create `~/Library/LaunchAgents/com.ai-code-reviewer.backup.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ai-code-reviewer.backup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/make</string>
        <string>docker-backup</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/ai_code_reviewer</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.ai-code-reviewer.backup.plist
```

### Backup Before Critical Operations

Always backup before:
- Upgrading the application
- Making schema changes
- Cleaning Docker volumes
- Testing new features

```bash
# Manual workflow
make docker-backup
# ... perform risky operation ...

# Or use safe upgrade (auto-backup)
make docker-upgrade
```

---

## Restore Operations

### Scenario 1: Restore to Running Container

**When to use:** Fix corrupted data, revert to previous state

```bash
# Interactive mode (recommended)
make docker-restore
```

**Interactive flow:**
```
╔════════════════════════════════════════════════╗
║   AI Code Reviewer - Database Restore         ║
╚════════════════════════════════════════════════╝

Available backups in /Users/pandi/source/ai_code_reviewer/backups:

  [1] ai_code_reviewer_20251110_164931.db (65K) - 2025-11-10 16:49:31
  [2] ai_code_reviewer_20251110_153045.db (62K) - 2025-11-10 15:30:45
  [3] ai_code_reviewer_20251109_180000.db (58K) - 2025-11-09 18:00:00

Enter backup number to restore (or 'q' to quit): 1

Selected backup: ai_code_reviewer_20251110_164931.db (65K)
Found container: a4f918ab76f2

⚠️  WARNING: This will replace the current database!

Current database will be backed up automatically before restore.

Do you want to continue? (yes/no): yes

[1/4] Creating safety backup of current database...
✓ Safety backup created: pre_restore_safety_20251110_165000.db (65K)

[2/4] Stopping application processes...
✓ Processes stopped

[3/4] Copying backup to container...
✓ Database restored

[4/4] Restarting application...
✓ Application restarted successfully

Verifying restored database...
✓ Database verified: 42 review records found

╔════════════════════════════════════════════════╗
║           Restore Complete! 🎉                ║
╚════════════════════════════════════════════════╝

Restored from: ai_code_reviewer_20251110_164931.db
Safety backup: pre_restore_safety_20251110_165000.db

Next steps:
  1. Verify data: curl http://localhost:8000/api/reviews/latest
  2. Check health: curl http://localhost:8000/health
  3. Test the UI: http://localhost:3000

If something went wrong, restore the safety backup:
  bash scripts/docker-restore.sh --file backups/pre_restore_safety_20251110_165000.db
```

### Scenario 2: Restore to Fresh Container

**When to use:** After cleaning Docker, moving to new server, disaster recovery

```bash
# 1. Build and start new container
make docker-build
make docker-run

# 2. Wait for container to initialize (5-10 seconds)
sleep 10

# 3. Restore your backup
make docker-restore
# Select backup from list

# 4. Verify data
curl http://localhost:8000/api/reviews/latest
```

**Complete example:**

```bash
# You have this backup
ls backups/
# ai_code_reviewer_20251110_164931.db (your production data)

# Clean everything
docker-compose -f docker/docker-compose.yml down -v
docker system prune -a -f

# Start fresh
make docker-build
make docker-run

# Wait for startup
echo "Waiting for container to initialize..."
sleep 10

# Restore
make docker-restore
# Choose: [1] ai_code_reviewer_20251110_164931.db

# Verify
curl -s http://localhost:8000/api/reviews/latest | python -m json.tool
```

### Scenario 3: Non-Interactive Restore (Automation)

**When to use:** Scripts, CI/CD, automated recovery

```bash
# Restore specific file without prompts
bash scripts/docker-restore.sh \
  --file backups/ai_code_reviewer_20251110_164931.db \
  --yes
```

**In a script:**

```bash
#!/bin/bash
# automated-restore.sh

set -e

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file>"
    exit 1
fi

# Start container
docker-compose -f docker/docker-compose.yml up -d

# Wait for healthy
echo "Waiting for container to be healthy..."
for i in {1..30}; do
    if curl -sf http://localhost:8000/health > /dev/null; then
        echo "Container is healthy"
        break
    fi
    sleep 2
done

# Restore
bash scripts/docker-restore.sh --file "$BACKUP_FILE" --yes

# Verify
RECORD_COUNT=$(curl -s http://localhost:8000/api/reviews/latest | jq '. | length')
echo "Restored $RECORD_COUNT records"
```

### Scenario 4: Migrate Between Servers

**When to use:** Moving to new server, disaster recovery

**On old server:**
```bash
# 1. Create backup
make docker-backup
# Output: backups/ai_code_reviewer_20251110_164931.db

# 2. Copy backup to new server
scp backups/ai_code_reviewer_20251110_164931.db user@new-server:/tmp/
```

**On new server:**
```bash
# 1. Clone repository
git clone <repo-url>
cd ai_code_reviewer

# 2. Setup environment
cp .env.example .env
vim .env  # Configure

# 3. Start container
make docker-build
make docker-run

# 4. Copy backup to backups directory
mkdir -p backups
mv /tmp/ai_code_reviewer_20251110_164931.db backups/

# 5. Restore
make docker-restore
# Select the backup

# 6. Verify
curl http://localhost:8000/api/reviews/latest
```

---

## Backup Management

### Listing Backups

```bash
# List all backups with details
ls -lht backups/

# Count backups
ls -1 backups/*.db | wc -l

# Show sizes
du -sh backups/*.db
```

### Cleanup Old Backups

Automatic cleanup keeps last 10 backups. Manual cleanup:

```bash
# Keep last 30 backups
ls -t backups/*.db | tail -n +31 | xargs rm -f

# Delete backups older than 90 days
find backups/ -name "*.db" -type f -mtime +90 -delete

# Delete specific backup
rm backups/ai_code_reviewer_20251109_180000.db
```

### Verify Backup Integrity

```bash
# Check backup file
sqlite3 backups/ai_code_reviewer_20251110_164931.db "PRAGMA integrity_check;"

# Count records in backup
sqlite3 backups/ai_code_reviewer_20251110_164931.db "SELECT COUNT(*) FROM review_records;"

# Show backup details
sqlite3 backups/ai_code_reviewer_20251110_164931.db ".tables"
```

---

## Troubleshooting

### Restore fails with "No running container"

```bash
# Start the container first
make docker-run

# Wait for it to be ready
sleep 10

# Then restore
make docker-restore
```

### Restore completed but data is missing

```bash
# Check database file size
docker exec <container> ls -lh /app/data/ai_code_reviewer.db

# Verify tables exist
docker exec <container> sqlite3 /app/data/ai_code_reviewer.db ".tables"

# Count records
docker exec <container> sqlite3 /app/data/ai_code_reviewer.db \
  "SELECT COUNT(*) FROM review_records;"

# Check application logs
docker logs <container> | grep -i "database\|migration"
```

### Safety backup to recover from failed restore

If restore went wrong, use the safety backup created automatically:

```bash
# List safety backups
ls -lt backups/pre_restore_safety_*.db

# Restore the safety backup
bash scripts/docker-restore.sh --file backups/pre_restore_safety_20251110_165000.db --yes
```

### Backup file is corrupted

```bash
# Check integrity
sqlite3 backups/backup.db "PRAGMA integrity_check;"

# If corrupted, try to recover
sqlite3 backups/backup.db ".recover" > recovered.sql
sqlite3 new_backup.db < recovered.sql
```

---

## Best Practices

### ✅ Do

- **Backup before upgrades** - Use `make docker-upgrade` (auto-backup)
- **Regular scheduled backups** - Daily at minimum for production
- **Test restores periodically** - Verify backups are working
- **Keep multiple backup versions** - At least 10 recent backups
- **Store backups off-server** - Use S3, NAS, or remote storage
- **Document backup schedule** - Team should know the process
- **Verify after restore** - Always check data integrity

### ❌ Don't

- **Don't rely on single backup** - Keep multiple versions
- **Don't skip verification** - Always test backups
- **Don't forget about migrations** - Backups include schema version
- **Don't commit backups to git** - They're in `.gitignore` for a reason
- **Don't restore without safety backup** - Script creates one automatically

---

## Advanced Topics

### Backup to Remote Storage

**AWS S3:**
```bash
# After backup
aws s3 cp backups/ai_code_reviewer_20251110_164931.db \
  s3://my-bucket/ai-code-reviewer-backups/
```

**rsync to NAS:**
```bash
# Sync entire backups directory
rsync -av backups/ user@nas:/backups/ai-code-reviewer/
```

### Encrypted Backups

```bash
# Backup with encryption
make docker-backup
gpg --symmetric --cipher-algo AES256 \
  backups/ai_code_reviewer_20251110_164931.db

# Decrypt for restore
gpg --decrypt backups/ai_code_reviewer_20251110_164931.db.gpg > \
  backups/decrypted_backup.db
bash scripts/docker-restore.sh --file backups/decrypted_backup.db
```

### Point-in-Time Recovery

For critical deployments, consider:
- WAL mode for SQLite
- PostgreSQL with WAL archiving
- Continuous backup solutions

---

## Support

- **Docker Guide**: [docs/DOCKER.md](./DOCKER.md)
- **Database Guide**: [docs/DATABASE.md](./DATABASE.md)
- **Quick Start**: [docker/README.md](../docker/README.md)
