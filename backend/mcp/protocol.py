"""
MCP Protocol implementation.

This module implements the Model Context Protocol for tool execution.
It handles JSON-RPC 2.0 protocol for communication between agents and tools.
"""

import json
from typing import Any, Dict, List, Optional

from structlog import get_logger

from .tools import get_tool, get_tool_registry

logger = get_logger(__name__)


class MCPServer:
    """
    MCP Server implementation using JSON-RPC 2.0.

    This server handles tool discovery and execution requests from agents.
    It implements the Model Context Protocol for standardized tool communication.
    """

    def __init__(self):
        """Initialize MCP server."""
        self.tool_registry = get_tool_registry()

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools.

        Returns:
            List of tool schemas
        """
        tools = []
        for tool in self.tool_registry.values():
            tools.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.get_parameter_schema(),
                }
            )

        logger.debug("Tools listed", count=len(tools))
        return tools

    async def call_tool(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call a tool by name.

        Args:
            tool_name: Name of the tool
            parameters: Tool parameters

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found
        """
        tool = get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")

        logger.info("Tool called", tool_name=tool_name, parameters=parameters)

        try:
            result = await tool.execute(parameters)

            return {
                "success": result.success,
                "result": result.result,
                "error": result.error,
                "metadata": result.metadata,
            }

        except Exception as e:
            logger.error(
                "Tool execution failed",
                tool_name=tool_name,
                error=str(e),
                exc_info=True,
            )
            return {
                "success": False,
                "error": str(e),
            }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle JSON-RPC 2.0 request.

        Args:
            request: JSON-RPC request

        Returns:
            JSON-RPC response
        """
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        try:
            if method == "tools/list":
                result = await self.list_tools()
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result,
                }

            elif method == "tools/call":
                tool_name = params.get("name")
                tool_params = params.get("arguments", {})

                if not tool_name:
                    raise ValueError("Tool name required")

                result = await self.call_tool(tool_name, tool_params)

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result,
                }

            else:
                raise ValueError(f"Unknown method: {method}")

        except Exception as e:
            logger.error(
                "Request handling failed",
                method=method,
                error=str(e),
                exc_info=True,
            )
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e),
                },
            }

