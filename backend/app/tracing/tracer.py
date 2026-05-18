"""Lightweight in-process tracing SDK for AgentOps.

Usage::

    from backend.app.tracing import AgentTracer

    tracer = AgentTracer(db=session)

    with tracer.start_run("PlannerAgent", user_query="plan a trip") as run:
        print(run.trace_id)          # UUID for this execution

        with tracer.start_span(SpanType.LLM_CALL, "chat_completion", input="hello") as span:
            span.set_output("world")
            span.set_metadata({"model": "gpt-4o", "tokens": 42})

            # Nested span
            with tracer.start_span(SpanType.TOOL_CALL, "web_search",
                                   parent_span_id=span.span_id) as child:
                child.set_output(["result_1", "result_2"])
"""
from __future__ import annotations

import json
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.models.agent_run import AgentRun
from backend.models.trace_span import TraceSpan
from backend.repositories import agent_run as run_repo
from backend.repositories import trace_span as span_repo
from backend.schemas.agent_run import AgentRunCreate
from backend.schemas.enums import SpanType
from backend.schemas.trace_span import SpanCreateRequest

# Tracks the currently active RunContext within the current thread/async task.
# ContextVar is used instead of a plain attribute so the tracer stays
# re-entrant and does not bleed state across threads.
_active_run: ContextVar[Optional[RunContext]] = ContextVar(
    "_active_run", default=None
)


def _naive(dt: datetime) -> datetime:
    """Return a timezone-naive datetime.

    SQLite stores DateTime columns without timezone info, so values read back
    via db.refresh() are naive even when they were originally written as
    timezone-aware. Stripping tzinfo from both sides before arithmetic
    prevents TypeError on mixed subtraction.
    """
    return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt


class SpanContext:
    """Wraps a single TraceSpan.  Returned by :meth:`AgentTracer.start_span`.

    Must be used as a context manager.  Status, end time, and duration are
    committed automatically on ``__exit__``; exceptions are *not* suppressed.
    """

    def __init__(self, span: TraceSpan, db: Session) -> None:
        self._span = span
        self._db = db
        self._metadata: dict = {}
        self.span_id: int = span.id

    # -- helpers ---------------------------------------------------------------

    def set_output(self, output: Any) -> None:
        """Persist the span's output.  Non-strings are JSON-serialised."""
        self._span.output_data = (
            output if isinstance(output, str) else json.dumps(output)
        )

    def set_metadata(self, data: dict) -> None:
        """Accumulate key/value pairs; flushed to ``input_data`` on exit."""
        self._metadata.update(data)

    def set_error(self, error: str) -> None:
        """Explicitly record an error string without raising an exception."""
        self._span.error_message = error

    # -- context manager -------------------------------------------------------

    def __enter__(self) -> SpanContext:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        now = _naive(datetime.now(timezone.utc))
        self._span.ended_at = now

        if self._span.started_at is not None:
            self._span.duration_ms = (
                now - _naive(self._span.started_at)
            ).total_seconds() * 1000

        if exc_type is None:
            self._span.status = "completed"
        else:
            self._span.status = "failed"
            if not self._span.error_message:
                self._span.error_message = str(exc_val)

        # Merge metadata into input_data as {"input": ..., "metadata": {...}}.
        if self._metadata:
            try:
                existing = (
                    json.loads(self._span.input_data)
                    if self._span.input_data
                    else {}
                )
                if not isinstance(existing, dict):
                    existing = {"input": existing}
            except (json.JSONDecodeError, TypeError):
                existing = {"input": self._span.input_data}
            existing["metadata"] = self._metadata
            self._span.input_data = json.dumps(existing)

        self._db.commit()
        return False  # never suppress exceptions


class RunContext:
    """Wraps a single AgentRun.  Returned by :meth:`AgentTracer.start_run`.

    Must be used as a context manager.  Sets itself as the active run via
    :data:`_active_run` so nested :meth:`AgentTracer.start_span` calls can
    discover it without an explicit parameter.
    """

    def __init__(self, run: AgentRun, db: Session) -> None:
        self._run = run
        self._db = db
        self._token = None
        self.trace_id: str = run.trace_id
        self.run_id: int = run.id

    @property
    def duration_ms(self) -> Optional[int]:
        return self._run.duration_ms

    def __enter__(self) -> RunContext:
        self._token = _active_run.set(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._token is not None:
            _active_run.reset(self._token)

        now = _naive(datetime.now(timezone.utc))
        self._run.completed_at = now

        if self._run.started_at is not None:
            self._run.duration_ms = int(
                (now - _naive(self._run.started_at)).total_seconds() * 1000
            )

        if exc_type is None:
            self._run.status = "completed"
        else:
            self._run.status = "failed"
            self._run.error_message = str(exc_val)

        self._db.commit()
        return False  # never suppress exceptions


class AgentTracer:
    """Instruments agent workflows by writing AgentRun and TraceSpan rows.

    One tracer instance per database session.  No singleton, no global
    mutable state beyond the thread-local :data:`_active_run` ContextVar.

    Example::

        tracer = AgentTracer(db=db_session)

        with tracer.start_run("MyAgent", user_query="What is 2+2?") as run:
            with tracer.start_span(SpanType.LLM_CALL, "completion", input="2+2") as span:
                span.set_output("4")
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def start_run(
        self,
        agent_name: str,
        user_query: Optional[str] = None,
        model_name: Optional[str] = None,
        prompt_version: Optional[str] = None,
    ) -> RunContext:
        """Create an AgentRun and return its :class:`RunContext`.

        The returned object **must** be used as a context manager so the run
        is finalised on exit.
        """
        payload: dict = {}
        if user_query is not None:
            payload["user_query"] = user_query
        if model_name is not None:
            payload["model_name"] = model_name
        if prompt_version is not None:
            payload["prompt_version"] = prompt_version

        data = AgentRunCreate(
            agent_id=str(uuid4()),
            agent_name=agent_name,
            status="running",
            input_data=json.dumps(payload) if payload else None,
        )
        run = run_repo.create(self._db, data)
        return RunContext(run, self._db)

    def start_span(
        self,
        span_type: SpanType | str,
        name: str,
        input: Optional[Any] = None,
        metadata: Optional[dict] = None,
        parent_span_id: Optional[int] = None,
    ) -> SpanContext:
        """Create a TraceSpan under the currently active run.

        Raises :exc:`RuntimeError` if called outside a ``start_run`` context.
        Pass ``parent_span_id=span.span_id`` to nest spans.
        """
        active = _active_run.get()
        if active is None:
            raise RuntimeError(
                "No active run. Enter a start_run() context before calling start_span()."
            )

        input_str: Optional[str] = (
            None
            if input is None
            else (input if isinstance(input, str) else json.dumps(input))
        )

        data = SpanCreateRequest(
            span_name=name,
            span_type=span_type,
            status="started",
            input_data=input_str,
            parent_span_id=parent_span_id,
        )
        span = span_repo.create(self._db, active.run_id, data)
        ctx = SpanContext(span, self._db)
        if metadata:
            ctx.set_metadata(metadata)
        return ctx
