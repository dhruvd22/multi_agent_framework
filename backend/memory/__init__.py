"""
Memory management module.

This module provides a unified interface for memory operations across
graph store (Neo4j) and PostgreSQL. The router module intelligently
routes operations to the appropriate storage backend.
"""

from .memory_manager import MemoryManager
from .postgres_store import PostgresStore
from .router import MemoryRouter, get_memory_router
from .schemas import (
    MemoryItem,
    MemoryQuery,
    MemoryRelationship,
    MemorySearchResult,
)

__all__ = [
    "MemoryManager",
    "MemoryRouter",
    "get_memory_router",
    "PostgresStore",
    "MemoryItem",
    "MemoryQuery",
    "MemoryRelationship",
    "MemorySearchResult",
]

