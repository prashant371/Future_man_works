"""
GitHub API Client

Handles all direct communication with the GitHub REST API.
Uses httpx for async HTTP requests.
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger("github-client")

GITHUB_API_BASE = "https://api.github.com"


class GitHubClient:
    """
    Async GitHub REST API client.

    All methods require an access_token obtained via OAuth.
    """

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make an authenticated GitHub API request."""
        url = f"{GITHUB_API_BASE}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method, url, headers=self.headers, **kwargs
            )

            # Handle rate limiting
            if response.status_code == 403:
                remaining = response.headers.get("X-RateLimit-Remaining", "?")
                if remaining == "0":
                    raise GitHubAPIError(
                        "GitHub API rate limit reached. Please try again later.",
                        status_code=403,
                    )

            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                message = error_data.get("message", f"GitHub API error ({response.status_code})")
                raise GitHubAPIError(message, status_code=response.status_code)

            if response.status_code == 204:
                return {}

            return response.json()

    # ── Repositories ──────────────────────────────────────────
    async def list_repositories(
        self,
        sort: Optional[str] = "updated",
        per_page: int = 10,
    ) -> list[dict]:
        """List authenticated user's repositories."""
        params = {"sort": sort, "per_page": per_page, "type": "owner"}
        return await self._request("GET", "/user/repos", params=params)

    async def get_repository(self, owner: str, repo: str) -> dict:
        """Get a single repository."""
        return await self._request("GET", f"/repos/{owner}/{repo}")

    # ── Issues ────────────────────────────────────────────────
    async def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: Optional[str] = None,
        per_page: int = 10,
    ) -> list[dict]:
        """List issues for a repository."""
        params = {"state": state, "per_page": per_page}
        if labels:
            params["labels"] = labels
        return await self._request("GET", f"/repos/{owner}/{repo}/issues", params=params)

    async def get_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> dict:
        """Get a specific issue."""
        return await self._request("GET", f"/repos/{owner}/{repo}/issues/{issue_number}")

    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> dict:
        """Create a new issue."""
        data = {"title": title}
        if body:
            data["body"] = body
        if labels:
            data["labels"] = labels
        return await self._request("POST", f"/repos/{owner}/{repo}/issues", json=data)

    async def create_comment(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        body: str,
    ) -> dict:
        """Add a comment to an issue."""
        return await self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            json={"body": body},
        )

    # ── Branches ──────────────────────────────────────────────
    async def get_branch_sha(self, owner: str, repo: str, branch: str) -> str:
        """Get the SHA of a branch's HEAD commit."""
        data = await self._request("GET", f"/repos/{owner}/{repo}/git/ref/heads/{branch}")
        return data["object"]["sha"]

    async def create_branch(
        self,
        owner: str,
        repo: str,
        branch_name: str,
        source_branch: str = "main",
    ) -> dict:
        """Create a new branch from a source branch."""
        sha = await self.get_branch_sha(owner, repo, source_branch)
        return await self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/refs",
            json={"ref": f"refs/heads/{branch_name}", "sha": sha},
        )

    # ── Pull Requests ─────────────────────────────────────────
    async def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        per_page: int = 10,
    ) -> list[dict]:
        """List pull requests for a repository."""
        params = {"state": state, "per_page": per_page}
        return await self._request("GET", f"/repos/{owner}/{repo}/pulls", params=params)

    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str = "main",
        body: Optional[str] = None,
    ) -> dict:
        """Create a pull request."""
        data = {"title": title, "head": head, "base": base}
        if body:
            data["body"] = body
        return await self._request("POST", f"/repos/{owner}/{repo}/pulls", json=data)


class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors."""

    def __init__(self, message: str, status_code: int = 0):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
