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

export interface HealthService {
  service: string;
  status: string;
  detail: string;
  updated_at: string | null;
}

export interface HealthSession {
  session_id: string;
  breaker_state: string;
  risk_score: number;
  loop_score: number;
  progress_score: number;
  active_agents: string[];
  updated_at: string;
}

export interface HealthIncident {
  incident_id: string;
  session_id: string;
  incident_type: string;
  severity: string;
  reason: string;
  created_at?: string;
}

export interface HealthLive {
  redis: string;
  services: HealthService[];
  sessions: HealthSession[];
  active_agent_count: number;
  incidents: HealthIncident[];
  aggregate: { risk_score: number; loop_score: number; progress_score: number };
  updated_at: string;
}

export interface HealthAgents {
  total: number;
  agent_count: number;
  capability_count: number;
  agents_firing: string[];
  roster: Array<Record<string, unknown>>;
  updated_at: string;
}

export interface OpsNode {
  id: string;
  label: string;
  layer: string;
  status: string;
  detail: string;
  links: Array<{ label: string; url: string }>;
}

export interface OpsTopology {
  nodes: OpsNode[];
  edges: Array<{ from: string; to: string; label: string }>;
  branches: Array<{ name: string; owner: string; role: string }>;
  project_id: string;
  region: string;
  dashboard_url: string;
  collector_url: string;
  updated_at: string;
}

export interface OpsTask {
  id: string;
  title: string;
  owner: string;
  status: string;
  priority: string;
}

export interface OpsTasks {
  tasks: OpsTask[];
  summary: { total: number; done: number; pending: number };
  deadline: string;
  updated_at: string;
}

export interface OpsDynamics {
  pipeline: Array<{
    stage: string;
    service: string;
    agents: string[];
    status: string;
    active_count: number;
  }>;
  agents_firing: string[];
  active_agent_count: number;
  sessions: HealthSession[];
  incidents: HealthIncident[];
  aggregate: { risk_score: number; loop_score: number; progress_score: number };
  domains: Record<string, number>;
  roster_total: number;
  updated_at: string;
}

export interface OpsSecrets {
  secrets: Array<{
    id: string;
    source: string;
    consumers: string[];
    status: string;
    env_var: string;
    note?: string;
  }>;
  service_accounts: { deploy: string; runtime: string };
  updated_at: string;
}

export interface OpsSummary {
  health: {
    redis: string;
    services_ok: number;
    services_total: number;
    active_agents: number;
    roster_total: number;
  };
  tasks: { total: number; done: number; pending: number };
  topology: { project: string; region: string };
  updated_at: string;
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
  getHealthLive: () => fetchJson<HealthLive>("/health/live"),
  getHealthAgents: () => fetchJson<HealthAgents>("/health/agents"),
  getOpsSummary: () => fetchJson<OpsSummary>("/ops/summary"),
  getOpsTopology: () => fetchJson<OpsTopology>("/ops/topology"),
  getOpsDynamics: () => fetchJson<OpsDynamics>("/ops/dynamics"),
  getOpsTasks: () => fetchJson<OpsTasks>("/ops/tasks"),
  getOpsSecrets: () => fetchJson<OpsSecrets>("/ops/secrets"),
};
