#!/bin/bash

#############################################################
# GitHub Issues Creator for Phase 3: Documentation Updates
#############################################################
#
# This script creates GitHub issues via REST API
# Requires: curl, jq (optional), GitHub Personal Access Token
#
# Usage:
#   ./create-phase3-issues.sh
#
# The script will prompt for:
#   - GitHub Personal Access Token
#   - Repository owner (username or org)
#   - Repository name
#
#############################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to make GitHub API calls
github_api() {
    local method=$1
    local endpoint=$2
    local data=$3

    local response
    response=$(curl -s -X "$method" \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        -H "Content-Type: application/json" \
        "https://api.github.com/$endpoint" \
        ${data:+-d "$data"})

    echo "$response"
}

# Parse repository URL
get_repo_info() {
    local git_url
    git_url=$(git config --get remote.origin.url 2>/dev/null || echo "")

    if [[ $git_url =~ github.com[:/]([^/]+)/([^/.]+) ]]; then
        REPO_OWNER="${BASH_REMATCH[1]}"
        REPO_NAME="${BASH_REMATCH[2]}"
        return 0
    fi
    return 1
}

# Welcome message
echo ""
echo "=========================================="
echo "  GitHub Issues Creator - Phase 3"
echo "=========================================="
echo ""

# Get GitHub token
if [ -z "$GITHUB_TOKEN" ]; then
    print_info "GitHub Personal Access Token required"
    echo ""
    echo "To create a token:"
    echo "1. Go to: https://github.com/settings/tokens"
    echo "2. Click 'Generate new token (classic)'"
    echo "3. Select scopes: 'repo' (full control)"
    echo "4. Copy the generated token"
    echo ""
    read -sp "Enter your GitHub Personal Access Token: " GITHUB_TOKEN
    echo ""
    echo ""
fi

if [ -z "$GITHUB_TOKEN" ]; then
    print_error "GitHub token is required"
    exit 1
fi

# Try to get repository info from git
if get_repo_info; then
    print_info "Detected repository: $REPO_OWNER/$REPO_NAME"
    read -p "Is this correct? (y/n): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        REPO_OWNER=""
        REPO_NAME=""
    fi
fi

# Get repository owner if not detected
if [ -z "$REPO_OWNER" ]; then
    read -p "Enter repository owner (username or org): " REPO_OWNER
fi

# Get repository name if not detected
if [ -z "$REPO_NAME" ]; then
    read -p "Enter repository name: " REPO_NAME
fi

echo ""
print_info "Creating issues in: $REPO_OWNER/$REPO_NAME"
echo ""

# Test API access
print_info "Testing GitHub API access..."
test_response=$(github_api "GET" "repos/$REPO_OWNER/$REPO_NAME" "")
if echo "$test_response" | grep -q '"message"'; then
    print_error "Failed to access repository"
    echo "$test_response"
    exit 1
fi
print_success "API access verified"
echo ""

# Get current username
GITHUB_USER=$(github_api "GET" "user" "" | grep -o '"login": "[^"]*' | cut -d'"' -f4)
print_info "Authenticated as: $GITHUB_USER"
echo ""

# Create labels
print_info "Creating labels..."

create_label() {
    local name=$1
    local color=$2
    local description=$3

    # Check if label exists
    existing=$(github_api "GET" "repos/$REPO_OWNER/$REPO_NAME/labels/$name" "")
    if echo "$existing" | grep -q '"name"'; then
        print_warning "Label '$name' already exists"
        return 0
    fi

    # Create label
    local data="{\"name\":\"$name\",\"color\":\"$color\",\"description\":\"$description\"}"
    response=$(github_api "POST" "repos/$REPO_OWNER/$REPO_NAME/labels" "$data")

    if echo "$response" | grep -q '"name"'; then
        print_success "Created label: $name"
    else
        print_error "Failed to create label: $name"
    fi
}

create_label "phase-3" "0075ca" "Phase 3: Documentation Updates"
create_label "documentation" "0075ca" "Documentation improvements"
create_label "security" "d73a4a" "Security related"
create_label "high-priority" "d93f0b" "High priority issue"
create_label "medium-priority" "fbca04" "Medium priority issue"
create_label "low-priority" "c5def5" "Low priority issue"
create_label "effort:small" "c2e0c6" "Small effort (< 2 hours)"
create_label "effort:medium" "bfd4f2" "Medium effort (2-4 hours)"
create_label "effort:large" "f9d0c4" "Large effort (> 4 hours)"

