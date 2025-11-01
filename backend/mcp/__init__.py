"""
MCP server and tools module.

This module provides the Model Context Protocol (MCP) server implementation
and tool definitions for code writing, testing, script execution, and file management.
"""

from .protocol import MCPServer, get_mcp_server
from .server import initialize_tools, start_mcp_server
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
    "get_mcp_server",
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

