"""Unit tests for review engine payload parsing and processing logic"""

from unittest.mock import AsyncMock, patch

import pytest

from ai_code_reviewer.core.review_engine import process_commit_review, process_pull_request_review


class TestPullRequestPayloadParsing:
    """Test pull request webhook payload parsing"""

    @pytest.mark.asyncio
    async def test_valid_pr_payload_structure(self, sample_pr_webhook):
        """Test processing with valid PR payload structure"""
        mock_bb = AsyncMock()
        mock_bb.get_pull_request_diff = AsyncMock(return_value="mock diff")
        mock_bb.get_pull_request_info = AsyncMock(
            return_value={"author": {"user": {"emailAddress": "test@example.com", "displayName": "Test User"}}}
        )

        mock_llm = AsyncMock()
        mock_llm.get_code_review = AsyncMock(return_value="Mock review with issues")

        with (
            patch("ai_code_reviewer.core.review_engine.send_review_email", new_callable=AsyncMock) as mock_send,
            patch("ai_code_reviewer.core.review_engine.save_review_to_database", new_callable=AsyncMock),
        ):
            mock_send.return_value = (True, "test@example.com", "Test User")

            await process_pull_request_review(mock_bb, mock_llm, sample_pr_webhook)

            # Verify that the correct repository info was extracted
            mock_bb.get_pull_request_diff.assert_called_once_with("TEST", "test-repo", 123)

    @pytest.mark.asyncio
    async def test_pr_payload_missing_pullrequest_key(self):
        """Test handling of payload missing 'pullRequest' key"""
        invalid_payload = {"eventKey": "pr:opened", "date": "2024-01-01T00:00:00Z"}

        mock_bb = AsyncMock()
        mock_llm = AsyncMock()

        # Should return early without calling any methods
        await process_pull_request_review(mock_bb, mock_llm, invalid_payload)

        mock_bb.get_pull_request_diff.assert_not_called()
        mock_llm.get_code_review.assert_not_called()

    @pytest.mark.asyncio
    async def test_pr_payload_missing_toref_key(self):
        """Test handling of payload missing 'toRef' key in pullRequest"""
        invalid_payload = {
            "eventKey": "pr:opened",
            "date": "2024-01-01T00:00:00Z",
            "pullRequest": {"id": 123, "title": "Test PR"},
        }

        mock_bb = AsyncMock()
        mock_llm = AsyncMock()

        # Should return early without calling any methods
        await process_pull_request_review(mock_bb, mock_llm, invalid_payload)

        mock_bb.get_pull_request_diff.assert_not_called()
        mock_llm.get_code_review.assert_not_called()

    @pytest.mark.asyncio
    async def test_pr_payload_missing_repository_in_toref(self):
        """Test handling of payload missing 'repository' in toRef"""
        invalid_payload = {
            "eventKey": "pr:opened",
            "date": "2024-01-01T00:00:00Z",
            "pullRequest": {
                "id": 123,
                "title": "Test PR",
                "toRef": {"id": "refs/heads/main", "displayId": "main"},
            },
        }

        mock_bb = AsyncMock()
        mock_llm = AsyncMock()

        # Should return early without calling any methods
        await process_pull_request_review(mock_bb, mock_llm, invalid_payload)

        mock_bb.get_pull_request_diff.assert_not_called()
        mock_llm.get_code_review.assert_not_called()

    @pytest.mark.asyncio
    async def test_pr_payload_extracts_correct_repository_info(self, sample_pr_webhook):
        """Test that repository info is correctly extracted from toRef"""
        mock_bb = AsyncMock()
        mock_bb.get_pull_request_diff = AsyncMock(return_value="mock diff")
        mock_bb.get_pull_request_info = AsyncMock(
            return_value={"author": {"user": {"emailAddress": "test@example.com", "displayName": "Test User"}}}
        )

        mock_llm = AsyncMock()
        mock_llm.get_code_review = AsyncMock(return_value="Mock review")

        with (
            patch("ai_code_reviewer.core.review_engine.send_review_email", new_callable=AsyncMock) as mock_send,
            patch("ai_code_reviewer.core.review_engine.save_review_to_database", new_callable=AsyncMock),
        ):
            mock_send.return_value = (True, "test@example.com", "Test User")

            await process_pull_request_review(mock_bb, mock_llm, sample_pr_webhook)

            # Verify correct project_key, repo_slug, and pr_id were extracted
            call_args = mock_bb.get_pull_request_diff.call_args
            assert call_args[0] == ("TEST", "test-repo", 123)

    @pytest.mark.asyncio
    async def test_pr_payload_with_updated_event(self, sample_pr_webhook):
        """Test processing PR with pr:updated event"""
        sample_pr_webhook["eventKey"] = "pr:from_ref_updated"

        mock_bb = AsyncMock()
        mock_bb.get_pull_request_diff = AsyncMock(return_value="mock diff")
        mock_bb.get_pull_request_info = AsyncMock(
            return_value={"author": {"user": {"emailAddress": "test@example.com", "displayName": "Test User"}}}
        )

        mock_llm = AsyncMock()
        mock_llm.get_code_review = AsyncMock(return_value="Mock review")

        with (
            patch("ai_code_reviewer.core.review_engine.send_review_email", new_callable=AsyncMock) as mock_send,
            patch("ai_code_reviewer.core.review_engine.save_review_to_database", new_callable=AsyncMock),
        ):
            mock_send.return_value = (True, "test@example.com", "Test User")

            await process_pull_request_review(mock_bb, mock_llm, sample_pr_webhook)

            # Should still process correctly
            mock_bb.get_pull_request_diff.assert_called_once()

    @pytest.mark.asyncio
    async def test_pr_no_diff_found(self, sample_pr_webhook):
        """Test PR processing when no diff is found"""
        mock_bb = AsyncMock()
        mock_bb.get_pull_request_diff = AsyncMock(return_value=None)

        mock_llm = AsyncMock()

        await process_pull_request_review(mock_bb, mock_llm, sample_pr_webhook)

        # Should not call LLM if no diff
        mock_llm.get_code_review.assert_not_called()

    @pytest.mark.asyncio
    async def test_pr_empty_diff_found(self, sample_pr_webhook):
        """Test PR processing when empty diff is found"""
        mock_bb = AsyncMock()
        mock_bb.get_pull_request_diff = AsyncMock(return_value="   ")

        mock_llm = AsyncMock()

        await process_pull_request_review(mock_bb, mock_llm, sample_pr_webhook)

        # Should not call LLM if diff is empty
        mock_llm.get_code_review.assert_not_called()


