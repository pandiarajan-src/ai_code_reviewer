from unittest.mock import AsyncMock, patch

import pytest

from ai_code_reviewer.clients.llm_client import LLMClient


class TestLLMClient:
    """Test LLM client"""

    @pytest.fixture
    def client(self):
        """Create LLM client instance"""
        return LLMClient()

    @pytest.mark.asyncio
    async def test_test_openai_connection_success(self, client):
        """Test successful OpenAI connection"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "Hello"}}]}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client_instance
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await client._test_openai_connection()

            assert result["status"] == "connected"
            assert result["provider"] == "openai"

    @pytest.mark.asyncio
    async def test_test_openai_connection_failure(self, client):
        """Test failed OpenAI connection"""
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client_instance
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await client._test_openai_connection()

            assert result["status"] == "failed"
            assert "401" in result["error"]

    @pytest.mark.asyncio
    async def test_test_ollama_connection_success(self, client):
        """Test successful Ollama connection"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "llama3"}, {"name": "qwen-coder"}]}

        with patch("httpx.AsyncClient") as mock_client_class:
            # Create a mock context manager that returns a mock client
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response

            # Set up the context manager to return our mock client instance
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value = mock_client_instance
            mock_context_manager.__aexit__.return_value = None

            mock_client_class.return_value = mock_context_manager

            # Test with model that exists
            client.model = "llama3"
            result = await client._test_ollama_connection()

            assert result["status"] == "connected"
            assert result["provider"] == "ollama"
            assert "llama3" in result["available_models"]

    @pytest.mark.asyncio
    async def test_test_ollama_connection_model_not_found(self, client):
        """Test Ollama connection with model not found"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "llama3"}]}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client_instance
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            # Test with model that doesn't exist
            client.model = "nonexistent-model"
            result = await client._test_ollama_connection()

            assert result["status"] == "model_not_found"
            assert "nonexistent-model" in result["error"]

    @pytest.mark.asyncio
    async def test_get_openai_review_success(self, client, sample_diff):
        """Test successful OpenAI code review"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "The code looks good. No issues found."}}]
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client_instance
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            prompt = f"Review this code: {sample_diff}"
            result = await client._get_openai_review(prompt)

            assert result == "The code looks good. No issues found."

    @pytest.mark.asyncio
    async def test_get_openai_review_failure(self, client, sample_diff):
        """Test failed OpenAI code review"""
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client_instance
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            prompt = f"Review this code: {sample_diff}"
            result = await client._get_openai_review(prompt)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_ollama_review_success(self, client, sample_diff):
        """Test successful Ollama code review"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "The code looks good. No issues found."}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client_instance
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            prompt = f"Review this code: {sample_diff}"
            result = await client._get_ollama_review(prompt)

            assert result == "The code looks good. No issues found."

    @pytest.mark.asyncio
    async def test_get_code_review_openai(self, client, sample_diff):
        """Test code review with OpenAI provider"""
        client.provider = "openai"

        with patch.object(client, "_get_openai_review", new_callable=AsyncMock, return_value="Mock review"):
            result = await client.get_code_review(sample_diff)

            assert result == "Mock review"

    @pytest.mark.asyncio
    async def test_get_code_review_ollama(self, client, sample_diff):
        """Test code review with Ollama provider"""
        client.provider = "local_ollama"

        with patch.object(client, "_get_ollama_review", new_callable=AsyncMock, return_value="Mock review"):
            result = await client.get_code_review(sample_diff)

            assert result == "Mock review"

    @pytest.mark.asyncio
    async def test_get_code_review_unknown_provider(self, client, sample_diff):
        """Test code review with unknown provider"""
        client.provider = "unknown"

        result = await client.get_code_review(sample_diff)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_code_review_truncation(self, client):
        """Test code review with long diff truncation"""
        # Create a very long diff
        long_diff = "a" * 60000
        client.provider = "openai"

        with patch.object(
            client, "_get_openai_review", new_callable=AsyncMock, return_value="Mock review"
        ) as mock_review:
            await client.get_code_review(long_diff)

            # Check that the prompt was truncated
            call_args = mock_review.call_args[0][0]
            assert len(call_args) < 60000
            assert "[... diff truncated ...]" in call_args

    @pytest.mark.asyncio
    async def test_get_summary_review(self, client, sample_diff):
        """Test summary review for large changesets"""
        client.provider = "openai"

        with patch.object(client, "_get_openai_review", new_callable=AsyncMock, return_value="Summary review"):
            result = await client.get_summary_review(sample_diff, 10)

            assert result == "Summary review"

    def test_clean_diff_for_review(self, client):
        """Test diff cleaning functionality"""
        dirty_diff = (
            """Binary files a/image.png and b/image.png differ
This is a normal line
"""
            + "a" * 600
            + """
Another normal line"""
        )

        cleaned = client._clean_diff_for_review(dirty_diff)

        assert "Binary files" not in cleaned
        assert "differ" not in cleaned
        assert "[line truncated]" in cleaned
        assert "Another normal line" in cleaned
