"""FastAPI dependency injection."""

from ai_code_reviewer.clients.bitbucket_client import BitbucketClient
from ai_code_reviewer.clients.llm_client import LLMClient


# Global client instances (initialized once)
_bitbucket_client: BitbucketClient | None = None
_llm_client: LLMClient | None = None


def get_bitbucket_client() -> BitbucketClient:
    """Get or create Bitbucket client instance"""
    global _bitbucket_client
    if _bitbucket_client is None:
        _bitbucket_client = BitbucketClient()
    return _bitbucket_client


def get_llm_client() -> LLMClient:
    """Get or create LLM client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
