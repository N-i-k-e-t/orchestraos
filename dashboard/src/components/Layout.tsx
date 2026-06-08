import { NavLink, Outlet } from "react-router-dom";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
    isActive
      ? "bg-indigo-600 text-white"
      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
  }`;

export function Layout() {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-bold text-slate-900">OrchestraOS</h1>
            <p className="text-sm text-slate-400">Loop Sentinel · Multi-Agent Reliability OS</p>
          </div>
          <nav className="flex gap-2">
            <NavLink to="/" end className={linkClass}>
              Demo
            </NavLink>
            <NavLink to="/incidents" className={linkClass}>
              Incidents
            </NavLink>
            <NavLink to="/metrics" className={linkClass}>
              Metrics
            </NavLink>
            <NavLink to="/health" className={linkClass}>
              Health
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
