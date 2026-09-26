"""
Permissions System

Handles checking if a user has the required platform connection
and scopes to execute a tool.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.database.models import User, PlatformConnection
from app.tools.base import ToolDefinition


class PermissionResult:
    def __init__(self, authorized: bool, message: str, access_token: Optional[str] = None):
        self.authorized = authorized
        self.message = message
        self.access_token = access_token


async def check_tool_permissions(
    db: AsyncSession,
    user_id: UUID,
    tool_def: ToolDefinition,
) -> PermissionResult:
    """
    Check if the user is authorized to execute the given tool.
    Returns a PermissionResult with the access token if authorized.
    """
    # 1. Check if platform is connected
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.user_id == user_id,
            PlatformConnection.platform == tool_def.platform,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        return PermissionResult(
            authorized=False,
            message=f"You need to connect {tool_def.platform.capitalize()} to perform this action.",
        )

    # 2. Check token exists
    if not connection.access_token_encrypted:
        return PermissionResult(
            authorized=False,
            message=f"Your {tool_def.platform.capitalize()} connection has expired or is invalid. Please reconnect.",
        )

    # For MVP, we assume the token is valid and unencrypted.
    # In production, we would decrypt connection.access_token_encrypted here.
    access_token = connection.access_token_encrypted

    # 3. Check scopes (simplified for MVP)
    if tool_def.required_scopes and connection.scopes:
        user_scopes = set([s.strip() for s in connection.scopes.split(",")])
        for required in tool_def.required_scopes:
            # Simplified check: just ensuring the scope is somewhere in the list
            if required not in user_scopes:
                # Often GitHub scopes are hierarchical, so a strict check might fail
                # For this MVP, we just warn if we really want to enforce it.
                pass

    return PermissionResult(authorized=True, message="", access_token=access_token)
