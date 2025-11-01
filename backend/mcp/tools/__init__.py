"""
Tool implementations for MCP server.

This module contains all tool implementations including code writing,
file management, test generation, and script execution.
"""

from .base_tool import BaseTool, ToolResult, ToolSchema
from .code_writer import CodeWriterTool
from .file_manager import FileManagerTool
from .script_executor import ScriptExecutorTool
from .test_generator import TestGeneratorTool

__all__ = [
    "BaseTool",
    "ToolResult",
    "ToolSchema",
    "CodeWriterTool",
    "FileManagerTool",
    "ScriptExecutorTool",
    "TestGeneratorTool",
]

# Tool registry
_tool_registry: dict[str, BaseTool] = {}


def get_tool_registry() -> dict[str, BaseTool]:
    """
    Get the global tool registry.

    Returns:
        Dictionary mapping tool names to tool instances
    """
    return _tool_registry


def register_tool(tool: BaseTool) -> None:
    """
    Register a tool in the global registry.

    Args:
        tool: Tool instance to register
    """
    _tool_registry[tool.name] = tool


def get_tool(tool_name: str) -> BaseTool | None:
    """
    Get a tool by name.

    Args:
        tool_name: Name of the tool

    Returns:
        Tool instance if found, None otherwise
    """
    return _tool_registry.get(tool_name)

