"""
Data models and schemas for memory operations.

This module defines Pydantic models for all memory-related data structures,
ensuring type safety and validation throughout the memory system.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Types of memory items."""

    CONVERSATION = "conversation"
    TASK = "task"
    CODE_FILE = "code_file"
    TEST = "test"
    LOG = "log"
    AGENT_STATE = "agent_state"
    DEPENDENCY = "dependency"


class RelationshipType(str, Enum):
    """Types of relationships in the graph store."""

    CREATES = "creates"
    DEPENDS_ON = "depends_on"
    REFERENCES = "references"
    MODIFIES = "modifies"
    CALLS = "calls"
    TESTED_BY = "tested_by"
    FOLLOWS = "follows"


class MemoryItem(BaseModel):
    """
    Represents a memory item stored in PostgreSQL.

    This model represents structured data that can be queried efficiently
    using SQL. Suitable for logs, conversations, task history, etc.
    """

    id: Optional[str] = Field(default=None, description="Unique identifier")
    type: MemoryType = Field(..., description="Type of memory item")
    content: Dict[str, Any] = Field(..., description="Content of the memory item")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    agent_id: Optional[str] = Field(default=None, description="Associated agent ID")
    task_id: Optional[str] = Field(default=None, description="Associated task ID")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Update timestamp")

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class MemoryRelationship(BaseModel):
    """
    Represents a relationship in the graph store.

    This model represents relationships between entities in Neo4j.
    Suitable for tracking dependencies, references, and agent interactions.
    """

    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Relationship properties"
    )
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class MemoryQuery(BaseModel):
    """
    Query parameters for memory search operations.

    This model defines how to search and filter memory items.
    """

    type: Optional[MemoryType] = Field(default=None, description="Filter by memory type")
    agent_id: Optional[str] = Field(default=None, description="Filter by agent ID")
    task_id: Optional[str] = Field(default=None, description="Filter by task ID")
    content_search: Optional[str] = Field(
        default=None, description="Full-text search in content"
    )
    metadata_filters: Dict[str, Any] = Field(
        default_factory=dict, description="Filter by metadata fields"
    )
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Result offset")


class MemorySearchResult(BaseModel):
    """
    Result of a memory search operation.

    Contains the search results and pagination information.
    """

    items: List[MemoryItem] = Field(default_factory=list, description="Search results")
    total: int = Field(default=0, description="Total number of matching items")
    limit: int = Field(default=100, description="Results per page")
    offset: int = Field(default=0, description="Current offset")

