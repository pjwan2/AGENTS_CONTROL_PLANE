"""Pydantic schemas for PromptVersion."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PromptVersionBase(BaseModel):
    """Base schema for prompt version."""

    prompt_key: str
    version: int
    content: str
    description: Optional[str] = None
    meta_data: Optional[str] = None
    is_active: int = 1


class PromptVersionCreate(PromptVersionBase):
    """Schema for creating a prompt version."""

    pass


class PromptVersionResponse(PromptVersionBase):
    """Schema for prompt version response."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
