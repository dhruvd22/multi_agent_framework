"""
Base tool class for MCP tools.

This module provides the BaseTool class that all MCP tools inherit from.
It defines the interface for tool registration and execution.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from structlog import get_logger

logger = get_logger(__name__)


class ToolSchema(BaseModel):
    """Schema definition for a tool."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Tool parameter schema"
    )


class ToolResult(BaseModel):
    """Result from tool execution."""

    success: bool = Field(..., description="Whether execution succeeded")
    result: Any = Field(default=None, description="Execution result")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class BaseTool(ABC):
    """
    Base class for all MCP tools.

    This class defines the interface that all tools must implement.
    Tools are registered with the MCP server and can be called by agents.

    Attributes:
        name: Tool name (must be unique)
        description: Tool description
        schema: Tool schema definition
    """

    def __init__(self, name: str, description: str):
        """
        Initialize base tool.

        Args:
            name: Tool name (must be unique)
            description: Tool description
        """
        self.name = name
        self.description = description
        self.schema = self._generate_schema()
        self.logger = logger.bind(tool=name)

    def _generate_schema(self) -> ToolSchema:
        """
        Generate tool schema from class definition.

        Returns:
            Tool schema definition
        """
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=self.get_parameter_schema(),
        )

    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool with given parameters.

        Args:
            parameters: Tool parameters

        Returns:
            Tool execution result

        Raises:
            Exception: If tool execution fails
        """
        pass

    @abstractmethod
    def get_parameter_schema(self) -> Dict[str, Any]:
        """
        Get JSON schema for tool parameters.

        Returns:
            JSON schema dictionary

        Example:
            {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file"
                    }
                },
                "required": ["file_path"]
            }
        """
        pass

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate tool parameters.

        Args:
            parameters: Parameters to validate

        Returns:
            True if parameters are valid

        Raises:
            ValueError: If parameters are invalid
        """
        schema = self.get_parameter_schema()
        required = schema.get("required", [])

        for param in required:
            if param not in parameters:
                raise ValueError(f"Missing required parameter: {param}")

        return True

