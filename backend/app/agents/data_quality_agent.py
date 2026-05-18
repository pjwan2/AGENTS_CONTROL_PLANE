"""Data Quality Demo Agent using the AgentTracer SDK."""
from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.tracing import AgentTracer
from backend.schemas.enums import SpanType

_DEFAULT_DATASET = Path(__file__).parent.parent.parent / "sample_data" / "payments.csv"

_VALID_CURRENCIES = frozenset({
    "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY",
    "HKD", "NZD", "SEK", "NOK", "DKK", "SGD", "MXN", "INR",
    "BRL", "ZAR", "RUB", "KRW",
})


def _load_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _check_duplicates(rows: list[dict]) -> list[str]:
    seen: set[str] = set()
    dupes: list[str] = []
    for row in rows:
        txn_id = row.get("transaction_id", "")
        if txn_id in seen:
            dupes.append(txn_id)
        else:
            seen.add(txn_id)
    return dupes


def _check_null_settlement_date(rows: list[dict]) -> list[str]:
    return [
        row["transaction_id"]
        for row in rows
        if not row.get("settlement_date", "").strip()
    ]


def _check_negative_amount(rows: list[dict]) -> list[str]:
    result = []
    for row in rows:
        try:
            if float(row.get("amount", "0") or "0") < 0:
                result.append(row["transaction_id"])
        except ValueError:
            pass
    return result


def _check_invalid_currency(rows: list[dict]) -> list[str]:
    return [
        row["transaction_id"]
        for row in rows
        if row.get("currency", "").strip() not in _VALID_CURRENCIES
    ]


def _check_future_payment_date(rows: list[dict]) -> list[str]:
    today = date.today()
    result = []
    for row in rows:
        try:
            pdate = datetime.strptime(row.get("payment_date", ""), "%Y-%m-%d").date()
            if pdate > today:
                result.append(row["transaction_id"])
        except ValueError:
            pass
    return result


class DataQualityAgent:
    """Runs data-quality checks on a CSV payments dataset using AgentTracer."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def run(
        self,
        user_query: str = "Check data quality",
        dataset_path: Optional[str] = None,
    ) -> dict[str, Any]:
        """Execute all quality checks and return trace_id plus findings dict.

        Raises FileNotFoundError if dataset_path does not exist.
        """
        path = str(dataset_path or _DEFAULT_DATASET)
        tracer = AgentTracer(db=self._db)
        findings: dict[str, Any] = {}
        trace_id: str = ""

        with tracer.start_run("DataQualityAgent", user_query=user_query) as run:
            trace_id = run.trace_id

            with tracer.start_span(SpanType.TOOL_CALL, "load_dataset", input=path) as span:
                rows = _load_csv(path)
                span.set_output(f"Loaded {len(rows)} rows")

            with tracer.start_span(SpanType.TOOL_CALL, "inspect_schema") as span:
                schema = list(rows[0].keys()) if rows else []
                span.set_output(schema)
                findings["schema"] = schema

            with tracer.start_span(SpanType.TOOL_CALL, "check_duplicate_transaction_id") as span:
                dupes = _check_duplicates(rows)
                span.set_output(dupes)
                findings["duplicate_transaction_ids"] = dupes

            with tracer.start_span(SpanType.TOOL_CALL, "check_null_settlement_date") as span:
                nulls = _check_null_settlement_date(rows)
                span.set_output(nulls)
                findings["null_settlement_dates"] = nulls

            with tracer.start_span(SpanType.TOOL_CALL, "check_negative_amount") as span:
                negatives = _check_negative_amount(rows)
                span.set_output(negatives)
                findings["negative_amounts"] = negatives

            with tracer.start_span(SpanType.TOOL_CALL, "check_invalid_currency") as span:
                invalid_curr = _check_invalid_currency(rows)
                span.set_output(invalid_curr)
                findings["invalid_currencies"] = invalid_curr

            with tracer.start_span(SpanType.TOOL_CALL, "check_future_payment_date") as span:
                future_dates = _check_future_payment_date(rows)
                span.set_output(future_dates)
                findings["future_payment_dates"] = future_dates

            with tracer.start_span(SpanType.CUSTOM, "summarize_findings") as span:
                issue_count = sum(
                    len(v)
                    for k, v in findings.items()
                    if k != "schema" and isinstance(v, list)
                )
                summary = {
                    "total_rows": len(rows),
                    "total_issues": issue_count,
                    "checks_passed": issue_count == 0,
                }
                span.set_output(summary)
                findings["summary"] = summary

        return {"trace_id": trace_id, "findings": findings}
