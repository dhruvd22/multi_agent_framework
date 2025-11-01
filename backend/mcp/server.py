"""
MCP Server startup and initialization.

This module provides functions to start and configure the MCP server.
"""

from typing import Optional

from structlog import get_logger

from ..config import get_settings
from .protocol import MCPServer
from .tools import (
    CodeWriterTool,
    FileManagerTool,
    ScriptExecutorTool,
    TestGeneratorTool,
    register_tool,
)

logger = get_logger(__name__)


_mcp_server: Optional[MCPServer] = None


def get_mcp_server_instance() -> MCPServer:
    """
    Get the global MCP server instance.

    Returns:
        MCPServer instance
    """
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPServer()
    return _mcp_server


def initialize_tools(workspace_root: str = "./workspace") -> None:
    """
    Initialize and register all tools.

    Args:
        workspace_root: Root directory for workspace files
    """
    tools = [
        CodeWriterTool(workspace_root=workspace_root),
        FileManagerTool(workspace_root=workspace_root),
        ScriptExecutorTool(workspace_root=workspace_root),
        TestGeneratorTool(workspace_root=workspace_root),
    ]

    for tool in tools:
        register_tool(tool)
        logger.info("Tool registered", tool_name=tool.name)

    logger.info("All tools initialized", count=len(tools))


async def start_mcp_server(host: str = "localhost", port: int = 8001) -> None:
    """
    Start the MCP server.

    Args:
        host: Server host
        port: Server port

    Note:
        This is a placeholder for future HTTP/WebSocket server implementation.
        Currently, tools are accessed directly via the MCPServer class.
    """
    logger.info("MCP server starting", host=host, port=port)

    # Initialize tools
    initialize_tools()

    # Initialize server
    server = get_mcp_server_instance()

    logger.info("MCP server ready", host=host, port=port)

    # TODO: Implement HTTP/WebSocket server for remote access
    # For now, tools are accessed directly via the server instance

