import os
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient


# Set test environment variables
os.environ["BITBUCKET_URL"] = "https://test-bitbucket.com"
os.environ["BITBUCKET_TOKEN"] = "test_token"
os.environ["LLM_PROVIDER"] = "openai"
os.environ["LLM_API_KEY"] = "test_api_key"
os.environ["LLM_MODEL"] = "gpt-4o"
os.environ["WEBHOOK_SECRET"] = "test_secret"

from ai_code_reviewer.api.clients.bitbucket_client import BitbucketClient
from ai_code_reviewer.api.clients.llm_client import LLMClient
from ai_code_reviewer.api.main import app


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_bitbucket_client():
    """Mock Bitbucket client"""
    client = AsyncMock(spec=BitbucketClient)
    client.test_connection.return_value = {"status": "connected", "version": "7.0.0"}
    client.get_pull_request_diff.return_value = "mock diff content"
    client.get_commit_diff.return_value = "mock diff content"
    client.post_pull_request_comment.return_value = True
    client.post_commit_comment.return_value = True
    return client


@pytest.fixture
def mock_llm_client():
    """Mock LLM client"""
    client = AsyncMock(spec=LLMClient)
    client.test_connection.return_value = {"status": "connected", "provider": "openai"}
    client.get_code_review.return_value = "Mock AI review: Code looks good!"
    return client


@pytest.fixture
def sample_pr_webhook():
    """Sample pull request webhook payload with correct Bitbucket structure"""
    return {
        "eventKey": "pr:opened",
        "date": "2024-01-01T00:00:00Z",
        "actor": {
            "name": "testuser",
            "emailAddress": "test@example.com",
            "active": True,
            "displayName": "Test User",
            "id": 1,
            "slug": "testuser",
            "type": "NORMAL",
        },
        "pullRequest": {
            "id": 123,
            "version": 0,
            "title": "Test PR",
            "description": "Test pull request",
            "state": "OPEN",
            "open": True,
            "closed": False,
            "createdDate": 1704067200000,
            "updatedDate": 1704067200000,
            "fromRef": {
                "id": "refs/heads/feature-branch",
                "displayId": "feature-branch",
                "latestCommit": "abc123",
                "repository": {
                    "slug": "test-repo",
                    "name": "Test Repository",
                    "project": {"key": "TEST", "name": "Test Project"},
                },
            },
            "toRef": {
                "id": "refs/heads/main",
                "displayId": "main",
                "latestCommit": "def456",
                "repository": {
                    "slug": "test-repo",
                    "name": "Test Repository",
                    "project": {"key": "TEST", "name": "Test Project"},
                },
            },
            "locked": False,
            "author": {
                "user": {
                    "name": "testuser",
                    "emailAddress": "test@example.com",
                    "displayName": "Test User",
                }
            },
            "reviewers": [],
            "participants": [],
        },
    }


@pytest.fixture
def sample_commit_webhook():
    """Sample commit webhook payload"""
    return {
        "eventKey": "repo:refs_changed",
        "date": "2024-01-01T00:00:00Z",
        "actor": {"name": "testuser", "emailAddress": "test@example.com"},
        "repository": {"slug": "test-repo", "project": {"key": "TEST"}},
        "changes": [
            {
                "ref": {"id": "refs/heads/main", "displayId": "main", "type": "BRANCH"},
                "refId": "refs/heads/main",
                "fromHash": "abc123",
                "toHash": "def456",
                "type": "UPDATE",
            }
        ],
    }


@pytest.fixture
def sample_diff():
    """Sample git diff content"""
    return """diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,5 +1,8 @@
 def hello_world():
-    print("Hello World")
+    print("Hello, World!")
+
+def new_function():
+    return "This is a new function"

 if __name__ == "__main__":
     hello_world()
+    print(new_function())
"""
