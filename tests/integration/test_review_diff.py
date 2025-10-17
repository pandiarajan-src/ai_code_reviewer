"""Integration tests for the /review-diff endpoint."""

import io
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from ai_code_reviewer.api.app import create_app


@pytest.fixture
def client():
    """Create a test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_diff():
    """Sample diff content for testing."""
    return """diff --git a/example.py b/example.py
index abc123..def456 100644
--- a/example.py
+++ b/example.py
@@ -1,5 +1,10 @@
 def hello():
-    print("Hello World")
+    name = "World"
+    print(f"Hello {name}")
+
+def goodbye():
+    # TODO: implement this function
+    pass

 if __name__ == "__main__":
     hello()
+    goodbye()
"""


@pytest.fixture
def mock_llm_review():
    """Mock LLM review response."""
    return """## Code Review

### Issues Found

1. **TODO Comment**: The `goodbye()` function has a TODO comment indicating incomplete implementation.
   - Consider implementing the function or removing it if not needed.

2. **Code Quality**: The f-string usage in `hello()` is good practice.

### Recommendations

- Complete the `goodbye()` function implementation
- Add docstrings to both functions
- Consider adding type hints

Overall: Minor issues found. Address the TODO before production deployment."""


class TestReviewDiffEndpoint:
    """Tests for the /review-diff endpoint."""

    @patch("ai_code_reviewer.api.routes.manual.get_llm_client")
    @patch("ai_code_reviewer.api.routes.manual.save_review_to_database")
    def test_basic_diff_upload_success(self, mock_save_db, mock_get_llm, client, sample_diff, mock_llm_review):
        """Test basic diff file upload with successful review."""
        # Setup mocks
        mock_llm_client = AsyncMock()
        mock_llm_client.get_code_review = AsyncMock(return_value=mock_llm_review)
        mock_llm_client.provider = "openai"
        mock_llm_client.model = "gpt-4o"
        mock_get_llm.return_value = mock_llm_client
        mock_save_db.return_value = 123

        # Create file-like object
        files = {"file": ("test.diff", io.BytesIO(sample_diff.encode()), "text/plain")}

        # Make request
        response = client.post("/review-diff", files=files)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "review_markdown" in data
        assert data["review_markdown"] == mock_llm_review
        assert data["metadata"]["record_id"] == 123
        assert data["metadata"]["filename"] == "test.diff"
        assert data["metadata"]["project_key"] == "MANUAL"
        assert data["metadata"]["repo_slug"] == "diff-upload"
        assert data["metadata"]["author_name"] == "Anonymous"
        assert data["metadata"]["llm_provider"] == "openai"
        assert data["metadata"]["llm_model"] == "gpt-4o"

        # Verify LLM client was called
        mock_llm_client.get_code_review.assert_called_once()

        # Verify database save was called
        mock_save_db.assert_called_once()
        call_kwargs = mock_save_db.call_args.kwargs
        assert call_kwargs["review_type"] == "manual"
        assert call_kwargs["trigger_type"] == "diff_upload"
        assert call_kwargs["email_sent"] is False

    @patch("ai_code_reviewer.api.routes.manual.get_llm_client")
    @patch("ai_code_reviewer.api.routes.manual.save_review_to_database")
    def test_diff_upload_with_metadata(self, mock_save_db, mock_get_llm, client, sample_diff, mock_llm_review):
        """Test diff upload with custom metadata."""
        # Setup mocks
        mock_llm_client = AsyncMock()
        mock_llm_client.get_code_review = AsyncMock(return_value=mock_llm_review)
        mock_llm_client.provider = "openai"
        mock_llm_client.model = "gpt-4o"
        mock_get_llm.return_value = mock_llm_client
        mock_save_db.return_value = 456

        # Create file with metadata
        files = {"file": ("feature.diff", io.BytesIO(sample_diff.encode()), "text/plain")}
        data = {
            "project_key": "MY-PROJECT",
            "repo_slug": "backend",
            "author_name": "John Doe",
            "author_email": "john@example.com",
            "description": "New feature implementation",
        }

        # Make request
        response = client.post("/review-diff", files=files, data=data)

        # Assertions
        assert response.status_code == 200
        result = response.json()
        assert result["metadata"]["project_key"] == "MY-PROJECT"
        assert result["metadata"]["repo_slug"] == "backend"
        assert result["metadata"]["author_name"] == "John Doe"
        assert result["metadata"]["author_email"] == "john@example.com"
        assert result["metadata"]["description"] == "New feature implementation"

        # Verify database save with correct metadata
        call_kwargs = mock_save_db.call_args.kwargs
        assert call_kwargs["project_key"] == "MY-PROJECT"
        assert call_kwargs["repo_slug"] == "backend"
        assert call_kwargs["author_name"] == "John Doe"
        assert call_kwargs["author_email"] == "john@example.com"

    def test_invalid_file_extension(self, client):
        """Test that non-.diff files are rejected."""
        invalid_content = "This is not a diff file"
        files = {"file": ("readme.txt", io.BytesIO(invalid_content.encode()), "text/plain")}

        response = client.post("/review-diff", files=files)

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_patch_file_extension_accepted(self, client, sample_diff, mock_llm_review):
        """Test that .patch files are also accepted."""
        with (
            patch("ai_code_reviewer.api.routes.manual.get_llm_client") as mock_get_llm,
            patch("ai_code_reviewer.api.routes.manual.save_review_to_database") as mock_save_db,
        ):
            mock_llm_client = AsyncMock()
            mock_llm_client.get_code_review = AsyncMock(return_value=mock_llm_review)
            mock_llm_client.provider = "openai"
            mock_llm_client.model = "gpt-4o"
            mock_get_llm.return_value = mock_llm_client
            mock_save_db.return_value = 789

            files = {"file": ("changes.patch", io.BytesIO(sample_diff.encode()), "text/plain")}
            response = client.post("/review-diff", files=files)

            assert response.status_code == 200
            assert response.json()["metadata"]["filename"] == "changes.patch"

    def test_empty_diff_file(self, client):
        """Test that empty diff files are rejected."""
        files = {"file": ("empty.diff", io.BytesIO(b""), "text/plain")}

        response = client.post("/review-diff", files=files)

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_large_file_rejection(self, client):
        """Test that files larger than 10MB are rejected."""
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        files = {"file": ("large.diff", io.BytesIO(large_content), "text/plain")}

        response = client.post("/review-diff", files=files)

        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()

    def test_non_utf8_file(self, client):
        """Test that non-UTF-8 files are rejected."""
        # Create binary content that's not valid UTF-8
        invalid_utf8 = b"\xff\xfe\xfd\xfc"
        files = {"file": ("binary.diff", io.BytesIO(invalid_utf8), "application/octet-stream")}

        response = client.post("/review-diff", files=files)

        assert response.status_code == 400
        assert "UTF-8" in response.json()["detail"]

    @patch("ai_code_reviewer.api.routes.manual.get_llm_client")
    @patch("ai_code_reviewer.api.routes.manual.save_review_to_database")
    @patch("ai_code_reviewer.api.routes.manual.log_review_failure")
    def test_llm_error_handling(self, mock_log_failure, mock_save_db, mock_get_llm, client, sample_diff):
        """Test that LLM errors are properly handled and logged."""
        # Setup mock to raise exception
        mock_llm_client = AsyncMock()
        mock_llm_client.get_code_review = AsyncMock(side_effect=Exception("LLM API timeout"))
        mock_get_llm.return_value = mock_llm_client

        files = {"file": ("test.diff", io.BytesIO(sample_diff.encode()), "text/plain")}
        response = client.post("/review-diff", files=files)

        # Should return 500 error
        assert response.status_code == 500
        assert "Failed to get LLM review" in response.json()["detail"]

        # Verify failure was logged
        mock_log_failure.assert_called()
        call_kwargs = mock_log_failure.call_args.kwargs
        assert call_kwargs["event_type"] == "manual"
        assert call_kwargs["event_key"] == "diff_upload"
        assert call_kwargs["failure_stage"] == "llm_review"

    @patch("ai_code_reviewer.api.routes.manual.get_llm_client")
    @patch("ai_code_reviewer.api.routes.manual.save_review_to_database")
    def test_database_save_failure_still_returns_review(
        self, mock_save_db, mock_get_llm, client, sample_diff, mock_llm_review
    ):
        """Test that review is still returned even if database save fails."""
        # Setup mocks
        mock_llm_client = AsyncMock()
        mock_llm_client.get_code_review = AsyncMock(return_value=mock_llm_review)
        mock_llm_client.provider = "openai"
        mock_llm_client.model = "gpt-4o"
        mock_get_llm.return_value = mock_llm_client

        # Make database save fail
        mock_save_db.side_effect = Exception("Database connection error")

        files = {"file": ("test.diff", io.BytesIO(sample_diff.encode()), "text/plain")}
        response = client.post("/review-diff", files=files)

        # Should still return 200 with review
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["review_markdown"] == mock_llm_review
        # record_id should be None when save fails
        assert data["metadata"]["record_id"] is None

    @patch("ai_code_reviewer.api.routes.manual.get_llm_client")
    @patch("ai_code_reviewer.api.routes.manual.save_review_to_database")
    def test_response_includes_line_counts(self, mock_save_db, mock_get_llm, client, sample_diff, mock_llm_review):
        """Test that response includes correct line count statistics."""
        # Setup mocks
        mock_llm_client = AsyncMock()
        mock_llm_client.get_code_review = AsyncMock(return_value=mock_llm_review)
        mock_llm_client.provider = "openai"
        mock_llm_client.model = "gpt-4o"
        mock_get_llm.return_value = mock_llm_client
        mock_save_db.return_value = 999

        files = {"file": ("test.diff", io.BytesIO(sample_diff.encode()), "text/plain")}
        response = client.post("/review-diff", files=files)

        assert response.status_code == 200
        metadata = response.json()["metadata"]

        # Verify line counts are present
        assert "lines_total" in metadata
        assert "lines_added" in metadata
        assert "lines_removed" in metadata
        assert metadata["lines_total"] > 0
        assert metadata["lines_added"] > 0
        assert metadata["lines_removed"] > 0

        # Verify processing metadata
        assert "processing_time_seconds" in metadata
        assert "review_timestamp" in metadata
        assert "diff_size_bytes" in metadata
