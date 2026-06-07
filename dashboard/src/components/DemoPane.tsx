import type { DemoSide } from "../api/client";
import { StatCard } from "./StatCard";

interface DemoPaneProps {
  title: string;
  side: DemoSide;
  tint: "rose" | "emerald";
  subtitle: string;
}

export function DemoPane({ title, side, tint, subtitle }: DemoPaneProps) {
  const border = tint === "rose" ? "border-rose-200" : "border-emerald-200";
  const headerBg = tint === "rose" ? "bg-rose-50" : "bg-emerald-50";
  const outcomeColor =
    side.outcome === "FAILURE" ? "text-rose-500" : "text-emerald-500";

  return (
    <section
      className={`flex flex-1 flex-col overflow-hidden rounded-2xl border ${border} bg-white shadow-sm`}
    >
      <header className={`border-b ${border} px-6 py-4 ${headerBg}`}>
        <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
        <p className="text-sm text-slate-600">{subtitle}</p>
      </header>
      <div className="grid gap-4 p-6 sm:grid-cols-2">
        <StatCard label="Tool calls" value={side.calls} accent={tint} />
        <StatCard label="Duration" value={side.duration} accent={tint} />
        <StatCard label="Cost" value={`$${side.cost_usd.toFixed(2)}`} accent={tint} />
        <StatCard
          label="Outcome"
          value={side.outcome}
          sub={side.tokens ? `${side.tokens.toLocaleString()} tokens` : undefined}
          accent={tint}
        />
      </div>
      <footer className={`mt-auto border-t ${border} px-6 py-3 ${headerBg}`}>
        <p className={`text-sm font-medium ${outcomeColor}`}>
          Status: {side.outcome}
        </p>
      </footer>
    </section>
  );
}
