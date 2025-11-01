"""
Agent registry for dynamic agent discovery and registration.

This module provides a registry pattern for managing agents, allowing
dynamic registration and retrieval of agent instances.
"""

from typing import Dict, Optional

from structlog import get_logger

from ..core.exceptions import AgentError
from .base_agent import BaseAgent

logger = get_logger(__name__)


class AgentRegistry:
    """
    Registry for managing agent instances.

    This class provides a centralized registry for all agents in the system.
    It allows for dynamic registration and retrieval of agents by type and ID.

    Attributes:
        agents: Dictionary mapping agent IDs to agent instances
        agents_by_type: Dictionary mapping agent types to lists of agent IDs
    """

    def __init__(self):
        """Initialize agent registry."""
        self.agents: Dict[str, BaseAgent] = {}
        self.agents_by_type: Dict[str, list[str]] = {}

    def register(self, agent: BaseAgent, agent_type: str) -> None:
        """
        Register an agent in the registry.

        Args:
            agent: Agent instance to register
            agent_type: Type of agent (e.g., "planner", "builder", "critic")

        Raises:
            AgentError: If agent ID already exists
        """
        if agent.agent_id in self.agents:
            raise AgentError(
                f"Agent with ID {agent.agent_id} already registered",
                context={"agent_id": agent.agent_id, "agent_type": agent_type},
            )

        self.agents[agent.agent_id] = agent

        if agent_type not in self.agents_by_type:
            self.agents_by_type[agent_type] = []

        self.agents_by_type[agent_type].append(agent.agent_id)

        logger.info(
            "Agent registered",
            agent_id=agent.agent_id,
            agent_type=agent_type,
        )

    def get(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get an agent by ID.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent instance if found, None otherwise
        """
        return self.agents.get(agent_id)

    def get_by_type(self, agent_type: str) -> list[BaseAgent]:
        """
        Get all agents of a specific type.

        Args:
            agent_type: Agent type

        Returns:
            List of agent instances
        """
        agent_ids = self.agents_by_type.get(agent_type, [])
        return [self.agents[aid] for aid in agent_ids if aid in self.agents]

    def get_all(self) -> list[BaseAgent]:
        """
        Get all registered agents.

        Returns:
            List of all agent instances
        """
        return list(self.agents.values())

    def unregister(self, agent_id: str) -> bool:
        """
        Unregister an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            True if agent was unregistered, False if not found
        """
        if agent_id not in self.agents:
            return False

        agent = self.agents[agent_id]

        # Remove from type mapping
        for agent_type, agent_ids in self.agents_by_type.items():
            if agent_id in agent_ids:
                agent_ids.remove(agent_id)

        del self.agents[agent_id]

        logger.info("Agent unregistered", agent_id=agent_id)

        return True

    def clear(self) -> None:
        """Clear all registered agents."""
        self.agents.clear()
        self.agents_by_type.clear()
        logger.info("Agent registry cleared")


# Global agent registry instance
_agent_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """
    Get the global agent registry instance.

    Returns:
        AgentRegistry: Singleton agent registry instance

    Note:
        This function creates a new registry if one doesn't exist.
    """
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry

