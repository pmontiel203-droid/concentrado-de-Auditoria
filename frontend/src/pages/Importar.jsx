import { useState, useCallback } from "react";
import { api } from "../lib/sar";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { UploadCloud, FileSpreadsheet, CheckCircle2, XCircle, AlertTriangle, Loader2, Trash2 } from "lucide-react";

const RESULT_STYLES = {
  "IMPORTADO": { icon: CheckCircle2, cls: "text-emerald-600 bg-emerald-50 border-emerald-200" },
  "IMPORTADO (FORZADO)": { icon: CheckCircle2, cls: "text-emerald-600 bg-emerald-50 border-emerald-200" },
  "CON DIFERENCIAS": { icon: AlertTriangle, cls: "text-amber-600 bg-amber-50 border-amber-200" },
  "OMITIDO": { icon: XCircle, cls: "text-slate-500 bg-slate-50 border-slate-200" },
  "ERROR": { icon: XCircle, cls: "text-red-600 bg-red-50 border-red-200" },
};

export default function Importar({ onImported }) {
  const [files, setFiles] = useState([]);
  const [forzar, setForzar] = useState(false);
  const [loading, setLoading] = useState(false);
  const [resultados, setResultados] = useState([]);
  const [drag, setDrag] = useState(false);

  const addFiles = useCallback((list) => {
    const arr = Array.from(list).filter((f) => f.name.match(/\.xlsx?$/i));
    setFiles((prev) => {
      const names = new Set(prev.map((f) => f.name));
      return [...prev, ...arr.filter((f) => !names.has(f.name))];
    });
  }, []);
  const onDrop = (e) => {
    e.preventDefault(); setDrag(false);
    addFiles(e.dataTransfer.files);
  };

  const procesar = async () => {
    if (!files.length) return;
    setLoading(true);
    const fd = new FormData();
    files.forEach((f) => fd.append("files", f));
    fd.append("forzar", forzar);
    try {
      const { data } = await api.post("/import", fd, { headers: { "Content-Type": "multipart/form-data" } });
      setResultados(data.resultados);
      const ok = data.resultados.filter((r) => r.resultado.startsWith("IMPORTADO")).length;
      toast.success(`${ok} de ${data.resultados.length} archivos importados`);
      onImported && onImported();
    } catch (e) {
      toast.error("Error al procesar los archivos");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sar-fade space-y-6">
      <div>
        <h1 className="font-display text-3xl font-bold text-slate-900">Importar auditorías</h1>
        <p className="text-slate-500 mt-1 text-sm">Sube los archivos Excel de las 17 tiendas de la semana. El sistema detecta las hojas <b>Conc Dictámenes</b> y <b>Exhibiciones</b>, valida y consolida automáticamente.</p>
      </div>

      <div
        data-testid="dropzone"
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={onDrop}
        className={`rounded-2xl border-2 border-dashed p-10 text-center transition-colors ${drag ? "border-amber-400 bg-amber-50" : "border-slate-300 bg-white"}`}
      >
        <UploadCloud className="mx-auto h-12 w-12 text-amber-500" />
        <p className="mt-3 font-medium text-slate-700">Arrastra tus archivos .xlsx aquí</p>
        <p className="text-sm text-slate-400">o</p>
        <label className="inline-block mt-2">
          <input data-testid="file-input" type="file" multiple accept=".xlsx,.xls" className="hidden"
            onChange={(e) => addFiles(e.target.files)} />
          <span className="cursor-pointer inline-flex items-center gap-2 rounded-lg bg-slate-900 text-white px-4 py-2 text-sm font-medium hover:bg-slate-700 transition-colors">
            Seleccionar archivos
          </span>
        </label>
      </div>

      {files.length > 0 && (
        <Card className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-slate-800">{files.length} archivo(s) seleccionado(s)</h3>
            <Button variant="ghost" size="sm" onClick={() => setFiles([])} data-testid="clear-files">
              <Trash2 className="h-4 w-4 mr-1" /> Limpiar
            </Button>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2 max-h-52 overflow-auto">
            {files.map((f) => (
              <div key={f.name} className="flex items-center gap-2 text-sm bg-slate-50 rounded-lg px-3 py-2 border border-slate-100">
                <FileSpreadsheet className="h-4 w-4 text-emerald-600 shrink-0" />
                <span className="truncate text-slate-600">{f.name}</span>
              </div>
            ))}
          </div>
          <div className="flex flex-wrap items-center justify-between gap-4 mt-4 pt-4 border-t">
            <label className="flex items-center gap-3 text-sm text-slate-600">
              <Switch checked={forzar} onCheckedChange={setForzar} data-testid="forzar-switch" />
              Forzar importación aunque existan diferencias en Exhibiciones
            </label>
            <Button onClick={procesar} disabled={loading} data-testid="procesar-btn"
              className="bg-amber-500 hover:bg-amber-600 text-slate-900 font-semibold">
              {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <UploadCloud className="h-4 w-4 mr-2" />}
              Procesar {files.length} archivo(s)
            </Button>
          </div>
        </Card>
      )}

      {resultados.length > 0 && (
        <div className="space-y-2" data-testid="resultados">
          <h3 className="font-semibold text-slate-800">Resultado del proceso</h3>
          {resultados.map((r, i) => {
            const st = RESULT_STYLES[r.resultado] || RESULT_STYLES.OMITIDO;
            const Icon = st.icon;
            return (
              <div key={`${r.archivo}-${i}`} className={`flex items-start gap-3 rounded-xl border p-3 ${st.cls}`} data-testid={`resultado-${i}`}>
                <Icon className="h-5 w-5 mt-0.5 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium truncate">{r.archivo}</span>
                    <Badge variant="outline" className="text-xs">{r.resultado}</Badge>
                    {r.tienda && <span className="text-xs opacity-70">{r.tienda} · Semana {r.semana}</span>}
                  </div>
                  <p className="text-xs opacity-80 mt-0.5">{r.observaciones}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
