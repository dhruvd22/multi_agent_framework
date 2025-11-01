"""
WebSocket handlers for real-time updates.

This module provides WebSocket endpoints for streaming execution updates,
logs, and system events to the frontend.
"""

import json
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from structlog import get_logger

from ..main import app

router = APIRouter()
logger = get_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str = "default"):
        """
        Accept a WebSocket connection.

        Args:
            websocket: WebSocket connection
            channel: Channel name for grouping connections
        """
        await websocket.accept()

        if channel not in self.active_connections:
            self.active_connections[channel] = []

        self.active_connections[channel].append(websocket)
        logger.info("WebSocket connected", channel=channel)

    def disconnect(self, websocket: WebSocket, channel: str = "default"):
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection
            channel: Channel name
        """
        if channel in self.active_connections:
            self.active_connections[channel].remove(websocket)
            if not self.active_connections[channel]:
                del self.active_connections[channel]

        logger.info("WebSocket disconnected", channel=channel)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Send message to a specific connection.

        Args:
            message: Message dictionary
            websocket: WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error("Failed to send WebSocket message", error=str(e))

    async def broadcast(self, message: dict, channel: str = "default"):
        """
        Broadcast message to all connections in a channel.

        Args:
            message: Message dictionary
            channel: Channel name
        """
        if channel not in self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("Failed to broadcast message", error=str(e))
                disconnected.append(connection)

        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn, channel)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/execution")
async def websocket_execution(websocket: WebSocket):
    """
    WebSocket endpoint for execution updates.

    Streams real-time updates about task execution, agent activities,
    and plan progress.
    """
    await manager.connect(websocket, "execution")

    try:
        while True:
            # Receive messages from client (for future bidirectional communication)
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                logger.debug("Received WebSocket message", message=message)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in WebSocket message", data=data)

    except WebSocketDisconnect:
        manager.disconnect(websocket, "execution")


@router.websocket("/logs")
async def websocket_logs(websocket: WebSocket):
    """
    WebSocket endpoint for log streaming.

    Streams real-time logs, errors, and warnings to connected clients.
    """
    await manager.connect(websocket, "logs")

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                logger.debug("Received log WebSocket message", message=message)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in WebSocket message", data=data)

    except WebSocketDisconnect:
        manager.disconnect(websocket, "logs")


# Function to broadcast execution updates (called from agent executor)
async def broadcast_execution_update(update: dict):
    """
    Broadcast execution update to all connected clients.

    Args:
        update: Update dictionary
    """
    await manager.broadcast({"type": "execution_update", "data": update}, "execution")


# Function to broadcast log entry (called from logging system)
async def broadcast_log(log_entry: dict):
    """
    Broadcast log entry to all connected clients.

    Args:
        log_entry: Log entry dictionary
    """
    await manager.broadcast({"type": "log", "data": log_entry}, "logs")

