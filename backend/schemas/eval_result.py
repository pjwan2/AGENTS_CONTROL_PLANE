"""Pydantic schemas for EvalResult."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EvalResultBase(BaseModel):
    """Base schema for eval result."""

    agent_run_id: int
    eval_name: str
    eval_type: str
    score: float = Field(..., ge=0.0, le=1.0)
    meta_data: Optional[str] = None


class EvalResultCreate(EvalResultBase):
    """Schema for creating an eval result."""

    pass


class EvalResultResponse(EvalResultBase):
    """Schema for eval result response."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
