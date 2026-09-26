"""
Tool Executor

Handles the safe execution of tools, including permission checks,
argument validation, and confirmation flows.
"""

from uuid import UUID
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.models import User, Task, ToolExecution
from app.tools.registry import get_registry
from app.agent.permissions import check_tool_permissions


class ExecutorResult:
    def __init__(
        self,
        success: bool,
        message: str,
        status: str = "completed",
        task_id: str = None,
        data: Any = None,
        error: str = None
    ):
        self.success = success
        self.message = message
        self.status = status
        self.task_id = task_id
        self.data = data
        self.error = error


async def execute_tool(
    db: AsyncSession,
    user_id: UUID,
    conversation_id: UUID,
    tool_name: str,
    arguments: dict,
) -> ExecutorResult:
    """
    Safely execute a tool or stage it for confirmation.
    """
    registry = get_registry()
    tool = registry.get(tool_name)

    if not tool:
        return ExecutorResult(
            success=False,
            message=f"I tried to use a tool that doesn't exist: {tool_name}.",
            status="error",
            error=f"Tool {tool_name} not found in registry."
        )

    tool_def = tool.definition

    # 1. Check permissions
    perm_result = await check_tool_permissions(db, user_id, tool_def)
    if not perm_result.authorized:
        return ExecutorResult(
            success=False,
            message=perm_result.message,
            status="error",
            error="Unauthorized"
        )

    # 2. Validate arguments
    is_valid, val_error = tool.validate_arguments(arguments)
    if not is_valid:
        return ExecutorResult(
            success=False,
            message=f"I couldn't complete the action because some information is missing: {val_error}",
            status="error",
            error=val_error
        )

    # 3. Create Task & ToolExecution records
    task = Task(
        user_id=user_id,
        conversation_id=conversation_id,
        goal=f"Execute {tool_def.name}",
        status="pending"
    )
    db.add(task)
    await db.flush()

    execution = ToolExecution(
        task_id=task.id,
        tool_name=tool_def.name,
        platform=tool_def.platform,
        arguments=arguments,
        risk_level=tool_def.risk_level.value,
        confirmation_required=tool_def.confirmation_required,
        status="pending"
    )
    db.add(execution)
    await db.flush()

    # 4. Handle confirmation
    if tool_def.confirmation_required:
        task.status = "awaiting_confirmation"
        execution.status = "awaiting_confirmation"
        await db.commit()
        return ExecutorResult(
            success=True,
            message=f"This action requires your confirmation before proceeding.\n\n**Action:** {tool_def.name}",
            status="awaiting_confirmation",
            task_id=str(task.id)
        )

    # 5. Execute immediately if safe
    execution.status = "running"
    task.status = "in_progress"
    await db.commit()

    tool_result = await tool.execute(arguments, perm_result.access_token)

    # 6. Update DB with results
    if tool_result.success:
        execution.status = "completed"
        execution.result = tool_result.data
        task.status = "completed"
    else:
        execution.status = "failed"
        execution.error = tool_result.error
        task.status = "failed"
    
    await db.commit()

    return ExecutorResult(
        success=tool_result.success,
        message=tool_result.message or ("Action completed successfully." if tool_result.success else "Action failed."),
        status="completed" if tool_result.success else "error",
        task_id=str(task.id),
        data=tool_result.data,
        error=tool_result.error
    )
