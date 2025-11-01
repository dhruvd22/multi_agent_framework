"""
Memory management API routes.

This module provides endpoints for searching and retrieving memory items.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...memory import MemoryRouter
from ...memory.schemas import MemoryItem, MemoryQuery, MemorySearchResult, MemoryType
from ..main import app

router = APIRouter()


def get_memory_router() -> MemoryRouter:
    """Get memory router from app state."""
    return app.state.memory_router


@router.get("/search", response_model=MemorySearchResult)
async def search_memory(
    type: MemoryType | None = Query(None, description="Filter by memory type"),
    agent_id: str | None = Query(None, description="Filter by agent ID"),
    task_id: str | None = Query(None, description="Filter by task ID"),
    content_search: str | None = Query(None, description="Full-text search"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    router: MemoryRouter = Depends(get_memory_router),
):
    """
    Search memory items.

    Args:
        type: Memory type filter
        agent_id: Agent ID filter
        task_id: Task ID filter
        content_search: Full-text search query
        limit: Maximum results
        offset: Result offset
        router: Memory router instance

    Returns:
        Search results
    """
    query = MemoryQuery(
        type=type,
        agent_id=agent_id,
        task_id=task_id,
        content_search=content_search,
        limit=limit,
        offset=offset,
    )

    return await router.search_items(query)


@router.get("/{item_id}", response_model=MemoryItem)
async def get_memory_item(
    item_id: str,
    router: MemoryRouter = Depends(get_memory_router),
):
    """
    Get a memory item by ID.

    Args:
        item_id: Memory item ID
        router: Memory router instance

    Returns:
        Memory item
    """
    item = await router.read_item(item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Memory item not found")

    return item


@router.get("/{item_id}/context")
async def get_memory_context(
    item_id: str,
    max_depth: int = Query(2, ge=1, le=5),
    router: MemoryRouter = Depends(get_memory_router),
):
    """
    Get comprehensive context for a memory item.

    Args:
        item_id: Memory item ID
        max_depth: Maximum relationship depth
        router: Memory router instance

    Returns:
        Context dictionary
    """
    return await router.get_context(item_id, max_depth)

