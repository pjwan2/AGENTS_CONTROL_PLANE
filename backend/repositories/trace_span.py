"""Data-access functions for TraceSpan."""
from sqlalchemy.orm import Session

from backend.models.trace_span import TraceSpan
from backend.schemas.trace_span import SpanCreateRequest


def create(db: Session, agent_run_id: int, data: SpanCreateRequest) -> TraceSpan:
    span = TraceSpan(agent_run_id=agent_run_id, **data.model_dump())
    db.add(span)
    db.commit()
    db.refresh(span)
    return span


def list_by_run(db: Session, agent_run_id: int) -> list[TraceSpan]:
    return (
        db.query(TraceSpan)
        .filter(TraceSpan.agent_run_id == agent_run_id)
        .order_by(TraceSpan.started_at.asc())
        .all()
    )
