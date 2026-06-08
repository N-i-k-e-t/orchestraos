import { useCallback, useEffect, useState } from "react";
import { api, type HealthAgents, type HealthLive } from "../api/client";
import { CircuitBadge } from "../components/CircuitBadge";

function Gauge({
  label,
  value,
  textClass,
  barClass,
}: {
  label: string;
  value: number;
  textClass: string;
  barClass: string;
}) {
  const pct = Math.round(value * 100);
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-sm font-medium text-slate-600">{label}</p>
      <p className={`mt-2 text-3xl font-bold ${textClass}`}>{pct}%</p>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${barClass}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function ServiceStatus({ name, status }: { name: string; status: string }) {
  const colors: Record<string, string> = {
    ok: "bg-emerald-100 text-emerald-700",
    standby: "bg-amber-100 text-amber-700",
    degraded: "bg-rose-100 text-rose-700",
    unknown: "bg-slate-100 text-slate-600",
  };
  return (
    <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
      <span className="font-medium text-slate-800">{name}</span>
      <span className={`rounded-lg px-2 py-1 text-xs font-semibold uppercase ${colors[status] || colors.unknown}`}>
        {status}
      </span>
    </div>
  );
}

export function HealthPage() {
  const [live, setLive] = useState<HealthLive | null>(null);
  const [agents, setAgents] = useState<HealthAgents | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [liveData, agentData] = await Promise.all([api.getHealthLive(), api.getHealthAgents()]);
      setLive(liveData);
      setAgents(agentData);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Health poll failed");
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 2000);
    return () => clearInterval(id);
  }, [refresh]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">System Health</h2>
        <p className="mt-1 text-slate-600">Live pipeline status — polls every 2 seconds</p>
      </div>

      {error && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
      )}

      {live && agents && (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <Gauge label="Risk score" value={live.aggregate.risk_score} textClass="text-rose-500" barClass="bg-rose-500" />
            <Gauge label="Loop score" value={live.aggregate.loop_score} textClass="text-amber-500" barClass="bg-amber-500" />
            <Gauge label="Progress" value={live.aggregate.progress_score} textClass="text-emerald-500" barClass="bg-emerald-500" />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-slate-900">Services</h3>
              <p className="mb-4 text-sm text-slate-500">Redis: {live.redis}</p>
              <div className="space-y-2">
                {live.services.map((s) => (
                  <ServiceStatus key={s.service} name={s.service} status={s.status} />
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-slate-900">Active agents</h3>
              <p className="mb-4 text-sm text-slate-500">
                {agents.agent_count} agents · {agents.capability_count} capabilities ·{" "}
                <span className="font-semibold text-indigo-600">{agents.agents_firing.length} firing</span>
              </p>
              <div className="flex flex-wrap gap-2">
                {agents.agents_firing.length === 0 ? (
                  <span className="text-sm text-slate-500">No agents firing</span>
                ) : (
                  agents.agents_firing.map((name) => (
                    <span
                      key={name}
                      className="rounded-lg bg-indigo-100 px-3 py-1 text-sm font-medium text-indigo-700"
                    >
                      {name}
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900">Circuit breakers</h3>
            <div className="mt-4 space-y-3">
              {live.sessions.length === 0 ? (
                <p className="text-sm text-slate-500">No active sessions</p>
              ) : (
                live.sessions.map((s) => (
                  <div
                    key={s.session_id}
                    className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-100 bg-slate-50 px-4 py-3"
                  >
                    <div>
                      <p className="font-medium text-slate-800">{s.session_id}</p>
                      <p className="text-xs text-slate-500">
                        risk {Math.round(s.risk_score * 100)}% · loop {Math.round(s.loop_score * 100)}%
                      </p>
                    </div>
                    <CircuitBadge state={s.breaker_state} />
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900">Recent incidents</h3>
            <ul className="mt-4 divide-y divide-slate-100">
              {live.incidents.length === 0 ? (
                <li className="py-3 text-sm text-slate-500">No incidents yet</li>
              ) : (
                live.incidents.map((inc) => (
                  <li key={inc.incident_id} className="flex flex-wrap items-start justify-between gap-2 py-3">
                    <div>
                      <p className="font-medium text-slate-800">{inc.incident_type}</p>
                      <p className="text-sm text-slate-600">{inc.reason}</p>
                    </div>
                    <span
                      className={`rounded-lg px-2 py-1 text-xs font-semibold ${
                        inc.severity === "critical"
                          ? "bg-rose-100 text-rose-700"
                          : inc.severity === "warning"
                            ? "bg-amber-100 text-amber-700"
                            : "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {inc.severity}
                    </span>
                  </li>
                ))
              )}
            </ul>
          </div>
        </>
      )}
    </div>
  );
}
