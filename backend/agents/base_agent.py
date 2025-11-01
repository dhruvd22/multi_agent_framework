"""
Base agent class with common functionality.

This module provides the BaseAgent class that all specific agents inherit from.
It includes LLM integration, tool calling, memory access, and common agent behaviors.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI
from structlog import get_logger

from ..config import get_settings
from ..core import get_budget_tracker
from ..core.logger import get_logger as get_logger_func
from ..core.exceptions import AgentError
from ..memory import MemoryRouter
from .schemas import (
    AgentCapabilities,
    AgentMessage,
    AgentResponse,
    AgentState,
    AgentStatus,
    TaskRequest,
)

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents in the framework.

    This class provides common functionality including:
    - OpenAI LLM integration
    - Tool calling via MCP server
    - Memory access via memory router
    - State management
    - Budget tracking
    - Logging

    Subclasses should implement the `execute` method to define agent-specific behavior.

    Attributes:
        agent_id: Unique agent identifier
        capabilities: Agent capabilities configuration
        state: Current agent state
        memory_router: Memory router for storing/retrieving context
        llm_client: OpenAI async client
        budget_tracker: Budget tracking instance
    """

    def __init__(
        self,
        agent_id: str,
        capabilities: AgentCapabilities,
        memory_router: Optional[MemoryRouter] = None,
    ):
        """
        Initialize base agent.

        Args:
            agent_id: Unique agent identifier
            capabilities: Agent capabilities
            memory_router: Optional memory router instance
        """
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.state = AgentState(
            agent_id=agent_id,
            status=AgentStatus.IDLE,
        )
        self.memory_router = memory_router
        self.settings = get_settings()

        # Initialize OpenAI client
        self.llm_client = AsyncOpenAI(api_key=self.settings.openai.api_key)

        # Initialize budget tracker
        self.budget_tracker = get_budget_tracker()

        # Logger bound to this agent
        self.logger = get_logger_func(self.__class__.__name__).bind(agent_id=agent_id)

    async def process(
        self,
        task_request: TaskRequest,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        """
        Process a task request.

        This is the main entry point for agent execution. It handles:
        1. State management
        2. Context retrieval from memory
        3. LLM interaction
        4. Tool execution
        5. Memory storage
        6. Error handling

        Args:
            task_request: Task request to process
            context: Optional additional context

        Returns:
            Agent response

        Raises:
            AgentError: If agent execution fails
        """
        try:
            self.state.status = AgentStatus.THINKING
            self.state.current_task_id = task_request.task_id

            # Get context from memory
            memory_context = await self._get_memory_context(task_request.task_id)

            # Combine contexts
            full_context = {
                **(context or {}),
                "memory": memory_context,
                "task": task_request.dict(),
            }

            # Execute agent-specific logic
            self.state.status = AgentStatus.EXECUTING
            response = await self.execute(task_request, full_context)

            # Store response in memory
            if self.memory_router:
                await self._store_response(task_request.task_id, response)

            self.state.status = AgentStatus.COMPLETED
            self.state.last_activity = response.metadata.get("timestamp")

            return response

        except Exception as e:
            self.state.status = AgentStatus.ERROR
            self.state.error = str(e)
            self.logger.error(
                "Agent execution failed",
                task_id=task_request.task_id,
                error=str(e),
                exc_info=True,
            )
            raise AgentError(
                f"Agent {self.agent_id} failed: {str(e)}",
                context={"task_id": task_request.task_id, "agent_id": self.agent_id},
            ) from e

    @abstractmethod
    async def execute(
        self,
        task_request: TaskRequest,
        context: Dict[str, Any],
    ) -> AgentResponse:
        """
        Execute agent-specific logic.

        This method must be implemented by subclasses to define the agent's behavior.

        Args:
            task_request: Task request
            context: Full context including memory

        Returns:
            Agent response

        Raises:
            AgentError: If execution fails
        """
        pass

    async def call_llm(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Call OpenAI LLM with automatic token tracking.

        Args:
            messages: List of message dictionaries
            model: Model name (defaults to configured model)
            temperature: Temperature setting (defaults to configured value)
            max_tokens: Max tokens (defaults to configured value)
            tools: Optional list of tool definitions

        Returns:
            LLM response dictionary

        Raises:
            AgentError: If LLM call fails
        """
        model = model or self.settings.openai.model
        temperature = temperature or self.settings.openai.temperature
        max_tokens = max_tokens or self.settings.openai.max_tokens

        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            if tools:
                kwargs["tools"] = tools

            response = await self.llm_client.chat.completions.create(**kwargs)

            # Track token usage
            usage = response.usage
            if usage:
                await self.budget_tracker.record_usage(
                    model=model,
                    input_tokens=usage.prompt_tokens or 0,
                    output_tokens=usage.completion_tokens or 0,
                    task_id=self.state.current_task_id,
                )

            return {
                "content": response.choices[0].message.content,
                "tool_calls": response.choices[0].message.tool_calls or [],
                "usage": {
                    "prompt_tokens": usage.prompt_tokens if usage else 0,
                    "completion_tokens": usage.completion_tokens if usage else 0,
                    "total_tokens": usage.total_tokens if usage else 0,
                },
            }

        except Exception as e:
            self.logger.error(
                "LLM call failed",
                model=model,
                error=str(e),
                exc_info=True,
            )
            raise AgentError(f"LLM call failed: {str(e)}") from e

    async def call_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Call an MCP tool.

        Args:
            tool_name: Name of the tool to call
            parameters: Tool parameters

        Returns:
            Tool execution result

        Raises:
            AgentError: If tool call fails
        """
        try:
            from ..mcp import get_mcp_server

            server = get_mcp_server()
            result = await server.call_tool(tool_name, parameters)

            if not result.get("success"):
                raise AgentError(
                    f"Tool '{tool_name}' execution failed: {result.get('error')}",
                    context={"tool_name": tool_name, "parameters": parameters},
                )

            return result

        except Exception as e:
            self.logger.error(
                "Tool call failed",
                tool_name=tool_name,
                error=str(e),
                exc_info=True,
            )
            raise AgentError(f"Tool call failed: {str(e)}") from e

    async def _get_memory_context(self, task_id: str) -> Dict[str, Any]:
        """
        Get relevant context from memory.

        Args:
            task_id: Task identifier

        Returns:
            Memory context dictionary
        """
        if not self.memory_router:
            return {}

        try:
            from ..memory.schemas import MemoryQuery, MemoryType

            query = MemoryQuery(
                task_id=task_id,
                agent_id=self.agent_id,
                limit=50,
            )

            search_result = await self.memory_router.search_items(query)

            # Get graph relationships if available
            context = {
                "items": [item.dict() for item in search_result.items],
                "relationships": [],
            }

            # Try to get relationships for this agent's items
            for item in search_result.items[:10]:  # Limit to first 10 items
                if item.type in ["task", "code_file", "agent_state"]:
                    node_type = item.type.replace("_", "").title()
                    rels = await self.memory_router.get_relationships(
                        item.id, node_type, direction="both"
                    )
                    context["relationships"].extend(rels)

            return context

        except Exception as e:
            self.logger.warning(
                "Failed to retrieve memory context",
                task_id=task_id,
                error=str(e),
            )
            return {}

    async def _store_response(
        self,
        task_id: str,
        response: AgentResponse,
    ) -> None:
        """
        Store agent response in memory.

        Args:
            task_id: Task identifier
            response: Agent response
        """
        if not self.memory_router:
            return

        try:
            from ..memory.schemas import MemoryItem, MemoryType

            item = MemoryItem(
                type=MemoryType.AGENT_STATE,
                content={
                    "response": response.content,
                    "status": response.status.value,
                    "tool_calls": response.tool_calls,
                },
                agent_id=self.agent_id,
                task_id=task_id,
                metadata={
                    "memory_writes": response.memory_writes,
                    **response.metadata,
                },
            )

            await self.memory_router.write_item(item)

        except Exception as e:
            self.logger.warning(
                "Failed to store response in memory",
                task_id=task_id,
                error=str(e),
            )

    def get_state(self) -> AgentState:
        """
        Get current agent state.

        Returns:
            Current agent state
        """
        return self.state

    def reset(self) -> None:
        """Reset agent state to idle."""
        self.state.status = AgentStatus.IDLE
        self.state.current_task_id = None
        self.state.error = None
        self.state.context = {}

