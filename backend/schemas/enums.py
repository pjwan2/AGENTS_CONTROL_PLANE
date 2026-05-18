"""Shared enumeration types for AgentOps schemas."""
from enum import Enum


class SpanType(str, Enum):
    """Allowed values for TraceSpan.span_type.

    Using ``str`` as a mixin means each member *is* its value string, so
    Pydantic serialises it as a plain string and SQLAlchemy stores it directly
    in the ``String(50)`` column without any extra mapping.
    """

    LLM_CALL = "LLM_CALL"
    TOOL_CALL = "TOOL_CALL"
    RETRIEVAL = "RETRIEVAL"
    EVALUATION = "EVALUATION"
    HANDOFF = "HANDOFF"
    GUARDRAIL = "GUARDRAIL"
    ERROR = "ERROR"
    CUSTOM = "CUSTOM"
