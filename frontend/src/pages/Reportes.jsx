import { useState } from "react";
import { API, MESES, descargar } from "../lib/sar";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { FileDown, CalendarDays, CalendarRange, CalendarClock } from "lucide-react";

function ReportCard({ icon: Icon, title, desc, children }) {
  return (
    <Card className="p-6 sar-fade flex flex-col">
      <div className="h-11 w-11 rounded-xl bg-amber-100 flex items-center justify-center mb-4">
        <Icon className="h-5 w-5 text-amber-600" />
      </div>
      <h3 className="font-display font-bold text-lg text-slate-900">{title}</h3>
      <p className="text-sm text-slate-500 mt-1 mb-4 flex-1">{desc}</p>
      {children}
    </Card>
  );
}

export default function Reportes({ semanas }) {
  const anios = [...new Set(semanas.map((s) => s.anio).filter(Boolean))].sort((a, b) => b - a);
  const meses = [...new Set(semanas.map((s) => s.mes).filter(Boolean))].sort((a, b) => a - b);

  const [semSel, setSemSel] = useState("");
  const [mesSel, setMesSel] = useState("");
  const [anioSel, setAnioSel] = useState(anios[0] ? String(anios[0]) : "");

  const bajar = (url, name) => {
    toast.info("Generando reporte…");
    descargar(url, name);
  };

  return (
    <div className="sar-fade space-y-6">
      <div>
        <h1 className="font-display text-3xl font-bold text-slate-900">Concentrados</h1>
        <p className="text-slate-500 text-sm mt-1">Genera y descarga los concentrados en formato Excel idéntico al de la Gerencia de Mejoras (plantilla MACHOTE).</p>
      </div>

      {!semanas.length ? (
        <Card className="p-10 text-center text-slate-400">Importa auditorías primero para poder generar concentrados.</Card>
      ) : (
        <div className="grid md:grid-cols-3 gap-5">
          <ReportCard icon={CalendarDays} title="Concentrado Semanal" desc="Consolida las 17 tiendas de una semana en el formato MACHOTE.">
            <div className="flex gap-2">
              <Select value={semSel} onValueChange={setSemSel}>
                <SelectTrigger data-testid="rep-semana-select"><SelectValue placeholder="Semana" /></SelectTrigger>
                <SelectContent>
                  {semanas.map((s) => (
                    <SelectItem key={`${s.semana}|${s.anio}`} value={`${s.semana}|${s.anio}`}>Semana {s.semana} · {s.anio}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button data-testid="dl-semanal" disabled={!semSel} className="bg-slate-900 hover:bg-slate-700 shrink-0"
                onClick={() => { const [s, a] = semSel.split("|"); bajar(`${API}/reporte/semanal?semana=${s}&anio=${a}`, `Concentrado_Semanal_${s}.xlsx`); }}>
                <FileDown className="h-4 w-4" />
              </Button>
            </div>
          </ReportCard>

          <ReportCard icon={CalendarRange} title="Concentrado Mensual" desc="Suma todas las semanas del mes desde la Base Histórica.">
            <div className="flex gap-2">
              <Select value={mesSel} onValueChange={setMesSel}>
                <SelectTrigger data-testid="rep-mes-select"><SelectValue placeholder="Mes" /></SelectTrigger>
                <SelectContent>
                  {meses.map((m) => (<SelectItem key={m} value={String(m)}>{MESES[m]}</SelectItem>))}
                </SelectContent>
              </Select>
              <Button data-testid="dl-mensual" disabled={!mesSel} className="bg-slate-900 hover:bg-slate-700 shrink-0"
                onClick={() => bajar(`${API}/reporte/mensual?mes=${mesSel}${anioSel ? `&anio=${anioSel}` : ""}`, `Concentrado_Mensual_${MESES[mesSel]}.xlsx`)}>
                <FileDown className="h-4 w-4" />
              </Button>
            </div>
          </ReportCard>

          <ReportCard icon={CalendarClock} title="Concentrado Anual" desc="Acumulado anual completo tomado de la Base Histórica.">
            <div className="flex gap-2">
              <Select value={anioSel} onValueChange={setAnioSel}>
                <SelectTrigger data-testid="rep-anio-select"><SelectValue placeholder="Año" /></SelectTrigger>
                <SelectContent>
                  {anios.map((a) => (<SelectItem key={a} value={String(a)}>{a}</SelectItem>))}
                </SelectContent>
              </Select>
              <Button data-testid="dl-anual" disabled={!anioSel} className="bg-slate-900 hover:bg-slate-700 shrink-0"
                onClick={() => bajar(`${API}/reporte/anual?anio=${anioSel}`, `Concentrado_Anual_${anioSel}.xlsx`)}>
                <FileDown className="h-4 w-4" />
              </Button>
            </div>
          </ReportCard>
        </div>
      )}
    </div>
  );
}
