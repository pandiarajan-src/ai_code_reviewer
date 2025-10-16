# Bitbucket Webhook Payload Reference

This document describes the structure of webhook payloads received from Bitbucket Enterprise Server and how the AI Code Reviewer processes them.

## Overview

The AI Code Reviewer supports two types of Bitbucket webhook events:

1. **Pull Request Events** (`pr:opened`, `pr:from_ref_updated`)
2. **Commit/Push Events** (`repo:refs_changed`)

Each event type has a different payload structure, which is documented below with real-world examples.

## Pull Request Events

### Supported Event Keys

- `pr:opened` - When a new pull request is created
- `pr:from_ref_updated` - When source branch of PR is updated with new commits

### Payload Structure

**IMPORTANT**: The repository information for pull requests is nested within the `pullRequest` object, specifically in `pullRequest.toRef.repository` (target branch) or `pullRequest.fromRef.repository` (source branch).

```json
{
  "eventKey": "pr:opened",
  "date": "2025-10-16T15:57:18+0000",
  "actor": {
    "name": "USWU52341",
    "emailAddress": "user@example.com",
    "active": true,
    "displayName": "John Doe",
    "id": 2666,
    "slug": "uswu52341",
    "type": "NORMAL"
  },
  "pullRequest": {
    "id": 1,
    "version": 0,
    "title": "Feature: Add new component",
    "description": "Description of the pull request",
    "state": "OPEN",
    "open": true,
    "closed": false,
    "draft": false,
    "createdDate": 1760630238441,
    "updatedDate": 1760630238441,
    "fromRef": {
      "id": "refs/heads/feature-branch",
      "displayId": "feature-branch",
      "latestCommit": "abc123def456",
      "repository": {
        "slug": "my-repo",
        "name": "My Repository",
        "project": {
          "key": "PROJ",
          "name": "My Project"
        }
      }
    },
    "toRef": {
      "id": "refs/heads/main",
      "displayId": "main",
      "latestCommit": "def456abc789",
      "repository": {
        "slug": "my-repo",
        "name": "My Repository",
        "project": {
          "key": "PROJ",
          "name": "My Project"
        }
      }
    },
    "locked": false,
    "author": {
      "user": {
        "name": "author-username",
        "emailAddress": "author@example.com",
        "displayName": "Author Name"
      }
    },
    "reviewers": [],
    "participants": []
  }
}
```

### Extraction Logic

The code extracts repository information from the **target branch** (`toRef`):

```python
# From src/ai_code_reviewer/core/review_engine.py
pull_request = payload["pullRequest"]
to_ref = pull_request["toRef"]
repository = to_ref["repository"]

project_key = repository["project"]["key"]  # "PROJ"
repo_slug = repository["slug"]              # "my-repo"
pr_id = pull_request["id"]                  # 1
```

### Common Mistakes

❌ **INCORRECT**: Trying to access `payload["repository"]` at the top level
```python
# This will fail - repository is NOT at the top level for PR events
repository = payload["repository"]  # KeyError!
```

✅ **CORRECT**: Access repository via `pullRequest.toRef.repository`
```python
repository = payload["pullRequest"]["toRef"]["repository"]
```

## Commit/Push Events

### Supported Event Keys

- `repo:refs_changed` - When commits are pushed to a branch

### Payload Structure

For commit events, the repository **IS** at the top level of the payload:

```json
{
  "eventKey": "repo:refs_changed",
  "date": "2025-10-16T10:00:00+0000",
  "actor": {
    "name": "developer",
    "emailAddress": "developer@example.com",
    "active": true,
    "displayName": "Developer Name",
    "id": 1234,
    "slug": "developer",
    "type": "NORMAL"
  },
  "repository": {
    "slug": "my-repo",
    "name": "My Repository",
    "project": {
      "key": "PROJ",
      "name": "My Project"
    }
  },
  "changes": [
    {
      "ref": {
        "id": "refs/heads/main",
        "displayId": "main",
        "type": "BRANCH"
      },
      "refId": "refs/heads/main",
      "fromHash": "abc123",
      "toHash": "def456",
      "type": "UPDATE"
    }
  ]
}
```

