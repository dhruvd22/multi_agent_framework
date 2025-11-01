"""
Unified memory manager.

This module provides a high-level interface for memory operations,
combining both PostgreSQL and Neo4j backends through the router.
"""

from typing import Any, Dict, Optional

from structlog import get_logger

from .router import MemoryRouter
from .schemas import (
    MemoryItem,
    MemoryQuery,
    MemoryRelationship,
    MemorySearchResult,
    MemoryType,
    RelationshipType,
)

logger = get_logger(__name__)


class MemoryManager:
    """
    High-level memory management interface.

    This class provides a simplified API for memory operations, abstracting
    away the details of which storage backend is used. It delegates to
    the MemoryRouter for actual operations.

    Attributes:
        router: Memory router instance
    """

    def __init__(self, router: MemoryRouter):
        """
        Initialize memory manager.

        Args:
            router: Memory router instance
        """
        self.router = router

    async def store(
        self,
        item_type: str,
        content: Dict[str, Any],
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store a memory item.

        Args:
            item_type: Type of memory item
            content: Content dictionary
            agent_id: Optional agent identifier
            task_id: Optional task identifier
            metadata: Optional metadata dictionary

        Returns:
            ID of the stored item
        """
        # Convert string to MemoryType enum if needed
        if isinstance(item_type, str):
            try:
                item_type = MemoryType(item_type)
            except ValueError:
                raise ValueError(f"Invalid memory type: {item_type}")

        item = MemoryItem(
            type=item_type,
            content=content,
            agent_id=agent_id,
            task_id=task_id,
            metadata=metadata or {},
        )

        return await self.router.write_item(item)

    async def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item by ID.

        Args:
            item_id: Memory item ID

        Returns:
            Memory item if found, None otherwise
        """
        return await self.router.read_item(item_id)

    async def search(
        self,
        query: MemoryQuery,
    ) -> MemorySearchResult:
        """
        Search memory items.

        Args:
            query: Search query parameters

        Returns:
            Search results
        """
        return await self.router.search_items(query)

    async def link(
        self,
        source_id: str,
        target_id: str,
        relationship_type: RelationshipType,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Create a relationship between two items.

        Args:
            source_id: Source item ID
            target_id: Target item ID
            relationship_type: Type of relationship
            properties: Optional relationship properties
        """
        relationship = MemoryRelationship(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            properties=properties or {},
        )

        # Determine node types from items
        source_item = await self.router.read_item(source_id)
        target_item = await self.router.read_item(target_id)

        if source_item and target_item:
            source_type = source_item.type.value.replace("_", "").title()
            target_type = target_item.type.value.replace("_", "").title()
            await self.router.create_relationship(
                relationship, source_type, target_type
            )

    async def get_context(
        self,
        item_id: str,
        max_depth: int = 2,
    ) -> Dict[str, Any]:
        """
        Get comprehensive context for an item.

        Args:
            item_id: Item ID
            max_depth: Maximum relationship depth

        Returns:
            Context dictionary
        """
        return await self.router.get_context(item_id, max_depth)