class TestCommitPayloadParsing:
    """Test commit webhook payload parsing"""

    @pytest.mark.asyncio
    async def test_valid_commit_payload_structure(self, sample_commit_webhook):
        """Test processing with valid commit payload structure"""
        mock_bb = AsyncMock()
        mock_bb.get_commit_diff = AsyncMock(return_value="mock diff")
        mock_bb.get_commit_info = AsyncMock(
            return_value={"author": {"emailAddress": "test@example.com", "name": "Test User"}}
        )

        mock_llm = AsyncMock()
        mock_llm.get_code_review = AsyncMock(return_value="Mock review with issues")

        with (
            patch("ai_code_reviewer.core.review_engine.send_review_email", new_callable=AsyncMock) as mock_send,
            patch("ai_code_reviewer.core.review_engine.save_review_to_database", new_callable=AsyncMock),
        ):
            mock_send.return_value = (True, "test@example.com", "Test User")

            await process_commit_review(mock_bb, mock_llm, sample_commit_webhook)

            # Verify that the correct repository info was extracted
            mock_bb.get_commit_diff.assert_called_once_with("TEST", "test-repo", "def456")

    @pytest.mark.asyncio
    async def test_commit_payload_missing_repository_key(self):
        """Test handling of commit payload missing 'repository' key"""
        invalid_payload = {
            "eventKey": "repo:refs_changed",
            "date": "2024-01-01T00:00:00Z",
            "changes": [{"toHash": "abc123"}],
        }

        mock_bb = AsyncMock()
        mock_llm = AsyncMock()

        # Should raise KeyError and be caught by exception handler
        await process_commit_review(mock_bb, mock_llm, invalid_payload)

        # Should not call these methods due to error
        mock_bb.get_commit_diff.assert_not_called()
        mock_llm.get_code_review.assert_not_called()

    @pytest.mark.asyncio
    async def test_commit_payload_no_changes(self, sample_commit_webhook):
        """Test handling of commit payload with no changes"""
        sample_commit_webhook["changes"] = []

        mock_bb = AsyncMock()
        mock_llm = AsyncMock()

        await process_commit_review(mock_bb, mock_llm, sample_commit_webhook)

        # Should not call these methods when no changes
        mock_bb.get_commit_diff.assert_not_called()
        mock_llm.get_code_review.assert_not_called()

    @pytest.mark.asyncio
    async def test_commit_payload_multiple_changes(self, sample_commit_webhook):
        """Test processing commit payload with multiple changes"""
        sample_commit_webhook["changes"] = [
            {"toHash": "commit1", "type": "UPDATE"},
            {"toHash": "commit2", "type": "UPDATE"},
        ]

        mock_bb = AsyncMock()
        mock_bb.get_commit_diff = AsyncMock(return_value="mock diff")
        mock_bb.get_commit_info = AsyncMock(
            return_value={"author": {"emailAddress": "test@example.com", "name": "Test User"}}
        )

        mock_llm = AsyncMock()
        mock_llm.get_code_review = AsyncMock(return_value="Mock review")

        with (
            patch("ai_code_reviewer.core.review_engine.send_review_email", new_callable=AsyncMock) as mock_send,
            patch("ai_code_reviewer.core.review_engine.save_review_to_database", new_callable=AsyncMock),
        ):
            mock_send.return_value = (True, "test@example.com", "Test User")

            await process_commit_review(mock_bb, mock_llm, sample_commit_webhook)

            # Should process both commits
            assert mock_bb.get_commit_diff.call_count == 2
            assert mock_llm.get_code_review.call_count == 2

    @pytest.mark.asyncio
    async def test_commit_no_diff_found(self, sample_commit_webhook):
        """Test commit processing when no diff is found"""
        mock_bb = AsyncMock()
        mock_bb.get_commit_diff = AsyncMock(return_value=None)

        mock_llm = AsyncMock()

        await process_commit_review(mock_bb, mock_llm, sample_commit_webhook)

        # Should not call LLM if no diff
        mock_llm.get_code_review.assert_not_called()

    @pytest.mark.asyncio
    async def test_commit_empty_diff_found(self, sample_commit_webhook):
        """Test commit processing when empty diff is found"""
        mock_bb = AsyncMock()
        mock_bb.get_commit_diff = AsyncMock(return_value="")

        mock_llm = AsyncMock()

        await process_commit_review(mock_bb, mock_llm, sample_commit_webhook)

        # Should not call LLM if diff is empty
        mock_llm.get_code_review.assert_not_called()


