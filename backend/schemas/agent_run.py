"""Pydantic schemas for AgentRun."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentRunBase(BaseModel):
    """Base schema for agent run."""

    agent_id: str
    agent_name: str
    status: str = "pending"
    input_data: Optional[str] = None
    output_data: Optional[str] = None
    error_message: Optional[str] = None


class AgentRunCreate(AgentRunBase):
    """Schema for creating an agent run."""

    pass


class AgentRunUpdate(BaseModel):
    """Schema for updating an agent run."""

    status: Optional[str] = None
    output_data: Optional[str] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None


class AgentRunResponse(AgentRunBase):
    """Schema for agent run response."""

    id: int
    trace_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
