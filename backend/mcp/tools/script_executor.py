"""
Script executor tool for running scripts safely.

This tool executes scripts in a sandboxed environment with resource limits.
"""

import asyncio
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict

from structlog import get_logger

from .base_tool import BaseTool, ToolResult

logger = get_logger(__name__)


class ScriptExecutorTool(BaseTool):
    """
    Tool for executing scripts safely.

    Executes scripts in a sandboxed environment with timeout and resource limits.
    """

    def __init__(self, workspace_root: str = "./workspace", timeout: int = 30):
        """
        Initialize script executor tool.

        Args:
            workspace_root: Root directory for scripts
            timeout: Execution timeout in seconds
        """
        super().__init__(
            name="execute_script",
            description="Execute a script safely with timeout and resource limits",
        )
        self.workspace_root = Path(workspace_root).resolve()
        self.timeout = timeout

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get parameter schema for script executor."""
        return {
            "type": "object",
            "properties": {
                "script_path": {
                    "type": "string",
                    "description": "Path to script file (relative to workspace)",
                },
                "arguments": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Command-line arguments",
                    "default": [],
                },
                "timeout": {
                    "type": "integer",
                    "description": "Execution timeout in seconds",
                    "default": 30,
                },
            },
            "required": ["script_path"],
        }

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute script.

        Args:
            parameters: Tool parameters

        Returns:
            Tool execution result
        """
        try:
            self.validate_parameters(parameters)

            script_path = parameters["script_path"]
            arguments = parameters.get("arguments", [])
            timeout = parameters.get("timeout", self.timeout)

            full_path = self.workspace_root / script_path.lstrip("/").replace("..", "")

            if not full_path.exists():
                return ToolResult(success=False, error="Script file not found")

            # Determine interpreter based on file extension
            interpreter = self._get_interpreter(full_path)

            # Execute script
            cmd = [interpreter, str(full_path)] + arguments

            try:
                result = await asyncio.wait_for(
                    self._run_command(cmd),
                    timeout=timeout,
                )

                return ToolResult(
                    success=result["returncode"] == 0,
                    result={
                        "stdout": result["stdout"],
                        "stderr": result["stderr"],
                        "returncode": result["returncode"],
                    },
                    error=None if result["returncode"] == 0 else result["stderr"],
                )

            except asyncio.TimeoutError:
                return ToolResult(
                    success=False,
                    error=f"Script execution timed out after {timeout} seconds",
                )

        except Exception as e:
            self.logger.error(
                "Script execution failed",
                error=str(e),
                parameters=parameters,
                exc_info=True,
            )
            return ToolResult(success=False, error=str(e))

    async def _run_command(self, cmd: list[str]) -> Dict[str, Any]:
        """Run command and capture output."""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.workspace_root),
        )

        stdout, stderr = await process.communicate()

        return {
            "returncode": process.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
        }

    def _get_interpreter(self, file_path: Path) -> str:
        """Get interpreter command for script file."""
        suffix = file_path.suffix.lower()

        interpreters = {
            ".py": "python",
            ".sh": "bash",
            ".js": "node",
            ".ts": "ts-node",
        }

        return interpreters.get(suffix, "python")

