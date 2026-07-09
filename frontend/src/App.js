import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import { api } from "./lib/sar";
import { Toaster } from "@/components/ui/sonner";
import Importar from "./pages/Importar";
import Dashboard from "./pages/Dashboard";
import Reportes from "./pages/Reportes";
import Historial from "./pages/Historial";
import { LayoutDashboard, UploadCloud, FileSpreadsheet, Database, ShieldCheck } from "lucide-react";

const NAV = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "importar", label: "Importar", icon: UploadCloud },
  { id: "reportes", label: "Concentrados", icon: FileSpreadsheet },
  { id: "historial", label: "Base Histórica", icon: Database },
];

function App() {
  const [view, setView] = useState("dashboard");
  const [semanas, setSemanas] = useState([]);

  const loadSemanas = useCallback(() => {
    api.get("/semanas").then((r) => setSemanas(r.data)).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => { loadSemanas(); }, [loadSemanas]);

  return (
    <div className="min-h-screen flex" style={{ background: "#f4f6fb" }}>
      <Toaster position="top-right" richColors />
      {/* Sidebar */}
      <aside className="w-64 shrink-0 text-white flex flex-col" style={{ background: "var(--sar-navy)" }}>
        <div className="px-6 py-6 border-b border-white/10">
          <div className="flex items-center gap-2.5">
            <div className="h-9 w-9 rounded-lg bg-amber-500 flex items-center justify-center">
              <ShieldCheck className="h-5 w-5 text-slate-900" />
            </div>
            <div>
              <div className="font-display font-extrabold text-lg leading-none">SAR</div>
              <div className="text-[10px] text-white/50 tracking-wide">Auditoría & Recuperación</div>
            </div>
          </div>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {NAV.map((n) => {
            const Icon = n.icon;
            const active = view === n.id;
            return (
              <button key={n.id} data-testid={`nav-${n.id}`} onClick={() => setView(n.id)}
                className={`sar-nav-item w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium ${active ? "bg-amber-500 text-slate-900" : "text-white/70 hover:bg-white/10 hover:text-white"}`}>
                <Icon className="h-4 w-4" />{n.label}
              </button>
            );
          })}
        </nav>
        <div className="p-4 text-[11px] text-white/40 border-t border-white/10">
          Gerencia de Mejoras · 17 tiendas
        </div>
      </aside>

      {/* Content */}
      <main className="flex-1 min-w-0 p-6 lg:p-10 overflow-auto max-h-screen">
        {view === "dashboard" && <Dashboard semanas={semanas} />}
        {view === "importar" && <Importar onImported={loadSemanas} />}
        {view === "reportes" && <Reportes semanas={semanas} />}
        {view === "historial" && <Historial />}
      </main>
    </div>
  );
}

export default App;
