"""
PostgreSQL store implementation.

This module provides the PostgreSQL storage backend for structured memory data.
It uses asyncpg for async database operations and SQLAlchemy for schema management.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg
from structlog import get_logger

from ..config import get_settings
from .schemas import MemoryItem, MemoryQuery, MemorySearchResult, MemoryType

logger = get_logger(__name__)


class PostgresStore:
    """
    PostgreSQL storage backend for memory items.

    This class handles all PostgreSQL operations for storing and retrieving
    structured memory data. It uses asyncpg for async database access.

    Attributes:
        pool: AsyncPG connection pool
        settings: Application settings
    """

    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize PostgreSQL store.

        Args:
            pool: AsyncPG connection pool
        """
        self.pool = pool
        self.settings = get_settings()

    async def create_table(self) -> None:
        """
        Create the memory_items table if it doesn't exist.

        This method should be called during application startup to ensure
        the database schema is set up correctly.
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_items (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    type VARCHAR(50) NOT NULL,
                    content JSONB NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    agent_id VARCHAR(255),
                    task_id VARCHAR(255),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                """
            )
            # Create indexes separately
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_type ON memory_items(type);
                CREATE INDEX IF NOT EXISTS idx_agent_id ON memory_items(agent_id);
                CREATE INDEX IF NOT EXISTS idx_task_id ON memory_items(task_id);
                CREATE INDEX IF NOT EXISTS idx_created_at ON memory_items(created_at);
                """
            )
            # Create GIN indexes for full-text search
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_content_search ON memory_items
                USING gin(to_tsvector('english', content::text));
                CREATE INDEX IF NOT EXISTS idx_metadata ON memory_items
                USING gin(metadata);
                """
            )
        logger.info("PostgreSQL memory_items table created or verified")

    async def write(
        self,
        item: MemoryItem,
    ) -> str:
        """
        Write a memory item to PostgreSQL.

        Args:
            item: Memory item to write

        Returns:
            The ID of the created item

        Raises:
            Exception: If database operation fails
        """
        async with self.pool.acquire() as conn:
            item_id = await conn.fetchval(
                """
                INSERT INTO memory_items (type, content, metadata, agent_id, task_id, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id::text
                """,
                item.type.value,
                item.content,
                item.metadata,
                item.agent_id,
                item.task_id,
                item.created_at,
                item.updated_at,
            )

        logger.debug(
            "Memory item written to PostgreSQL",
            item_id=item_id,
            type=item.type.value,
            agent_id=item.agent_id,
            task_id=item.task_id,
        )

        return item_id

    async def read(self, item_id: str) -> Optional[MemoryItem]:
        """
        Read a memory item by ID.

        Args:
            item_id: Memory item ID

        Returns:
            Memory item if found, None otherwise
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id::text, type, content, metadata, agent_id, task_id, created_at, updated_at
                FROM memory_items
                WHERE id = $1
                """,
                item_id,
            )

        if not row:
            return None

        return MemoryItem(
            id=row["id"],
            type=MemoryType(row["type"]),
            content=row["content"],
            metadata=row["metadata"] or {},
            agent_id=row["agent_id"],
            task_id=row["task_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def update(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a memory item.

        Args:
            item_id: Memory item ID
            updates: Dictionary of fields to update

        Returns:
            True if item was updated, False if not found
        """
        updates["updated_at"] = datetime.now()

        set_clauses = []
        values = []
        param_index = 1

        for key, value in updates.items():
            if key in ["content", "metadata"]:
                set_clauses.append(f"{key} = ${param_index}::jsonb")
            else:
                set_clauses.append(f"{key} = ${param_index}")
            values.append(value)
            param_index += 1

        values.append(item_id)

        async with self.pool.acquire() as conn:
            result = await conn.execute(
                f"""
                UPDATE memory_items
                SET {', '.join(set_clauses)}
                WHERE id = ${param_index}
                """,
                *values,
            )

        updated = result == "UPDATE 1"
        logger.debug(
            "Memory item updated in PostgreSQL",
            item_id=item_id,
            updated=updated,
        )

        return updated

    async def search(self, query: MemoryQuery) -> MemorySearchResult:
        """
        Search memory items based on query parameters.

        Args:
            query: Search query parameters

        Returns:
            Search results with pagination
        """
        conditions = []
        params = []
        param_index = 1

        if query.type:
            conditions.append(f"type = ${param_index}")
            params.append(query.type.value)
            param_index += 1

        if query.agent_id:
            conditions.append(f"agent_id = ${param_index}")
            params.append(query.agent_id)
            param_index += 1

        if query.task_id:
            conditions.append(f"task_id = ${param_index}")
            params.append(query.task_id)
            param_index += 1

        if query.content_search:
            conditions.append(
                f"to_tsvector('english', content::text) @@ plainto_tsquery('english', ${param_index})"
            )
            params.append(query.content_search)
            param_index += 1

        # Metadata filters
        for key, value in query.metadata_filters.items():
            conditions.append(f"metadata->>${param_index} = ${param_index + 1}")
            params.extend([key, str(value)])
            param_index += 2

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        # Get total count
        async with self.pool.acquire() as conn:
            total = await conn.fetchval(
                f"SELECT COUNT(*) FROM memory_items WHERE {where_clause}",
                *params,
            )

            # Get results
            rows = await conn.fetch(
                f"""
                SELECT id::text, type, content, metadata, agent_id, task_id, created_at, updated_at
                FROM memory_items
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_index} OFFSET ${param_index + 1}
                """,
                *params,
                query.limit,
                query.offset,
            )

        items = [
            MemoryItem(
                id=row["id"],
                type=MemoryType(row["type"]),
                content=row["content"],
                metadata=row["metadata"] or {},
                agent_id=row["agent_id"],
                task_id=row["task_id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

        logger.debug(
            "Memory search completed",
            query_type=query.type.value if query.type else None,
            results_count=len(items),
            total=total,
        )

        return MemorySearchResult(
            items=items,
            total=total or 0,
            limit=query.limit,
            offset=query.offset,
        )

    async def delete(self, item_id: str) -> bool:
        """
        Delete a memory item.

        Args:
            item_id: Memory item ID

        Returns:
            True if item was deleted, False if not found
        """
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM memory_items WHERE id = $1",
                item_id,
            )

        deleted = result == "DELETE 1"
        logger.debug(
            "Memory item deleted from PostgreSQL",
            item_id=item_id,
            deleted=deleted,
        )

        return deleted

