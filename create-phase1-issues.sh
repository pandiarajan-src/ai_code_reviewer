#!/bin/bash

#############################################################
# GitHub Issues Creator for Phase 1: Critical Security Fixes
#############################################################
#
# This script creates GitHub issues via REST API
# Requires: curl, jq (optional), GitHub Personal Access Token
#
# Usage:
#   ./create-phase1-issues.sh
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
echo "  GitHub Issues Creator - Phase 1"
echo "  Critical Security Fixes"
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

# Create labels (if they don't exist from Phase 3)
print_info "Ensuring labels exist..."

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

create_label "phase-1" "d73a4a" "Phase 1: Critical Security Fixes"
create_label "security" "d73a4a" "Security related"
create_label "critical" "b60205" "Critical priority - immediate action required"
create_label "high-priority" "d93f0b" "High priority issue"
create_label "effort:small" "c2e0c6" "Small effort (< 2 hours)"
create_label "effort:medium" "bfd4f2" "Medium effort (2-4 hours)"
create_label "effort:large" "f9d0c4" "Large effort (> 4 hours)"

echo ""

# Create milestone
print_info "Creating milestone..."

milestone_data='{
  "title": "Phase 1: Critical Security Fixes",
  "description": "Address critical security vulnerabilities before production deployment",
  "due_on": null
}'

milestone_response=$(github_api "POST" "repos/$REPO_OWNER/$REPO_NAME/milestones" "$milestone_data")
MILESTONE_NUMBER=$(echo "$milestone_response" | grep -o '"number": [0-9]*' | head -1 | cut -d' ' -f2)

if [ -n "$MILESTONE_NUMBER" ]; then
    print_success "Created milestone #$MILESTONE_NUMBER"
else
    # Milestone might already exist, try to get it
    milestones=$(github_api "GET" "repos/$REPO_OWNER/$REPO_NAME/milestones" "")
    MILESTONE_NUMBER=$(echo "$milestones" | grep -B2 '"title": "Phase 1: Critical Security Fixes"' | grep '"number"' | grep -o '[0-9]*' | head -1)
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
print_info "[1/5] Creating parent issue..."

parent_body='## Overview
Address critical security vulnerabilities that prevent safe production deployment. These features are currently disabled by default and must be enabled to prevent unauthorized access, DoS attacks, and data breaches.

## Background
The application was developed with several security features disabled for development convenience. Before production deployment, these must be enabled and properly configured to prevent:
- Unauthorized webhook triggers leading to DoS and excessive LLM costs
- Cross-site request forgery (CSRF) attacks
- Man-in-the-middle (MITM) attacks
- Resource exhaustion from unlimited API requests

## Objectives
- Enable webhook signature verification for authenticated webhook requests
- Restrict CORS policy to specific allowed origins
- Implement rate limiting on all API endpoints
- Make SSL verification configurable with support for custom CA certificates

## Sub-Issues Checklist
- [ ] Enable webhook signature verification
- [ ] Fix CORS policy to restrict origins
- [ ] Add rate limiting on API endpoints
- [ ] Make SSL verification configurable

## Success Criteria
- [ ] Webhook endpoints reject requests without valid signatures
- [ ] CORS policy blocks requests from unauthorized origins
- [ ] Rate limiting prevents excessive API usage
- [ ] SSL verification can be enabled/disabled via configuration
- [ ] All security fixes are backward compatible with existing deployments
- [ ] Documentation updated with security best practices

## Priority
**CRITICAL** - Must be completed before production deployment

## Estimated Effort
1 week

## Related Issues
- Blocks: Production deployment
- Related: Phase 3 Documentation Updates (security warnings documented)'

parent_number=$(create_issue \
    "[Phase 1] Critical Security Fixes - Production Readiness" \
    "$parent_body" \
    '"phase-1","security","critical","high-priority"' \
    "$ASSIGNEE")

