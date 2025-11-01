"""
Agent executor for orchestrating multi-agent workflows.

This module provides the AgentExecutor class that coordinates agent execution,
manages agent communication, and orchestrates task completion across multiple agents.
"""

from typing import Any, Dict, List, Optional

from structlog import get_logger

from ..core.exceptions import AgentError, TaskError
from ..memory import MemoryRouter
from .agent_registry import AgentRegistry
from .schemas import AgentResponse, AgentStatus, ExecutionPlan, PlanStep, TaskRequest

logger = get_logger(__name__)


class AgentExecutor:
    """
    Orchestrates multi-agent task execution.

    This class coordinates the execution of tasks across multiple agents,
    managing the workflow, dependencies, and communication between agents.

    Attributes:
        registry: Agent registry instance
        memory_router: Memory router for agent communication
    """

    def __init__(
        self,
        registry: AgentRegistry,
        memory_router: Optional[MemoryRouter] = None,
    ):
        """
        Initialize agent executor.

        Args:
            registry: Agent registry instance
            memory_router: Optional memory router for agent communication
        """
        self.registry = registry
        self.memory_router = memory_router

    async def execute_task(
        self,
        task_request: TaskRequest,
        plan: Optional[ExecutionPlan] = None,
    ) -> Dict[str, Any]:
        """
        Execute a task using multiple agents.

        This method orchestrates the execution of a task by:
        1. Using the plan if provided, or creating one via Planner agent
        2. Executing plan steps in dependency order
        3. Managing agent communication via memory
        4. Collecting and returning results

        Args:
            task_request: Task request
            plan: Optional execution plan (if None, Planner agent will create one)

        Returns:
            Dictionary containing execution results

        Raises:
            TaskError: If task execution fails
        """
        try:
            logger.info("Starting task execution", task_id=task_request.task_id)

            # Step 1: Create plan if not provided
            if not plan:
                plan = await self._create_plan(task_request)

            # Step 2: Execute plan steps
            results = await self._execute_plan(plan, task_request)

            # Step 3: Verify completion (if Critic agent available)
            verification = await self._verify_completion(task_request, results)

            return {
                "task_id": task_request.task_id,
                "plan": plan.dict(),
                "results": results,
                "verification": verification,
                "status": "completed",
            }

        except Exception as e:
            logger.error(
                "Task execution failed",
                task_id=task_request.task_id,
                error=str(e),
                exc_info=True,
            )
            raise TaskError(
                f"Task execution failed: {str(e)}",
                context={"task_id": task_request.task_id},
            ) from e

    async def _create_plan(self, task_request: TaskRequest) -> ExecutionPlan:
        """
        Create an execution plan using the Planner agent.

        Args:
            task_request: Task request

        Returns:
            Execution plan

        Raises:
            AgentError: If Planner agent not found or planning fails
        """
        planners = self.registry.get_by_type("planner")
        if not planners:
            raise AgentError(
                "No Planner agent found in registry",
                context={"task_id": task_request.task_id},
            )

        planner = planners[0]
        logger.info("Creating execution plan", task_id=task_request.task_id)

        response = await planner.process(task_request)

        # Parse plan from response
        # TODO: Implement plan parsing from LLM response
        # For now, create a simple plan structure
        plan = ExecutionPlan(
            plan_id=f"plan_{task_request.task_id}",
            task_id=task_request.task_id,
            steps=[
                PlanStep(
                    step_id=f"step_{i}",
                    description=f"Step {i}",
                    agent_type="builder",
                    dependencies=[],
                )
                for i in range(1, 4)
            ],
        )

        return plan

    async def _execute_plan(
        self,
        plan: ExecutionPlan,
        task_request: TaskRequest,
    ) -> Dict[str, Any]:
        """
        Execute plan steps in dependency order.

        Args:
            plan: Execution plan
            task_request: Original task request

        Returns:
            Dictionary mapping step IDs to results
        """
        results: Dict[str, Any] = {}
        completed_steps: set[str] = set()

        # Sort steps by dependencies
        sorted_steps = self._topological_sort(plan.steps)

        for step in sorted_steps:
            # Check dependencies
            if not all(dep in completed_steps for dep in step.dependencies):
                logger.warning(
                    "Step dependencies not met",
                    step_id=step.step_id,
                    dependencies=step.dependencies,
                )
                continue

            # Get agent for this step
            agents = self.registry.get_by_type(step.agent_type)
            if not agents:
                logger.error(
                    "Agent type not found",
                    step_id=step.step_id,
                    agent_type=step.agent_type,
                )
                step.status = AgentStatus.ERROR
                continue

            agent = agents[0]

            # Create task request for this step
            step_request = TaskRequest(
                task_id=f"{task_request.task_id}_{step.step_id}",
                description=step.description,
                context={
                    **task_request.context,
                    "plan": plan.dict(),
                    "step": step.dict(),
                    "previous_results": results,
                },
            )

            # Execute step
            try:
                step.status = AgentStatus.EXECUTING
                response = await agent.process(step_request, context=step_request.context)
                step.status = AgentStatus.COMPLETED
                step.result = response.dict()
                results[step.step_id] = response.dict()
                completed_steps.add(step.step_id)

            except Exception as e:
                logger.error(
                    "Step execution failed",
                    step_id=step.step_id,
                    error=str(e),
                )
                step.status = AgentStatus.ERROR
                step.result = {"error": str(e)}
                results[step.step_id] = {"error": str(e)}

        return results

    async def _verify_completion(
        self,
        task_request: TaskRequest,
        results: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Verify task completion using Critic agent.

        Args:
            task_request: Original task request
            results: Execution results

        Returns:
            Verification result if Critic agent available, None otherwise
        """
        critics = self.registry.get_by_type("critic")
        if not critics:
            logger.info("No Critic agent available for verification")
            return None

        critic = critics[0]

        verification_request = TaskRequest(
            task_id=f"{task_request.task_id}_verification",
            description=f"Verify completion of task: {task_request.description}",
            context={
                "original_task": task_request.dict(),
                "execution_results": results,
            },
        )

        try:
            response = await critic.process(verification_request)
            return response.dict()
        except Exception as e:
            logger.warning(
                "Verification failed",
                task_id=task_request.task_id,
                error=str(e),
            )
            return {"error": str(e)}

    def _topological_sort(self, steps: List[PlanStep]) -> List[PlanStep]:
        """
        Sort steps by dependencies using topological sort.

        Args:
            steps: List of plan steps

        Returns:
            Sorted list of steps
        """
        # Build dependency graph
        step_map = {step.step_id: step for step in steps}
        in_degree = {step.step_id: len(step.dependencies) for step in steps}

        # Find steps with no dependencies
        queue = [step for step in steps if in_degree[step.step_id] == 0]
        result = []

        while queue:
            step = queue.pop(0)
            result.append(step)

            # Update in-degrees
            for other_step in steps:
                if step.step_id in other_step.dependencies:
                    in_degree[other_step.step_id] -= 1
                    if in_degree[other_step.step_id] == 0:
                        queue.append(other_step)

        # Handle cycles (steps not in result)
        remaining = [step for step in steps if step not in result]
        result.extend(remaining)

        return result

