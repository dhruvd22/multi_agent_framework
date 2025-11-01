"""
Agent management API routes.

This module provides endpoints for querying agent status and capabilities.
"""

from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...agents.agent_registry import AgentRegistry
from ...agents.schemas import AgentCapabilities, AgentState, AgentStatus
from ..main import app

router = APIRouter()


class AgentInfo(BaseModel):
    """Agent information model."""

    agent_id: str
    agent_type: str
    status: AgentStatus
    capabilities: AgentCapabilities
    current_task_id: str | None = None


@router.get("/", response_model=List[AgentInfo])
async def list_agents():
    """
    List all registered agents.

    Returns:
        List of agent information
    """
    registry: AgentRegistry = app.state.agent_registry
    agents = registry.get_all()

    # Get agent types
    agent_types = {}
    for agent_type, agent_ids in registry.agents_by_type.items():
        for agent_id in agent_ids:
            agent_types[agent_id] = agent_type

    return [
        AgentInfo(
            agent_id=agent.agent_id,
            agent_type=agent_types.get(agent.agent_id, "unknown"),
            status=agent.state.status,
            capabilities=agent.capabilities,
            current_task_id=agent.state.current_task_id,
        )
        for agent in agents
    ]


@router.get("/{agent_id}", response_model=AgentInfo)
async def get_agent(agent_id: str):
    """
    Get agent information.

    Args:
        agent_id: Agent identifier

    Returns:
        Agent information
    """
    registry: AgentRegistry = app.state.agent_registry
    agent = registry.get(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Get agent type
    agent_type = "unknown"
    for atype, agent_ids in registry.agents_by_type.items():
        if agent_id in agent_ids:
            agent_type = atype
            break

    return AgentInfo(
        agent_id=agent.agent_id,
        agent_type=agent_type,
        status=agent.state.status,
        capabilities=agent.capabilities,
        current_task_id=agent.state.current_task_id,
    )


@router.get("/{agent_id}/state", response_model=AgentState)
async def get_agent_state(agent_id: str):
    """
    Get current agent state.

    Args:
        agent_id: Agent identifier

    Returns:
        Agent state
    """
    registry: AgentRegistry = app.state.agent_registry
    agent = registry.get(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent.get_state()

