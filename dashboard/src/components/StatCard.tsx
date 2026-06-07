interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  accent?: "rose" | "emerald" | "default";
}

const accentMap = {
  rose: "border-rose-200 bg-rose-50/50",
  emerald: "border-emerald-200 bg-emerald-50/50",
  default: "border-slate-200 bg-white",
};

export function StatCard({ label, value, sub, accent = "default" }: StatCardProps) {
  return (
    <div className={`rounded-2xl border p-5 shadow-sm ${accentMap[accent]}`}>
      <p className="text-sm font-medium text-slate-600">{label}</p>
      <p className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">{value}</p>
      {sub && <p className="mt-1 text-sm text-slate-400">{sub}</p>}
    </div>
  );
}
