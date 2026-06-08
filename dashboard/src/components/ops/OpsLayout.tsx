import { NavLink, Outlet } from "react-router-dom";

export function OpsLayout() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur">
        <div className="mx-auto flex max-w-[1400px] items-center justify-between px-6 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-cyan-400">Separate ops view</p>
            <h1 className="text-xl font-bold text-white">OrchestraOS Ops Center</h1>
            <p className="text-sm text-slate-400">Agents · pipeline · GitHub → GCP · keys map</p>
          </div>
          <nav className="flex items-center gap-3">
            <a
              href="/"
              className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:border-slate-500 hover:text-white"
            >
              ← Demo dashboard
            </a>
            <NavLink
              to="/ops"
              end
              className={({ isActive }) =>
                `rounded-lg px-3 py-2 text-sm font-medium ${
                  isActive ? "bg-cyan-600 text-white" : "text-slate-400 hover:text-white"
                }`
              }
            >
              Command center
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-[1400px] px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
