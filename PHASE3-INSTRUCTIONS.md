# Phase 3: Documentation Updates - Setup Instructions

This guide will help you create all Phase 3 GitHub issues automatically using the provided script.

## Prerequisites

### Required on Your Mac
- **curl**: Already installed on macOS
- **jq**: JSON processor (optional but recommended)
  ```bash
  brew install jq
  ```
  (If jq is not installed, the script will still work but may show warnings)

### GitHub Personal Access Token

You need a GitHub Personal Access Token with `repo` permissions.

#### Create a Token:

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Give it a name: `AI Code Reviewer - Issue Creation`
4. Select scopes:
   - ✅ **repo** (Full control of private repositories)
     - This includes: repo:status, repo_deployment, public_repo, repo:invite, security_events
5. Click **"Generate token"**
6. **Copy the token immediately** (you won't see it again!)

**Security Note**: Keep your token secure. Don't commit it to git or share it publicly.

---

## Option 1: Run the Script (Recommended - Fastest)

### Step 1: Download Files to Your Mac

If you're working in Claude Code, the files are already created. You need to get them to your Mac:

```bash
# If using git, commit and pull:
git add phase3-issues.md create-phase3-issues.sh
git commit -m "Add Phase 3 issue creation script"
git push

# On your Mac, pull the changes:
git pull
```

**OR** copy the files manually from the workspace to your Mac.

### Step 2: Run the Script

```bash
# Navigate to repository directory
cd /path/to/ai_code_reviewer

# Run the script
./create-phase3-issues.sh
```

### Step 3: Follow the Prompts

The script will ask for:

1. **GitHub Personal Access Token**:
   ```
   Enter your GitHub Personal Access Token: [paste token here]
   ```

2. **Repository Information** (auto-detected from git):
   ```
   Detected repository: pandiarajan-src/ai_code_reviewer
   Is this correct? (y/n): y
   ```
   If not auto-detected, you'll be prompted to enter:
   - Repository owner: `pandiarajan-src` (or your GitHub username)
   - Repository name: `ai_code_reviewer`

3. **Issue Assignment** (optional):
   ```
   Assign all issues to a user? (Enter username or leave blank): pandiarajan-src
   ```

### Step 4: Wait for Completion

The script will:
1. ✓ Test GitHub API access
2. ✓ Create 9 labels (phase-3, documentation, priorities, effort levels)
3. ✓ Create milestone "Phase 3: Documentation Updates"
4. ✓ Create 1 parent issue + 8 sub-issues
5. ✓ Link all sub-issues to parent issue

**Time**: ~30-60 seconds

### Step 5: View Your Issues

The script will output:
```
✓ All issues created successfully!

Summary:
  - Parent issue: #123
  - Sub-issues: #124, #125, #126, #127, #128, #129, #130, #131

View issues: https://github.com/pandiarajan-src/ai_code_reviewer/issues
View milestone: https://github.com/pandiarajan-src/ai_code_reviewer/milestone/1
```

Click the links to view your issues!

---

## Option 2: Manual Creation (Slower - 10-15 minutes)

If you prefer to create issues manually or the script doesn't work:

### Step 1: Create Labels

Go to: `https://github.com/YOUR_USERNAME/ai_code_reviewer/labels/new`

Create these labels:

| Name | Color | Description |
|------|-------|-------------|
| `phase-3` | `0075ca` (blue) | Phase 3: Documentation Updates |
| `documentation` | `0075ca` (blue) | Documentation improvements |
| `security` | `d73a4a` (red) | Security related |
| `high-priority` | `d93f0b` (orange) | High priority issue |
| `medium-priority` | `fbca04` (yellow) | Medium priority issue |
| `low-priority` | `c5def5` (light blue) | Low priority issue |
| `effort:small` | `c2e0c6` (light green) | Small effort (< 2 hours) |
| `effort:medium` | `bfd4f2` (light blue) | Medium effort (2-4 hours) |
| `effort:large` | `f9d0c4` (light red) | Large effort (> 4 hours) |

### Step 2: Create Milestone

Go to: `https://github.com/YOUR_USERNAME/ai_code_reviewer/milestones/new`

- **Title**: `Phase 3: Documentation Updates`
- **Description**: `Fix outdated documentation to match current codebase structure`
- Click **"Create milestone"**

### Step 3: Create Issues

Open the file: `phase3-issues.md`

For each issue section:
1. Go to: `https://github.com/YOUR_USERNAME/ai_code_reviewer/issues/new`
2. Copy the **Title** from the markdown
3. Copy the **Body** from the markdown
4. Add **Labels** as specified
5. Set **Milestone** to "Phase 3: Documentation Updates"
6. Assign to yourself
7. Click **"Submit new issue"**

Create in this order:
1. Parent issue first
2. Then all 8 sub-issues
3. Edit parent issue to add actual sub-issue numbers

---

## Troubleshooting

### "gh: command not found"
This is expected! The script uses `curl` directly, not `gh` CLI.

### "Failed to access repository"
- Check your GitHub token has `repo` permissions
- Verify repository owner and name are correct
- Ensure repository exists and you have access

### "Failed to create label: already exists"
This is fine! The script will skip existing labels.

### "jq: command not found"
The script will work without `jq`, but install it for better formatting:
```bash
brew install jq
```

### Script Hangs or Times Out
- Check your internet connection
- Verify GitHub.com is accessible
- Try again in a few minutes (GitHub rate limits)

### Permission Denied When Running Script
```bash
chmod +x create-phase3-issues.sh
```

---

## After Creating Issues

### View All Phase 3 Issues

1. Go to: `https://github.com/YOUR_USERNAME/ai_code_reviewer/issues`
2. Filter by label: `phase-3`
3. Or view by milestone: Click "Milestones" tab

### Next Steps

Once issues are created, return to Claude Code and I will:
1. Work through each issue systematically
2. Fix the documentation files
3. Commit changes with proper issue references
4. Close issues as they're completed

### Tracking Progress

Watch the parent issue checklist to see overall progress:
- [ ] Unchecked = Not started
- [x] Checked = Completed

---

## Security Note

### Token Storage

The script does NOT store your GitHub token. It's only used during execution.

However, your shell history may contain the token if you export it. To clear:

```bash
# Clear bash history
history -c

# Or avoid history by starting command with a space:
 export GITHUB_TOKEN=your_token
./create-phase3-issues.sh
```

### Best Practice

Use an environment variable:

```bash
# Set token for this session only
export GITHUB_TOKEN=your_token_here

# Run script (will use GITHUB_TOKEN env var)
./create-phase3-issues.sh

# Unset when done
unset GITHUB_TOKEN
```

---

## Need Help?

If you encounter issues:
1. Check the troubleshooting section above
2. Verify your GitHub token permissions
3. Try manual creation (Option 2)
4. Ask in Claude Code for assistance

---

**Ready?** Run `./create-phase3-issues.sh` and let's get started! 🚀
