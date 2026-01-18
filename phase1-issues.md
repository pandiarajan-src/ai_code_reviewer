# Phase 1: Critical Security Issues

This file contains all GitHub issues for Phase 1: Critical Security Fixes.

---

## Parent Issue

### Title
`[Phase 1] Critical Security Fixes - Production Readiness`

### Labels
`phase-1`, `security`, `critical`, `high-priority`

### Milestone
`Phase 1: Critical Security Fixes`

### Body
```markdown
## Overview
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
- Related: Phase 3 Documentation Updates (security warnings documented)
```

---

## Sub-Issue 1

### Title
`[Phase 1][Critical] Enable webhook signature verification`

### Labels
`phase-1`, `security`, `critical`, `high-priority`, `effort:medium`

### Milestone
`Phase 1: Critical Security Fixes`

### Body
```markdown
## Problem
Webhook signature verification is currently **commented out** in `src/ai_code_reviewer/api/routes/webhook.py` (lines 53-56), allowing anyone who knows the webhook URL to trigger code reviews without authorization.

## Current State (❌ VULNERABLE)

**File**: `src/ai_code_reviewer/api/routes/webhook.py:53-56`

```python
# # Verify webhook signature if configured
# signature = request.headers.get("X-Hub-Signature-256", "")
# if not verify_webhook_signature(payload_bytes, signature):
#     raise HTTPException(status_code=401, detail="Invalid webhook signature")
```

## Security Risks

**Severity**: CRITICAL

- **Unauthorized Access**: Anyone can trigger code reviews by sending POST requests to `/webhook/code-review`
- **DoS Attacks**: Attackers can flood the system with fake webhook requests
- **Cost Exploitation**: Each fake review triggers expensive LLM API calls
- **Resource Exhaustion**: Server resources consumed processing malicious requests
- **Data Exposure**: Attackers could potentially extract information through crafted requests

## Proposed Solution

### 1. Uncomment Signature Verification

**File**: `src/ai_code_reviewer/api/routes/webhook.py`

```python
# Verify webhook signature if configured
if Config.WEBHOOK_SECRET:
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature")

    if not verify_webhook_signature(payload_bytes, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
```

### 2. Update Configuration

**File**: `src/ai_code_reviewer/api/core/config.py`

Ensure `WEBHOOK_SECRET` is properly documented:

```python
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")  # Required for production
```

### 3. Verify `verify_webhook_signature` Function

Check that the function correctly implements HMAC-SHA256 verification matching Bitbucket's signature format.

### 4. Update Documentation

**Files**: `README.md`, `docs/deployment.md`

Add requirement for `WEBHOOK_SECRET` in production:

```bash
# Generate secure webhook secret
openssl rand -hex 32

# Add to .env
WEBHOOK_SECRET=your_generated_secret_here
```

## Implementation Checklist

- [ ] Uncomment signature verification code
- [ ] Add check for missing signature header
- [ ] Verify `verify_webhook_signature()` implementation is correct
- [ ] Test with valid Bitbucket webhook signatures
- [ ] Test rejection of invalid signatures
- [ ] Test rejection of missing signatures
- [ ] Update README.md with WEBHOOK_SECRET requirement
- [ ] Update docs/deployment.md with secret generation instructions
- [ ] Add environment variable validation at startup
- [ ] Update .env.example with WEBHOOK_SECRET placeholder

## Testing Strategy

```bash
# Test 1: Valid signature (should succeed)
curl -X POST http://localhost:8000/webhook/code-review \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=VALID_SIGNATURE" \
  -d @test_webhook_payload.json

# Test 2: Invalid signature (should fail with 401)
curl -X POST http://localhost:8000/webhook/code-review \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=INVALID" \
  -d @test_webhook_payload.json

# Test 3: Missing signature (should fail with 401)
curl -X POST http://localhost:8000/webhook/code-review \
  -H "Content-Type: application/json" \
  -d @test_webhook_payload.json
```

## Backward Compatibility

Make signature verification optional if `WEBHOOK_SECRET` is not set (for development only):

```python
if Config.WEBHOOK_SECRET:
    # Verify signature
    ...
else:
    logger.warning("Webhook signature verification disabled - not recommended for production")
```

## Documentation Updates

- [ ] README.md: Add WEBHOOK_SECRET to required environment variables
- [ ] docs/deployment.md: Add webhook secret generation to security configuration
- [ ] .env.example: Add WEBHOOK_SECRET placeholder
- [ ] CLAUDE.md: Update security considerations section

## Related Issues
- Parent: [Phase 1] Critical Security Fixes
- Related: Phase 3 documentation (security warnings)

## Definition of Done
- [ ] Signature verification enabled and working
- [ ] Tests pass for valid/invalid/missing signatures
- [ ] Documentation updated
- [ ] Backward compatible for development
- [ ] Security warning removed from README (or updated)
- [ ] Changes committed and pushed
```

---

## Sub-Issue 2

### Title
`[Phase 1][Critical] Fix CORS policy to restrict origins`

### Labels
`phase-1`, `security`, `critical`, `high-priority`, `effort:small`

### Milestone
`Phase 1: Critical Security Fixes`

### Body
```markdown
## Problem
CORS policy currently allows requests from **any origin** (`allow_origins=["*"]`) with credentials enabled in `src/ai_code_reviewer/api/app.py` (lines 68-74), making the application vulnerable to CSRF attacks.

## Current State (❌ VULNERABLE)

**File**: `src/ai_code_reviewer/api/app.py:68-74`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ❌ SECURITY RISK
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Security Risks

**Severity**: HIGH

- **CSRF Attacks**: Malicious websites can make authenticated requests on behalf of users
- **Session Hijacking**: Credentials can be stolen from authenticated sessions
- **Data Theft**: Unauthorized domains can access review data
- **XSS Exploitation**: Cross-site scripting attacks can leverage permissive CORS

## Proposed Solution

### 1. Add CORS Configuration Environment Variable

**File**: `src/ai_code_reviewer/api/core/config.py`

```python
# CORS Configuration
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
# Example: "http://localhost:3000,https://code-review.company.com"
```

### 2. Update CORS Middleware

**File**: `src/ai_code_reviewer/api/app.py`

```python
# Determine allowed origins
allowed_origins = Config.CORS_ALLOWED_ORIGINS if Config.CORS_ALLOWED_ORIGINS else ["*"]

# Warn if using wildcard in production
if "*" in allowed_origins:
    logger.warning(
        "CORS allows all origins (*) - this is a security risk in production. "
        "Set CORS_ALLOWED_ORIGINS environment variable to restrict access."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicit methods
    allow_headers=["Content-Type", "Authorization"],  # Explicit headers
)
```

### 3. Update Environment Configuration

**File**: `.env.example`

```bash
# CORS Configuration (comma-separated list of allowed origins)
# For production, specify exact origins that should have access
# For development, you can use http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Example production configuration:
# CORS_ALLOWED_ORIGINS=https://code-review.yourcompany.com,https://api.yourcompany.com
```

## Implementation Checklist

- [ ] Add `CORS_ALLOWED_ORIGINS` to config.py
- [ ] Update CORS middleware in app.py
- [ ] Add validation for CORS_ALLOWED_ORIGINS format
- [ ] Add warning log when using wildcard (*)
- [ ] Restrict `allow_methods` to specific HTTP methods
- [ ] Restrict `allow_headers` to required headers only
- [ ] Update .env.example with CORS_ALLOWED_ORIGINS
- [ ] Test with allowed origin (should work)
- [ ] Test with disallowed origin (should be blocked)
- [ ] Update documentation

## Testing Strategy

```bash
# Test 1: Request from allowed origin (should succeed)
curl -X GET http://localhost:8000/api/health \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -v

# Test 2: Request from disallowed origin (should be blocked)
curl -X GET http://localhost:8000/api/health \
  -H "Origin: https://malicious-site.com" \
  -H "Access-Control-Request-Method: GET" \
  -v

# Test 3: Preflight request
curl -X OPTIONS http://localhost:8000/api/reviews/latest \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -v
```

## Configuration Examples

### Development
```bash
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000
```

### Production
```bash
CORS_ALLOWED_ORIGINS=https://code-review.yourcompany.com,https://api.yourcompany.com
```

### Testing (allow all - NOT for production)
```bash
CORS_ALLOWED_ORIGINS=*
```

## Backward Compatibility

- If `CORS_ALLOWED_ORIGINS` is not set, default to `["*"]` with a warning
- This allows existing deployments to continue working
- Strongly encourage users to set explicit origins via documentation

## Documentation Updates

- [ ] README.md: Add CORS_ALLOWED_ORIGINS to environment variables table
- [ ] docs/deployment.md: Add CORS configuration to security section
- [ ] README.md: Update or remove security warning about permissive CORS
- [ ] CLAUDE.md: Update security considerations

## Related Issues
- Parent: [Phase 1] Critical Security Fixes
- Related: Phase 3 documentation (CORS warning documented)

## Definition of Done
- [ ] CORS origins configurable via environment variable
- [ ] Wildcard triggers warning in logs
- [ ] Tests pass for allowed/disallowed origins
- [ ] Documentation updated
- [ ] Backward compatible (defaults to * with warning)
- [ ] Changes committed and pushed
```

---

## Sub-Issue 3

### Title
`[Phase 1][Critical] Add rate limiting on API endpoints`

### Labels
`phase-1`, `security`, `critical`, `high-priority`, `effort:large`

### Milestone
`Phase 1: Critical Security Fixes`

### Body
```markdown
## Problem
No rate limiting is implemented on any API endpoint, making the application vulnerable to:
- **DoS attacks** via excessive requests
- **Resource exhaustion** from unlimited API calls
- **Excessive LLM costs** from repeated review triggers
- **Database overload** from high-frequency queries

## Current State (❌ VULNERABLE)

**All endpoints in**:
- `src/ai_code_reviewer/api/routes/webhook.py`
- `src/ai_code_reviewer/api/routes/manual.py`
- `src/ai_code_reviewer/api/routes/reviews.py`
- `src/ai_code_reviewer/api/routes/health.py`
- `src/ai_code_reviewer/api/routes/failures.py`

Have **NO rate limiting** protection.

## Security Risks

**Severity**: CRITICAL

- **DoS Attacks**: Attackers can overwhelm the server with unlimited requests
- **Cost Exploitation**: Repeated calls to `/review-diff` and `/manual-review` trigger expensive LLM API calls
- **Resource Exhaustion**: Database connections, memory, CPU can be exhausted
- **Service Degradation**: Legitimate users affected by performance issues

## Proposed Solution

### 1. Install slowapi Library

**File**: `pyproject.toml`

```toml
dependencies = [
    # ... existing dependencies ...
    "slowapi>=0.1.9",
]
```

### 2. Add Rate Limiting Configuration

**File**: `src/ai_code_reviewer/api/core/config.py`

```python
# Rate Limiting Configuration
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "100/minute")  # Default limit
RATE_LIMIT_WEBHOOK = os.getenv("RATE_LIMIT_WEBHOOK", "10/minute")  # Webhook endpoints
RATE_LIMIT_EXPENSIVE = os.getenv("RATE_LIMIT_EXPENSIVE", "5/minute")  # LLM operations
RATE_LIMIT_STORAGE_URI = os.getenv("RATE_LIMIT_STORAGE_URI", "memory://")  # Or redis://
```

### 3. Initialize Rate Limiter

**File**: `src/ai_code_reviewer/api/app.py`

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[Config.RATE_LIMIT_DEFAULT] if Config.RATE_LIMIT_ENABLED else [],
    storage_uri=Config.RATE_LIMIT_STORAGE_URI,
    enabled=Config.RATE_LIMIT_ENABLED,
)

# Add to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

### 4. Apply Rate Limits to Endpoints

**File**: `src/ai_code_reviewer/api/routes/webhook.py`

```python
from slowapi import Limiter
from src.ai_code_reviewer.api.core.config import Config

