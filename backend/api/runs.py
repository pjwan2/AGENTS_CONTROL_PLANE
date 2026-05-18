"""REST endpoints for agent runs, their trace spans, and eval results."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.repositories import agent_run as run_repo
from backend.repositories import eval_result as eval_repo
from backend.repositories import trace_span as span_repo
from backend.schemas.agent_run import AgentRunCreate, AgentRunResponse
from backend.schemas.eval_result import EvalResultResponse
from backend.schemas.trace_span import SpanCreateRequest, TraceSpanResponse

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.post("", response_model=AgentRunResponse, status_code=201)
def create_run(data: AgentRunCreate, db: Session = Depends(get_db)) -> AgentRunResponse:
    return run_repo.create(db, data)


@router.get("", response_model=list[AgentRunResponse])
def list_runs(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> list[AgentRunResponse]:
    return run_repo.list_runs(db, skip=skip, limit=limit)


@router.get("/{trace_id}", response_model=AgentRunResponse)
def get_run(trace_id: str, db: Session = Depends(get_db)) -> AgentRunResponse:
    run = run_repo.get_by_trace_id(db, trace_id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return run


@router.post("/{trace_id}/spans", response_model=TraceSpanResponse, status_code=201)
def create_span(
    trace_id: str, data: SpanCreateRequest, db: Session = Depends(get_db)
) -> TraceSpanResponse:
    run = run_repo.get_by_trace_id(db, trace_id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return span_repo.create(db, run.id, data)


@router.get("/{trace_id}/spans", response_model=list[TraceSpanResponse])
def list_spans(trace_id: str, db: Session = Depends(get_db)) -> list[TraceSpanResponse]:
    run = run_repo.get_by_trace_id(db, trace_id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return span_repo.list_by_run(db, run.id)


@router.get("/{trace_id}/evals", response_model=list[EvalResultResponse])
def list_evals(trace_id: str, db: Session = Depends(get_db)) -> list[EvalResultResponse]:
    run = run_repo.get_by_trace_id(db, trace_id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return eval_repo.list_by_run(db, run.id)
