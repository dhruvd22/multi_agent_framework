"""
File manager tool for file operations.

This tool provides read, write, delete, and list operations for files.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from structlog import get_logger

from ...core.exceptions import ValidationError
from .base_tool import BaseTool, ToolResult

logger = get_logger(__name__)


class FileManagerTool(BaseTool):
    """
    Tool for file management operations.

    Supports reading, writing, deleting, and listing files.
    """

    def __init__(self, workspace_root: str = "./workspace"):
        """
        Initialize file manager tool.

        Args:
            workspace_root: Root directory for files
        """
        super().__init__(
            name="file_manager",
            description="Manage files: read, write, delete, list directory contents",
        )
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get parameter schema for file manager."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "write", "delete", "list"],
                    "description": "Operation to perform",
                },
                "file_path": {
                    "type": "string",
                    "description": "Path to the file (relative to workspace root)",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write (for write operation)",
                },
            },
            "required": ["operation", "file_path"],
        }

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute file operation.

        Args:
            parameters: Tool parameters

        Returns:
            Tool execution result
        """
        try:
            self.validate_parameters(parameters)

            operation = parameters["operation"]
            file_path = parameters["file_path"]
            full_path = self._validate_path(file_path)

            if operation == "read":
                return await self._read_file(full_path)
            elif operation == "write":
                content = parameters.get("content", "")
                return await self._write_file(full_path, content)
            elif operation == "delete":
                return await self._delete_file(full_path)
            elif operation == "list":
                return await self._list_directory(full_path)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown operation: {operation}",
                )

        except Exception as e:
            self.logger.error(
                "File operation failed",
                error=str(e),
                parameters=parameters,
                exc_info=True,
            )
            return ToolResult(success=False, error=str(e))

    async def _read_file(self, file_path: Path) -> ToolResult:
        """Read file contents."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            return ToolResult(
                success=True,
                result={"content": content, "file_path": str(file_path)},
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to read file: {str(e)}")

    async def _write_file(self, file_path: Path, content: str) -> ToolResult:
        """Write file contents."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return ToolResult(
                success=True,
                result={"file_path": str(file_path), "bytes_written": len(content)},
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to write file: {str(e)}")

    async def _delete_file(self, file_path: Path) -> ToolResult:
        """Delete file."""
        try:
            if file_path.exists():
                file_path.unlink()
                return ToolResult(success=True, result={"file_path": str(file_path)})
            else:
                return ToolResult(success=False, error="File not found")
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to delete file: {str(e)}")

    async def _list_directory(self, dir_path: Path) -> ToolResult:
        """List directory contents."""
        try:
            if not dir_path.exists():
                return ToolResult(success=False, error="Directory not found")

            if not dir_path.is_dir():
                return ToolResult(success=False, error="Path is not a directory")

            items = []
            for item in dir_path.iterdir():
                items.append(
                    {
                        "name": item.name,
                        "path": str(item.relative_to(self.workspace_root)),
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None,
                    }
                )

            return ToolResult(success=True, result={"items": items})
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to list directory: {str(e)}")

    def _validate_path(self, file_path: str) -> Path:
        """Validate and sanitize file path."""
        clean_path = file_path.lstrip("/")
        clean_path = clean_path.replace("..", "")

        full_path = self.workspace_root / clean_path

        try:
            full_path.resolve().relative_to(self.workspace_root.resolve())
        except ValueError:
            raise ValidationError(
                f"Path {file_path} is outside workspace root",
                context={"file_path": file_path},
            )

        return full_path

