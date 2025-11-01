"""
Task management API routes.

This module provides endpoints for creating, retrieving, and managing tasks.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ...agents.agent_executor import AgentExecutor
from ...agents.agent_registry import AgentRegistry
from ...agents.schemas import TaskRequest
from ...agents.schemas import AgentStatus, ExecutionPlan
from ..main import app

router = APIRouter()


class CreateTaskRequest(BaseModel):
    """Request model for creating a task."""

    description: str
    requirements: List[str] = []
    constraints: dict = {}


class TaskResponse(BaseModel):
    """Response model for task operations."""

    task_id: str
    status: str
    description: str
    plan: dict | None = None
    results: dict | None = None


def get_agent_executor() -> AgentExecutor:
    """Get agent executor from app state."""
    registry: AgentRegistry = app.state.agent_registry
    memory_router = app.state.memory_router
    return AgentExecutor(registry, memory_router)


@router.post("/", response_model=TaskResponse)
async def create_task(
    request: CreateTaskRequest,
    executor: AgentExecutor = Depends(get_agent_executor),
):
    """
    Create and execute a new task.

    Args:
        request: Task creation request
        executor: Agent executor instance

    Returns:
        Task response with execution results
    """
    import uuid

    task_id = str(uuid.uuid4())

    task_request = TaskRequest(
        task_id=task_id,
        description=request.description,
        requirements=request.requirements,
        constraints=request.constraints,
    )

    try:
        # Execute task
        execution_result = await executor.execute_task(task_request)

        return TaskResponse(
            task_id=task_id,
            status="completed",
            description=request.description,
            plan=execution_result.get("plan"),
            results=execution_result.get("results"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """
    Get task status and results.

    Args:
        task_id: Task identifier

    Returns:
        Task response
    """
    # TODO: Retrieve task from memory/database
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{task_id}/logs")
async def get_task_logs(task_id: str):
    """
    Get logs for a specific task.

    Args:
        task_id: Task identifier

    Returns:
        List of log entries
    """
    # TODO: Retrieve logs from memory
    return {"task_id": task_id, "logs": []}