@router.post("/code-review")
@limiter.limit(Config.RATE_LIMIT_WEBHOOK)
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    # ... existing code ...
```

**File**: `src/ai_code_reviewer/api/routes/manual.py`

```python
@router.post("/review-diff")
@limiter.limit(Config.RATE_LIMIT_EXPENSIVE)  # More restrictive for LLM calls
async def review_diff_endpoint(request: Request, file: UploadFile):
    # ... existing code ...

@router.post("/manual-review")
@limiter.limit(Config.RATE_LIMIT_EXPENSIVE)
async def trigger_manual_review(request: Request, review_request: ManualReviewRequest):
    # ... existing code ...
```

**File**: `src/ai_code_reviewer/api/routes/reviews.py`

```python
@router.get("/latest")
@limiter.limit(Config.RATE_LIMIT_DEFAULT)
async def get_latest_reviews(limit: int = 10):
    # ... existing code ...
```

### 5. Update Dependencies

```bash
uv pip install slowapi
# Or: pip install slowapi
```

## Implementation Checklist

- [ ] Add slowapi to dependencies in pyproject.toml
- [ ] Add rate limit configuration to config.py
- [ ] Initialize rate limiter in app.py
- [ ] Add rate limiting exception handler
- [ ] Apply limits to webhook endpoints (10/minute)
- [ ] Apply limits to expensive endpoints (5/minute)
- [ ] Apply limits to query endpoints (100/minute)
- [ ] Leave health endpoints unrestricted (for monitoring)
- [ ] Add Redis support for distributed rate limiting (optional)
- [ ] Test rate limiting enforcement
- [ ] Update documentation

## Rate Limit Strategy

### Endpoint Categories

| Endpoint Type | Rate Limit | Reasoning |
|--------------|------------|-----------|
| **Expensive (LLM)** | 5/minute | Prevent LLM cost exploitation |
| `/review-diff` | 5/minute | Each call triggers expensive LLM API |
| `/manual-review` | 5/minute | Triggers full review workflow |
| **Webhooks** | 10/minute | Normal webhook volume from Bitbucket |
| `/webhook/code-review` | 10/minute | Prevent DoS via webhook flooding |
| **Query Endpoints** | 100/minute | Normal API usage |
| `/reviews/*` | 100/minute | Database queries, reasonable limit |
| **Health Checks** | Unlimited | Allow monitoring systems |
| `/health` | Unlimited | Prometheus, load balancers, etc. |

## Testing Strategy

```bash
# Test 1: Exceed rate limit (should get 429 Too Many Requests)
for i in {1..15}; do
  curl -X POST http://localhost:8000/api/review-diff \
    -F "file=@test.diff" \
    -w "%{http_code}\n"
  sleep 0.1
done

# Test 2: Respect rate limit (should succeed)
curl -X GET http://localhost:8000/api/reviews/latest

# Test 3: Health endpoint unrestricted
for i in {1..200}; do
  curl -X GET http://localhost:8000/health -w "%{http_code}\n"
done
```

## Configuration Examples

### Development (Lenient)
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=200/minute
RATE_LIMIT_WEBHOOK=20/minute
RATE_LIMIT_EXPENSIVE=10/minute
RATE_LIMIT_STORAGE_URI=memory://
```

### Production (Strict)
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_WEBHOOK=10/minute
RATE_LIMIT_EXPENSIVE=5/minute
RATE_LIMIT_STORAGE_URI=redis://redis:6379/0  # Distributed
```

### Testing (Disabled)
```bash
RATE_LIMIT_ENABLED=false
```

## Distributed Rate Limiting (Optional Enhancement)

For multi-instance deployments, use Redis:

```bash
# Add redis dependency
pip install redis

# Configure Redis storage
RATE_LIMIT_STORAGE_URI=redis://redis-host:6379/0
```

## Documentation Updates

- [ ] README.md: Add rate limiting configuration to environment variables
- [ ] docs/deployment.md: Add rate limiting to production deployment guide
- [ ] README.md: Update or remove security warning about missing rate limits
- [ ] CLAUDE.md: Update dependencies section
- [ ] Add troubleshooting entry for 429 errors

## Related Issues
- Parent: [Phase 1] Critical Security Fixes
- Related: Phase 3 documentation (rate limiting warning)

## Definition of Done
- [ ] slowapi installed and integrated
- [ ] Rate limits applied to all appropriate endpoints
- [ ] Configuration via environment variables
- [ ] Tests verify rate limiting enforcement
- [ ] Documentation updated
- [ ] Health endpoints remain unrestricted
- [ ] Changes committed and pushed
```

---

## Sub-Issue 4

### Title
`[Phase 1][High] Make SSL verification configurable`

### Labels
`phase-1`, `security`, `high-priority`, `effort:medium`

### Milestone
`Phase 1: Critical Security Fixes`

### Body
```markdown
## Problem
SSL certificate verification is **hardcoded to disabled** (`verify=False`) for all Bitbucket API calls in `src/ai_code_reviewer/api/clients/bitbucket_client.py` (lines 31, 53), making the application vulnerable to man-in-the-middle (MITM) attacks.

## Current State (❌ VULNERABLE)

**File**: `src/ai_code_reviewer/api/clients/bitbucket_client.py`

```python
# Line 31
async with httpx.AsyncClient(verify=False, timeout=30.0) as client:  # nosec B501

# Line 53
async with httpx.AsyncClient(verify=False, timeout=30.0) as client:  # nosec B501
```

## Security Risks

**Severity**: MEDIUM-HIGH

- **MITM Attacks**: Attackers can intercept and modify Bitbucket API communications
- **Credential Theft**: Bitbucket tokens can be stolen in transit
- **Data Tampering**: Diff content and PR data can be manipulated
- **False Trust**: Users may assume secure communication when it's not

## Proposed Solution

### 1. Add SSL Configuration

**File**: `src/ai_code_reviewer/api/core/config.py`

```python
# SSL/TLS Configuration
BITBUCKET_SSL_VERIFY = os.getenv("BITBUCKET_SSL_VERIFY", "true").lower() == "true"
BITBUCKET_SSL_CERT_PATH = os.getenv("BITBUCKET_SSL_CERT_PATH")  # Path to CA bundle
```

### 2. Update Bitbucket Client

**File**: `src/ai_code_reviewer/api/clients/bitbucket_client.py`

```python
def _get_ssl_context(self) -> Union[bool, str]:
    """
    Get SSL verification configuration.

    Returns:
        - True: Verify using system CA bundle (default)
        - False: Disable verification (not recommended)
        - str: Path to custom CA certificate bundle
    """
    if not Config.BITBUCKET_SSL_VERIFY:
        logger.warning(
            "SSL certificate verification is DISABLED for Bitbucket API calls. "
            "This is insecure and should only be used in development. "
            "Set BITBUCKET_SSL_VERIFY=true for production."
        )
        return False

    # Use custom CA bundle if provided
    if Config.BITBUCKET_SSL_CERT_PATH:
        cert_path = Path(Config.BITBUCKET_SSL_CERT_PATH)
        if not cert_path.exists():
            raise ValueError(f"SSL certificate not found: {cert_path}")
        logger.info(f"Using custom CA certificate: {cert_path}")
        return str(cert_path)

    # Use system CA bundle
    return True

async def get_commit_diff(self, project_key: str, repo_slug: str, commit_hash: str) -> str:
    """Fetch the diff for a specific commit."""
    url = f"{self.base_url}/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/commits/{commit_hash}/diff"

    ssl_verify = self._get_ssl_context()

    try:
        async with httpx.AsyncClient(verify=ssl_verify, timeout=30.0) as client:
            response = await client.get(url, headers=self.headers)
            # ... rest of code ...
```

### 3. Apply to All Bitbucket API Methods

Update all methods that use `httpx.AsyncClient`:
- `get_commit_diff()`
- `get_pull_request_diff()`
- `get_commit_info()`
- `get_pull_request_info()`

### 4. Update Environment Configuration

**File**: `.env.example`

```bash
# SSL/TLS Configuration for Bitbucket
# Set to 'true' to enable SSL certificate verification (recommended for production)
# Set to 'false' to disable verification (only for development with self-signed certs)
BITBUCKET_SSL_VERIFY=true

# Path to custom CA certificate bundle (optional)
# Use this if your Bitbucket server uses self-signed or internal CA certificates
# BITBUCKET_SSL_CERT_PATH=/path/to/ca-bundle.crt
```

## Implementation Checklist

- [ ] Add `BITBUCKET_SSL_VERIFY` to config.py
- [ ] Add `BITBUCKET_SSL_CERT_PATH` to config.py
- [ ] Create `_get_ssl_context()` helper method
- [ ] Update `get_commit_diff()` to use configurable SSL
- [ ] Update `get_pull_request_diff()` to use configurable SSL
- [ ] Update `get_commit_info()` to use configurable SSL (if applicable)
- [ ] Update `get_pull_request_info()` to use configurable SSL (if applicable)
- [ ] Add warning log when SSL verification is disabled
- [ ] Add validation for custom CA certificate path
- [ ] Test with SSL verification enabled (production mode)
- [ ] Test with SSL verification disabled (dev mode)
- [ ] Test with custom CA certificate
- [ ] Update documentation

## Testing Strategy

### Test 1: Enabled SSL Verification (Production)
```bash
# .env
BITBUCKET_SSL_VERIFY=true

# Should succeed with valid certificate
curl http://localhost:8000/webhook/code-review -X POST -d @webhook.json
```

### Test 2: Disabled SSL Verification (Development)
```bash
# .env
BITBUCKET_SSL_VERIFY=false

# Should show warning in logs but work
curl http://localhost:8000/webhook/code-review -X POST -d @webhook.json
```

### Test 3: Custom CA Certificate
```bash
# .env
BITBUCKET_SSL_VERIFY=true
BITBUCKET_SSL_CERT_PATH=/path/to/company-ca-bundle.crt

# Should use custom CA for verification
curl http://localhost:8000/webhook/code-review -X POST -d @webhook.json
```

## Configuration Examples

### Production (Verify with system CA)
```bash
BITBUCKET_SSL_VERIFY=true
```

### Production (Verify with custom CA)
```bash
BITBUCKET_SSL_VERIFY=true
BITBUCKET_SSL_CERT_PATH=/etc/ssl/certs/company-ca-bundle.crt
```

### Development (Disable - NOT recommended)
```bash
BITBUCKET_SSL_VERIFY=false
```

## Backward Compatibility

- Default `BITBUCKET_SSL_VERIFY=true` for security
- This changes existing behavior (currently defaults to `False`)
- Users with self-signed certs must either:
  - Provide custom CA via `BITBUCKET_SSL_CERT_PATH`
  - Or explicitly disable with `BITBUCKET_SSL_VERIFY=false`

## Migration Guide

Add to documentation:

```markdown
### ⚠️ Breaking Change: SSL Verification Now Enabled by Default

If you're using a Bitbucket server with self-signed certificates, you must either:

**Option 1: Provide Custom CA Certificate (Recommended)**
```bash
BITBUCKET_SSL_VERIFY=true
BITBUCKET_SSL_CERT_PATH=/path/to/your-ca-bundle.crt
```

**Option 2: Disable SSL Verification (NOT for production)**
```bash
BITBUCKET_SSL_VERIFY=false
```
```

## Documentation Updates

- [ ] README.md: Add SSL configuration to environment variables
- [ ] docs/deployment.md: Add SSL configuration to security section
- [ ] README.md: Update or remove security warning about disabled SSL
- [ ] Add migration guide for breaking change
- [ ] CLAUDE.md: Update security considerations
- [ ] Add troubleshooting for SSL certificate errors

## Related Issues
- Parent: [Phase 1] Critical Security Fixes
- Related: Phase 3 documentation (SSL verification warning)

## Definition of Done
- [ ] SSL verification configurable via environment variables
- [ ] Support for custom CA certificates
- [ ] Warning logged when verification disabled
- [ ] All Bitbucket API methods updated
- [ ] Tests pass for enabled/disabled/custom CA modes
- [ ] Documentation updated with migration guide
- [ ] Changes committed and pushed
```

---

## Summary

**Total Issues**: 5 (1 parent + 4 sub-issues)

**Priority Breakdown**:
- Critical: 3 issues (webhook auth, CORS, rate limiting)
- High: 1 issue (SSL verification)

**Effort Breakdown**:
- Small: 1 issue (CORS) - ~2 hours
- Medium: 2 issues (webhook auth, SSL) - ~3-4 hours each
- Large: 1 issue (rate limiting) - ~6-8 hours
- Total Estimated Time: 1 week

**Issue Creation Order**:
1. Create parent issue first
2. Create sub-issues 1-4
3. Update parent issue with actual issue numbers in checklist

**Note**: Replace `#ISSUE_X` placeholders with actual issue numbers after creation.
