"""Tests for models and schemas."""
import pytest
from pydantic import ValidationError

from backend.models import AgentRun, EvalResult, PromptVersion, TraceSpan
from backend.schemas.enums import SpanType
from backend.schemas import (
    AgentRunCreate,
    AgentRunResponse,
    EvalResultCreate,
    EvalResultResponse,
    PromptVersionCreate,
    PromptVersionResponse,
    TraceSpanCreate,
    TraceSpanResponse,
)


def test_models_import_successfully() -> None:
    """Test that all models can be imported."""
    assert AgentRun is not None
    assert TraceSpan is not None
    assert EvalResult is not None
    assert PromptVersion is not None


def test_schemas_import_successfully() -> None:
    """Test that all schemas can be imported."""
    assert AgentRunCreate is not None
    assert AgentRunResponse is not None
    assert TraceSpanCreate is not None
    assert TraceSpanResponse is not None
    assert EvalResultCreate is not None
    assert EvalResultResponse is not None
    assert PromptVersionCreate is not None
    assert PromptVersionResponse is not None


def test_agent_run_schema_creation() -> None:
    """Test creating AgentRun schema."""
    schema = AgentRunCreate(
        agent_id="agent_001",
        agent_name="Test Agent",
        status="pending",
    )
    assert schema.agent_id == "agent_001"
    assert schema.agent_name == "Test Agent"
    assert schema.status == "pending"


def test_trace_span_schema_creation() -> None:
    """Test creating TraceSpan schema with a valid SpanType."""
    schema = TraceSpanCreate(
        agent_run_id=1,
        span_name="test_span",
        span_type=SpanType.TOOL_CALL,
        status="started",
    )
    assert schema.agent_run_id == 1
    assert schema.span_name == "test_span"
    assert schema.span_type == SpanType.TOOL_CALL


def test_trace_span_schema_rejects_unknown_type() -> None:
    """TraceSpanCreate raises ValidationError for an unrecognised span_type."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        TraceSpanCreate(
            agent_run_id=1,
            span_name="test_span",
            span_type="llm",  # old freeform value — now invalid
            status="started",
        )


def test_eval_result_schema_creation() -> None:
    """Test creating EvalResult schema with valid score."""
    schema = EvalResultCreate(
        agent_run_id=1,
        eval_name="correctness",
        eval_type="correctness",
        score=0.85,
    )
    assert schema.agent_run_id == 1
    assert schema.score == 0.85


def test_eval_result_schema_score_validation() -> None:
    """Test that EvalResult score must be between 0 and 1."""
    with pytest.raises(ValidationError):
        EvalResultCreate(
            agent_run_id=1,
            eval_name="correctness",
            eval_type="correctness",
            score=1.5,  # Invalid: > 1.0
        )


def test_prompt_version_schema_creation() -> None:
    """Test creating PromptVersion schema."""
    schema = PromptVersionCreate(
        prompt_key="agent_planning",
        version=1,
        content="You are a planning agent...",
    )
    assert schema.prompt_key == "agent_planning"
    assert schema.version == 1
