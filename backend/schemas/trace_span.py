"""Pydantic schemas for TraceSpan."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from backend.schemas.enums import SpanType


class TraceSpanBase(BaseModel):
    """Base schema for trace span."""

    agent_run_id: int
    parent_span_id: Optional[int] = None
    span_name: str
    span_type: SpanType
    status: str = "started"
    input_data: Optional[str] = None
    output_data: Optional[str] = None
    error_message: Optional[str] = None


class TraceSpanCreate(TraceSpanBase):
    """Schema for creating a trace span."""

    pass


class SpanCreateRequest(BaseModel):
    """Request body for POST /api/runs/{trace_id}/spans (agent_run_id comes from URL)."""

    parent_span_id: Optional[int] = None
    span_name: str
    span_type: SpanType
    status: str = "started"
    input_data: Optional[str] = None
    output_data: Optional[str] = None
    error_message: Optional[str] = None


class TraceSpanUpdate(BaseModel):
    """Schema for updating a trace span."""

    status: Optional[str] = None
    output_data: Optional[str] = None
    error_message: Optional[str] = None
    ended_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    token_count: Optional[int] = None


class TraceSpanResponse(TraceSpanBase):
    """Schema for trace span response."""

    id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    token_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
