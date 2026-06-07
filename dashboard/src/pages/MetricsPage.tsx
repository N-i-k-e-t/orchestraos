import { useEffect, useState } from "react";
import { api, type MetricsSummary } from "../api/client";
import { StatCard } from "../components/StatCard";

export function MetricsPage() {
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);

  useEffect(() => {
    api.getMetrics().then(setMetrics).catch(() => setMetrics(null));
  }, []);

  if (!metrics) {
    return <p className="text-slate-400">Loading metrics…</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Metrics</h2>
        <p className="mt-1 text-slate-600">Aggregate reliability telemetry across agent sessions.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard label="Total sessions" value={metrics.total_sessions} />
        <StatCard label="Loops detected" value={metrics.loops_detected} accent="rose" />
        <StatCard label="Breakers tripped" value={metrics.breakers_tripped} accent="rose" />
        <StatCard label="Recoveries" value={metrics.recoveries} accent="emerald" />
        <StatCard label="Avg risk score" value={metrics.avg_risk_score.toFixed(2)} />
        <StatCard
          label="Cost saved"
          value={`$${metrics.cost_saved_usd.toFixed(2)}`}
          accent="emerald"
        />
      </div>
    </div>
  );
}
