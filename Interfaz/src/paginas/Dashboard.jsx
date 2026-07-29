import { useEffect, useState } from "react";
import { api, fmt, money } from "../lib/sar";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Store, AlertTriangle, TrendingDown, TrendingUp, Trophy, Boxes, Loader2 } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, LineChart, Line, Legend } from "recharts";

const BAR_CHART_HEIGHT = 280;
const LINE_CHART_HEIGHT = 260;
const AXIS_TICK = { fontSize: 11 };
const AXIS_TICK_SM = { fontSize: 10 };
const BAR_CHART_MARGIN = { left: 20 };
const BAR_RADIUS = [0, 4, 4, 0];

function Kpi({ icon: Icon, label, value, sub, accent }) {
  return (
    <Card className="p-4 sar-fade" data-testid={`kpi-${label}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</span>
        <Icon className={`h-4 w-4 ${accent}`} />
      </div>
      <div className="mt-2 font-display text-2xl font-bold text-slate-900">{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-0.5">{sub}</div>}
    </Card>
  );
}

export default function Dashboard({ semanas }) {
  const [sel, setSel] = useState("");
  const [data, setData] = useState(null);
  const [comp, setComp] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (semanas.length && !sel) setSel(`${semanas[0].semana}|${semanas[0].anio}`);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [semanas]);

  useEffect(() => {
    if (!sel) return;
    const [semana, anio] = sel.split("|");
    setLoading(true);
    Promise.all([
      api.get(`/dashboard?semana=${semana}&anio=${anio}`),
      api.get(`/comparativo?anio=${anio}&tipo=semana`),
    ]).then(([d, c]) => { setData(d.data); setComp(c.data); }).finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sel]);

  if (!semanas.length) {
    return <Empty msg="Aún no hay datos importados. Ve a la sección Importar para comenzar." />;
  }

  return (
    <div className="sar-fade space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-display text-3xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-slate-500 text-sm mt-1">Indicadores de auditoría y recuperación</p>
        </div>
        <Select value={sel} onValueChange={setSel}>
          <SelectTrigger className="w-56 bg-white" data-testid="semana-select"><SelectValue placeholder="Selecciona semana" /></SelectTrigger>
          <SelectContent>
            {semanas?.map((s) => (
              <SelectItem key={`${s.semana}|${s.anio}`} value={`${s.semana}|${s.anio}`}>
                Semana {s.semana} · {s.anio} ({s.num_tiendas} tiendas)
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {loading || !data ? <Loading /> : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <Kpi icon={Store} label="Tiendas recibidas" value={`${data.tiendas_recibidas}/17`} sub={`${data.tiendas_pendientes} pendientes`} accent="text-emerald-500" />
            <Kpi icon={AlertTriangle} label="Con diferencias" value={data.tiendas_con_errores} sub={data.lista_con_errores.join(", ") || "Ninguna"} accent="text-amber-500" />
            <Kpi icon={TrendingDown} label="% Negado" value={`${data.pct_negado}%`} sub={`${fmt(data.total_negado)} tallas negadas`} accent="text-red-500" />
            <Kpi icon={TrendingUp} label="% Recuperado" value={`${data.pct_recuperado}%`} sub={`${fmt(data.total_recuperado)} recuperadas`} accent="text-emerald-500" />
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
            <Kpi icon={Boxes} label="Tallas auditadas" value={fmt(data.total_auditados)} accent="text-slate-400" />
            <Kpi icon={TrendingDown} label="Costo de oportunidad" value={money(data.total_costo)} accent="text-amber-500" />
            <Kpi icon={Store} label="Catálogos evaluados" value={data?.por_catalogo?.length|| accent="text-slate-400" />
          </div>

          <div className="grid lg:grid-cols-2 gap-4">
            <Card className="p-5">
              <h3 className="font-semibold text-slate-800 mb-1 flex items-center gap-2"><Trophy className="h-4 w-4 text-amber-500" /> Ranking de tiendas (% recuperado)</h3>
              <div className="mt-3 space-y-1.5 max-h-72 overflow-auto" data-testid="ranking-tiendas">
                {(data?.ranking_tiendas||[]).map((t, i) => (
                  <div key={t.tienda} className="flex items-center gap-3 text-sm py-1.5 border-b border-slate-50">
                    <span className="w-6 text-center font-bold text-slate-300">{i + 1}</span>
                    <span className="flex-1 truncate text-slate-700">{t.tienda}</span>
                    <Badge variant="outline" className="text-xs">neg {t.pct_negado}%</Badge>
                    <span className="font-semibold text-emerald-600 w-14 text-right">{t.pct_recuperado}%</span>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="p-5">
              <h3 className="font-semibold text-slate-800 mb-3">Resultados por catálogo</h3>
              <ResponsiveContainer width="100%" height={BAR_CHART_HEIGHT}>
                <BarChart data={data.por_catalogo.slice(0, 10)} layout="vertical" margin={BAR_CHART_MARGIN}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#eef2f7" />
                  <XAxis type="number" tick={AXIS_TICK} />
                  <YAxis type="category" dataKey="catalogo" width={90} tick={AXIS_TICK_SM} />
                  <Tooltip />
                  <Bar dataKey="negado" fill="#f5a524" radius={BAR_RADIUS} name="Negado" />
                  <Bar dataKey="recuperado" fill="#10b981" radius={BAR_RADIUS} name="Recuperado" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </div>

          <div className="grid lg:grid-cols-2 gap-4">
            <Card className="p-5">
              <h3 className="font-semibold text-slate-800 mb-1 flex items-center gap-2"><Trophy className="h-4 w-4 text-amber-500" /> Ranking de responsables</h3>
              <div className="mt-3 space-y-1.5 max-h-64 overflow-auto" data-testid="ranking-responsables">
                {data.ranking_responsables?.map((t, i) => (
                  <div key={t.responsable} className="flex items-center gap-3 text-sm py-1.5 border-b border-slate-50">
                    <span className="w-6 text-center font-bold text-slate-300">{i + 1}</span>
                    <span className="flex-1 truncate text-slate-700">{t.responsable}</span>
                    <span className="text-xs text-slate-400">neg {fmt(t.negado)}</span>
                    <span className="font-semibold text-emerald-600 w-14 text-right">{t.pct_recuperado}%</span>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="p-5">
              <h3 className="font-semibold text-slate-800 mb-3">Comparativo por semana ({sel.split("|")[1]})</h3>
              <ResponsiveContainer width="100%" height={LINE_CHART_HEIGHT}>
                <LineChart data={comp}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" />
                  <XAxis dataKey="periodo" tick={AXIS_TICK} />
                  <YAxis tick={AXIS_TICK} />
                  <Tooltip /><Legend />
                  <Line type="monotone" dataKey="pct_negado" stroke="#ef4444" name="% Negado" strokeWidth={2} />
                  <Line type="monotone" dataKey="pct_recuperado" stroke="#10b981" name="% Recuperado" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

const Loading = () => <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-amber-500" /></div>;
const Empty = ({ msg }) => (
  <div className="sar-fade text-center py-24 text-slate-400">
    <Boxes className="h-12 w-12 mx-auto mb-3 opacity-40" />
    <p>{msg}</p>
  </div>
);
