"""Data-access functions for EvalResult."""
from sqlalchemy.orm import Session

from backend.models.eval_result import EvalResult
from backend.schemas.eval_result import EvalResultCreate


def create(db: Session, data: EvalResultCreate) -> EvalResult:
    row = EvalResult(**data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_by_run(db: Session, agent_run_id: int) -> list[EvalResult]:
    return (
        db.query(EvalResult)
        .filter(EvalResult.agent_run_id == agent_run_id)
        .order_by(EvalResult.created_at.asc())
        .all()
    )
