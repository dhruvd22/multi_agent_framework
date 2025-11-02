"""
MCP server and tools module.

This module provides the Model Context Protocol (MCP) server implementation
and tool definitions for code writing, testing, script execution, and file management.
"""

from .protocol import MCPServer
from .server import get_mcp_server_instance, initialize_tools, start_mcp_server
from .tools import (
    BaseTool,
    CodeWriterTool,
    FileManagerTool,
    ScriptExecutorTool,
    TestGeneratorTool,
    get_tool,
    get_tool_registry,
    register_tool,
)

__all__ = [
    "MCPServer",
    "get_mcp_server_instance",
    "start_mcp_server",
    "initialize_tools",
    "BaseTool",
    "CodeWriterTool",
    "FileManagerTool",
    "ScriptExecutorTool",
    "TestGeneratorTool",
    "get_tool_registry",
    "get_tool",
    "register_tool",
]

# Alias for convenience
get_mcp_server = get_mcp_server_instance

