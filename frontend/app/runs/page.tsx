"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getRuns, type AgentRun } from "@/lib/api";

export default function RunsPage() {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getRuns()
      .then(setRuns)
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : "Failed to load runs")
      )
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Agent Runs</h1>
          <p className="text-gray-500 text-sm mt-0.5">
            All recorded agent executions
          </p>
        </div>
        <Link
          href="/demo"
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors"
        >
          + New Run
        </Link>
      </div>

      {loading && (
        <p className="text-gray-500 text-sm">Loading runs…</p>
      )}

      {error && (
        <div className="p-4 bg-red-950 border border-red-800 rounded-lg text-red-300 text-sm">
          {error}
        </div>
      )}

      {!loading && !error && runs.length === 0 && (
        <div className="text-center py-16 text-gray-600">
          <p className="mb-2">No runs yet.</p>
          <Link href="/demo" className="text-blue-400 hover:underline text-sm">
            Run the demo to get started →
          </Link>
        </div>
      )}

      {runs.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-left text-xs text-gray-500">
                <th className="px-4 py-3 font-medium">Trace ID</th>
                <th className="px-4 py-3 font-medium">Agent</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Duration</th>
                <th className="px-4 py-3 font-medium">Started</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {runs.map((run) => (
                <tr key={run.trace_id} className="hover:bg-gray-800/40 transition-colors">
                  <td className="px-4 py-3">
                    <Link
                      href={`/runs/${run.trace_id}`}
                      className="font-mono text-blue-400 hover:text-blue-300 hover:underline"
                    >
                      {run.trace_id.slice(0, 8)}…
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-300">{run.agent_name}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={run.status} />
                  </td>
                  <td className="px-4 py-3 font-mono text-gray-400 text-xs">
                    {run.duration_ms != null ? `${run.duration_ms} ms` : "—"}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {new Date(run.started_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: "bg-green-950 text-green-400 border-green-900",
    failed: "bg-red-950 text-red-400 border-red-900",
    running: "bg-yellow-950 text-yellow-400 border-yellow-900",
    pending: "bg-gray-800 text-gray-400 border-gray-700",
  };
  const cls = styles[status] ?? "bg-gray-800 text-gray-400 border-gray-700";
  return (
    <span className={`px-2 py-0.5 rounded border text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
}
