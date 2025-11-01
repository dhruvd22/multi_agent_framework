"""
Test generator tool for creating unit tests.

This tool generates unit tests for code files using LLM assistance.
"""

from pathlib import Path
from typing import Any, Dict

from structlog import get_logger

from .base_tool import BaseTool, ToolResult

logger = get_logger(__name__)


class TestGeneratorTool(BaseTool):
    """
    Tool for generating unit tests.

    Uses LLM to analyze code and generate appropriate unit tests.
    """

    def __init__(self, workspace_root: str = "./workspace"):
        """
        Initialize test generator tool.

        Args:
            workspace_root: Root directory for code files
        """
        super().__init__(
            name="generate_tests",
            description="Generate unit tests for a code file using LLM analysis",
        )
        self.workspace_root = Path(workspace_root).resolve()

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get parameter schema for test generator."""
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to code file (relative to workspace)",
                },
                "test_framework": {
                    "type": "string",
                    "enum": ["pytest", "unittest", "jest", "mocha"],
                    "description": "Test framework to use",
                    "default": "pytest",
                },
                "output_path": {
                    "type": "string",
                    "description": "Path for generated test file (optional)",
                },
            },
            "required": ["file_path"],
        }

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Generate unit tests.

        Args:
            parameters: Tool parameters

        Returns:
            Tool execution result
        """
        try:
            self.validate_parameters(parameters)

            file_path = parameters["file_path"]
            test_framework = parameters.get("test_framework", "pytest")
            output_path = parameters.get("output_path")

            full_path = self.workspace_root / file_path.lstrip("/").replace("..", "")

            if not full_path.exists():
                return ToolResult(success=False, error="Code file not found")

            # Read source code
            with open(full_path, "r", encoding="utf-8") as f:
                source_code = f.read()

            # Generate test file path
            if not output_path:
                test_dir = full_path.parent / "tests"
                test_dir.mkdir(exist_ok=True)
                test_file = test_dir / f"test_{full_path.stem}.py"
            else:
                test_file = self.workspace_root / output_path.lstrip("/").replace("..", "")

            # TODO: Integrate with LLM to generate tests
            # For now, create a basic test template
            test_code = self._generate_test_template(source_code, full_path, test_framework)

            # Write test file
            test_file.parent.mkdir(parents=True, exist_ok=True)
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_code)

            logger.info(
                "Test file generated",
                source_file=str(full_path),
                test_file=str(test_file),
            )

            return ToolResult(
                success=True,
                result={
                    "test_file": str(test_file.relative_to(self.workspace_root)),
                    "framework": test_framework,
                },
            )

        except Exception as e:
            self.logger.error(
                "Test generation failed",
                error=str(e),
                parameters=parameters,
                exc_info=True,
            )
            return ToolResult(success=False, error=str(e))

    def _generate_test_template(
        self, source_code: str, source_path: Path, framework: str
    ) -> str:
        """Generate basic test template."""
        if framework == "pytest":
            return f'''"""
Generated test file for {source_path.name}
"""
import pytest
import sys
from pathlib import Path

# Add source directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# TODO: Import the module being tested
# TODO: Write test cases based on the source code

def test_example():
    """Example test - replace with actual tests."""
    assert True
'''
        else:
            return f'# Generated test file for {source_path.name}\n# Framework: {framework}\n'

