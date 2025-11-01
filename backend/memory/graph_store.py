"""
Graph store implementation using Neo4j.

This module provides the Neo4j graph database backend for relationship-based
memory storage. It handles nodes, relationships, and graph queries.
"""

from typing import Any, Dict, List, Optional

from neo4j import AsyncGraphDatabase, AsyncSession
from structlog import get_logger

from ..config import get_settings
from .schemas import MemoryRelationship, RelationshipType

logger = get_logger(__name__)


class GraphStore:
    """
    Neo4j graph store backend for relationship-based memory.

    This class handles all Neo4j operations for storing and querying
    graph relationships between entities (agents, tasks, code files, etc.).

    Attributes:
        driver: Neo4j async driver
        settings: Application settings
    """

    def __init__(self, driver):
        """
        Initialize graph store.

        Args:
            driver: Neo4j async driver instance
        """
        self.driver = driver
        self.settings = get_settings()

    async def create_node(
        self,
        node_id: str,
        node_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Create a node in the graph.

        Args:
            node_id: Unique node identifier
            node_type: Type of node (e.g., "Agent", "Task", "CodeFile")
            properties: Node properties

        Raises:
            Exception: If database operation fails
        """
        properties = properties or {}
        properties["id"] = node_id
        properties["created_at"] = properties.get("created_at", "datetime()")

        async with self.driver.session() as session:
            await session.run(
                f"""
                MERGE (n:{node_type} {{id: $id}})
                SET n += $properties
                """,
                id=node_id,
                properties=properties,
            )

        logger.debug(
            "Node created in graph store",
            node_id=node_id,
            node_type=node_type,
        )

    async def create_relationship(
        self,
        relationship: MemoryRelationship,
        source_type: str,
        target_type: str,
    ) -> None:
        """
        Create a relationship between two nodes.

        Args:
            relationship: Relationship to create
            source_type: Type of source node
            target_type: Type of target node

        Raises:
            Exception: If database operation fails
        """
        async with self.driver.session() as session:
            await session.run(
                f"""
                MATCH (source:{source_type} {{id: $source_id}})
                MATCH (target:{target_type} {{id: $target_id}})
                MERGE (source)-[r:{relationship.relationship_type.value}]->(target)
                SET r += $properties
                """,
                source_id=relationship.source_id,
                target_id=relationship.target_id,
                properties={
                    **relationship.properties,
                    "created_at": relationship.created_at.isoformat(),
                },
            )

        logger.debug(
            "Relationship created in graph store",
            source_id=relationship.source_id,
            target_id=relationship.target_id,
            relationship_type=relationship.relationship_type.value,
        )

    async def get_node(self, node_id: str, node_type: str) -> Optional[Dict[str, Any]]:
        """
        Get a node by ID and type.

        Args:
            node_id: Node identifier
            node_type: Type of node

        Returns:
            Node properties if found, None otherwise
        """
        async with self.driver.session() as session:
            result = await session.run(
                f"""
                MATCH (n:{node_type} {{id: $id}})
                RETURN n
                """,
                id=node_id,
            )

            record = await result.single()
            if record:
                return dict(record["n"])

        return None

    async def get_relationships(
        self,
        node_id: str,
        node_type: str,
        relationship_type: Optional[RelationshipType] = None,
        direction: str = "both",
    ) -> List[Dict[str, Any]]:
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
        rel_filter = f":{relationship_type.value}" if relationship_type else ""

        if direction == "outgoing":
            match_pattern = f"(source:{node_type} {{id: $id}})-[r{rel_filter}]->(target)"
        elif direction == "incoming":
            match_pattern = f"(source)<-[r{rel_filter}]-(target:{node_type} {{id: $id}})"
        else:  # both
            match_pattern = f"(source:{node_type} {{id: $id}})-[r{rel_filter}]-(target)"

        async with self.driver.session() as session:
            result = await session.run(
                f"""
                MATCH {match_pattern}
                RETURN source, r, target, type(r) as rel_type
                """,
                id=node_id,
            )

            relationships = []
            async for record in result:
                relationships.append(
                    {
                        "source": dict(record["source"]),
                        "relationship": dict(record["r"]),
                        "target": dict(record["target"]),
                        "type": record["rel_type"],
                    }
                )

        logger.debug(
            "Relationships retrieved from graph store",
            node_id=node_id,
            count=len(relationships),
        )

        return relationships

    async def query(
        self,
        cypher: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query.

        Args:
            cypher: Cypher query string
            parameters: Query parameters

        Returns:
            Query results as list of dictionaries

        Warning:
            This method allows arbitrary Cypher queries. Use with caution
            and ensure proper input validation in production.
        """
        parameters = parameters or {}

        async with self.driver.session() as session:
            result = await session.run(cypher, **parameters)

            records = []
            async for record in result:
                records.append(dict(record))

        logger.debug(
            "Cypher query executed",
            cypher=cypher[:100],  # Log first 100 chars
            result_count=len(records),
        )

        return records

    async def delete_node(self, node_id: str, node_type: str) -> bool:
        """
        Delete a node and all its relationships.

        Args:
            node_id: Node identifier
            node_type: Type of node

        Returns:
            True if node was deleted, False if not found
        """
        async with self.driver.session() as session:
            result = await session.run(
                f"""
                MATCH (n:{node_type} {{id: $id}})
                DETACH DELETE n
                RETURN count(n) as deleted
                """,
                id=node_id,
            )

            record = await result.single()
            deleted = record["deleted"] > 0 if record else False

        logger.debug(
            "Node deleted from graph store",
            node_id=node_id,
            node_type=node_type,
            deleted=deleted,
        )

        return deleted

    async def delete_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: RelationshipType,
    ) -> bool:
        """
        Delete a relationship between two nodes.

        Args:
            source_id: Source node identifier
            target_id: Target node identifier
            relationship_type: Type of relationship

        Returns:
            True if relationship was deleted, False if not found
        """
        async with self.driver.session() as session:
            result = await session.run(
                f"""
                MATCH (source {{id: $source_id}})-[r:{relationship_type.value}]->(target {{id: $target_id}})
                DELETE r
                RETURN count(r) as deleted
                """,
                source_id=source_id,
                target_id=target_id,
            )

            record = await result.single()
            deleted = record["deleted"] > 0 if record else False

        logger.debug(
            "Relationship deleted from graph store",
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type.value,
            deleted=deleted,
        )

        return deleted

