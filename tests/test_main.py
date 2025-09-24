import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app


class TestMainApp:
    """Test main FastAPI application"""

    @pytest.fixture
    def client(self):
        """FastAPI test client"""
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "AI Code Reviewer is running"
        assert data["status"] == "healthy"

    def test_health_endpoint_success(self, client):
        """Test basic health check endpoint success"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "config" in data
        # Basic health check should NOT include bitbucket/llm status
        assert "bitbucket" not in data
        assert "llm" not in data

    def test_health_endpoint_failure(self, client):
        """Test health check endpoint failure"""
        with patch("config.Config.validate_config", side_effect=ValueError("Config error")):
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert "error" in data

    def test_detailed_health_endpoint_success(self, client):
        """Test detailed health check endpoint success"""
        with patch("main.bitbucket_client") as mock_bb, patch("main.llm_client") as mock_llm:
            mock_bb.test_connection = AsyncMock(return_value={"status": "connected"})
            mock_llm.test_connection = AsyncMock(return_value={"status": "connected"})

            response = client.get("/health/detailed")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert "bitbucket" in data
            assert "llm" in data
            assert "config" in data

    def test_webhook_pr_opened(self, client, sample_pr_webhook):
        """Test webhook handling for PR opened event"""
        with patch("main.process_pull_request_review"):
            response = client.post(
                "/webhook/code-review", json=sample_pr_webhook, headers={"Content-Type": "application/json"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "accepted"
            assert data["event"] == "pr:opened"

    def test_webhook_commit_push(self, client, sample_commit_webhook):
        """Test webhook handling for commit push event"""
        with patch("main.process_commit_review"):
            response = client.post(
                "/webhook/code-review", json=sample_commit_webhook, headers={"Content-Type": "application/json"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "accepted"
            assert data["event"] == "repo:refs_changed"

    def test_webhook_ignored_event(self, client):
        """Test webhook handling for ignored event"""
        payload = {"eventKey": "pr:declined", "date": "2024-01-01T00:00:00Z"}

        response = client.post("/webhook/code-review", json=payload, headers={"Content-Type": "application/json"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["event"] == "pr:declined"

    def test_webhook_signature_verification_success(self, client, sample_pr_webhook):
        """Test webhook signature verification success"""
        payload = json.dumps(sample_pr_webhook).encode()
        secret = "test_secret"
        signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

        with patch("config.Config.WEBHOOK_SECRET", secret), patch("main.process_pull_request_review"):
            response = client.post(
                "/webhook/code-review",
                content=payload,
                headers={"Content-Type": "application/json", "X-Hub-Signature-256": f"sha256={signature}"},
            )

            assert response.status_code == 200

    def test_webhook_signature_verification_failure(self, client, sample_pr_webhook):
        """Test webhook signature verification failure"""
        payload = json.dumps(sample_pr_webhook).encode()

        with patch("config.Config.WEBHOOK_SECRET", "test_secret"):
            response = client.post(
                "/webhook/code-review",
                content=payload,
                headers={"Content-Type": "application/json", "X-Hub-Signature-256": "sha256=invalid_signature"},
            )

            assert response.status_code == 401

    def test_webhook_no_signature_with_secret(self, client, sample_pr_webhook):
        """Test webhook without signature when secret is configured"""
        with patch("config.Config.WEBHOOK_SECRET", None), patch("main.process_pull_request_review"):
            response = client.post(
                "/webhook/code-review", json=sample_pr_webhook, headers={"Content-Type": "application/json"}
            )

            assert response.status_code == 200

    def test_manual_review_pr(self, client):
        """Test manual PR review endpoint"""
        with patch("main.bitbucket_client") as mock_bb, patch("main.llm_client") as mock_llm:
            mock_bb.get_pull_request_diff = AsyncMock(return_value="mock diff")
            mock_llm.get_code_review = AsyncMock(return_value="Mock review")
            mock_bb.post_pull_request_comment = AsyncMock(return_value=True)

            response = client.post(
                "/manual-review", params={"project_key": "TEST", "repo_slug": "test-repo", "pr_id": 123}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["review"] == "Mock review"

    def test_manual_review_commit(self, client):
        """Test manual commit review endpoint"""
        with patch("main.bitbucket_client") as mock_bb, patch("main.llm_client") as mock_llm:
            mock_bb.get_commit_diff = AsyncMock(return_value="mock diff")
            mock_llm.get_code_review = AsyncMock(return_value="Mock review")
            mock_bb.post_commit_comment = AsyncMock(return_value=True)

            response = client.post(
                "/manual-review", params={"project_key": "TEST", "repo_slug": "test-repo", "commit_id": "abc123"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["review"] == "Mock review"

    def test_manual_review_no_diff(self, client):
        """Test manual review with no diff"""
        with patch("main.bitbucket_client") as mock_bb:
            mock_bb.get_pull_request_diff = AsyncMock(return_value=None)

            response = client.post(
                "/manual-review", params={"project_key": "TEST", "repo_slug": "test-repo", "pr_id": 123}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "no_diff"

    def test_manual_review_missing_params(self, client):
        """Test manual review with missing parameters"""
        response = client.post("/manual-review", params={"project_key": "TEST", "repo_slug": "test-repo"})

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_process_pull_request_review(self, sample_pr_webhook):
        """Test pull request review processing"""
        from main import process_pull_request_review

        with patch("main.bitbucket_client") as mock_bb, patch("main.llm_client") as mock_llm:
            mock_bb.get_pull_request_diff = AsyncMock(return_value="mock diff")
            mock_llm.get_code_review = AsyncMock(return_value="Mock review")
            mock_bb.post_pull_request_comment = AsyncMock(return_value=True)

            await process_pull_request_review(sample_pr_webhook)

            mock_bb.get_pull_request_diff.assert_called_once()
            mock_llm.get_code_review.assert_called_once()
            mock_bb.post_pull_request_comment.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_pull_request_review_no_issues(self, sample_pr_webhook):
        """Test pull request review processing with no issues found"""
        from main import process_pull_request_review

        with patch("main.bitbucket_client") as mock_bb, patch("main.llm_client") as mock_llm:
            mock_bb.get_pull_request_diff = AsyncMock(return_value="mock diff")
            mock_llm.get_code_review = AsyncMock(return_value="No issues found.")

            await process_pull_request_review(sample_pr_webhook)

            mock_bb.post_pull_request_comment.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_commit_review(self, sample_commit_webhook):
        """Test commit review processing"""
        from main import process_commit_review

        with patch("main.bitbucket_client") as mock_bb, patch("main.llm_client") as mock_llm:
            mock_bb.get_commit_diff = AsyncMock(return_value="mock diff")
            mock_llm.get_code_review = AsyncMock(return_value="Mock review")
            mock_bb.post_commit_comment = AsyncMock(return_value=True)

            await process_commit_review(sample_commit_webhook)

            mock_bb.get_commit_diff.assert_called_once()
            mock_llm.get_code_review.assert_called_once()
            mock_bb.post_commit_comment.assert_called_once()
