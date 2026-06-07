import { useCallback, useEffect, useState } from "react";
import { api, type DemoCompare } from "../api/client";
import { CircuitBadge } from "../components/CircuitBadge";
import { DemoPane } from "../components/DemoPane";

export function DemoPage() {
  const [data, setData] = useState<DemoCompare | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (live = false) => {
    setLoading(true);
    setError(null);
    try {
      const result = live ? await api.runDemo() : await api.getDemo();
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load demo");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(false);
  }, [load]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">AutoGPT Loop Demo</h2>
          <p className="mt-1 text-slate-600">
            Every other platform tells you your agent failed. OrchestraOS makes sure it doesn&apos;t.
          </p>
        </div>
        <button
          type="button"
          onClick={() => load(true)}
          disabled={loading}
          className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "Running…" : "Run live demo"}
        </button>
      </div>

      {error && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error}
        </div>
      )}

      {data && (
        <>
          <div className="rounded-2xl border border-slate-200 bg-white px-6 py-4 shadow-sm">
            <p className="text-sm text-slate-600">
              Cost reduction:{" "}
              <span className="text-lg font-semibold text-emerald-500">
                {data.cost_reduction_pct}%
              </span>
            </p>
          </div>

          <div className="flex flex-col gap-6 lg:flex-row">
            <DemoPane
              title="Unprotected Agent"
              subtitle="AutoGPT · no OrchestraOS"
              side={data.unprotected}
              tint="rose"
            />
            <DemoPane
              title="Protected Agent"
              subtitle="AutoGPT · OrchestraOS enabled"
              side={data.protected}
              tint="emerald"
            />
          </div>

          {data.protected_log && data.protected_log.length > 0 && (
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="mb-4 text-lg font-semibold text-slate-900">Protected run log</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-600">
                      <th className="pb-2 pr-4 font-medium">Step</th>
                      <th className="pb-2 pr-4 font-medium">Tool</th>
                      <th className="pb-2 pr-4 font-medium">Risk</th>
                      <th className="pb-2 pr-4 font-medium">Breaker</th>
                      <th className="pb-2 font-medium">Blocked</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.protected_log.map((row, i) => (
                      <tr key={i} className="border-b border-slate-100">
                        <td className="py-2 pr-4">{String(row.step ?? "-")}</td>
                        <td className="py-2 pr-4 font-mono text-xs">{String(row.tool_name ?? "-")}</td>
                        <td className="py-2 pr-4">{String(row.risk_score ?? "-")}</td>
                        <td className="py-2 pr-4">
                          {row.breaker_state ? (
                            <CircuitBadge state={String(row.breaker_state)} />
                          ) : (
                            "-"
                          )}
                        </td>
                        <td className="py-2">{row.blocked ? "Yes" : "No"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
