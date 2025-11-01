"""
Critic/Verifier agent implementation.

The Critic agent is responsible for reviewing code, verifying specifications,
checking unit tests, validating style, and ensuring safety constraints.
"""

from typing import Any, Dict

from structlog import get_logger

from ..memory import MemoryRouter
from .base_agent import BaseAgent
from .schemas import AgentCapabilities, AgentResponse, AgentStatus, TaskRequest

logger = get_logger(__name__)


class CriticAgent(BaseAgent):
    """
    Critic/Verifier agent for code review and verification.

    This agent handles:
    - Code review and quality checks
    - Specification verification
    - Test validation
    - Style checking
    - Safety constraint validation

    Capabilities:
        - can_criticize: True
        - can_run_tests: True
    """

    def __init__(
        self,
        agent_id: str = "critic",
        memory_router: MemoryRouter | None = None,
    ):
        """
        Initialize Critic agent.

        Args:
            agent_id: Agent identifier (default: "critic")
            memory_router: Optional memory router instance
        """
        capabilities = AgentCapabilities(
            can_criticize=True,
            can_run_tests=True,
        )
        super().__init__(agent_id, capabilities, memory_router)

    async def execute(
        self,
        task_request: TaskRequest,
        context: Dict[str, Any],
    ) -> AgentResponse:
        """
        Execute critic/verification logic.

        This method reviews the work done, verifies it meets requirements,
        checks tests, and validates constraints.

        Args:
            task_request: Task request
            context: Full context including execution results

        Returns:
            Agent response containing verification results
        """
        self.logger.info("Executing verification", task_id=task_request.task_id)

        # Build system prompt for criticism
        system_prompt = """You are a Critic/Verifier agent in a multi-agent system.
Your role is to review and verify that work meets specifications, quality standards,
and safety constraints.

When reviewing:
1. Check if specifications are met
2. Verify code quality and style
3. Validate test coverage and results
4. Check safety constraints
5. Identify any issues or improvements needed

Provide a detailed review with:
- Overall assessment (pass/fail/needs_work)
- Specification compliance check
- Code quality assessment
- Test validation results
- Safety constraint verification
- Issues found (if any)
- Recommendations for improvement

Format your response as structured feedback.
"""

        # Build user prompt with execution results
        original_task = context.get("original_task", {})
        execution_results = context.get("execution_results", {})

        user_prompt = f"""Review the following task execution:

Original Task:
{original_task.get('description', 'N/A')}

Requirements:
{chr(10).join(f"- {req}" for req in original_task.get('requirements', []))}

Constraints:
{chr(10).join(f"- {k}: {v}" for k, v in original_task.get('constraints', {}).items())}

Execution Results:
{execution_results}

Verify that:
1. All requirements are met
2. Code quality is acceptable
3. Tests pass (if applicable)
4. Safety constraints are satisfied
5. Overall quality is production-ready

Provide your detailed review."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Call LLM
        llm_response = await self.call_llm(messages, temperature=0.5)

        # Check if we should run tests
        # TODO: Parse LLM response to determine if tests should be run
        # For now, assume we run tests if execution results contain code
        test_results = []
        if execution_results:
            # Try to run tests if applicable
            # This would be done via MCP tools
            pass

        # Create response
        response = AgentResponse(
            agent_id=self.agent_id,
            status=AgentStatus.COMPLETED,
            content=llm_response["content"],
            tool_calls=test_results,
            metadata={
                "task_id": task_request.task_id,
                "verification_type": "full_review",
                "token_usage": llm_response.get("usage", {}),
            },
        )

        self.logger.info(
            "Verification completed",
            task_id=task_request.task_id,
        )

        return response

