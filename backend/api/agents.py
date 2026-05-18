"""Agent execution endpoints."""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.agents.data_quality_agent import DataQualityAgent
from backend.app.evals.data_quality_evaluator import evaluate_data_quality_run
from backend.db.database import get_db
from backend.repositories import agent_run as run_repo

router = APIRouter(prefix="/api/agents", tags=["agents"])


class DataQualityRunRequest(BaseModel):
    user_query: str = "Check data quality"
    dataset_path: Optional[str] = None


@router.post("/data-quality/run")
def run_data_quality(
    body: DataQualityRunRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        agent = DataQualityAgent(db=db)
        result = agent.run(user_query=body.user_query, dataset_path=body.dataset_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {exc}")

    trace_id: str = result["trace_id"]
    findings: dict[str, Any] = result["findings"]

    run = run_repo.get_by_trace_id(db, trace_id)
    evals = evaluate_data_quality_run(db, run.id, findings)

    issue_count = sum(
        len(v)
        for k, v in findings.items()
        if k not in ("schema", "summary") and isinstance(v, list)
    )

    return {
        "trace_id": trace_id,
        "status": run.status,
        "issue_count": issue_count,
        "findings": findings,
        "eval_summary": {e.eval_name: e.score for e in evals},
        "duration_ms": run.duration_ms,
    }
