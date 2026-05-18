"""SQLAlchemy ORM models for PromptVersion."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text

from backend.models.base import Base


class PromptVersion(Base):
    """Versioned prompt templates for reproducibility."""

    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, index=True)
    prompt_key = Column(String(255), nullable=False, index=True)  # e.g., "agent_planning", "tool_selection"
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    meta_data = Column(Text, nullable=True)  # JSON with model, temperature, etc.
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    is_active = Column(Integer, default=1, nullable=False)

    def __repr__(self) -> str:
        """String representation."""
        return f"<PromptVersion(id={self.id}, prompt_key={self.prompt_key}, version={self.version})>"
