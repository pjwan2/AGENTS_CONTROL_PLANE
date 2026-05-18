"""Tests for the AgentTracer SDK.

Tests use the existing test_db_session fixture (SQLite in-memory) directly —
the tracer is a pure Python library that does not go through HTTP.
"""
import json

import pytest
from sqlalchemy.orm import Session

from backend.app.tracing.tracer import AgentTracer
from backend.repositories import agent_run as run_repo
from backend.repositories import trace_span as span_repo
from backend.schemas.enums import SpanType


# ---------------------------------------------------------------------------
# AgentRun tests
# ---------------------------------------------------------------------------


def test_run_creation_persists_to_db(test_db_session: Session) -> None:
    """A completed run is written to the database with status 'completed'."""
    tracer = AgentTracer(db=test_db_session)

    with tracer.start_run("PlannerAgent", user_query="plan a trip") as run:
        trace_id = run.trace_id

    stored = run_repo.get_by_trace_id(test_db_session, trace_id)
    assert stored is not None
    assert stored.agent_name == "PlannerAgent"
    assert stored.status == "completed"
    assert stored.completed_at is not None
    # user_query was serialised into input_data
    payload = json.loads(stored.input_data)
    assert payload["user_query"] == "plan a trip"


def test_run_failure_records_error(test_db_session: Session) -> None:
    """An exception inside start_run sets status='failed' and records the message."""
    tracer = AgentTracer(db=test_db_session)
    trace_id: str = ""

    with pytest.raises(RuntimeError):
        with tracer.start_run("FailingAgent") as run:
            trace_id = run.trace_id
            raise RuntimeError("agent crashed")

    stored = run_repo.get_by_trace_id(test_db_session, trace_id)
    assert stored.status == "failed"
    assert "agent crashed" in stored.error_message


# ---------------------------------------------------------------------------
# TraceSpan tests
# ---------------------------------------------------------------------------


def test_span_creation_persists_to_db(test_db_session: Session) -> None:
    """A completed span is stored with correct type, output, and metadata."""
    tracer = AgentTracer(db=test_db_session)

    with tracer.start_run("TestAgent") as run:
        with tracer.start_span(SpanType.LLM_CALL, "chat_completion", input="hello") as span:
            span.set_output("world")
            span.set_metadata({"model": "gpt-4o", "tokens": 42})

    spans = span_repo.list_by_run(test_db_session, run.run_id)
    assert len(spans) == 1
    s = spans[0]
    assert s.span_name == "chat_completion"
    assert s.span_type == SpanType.LLM_CALL
    assert s.status == "completed"
    assert s.output_data == "world"
    # metadata is merged into input_data
    stored_input = json.loads(s.input_data)
    assert stored_input["metadata"]["model"] == "gpt-4o"
    assert stored_input["metadata"]["tokens"] == 42


def test_nested_span_records_parent_id(test_db_session: Session) -> None:
    """A child span created with parent_span_id carries that FK in the database."""
    tracer = AgentTracer(db=test_db_session)

    with tracer.start_run("TestAgent") as run:
        with tracer.start_span(SpanType.TOOL_CALL, "outer") as parent:
            with tracer.start_span(
                SpanType.LLM_CALL, "inner", parent_span_id=parent.span_id
            ) as child:
                pass

    spans = span_repo.list_by_run(test_db_session, run.run_id)
    assert len(spans) == 2
    inner = next(s for s in spans if s.span_name == "inner")
    assert inner.parent_span_id == parent.span_id


def test_error_span_records_failure_status(test_db_session: Session) -> None:
    """An exception inside start_span sets status='failed' and error_message."""
    tracer = AgentTracer(db=test_db_session)

    with tracer.start_run("TestAgent") as run:
        with pytest.raises(ValueError):
            with tracer.start_span(SpanType.TOOL_CALL, "bad_tool") as span:
                raise ValueError("tool exploded")

    spans = span_repo.list_by_run(test_db_session, run.run_id)
    assert len(spans) == 1
    s = spans[0]
    assert s.status == "failed"
    assert "tool exploded" in s.error_message


def test_latency_ms_populated_for_run_and_span(test_db_session: Session) -> None:
    """duration_ms is a non-negative number after both a run and a span finish."""
    tracer = AgentTracer(db=test_db_session)

    with tracer.start_run("TestAgent") as run:
        with tracer.start_span(SpanType.LLM_CALL, "timed_call") as span:
            pass

    stored_run = run_repo.get_by_trace_id(test_db_session, run.trace_id)
    spans = span_repo.list_by_run(test_db_session, run.run_id)

    assert stored_run.duration_ms is not None
    assert stored_run.duration_ms >= 0
    assert spans[0].duration_ms is not None
    assert spans[0].duration_ms >= 0


def test_start_span_outside_run_raises(test_db_session: Session) -> None:
    """Calling start_span outside a start_run context raises RuntimeError."""
    tracer = AgentTracer(db=test_db_session)

    with pytest.raises(RuntimeError, match="No active run"):
        tracer.start_span("llm", "orphan_span")