echo ""

# Create milestone
print_info "Creating milestone..."

milestone_data='{
  "title": "Phase 3: Documentation Updates",
  "description": "Fix outdated documentation to match current codebase structure",
  "due_on": null
}'

milestone_response=$(github_api "POST" "repos/$REPO_OWNER/$REPO_NAME/milestones" "$milestone_data")
MILESTONE_NUMBER=$(echo "$milestone_response" | grep -o '"number": [0-9]*' | head -1 | cut -d' ' -f2)

if [ -n "$MILESTONE_NUMBER" ]; then
    print_success "Created milestone #$MILESTONE_NUMBER"
else
    # Milestone might already exist, try to get it
    milestones=$(github_api "GET" "repos/$REPO_OWNER/$REPO_NAME/milestones" "")
    MILESTONE_NUMBER=$(echo "$milestones" | grep -B2 '"title": "Phase 3: Documentation Updates"' | grep '"number"' | grep -o '[0-9]*' | head -1)
    if [ -n "$MILESTONE_NUMBER" ]; then
        print_warning "Milestone already exists: #$MILESTONE_NUMBER"
    else
        print_error "Failed to create or find milestone"
        MILESTONE_NUMBER=""
    fi
fi

echo ""

# Function to create an issue
create_issue() {
    local title=$1
    local body=$2
    local labels=$3
    local assignee=$4

    # Escape body for JSON
    body=$(echo "$body" | jq -Rs .)

    local issue_data="{
      \"title\": \"$title\",
      \"body\": $body,
      \"labels\": [$labels]"

    if [ -n "$MILESTONE_NUMBER" ]; then
        issue_data="$issue_data, \"milestone\": $MILESTONE_NUMBER"
    fi

    if [ -n "$assignee" ]; then
        issue_data="$issue_data, \"assignees\": [\"$assignee\"]"
    fi

    issue_data="$issue_data}"

    response=$(github_api "POST" "repos/$REPO_OWNER/$REPO_NAME/issues" "$issue_data")
    issue_number=$(echo "$response" | grep -o '"number": [0-9]*' | head -1 | cut -d' ' -f2)

    echo "$issue_number"
}

# Ask for assignee
read -p "Assign all issues to a user? (Enter username or leave blank): " ASSIGNEE
if [ -z "$ASSIGNEE" ]; then
    ASSIGNEE="$REPO_OWNER"
fi

echo ""
print_info "Creating issues (this may take a minute)..."
echo ""

# Array to store issue numbers
declare -a issue_numbers

# Create Parent Issue
print_info "[1/9] Creating parent issue..."

parent_body='## Overview
Comprehensive documentation audit and fixes to ensure all documentation matches the current codebase structure and functionality.

## Background
Recent refactoring moved core modules from `ai_code_reviewer.core.*` to `ai_code_reviewer.api.core.*`, but documentation was not updated. Multiple docs still reference old paths, causing confusion for developers.

## Objectives
- Fix all outdated module import paths
- Add prominent security warnings about disabled features
- Improve database persistence documentation
- Enhance frontend documentation visibility
- Validate all cross-references and links

## Sub-Issues Checklist
- [ ] Fix outdated import paths in deployment.md
- [ ] Fix outdated import paths in development.md
- [ ] Add security warnings to README and CLAUDE.md
- [ ] Update database persistence documentation
- [ ] Improve frontend documentation visibility
- [ ] Fix environment variable defaults table
- [ ] Add webhook payload documentation references
- [ ] Validate all internal links and cross-references

## Success Criteria
- [ ] All documentation uses correct module paths
- [ ] Security warnings are prominent and clear
- [ ] All commands in docs have been tested and work
- [ ] All internal links resolve correctly
- [ ] Database features are properly documented

## Estimated Effort
2-3 days

## Priority
High - Prevents confusion and wasted developer time'

parent_number=$(create_issue \
    "[Phase 3] Documentation Updates - Fix Outdated Information" \
    "$parent_body" \
    '"phase-3","documentation","high-priority"' \
    "$ASSIGNEE")

