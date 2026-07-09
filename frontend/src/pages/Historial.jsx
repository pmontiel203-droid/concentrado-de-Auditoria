import { useEffect, useState } from "react";
import { api, fmt, money } from "../lib/sar";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { History, Search, Database } from "lucide-react";

const RESULT_COLOR = (r) => {
  if (!r) return "bg-slate-100 text-slate-600";
  if (r.startsWith("IMPORTADO")) return "bg-emerald-100 text-emerald-700";
  if (r.includes("DIFERENCIAS")) return "bg-amber-100 text-amber-700";
  if (r === "OMITIDO") return "bg-slate-100 text-slate-600";
  return "bg-red-100 text-red-700";
};

export default function Historial() {
  const [tab, setTab] = useState("base");
  const [logs, setLogs] = useState([]);
  const [regs, setRegs] = useState([]);
  const [q, setQ] = useState("");

  useEffect(() => {
    api.get("/imports").then((r) => setLogs(r.data));
    api.get("/registros").then((r) => setRegs(r.data));
  }, []);

  const filtered = regs.filter((r) => {
    if (!q) return true;
    const s = q.toLowerCase();
    return (r.tienda || "").toLowerCase().includes(s) || (r.catalogo || "").toLowerCase().includes(s) || (r.responsable || "").toLowerCase().includes(s);
  });

  return (
    <div className="sar-fade space-y-6">
      <div>
        <h1 className="font-display text-3xl font-bold text-slate-900">Base Histórica & Registros</h1>
        <p className="text-slate-500 text-sm mt-1">Todos los datos en una única base con detalle por tienda y catálogo.</p>
      </div>

      <div className="flex gap-2">
        <button data-testid="tab-base" onClick={() => setTab("base")}
          className={`sar-nav-item px-4 py-2 rounded-lg text-sm font-medium border ${tab === "base" ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-600 border-slate-200"}`}>
          <Database className="h-4 w-4 inline mr-1.5" />Base Histórica ({regs.length})
        </button>
        <button data-testid="tab-logs" onClick={() => setTab("logs")}
          className={`sar-nav-item px-4 py-2 rounded-lg text-sm font-medium border ${tab === "logs" ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-600 border-slate-200"}`}>
          <History className="h-4 w-4 inline mr-1.5" />Registro de importaciones ({logs.length})
        </button>
      </div>

      {tab === "base" ? (
        <Card className="p-4">
          <div className="relative mb-3 max-w-sm">
            <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <Input data-testid="search-base" placeholder="Buscar tienda, catálogo o responsable…" value={q} onChange={(e) => setQ(e.target.value)} className="pl-9" />
          </div>
          <div className="overflow-auto max-h-[60vh] rounded-lg border">
            <Table>
              <TableHeader className="sticky top-0 bg-slate-50 z-10">
                <TableRow>
                  {["Sem", "Tienda", "Área", "Catálogo", "Responsable", "Auditados", "Negado", "Recuperado", "Sin Exhib.", "Exhib.", "Frente", "Bodega", "Costo"].map((h) => (
                    <TableHead key={h} className="text-xs whitespace-nowrap">{h}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.slice(0, 500).map((r) => (
                  <TableRow key={r.id} className="text-xs" data-testid="base-row">
                    <TableCell>{r.semana}</TableCell>
                    <TableCell className="font-medium whitespace-nowrap">{r.tienda}</TableCell>
                    <TableCell><Badge variant="outline" className="text-[10px]">{r.area}</Badge></TableCell>
                    <TableCell className="whitespace-nowrap">{r.catalogo}</TableCell>
                    <TableCell className="whitespace-nowrap text-slate-500">{r.responsable}</TableCell>
                    <TableCell>{fmt(r.auditados)}</TableCell>
                    <TableCell className="text-red-600">{fmt(r.negado)}</TableCell>
                    <TableCell className="text-emerald-600">{fmt(r.recuperado)}</TableCell>
                    <TableCell>{fmt(r.sin_exhibicion)}</TableCell>
                    <TableCell>{fmt(r.exhibicion)}</TableCell>
                    <TableCell>{fmt(r.frente)}</TableCell>
                    <TableCell>{fmt(r.bodega)}</TableCell>
                    <TableCell>{money(r.costo)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          {filtered.length > 500 && <p className="text-xs text-slate-400 mt-2">Mostrando 500 de {filtered.length} registros.</p>}
          {filtered.length === 0 && <p className="text-center text-slate-400 py-8 text-sm">Sin registros.</p>}
        </Card>
      ) : (
        <Card className="p-4">
          <div className="overflow-auto max-h-[60vh] rounded-lg border">
            <Table>
              <TableHeader className="sticky top-0 bg-slate-50 z-10">
                <TableRow>
                  {["Fecha", "Hora", "Sem", "Tienda", "Archivo", "Resultado", "Observaciones", "Usuario"].map((h) => (
                    <TableHead key={h} className="text-xs">{h}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((l) => (
                  <TableRow key={l.id} className="text-xs" data-testid="log-row">
                    <TableCell className="whitespace-nowrap">{l.fecha}</TableCell>
                    <TableCell className="whitespace-nowrap">{l.hora}</TableCell>
                    <TableCell>{l.semana}</TableCell>
                    <TableCell className="font-medium whitespace-nowrap">{l.tienda}</TableCell>
                    <TableCell className="max-w-[180px] truncate">{l.archivo}</TableCell>
                    <TableCell><span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${RESULT_COLOR(l.resultado)}`}>{l.resultado}</span></TableCell>
                    <TableCell className="max-w-[280px] text-slate-500">{l.observaciones}</TableCell>
                    <TableCell className="whitespace-nowrap text-slate-500">{l.usuario}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          {logs.length === 0 && <p className="text-center text-slate-400 py-8 text-sm">Sin importaciones registradas.</p>}
        </Card>
      )}
    </div>
  );
}
