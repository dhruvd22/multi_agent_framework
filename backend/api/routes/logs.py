"""
Logging API routes.

This module provides endpoints for retrieving logs and system messages.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...memory import MemoryRouter
from ...memory.schemas import MemoryQuery, MemoryType
from ..main import app

router = APIRouter()


class LogEntry(BaseModel):
    """Log entry model."""

    timestamp: datetime
    level: str
    message: str
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    metadata: dict = {}


@router.get("/", response_model=List[LogEntry])
async def get_logs(
    level: Optional[str] = Query(None, description="Filter by log level"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    router: MemoryRouter = Depends(lambda: app.state.memory_router),
):
    """
    Get log entries.

    Args:
        level: Log level filter
        agent_id: Agent ID filter
        task_id: Task ID filter
        limit: Maximum results
        offset: Result offset
        router: Memory router instance

    Returns:
        List of log entries
    """
    query = MemoryQuery(
        type=MemoryType.LOG,
        agent_id=agent_id,
        task_id=task_id,
        limit=limit,
        offset=offset,
    )

    if level:
        query.metadata_filters["level"] = level

    search_result = await router.search_items(query)

    # Convert to log entries
    logs = []
    for item in search_result.items:
        logs.append(
            LogEntry(
                timestamp=item.created_at,
                level=item.metadata.get("level", "INFO"),
                message=item.content.get("message", ""),
                agent_id=item.agent_id,
                task_id=item.task_id,
                metadata=item.metadata,
            )
        )

    return logs


@router.get("/errors")
async def get_errors(
    task_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    router: MemoryRouter = Depends(lambda: app.state.memory_router),
):
    """
    Get error log entries.

    Args:
        task_id: Optional task ID filter
        limit: Maximum results
        router: Memory router instance

    Returns:
        List of error log entries
    """
    query = MemoryQuery(
        type=MemoryType.LOG,
        task_id=task_id,
        limit=limit,
        offset=0,
    )
    query.metadata_filters["level"] = "ERROR"

    search_result = await router.search_items(query)

    errors = []
    for item in search_result.items:
        errors.append(
            LogEntry(
                timestamp=item.created_at,
                level="ERROR",
                message=item.content.get("message", ""),
                agent_id=item.agent_id,
                task_id=item.task_id,
                metadata=item.metadata,
            )
        )

    return errors


@router.get("/warnings")
async def get_warnings(
    task_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    router: MemoryRouter = Depends(lambda: app.state.memory_router),
):
    """
    Get warning log entries.

    Args:
        task_id: Optional task ID filter
        limit: Maximum results
        router: Memory router instance

    Returns:
        List of warning log entries
    """
    query = MemoryQuery(
        type=MemoryType.LOG,
        task_id=task_id,
        limit=limit,
        offset=0,
    )
    query.metadata_filters["level"] = "WARNING"

    search_result = await router.search_items(query)

    warnings = []
    for item in search_result.items:
        warnings.append(
            LogEntry(
                timestamp=item.created_at,
                level="WARNING",
                message=item.content.get("message", ""),
                agent_id=item.agent_id,
                task_id=item.task_id,
                metadata=item.metadata,
            )
        )

    return warnings