if [ -n "$parent_number" ]; then
    print_success "Created parent issue #$parent_number"
    PARENT_ISSUE=$parent_number
else
    print_error "Failed to create parent issue"
    exit 1
fi

echo ""

# Sub-Issue 1: deployment.md
print_info "[2/9] Creating issue: Fix deployment.md..."

issue1_body="## Problem
\`docs/deployment.md\` references the old module structure (\`ai_code_reviewer.main\`) instead of the current structure (\`ai_code_reviewer.api.main\`). This causes ModuleNotFoundError for developers following the documentation.

## Files Affected
- \`docs/deployment.md\`

## Lines to Fix
- Line 100: Development Setup section
- Line 305: Systemd Service ExecStart command
- Line 870: Debug Mode section

## Current State (❌ WRONG)
\`\`\`bash
python -m ai_code_reviewer.main
\`\`\`

## Expected State (✅ CORRECT)
\`\`\`bash
python -m ai_code_reviewer.api.main
\`\`\`

## Impact
- **User Impact**: HIGH - Developers get immediate errors when following docs
- **Frequency**: Every new developer setup
- **Time Wasted**: 15-30 minutes troubleshooting per developer

## Testing Checklist
- [ ] Verify command works: \`python -m ai_code_reviewer.api.main\`
- [ ] Check all occurrences in file are fixed
- [ ] Verify systemd service example is correct
- [ ] Test that debug mode instructions work

## Related Issues
- Parent: #$PARENT_ISSUE"

issue1=$(create_issue \
    "[Phase 3][High] Fix outdated import paths in deployment.md" \
    "$issue1_body" \
    '"phase-3","documentation","high-priority","effort:medium"' \
    "$ASSIGNEE")

print_success "Created issue #$issue1"
issue_numbers+=($issue1)

# Sub-Issue 2: development.md
print_info "[3/9] Creating issue: Fix development.md..."

issue2_body="## Problem
\`docs/development.md\` contains outdated module import examples that reference the old structure.

## Files Affected
- \`docs/development.md\`

## Lines to Fix
- Line 62: \"Running the Development Server\" section
- Lines 319-320: \"Troubleshooting Import Errors\" section

## Current State (❌ WRONG)
\`\`\`bash
python -m ai_code_reviewer.main
from ai_code_reviewer.core.config import Config
\`\`\`

## Expected State (✅ CORRECT)
\`\`\`bash
python -m ai_code_reviewer.api.main
from ai_code_reviewer.api.core.config import Config
\`\`\`

## Testing Checklist
- [ ] Verify server start command works
- [ ] Test import statements in Python REPL
- [ ] Check troubleshooting section accuracy
- [ ] Ensure no other outdated imports in file

## Related Issues
- Parent: #$PARENT_ISSUE"

issue2=$(create_issue \
    "[Phase 3][High] Fix outdated import paths in development.md" \
    "$issue2_body" \
    '"phase-3","documentation","high-priority","effort:small"' \
    "$ASSIGNEE")

print_success "Created issue #$issue2"
issue_numbers+=($issue2)

# Sub-Issue 3: Security warnings
print_info "[4/9] Creating issue: Add security warnings..."

issue3_body="## Problem
Critical security features are currently **disabled by default** in the codebase, but there are no prominent warnings in the main documentation files. This creates a false sense of security for users deploying to production.

## Security Issues Not Documented
1. **Webhook signature verification is commented out** (\`webhook.py:53-56\`)
2. **SSL verification disabled for Bitbucket** (\`bitbucket_client.py:31,53\`)
3. **CORS allows all origins** (\`app.py:68-74\`)
4. **No rate limiting** on any endpoints
5. **No API authentication** required

## Files to Update
- \`README.md\` - Add security warning section after \"Key Features\"
- \`CLAUDE.md\` - Add to \"Code Standards\" section

## Impact
- **Current State**: Users may unknowingly deploy insecure systems to production
- **After Fix**: Clear visibility of security posture, informed decisions
- **Prevents**: Security incidents, data breaches, unauthorized access

## Related Issues
- Parent: #$PARENT_ISSUE
- Blocks: Phase 1 security fixes (provides visibility)"

issue3=$(create_issue \
    "[Phase 3][High] Add security warnings to README and CLAUDE.md" \
    "$issue3_body" \
    '"phase-3","documentation","security","high-priority","effort:medium"' \
    "$ASSIGNEE")

print_success "Created issue #$issue3"
issue_numbers+=($issue3)

# Sub-Issue 4: Database documentation
print_info "[5/9] Creating issue: Update database docs..."

issue4_body="## Problem
The README doesn't prominently feature the database persistence functionality. Users may not realize that all code reviews are automatically saved with complete metadata.

## Files to Update
- \`README.md\` - Key Features section
- \`README.md\` - Add \"Review History & Database\" section

## Proposed Changes
- Add database features to Key Features list
- Create new section documenting database functionality
- Document API endpoints for querying reviews
- Include db_helper.py commands

## Impact
- Better visibility of database features
- Users understand review data is not ephemeral
- Clear documentation of API endpoints

## Related Issues
- Parent: #$PARENT_ISSUE"

issue4=$(create_issue \
    "[Phase 3][Medium] Update database persistence documentation in README" \
    "$issue4_body" \
    '"phase-3","documentation","medium-priority","effort:small"' \
    "$ASSIGNEE")

print_success "Created issue #$issue4"
issue_numbers+=($issue4)

# Sub-Issue 5: Frontend docs
print_info "[6/9] Creating issue: Improve frontend docs..."

issue5_body="## Problem
The web UI frontend features are buried deep in the documentation structure and not visible in the README overview. Users may not know a full web interface exists.

## Files to Update
- \`README.md\` - Key Features section
- \`README.md\` - Quick Start section (add frontend development commands)

## Proposed Changes
- Add Web UI features to Key Features list
- Document all 5 tabs of the frontend
- Add frontend development commands to Quick Start
- Include links to frontend README

## Impact
- Increased visibility of web UI capabilities
- Clear instructions for frontend development
- Better user experience discovering features

## Related Issues
- Parent: #$PARENT_ISSUE"

issue5=$(create_issue \
    "[Phase 3][Medium] Improve frontend documentation visibility in README" \
    "$issue5_body" \
    '"phase-3","documentation","medium-priority","effort:small"' \
    "$ASSIGNEE")

print_success "Created issue #$issue5"
issue_numbers+=($issue5)

# Sub-Issue 6: Environment variables
print_info "[7/9] Creating issue: Fix env var defaults..."

issue6_body="## Problem
The environment variables table in README.md shows defaults that may not match the actual defaults in \`config.py\`.

## Files to Update
- \`README.md\` - Environment Variables table

## Verification Needed
Cross-reference README table with \`src/ai_code_reviewer/api/core/config.py\`:
- \`EMAIL_OPTOUT\` default
- \`LOGIC_APP_FROM_EMAIL\` default (placeholder value)
- \`DATABASE_URL\` default
- \`DATABASE_ECHO\` default
- \`LOG_LEVEL\` default

## Related Issues
- Parent: #$PARENT_ISSUE"

issue6=$(create_issue \
    "[Phase 3][Low] Fix environment variable defaults table in README" \
    "$issue6_body" \
    '"phase-3","documentation","low-priority","effort:small"' \
    "$ASSIGNEE")

print_success "Created issue #$issue6"
issue_numbers+=($issue6)

# Sub-Issue 7: Webhook payloads
print_info "[8/9] Creating issue: Add webhook docs references..."

issue7_body="## Problem
The file \`docs/webhook-payloads.md\` contains critical information about PR vs Commit payload differences, but it's not referenced in README or CLAUDE.md troubleshooting sections.

## Files to Update
- \`README.md\` - Troubleshooting section
- \`CLAUDE.md\` - Troubleshooting section
- Consider: \`docs/deployment.md\` - Bitbucket Configuration section

## Impact
- Faster troubleshooting of webhook issues
- Better understanding of payload differences
- Improved developer experience

## Related Issues
- Parent: #$PARENT_ISSUE"

issue7=$(create_issue \
    "[Phase 3][Low] Add webhook payload documentation references" \
    "$issue7_body" \
    '"phase-3","documentation","low-priority","effort:small"' \
    "$ASSIGNEE")

print_success "Created issue #$issue7"
issue_numbers+=($issue7)

# Sub-Issue 8: Validate links
print_info "[9/9] Creating issue: Validate all links..."

issue8_body="## Problem
Documentation files contain numerous internal links and cross-references. After all Phase 3 updates, we need to validate that all links work correctly.

## Files to Validate
- \`README.md\`
- \`CLAUDE.md\`
- \`docs/deployment.md\`
- \`docs/development.md\`
- \`docs/architecture.md\`
- \`docker/README.md\`
- \`src/ai_code_reviewer/api/frontend/README.md\`

## Validation Tasks
- [ ] Internal markdown links
- [ ] Anchor links (table of contents)
- [ ] File path references in code examples
- [ ] Command verification
- [ ] Version number consistency

## Related Issues
- Parent: #$PARENT_ISSUE
- Should be done LAST after all other Phase 3 issues"

issue8=$(create_issue \
    "[Phase 3][Medium] Validate all internal links and cross-references" \
    "$issue8_body" \
    '"phase-3","documentation","medium-priority","effort:medium"' \
    "$ASSIGNEE")

print_success "Created issue #$issue8"
issue_numbers+=($issue8)

echo ""
print_success "All issues created successfully!"
echo ""

# Update parent issue with actual issue numbers
print_info "Updating parent issue with sub-issue links..."

updated_parent_body="## Overview
Comprehensive documentation audit and fixes to ensure all documentation matches the current codebase structure and functionality.

## Background
Recent refactoring moved core modules from \`ai_code_reviewer.core.*\` to \`ai_code_reviewer.api.core.*\`, but documentation was not updated. Multiple docs still reference old paths, causing confusion for developers.

## Objectives
- Fix all outdated module import paths
- Add prominent security warnings about disabled features
- Improve database persistence documentation
- Enhance frontend documentation visibility
- Validate all cross-references and links

## Sub-Issues Checklist
- [ ] #${issue_numbers[0]} - Fix outdated import paths in deployment.md
- [ ] #${issue_numbers[1]} - Fix outdated import paths in development.md
- [ ] #${issue_numbers[2]} - Add security warnings to README and CLAUDE.md
- [ ] #${issue_numbers[3]} - Update database persistence documentation
- [ ] #${issue_numbers[4]} - Improve frontend documentation visibility
- [ ] #${issue_numbers[5]} - Fix environment variable defaults table
- [ ] #${issue_numbers[6]} - Add webhook payload documentation references
- [ ] #${issue_numbers[7]} - Validate all internal links and cross-references

## Success Criteria
- [ ] All documentation uses correct module paths
- [ ] Security warnings are prominent and clear
- [ ] All commands in docs have been tested and work
- [ ] All internal links resolve correctly
- [ ] Database features are properly documented

## Estimated Effort
2-3 days

## Priority
High - Prevents confusion and wasted developer time"

updated_parent_body=$(echo "$updated_parent_body" | jq -Rs .)
update_data="{\"body\": $updated_parent_body}"
github_api "PATCH" "repos/$REPO_OWNER/$REPO_NAME/issues/$PARENT_ISSUE" "$update_data" > /dev/null

print_success "Parent issue updated with sub-issue links"
echo ""

# Summary
echo "=========================================="
echo "  Summary"
echo "=========================================="
echo ""
print_success "Created 9 issues total:"
echo "  - Parent issue: #$PARENT_ISSUE"
echo "  - Sub-issues: #${issue_numbers[0]}, #${issue_numbers[1]}, #${issue_numbers[2]}, #${issue_numbers[3]}, #${issue_numbers[4]}, #${issue_numbers[5]}, #${issue_numbers[6]}, #${issue_numbers[7]}"
echo ""
print_success "Created milestone: Phase 3: Documentation Updates (#$MILESTONE_NUMBER)"
echo ""
print_success "Created 9 labels (phase-3, documentation, security, priorities, effort)"
echo ""
echo "View issues: https://github.com/$REPO_OWNER/$REPO_NAME/issues"
echo "View milestone: https://github.com/$REPO_OWNER/$REPO_NAME/milestone/$MILESTONE_NUMBER"
echo ""
print_success "Done!"
echo ""
