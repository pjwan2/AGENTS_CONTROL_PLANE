"""SQLAlchemy ORM models for AgentRun."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.models.base import Base


class AgentRun(Base):
    """Agent run execution record."""

    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String(36), unique=True, nullable=False, index=True)
    agent_id = Column(String(255), nullable=False, index=True)
    agent_name = Column(String(255), nullable=False)
    status = Column(String(50), default="pending", nullable=False, index=True)
    input_data = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True, index=True)
    duration_ms = Column(Integer, nullable=True)

    # Relationships
    trace_spans = relationship("TraceSpan", back_populates="agent_run", cascade="all, delete-orphan")
    eval_results = relationship("EvalResult", back_populates="agent_run", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation."""
        return f"<AgentRun(id={self.id}, agent_id={self.agent_id}, status={self.status})>"
