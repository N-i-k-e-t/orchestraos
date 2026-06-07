import { useEffect, useState } from "react";
import { api, type Incident } from "../api/client";

const severityColor: Record<string, string> = {
  critical: "text-rose-500",
  warning: "text-amber-500",
  info: "text-slate-600",
};

export function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);

  useEffect(() => {
    api.getIncidents().then((r) => setIncidents(r.incidents)).catch(() => setIncidents([]));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Incidents</h2>
        <p className="mt-1 text-slate-600">Detected loops, breaker trips, and escalations.</p>
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50">
            <tr className="text-slate-600">
              <th className="px-6 py-3 font-medium">ID</th>
              <th className="px-6 py-3 font-medium">Session</th>
              <th className="px-6 py-3 font-medium">Type</th>
              <th className="px-6 py-3 font-medium">Severity</th>
              <th className="px-6 py-3 font-medium">Scenario</th>
              <th className="px-6 py-3 font-medium">Reason</th>
            </tr>
          </thead>
          <tbody>
            {incidents.map((inc) => (
              <tr key={inc.incident_id} className="border-b border-slate-100">
                <td className="px-6 py-4 font-mono text-xs text-slate-400">{inc.incident_id.slice(0, 8)}</td>
                <td className="px-6 py-4">{inc.session_id}</td>
                <td className="px-6 py-4 capitalize">{inc.incident_type.replace("_", " ")}</td>
                <td className={`px-6 py-4 font-medium capitalize ${severityColor[inc.severity] ?? ""}`}>
                  {inc.severity}
                </td>
                <td className="px-6 py-4">{inc.scenario}</td>
                <td className="px-6 py-4 text-slate-600">{inc.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {incidents.length === 0 && (
          <p className="px-6 py-8 text-center text-slate-400">No incidents recorded yet.</p>
        )}
      </div>
    </div>
  );
}
