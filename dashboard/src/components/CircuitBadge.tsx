type CircuitState = "closed" | "half_open" | "open" | string;

const styles: Record<string, string> = {
  closed: "bg-emerald-100 text-emerald-700 border-emerald-200",
  half_open: "bg-amber-100 text-amber-700 border-amber-200",
  open: "bg-rose-100 text-rose-700 border-rose-200",
};

export function CircuitBadge({ state }: { state: CircuitState }) {
  const key = state.toLowerCase().replace("-", "_");
  const label = key.replace("_", "-").toUpperCase();
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${styles[key] ?? "bg-slate-100 text-slate-600 border-slate-200"}`}
    >
      {label}
    </span>
  );
}
