"""
Memory router module.

This module provides intelligent routing of memory operations to the appropriate
storage backend (PostgreSQL for structured data, Neo4j for relationships).
It acts as a unified interface for all memory operations.
"""

from typing import Any, Dict, Optional

from structlog import get_logger

from ..config import get_settings
from .graph_store import GraphStore
from .postgres_store import PostgresStore
from .schemas import (
    MemoryItem,
    MemoryQuery,
    MemoryRelationship,
    MemorySearchResult,
    MemoryType,
    RelationshipType,
)

logger = get_logger(__name__)


class MemoryRouter:
    """
    Intelligent router for memory operations.

    This class routes memory operations to the appropriate storage backend:
    - PostgreSQL: For structured, queryable data (conversations, logs, tasks)
    - Neo4j: For relationship-based data (dependencies, references, agent interactions)

    The router decides which backend to use based on the operation type and
    data characteristics.

    Attributes:
        postgres_store: PostgreSQL storage backend
        graph_store: Neo4j graph storage backend
    """

    def __init__(
        self,
        postgres_store: PostgresStore,
        graph_store: GraphStore,
    ):
        """
        Initialize memory router.

        Args:
            postgres_store: PostgreSQL storage instance
            graph_store: Neo4j graph store instance
        """
        self.postgres_store = postgres_store
        self.graph_store = graph_store
        self.settings = get_settings()

    async def write_item(self, item: MemoryItem) -> str:
        """
        Write a memory item to the appropriate store.

        Items are always written to PostgreSQL for structured storage.
        If the item represents an entity that should have relationships,
        a corresponding node is also created in the graph store.

        Args:
            item: Memory item to write

        Returns:
            The ID of the created item

        Example:
            ```python
            item = MemoryItem(
                type=MemoryType.TASK,
                content={"description": "Build API"},
                agent_id="planner"
            )
            item_id = await router.write_item(item)
            ```
        """
        # Always write to PostgreSQL
        item_id = await self.postgres_store.write(item)

        # Create corresponding node in graph store for certain types
        if item.type in [
            MemoryType.TASK,
            MemoryType.CODE_FILE,
            MemoryType.AGENT_STATE,
        ]:
            await self.graph_store.create_node(
                node_id=item_id,
                node_type=item.type.value.replace("_", "").title(),
                properties={
                    "type": item.type.value,
                    "agent_id": item.agent_id,
                    "task_id": item.task_id,
                },
            )

        logger.info(
            "Memory item written",
            item_id=item_id,
            type=item.type.value,
            stored_in="postgres+graph" if item.type in [MemoryType.TASK, MemoryType.CODE_FILE, MemoryType.AGENT_STATE] else "postgres",
        )

        return item_id

    async def read_item(self, item_id: str) -> Optional[MemoryItem]:
        """
        Read a memory item by ID.

        Args:
            item_id: Memory item ID

        Returns:
            Memory item if found, None otherwise
        """
        return await self.postgres_store.read(item_id)

    async def update_item(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a memory item.

        Args:
            item_id: Memory item ID
            updates: Dictionary of fields to update

        Returns:
            True if item was updated, False if not found
        """
        updated = await self.postgres_store.update(item_id, updates)

        # Also update graph node if it exists
        if updated:
            # Try to update graph node properties
            item = await self.postgres_store.read(item_id)
            if item and item.type in [
                MemoryType.TASK,
                MemoryType.CODE_FILE,
                MemoryType.AGENT_STATE,
            ]:
                node_properties = {
                    k: v
                    for k, v in updates.items()
                    if k in ["agent_id", "task_id", "metadata"]
                }
                if node_properties:
                    await self.graph_store.create_node(
                        node_id=item_id,
                        node_type=item.type.value.replace("_", "").title(),
                        properties=node_properties,
                    )

        return updated

    async def search_items(self, query: MemoryQuery) -> MemorySearchResult:
        """
        Search memory items.

        This operation uses PostgreSQL for full-text search and filtering.

        Args:
            query: Search query parameters

        Returns:
            Search results with pagination

        Example:
            ```python
            query = MemoryQuery(
                type=MemoryType.TASK,
                agent_id="planner",
                content_search="API",
                limit=10
            )
            results = await router.search_items(query)
            ```
        """
        return await self.postgres_store.search(query)

    async def create_relationship(
        self,
        relationship: MemoryRelationship,
        source_type: str,
        target_type: str,
    ) -> None:
        """
        Create a relationship in the graph store.

        Args:
            relationship: Relationship to create
            source_type: Type of source node
            target_type: Type of target node

        Example:
            ```python
            relationship = MemoryRelationship(
                source_id="task_123",
                target_id="code_file_456",
                relationship_type=RelationshipType.CREATES
            )
            await router.create_relationship(relationship, "Task", "Codefile")
            ```
        """
        await self.graph_store.create_relationship(
            relationship, source_type, target_type
        )

    async def get_relationships(
        self,
        node_id: str,
        node_type: str,
        relationship_type: Optional[RelationshipType] = None,
        direction: str = "both",
    ) -> list[Dict[str, Any]]:
        """
        Get relationships for a node.

        Args:
            node_id: Node identifier
            node_type: Type of node
            relationship_type: Optional filter by relationship type
            direction: Relationship direction ("outgoing", "incoming", "both")

        Returns:
            List of relationships with connected nodes
        """
        return await self.graph_store.get_relationships(
            node_id, node_type, relationship_type, direction
        )

    async def get_context(
        self,
        item_id: str,
        max_depth: int = 2,
    ) -> Dict[str, Any]:
        """
        Get comprehensive context for a memory item.

        This method retrieves:
        1. The item itself from PostgreSQL
        2. Related items via graph relationships
        3. Contextual information from related entities

        Args:
            item_id: Memory item ID
            max_depth: Maximum depth to traverse relationships

        Returns:
            Dictionary containing the item and its context

        Example:
            ```python
            context = await router.get_context("task_123", max_depth=2)
            # Returns: {
            #   "item": MemoryItem(...),
            #   "relationships": [...],
            #   "related_items": [...]
            # }
            ```
        """
        # Get the item
        item = await self.read_item(item_id)
        if not item:
            return {}

        context: Dict[str, Any] = {
            "item": item,
            "relationships": [],
            "related_items": [],
        }

        # Get relationships if this is a graph-backed item
        if item.type in [
            MemoryType.TASK,
            MemoryType.CODE_FILE,
            MemoryType.AGENT_STATE,
        ]:
            node_type = item.type.value.replace("_", "").title()
            relationships = await self.get_relationships(
                item_id, node_type, direction="both"
            )
            context["relationships"] = relationships

            # Get related items
            for rel in relationships:
                related_id = (
                    rel["target"]["id"]
                    if rel["source"]["id"] == item_id
                    else rel["source"]["id"]
                )
                related_item = await self.read_item(related_id)
                if related_item:
                    context["related_items"].append(related_item)

        logger.debug(
            "Context retrieved for memory item",
            item_id=item_id,
            relationships_count=len(context.get("relationships", [])),
            related_items_count=len(context.get("related_items", [])),
        )

        return context

    async def delete_item(self, item_id: str) -> bool:
        """
        Delete a memory item and its relationships.

        Args:
            item_id: Memory item ID

        Returns:
            True if item was deleted, False if not found
        """
        # Get item first to check if it has graph representation
        item = await self.read_item(item_id)
        if not item:
            return False

        # Delete from graph store if applicable
        if item.type in [
            MemoryType.TASK,
            MemoryType.CODE_FILE,
            MemoryType.AGENT_STATE,
        ]:
            node_type = item.type.value.replace("_", "").title()
            await self.graph_store.delete_node(item_id, node_type)

        # Delete from PostgreSQL
        return await self.postgres_store.delete(item_id)


# Global memory router instance
_memory_router: Optional[MemoryRouter] = None


def get_memory_router() -> MemoryRouter:
    """
    Get the global memory router instance.

    Returns:
        MemoryRouter: Singleton memory router instance

    Note:
        This function assumes the router has been initialized with
        database connections. Initialization should happen during
        application startup.
    """
    global _memory_router
    if _memory_router is None:
        raise RuntimeError(
            "Memory router not initialized. Call initialize_memory_router() first."
        )
    return _memory_router


def initialize_memory_router(
    postgres_store: PostgresStore,
    graph_store: GraphStore,
) -> MemoryRouter:
    """
    Initialize the global memory router.

    Args:
        postgres_store: PostgreSQL storage instance
        graph_store: Neo4j graph store instance

    Returns:
        Initialized memory router instance

    This function should be called during application startup after
    database connections are established.
    """
    global _memory_router
    _memory_router = MemoryRouter(postgres_store, graph_store)
    logger.info("Memory router initialized")
    return _memory_router

