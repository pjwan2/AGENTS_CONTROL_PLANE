"""Deterministic evaluation engine for DataQualityAgent runs.

Three scores are computed from the agent's findings dict and the span outputs
already persisted in the database — no LLM calls, no external dependencies.

Scores:
  issue_detection_score  — fraction of expected issue categories that were
                           detected (1.0 = all five found).
  groundedness_score     — fraction of check spans whose output exactly matches
                           the corresponding entry in the findings dict
                           (1.0 = every finding is backed by a span).
  hallucination_risk_score — fraction of reported issue items NOT supported by
                             any span output (0.0 = no hallucinations).
"""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from backend.models.eval_result import EvalResult
from backend.repositories import eval_result as eval_repo
from backend.repositories import trace_span as span_repo
from backend.schemas.eval_result import EvalResultCreate

_EXPECTED_ISSUE_KEYS: list[str] = [
    "duplicate_transaction_ids",
    "null_settlement_dates",
    "negative_amounts",
    "invalid_currencies",
    "future_payment_dates",
]

# Maps span name → findings dict key for the five check spans.
_SPAN_TO_FINDING: dict[str, str] = {
    "check_duplicate_transaction_id": "duplicate_transaction_ids",
    "check_null_settlement_date": "null_settlement_dates",
    "check_negative_amount": "negative_amounts",
    "check_invalid_currency": "invalid_currencies",
    "check_future_payment_date": "future_payment_dates",
}


def _issue_detection_score(findings: dict[str, Any]) -> float:
    detected = sum(1 for key in _EXPECTED_ISSUE_KEYS if findings.get(key))
    return round(detected / len(_EXPECTED_ISSUE_KEYS), 4)


def _groundedness_score(
    findings: dict[str, Any],
    span_outputs: dict[str, str | None],
) -> float:
    grounded = 0
    for span_name, finding_key in _SPAN_TO_FINDING.items():
        finding = findings.get(finding_key, [])
        raw = span_outputs.get(span_name)
        if raw is not None:
            try:
                if sorted(finding) == sorted(json.loads(raw)):
                    grounded += 1
            except (json.JSONDecodeError, TypeError):
                pass
    return round(grounded / len(_SPAN_TO_FINDING), 4)


def _hallucination_risk_score(
    findings: dict[str, Any],
    span_outputs: dict[str, str | None],
) -> float:
    total_reported = sum(
        len(v)
        for k, v in findings.items()
        if k in _EXPECTED_ISSUE_KEYS and isinstance(v, list)
    )
    if total_reported == 0:
        return 0.0

    total_supported = 0
    for span_name, finding_key in _SPAN_TO_FINDING.items():
        reported = set(findings.get(finding_key, []))
        raw = span_outputs.get(span_name)
        if raw is not None:
            try:
                from_span = set(json.loads(raw))
                total_supported += len(reported & from_span)
            except (json.JSONDecodeError, TypeError):
                pass

    return round((total_reported - total_supported) / total_reported, 4)


def evaluate_data_quality_run(
    db: Session,
    run_id: int,
    findings: dict[str, Any],
) -> list[EvalResult]:
    """Compute and persist three deterministic eval scores for a DataQualityAgent run."""
    spans = span_repo.list_by_run(db, run_id)
    span_outputs: dict[str, str | None] = {s.span_name: s.output_data for s in spans}

    scores = [
        EvalResultCreate(
            agent_run_id=run_id,
            eval_name="issue_detection_score",
            eval_type="correctness",
            score=_issue_detection_score(findings),
            meta_data=json.dumps({"expected_keys": _EXPECTED_ISSUE_KEYS}),
        ),
        EvalResultCreate(
            agent_run_id=run_id,
            eval_name="groundedness_score",
            eval_type="correctness",
            score=_groundedness_score(findings, span_outputs),
            meta_data=json.dumps({"span_count": len(spans)}),
        ),
        EvalResultCreate(
            agent_run_id=run_id,
            eval_name="hallucination_risk_score",
            eval_type="safety",
            score=_hallucination_risk_score(findings, span_outputs),
            meta_data=json.dumps({"span_count": len(spans)}),
        ),
    ]
    return [eval_repo.create(db, s) for s in scores]
