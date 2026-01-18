# Phase 1: Critical Security Fixes - Setup Instructions

This guide will help you create all Phase 1 GitHub issues for critical security vulnerabilities.

## 📋 What Gets Fixed in Phase 1

**Critical security vulnerabilities that must be addressed before production:**

1. **Webhook Signature Verification** (CRITICAL)
   - Enable authentication for webhook endpoints
   - Prevent unauthorized code review triggers
   - Stop DoS attacks and LLM cost exploitation

2. **CORS Policy Restriction** (CRITICAL)
   - Restrict allowed origins to prevent CSRF attacks
   - Block unauthorized domain access
   - Protect user sessions and credentials

3. **Rate Limiting** (CRITICAL)
   - Prevent DoS attacks via unlimited requests
   - Protect expensive LLM endpoints
   - Control resource consumption

4. **SSL Verification** (HIGH)
   - Make SSL verification configurable
   - Support custom CA certificates
   - Prevent MITM attacks

---

## 🚀 Quick Start

### Option 1: Run the Script (Recommended)

```bash
# Pull latest changes (if not already done)
git pull

# Run the script
./create-phase1-issues.sh
```

Follow the prompts to create all Phase 1 issues automatically!

---

## 📖 Detailed Instructions

### Prerequisites

Same as Phase 3:
- **curl**: Already installed
- **jq**: Optional but recommended (`brew install jq`)
- **GitHub Personal Access Token** with `repo` permissions

If you created Phase 3 issues, you can **reuse the same token**.

### Step 1: Get Your GitHub Token

If you don't have a token from Phase 3:

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Name it: `AI Code Reviewer - Phase 1 Security Fixes`
4. Select scopes: ✅ **repo** (Full control)
5. Generate and **copy the token**

### Step 2: Run the Script

```bash
# Navigate to repository
cd /path/to/ai_code_reviewer

# Run the script
./create-phase1-issues.sh
```

### Step 3: Provide Information

The script will ask for:

1. **GitHub Token**: Paste your token (from Step 1 or Phase 3)
2. **Repository**: Auto-detected as `pandiarajan-src/ai_code_reviewer`
3. **Assignee**: Your GitHub username (default: repository owner)

### Step 4: Wait for Completion

The script will:
- ✓ Create 7 labels (phase-1, security, critical, priorities, efforts)
- ✓ Create milestone "Phase 1: Critical Security Fixes"
- ✓ Create 1 parent issue + 4 sub-issues
- ✓ Link all issues together

**Time**: ~30-60 seconds

### Step 5: View Your Issues

```
✓ Created 5 issues total:
  - Parent issue: #<number>
  - Sub-issues: #<number>, #<number>, #<number>, #<number>

View issues: https://github.com/pandiarajan-src/ai_code_reviewer/issues
```

---

## 📋 What Gets Created

### Labels (7 total)

| Label | Color | Purpose |
|-------|-------|---------|
| `phase-1` | Red | Phase 1 tracking |
| `security` | Red | Security issues |
| `critical` | Dark red | Immediate action required |
| `high-priority` | Orange | High priority |
| `effort:small` | Green | < 2 hours |
| `effort:medium` | Blue | 2-4 hours |
| `effort:large` | Pink | > 4 hours |

### Milestone

**"Phase 1: Critical Security Fixes"**
- Description: Address critical security vulnerabilities before production deployment
- Due date: None (work at your own pace)

### Issues (5 total)

#### Parent Issue
`[Phase 1] Critical Security Fixes - Production Readiness`
- Tracks overall progress
- Lists all 4 sub-issues
- Priority: CRITICAL

#### Sub-Issue 1: Webhook Signature Verification
- **Severity**: CRITICAL
- **Effort**: Medium (3-4 hours)
- **File**: `src/ai_code_reviewer/api/routes/webhook.py`
- **Fix**: Uncomment signature verification, add config

#### Sub-Issue 2: CORS Policy
- **Severity**: CRITICAL (HIGH)
- **Effort**: Small (2 hours)
- **File**: `src/ai_code_reviewer/api/app.py`
- **Fix**: Make CORS origins configurable

#### Sub-Issue 3: Rate Limiting
- **Severity**: CRITICAL
- **Effort**: Large (6-8 hours)
- **Files**: All route files
- **Fix**: Install slowapi, apply rate limits

#### Sub-Issue 4: SSL Verification
- **Severity**: HIGH
- **Effort**: Medium (3-4 hours)
- **File**: `src/ai_code_reviewer/api/clients/bitbucket_client.py`
- **Fix**: Make SSL verification configurable

---

## ⚙️ Environment Variables

You can set the GitHub token as an environment variable:

```bash
# Set token for this session only
export GITHUB_TOKEN=your_token_here

# Run script (will use GITHUB_TOKEN env var)
./create-phase1-issues.sh

# Unset when done
unset GITHUB_TOKEN
```

---

## 🔒 Security Note

Your GitHub token is only used during script execution and is **not stored**. However:

- Shell history may contain the token
- To clear: `history -c`
- Or start command with space to avoid history: ` export GITHUB_TOKEN=...`

---

## 🆘 Troubleshooting

### "Failed to access repository"
- Verify token has `repo` permissions
- Confirm repository owner and name are correct
- Check repository exists and you have access

### "Label already exists"
- This is normal if you ran Phase 3 script
- Some labels are shared between phases
- Script will skip and continue

### "Milestone already exists"
- Script will find and reuse existing milestone
- This is expected behavior

### Script hangs or times out
- Check internet connection
- Verify GitHub.com is accessible
- Wait a few minutes (rate limits) and try again

---

## 📊 Next Steps After Creating Issues

Once Phase 1 issues are created:

1. **Review the issues** in GitHub
2. **Return to Claude Code** and say: "Phase 1 issues created"
3. **Claude will start fixing** each security vulnerability systematically
4. **Track progress** via the parent issue checklist

---

## 🎯 Phase 1 Timeline

**Total Estimated Effort**: 1 week (14-18 hours)

- Issue 1 (Webhook Auth): 3-4 hours
- Issue 2 (CORS): 2 hours
- Issue 3 (Rate Limiting): 6-8 hours
- Issue 4 (SSL Verification): 3-4 hours

Each issue includes:
- Implementation
- Testing
- Documentation
- Commit and push

---

## ✅ Success Criteria

After Phase 1 is complete:

- [ ] Webhooks require valid signatures
- [ ] CORS blocks unauthorized origins
- [ ] Rate limiting prevents excessive requests
- [ ] SSL verification is configurable
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Security warnings removed from README

---

**Ready?** Run `./create-phase1-issues.sh` and then come back to start fixing! 🚀