if [ -n "$parent_number" ]; then
    print_success "Created parent issue #$parent_number"
    PARENT_ISSUE=$parent_number
else
    print_error "Failed to create parent issue"
    exit 1
fi

echo ""

# Sub-Issue 1: Webhook signature verification
print_info "[2/5] Creating issue: Enable webhook signature verification..."

issue1_body="## Problem
Webhook signature verification is currently **commented out** in \`src/ai_code_reviewer/api/routes/webhook.py\` (lines 53-56), allowing anyone who knows the webhook URL to trigger code reviews without authorization.

## Security Risks

**Severity**: CRITICAL

- **Unauthorized Access**: Anyone can trigger code reviews
- **DoS Attacks**: Attackers can flood the system with fake webhook requests
- **Cost Exploitation**: Each fake review triggers expensive LLM API calls
- **Resource Exhaustion**: Server resources consumed processing malicious requests

## Proposed Solution

Uncomment signature verification and make it configurable:

\`\`\`python
# Verify webhook signature if configured
if Config.WEBHOOK_SECRET:
    signature = request.headers.get(\"X-Hub-Signature-256\", \"\")
    if not signature:
        raise HTTPException(status_code=401, detail=\"Missing webhook signature\")

    if not verify_webhook_signature(payload_bytes, signature):
        raise HTTPException(status_code=401, detail=\"Invalid webhook signature\")
\`\`\`

## Implementation Checklist

- [ ] Uncomment signature verification code
- [ ] Add check for missing signature header
- [ ] Verify verify_webhook_signature() implementation
- [ ] Test with valid Bitbucket webhook signatures
- [ ] Test rejection of invalid signatures
- [ ] Update documentation with WEBHOOK_SECRET requirement
- [ ] Add environment variable validation at startup
- [ ] Update .env.example

## Documentation Updates

- [ ] README.md: Add WEBHOOK_SECRET to required variables
- [ ] docs/deployment.md: Add secret generation instructions
- [ ] .env.example: Add WEBHOOK_SECRET placeholder

## Related Issues
- Parent: #$PARENT_ISSUE
- Related: Phase 3 documentation"

issue1=$(create_issue \
    "[Phase 1][Critical] Enable webhook signature verification" \
    "$issue1_body" \
    '"phase-1","security","critical","high-priority","effort:medium"' \
    "$ASSIGNEE")

print_success "Created issue #$issue1"
issue_numbers+=($issue1)

# Sub-Issue 2: CORS policy
print_info "[3/5] Creating issue: Fix CORS policy..."

issue2_body="## Problem
CORS policy currently allows requests from **any origin** (\`allow_origins=[\"*\"]\`) with credentials enabled in \`src/ai_code_reviewer/api/app.py\` (lines 68-74).

## Security Risks

**Severity**: HIGH

- **CSRF Attacks**: Malicious websites can make authenticated requests
- **Session Hijacking**: Credentials can be stolen
- **Data Theft**: Unauthorized domains can access review data

## Proposed Solution

Make CORS configurable via environment variable:

\`\`\`python
# Add to config.py
CORS_ALLOWED_ORIGINS = os.getenv(\"CORS_ALLOWED_ORIGINS\", \"\").split(\",\")

# Update app.py
allowed_origins = Config.CORS_ALLOWED_ORIGINS if Config.CORS_ALLOWED_ORIGINS else [\"*\"]

if \"*\" in allowed_origins:
    logger.warning(\"CORS allows all origins - security risk in production\")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=[\"GET\", \"POST\", \"PUT\", \"DELETE\", \"OPTIONS\"],
    allow_headers=[\"Content-Type\", \"Authorization\"],
)
\`\`\`

## Configuration Examples

Development: \`CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000\`
Production: \`CORS_ALLOWED_ORIGINS=https://code-review.company.com\`

## Implementation Checklist

- [ ] Add CORS_ALLOWED_ORIGINS to config.py
- [ ] Update CORS middleware in app.py
- [ ] Add warning when using wildcard
- [ ] Restrict allow_methods and allow_headers
- [ ] Update .env.example
- [ ] Test with allowed/disallowed origins
- [ ] Update documentation

## Related Issues
- Parent: #$PARENT_ISSUE"

issue2=$(create_issue \
    "[Phase 1][Critical] Fix CORS policy to restrict origins" \
    "$issue2_body" \
    '"phase-1","security","critical","high-priority","effort:small"' \
    "$ASSIGNEE")

print_success "Created issue #$issue2"
issue_numbers+=($issue2)

# Sub-Issue 3: Rate limiting
print_info "[4/5] Creating issue: Add rate limiting..."

issue3_body="## Problem
No rate limiting is implemented on any API endpoint, making the application vulnerable to DoS attacks, resource exhaustion, and excessive LLM costs.

## Security Risks

**Severity**: CRITICAL

- **DoS Attacks**: Unlimited requests can overwhelm the server
- **Cost Exploitation**: Repeated calls to LLM endpoints trigger expensive API calls
- **Resource Exhaustion**: Database, memory, CPU can be exhausted

## Proposed Solution

Use slowapi library for rate limiting:

\`\`\`python
# Install slowapi
pip install slowapi

# Configure rate limits
RATE_LIMIT_DEFAULT = \"100/minute\"
RATE_LIMIT_WEBHOOK = \"10/minute\"
RATE_LIMIT_EXPENSIVE = \"5/minute\"  # For LLM operations

# Apply to endpoints
@router.post(\"/review-diff\")
@limiter.limit(Config.RATE_LIMIT_EXPENSIVE)
async def review_diff_endpoint(request: Request, file: UploadFile):
    # ...
\`\`\`

## Rate Limit Strategy

- **Expensive (LLM)**: 5/minute - Prevent cost exploitation
- **Webhooks**: 10/minute - Normal webhook volume
- **Query Endpoints**: 100/minute - Normal API usage
- **Health Checks**: Unlimited - Allow monitoring

## Implementation Checklist

- [ ] Add slowapi to dependencies
- [ ] Add rate limit configuration
- [ ] Initialize rate limiter
- [ ] Apply limits to webhook endpoints (10/min)
- [ ] Apply limits to expensive endpoints (5/min)
- [ ] Apply limits to query endpoints (100/min)
- [ ] Leave health endpoints unrestricted
- [ ] Test rate limiting enforcement
- [ ] Update documentation

## Related Issues
- Parent: #$PARENT_ISSUE"

issue3=$(create_issue \
    "[Phase 1][Critical] Add rate limiting on API endpoints" \
    "$issue3_body" \
    '"phase-1","security","critical","high-priority","effort:large"' \
    "$ASSIGNEE")

print_success "Created issue #$issue3"
issue_numbers+=($issue3)

# Sub-Issue 4: SSL verification
print_info "[5/5] Creating issue: Make SSL verification configurable..."

issue4_body="## Problem
SSL certificate verification is **hardcoded to disabled** (\`verify=False\`) for all Bitbucket API calls in \`src/ai_code_reviewer/api/clients/bitbucket_client.py\` (lines 31, 53).

## Security Risks

**Severity**: MEDIUM-HIGH

- **MITM Attacks**: Communications can be intercepted and modified
- **Credential Theft**: Bitbucket tokens can be stolen in transit
- **Data Tampering**: Diff content can be manipulated

## Proposed Solution

Make SSL verification configurable:

\`\`\`python
# Add to config.py
BITBUCKET_SSL_VERIFY = os.getenv(\"BITBUCKET_SSL_VERIFY\", \"true\").lower() == \"true\"
BITBUCKET_SSL_CERT_PATH = os.getenv(\"BITBUCKET_SSL_CERT_PATH\")

# Update bitbucket_client.py
def _get_ssl_context(self):
    if not Config.BITBUCKET_SSL_VERIFY:
        logger.warning(\"SSL verification DISABLED - not recommended\")
        return False

    if Config.BITBUCKET_SSL_CERT_PATH:
        return str(Config.BITBUCKET_SSL_CERT_PATH)

    return True

# Use in API calls
async with httpx.AsyncClient(verify=ssl_verify, timeout=30.0) as client:
    # ...
\`\`\`

## Configuration Examples

Production: \`BITBUCKET_SSL_VERIFY=true\`
With custom CA: \`BITBUCKET_SSL_CERT_PATH=/path/to/ca-bundle.crt\`
Development: \`BITBUCKET_SSL_VERIFY=false\` (not recommended)

## Implementation Checklist

- [ ] Add SSL configuration to config.py
- [ ] Create _get_ssl_context() helper method
- [ ] Update all Bitbucket API methods
- [ ] Add warning when verification disabled
- [ ] Support custom CA certificates
- [ ] Test with enabled/disabled/custom CA
- [ ] Update documentation with migration guide

## Related Issues
- Parent: #$PARENT_ISSUE"

issue4=$(create_issue \
    "[Phase 1][High] Make SSL verification configurable" \
    "$issue4_body" \
    '"phase-1","security","high-priority","effort:medium"' \
    "$ASSIGNEE")

print_success "Created issue #$issue4"
issue_numbers+=($issue4)

echo ""
print_success "All issues created successfully!"
echo ""

# Update parent issue with actual issue numbers
print_info "Updating parent issue with sub-issue links..."

updated_parent_body="## Overview
Address critical security vulnerabilities that prevent safe production deployment. These features are currently disabled by default and must be enabled to prevent unauthorized access, DoS attacks, and data breaches.

## Background
The application was developed with several security features disabled for development convenience. Before production deployment, these must be enabled and properly configured to prevent:
- Unauthorized webhook triggers leading to DoS and excessive LLM costs
- Cross-site request forgery (CSRF) attacks
- Man-in-the-middle (MITM) attacks
- Resource exhaustion from unlimited API requests

## Objectives
- Enable webhook signature verification for authenticated webhook requests
- Restrict CORS policy to specific allowed origins
- Implement rate limiting on all API endpoints
- Make SSL verification configurable with support for custom CA certificates

## Sub-Issues Checklist
- [ ] #${issue_numbers[0]} - Enable webhook signature verification
- [ ] #${issue_numbers[1]} - Fix CORS policy to restrict origins
- [ ] #${issue_numbers[2]} - Add rate limiting on API endpoints
- [ ] #${issue_numbers[3]} - Make SSL verification configurable

## Success Criteria
- [ ] Webhook endpoints reject requests without valid signatures
- [ ] CORS policy blocks requests from unauthorized origins
- [ ] Rate limiting prevents excessive API usage
- [ ] SSL verification can be enabled/disabled via configuration
- [ ] All security fixes are backward compatible with existing deployments
- [ ] Documentation updated with security best practices

## Priority
**CRITICAL** - Must be completed before production deployment

## Estimated Effort
1 week

## Related Issues
- Blocks: Production deployment
- Related: Phase 3 Documentation Updates (security warnings documented)"

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
print_success "Created 5 issues total:"
echo "  - Parent issue: #$PARENT_ISSUE"
echo "  - Sub-issues: #${issue_numbers[0]}, #${issue_numbers[1]}, #${issue_numbers[2]}, #${issue_numbers[3]}"
echo ""
print_success "Created milestone: Phase 1: Critical Security Fixes (#$MILESTONE_NUMBER)"
echo ""
print_success "Created/verified 7 labels (phase-1, security, critical, priorities, effort)"
echo ""
echo "View issues: https://github.com/$REPO_OWNER/$REPO_NAME/issues"
echo "View milestone: https://github.com/$REPO_OWNER/$REPO_NAME/milestone/$MILESTONE_NUMBER"
echo ""
print_success "Done!"
echo ""
