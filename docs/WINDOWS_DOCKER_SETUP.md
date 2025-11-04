# Windows Docker Setup Guide

This guide helps you resolve `.env` file loading issues when running the AI Code Reviewer in Docker on Windows.

## Common Issue: Environment Variables Not Loading

**Symptoms:**
```
ERROR - Failed to start server: Configuration errors: BITBUCKET_TOKEN is required, LLM_API_KEY is required
```

The container keeps restarting with configuration errors even though you have a `.env` file.

## Root Causes

1. **Line Endings (CRLF vs LF)** - Windows uses CRLF (`\r\n`) but Linux containers expect LF (`\n`)
2. **File Encoding** - `.env` file should be UTF-8 without BOM
3. **Path Resolution** - Windows path separators differ from Linux
4. **File Location** - `.env` file must be in the correct location

## Solutions

### Solution 1: Fix Line Endings (Recommended)

**Option A: Using Git Configuration**
```bash
# Configure Git to checkout LF line endings on Windows
git config --global core.autocrlf input

# Re-checkout the repository
cd /path/to/ai_code_reviewer
rm .env
git checkout .env.example
cp .env.example .env
# Edit .env with your values
```

**Option B: Using PowerShell**
```powershell
# Convert existing .env file from CRLF to LF
cd C:\path\to\ai_code_reviewer
(Get-Content .env -Raw) -replace "`r`n", "`n" | Set-Content .env -NoNewline
```

**Option C: Using Git Bash/WSL**
```bash
# Install dos2unix (WSL)
sudo apt-get install dos2unix

# Convert line endings
dos2unix .env

# Or using sed
sed -i 's/\r$//' .env
```

**Option D: Using VS Code**
1. Open `.env` file
2. Look at the bottom right corner for "CRLF" or "LF"
3. Click on "CRLF"
4. Select "LF" from the dropdown
5. Save the file (Ctrl+S)

### Solution 2: Verify .env File Location

The `.env` file should be in the **root** of the project:

```
ai_code_reviewer/
├── .env              ← HERE (root directory)
├── docker/
│   ├── docker-compose.yml
│   └── Dockerfile
├── src/
└── ...
```

**Check from PowerShell:**
```powershell
# Navigate to project root
cd C:\path\to\ai_code_reviewer

# Verify .env exists
Test-Path .env  # Should return True

# Check content
Get-Content .env
```

### Solution 3: Use Windows-Specific docker-compose File

Use the Windows-optimized configuration:

```powershell
# From project root
docker-compose -f docker/docker-compose.windows.yml up -d
```

### Solution 4: Pass Environment Variables Directly (Workaround)

If `.env` file still doesn't work, pass variables directly:

**Create a PowerShell script `docker-run.ps1`:**
```powershell
# Load .env file manually
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}

# Run docker-compose
docker-compose -f docker/docker-compose.yml up -d
```

**Or use docker-compose with explicit variables:**
```powershell
# Set environment variables in PowerShell session
$env:BITBUCKET_URL="https://your-bitbucket-server.com"
$env:BITBUCKET_TOKEN="your_token"
$env:LLM_PROVIDER="openai"
$env:LLM_API_KEY="your_api_key"

# Run docker-compose (it will use environment variables)
docker-compose -f docker/docker-compose.yml up -d
```

### Solution 5: Create .env from PowerShell

```powershell
# Create .env with proper LF line endings
@"
BITBUCKET_URL=https://your-bitbucket-server.com
BITBUCKET_TOKEN=your_token
LLM_PROVIDER=openai
LLM_API_KEY=your_api_key
LLM_ENDPOINT=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4o
OLLAMA_HOST=http://localhost:11434
WEBHOOK_SECRET=your_secret
LOGIC_APP_EMAIL_URL=https://your-logic-app-url
LOGIC_APP_FROM_EMAIL=pandiarajans@test.com
EMAIL_OPTOUT=true
HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=3000
LOG_LEVEL=INFO
"@ -replace "`r`n", "`n" | Out-File -FilePath .env -Encoding utf8 -NoNewline
```

