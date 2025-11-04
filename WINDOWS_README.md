# Windows Setup - Quick Start

If you're deploying on Windows and seeing configuration errors in Docker, follow this quick guide.

## Problem

Your Docker container keeps restarting with errors like:
```
ERROR - Failed to start server: Configuration errors: BITBUCKET_TOKEN is required, LLM_API_KEY is required
```

Even though your `.env` file exists and has all the values.

## Root Cause

**Windows line endings (CRLF) are incompatible with Docker containers (which expect LF).**

This is the #1 issue Windows users face with Docker and `.env` files.

## Quick Fix (3 Steps)

### Step 1: Fix Your .env File

**Option A: Automated Script (Recommended)**
```powershell
# Run from project root
.\scripts\fix-env-windows.ps1 -Fix
```

**Option B: Manual Fix in VS Code**
1. Open `.env` file
2. Look at bottom right corner - it will say "CRLF"
3. Click on "CRLF"
4. Select "LF" from dropdown
5. Save file (Ctrl+S)

**Option C: Manual Fix in PowerShell**
```powershell
(Get-Content .env -Raw) -replace "`r`n", "`n" | Set-Content .env -NoNewline
```

### Step 2: Rebuild Container
```powershell
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml build
docker-compose -f docker/docker-compose.yml up -d
```

### Step 3: Verify It Works
```powershell
# Check logs - should NOT see configuration errors
docker-compose -f docker/docker-compose.yml logs -f ai-code-reviewer
```

## Prevent This Issue

Configure Git to always use LF line endings:
```bash
git config --global core.autocrlf input
```

Then re-clone the repository or re-checkout the `.env` file.

## Complete Documentation

For detailed troubleshooting, see:
- **[Windows Docker Setup Guide](docs/WINDOWS_DOCKER_SETUP.md)** - Comprehensive guide with all solutions
- **[CLAUDE.md](CLAUDE.md)** - Full project documentation

## Still Not Working?

### Check Your .env File Format
```powershell
# Verify line endings are LF (not CRLF)
.\scripts\fix-env-windows.ps1 -Check
```

### Use Windows-Specific Compose File
```powershell
docker-compose -f docker/docker-compose.windows.yml up -d
```

### Manually Set Variables (Last Resort)
```powershell
# Set environment variables in PowerShell
$env:BITBUCKET_URL="https://your-bitbucket.com"
$env:BITBUCKET_TOKEN="your_token"
$env:LLM_API_KEY="your_api_key"

# Then run docker-compose
docker-compose -f docker/docker-compose.yml up -d
```

## Common Mistakes

❌ **Wrong:**
- `.env` file with CRLF line endings (Windows default)
- Spaces around equals: `KEY = value`
- Quotes around values: `KEY="value"`

✅ **Correct:**
- `.env` file with LF line endings (Unix)
- No spaces: `KEY=value`
- No quotes: `KEY=value`

## Need Help?

See the comprehensive [Windows Docker Setup Guide](docs/WINDOWS_DOCKER_SETUP.md) for:
- Detailed explanations
- Multiple solution methods
- Verification steps
- Troubleshooting checklist
- Docker Desktop configuration
- WSL2 setup

## Quick Links

- Frontend UI: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
