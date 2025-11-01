"""
Structured logging system using structlog.

This module provides a centralized logging system that outputs structured JSON logs.
Logs are LLM-friendly with clear context and are suitable for observability systems.
"""

import logging
import sys
from typing import Any, Dict, Optional

import structlog
from structlog.types import Processor


def setup_logging(log_level: str = "INFO", json_logs: bool = True) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to output logs in JSON format (default: True)

    This function sets up structlog with:
    - JSON formatting for structured logs
    - Timestamp, level, logger name, and message
    - Exception traceback formatting
    - Context processors for request IDs, agent names, etc.
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Configure structlog processors
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend(
            [
                structlog.dev.ConsoleRenderer(),
            ]
        )

    # Add exception processor last
    processors.append(structlog.processors.format_exc_info)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__). If None, uses the calling module.

    Returns:
        A bound logger instance with structured logging capabilities.

    Usage:
        ```python
        logger = get_logger(__name__)
        logger.info("Task started", task_id="123", agent="planner")
        logger.error("Operation failed", error=str(e), extra_context={"key": "value"})
        ```

    The logger supports context binding:
        ```python
        logger = logger.bind(agent="planner", task_id="123")
        logger.info("Processing step")  # Will include agent and task_id
        ```
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class.

    Usage:
        ```python
        class MyAgent(LoggerMixin):
            def __init__(self):
                super().__init__()
                self.logger = self.get_logger()

            def do_something(self):
                self.logger.info("Doing something", context={"key": "value"})
        ```
    """

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """
        Get a logger instance bound to this class.

        Returns:
            A logger instance with the class name as logger name.
        """
        return get_logger(self.__class__.__name__)

