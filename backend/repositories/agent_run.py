"""Data-access functions for AgentRun."""
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.models.agent_run import AgentRun
from backend.schemas.agent_run import AgentRunCreate


def create(db: Session, data: AgentRunCreate) -> AgentRun:
    run = AgentRun(trace_id=str(uuid4()), **data.model_dump())
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_by_trace_id(db: Session, trace_id: str) -> AgentRun | None:
    return db.query(AgentRun).filter(AgentRun.trace_id == trace_id).first()


def list_runs(db: Session, skip: int = 0, limit: int = 100) -> list[AgentRun]:
    return (
        db.query(AgentRun)
        .order_by(AgentRun.started_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
