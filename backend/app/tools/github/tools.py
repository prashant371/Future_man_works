"""
GitHub Tools

All 8 GitHub tools as defined in the PRD:
  1. github_list_repositories
  2. github_get_repository
  3. github_list_issues
  4. github_create_issue
  5. github_comment_issue
  6. github_create_branch
  7. github_list_pull_requests
  8. github_create_pull_request

Each tool extends BaseTool and uses the GitHubClient.
"""

import logging
from app.tools.base import BaseTool, ToolDefinition, ToolResult, ToolArgument, RiskLevel
from app.tools.github.client import GitHubClient, GitHubAPIError

logger = logging.getLogger("github-tools")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. List Repositories
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ListRepositoriesTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="github_list_repositories",
            description="List the authenticated user's GitHub repositories. Returns repository names, descriptions, languages, and URLs.",
            platform="github",
            risk_level=RiskLevel.LOW,
            confirmation_required=False,
            arguments=[
                ToolArgument(name="sort", description="Sort by: created, updated, pushed, full_name", required=False, default="updated"),
                ToolArgument(name="per_page", description="Number of results (max 100)", type="integer", required=False, default=10),
            ],
            required_scopes=["repo"],
        )

    async def execute(self, arguments: dict, access_token: str) -> ToolResult:
        try:
            client = GitHubClient(access_token)
            repos = await client.list_repositories(
                sort=arguments.get("sort", "updated"),
                per_page=arguments.get("per_page", 10),
            )
            repo_list = [
                {
                    "name": r["name"],
                    "full_name": r["full_name"],
                    "description": r.get("description", ""),
                    "language": r.get("language", ""),
                    "private": r.get("private", False),
                    "url": r["html_url"],
                    "updated_at": r.get("updated_at", ""),
                    "stars": r.get("stargazers_count", 0),
                }
                for r in repos
            ]
            return ToolResult(
                success=True,
                data={"repositories": repo_list, "count": len(repo_list)},
                message=f"Found {len(repo_list)} repositories.",
            )
        except GitHubAPIError as e:
            return ToolResult(success=False, error=e.message)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. Get Repository
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class GetRepositoryTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="github_get_repository",
            description="Get detailed information about a specific GitHub repository including description, language, stars, forks, and open issues count.",
            platform="github",
            risk_level=RiskLevel.LOW,
            confirmation_required=False,
            arguments=[
                ToolArgument(name="owner", description="Repository owner (username or organization)"),
                ToolArgument(name="repo", description="Repository name"),
            ],
            required_scopes=["repo"],
        )

    async def execute(self, arguments: dict, access_token: str) -> ToolResult:
        try:
            client = GitHubClient(access_token)
            r = await client.get_repository(arguments["owner"], arguments["repo"])
            repo_info = {
                "name": r["name"],
                "full_name": r["full_name"],
                "description": r.get("description", ""),
                "language": r.get("language", ""),
                "private": r.get("private", False),
                "url": r["html_url"],
                "default_branch": r.get("default_branch", "main"),
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "open_issues": r.get("open_issues_count", 0),
                "created_at": r.get("created_at", ""),
                "updated_at": r.get("updated_at", ""),
            }
            return ToolResult(
                success=True,
                data={"repository": repo_info},
                message=f"Repository: {r['full_name']}",
                url=r["html_url"],
            )
        except GitHubAPIError as e:
            return ToolResult(success=False, error=e.message)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. List Issues
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ListIssuesTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="github_list_issues",
            description="List issues for a specific GitHub repository. Can filter by state (open/closed/all) and labels.",
            platform="github",
            risk_level=RiskLevel.LOW,
            confirmation_required=False,
            arguments=[
                ToolArgument(name="owner", description="Repository owner"),
                ToolArgument(name="repo", description="Repository name"),
                ToolArgument(name="state", description="Filter: open, closed, or all", required=False, default="open"),
                ToolArgument(name="labels", description="Comma-separated label names to filter by", required=False),
                ToolArgument(name="per_page", description="Number of results", type="integer", required=False, default=10),
            ],
            required_scopes=["repo"],
        )

    async def execute(self, arguments: dict, access_token: str) -> ToolResult:
        try:
            client = GitHubClient(access_token)
            issues = await client.list_issues(
                owner=arguments["owner"],
                repo=arguments["repo"],
                state=arguments.get("state", "open"),
                labels=arguments.get("labels"),
                per_page=arguments.get("per_page", 10),
            )
            # Filter out pull requests (GitHub API returns PRs as issues)
            issue_list = [
                {
                    "number": i["number"],
                    "title": i["title"],
                    "state": i["state"],
                    "labels": [l["name"] for l in i.get("labels", [])],
                    "url": i["html_url"],
                    "created_at": i.get("created_at", ""),
                    "user": i.get("user", {}).get("login", ""),
                }
                for i in issues
                if "pull_request" not in i
            ]
            return ToolResult(
                success=True,
                data={"issues": issue_list, "count": len(issue_list)},
                message=f"Found {len(issue_list)} issues in {arguments['owner']}/{arguments['repo']}.",
            )
        except GitHubAPIError as e:
            return ToolResult(success=False, error=e.message)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. Create Issue
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class CreateIssueTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="github_create_issue",
            description="Create a new issue in a GitHub repository. Requires repository owner, repo name, and issue title. Optionally accepts a body and labels.",
            platform="github",
            risk_level=RiskLevel.MEDIUM,
            confirmation_required=True,
            arguments=[
                ToolArgument(name="owner", description="Repository owner"),
                ToolArgument(name="repo", description="Repository name"),
                ToolArgument(name="title", description="Issue title"),
                ToolArgument(name="body", description="Issue description/body", required=False),
                ToolArgument(name="labels", description="List of label names", type="array", required=False),
            ],
            required_scopes=["repo"],
        )

    async def execute(self, arguments: dict, access_token: str) -> ToolResult:
        try:
            client = GitHubClient(access_token)
            issue = await client.create_issue(
                owner=arguments["owner"],
                repo=arguments["repo"],
                title=arguments["title"],
                body=arguments.get("body"),
                labels=arguments.get("labels"),
            )
            return ToolResult(
                success=True,
                data={
                    "number": issue["number"],
                    "title": issue["title"],
                    "url": issue["html_url"],
                    "state": issue["state"],
                },
                message=f"✓ Issue #{issue['number']} created: {issue['title']}",
                url=issue["html_url"],
            )
        except GitHubAPIError as e:
            return ToolResult(success=False, error=e.message)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. Comment on Issue
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class CreateCommentTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="github_create_comment",
            description="Add a comment to an existing GitHub issue.",
            platform="github",
            risk_level=RiskLevel.MEDIUM,
            confirmation_required=True,
            arguments=[
                ToolArgument(name="owner", description="Repository owner"),
                ToolArgument(name="repo", description="Repository name"),
                ToolArgument(name="issue_number", description="Issue number", type="integer"),
                ToolArgument(name="body", description="Comment text"),
            ],
            required_scopes=["repo"],
        )

    async def execute(self, arguments: dict, access_token: str) -> ToolResult:
        try:
            client = GitHubClient(access_token)
            comment = await client.create_comment(
                owner=arguments["owner"],
                repo=arguments["repo"],
                issue_number=int(arguments["issue_number"]),
                body=arguments["body"],
            )
            return ToolResult(
                success=True,
                data={"comment_id": comment["id"], "url": comment["html_url"]},
                message=f"✓ Comment added to issue #{arguments['issue_number']}.",
                url=comment["html_url"],
            )
        except GitHubAPIError as e:
            return ToolResult(success=False, error=e.message)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. Create Branch
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class CreateBranchTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="github_create_branch",
            description="Create a new branch in a GitHub repository. Specify the branch name and optionally the source branch to create from (defaults to main).",
            platform="github",
            risk_level=RiskLevel.MEDIUM,
            confirmation_required=True,
            arguments=[
                ToolArgument(name="owner", description="Repository owner"),
                ToolArgument(name="repo", description="Repository name"),
                ToolArgument(name="branch_name", description="New branch name (e.g., feature/dark-mode)"),
                ToolArgument(name="source_branch", description="Source branch to create from", required=False, default="main"),
            ],
            required_scopes=["repo"],
        )

    async def execute(self, arguments: dict, access_token: str) -> ToolResult:
        try:
            client = GitHubClient(access_token)
            result = await client.create_branch(
                owner=arguments["owner"],
                repo=arguments["repo"],
                branch_name=arguments["branch_name"],
                source_branch=arguments.get("source_branch", "main"),
            )
            return ToolResult(
                success=True,
                data={"ref": result.get("ref", ""), "sha": result.get("object", {}).get("sha", "")},
                message=f"✓ Branch '{arguments['branch_name']}' created from '{arguments.get('source_branch', 'main')}'.",
            )
        except GitHubAPIError as e:
            return ToolResult(success=False, error=e.message)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. List Pull Requests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ListPullRequestsTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="github_list_pull_requests",
            description="List pull requests for a GitHub repository. Can filter by state (open/closed/all).",
            platform="github",
            risk_level=RiskLevel.LOW,
            confirmation_required=False,
            arguments=[
                ToolArgument(name="owner", description="Repository owner"),
                ToolArgument(name="repo", description="Repository name"),
                ToolArgument(name="state", description="Filter: open, closed, or all", required=False, default="open"),
                ToolArgument(name="per_page", description="Number of results", type="integer", required=False, default=10),
            ],
            required_scopes=["repo"],
        )

    async def execute(self, arguments: dict, access_token: str) -> ToolResult:
        try:
            client = GitHubClient(access_token)
            prs = await client.list_pull_requests(
                owner=arguments["owner"],
                repo=arguments["repo"],
                state=arguments.get("state", "open"),
                per_page=arguments.get("per_page", 10),
            )
            pr_list = [
                {
                    "number": pr["number"],
                    "title": pr["title"],
                    "state": pr["state"],
                    "head": pr["head"]["ref"],
                    "base": pr["base"]["ref"],
                    "url": pr["html_url"],
                    "user": pr.get("user", {}).get("login", ""),
                    "created_at": pr.get("created_at", ""),
                }
                for pr in prs
            ]
            return ToolResult(
                success=True,
                data={"pull_requests": pr_list, "count": len(pr_list)},
                message=f"Found {len(pr_list)} pull requests in {arguments['owner']}/{arguments['repo']}.",
            )
        except GitHubAPIError as e:
            return ToolResult(success=False, error=e.message)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. Create Pull Request
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class CreatePullRequestTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="github_create_pull_request",
            description="Create a pull request in a GitHub repository. Requires the head branch (with changes) and base branch (to merge into). Creating a PR is a SENSITIVE action that requires confirmation.",
            platform="github",
            risk_level=RiskLevel.HIGH,
            confirmation_required=True,
            arguments=[
                ToolArgument(name="owner", description="Repository owner"),
                ToolArgument(name="repo", description="Repository name"),
                ToolArgument(name="title", description="Pull request title"),
                ToolArgument(name="head", description="Branch containing changes"),
                ToolArgument(name="base", description="Branch to merge into", required=False, default="main"),
                ToolArgument(name="body", description="Pull request description", required=False),
            ],
            required_scopes=["repo"],
        )

    async def execute(self, arguments: dict, access_token: str) -> ToolResult:
        try:
            client = GitHubClient(access_token)
            pr = await client.create_pull_request(
                owner=arguments["owner"],
                repo=arguments["repo"],
                title=arguments["title"],
                head=arguments["head"],
                base=arguments.get("base", "main"),
                body=arguments.get("body"),
            )
            return ToolResult(
                success=True,
                data={
                    "number": pr["number"],
                    "title": pr["title"],
                    "url": pr["html_url"],
                    "state": pr["state"],
                    "head": pr["head"]["ref"],
                    "base": pr["base"]["ref"],
                },
                message=f"✓ Pull request #{pr['number']} created: {pr['title']}",
                url=pr["html_url"],
            )
        except GitHubAPIError as e:
            return ToolResult(success=False, error=e.message)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# ── Registration Helper ──────────────────────────────────────
def register_github_tools(registry) -> None:
    """Register all GitHub tools with the tool registry."""
    tools = [
        ListRepositoriesTool(),
        GetRepositoryTool(),
        ListIssuesTool(),
        CreateIssueTool(),
        CommentIssueTool(),
        CreateBranchTool(),
        ListPullRequestsTool(),
        CreatePullRequestTool(),
    ]
    for tool in tools:
        registry.register(tool)
    logger.info(f"Registered {len(tools)} GitHub tools.")
