import pytest
from unittest.mock import AsyncMock, patch
import httpx
from bitbucket_client import BitbucketClient

class TestBitbucketClient:
    """Test Bitbucket API client"""
    
    @pytest.fixture
    def client(self):
        """Create Bitbucket client instance"""
        return BitbucketClient()
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, client):
        """Test successful connection to Bitbucket"""
        mock_response = {
            "version": "7.0.0",
            "displayName": "Bitbucket Server"
        }
        
        with patch.object(client, '_make_request', return_value=mock_response):
            result = await client.test_connection()
            
            assert result["status"] == "connected"
            assert result["version"] == "7.0.0"
            assert result["display_name"] == "Bitbucket Server"
    
    @pytest.mark.asyncio
    async def test_test_connection_failure(self, client):
        """Test failed connection to Bitbucket"""
        with patch.object(client, '_make_request', return_value=None):
            result = await client.test_connection()
            
            assert result["status"] == "failed"
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_pull_request_diff_success(self, client, sample_diff):
        """Test successful PR diff retrieval"""
        with patch.object(client, '_make_request_text', return_value=sample_diff):
            result = await client.get_pull_request_diff("TEST", "test-repo", 123)
            
            assert result == sample_diff
    
    @pytest.mark.asyncio
    async def test_get_pull_request_diff_not_found(self, client):
        """Test PR diff not found"""
        with patch.object(client, '_make_request_text', return_value=None):
            result = await client.get_pull_request_diff("TEST", "test-repo", 123)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_commit_diff_success(self, client, sample_diff):
        """Test successful commit diff retrieval"""
        with patch.object(client, '_make_request_text', return_value=sample_diff):
            result = await client.get_commit_diff("TEST", "test-repo", "abc123")
            
            assert result == sample_diff
    
    @pytest.mark.asyncio
    async def test_post_pull_request_comment_success(self, client):
        """Test successful PR comment posting"""
        mock_response = {"id": 456}
        
        with patch.object(client, '_make_request', return_value=mock_response):
            result = await client.post_pull_request_comment("TEST", "test-repo", 123, "Test comment")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_post_pull_request_comment_failure(self, client):
        """Test failed PR comment posting"""
        with patch.object(client, '_make_request', return_value=None):
            result = await client.post_pull_request_comment("TEST", "test-repo", 123, "Test comment")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_post_commit_comment_success(self, client):
        """Test successful commit comment posting"""
        mock_response = {"id": 789}
        
        with patch.object(client, '_make_request', return_value=mock_response):
            result = await client.post_commit_comment("TEST", "test-repo", "abc123", "Test comment")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, client):
        """Test successful HTTP request"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_response.content = b'{"test": "data"}'
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
            
            result = await client._make_request("GET", "/test")
            
            assert result == {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_make_request_error(self, client):
        """Test HTTP request error"""
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
            
            result = await client._make_request("GET", "/test")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_make_request_exception(self, client):
        """Test HTTP request exception"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request.side_effect = Exception("Connection error")
            
            result = await client._make_request("GET", "/test")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_pull_request_info(self, client):
        """Test getting pull request information"""
        mock_pr_info = {
            "id": 123,
            "title": "Test PR",
            "state": "OPEN"
        }
        
        with patch.object(client, '_make_request', return_value=mock_pr_info):
            result = await client.get_pull_request_info("TEST", "test-repo", 123)
            
            assert result == mock_pr_info
    
    @pytest.mark.asyncio
    async def test_get_commit_info(self, client):
        """Test getting commit information"""
        mock_commit_info = {
            "id": "abc123",
            "message": "Test commit",
            "author": {"name": "testuser"}
        }
        
        with patch.object(client, '_make_request', return_value=mock_commit_info):
            result = await client.get_commit_info("TEST", "test-repo", "abc123")
            
            assert result == mock_commit_info

