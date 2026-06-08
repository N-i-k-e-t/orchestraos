import { useCallback, useEffect, useState } from "react";
import {
  api,
  type OpsDynamics,
  type OpsSecrets,
  type OpsSummary,
  type OpsTasks,
  type OpsTopology,
} from "../api/client";

const statusColor: Record<string, string> = {
  ok: "bg-emerald-500/20 text-emerald-300 ring-emerald-500/40",
  done: "bg-emerald-500/20 text-emerald-300 ring-emerald-500/40",
  configured: "bg-emerald-500/20 text-emerald-300 ring-emerald-500/40",
  standby: "bg-amber-500/20 text-amber-300 ring-amber-500/40",
  check: "bg-amber-500/20 text-amber-300 ring-amber-500/40",
  in_progress: "bg-sky-500/20 text-sky-300 ring-sky-500/40",
  pending: "bg-slate-500/20 text-slate-300 ring-slate-500/40",
  optional: "bg-slate-500/20 text-slate-400 ring-slate-500/40",
  missing: "bg-rose-500/20 text-rose-300 ring-rose-500/40",
  degraded: "bg-rose-500/20 text-rose-300 ring-rose-500/40",
  unknown: "bg-slate-500/20 text-slate-400 ring-slate-500/40",
};

function Badge({ status }: { status: string }) {
  return (
    <span className={`rounded-md px-2 py-0.5 text-xs font-semibold uppercase ring-1 ${statusColor[status] || statusColor.unknown}`}>
      {status}
    </span>
  );
}

