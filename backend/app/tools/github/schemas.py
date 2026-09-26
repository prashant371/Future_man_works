"""
GitHub Tool Argument Schemas

Pydantic models for validating GitHub tool arguments.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ListRepositoriesArgs(BaseModel):
    """Arguments for listing repositories."""
    sort: Optional[str] = Field(None, description="Sort by: created, updated, pushed, full_name")
    per_page: Optional[int] = Field(10, description="Number of results per page (max 100)")


class GetRepositoryArgs(BaseModel):
    """Arguments for getting a single repository."""
    owner: str = Field(..., description="Repository owner (username or org)")
    repo: str = Field(..., description="Repository name")


class ListIssuesArgs(BaseModel):
    """Arguments for listing issues."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    state: Optional[str] = Field("open", description="Filter by state: open, closed, all")
    labels: Optional[str] = Field(None, description="Comma-separated list of label names")
    per_page: Optional[int] = Field(10, description="Number of results per page")


class GetIssueArgs(BaseModel):
    """Arguments for getting a specific issue."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    issue_number: int = Field(..., description="Issue number")


class CreateIssueArgs(BaseModel):
    """Arguments for creating an issue."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    title: str = Field(..., description="Issue title")
    body: Optional[str] = Field(None, description="Issue body/description")
    labels: Optional[list[str]] = Field(None, description="List of label names")


class CreateCommentArgs(BaseModel):
    """Arguments for commenting on an issue."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    issue_number: int = Field(..., description="Issue number")
    body: str = Field(..., description="Comment text")


class CreateBranchArgs(BaseModel):
    """Arguments for creating a branch."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    branch_name: str = Field(..., description="New branch name")
    source_branch: Optional[str] = Field("main", description="Source branch to create from")


class ListPullRequestsArgs(BaseModel):
    """Arguments for listing pull requests."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    state: Optional[str] = Field("open", description="Filter by state: open, closed, all")
    per_page: Optional[int] = Field(10, description="Number of results per page")


class CreatePullRequestArgs(BaseModel):
    """Arguments for creating a pull request."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    title: str = Field(..., description="PR title")
    body: Optional[str] = Field(None, description="PR description")
    head: str = Field(..., description="Branch containing changes (head)")
    base: str = Field("main", description="Branch to merge into (base)")