class TestManualReviewFlag:
    """Test manual review flag handling"""

    @pytest.mark.asyncio
    async def test_pr_manual_review_flag(self, sample_pr_webhook):
        """Test PR processing with manual review flag"""
        mock_bb = AsyncMock()
        mock_bb.get_pull_request_diff = AsyncMock(return_value="mock diff")
        mock_bb.get_pull_request_info = AsyncMock(
            return_value={"author": {"user": {"emailAddress": "test@example.com", "displayName": "Test User"}}}
        )

        mock_llm = AsyncMock()
        mock_llm.get_code_review = AsyncMock(return_value="Mock review")

        with (
            patch("ai_code_reviewer.core.review_engine.send_review_email", new_callable=AsyncMock) as mock_send,
            patch("ai_code_reviewer.core.review_engine.save_review_to_database", new_callable=AsyncMock) as mock_save,
        ):
            mock_send.return_value = (True, "test@example.com", "Test User")

            await process_pull_request_review(mock_bb, mock_llm, sample_pr_webhook, is_manual=True)

            # Verify manual flag is passed to send_review_email
            call_args = mock_send.call_args
            assert "AI Code Review (Manual)" in call_args[0]

            # Verify manual flag is passed to save_review_to_database
            call_kwargs = mock_save.call_args.kwargs
            assert call_kwargs["review_type"] == "manual"

    @pytest.mark.asyncio
    async def test_commit_manual_review_flag(self, sample_commit_webhook):
        """Test commit processing with manual review flag"""
        mock_bb = AsyncMock()
        mock_bb.get_commit_diff = AsyncMock(return_value="mock diff")
        mock_bb.get_commit_info = AsyncMock(
            return_value={"author": {"emailAddress": "test@example.com", "name": "Test User"}}
        )

        mock_llm = AsyncMock()
        mock_llm.get_code_review = AsyncMock(return_value="Mock review")

        with (
            patch("ai_code_reviewer.core.review_engine.send_review_email", new_callable=AsyncMock) as mock_send,
            patch("ai_code_reviewer.core.review_engine.save_review_to_database", new_callable=AsyncMock) as mock_save,
        ):
            mock_send.return_value = (True, "test@example.com", "Test User")

            await process_commit_review(mock_bb, mock_llm, sample_commit_webhook, is_manual=True)

            # Verify manual flag is passed to send_review_email
            call_args = mock_send.call_args
            assert "AI Code Review (Manual)" in call_args[0]

            # Verify manual flag is passed to save_review_to_database
            call_kwargs = mock_save.call_args.kwargs
            assert call_kwargs["review_type"] == "manual"


class TestNoIssuesHandling:
    """Test handling when LLM finds no issues"""

    @pytest.mark.asyncio
    async def test_pr_no_issues_found(self, sample_pr_webhook):
        """Test PR processing when LLM finds no issues"""
        mock_bb = AsyncMock()
        mock_bb.get_pull_request_diff = AsyncMock(return_value="mock diff")

        mock_llm = AsyncMock()
        mock_llm.get_code_review = AsyncMock(return_value="No issues found.")

        with patch("ai_code_reviewer.core.review_engine.send_review_email", new_callable=AsyncMock) as mock_send:
            await process_pull_request_review(mock_bb, mock_llm, sample_pr_webhook)

            # Should not send email when no issues found
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_commit_no_issues_found(self, sample_commit_webhook):
        """Test commit processing when LLM finds no issues"""
        mock_bb = AsyncMock()
        mock_bb.get_commit_diff = AsyncMock(return_value="mock diff")

        mock_llm = AsyncMock()
        mock_llm.get_code_review = AsyncMock(return_value="No issues found.")

        with patch("ai_code_reviewer.core.review_engine.send_review_email", new_callable=AsyncMock) as mock_send:
            await process_commit_review(mock_bb, mock_llm, sample_commit_webhook)

            # Should not send email when no issues found
            mock_send.assert_not_called()
