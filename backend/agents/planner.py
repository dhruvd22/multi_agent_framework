"""
Planner agent implementation.

The Planner agent is responsible for creating execution plans by breaking down
tasks into actionable steps with dependencies.
"""

from typing import Any, Dict

from structlog import get_logger

from ..memory import MemoryRouter
from .base_agent import BaseAgent
from .schemas import AgentCapabilities, AgentResponse, AgentStatus, TaskRequest

logger = get_logger(__name__)


class PlannerAgent(BaseAgent):
    """
    Planner agent for creating execution plans.

    This agent analyzes tasks and breaks them down into steps with dependencies.
    It uses the LLM to understand requirements and create a structured plan.

    Capabilities:
        - can_plan: True
        - can_execute: False
        - can_criticize: False
    """

    def __init__(
        self,
        agent_id: str = "planner",
        memory_router: MemoryRouter | None = None,
    ):
        """
        Initialize Planner agent.

        Args:
            agent_id: Agent identifier (default: "planner")
            memory_router: Optional memory router instance
        """
        capabilities = AgentCapabilities(
            can_plan=True,
            can_execute=False,
            can_criticize=False,
        )
        super().__init__(agent_id, capabilities, memory_router)

    async def execute(
        self,
        task_request: TaskRequest,
        context: Dict[str, Any],
    ) -> AgentResponse:
        """
        Execute planning logic.

        This method uses the LLM to analyze the task and create a detailed
        execution plan with steps and dependencies.

        Args:
            task_request: Task request
            context: Full context including memory

        Returns:
            Agent response containing the execution plan
        """
        self.logger.info("Creating execution plan", task_id=task_request.task_id)

        # Build system prompt for planning
        system_prompt = """You are a Planner agent in a multi-agent system.
Your role is to analyze tasks and break them down into actionable steps.

Create a detailed execution plan with:
1. Steps that are clear and actionable
2. Dependencies between steps
3. Agent type assignments (builder, critic, etc.)
4. Estimated complexity

Format your response as a JSON object with:
- plan_id: unique identifier
- steps: array of step objects with:
  - step_id: unique step identifier
  - description: clear description of what needs to be done
  - agent_type: which agent should execute this (builder, critic, etc.)
  - dependencies: array of step_ids this step depends on
  - estimated_complexity: low/medium/high
"""

        # Build user prompt with task details
        user_prompt = f"""Task: {task_request.description}

Requirements:
{chr(10).join(f"- {req}" for req in task_request.requirements)}

Constraints:
{chr(10).join(f"- {k}: {v}" for k, v in task_request.constraints.items())}

Context:
{context.get('memory', {})}

Create an execution plan for this task."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Call LLM
        llm_response = await self.call_llm(messages, temperature=0.7)

        # Parse plan from response
        # TODO: Implement proper JSON parsing with validation
        plan_content = llm_response["content"]

        # Create response
        response = AgentResponse(
            agent_id=self.agent_id,
            status=AgentStatus.COMPLETED,
            content=plan_content,
            metadata={
                "plan_created": True,
                "task_id": task_request.task_id,
                "token_usage": llm_response.get("usage", {}),
            },
        )

        self.logger.info(
            "Execution plan created",
            task_id=task_request.task_id,
            response_length=len(plan_content),
        )

        return response

