"""
Builder/Executor agent implementation.

The Builder agent is responsible for executing code, writing files, running tests,
and executing scripts as part of task completion.
"""

from typing import Any, Dict

from structlog import get_logger

from ..memory import MemoryRouter
from .base_agent import BaseAgent
from .schemas import AgentCapabilities, AgentResponse, AgentStatus, TaskRequest

logger = get_logger(__name__)


class BuilderAgent(BaseAgent):
    """
    Builder/Executor agent for code execution and file operations.

    This agent handles:
    - Writing code files
    - Executing scripts
    - Running tests
    - File management operations

    Capabilities:
        - can_execute: True
        - can_write_code: True
        - can_run_tests: True
        - can_execute_scripts: True
    """

    def __init__(
        self,
        agent_id: str = "builder",
        memory_router: MemoryRouter | None = None,
    ):
        """
        Initialize Builder agent.

        Args:
            agent_id: Agent identifier (default: "builder")
            memory_router: Optional memory router instance
        """
        capabilities = AgentCapabilities(
            can_execute=True,
            can_write_code=True,
            can_run_tests=True,
            can_execute_scripts=True,
        )
        super().__init__(agent_id, capabilities, memory_router)

    async def execute(
        self,
        task_request: TaskRequest,
        context: Dict[str, Any],
    ) -> AgentResponse:
        """
        Execute building/execution logic.

        This method uses the LLM to understand what needs to be built/executed,
        then calls appropriate tools (via MCP server) to perform the work.

        Args:
            task_request: Task request
            context: Full context including memory and plan

        Returns:
            Agent response containing execution results
        """
        self.logger.info("Executing build task", task_id=task_request.task_id)

        # Build system prompt for building
        system_prompt = """You are a Builder/Executor agent in a multi-agent system.
Your role is to write code, execute scripts, run tests, and manage files.

When given a task:
1. Analyze what needs to be built/executed
2. Determine the appropriate tools to use
3. Execute the work using tool calls
4. Verify the results

Available tools:
- write_code: Write code to a file
- execute_script: Execute a script
- run_tests: Run unit tests
- read_file: Read a file
- list_files: List files in a directory

Format your tool calls as JSON with:
- tool_name: name of the tool
- parameters: object with tool parameters

After execution, summarize what was done and any results.
"""

        # Build user prompt with task details
        user_prompt = f"""Task: {task_request.description}

Step Context:
{context.get('step', {})}

Previous Results:
{context.get('previous_results', {})}

Memory Context:
{context.get('memory', {})}

Execute this task step."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Call LLM
        llm_response = await self.call_llm(messages, temperature=0.3)

        # Execute tool calls if any
        tool_calls = llm_response.get("tool_calls", [])
        tool_results = []

        for tool_call in tool_calls:
            try:
                tool_name = tool_call.get("function", {}).get("name")
                parameters = tool_call.get("function", {}).get("arguments", {})

                if tool_name:
                    result = await self.call_tool(tool_name, parameters)
                    tool_results.append({"tool": tool_name, "result": result})
            except Exception as e:
                self.logger.error(
                    "Tool execution failed",
                    tool_call=tool_call,
                    error=str(e),
                )
                tool_results.append({"tool": tool_name, "error": str(e)})

        # Create response
        response = AgentResponse(
            agent_id=self.agent_id,
            status=AgentStatus.COMPLETED,
            content=llm_response["content"],
            tool_calls=tool_results,
            metadata={
                "task_id": task_request.task_id,
                "step_id": context.get("step", {}).get("step_id"),
                "tool_calls_count": len(tool_calls),
                "token_usage": llm_response.get("usage", {}),
            },
        )

        self.logger.info(
            "Build task completed",
            task_id=task_request.task_id,
            tool_calls_count=len(tool_calls),
        )

        return response

