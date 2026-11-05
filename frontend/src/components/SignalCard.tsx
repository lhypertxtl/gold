import { Link } from 'react-router-dom';
import {
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  ChevronRight,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Hourglass,
  FileText,
} from 'lucide-react';
import { SignalItem } from '../api/client';

export function SignalCard({ signal }: { signal: SignalItem }) {
  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleString('es-ES', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return iso;
    }
  };

  const formatDuration = (mins: number | null) => {
    if (mins === null || mins === undefined) return 'No disponible';
    if (mins < 60) return `${mins} min`;
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    return m > 0 ? `${h}h ${m}m` : `${h}h`;
  };

  const statusBadge = () => {
    switch (signal.status) {
      case 'GANADA':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Ganada {signal.highest_tp_hit ? `(${signal.highest_tp_hit})` : ''}
          </span>
        );
      case 'PERDIDA':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-300 border border-rose-500/30">
            <XCircle className="w-3.5 h-3.5" />
            Perdida (SL)
          </span>
        );
      case 'PENDIENTE':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
            <Hourglass className="w-3.5 h-3.5" />
            Pendiente
          </span>
        );
      case 'EXPIRADA':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
            <Clock className="w-3.5 h-3.5" />
            Expirada
          </span>
        );
      case 'NO_DISPONIBLE':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
            <AlertCircle className="w-3.5 h-3.5" />
            Precio no disponible
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800/80 text-slate-400 border border-slate-700">
            <FileText className="w-3.5 h-3.5" />
            Sin interpretar
          </span>
        );
    }
  };

  const tps = [
    signal.tp1 ? { label: 'TP1', val: signal.tp1 } : null,
    signal.tp2 ? { label: 'TP2', val: signal.tp2 } : null,
    signal.tp3 ? { label: 'TP3', val: signal.tp3 } : null,
    signal.tp4 ? { label: 'TP4', val: signal.tp4 } : null,
  ].filter(Boolean) as Array<{ label: string; val: number }>;

  return (
    <div className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl p-5 transition-all shadow-sm">
      {/* Encabezado de tarjeta */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
        <div className="flex flex-wrap items-center gap-2">
          {signal.is_demo && (
            <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wide bg-purple-500/20 text-purple-300 border border-purple-500/40">
              🧪 Ejemplo
            </span>
          )}
          <span className="text-xs font-semibold text-amber-300 bg-amber-500/10 border border-amber-500/20 px-2.5 py-0.5 rounded-md">
            @{signal.channel_username}
          </span>
          <span className="text-xs text-slate-400">#{signal.telegram_message_id}</span>
          <span className="text-xs text-slate-400">· {formatDate(signal.published_at)}</span>
        </div>

        <div className="flex items-center gap-2">{statusBadge()}</div>
      </div>

      {/* Cuerpo: Si está parseada, mostrar niveles; si no, mostrar aviso y extracto del mensaje */}
      {signal.is_parsed ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-center">
          {/* Dirección e Instrumento */}
          <div className="lg:col-span-3 flex items-center gap-3">
            <div
              className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${
                signal.direction === 'COMPRA'
                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                  : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
              }`}
            >
              {signal.direction === 'COMPRA' ? (
                <ArrowUpRight className="w-6 h-6" />
              ) : (
                <ArrowDownRight className="w-6 h-6" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span
                  className={`text-sm font-bold ${
                    signal.direction === 'COMPRA' ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {signal.direction}
                </span>
                <span className="text-sm font-bold text-white">{signal.instrument || 'XAUUSD'}</span>
              </div>
              <div className="text-xs text-slate-400 mt-0.5">
                {signal.entry_range_low &&
                signal.entry_range_high &&
                signal.entry_range_low !== signal.entry_range_high
                  ? `Zona: ${signal.entry_range_low.toFixed(2)} – ${signal.entry_range_high.toFixed(2)}`
                  : `Precio fijo`}
              </div>
            </div>
          </div>

          {/* Entrada / Stop Loss / Take Profits */}
          <div className="lg:col-span-6 grid grid-cols-2 sm:grid-cols-3 gap-2.5 bg-slate-950/70 border border-slate-800/80 rounded-lg p-3">
            <div>
              <div className="text-[11px] uppercase text-slate-400">Entrada</div>
              <div className="text-sm font-semibold text-white">
                {signal.entry_price !== null ? `${signal.entry_price.toFixed(2)}` : 'No disponible'}
              </div>
            </div>

            <div>
              <div className="text-[11px] uppercase text-rose-400/90">Stop Loss</div>
              <div className="text-sm font-semibold text-rose-300">
                {signal.stop_loss !== null ? `${signal.stop_loss.toFixed(2)}` : 'No disponible'}
              </div>
            </div>

            <div className="col-span-2 sm:col-span-1">
              <div className="text-[11px] uppercase text-emerald-400/90">Take Profits</div>
              <div className="flex flex-wrap gap-1.5 mt-0.5">
                {tps.length > 0 ? (
                  tps.map((t) => (
                    <span
                      key={t.label}
                      className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                        signal.highest_tp_hit === t.label
                          ? 'bg-emerald-500 text-slate-950 font-bold'
                          : 'bg-slate-800 text-emerald-300'
                      }`}
                    >
                      {t.label}: {t.val.toFixed(2)}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-slate-500">No disponible</span>
                )}
              </div>
            </div>
          </div>

          {/* Resultado en Pips, % y Tiempo */}
          <div className="lg:col-span-3 flex sm:flex-row lg:flex-col items-start sm:items-center lg:items-end justify-between gap-2">
            <div className="lg:text-right">
              <div className="text-[11px] uppercase text-slate-400">Resultado Real</div>
              {signal.result_pips !== null && signal.result_percent !== null ? (
                <div className="flex items-baseline lg:justify-end gap-1.5">
                  <span
                    className={`text-base font-bold ${
                      signal.result_pips > 0
                        ? 'text-emerald-400'
                        : signal.result_pips < 0
                        ? 'text-rose-400'
                        : 'text-slate-300'
                    }`}
                  >
                    {signal.result_pips > 0 ? `+${signal.result_pips}` : signal.result_pips} pips
                  </span>
                  <span className="text-xs text-slate-400">
                    ({signal.result_percent > 0 ? `+${signal.result_percent}` : signal.result_percent}%)
                  </span>
                </div>
              ) : (
                <div className="text-xs text-slate-400">No disponible</div>
              )}
              <div className="text-[11px] text-slate-400 flex items-center lg:justify-end gap-1 mt-0.5">
                <Clock className="w-3 h-3" />
                <span>Tiempo: {formatDuration(signal.duration_minutes)}</span>
              </div>
            </div>

            <Link
              to={`/signals/${signal.id}`}
              className="inline-flex items-center gap-1 text-xs font-semibold text-amber-400 hover:text-amber-300 transition-colors mt-1"
            >
              <span>Ver detalle y mensaje</span>
              <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      ) : (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-950/60 border border-slate-800/80 rounded-lg p-3.5">
          <div>
            <div className="text-xs font-medium text-slate-300 mb-1">
              Mensaje guardado como <span className="text-amber-300">«Sin interpretar»</span> ({signal.parse_notes || 'Texto libre sin formato de señal'})
            </div>
            <p className="text-xs text-slate-400 line-clamp-2 whitespace-pre-line font-mono">
              {signal.raw_text}
            </p>
          </div>
          <Link
            to={`/signals/${signal.id}`}
            className="inline-flex items-center gap-1 text-xs font-semibold text-amber-400 hover:text-amber-300 shrink-0"
          >
            <span>Ver mensaje original</span>
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
      )}
    </div>
  );
}
