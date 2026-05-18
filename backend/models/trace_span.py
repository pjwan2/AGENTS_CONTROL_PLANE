"""SQLAlchemy ORM models for TraceSpan."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship, backref

from backend.models.base import Base


class TraceSpan(Base):
    """Trace span for agent execution observability."""

    __tablename__ = "trace_spans"

    id = Column(Integer, primary_key=True, index=True)
    agent_run_id = Column(Integer, ForeignKey("agent_runs.id"), nullable=False, index=True)
    parent_span_id = Column(Integer, ForeignKey("trace_spans.id"), nullable=True)
    span_name = Column(String(255), nullable=False)
    span_type = Column(String(50), nullable=False, index=True)  # see SpanType enum
    status = Column(String(50), nullable=False, index=True)  # started, completed, failed
    input_data = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    ended_at = Column(DateTime, nullable=True)
    duration_ms = Column(Float, nullable=True)
    token_count = Column(Integer, nullable=True)

    # Relationships
    agent_run = relationship("AgentRun", back_populates="trace_spans")
    # child_spans: one-to-many (parent → children). delete-orphan is valid on this side.
    # parent_span backref: many-to-one (child → parent) via remote_side=[id].
    child_spans = relationship(
        "TraceSpan",
        foreign_keys=[parent_span_id],
        backref=backref("parent_span", remote_side=[id]),
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<TraceSpan(id={self.id}, span_name={self.span_name}, status={self.status})>"
