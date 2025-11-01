"""
API module for FastAPI application.

This module provides REST API endpoints and WebSocket handlers for the frontend.
"""

from .main import app
from .routes import agents, logs, memory, tasks
from .websocket import router as websocket_router

__all__ = ["app", "agents", "logs", "memory", "tasks", "websocket_router"]

