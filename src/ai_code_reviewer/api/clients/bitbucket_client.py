import logging
from typing import Any

import httpx

from ai_code_reviewer.api.core.config import Config


logger = logging.getLogger(__name__)


class BitbucketClient:
    """Client for interacting with Bitbucket Enterprise Server API"""

    def __init__(self):
        self.base_url = Config.BITBUCKET_URL.rstrip("/")
        self.token = Config.BITBUCKET_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> dict[Any, Any] | None:
        """Make HTTP request to Bitbucket API"""
        url = f"{self.base_url}/rest/api/1.0{endpoint}"

        try:
            # nosec B501: SSL verification disabled for enterprise Bitbucket with self-signed certs
            # This is acceptable in internal enterprise networks. For production, configure proper CA certs.
            async with httpx.AsyncClient(verify=False, timeout=30.0) as client:  # nosec B501
                response = await client.request(method=method, url=url, headers=self.headers, **kwargs)

                if response.status_code == 200:
                    return response.json() if response.content else {}
                elif response.status_code == 204:
                    return {}
                else:
                    logger.error(f"Bitbucket API error: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error making request to {url}: {str(e)}")
            return None

    async def _make_request_text(self, method: str, endpoint: str, **kwargs) -> str | None:
        """Make HTTP request to Bitbucket API and return text response"""
        url = f"{self.base_url}/rest/api/1.0{endpoint}"

        try:
            # nosec B501: SSL verification disabled for enterprise Bitbucket with self-signed certs
            # This is acceptable in internal enterprise networks. For production, configure proper CA certs.
            async with httpx.AsyncClient(verify=False, timeout=30.0) as client:  # nosec B501
                response = await client.request(method=method, url=url, headers=self.headers, **kwargs)

                if response.status_code == 200:
                    result: str = response.text
                    return result
                else:
                    logger.error(f"Bitbucket API error: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error making request to {url}: {str(e)}")
            return None

    async def test_connection(self) -> dict[str, Any]:
        """Test connection to Bitbucket server"""
        try:
            response = await self._make_request("GET", "/application-properties")
            if response:
                return {
                    "status": "connected",
                    "version": response.get("version", "unknown"),
                    "display_name": response.get("displayName", "Bitbucket Server"),
                }
            else:
                return {"status": "failed", "error": "Unable to connect to Bitbucket server"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_pull_request_diff(self, project_key: str, repo_slug: str, pr_id: int) -> str | None:
        """Get diff for a pull request"""
        endpoint = f"/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/diff"

        try:
            # Get diff with context
            params = {"contextLines": 3, "whitespace": "ignore-all"}

            diff_text = await self._make_request_text("GET", endpoint, params=params)

            if diff_text:
                logger.info(f"Retrieved diff for PR {pr_id} ({len(diff_text)} characters)")
                return diff_text
            else:
                logger.warning(f"No diff found for PR {pr_id}")
                return None

        except Exception as e:
            logger.error(f"Error getting PR diff: {str(e)}")
            return None

    async def get_commit_diff(self, project_key: str, repo_slug: str, commit_id: str) -> str | None:
        """Get diff for a specific commit"""
        endpoint = f"/projects/{project_key}/repos/{repo_slug}/commits/{commit_id}/diff"

        try:
            # Get diff with context
            params = {"contextLines": 3, "whitespace": "ignore-all"}

            diff_text = await self._make_request_text("GET", endpoint, params=params)

            if diff_text:
                logger.info(f"Retrieved diff for commit {commit_id} ({len(diff_text)} characters)")
                return diff_text
            else:
                logger.warning(f"No diff found for commit {commit_id}")
                return None

        except Exception as e:
            logger.error(f"Error getting commit diff: {str(e)}")
            return None

    async def post_pull_request_comment(self, project_key: str, repo_slug: str, pr_id: int, comment: str) -> bool:
        """Post a comment on a pull request"""
        endpoint = f"/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/comments"

        try:
            payload = {"text": comment}

            response = await self._make_request("POST", endpoint, json=payload)

            if response:
                logger.info(f"Posted comment on PR {pr_id}")
                return True
            else:
                logger.error(f"Failed to post comment on PR {pr_id}")
                return False

        except Exception as e:
            logger.error(f"Error posting PR comment: {str(e)}")
            return False

    async def post_commit_comment(self, project_key: str, repo_slug: str, commit_id: str, comment: str) -> bool:
        """Post a comment on a commit"""
        endpoint = f"/projects/{project_key}/repos/{repo_slug}/commits/{commit_id}/comments"

        try:
            payload = {"text": comment}

            response = await self._make_request("POST", endpoint, json=payload)

            if response:
                logger.info(f"Posted comment on commit {commit_id}")
                return True
            else:
                logger.error(f"Failed to post comment on commit {commit_id}")
                return False

        except Exception as e:
            logger.error(f"Error posting commit comment: {str(e)}")
            return False

    async def get_pull_request_info(self, project_key: str, repo_slug: str, pr_id: int) -> dict[str, Any] | None:
        """Get pull request information"""
        endpoint = f"/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}"

        try:
            response = await self._make_request("GET", endpoint)

            if response:
                logger.info(f"Retrieved PR info for {pr_id}")
                return response
            else:
                logger.warning(f"No PR info found for {pr_id}")
                return None

        except Exception as e:
            logger.error(f"Error getting PR info: {str(e)}")
            return None

    async def get_commit_info(self, project_key: str, repo_slug: str, commit_id: str) -> dict[str, Any] | None:
        """Get commit information"""
        endpoint = f"/projects/{project_key}/repos/{repo_slug}/commits/{commit_id}"

        try:
            response = await self._make_request("GET", endpoint)

            if response:
                logger.info(f"Retrieved commit info for {commit_id}")
                return response
            else:
                logger.warning(f"No commit info found for {commit_id}")
                return None

        except Exception as e:
            logger.error(f"Error getting commit info: {str(e)}")
            return None

    async def get_repository_info(self, project_key: str, repo_slug: str) -> dict[str, Any] | None:
        """Get repository information"""
        endpoint = f"/projects/{project_key}/repos/{repo_slug}"

        try:
            response = await self._make_request("GET", endpoint)

            if response:
                logger.info(f"Retrieved repo info for {project_key}/{repo_slug}")
                return response
            else:
                logger.warning(f"No repo info found for {project_key}/{repo_slug}")
                return None

        except Exception as e:
            logger.error(f"Error getting repo info: {str(e)}")
            return None
