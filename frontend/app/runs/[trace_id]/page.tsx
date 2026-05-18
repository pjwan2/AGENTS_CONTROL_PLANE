"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  getRun,
  getSpans,
  getEvals,
  type AgentRun,
  type TraceSpan,
  type EvalResult,
} from "@/lib/api";

export default function RunDetailPage() {
  const params = useParams();
  const traceId = params.trace_id as string;

  const [run, setRun] = useState<AgentRun | null>(null);
  const [spans, setSpans] = useState<TraceSpan[]>([]);
  const [evals, setEvals] = useState<EvalResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSpan, setSelectedSpan] = useState<TraceSpan | null>(null);

  useEffect(() => {
    Promise.all([getRun(traceId), getSpans(traceId), getEvals(traceId)])
      .then(([r, s, e]) => {
        setRun(r);
        setSpans(s);
        setEvals(e);
      })
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : "Failed to load run")
      )
      .finally(() => setLoading(false));
  }, [traceId]);

  if (loading) return <p className="text-gray-500 text-sm">Loading…</p>;
  if (error)
    return (
      <div className="p-4 bg-red-950 border border-red-800 rounded-lg text-red-300 text-sm">
        {error}
      </div>
    );
  if (!run) return null;

  const runStartMs = new Date(run.started_at).getTime();
  const totalMs = run.duration_ms ?? 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start gap-4">
        <Link
          href="/runs"
          className="text-gray-500 hover:text-gray-300 text-sm mt-1 shrink-0"
        >
          ← Runs
        </Link>
        <div>
          <h1 className="text-xl font-bold font-mono break-all">{run.trace_id}</h1>
          <p className="text-gray-500 text-sm mt-0.5">
            {run.agent_name} · started {new Date(run.started_at).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Run summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Stat label="status" value={run.status} />
        <Stat label="agent" value={run.agent_name} />
        <Stat
          label="duration"
          value={run.duration_ms != null ? `${run.duration_ms} ms` : "—"}
        />
        <Stat label="spans" value={String(spans.length)} />
      </div>

      {/* Eval Scores */}
      {evals.length > 0 && (
        <Card title="Eval Scores">
          <div className="space-y-3">
            {evals.map((ev) => (
              <ScoreBar key={ev.id} ev={ev} />
            ))}
          </div>
        </Card>
      )}

      {/* Trace Timeline */}
      {spans.length > 0 && (
        <Card title={`Trace Timeline — ${spans.length} spans`}>
          <div className="space-y-2">
            {spans.map((span) => {
              const spanStart = new Date(span.started_at).getTime();
              const spanDuration = span.duration_ms ?? 0;
              const offsetPct = Math.max(
                0,
                ((spanStart - runStartMs) / totalMs) * 100
              );
              const widthPct = Math.max(0.5, (spanDuration / totalMs) * 100);
              const isSelected = selectedSpan?.id === span.id;

              return (
                <div key={span.id}>
                  <div className="flex items-center gap-3">
                    <span className="w-56 text-xs text-gray-400 truncate shrink-0">
                      {span.span_name}
                    </span>
                    <span className="w-24 text-xs text-gray-600 shrink-0">
                      {span.span_type}
                    </span>
                    <div className="flex-1 relative h-5 bg-gray-800 rounded overflow-hidden">
                      <button
                        onClick={() =>
                          setSelectedSpan(isSelected ? null : span)
                        }
                        className={`absolute h-full rounded transition-opacity ${
                          span.status === "failed"
                            ? "bg-red-500"
                            : "bg-blue-500"
                        } ${isSelected ? "opacity-100" : "opacity-60 hover:opacity-80"}`}
                        style={{
                          left: `${offsetPct}%`,
                          width: `${Math.min(widthPct, 100 - offsetPct)}%`,
                          minWidth: "4px",
                        }}
                        title={`${span.span_name} — ${spanDuration.toFixed(1)} ms`}
                      />
                    </div>
                    <span className="w-20 text-xs font-mono text-gray-500 text-right shrink-0">
                      {spanDuration.toFixed(1)} ms
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
          {!selectedSpan && (
            <p className="text-xs text-gray-600 mt-3">
              Click a span bar to inspect its details.
            </p>
          )}
        </Card>
      )}

      {/* Span Detail */}
      {selectedSpan && (
        <Card title={`Span Detail — ${selectedSpan.span_name}`}>
          <div className="flex justify-between items-center mb-3">
            <div className="flex gap-3 text-xs">
              <span className="text-gray-500">
                type:{" "}
                <span className="text-gray-300">{selectedSpan.span_type}</span>
              </span>
              <span className="text-gray-500">
                status:{" "}
                <span
                  className={
                    selectedSpan.status === "failed"
                      ? "text-red-400"
                      : "text-green-400"
                  }
                >
                  {selectedSpan.status}
                </span>
              </span>
              <span className="text-gray-500">
                duration:{" "}
                <span className="text-gray-300 font-mono">
                  {selectedSpan.duration_ms?.toFixed(1)} ms
                </span>
              </span>
            </div>
            <button
              onClick={() => setSelectedSpan(null)}
              className="text-xs text-gray-600 hover:text-gray-400"
            >
              close ✕
            </button>
          </div>
          <pre className="text-xs text-gray-400 overflow-auto leading-relaxed bg-gray-950 rounded p-3">
            {JSON.stringify(
              {
                input: safeJson(selectedSpan.input_data),
                output: safeJson(selectedSpan.output_data),
                error_message: selectedSpan.error_message,
              },
              null,
              2
            )}
          </pre>
        </Card>
      )}

      {/* Run error */}
      {run.error_message && (
        <Card title="Error">
          <p className="text-red-400 text-sm font-mono">{run.error_message}</p>
        </Card>
      )}
    </div>
  );
}

function safeJson(raw: string | null): unknown {
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-sm font-mono font-medium truncate">{value}</p>
    </div>
  );
}

function Card({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
      <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">
        {title}
      </h2>
      {children}
    </div>
  );
}

function ScoreBar({ ev }: { ev: EvalResult }) {
  const pct = Math.round(ev.score * 100);
  const isRisk = ev.eval_name.includes("risk");
  const barColor = isRisk
    ? ev.score === 0
      ? "bg-green-500"
      : "bg-red-500"
    : ev.score >= 0.9
      ? "bg-green-500"
      : ev.score >= 0.6
        ? "bg-yellow-500"
        : "bg-red-500";

  return (
    <div>
      <div className="flex justify-between text-xs mb-1.5">
        <span className="text-gray-400">{ev.eval_name}</span>
        <span className="font-mono text-gray-300">{ev.score.toFixed(4)}</span>
      </div>
      <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