function ConnectionMindMap({ topo }: { topo: OpsTopology }) {
  const layers = ["edge", "dev", "source", "cloud", "pipeline"] as const;
  const layerLabels: Record<string, string> = {
    edge: "External",
    dev: "Dev tools",
    source: "Source control",
    cloud: "Google Cloud",
    pipeline: "Cloud Run pipeline",
  };

  return (
    <div className="space-y-6">
      {layers.map((layer) => {
        const nodes = topo.nodes.filter((n) => n.layer === layer);
        if (!nodes.length) return null;
        return (
          <div key={layer}>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">{layerLabels[layer]}</p>
            <div className="flex flex-wrap gap-3">
              {nodes.map((node) => (
                <div
                  key={node.id}
                  className="min-w-[160px] rounded-xl border border-slate-700 bg-slate-900/60 p-3 shadow-lg"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold text-white">{node.label}</span>
                    <Badge status={node.status} />
                  </div>
                  <p className="mt-1 text-xs text-slate-400">{node.detail}</p>
                  {node.links?.map((l) => (
                    <a
                      key={l.url}
                      href={l.url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-2 block truncate text-xs text-cyan-400 hover:underline"
                    >
                      {l.label} ↗
                    </a>
                  ))}
                </div>
              ))}
            </div>
          </div>
        );
      })}

      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
        <p className="mb-3 text-sm font-medium text-slate-300">Connection flow (mind map)</p>
        <div className="flex flex-wrap items-center gap-2 text-sm text-slate-400">
          <span className="rounded-lg bg-violet-500/20 px-2 py-1 text-violet-200">Cursor</span>
          <span>→</span>
          <span className="rounded-lg bg-violet-500/20 px-2 py-1 text-violet-200">Antigravity</span>
          <span>→</span>
          <span className="rounded-lg bg-slate-700 px-2 py-1">GitHub</span>
          <span>→</span>
          <span className="rounded-lg bg-sky-500/20 px-2 py-1 text-sky-200">GCP Cloud Build</span>
          <span>→</span>
          <span className="rounded-lg bg-sky-500/20 px-2 py-1 text-sky-200">Cloud Run ×7</span>
          <span>→</span>
          <span className="rounded-lg bg-emerald-500/20 px-2 py-1 text-emerald-200">Live agents</span>
        </div>
        <div className="mt-4 grid gap-2 sm:grid-cols-2">
          {topo.edges.slice(0, 8).map((e, i) => (
            <div key={i} className="rounded-lg bg-slate-800/50 px-3 py-2 text-xs text-slate-400">
              <span className="text-slate-200">{e.from}</span> → <span className="text-slate-200">{e.to}</span>
              <span className="ml-2 text-slate-500">({e.label})</span>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
        <p className="mb-2 text-sm font-medium text-slate-300">Git branches</p>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {topo.branches.map((b) => (
            <div key={b.name} className="rounded-lg border border-slate-700 px-3 py-2">
              <p className="font-mono text-sm text-cyan-300">{b.name}</p>
              <p className="text-xs text-slate-400">
                {b.owner} · {b.role}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function OpsCenterPage() {
  const [summary, setSummary] = useState<OpsSummary | null>(null);
  const [topo, setTopo] = useState<OpsTopology | null>(null);
  const [dynamics, setDynamics] = useState<OpsDynamics | null>(null);
  const [tasks, setTasks] = useState<OpsTasks | null>(null);
  const [secrets, setSecrets] = useState<OpsSecrets | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [s, t, d, tk, sec] = await Promise.all([
        api.getOpsSummary(),
        api.getOpsTopology(),
        api.getOpsDynamics(),
        api.getOpsTasks(),
        api.getOpsSecrets(),
      ]);
      setSummary(s);
      setTopo(t);
      setDynamics(d);
      setTasks(tk);
      setSecrets(sec);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ops poll failed");
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 3000);
    return () => clearInterval(id);
  }, [refresh]);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white">Command Center</h2>
        <p className="mt-1 text-slate-400">
          Monitors the real app — agents, pipeline dynamics, team tasks, and GitHub → GCP → Cursor → Antigravity map
        </p>
      </div>

      {error && <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">{error}</div>}

      {summary && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
            <p className="text-xs text-slate-500">Redis</p>
            <p className="mt-1 text-2xl font-bold text-white">{summary.health.redis}</p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
            <p className="text-xs text-slate-500">Services OK</p>
            <p className="mt-1 text-2xl font-bold text-white">
              {summary.health.services_ok}/{summary.health.services_total}
            </p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
            <p className="text-xs text-slate-500">Agents firing</p>
            <p className="mt-1 text-2xl font-bold text-cyan-400">{summary.health.active_agents}</p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
            <p className="text-xs text-slate-500">Roster</p>
            <p className="mt-1 text-2xl font-bold text-white">{summary.health.roster_total}</p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
            <p className="text-xs text-slate-500">Tasks done</p>
            <p className="mt-1 text-2xl font-bold text-emerald-400">
              {summary.tasks.done}/{summary.tasks.total}
            </p>
          </div>
        </div>
      )}

      {dynamics && (
        <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
          <h3 className="text-lg font-semibold text-white">Agent pipeline dynamics</h3>
          <p className="mb-4 text-sm text-slate-400">Live Pub/Sub stages — polls every 3s</p>
          <div className="grid gap-3 lg:grid-cols-3">
            {dynamics.pipeline.map((stage) => (
              <div key={stage.stage} className="rounded-xl border border-slate-700 bg-slate-950/50 p-4">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-white">{stage.stage}</span>
                  <Badge status={stage.status} />
                </div>
                <p className="mt-1 text-xs text-slate-500">{stage.service}</p>
                <p className="mt-2 text-xs text-cyan-400/80">{stage.active_count} active in stage</p>
                <div className="mt-2 flex flex-wrap gap-1">
                  {stage.agents.map((a) => (
                    <span
                      key={a}
                      className={`rounded px-1.5 py-0.5 text-xs ${
                        dynamics.agents_firing.includes(a)
                          ? "bg-cyan-500/30 text-cyan-200"
                          : "bg-slate-800 text-slate-500"
                      }`}
                    >
                      {a}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
          {dynamics.agents_firing.length > 0 && (
            <p className="mt-4 text-sm text-slate-400">
              Currently firing:{" "}
              <span className="text-cyan-300">{dynamics.agents_firing.join(", ")}</span>
            </p>
          )}
        </section>
      )}

      {tasks && (
        <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white">Team tasks</h3>
              <p className="text-sm text-slate-400">Hackathon deadline: {tasks.deadline}</p>
            </div>
            <Badge status={tasks.summary.done === tasks.summary.total ? "done" : "in_progress"} />
          </div>
          <div className="space-y-2">
            {tasks.tasks.map((t) => (
              <div
                key={t.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-700/80 bg-slate-950/40 px-4 py-3"
              >
                <div>
                  <p className="text-sm text-white">{t.title}</p>
                  <p className="text-xs text-slate-500">
                    {t.owner} · {t.priority}
                  </p>
                </div>
                <Badge status={t.status} />
              </div>
            ))}
          </div>
        </section>
      )}

      {topo && (
        <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
          <h3 className="mb-4 text-lg font-semibold text-white">Connection map</h3>
          <p className="mb-4 text-sm text-slate-400">
            GitHub → GCP ({topo.project_id}) · Cursor · Antigravity · external agents
          </p>
          <ConnectionMindMap topo={topo} />
        </section>
      )}

      {secrets && (
        <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
          <h3 className="mb-4 text-lg font-semibold text-white">Keys & secrets map</h3>
          <p className="mb-4 text-sm text-slate-400">Secret IDs only — never values. See Secret Manager in GCP.</p>
          <div className="mb-4 rounded-lg border border-slate-700 bg-slate-950/50 p-3 font-mono text-xs text-slate-400">
            deploy: {secrets.service_accounts.deploy}
            <br />
            runtime: {secrets.service_accounts.runtime}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-700 text-slate-500">
                  <th className="py-2 pr-4">Secret ID</th>
                  <th className="py-2 pr-4">Source</th>
                  <th className="py-2 pr-4">Consumers</th>
                  <th className="py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {secrets.secrets.map((s) => (
                  <tr key={s.id} className="border-b border-slate-800/80">
                    <td className="py-3 pr-4 font-mono text-cyan-300">{s.id}</td>
                    <td className="py-3 pr-4 text-slate-400">{s.source}</td>
                    <td className="py-3 pr-4 text-slate-400">{s.consumers.join(", ")}</td>
                    <td className="py-3">
                      <Badge status={s.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
