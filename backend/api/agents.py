"""Agent execution endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.agents.data_quality_agent import DataQualityAgent
from backend.db.database import get_db

router = APIRouter(prefix="/api/agents", tags=["agents"])


class DataQualityRunRequest(BaseModel):
    user_query: str = "Check data quality"
    dataset_path: Optional[str] = None


@router.post("/data-quality/run")
def run_data_quality(
    body: DataQualityRunRequest,
    db: Session = Depends(get_db),
) -> dict:
    try:
        agent = DataQualityAgent(db=db)
        return agent.run(user_query=body.user_query, dataset_path=body.dataset_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {exc}")
