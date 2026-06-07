export interface DemoSide {
  calls: number;
  duration: string;
  cost_usd: number;
  outcome: string;
  tokens?: number;
}

export interface DemoCompare {
  scenario: string;
  title: string;
  unprotected: DemoSide;
  protected: DemoSide;
  cost_reduction_pct: number;
  protected_log?: Array<Record<string, unknown>>;
}

export interface Incident {
  incident_id: string;
  session_id: string;
  incident_type: string;
  severity: string;
  scenario: string;
  reason: string;
  created_at: string;
}

export interface MetricsSummary {
  total_sessions: number;
  loops_detected: number;
  breakers_tripped: number;
  recoveries: number;
  avg_risk_score: number;
  cost_saved_usd: number;
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  getDemo: () => fetchJson<DemoCompare>("/api/demo/compare"),
  runDemo: () => fetchJson<DemoCompare>("/api/demo/run", { method: "POST" }),
  getIncidents: () => fetchJson<{ incidents: Incident[] }>("/api/incidents"),
  getMetrics: () => fetchJson<MetricsSummary>("/api/metrics"),
};
