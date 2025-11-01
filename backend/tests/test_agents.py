"""
Basic test for agent functionality.
"""

import pytest
from backend.agents.agent_registry import AgentRegistry
from backend.agents.planner import PlannerAgent


@pytest.mark.asyncio
async def test_planner_agent():
    """Test planner agent creation."""
    agent = PlannerAgent(agent_id="test_planner")
    assert agent.agent_id == "test_planner"
    assert agent.capabilities.can_plan is True


@pytest.mark.asyncio
async def test_agent_registry():
    """Test agent registry."""
    registry = AgentRegistry()
    agent = PlannerAgent(agent_id="test_planner")
    registry.register(agent, "planner")
    
    retrieved = registry.get("test_planner")
    assert retrieved is not None
    assert retrieved.agent_id == "test_planner"

