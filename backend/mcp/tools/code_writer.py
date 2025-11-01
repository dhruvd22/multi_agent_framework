"""
Code writer tool for creating and modifying code files.

This tool allows agents to write code to files with syntax validation
and formatting support.
"""

import os
from pathlib import Path
from typing import Any, Dict

from structlog import get_logger

from ..core.exceptions import ValidationError
from .base_tool import BaseTool, ToolResult

logger = get_logger(__name__)


class CodeWriterTool(BaseTool):
    """
    Tool for writing code to files.

    This tool writes code to files with optional syntax validation.
    It supports creating new files and updating existing ones.

    Safety:
        - Validates file paths to prevent directory traversal
        - Restricts writes to allowed directories
        - Validates code syntax (basic checks)
    """

    def __init__(self, workspace_root: str = "./workspace"):
        """
        Initialize code writer tool.

        Args:
            workspace_root: Root directory for code files
        """
        super().__init__(
            name="write_code",
            description="Write code to a file. Creates the file if it doesn't exist, updates it if it does.",
        )
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get parameter schema for code writer."""
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative path to the file from workspace root",
                },
                "content": {
                    "type": "string",
                    "description": "Code content to write",
                },
                "append": {
                    "type": "boolean",
                    "description": "Append to file instead of overwriting",
                    "default": False,
                },
            },
            "required": ["file_path", "content"],
        }

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute code writing.

        Args:
            parameters: Tool parameters

        Returns:
            Tool execution result
        """
        try:
            self.validate_parameters(parameters)

            file_path = parameters["file_path"]
            content = parameters["content"]
            append = parameters.get("append", False)

            # Validate and sanitize file path
            full_path = self._validate_path(file_path)

            # Write file
            mode = "a" if append else "w"
            encoding = "utf-8"

            with open(full_path, mode, encoding=encoding) as f:
                f.write(content)

            # Basic syntax validation (can be extended)
            if full_path.suffix in [".py", ".js", ".ts", ".tsx"]:
                syntax_valid = self._validate_syntax(full_path, content)
            else:
                syntax_valid = True

            self.logger.info(
                "Code written to file",
                file_path=str(full_path),
                append=append,
                syntax_valid=syntax_valid,
            )

            return ToolResult(
                success=True,
                result={
                    "file_path": str(full_path),
                    "bytes_written": len(content.encode(encoding)),
                    "syntax_valid": syntax_valid,
                },
                metadata={"action": "write" if not append else "append"},
            )

        except Exception as e:
            self.logger.error(
                "Code writing failed",
                error=str(e),
                parameters=parameters,
                exc_info=True,
            )
            return ToolResult(
                success=False,
                error=str(e),
            )

    def _validate_path(self, file_path: str) -> Path:
        """
        Validate and sanitize file path.

        Args:
            file_path: Relative file path

        Returns:
            Resolved absolute path

        Raises:
            ValidationError: If path is invalid
        """
        # Remove any leading slashes and normalize
        clean_path = file_path.lstrip("/")
        clean_path = clean_path.replace("..", "")  # Prevent directory traversal

        full_path = self.workspace_root / clean_path

        # Ensure path is within workspace
        try:
            full_path.resolve().relative_to(self.workspace_root.resolve())
        except ValueError:
            raise ValidationError(
                f"Path {file_path} is outside workspace root",
                context={"file_path": file_path, "workspace_root": str(self.workspace_root)},
            )

        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)

        return full_path

    def _validate_syntax(self, file_path: Path, content: str) -> bool:
        """
        Validate code syntax (basic check).

        Args:
            file_path: Path to the file
            content: File content

        Returns:
            True if syntax appears valid, False otherwise

        Note:
            This is a basic validation. For production, consider using
            language-specific parsers (ast.parse for Python, etc.)
        """
        try:
            if file_path.suffix == ".py":
                import ast

                ast.parse(content)
                return True
            # Add other language validators as needed
            return True
        except SyntaxError:
            return False
        except Exception:
            # If validation fails for any reason, assume valid
            # (don't block execution for validation errors)
            return True

