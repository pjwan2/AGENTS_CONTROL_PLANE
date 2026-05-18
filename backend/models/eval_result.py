"""SQLAlchemy ORM models for EvalResult."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.models.base import Base


class EvalResult(Base):
    """Evaluation result for agent run."""

    __tablename__ = "eval_results"

    id = Column(Integer, primary_key=True, index=True)
    agent_run_id = Column(Integer, ForeignKey("agent_runs.id"), nullable=False, index=True)
    eval_name = Column(String(255), nullable=False)
    eval_type = Column(String(50), nullable=False)  # correctness, efficiency, safety, etc.
    score = Column(Float, nullable=False)  # 0.0 to 1.0
    meta_data = Column(Text, nullable=True)  # JSON or additional evaluation details
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    agent_run = relationship("AgentRun", back_populates="eval_results")

    def __repr__(self) -> str:
        """String representation."""
        return f"<EvalResult(id={self.id}, eval_name={self.eval_name}, score={self.score})>"
