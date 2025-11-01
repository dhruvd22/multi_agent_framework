"""
Custom exception classes for the multi-agent framework.

These exceptions provide clear error categorization and context for debugging
and error handling throughout the framework.
"""

from typing import Any, Dict, Optional


class FrameworkError(Exception):
    """
    Base exception class for all framework errors.

    All custom exceptions inherit from this class, allowing for
    catch-all error handling when needed.
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ):
        """
        Initialize framework error.

        Args:
            message: Human-readable error message
            context: Additional context about the error
            error_code: Optional error code for programmatic handling
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.error_code = error_code

    def __str__(self) -> str:
        """Return formatted error string with context."""
        base = f"{self.__class__.__name__}: {self.message}"
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{base} ({context_str})"
        return base

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
            "error_code": self.error_code,
        }


class AgentError(FrameworkError):
    """
    Exception raised when an agent encounters an error.

    Used for agent-specific failures such as:
    - Agent execution failures
    - Agent communication errors
    - Agent state inconsistencies
    """

    pass


class TaskError(FrameworkError):
    """
    Exception raised when a task encounters an error.

    Used for task-related failures such as:
    - Task creation failures
    - Task execution failures
    - Task state transitions
    """

    pass


class MemoryError(FrameworkError):
    """
    Exception raised when memory operations fail.

    Used for memory-related failures such as:
    - Database connection errors
    - Graph store errors
    - Memory retrieval failures
    - Memory write failures

    Note: This is different from Python's built-in MemoryError.
    """

    pass


class MCPError(FrameworkError):
    """
    Exception raised when MCP server or tool operations fail.

    Used for MCP-related failures such as:
    - Tool execution errors
    - MCP protocol errors
    - Sandbox execution failures
    """

    pass


class BudgetExceededError(FrameworkError):
    """
    Exception raised when budget limits are exceeded.

    Used when:
    - Daily budget limit is exceeded
    - Per-task budget limit is exceeded
    - Budget tracking detects threshold breach
    """

    def __init__(
        self,
        message: str,
        current_cost: float,
        limit: float,
        limit_type: str = "unknown",
        **kwargs,
    ):
        """
        Initialize budget exceeded error.

        Args:
            message: Error message
            current_cost: Current cost that exceeded limit
            limit: The budget limit that was exceeded
            limit_type: Type of limit (e.g., "daily", "task")
            **kwargs: Additional arguments passed to FrameworkError
        """
        context = {
            "current_cost": current_cost,
            "limit": limit,
            "limit_type": limit_type,
            **kwargs.get("context", {}),
        }
        super().__init__(message, context=context, **kwargs)
        self.current_cost = current_cost
        self.limit = limit
        self.limit_type = limit_type


class ValidationError(FrameworkError):
    """
    Exception raised when input validation fails.

    Used for:
    - Invalid input parameters
    - Schema validation failures
    - Type validation errors
    """

    pass

