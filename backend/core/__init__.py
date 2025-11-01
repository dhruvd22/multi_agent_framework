"""
Core utilities module.

This module provides fundamental utilities used throughout the framework:
- Logging system
- Error handling
- Budget tracking
- Supabase integration
"""

from .budget import BudgetTracker, get_budget_tracker
from .exceptions import (
    AgentError,
    BudgetExceededError,
    MemoryError,
    MCPError,
    TaskError,
    ValidationError,
)
from .logger import get_logger, setup_logging
from .supabase import (
    get_supabase_client,
    get_supabase_postgres_url,
    is_supabase_configured,
)

__all__ = [
    "get_logger",
    "setup_logging",
    "BudgetTracker",
    "get_budget_tracker",
    "AgentError",
    "BudgetExceededError",
    "MemoryError",
    "MCPError",
    "TaskError",
    "ValidationError",
    "get_supabase_client",
    "get_supabase_postgres_url",
    "is_supabase_configured",
]

