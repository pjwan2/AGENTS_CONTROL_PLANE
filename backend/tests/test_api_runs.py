"""Tests for POST/GET /api/runs and /api/runs/{trace_id}/spans endpoints."""
import pytest
from fastapi.testclient import TestClient

from backend.schemas.enums import SpanType


# ---------------------------------------------------------------------------
# Agent run tests
# ---------------------------------------------------------------------------


def test_create_run_returns_201(test_client: TestClient) -> None:
    """POST /api/runs creates a new run and returns 201 with a trace_id."""
    response = test_client.post(
        "/api/runs",
        json={"agent_id": "agent_001", "agent_name": "PlannerAgent"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["agent_id"] == "agent_001"
    assert body["agent_name"] == "PlannerAgent"
    assert body["status"] == "pending"
    assert "trace_id" in body
    assert len(body["trace_id"]) == 36  # UUID-4 format


def test_create_run_persists_to_db(test_client: TestClient) -> None:
    """A run created via POST is retrievable via GET."""
    create = test_client.post(
        "/api/runs",
        json={"agent_id": "agent_002", "agent_name": "ExecutorAgent"},
    )
    assert create.status_code == 201
    trace_id = create.json()["trace_id"]

    get = test_client.get(f"/api/runs/{trace_id}")
    assert get.status_code == 200
    assert get.json()["trace_id"] == trace_id
    assert get.json()["agent_id"] == "agent_002"


def test_list_runs_empty(test_client: TestClient) -> None:
    """GET /api/runs returns an empty list when no runs exist."""
    response = test_client.get("/api/runs")
    assert response.status_code == 200
    assert response.json() == []


def test_list_runs_returns_all_created(test_client: TestClient) -> None:
    """GET /api/runs returns every run that was created."""
    test_client.post("/api/runs", json={"agent_id": "a1", "agent_name": "A"})
    test_client.post("/api/runs", json={"agent_id": "a2", "agent_name": "B"})
    test_client.post("/api/runs", json={"agent_id": "a3", "agent_name": "C"})

    response = test_client.get("/api/runs")
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_get_run_not_found(test_client: TestClient) -> None:
    """GET /api/runs/{trace_id} returns 404 for an unknown trace_id."""
    response = test_client.get("/api/runs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["detail"] == "Agent run not found"


# ---------------------------------------------------------------------------
# Trace span tests
# ---------------------------------------------------------------------------


def _make_run(client: TestClient, agent_id: str = "agent_x") -> dict:
    resp = client.post("/api/runs", json={"agent_id": agent_id, "agent_name": "X"})
    assert resp.status_code == 201
    return resp.json()


def test_create_span_returns_201(test_client: TestClient) -> None:
    """POST /api/runs/{trace_id}/spans creates a span and returns 201."""
    run = _make_run(test_client)
    trace_id = run["trace_id"]

    response = test_client.post(
        f"/api/runs/{trace_id}/spans",
        json={"span_name": "llm_call", "span_type": SpanType.LLM_CALL, "status": "started"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["span_name"] == "llm_call"
    assert body["span_type"] == SpanType.LLM_CALL
    assert body["status"] == "started"
    assert body["agent_run_id"] == run["id"]


def test_create_span_rejects_unknown_type(test_client: TestClient) -> None:
    """POST /api/runs/{trace_id}/spans returns 422 for an unrecognised span_type."""
    run = _make_run(test_client)
    response = test_client.post(
        f"/api/runs/{run['trace_id']}/spans",
        json={"span_name": "x", "span_type": "llm", "status": "started"},
    )
    assert response.status_code == 422


def test_create_span_run_not_found(test_client: TestClient) -> None:
    """POST /api/runs/{trace_id}/spans returns 404 when the run doesn't exist."""
    response = test_client.post(
        "/api/runs/no-such-trace/spans",
        json={"span_name": "x", "span_type": SpanType.TOOL_CALL, "status": "started"},
    )
    assert response.status_code == 404


def test_list_spans_returns_all_for_run(test_client: TestClient) -> None:
    """GET /api/runs/{trace_id}/spans returns every span attached to that run."""
    run = _make_run(test_client)
    trace_id = run["trace_id"]

    test_client.post(
        f"/api/runs/{trace_id}/spans",
        json={"span_name": "tool_call", "span_type": SpanType.TOOL_CALL, "status": "started"},
    )
    test_client.post(
        f"/api/runs/{trace_id}/spans",
        json={"span_name": "llm_call", "span_type": SpanType.LLM_CALL, "status": "completed"},
    )

    response = test_client.get(f"/api/runs/{trace_id}/spans")
    assert response.status_code == 200
    spans = response.json()
    assert len(spans) == 2
    assert {s["span_name"] for s in spans} == {"tool_call", "llm_call"}


def test_list_spans_isolated_between_runs(test_client: TestClient) -> None:
    """Spans created for one run do not appear when listing another run's spans."""
    run_a = _make_run(test_client, "agent_a")
    run_b = _make_run(test_client, "agent_b")

    test_client.post(
        f"/api/runs/{run_a['trace_id']}/spans",
        json={"span_name": "span_a", "span_type": SpanType.TOOL_CALL, "status": "started"},
    )

    response = test_client.get(f"/api/runs/{run_b['trace_id']}/spans")
    assert response.status_code == 200
    assert response.json() == []


def test_list_spans_run_not_found(test_client: TestClient) -> None:
    """GET /api/runs/{trace_id}/spans returns 404 when the run doesn't exist."""
    response = test_client.get("/api/runs/no-such-trace/spans")
    assert response.status_code == 404