### Extraction Logic

```python
# From src/ai_code_reviewer/core/review_engine.py
repository = payload["repository"]  # Repository IS at top level for commits
changes = payload.get("changes", [])

project_key = repository["project"]["key"]
repo_slug = repository["slug"]

for change in changes:
    commit_id = change["toHash"]
    # Process each commit...
```

## Payload Validation

The review engine includes comprehensive validation to handle malformed payloads gracefully:

### Pull Request Validation

```python
# Check for required keys
if "pullRequest" not in payload:
    logger.error("Invalid payload: missing 'pullRequest' key")
    return

# Validate nested structure
if "toRef" not in pull_request:
    logger.error("Invalid pull request payload: missing 'toRef' key")
    return

repository = to_ref.get("repository")
if not repository:
    logger.error("Invalid pull request payload: missing 'repository' in toRef")
    return
```

### Commit Validation

```python
# Check for repository key
repository = payload["repository"]  # Will raise KeyError if missing

# Check for changes
changes = payload.get("changes", [])
if not changes:
    logger.info("No changes found in commit payload")
    return
```

## Testing

Test fixtures for both payload types are available in [tests/conftest.py](../tests/conftest.py):

- `sample_pr_webhook` - Complete PR webhook payload with correct structure
- `sample_commit_webhook` - Complete commit webhook payload

Example usage in tests:

```python
@pytest.mark.asyncio
async def test_pr_processing(sample_pr_webhook):
    """Test PR webhook processing"""
    await process_pull_request_review(
        bitbucket_client,
        llm_client,
        sample_pr_webhook
    )
```

## Webhook Configuration in Bitbucket

To configure webhooks in Bitbucket Enterprise Server:

1. Navigate to repository **Settings** → **Webhooks**
2. Click **Create webhook**
3. Configure the webhook:
   - **Name**: AI Code Reviewer
   - **URL**: `http://your-server:8000/webhook/code-review`
   - **Events**: Select:
     - Pull Request → Opened
     - Pull Request → Source branch updated
     - Repository → Push (for commit reviews)
   - **Secret**: (Optional) Configure `WEBHOOK_SECRET` environment variable
4. Save and enable the webhook

## Debugging Webhook Issues

### Enable Debug Logging

Set log level to DEBUG in your environment:

```bash
LOG_LEVEL=DEBUG python -m ai_code_reviewer.main
```

### Check Payload Structure

The webhook handler logs the incoming event key:

```
INFO: Processing webhook event: pr:opened
INFO: Processing PR review for PROJ/my-repo/pull-requests/1
```

### Common Issues

1. **Missing repository data** → Check if you're accessing the correct location based on event type
2. **KeyError on 'pullRequest'** → Verify the webhook event is actually a PR event
3. **No diff found** → Ensure the PR/commit has actual code changes

## API Endpoint

**Endpoint**: `POST /webhook/code-review`

**Headers**:
- `Content-Type: application/json`
- `X-Hub-Signature-256: sha256=<signature>` (if webhook secret is configured)

**Response**:
```json
{
  "status": "accepted",
  "event": "pr:opened",
  "message": "Webhook received and processing started"
}
```

## Related Files

- [src/ai_code_reviewer/core/review_engine.py](../src/ai_code_reviewer/core/review_engine.py) - Payload processing logic
- [src/ai_code_reviewer/api/routes/webhook.py](../src/ai_code_reviewer/api/routes/webhook.py) - Webhook handler
- [tests/conftest.py](../tests/conftest.py) - Test fixtures with sample payloads
- [tests/unit/test_review_engine.py](../tests/unit/test_review_engine.py) - Payload parsing tests

## References

- [Bitbucket Server Webhook Documentation](https://confluence.atlassian.com/bitbucketserver/event-payload-938025882.html)
- [Bitbucket REST API](https://docs.atlassian.com/bitbucket-server/rest/)
