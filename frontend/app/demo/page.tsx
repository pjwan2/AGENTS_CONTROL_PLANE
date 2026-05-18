"use client";

import { useState } from "react";
import Link from "next/link";
import { runDataQualityAgent, type DataQualityRunResponse } from "@/lib/api";

export default function DemoPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DataQualityRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await runDataQualityAgent();
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold mb-1">Data Quality Demo</h1>
      <p className="text-gray-500 text-sm mb-6">
        Runs the DataQualityAgent against the built-in payments dataset and
        evaluates the result. The run is persisted and viewable on the{" "}
        <Link href="/runs" className="text-blue-400 hover:underline">
          Runs
        </Link>{" "}
        page.
      </p>

      <button
        onClick={handleRun}
        disabled={loading}
        className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
      >
        {loading ? "Running…" : "Run Data Quality Agent"}
      </button>

      {error && (
        <div className="mt-4 p-4 bg-red-950 border border-red-800 rounded-lg text-red-300 text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Stat label="trace_id" value={result.trace_id.slice(0, 8) + "…"} />
            <Stat label="status" value={result.status} />
            <Stat label="issues found" value={String(result.issue_count)} />
            <Stat
              label="duration"
              value={
                result.duration_ms != null ? `${result.duration_ms} ms` : "—"
              }
            />
          </div>

          <Card title="Eval Scores">
            <div className="space-y-3">
              {Object.entries(result.eval_summary).map(([name, score]) => (
                <ScoreBar key={name} name={name} score={score} />
              ))}
            </div>
          </Card>

          <Card title="Findings">
            <pre className="text-xs text-gray-400 overflow-auto leading-relaxed">
              {JSON.stringify(result.findings, null, 2)}
            </pre>
          </Card>

          <Link
            href={`/runs/${result.trace_id}`}
            className="inline-block text-sm text-blue-400 hover:underline"
          >
            View full trace →
          </Link>
        </div>
      )}
    </div>
  );
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
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
        {title}
      </h2>
      {children}
    </div>
  );
}

function ScoreBar({ name, score }: { name: string; score: number }) {
  const pct = Math.round(score * 100);
  const isRisk = name.includes("risk");
  const barColor = isRisk
    ? score === 0
      ? "bg-green-500"
      : "bg-red-500"
    : score >= 0.9
      ? "bg-green-500"
      : score >= 0.6
        ? "bg-yellow-500"
        : "bg-red-500";

  return (
    <div>
      <div className="flex justify-between text-xs mb-1.5">
        <span className="text-gray-400">{name}</span>
        <span className="font-mono text-gray-300">{score.toFixed(4)}</span>
      </div>
      <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${barColor} transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
