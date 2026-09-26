"""
Tasks & Activity API Routes

GET /api/tasks           — List user's tasks (activity history)
GET /api/tasks/{id}      — Get task details with tool executions
POST /api/tasks/{id}/confirm — Confirm a pending action
POST /api/tasks/{id}/cancel  — Cancel a pending action
"""

from uuid import UUID
from typing import Optional

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.database import get_db
from app.database.models import User, Task, ToolExecution
from app.auth.security import get_current_user

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


# ── Response Schemas ──────────────────────────────────────────
class ToolExecutionResponse(BaseModel):
    id: str
    tool_name: str
    platform: Optional[str]
    arguments: Optional[dict]
    status: str
    result: Optional[dict]
    error: Optional[str]
    risk_level: str
    created_at: str
    completed_at: Optional[str]


class TaskResponse(BaseModel):
    id: str
    status: str
    goal: Optional[str]
    created_at: str
    completed_at: Optional[str]


class TaskDetailResponse(BaseModel):
    id: str
    status: str
    goal: Optional[str]
    plan: Optional[dict]
    created_at: str
    completed_at: Optional[str]
    tool_executions: list[ToolExecutionResponse]


# ── Routes ────────────────────────────────────────────────────
@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """List user's tasks (activity history), most recent first."""
    result = await db.execute(
        select(Task)
        .where(Task.user_id == current_user.id)
        .order_by(desc(Task.created_at))
        .limit(limit)
        .offset(offset)
    )
    tasks = result.scalars().all()

    return [
        TaskResponse(
            id=str(t.id),
            status=t.status,
            goal=t.goal,
            created_at=t.created_at.isoformat(),
            completed_at=t.completed_at.isoformat() if t.completed_at else None,
        )
        for t in tasks
    ]


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get task details with all tool executions."""
    result = await db.execute(
        select(Task)
        .where(
            Task.id == UUID(task_id),
            Task.user_id == current_user.id,
        )
        .options(selectinload(Task.tool_executions))
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    return TaskDetailResponse(
        id=str(task.id),
        status=task.status,
        goal=task.goal,
        plan=task.plan,
        created_at=task.created_at.isoformat(),
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        tool_executions=[
            ToolExecutionResponse(
                id=str(te.id),
                tool_name=te.tool_name,
                platform=te.platform,
                arguments=te.arguments,
                status=te.status,
                result=te.result,
                error=te.error,
                risk_level=te.risk_level,
                created_at=te.created_at.isoformat(),
                completed_at=te.completed_at.isoformat() if te.completed_at else None,
            )
            for te in task.tool_executions
        ],
    )


@router.post("/{task_id}/confirm")
async def confirm_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Confirm a task that is awaiting confirmation."""
    result = await db.execute(
        select(Task).where(
            Task.id == UUID(task_id),
            Task.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    if task.status != "awaiting_confirmation":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task is not awaiting confirmation. Current status: {task.status}",
        )

    # Execute the confirmed action
    result_exec = await db.execute(
        select(ToolExecution).where(
            ToolExecution.task_id == task.id,
            ToolExecution.status == "awaiting_confirmation"
        )
    )
    execution = result_exec.scalar_one_or_none()
    
    if not execution:
        task.status = "error"
        await db.commit()
        raise HTTPException(status_code=500, detail="No awaiting tool execution found.")

    # Get connection token
    from app.database.models import PlatformConnection
    conn_result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.user_id == current_user.id,
            PlatformConnection.platform == execution.platform
        )
    )
    connection = conn_result.scalar_one_or_none()
    if not connection or not connection.access_token_encrypted:
        raise HTTPException(status_code=401, detail="Platform not connected.")

    from app.tools.registry import get_registry
    registry = get_registry()
    tool = registry.get(execution.tool_name)
    
    if not tool:
        raise HTTPException(status_code=500, detail="Tool not found in registry.")

    task.status = "in_progress"
    execution.status = "running"
    await db.commit()

    # Execute it
    tool_result = await tool.execute(execution.arguments, connection.access_token_encrypted)
    
    if tool_result.success:
        execution.status = "completed"
        execution.result = tool_result.data
        task.status = "completed"
    else:
        execution.status = "failed"
        execution.error = tool_result.error
        task.status = "failed"
        
    await db.commit()
    return {"message": tool_result.message, "success": tool_result.success, "data": tool_result.data}


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a task that is awaiting confirmation."""
    result = await db.execute(
        select(Task).where(
            Task.id == UUID(task_id),
            Task.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    if task.status not in ("awaiting_confirmation", "pending"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task cannot be cancelled. Current status: {task.status}",
        )

    task.status = "cancelled"
    return {"message": "Task cancelled."}
