"""Tests for the Day 5 Evaluation Engine."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.agents.data_quality_agent import DataQualityAgent
from backend.app.evals.data_quality_evaluator import evaluate_data_quality_run
from backend.repositories import agent_run as run_repo
from backend.repositories import eval_result as eval_repo


# ---------------------------------------------------------------------------
# Unit tests — evaluator directly
# ---------------------------------------------------------------------------


def _run_agent(db: Session) -> tuple[str, int, dict]:
    """Helper: run DataQualityAgent and return (trace_id, run_id, findings)."""
    agent = DataQualityAgent(db=db)
    result = agent.run()
    run = run_repo.get_by_trace_id(db, result["trace_id"])
    return result["trace_id"], run.id, result["findings"]


def test_perfect_detection_gives_score_one(test_db_session: Session) -> None:
    """All five issue categories present in payments.csv → issue_detection_score = 1.0."""
    trace_id, run_id, findings = _run_agent(test_db_session)
    evals = evaluate_data_quality_run(test_db_session, run_id, findings)

    detection = next(e for e in evals if e.eval_name == "issue_detection_score")
    assert detection.score == 1.0


def test_groundedness_score_high_when_findings_match_spans(test_db_session: Session) -> None:
    """Findings produced by DataQualityAgent exactly match their span outputs → groundedness = 1.0."""
    trace_id, run_id, findings = _run_agent(test_db_session)
    evals = evaluate_data_quality_run(test_db_session, run_id, findings)

    groundedness = next(e for e in evals if e.eval_name == "groundedness_score")
    assert groundedness.score == 1.0


def test_hallucination_risk_zero_when_no_unsupported_findings(test_db_session: Session) -> None:
    """All reported issues are backed by span outputs → hallucination_risk_score = 0.0."""
    trace_id, run_id, findings = _run_agent(test_db_session)
    evals = evaluate_data_quality_run(test_db_session, run_id, findings)

    hallucination = next(e for e in evals if e.eval_name == "hallucination_risk_score")
    assert hallucination.score == 0.0


def test_eval_results_persisted_and_queryable_by_trace_id(test_db_session: Session) -> None:
    """Three EvalResult rows are written to the DB and retrievable via eval_repo."""
    trace_id, run_id, findings = _run_agent(test_db_session)
    evaluate_data_quality_run(test_db_session, run_id, findings)

    rows = eval_repo.list_by_run(test_db_session, run_id)
    assert len(rows) == 3
    eval_names = {r.eval_name for r in rows}
    assert eval_names == {
        "issue_detection_score",
        "groundedness_score",
        "hallucination_risk_score",
    }
    assert all(0.0 <= r.score <= 1.0 for r in rows)


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------


def test_api_response_includes_eval_summary(test_client: TestClient) -> None:
    """POST /api/agents/data-quality/run response contains eval_summary with all three scores."""
    response = test_client.post(
        "/api/agents/data-quality/run",
        json={"user_query": "eval engine test"},
    )
    assert response.status_code == 200
    body = response.json()

    # Enriched fields present
    assert "trace_id" in body
    assert "status" in body
    assert "issue_count" in body
    assert "findings" in body
    assert "duration_ms" in body

    # eval_summary has all three scores
    assert "eval_summary" in body
    summary = body["eval_summary"]
    assert set(summary.keys()) == {
        "issue_detection_score",
        "groundedness_score",
        "hallucination_risk_score",
    }
    assert all(0.0 <= v <= 1.0 for v in summary.values())
    assert summary["issue_detection_score"] == 1.0


def test_get_evals_endpoint_returns_persisted_rows(test_client: TestClient) -> None:
    """GET /api/runs/{trace_id}/evals returns the three EvalResult rows created by the agent run."""
    run_resp = test_client.post(
        "/api/agents/data-quality/run",
        json={"user_query": "evals endpoint test"},
    )
    assert run_resp.status_code == 200
    trace_id = run_resp.json()["trace_id"]

    evals_resp = test_client.get(f"/api/runs/{trace_id}/evals")
    assert evals_resp.status_code == 200
    rows = evals_resp.json()
    assert len(rows) == 3
    names = {r["eval_name"] for r in rows}
    assert names == {
        "issue_detection_score",
        "groundedness_score",
        "hallucination_risk_score",
    }
