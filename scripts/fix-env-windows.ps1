#!/usr/bin/env pwsh
# PowerShell script to fix .env file for Windows Docker
# This script converts CRLF to LF and validates the .env file

param(
    [switch]$Check,
    [switch]$Fix
)

$ErrorActionPreference = "Stop"

Write-Host "=== AI Code Reviewer - Windows .env File Fixer ===" -ForegroundColor Cyan
Write-Host ""

# Determine project root (script is in scripts/ directory)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$EnvFile = Join-Path $ProjectRoot ".env"
$EnvExampleFile = Join-Path $ProjectRoot ".env.example"

Write-Host "Project root: $ProjectRoot" -ForegroundColor Gray
Write-Host ".env file: $EnvFile" -ForegroundColor Gray
Write-Host ""

# Check if .env file exists
if (-not (Test-Path $EnvFile)) {
    Write-Host "❌ .env file not found at: $EnvFile" -ForegroundColor Red
    Write-Host ""

    if (Test-Path $EnvExampleFile) {
        Write-Host "📝 Found .env.example file. Would you like to create .env from it? (Y/N)" -ForegroundColor Yellow
        $response = Read-Host

        if ($response -eq "Y" -or $response -eq "y") {
            # Read .env.example and convert to LF
            $content = Get-Content $EnvExampleFile -Raw
            $content = $content -replace "`r`n", "`n"
            $content = $content -replace "`r", "`n"  # Handle old Mac format too

            # Write with LF endings
            [System.IO.File]::WriteAllText($EnvFile, $content, [System.Text.UTF8Encoding]::new($false))

            Write-Host "✅ Created .env file with LF line endings" -ForegroundColor Green
            Write-Host "⚠️  IMPORTANT: Edit .env and replace placeholder values with your actual configuration!" -ForegroundColor Yellow
            Write-Host ""
        }
    } else {
        Write-Host "❌ .env.example file not found. Please create .env manually." -ForegroundColor Red
    }

    exit 1
}

# Read file content
$content = Get-Content $EnvFile -Raw

# Check for line ending issues
$hasCRLF = $content -match "`r`n"
$hasCR = $content -match "`r" -and $content -notmatch "`n"

Write-Host "🔍 Checking .env file..." -ForegroundColor Cyan
Write-Host ""

# Detect line endings
if ($hasCRLF) {
    Write-Host "❌ Found CRLF (Windows) line endings - Docker needs LF (Unix)" -ForegroundColor Red
} elseif ($hasCR) {
    Write-Host "❌ Found CR (old Mac) line endings - Docker needs LF (Unix)" -ForegroundColor Red
} else {
    Write-Host "✅ Line endings: LF (Unix) - Correct!" -ForegroundColor Green
}

# Check for required variables
$requiredVars = @(
    "BITBUCKET_URL",
    "BITBUCKET_TOKEN",
    "LLM_PROVIDER",
    "LLM_API_KEY"
)

Write-Host ""
Write-Host "🔍 Checking required variables..." -ForegroundColor Cyan

$missingVars = @()
$placeholderVars = @()

foreach ($var in $requiredVars) {
    if ($content -match "(?m)^$var=(.+)$") {
        $value = $matches[1].Trim()
        if ($value -eq "" -or $value -match "your_|placeholder") {
            $placeholderVars += $var
            Write-Host "⚠️  $var is set but looks like a placeholder" -ForegroundColor Yellow
        } else {
            Write-Host "✅ $var is set" -ForegroundColor Green
        }
    } else {
        $missingVars += $var
        Write-Host "❌ $var is missing" -ForegroundColor Red
    }
}

# Check for spaces around =
Write-Host ""
Write-Host "🔍 Checking format..." -ForegroundColor Cyan

$lines = $content -split "`n"
$formatIssues = @()

foreach ($line in $lines) {
    $line = $line.Trim()
    if ($line -eq "" -or $line -match "^#") {
        continue
    }

    if ($line -match "^\s+\w+=|=\s+\w+") {
        $formatIssues += $line
        Write-Host "⚠️  Found spaces around '=' in: $line" -ForegroundColor Yellow
    }
}

if ($formatIssues.Count -eq 0) {
    Write-Host "✅ No format issues found" -ForegroundColor Green
}

# Summary
Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan

$needsFix = $hasCRLF -or $hasCR -or ($formatIssues.Count -gt 0)

if ($needsFix) {
    Write-Host "❌ Issues found that need fixing" -ForegroundColor Red

    if ($Fix -or (-not $Check)) {
        Write-Host ""
        Write-Host "🔧 Fixing .env file..." -ForegroundColor Yellow

        # Create backup
        $backupFile = "$EnvFile.backup"
        Copy-Item $EnvFile $backupFile
        Write-Host "📦 Created backup: $backupFile" -ForegroundColor Gray

        # Fix line endings
        $fixedContent = $content -replace "`r`n", "`n"
        $fixedContent = $fixedContent -replace "`r", "`n"

        # Write with LF endings and UTF-8 without BOM
        [System.IO.File]::WriteAllText($EnvFile, $fixedContent, [System.Text.UTF8Encoding]::new($false))

        Write-Host "✅ Fixed line endings to LF" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "Run with -Fix to automatically fix issues:" -ForegroundColor Yellow
        Write-Host "  .\scripts\fix-env-windows.ps1 -Fix" -ForegroundColor Gray
        Write-Host ""
    }
} else {
    Write-Host "✅ .env file format is correct for Docker" -ForegroundColor Green
    Write-Host ""
}

if ($missingVars.Count -gt 0) {
    Write-Host "⚠️  Missing required variables:" -ForegroundColor Yellow
    foreach ($var in $missingVars) {
        Write-Host "   - $var" -ForegroundColor Gray
    }
    Write-Host ""
}

if ($placeholderVars.Count -gt 0) {
    Write-Host "⚠️  Variables with placeholder values (need updating):" -ForegroundColor Yellow
    foreach ($var in $placeholderVars) {
        Write-Host "   - $var" -ForegroundColor Gray
    }
    Write-Host ""
}

# Final instructions
if ($needsFix -or $missingVars.Count -gt 0 -or $placeholderVars.Count -gt 0) {
    Write-Host "📝 Next steps:" -ForegroundColor Cyan
    if ($missingVars.Count -gt 0 -or $placeholderVars.Count -gt 0) {
        Write-Host "   1. Edit .env and set all required values" -ForegroundColor Gray
    }
    Write-Host "   2. Run: docker-compose -f docker\docker-compose.yml build" -ForegroundColor Gray
    Write-Host "   3. Run: docker-compose -f docker\docker-compose.yml up -d" -ForegroundColor Gray
    Write-Host "   4. Check logs: docker-compose -f docker\docker-compose.yml logs -f" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "🚀 Ready to deploy!" -ForegroundColor Green
    Write-Host "   Run: docker-compose -f docker\docker-compose.yml up -d" -ForegroundColor Gray
    Write-Host ""
}
