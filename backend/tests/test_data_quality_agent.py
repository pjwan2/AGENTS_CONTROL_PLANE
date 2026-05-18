"""Tests for the DataQualityAgent and its API endpoint."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.agents.data_quality_agent import DataQualityAgent
from backend.repositories import agent_run as run_repo
from backend.repositories import trace_span as span_repo


# ---------------------------------------------------------------------------
# Unit tests — agent directly (no HTTP)
# ---------------------------------------------------------------------------


def test_agent_detects_all_issues(test_db_session: Session) -> None:
    """Agent finds all five intentional defects in payments.csv."""
    agent = DataQualityAgent(db=test_db_session)
    result = agent.run()

    findings = result["findings"]
    assert findings["duplicate_transaction_ids"] == ["TXN001"]
    assert findings["null_settlement_dates"] == ["TXN003"]
    assert findings["negative_amounts"] == ["TXN004"]
    assert findings["invalid_currencies"] == ["TXN005"]
    assert findings["future_payment_dates"] == ["TXN006"]


def test_spans_created_for_all_steps(test_db_session: Session) -> None:
    """Agent creates exactly 8 spans covering every check step."""
    agent = DataQualityAgent(db=test_db_session)
    result = agent.run()

    run = run_repo.get_by_trace_id(test_db_session, result["trace_id"])
    spans = span_repo.list_by_run(test_db_session, run.id)

    assert len(spans) == 8
    span_names = {s.span_name for s in spans}
    assert span_names == {
        "load_dataset",
        "inspect_schema",
        "check_duplicate_transaction_id",
        "check_null_settlement_date",
        "check_negative_amount",
        "check_invalid_currency",
        "check_future_payment_date",
        "summarize_findings",
    }
    assert all(s.status == "completed" for s in spans)


def test_invalid_dataset_path_creates_failed_span(test_db_session: Session) -> None:
    """A missing dataset path marks the load_dataset span and run as failed."""
    agent = DataQualityAgent(db=test_db_session)

    with pytest.raises(FileNotFoundError):
        agent.run(dataset_path="/nonexistent/payments.csv")

    runs = run_repo.list_runs(test_db_session)
    assert len(runs) == 1
    failed_run = runs[0]
    assert failed_run.status == "failed"

    spans = span_repo.list_by_run(test_db_session, failed_run.id)
    assert len(spans) == 1
    assert spans[0].span_name == "load_dataset"
    assert spans[0].status == "failed"


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------


def test_api_returns_trace_id_and_findings(test_client: TestClient) -> None:
    """POST /api/agents/data-quality/run returns trace_id and findings."""
    response = test_client.post(
        "/api/agents/data-quality/run",
        json={"user_query": "automated quality check"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "trace_id" in body
    assert len(body["trace_id"]) == 36  # UUID-4
    findings = body["findings"]
    assert "duplicate_transaction_ids" in findings
    assert "null_settlement_dates" in findings
    assert "negative_amounts" in findings
    assert "invalid_currencies" in findings
    assert "future_payment_dates" in findings
    assert findings["summary"]["total_issues"] > 0