## Verification Steps

### 1. Check .env File Format
```powershell
# Check line endings (should show LF, not CRLF)
Get-Content .env -Raw | Select-String "`r`n"
# No output = LF (good), output = CRLF (needs fixing)

# Check encoding (should be UTF-8)
file .env  # In Git Bash/WSL
```

### 2. Test Environment Variable Loading
```powershell
# From project root
docker-compose -f docker/docker-compose.yml config
# This shows the resolved configuration with environment variables
# Verify that BITBUCKET_TOKEN and LLM_API_KEY show your actual values
```

### 3. Check Container Logs
```powershell
# View logs
docker-compose -f docker/docker-compose.yml logs ai-code-reviewer

# Follow logs in real-time
docker-compose -f docker/docker-compose.yml logs -f ai-code-reviewer

# Should NOT see "Configuration errors: BITBUCKET_TOKEN is required"
```

### 4. Verify Environment Variables Inside Container
```powershell
# Connect to running container
docker exec -it docker-ai-code-reviewer-1 sh

# Inside container, check environment variables
env | grep BITBUCKET_TOKEN
env | grep LLM_API_KEY
# Should show your actual values, not empty or placeholder values
```

## Complete Setup Process for Windows

```powershell
# 1. Clone repository
git clone https://github.com/your-org/ai_code_reviewer.git
cd ai_code_reviewer

# 2. Configure Git for LF line endings (important!)
git config core.autocrlf input

# 3. Create .env from example with LF line endings
(Get-Content .env.example -Raw) -replace "`r`n", "`n" | Set-Content .env -NoNewline

# 4. Edit .env with your configuration
code .env  # Or notepad .env
# Make sure to select LF line endings in your editor!

# 5. Build and run
docker-compose -f docker/docker-compose.yml build
docker-compose -f docker/docker-compose.yml up -d

# 6. Check logs
docker-compose -f docker/docker-compose.yml logs -f

# 7. Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Troubleshooting Checklist

- [ ] `.env` file exists in project root (not in `docker/` subdirectory)
- [ ] `.env` file has LF line endings (not CRLF)
- [ ] `.env` file is UTF-8 encoded without BOM
- [ ] All required variables are set (BITBUCKET_TOKEN, LLM_API_KEY)
- [ ] No spaces around `=` in `.env` (use `KEY=value`, not `KEY = value`)
- [ ] No quotes needed for values in `.env` (use `KEY=value`, not `KEY="value"`)
- [ ] Docker Desktop is running on Windows
- [ ] Git is configured with `core.autocrlf input`

## Common Mistakes

**❌ Wrong:**
```bash
# In .env (with spaces)
BITBUCKET_TOKEN = your_token

# Or with quotes
BITBUCKET_TOKEN="your_token"

# Or CRLF line endings (invisible but causes issues)
```

**✅ Correct:**
```bash
# In .env (no spaces, no quotes, LF line endings)
BITBUCKET_TOKEN=your_token
LLM_API_KEY=sk-your-api-key
```

## Still Having Issues?

If you've tried all solutions and still see configuration errors:

1. **Use explicit environment variables:**
   ```powershell
   # Create docker-compose.override.yml
   @"
   version: '3.8'
   services:
     ai-code-reviewer:
       environment:
         - BITBUCKET_TOKEN=your_actual_token
         - LLM_API_KEY=your_actual_api_key
   "@ | Out-File -FilePath docker/docker-compose.override.yml -Encoding utf8
   ```

2. **Check Docker Desktop settings:**
   - Open Docker Desktop
   - Go to Settings → Resources → File Sharing
   - Ensure your project directory is shared with Docker

3. **Try WSL2 backend:**
   - Docker Desktop → Settings → General
   - Enable "Use the WSL 2 based engine"
   - This provides better Linux compatibility on Windows

## Additional Resources

- [Docker Compose Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [Line Endings in Git](https://docs.github.com/en/get-started/getting-started-with-git/configuring-git-to-handle-line-endings)
- [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
