"""
Data models and schemas for agents.

This module defines Pydantic models for all agent-related data structures.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent execution status."""

    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"


class AgentCapabilities(BaseModel):
    """Agent capabilities configuration."""

    can_plan: bool = Field(default=False, description="Can create plans")
    can_execute: bool = Field(default=False, description="Can execute code")
    can_criticize: bool = Field(default=False, description="Can review and verify")
    can_write_code: bool = Field(default=False, description="Can write code")
    can_run_tests: bool = Field(default=False, description="Can run tests")
    can_execute_scripts: bool = Field(default=False, description="Can execute scripts")


class AgentState(BaseModel):
    """Current state of an agent."""

    agent_id: str = Field(..., description="Agent identifier")
    status: AgentStatus = Field(default=AgentStatus.IDLE, description="Current status")
    current_task_id: Optional[str] = Field(default=None, description="Current task ID")
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Agent context and memory"
    )
    last_activity: datetime = Field(
        default_factory=datetime.now, description="Last activity timestamp"
    )
    error: Optional[str] = Field(default=None, description="Last error message")


class AgentMessage(BaseModel):
    """Message sent to or from an agent."""

    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp")


class AgentResponse(BaseModel):
    """Response from an agent."""

    agent_id: str = Field(..., description="Agent identifier")
    status: AgentStatus = Field(..., description="Execution status")
    content: str = Field(..., description="Response content")
    tool_calls: List[Dict[str, Any]] = Field(
        default_factory=list, description="Tool calls made"
    )
    memory_writes: List[str] = Field(
        default_factory=list, description="Memory item IDs written"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    error: Optional[str] = Field(default=None, description="Error message if any")


class TaskRequest(BaseModel):
    """Request for an agent to perform a task."""

    task_id: str = Field(..., description="Task identifier")
    description: str = Field(..., description="Task description")
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Task context"
    )
    requirements: List[str] = Field(
        default_factory=list, description="Task requirements"
    )
    constraints: Dict[str, Any] = Field(
        default_factory=dict, description="Task constraints"
    )


class PlanStep(BaseModel):
    """A step in an execution plan."""

    step_id: str = Field(..., description="Step identifier")
    description: str = Field(..., description="Step description")
    agent_type: str = Field(..., description="Agent type to execute this step")
    dependencies: List[str] = Field(
        default_factory=list, description="Dependent step IDs"
    )
    status: AgentStatus = Field(
        default=AgentStatus.IDLE, description="Step execution status"
    )
    result: Optional[Dict[str, Any]] = Field(
        default=None, description="Step execution result"
    )


class ExecutionPlan(BaseModel):
    """An execution plan created by the Planner agent."""

    plan_id: str = Field(..., description="Plan identifier")
    task_id: str = Field(..., description="Associated task ID")
    steps: List[PlanStep] = Field(..., description="Plan steps")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation time")
    status: AgentStatus = Field(
        default=AgentStatus.IDLE, description="Plan execution status"
    )

