import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  RefreshCw,
  MessageSquare,
  CheckCircle2,
  XCircle,
  Clock,
  AlertCircle,
  TrendingUp,
} from 'lucide-react';
import { SignalItem, fetchSignalDetail, triggerEvaluateSignal } from '../api/client';

export function SignalDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [signal, setSignal] = useState<SignalItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    fetchSignalDetail(Number(id))
      .then(setSignal)
      .catch((err) => setError(err?.message || 'Error cargando señal'))
      .finally(() => setLoading(false));
  }, [id]);

  const handleReevaluate = async () => {
    if (!signal) return;
    setEvaluating(true);
    try {
      const updated = await triggerEvaluateSignal(signal.id);
      setSignal(updated);
    } catch (err: any) {
      setError(err?.message || 'Error al re-evaluar');
    } finally {
      setEvaluating(false);
    }
  };

  const formatDate = (iso: string | null) => {
    if (!iso) return 'No disponible';
    try {
      return new Date(iso).toLocaleString('es-ES', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return iso;
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-10 text-center text-sm text-slate-400">
        Cargando detalle de la señal...
      </div>
    );
  }

  if (error || !signal) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8">
        <p className="text-rose-400 text-sm mb-4">{error || 'Señal no encontrada'}</p>
        <Link to="/" className="text-xs text-amber-400 hover:underline">
          ← Volver al tablero
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Navegación superior */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-300 hover:text-amber-300 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Volver al tablero de operaciones</span>
        </Link>

        {!signal.is_demo && signal.is_parsed && (
          <button
            onClick={handleReevaluate}
            disabled={evaluating}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 border border-amber-500/30 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${evaluating ? 'animate-spin' : ''}`} />
            <span>{evaluating ? 'Evaluando precio real...' : 'Re-evaluar contra precio actual'}</span>
          </button>
        )}
      </div>

      {/* Encabezado principal */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div className="flex flex-wrap items-center gap-2">
            {signal.is_demo && (
              <span className="px-2.5 py-0.5 rounded text-xs font-bold uppercase bg-purple-500/20 text-purple-300 border border-purple-500/40">
                🧪 Dato de Ejemplo (Preview)
              </span>
            )}
            <span className="text-sm font-bold text-amber-300 bg-amber-500/10 border border-amber-500/20 px-3 py-1 rounded-md">
              @{signal.channel_username}
            </span>
            <span className="text-xs text-slate-400">
              Mensaje Telegram #{signal.telegram_message_id}
            </span>
          </div>

          <span
            className={`px-3 py-1 rounded-full text-xs font-bold border ${
              signal.status === 'GANADA'
                ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                : signal.status === 'PERDIDA'
                ? 'bg-rose-500/15 text-rose-300 border-rose-500/30'
                : signal.status === 'PENDIENTE'
                ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                : 'bg-slate-800 text-slate-300 border-slate-700'
            }`}
          >
            Estado: {signal.status} {signal.highest_tp_hit ? `(${signal.highest_tp_hit})` : ''}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-4 border-t border-slate-800 text-xs">
          <div>
            <span className="text-slate-400 block mb-0.5">Fecha de publicación</span>
            <strong className="text-slate-100">{formatDate(signal.published_at)}</strong>
          </div>
          <div>
            <span className="text-slate-400 block mb-0.5">Instrumento / Dirección</span>
            <strong className="text-slate-100">
              {signal.is_parsed
                ? `${signal.instrument || 'XAUUSD'} · ${signal.direction}`
                : 'Sin interpretar'}
            </strong>
          </div>
          <div>
            <span className="text-slate-400 block mb-0.5">Fuente de precios</span>
            <strong className="text-slate-100">{signal.price_source || 'No disponible'}</strong>
          </div>
          <div>
            <span className="text-slate-400 block mb-0.5">Última evaluación</span>
            <strong className="text-slate-100">{formatDate(signal.evaluated_at)}</strong>
          </div>
        </div>
      </div>

      {/* Dos columnas: Parámetros extraídos y Mensaje Original Íntegro */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Parámetros y Evaluación */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-5">
          <h2 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-amber-400" />
            <span>Parámetros Operativos y Resultado</span>
          </h2>

          {signal.is_parsed ? (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <div className="bg-slate-950 border border-slate-800 rounded-lg p-3">
                  <div className="text-[11px] text-slate-400 uppercase">Precio Entrada</div>
                  <div className="text-base font-bold text-white mt-0.5">
                    {signal.entry_price !== null ? `${signal.entry_price.toFixed(2)}` : 'N/D'}
                  </div>
                  {signal.entry_range_low !== signal.entry_range_high && (
                    <div className="text-[11px] text-slate-400">
                      Rango: {signal.entry_range_low?.toFixed(2)} - {signal.entry_range_high?.toFixed(2)}
                    </div>
                  )}
                </div>

                <div className="bg-slate-950 border border-rose-500/20 rounded-lg p-3">
                  <div className="text-[11px] text-rose-400 uppercase">Stop Loss (SL)</div>
                  <div className="text-base font-bold text-rose-300 mt-0.5">
                    {signal.stop_loss !== null ? `${signal.stop_loss.toFixed(2)}` : 'N/D'}
                  </div>
                </div>

                <div className="bg-slate-950 border border-slate-800 rounded-lg p-3">
                  <div className="text-[11px] text-slate-400 uppercase">Precio Salida / Ref</div>
                  <div className="text-base font-bold text-amber-300 mt-0.5">
                    {signal.exit_price !== null ? `${signal.exit_price.toFixed(2)}` : 'No disponible'}
                  </div>
                </div>
              </div>

              {/* Niveles de Take Profit */}
              <div>
                <div className="text-xs font-medium text-slate-400 mb-2">
                  Objetivos de Ganancia (Take Profits)
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                  {[
                    { label: 'TP1', val: signal.tp1 },
                    { label: 'TP2', val: signal.tp2 },
                    { label: 'TP3', val: signal.tp3 },
                    { label: 'TP4', val: signal.tp4 },
                  ].map((tp) => (
                    <div
                      key={tp.label}
                      className={`rounded-lg p-2.5 border text-center ${
                        signal.highest_tp_hit === tp.label
                          ? 'bg-emerald-500/20 border-emerald-500 text-emerald-200'
                          : 'bg-slate-950 border-slate-800 text-slate-300'
                      }`}
                    >
                      <div className="text-[11px] uppercase text-slate-400">{tp.label}</div>
                      <div className="text-sm font-bold mt-0.5">
                        {tp.val !== null ? tp.val.toFixed(2) : '—'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Desempeño cuantitativo */}
              <div className="grid grid-cols-3 gap-3 pt-3 border-t border-slate-800">
                <div>
                  <div className="text-[11px] text-slate-400 uppercase">Resultado (Pips)</div>
                  <div
                    className={`text-lg font-bold ${
                      (signal.result_pips || 0) > 0
                        ? 'text-emerald-400'
                        : (signal.result_pips || 0) < 0
                        ? 'text-rose-400'
                        : 'text-slate-200'
                    }`}
                  >
                    {signal.result_pips !== null
                      ? `${signal.result_pips > 0 ? '+' : ''}${signal.result_pips} pips`
                      : 'No disponible'}
                  </div>
                </div>

                <div>
                  <div className="text-[11px] text-slate-400 uppercase">Variación (%)</div>
                  <div className="text-lg font-bold text-slate-100">
                    {signal.result_percent !== null
                      ? `${signal.result_percent > 0 ? '+' : ''}${signal.result_percent}%`
                      : 'No disponible'}
                  </div>
                </div>

                <div>
                  <div className="text-[11px] text-slate-400 uppercase">Tiempo a TP/SL</div>
                  <div className="text-lg font-bold text-slate-100">
                    {signal.duration_minutes !== null ? `${signal.duration_minutes} min` : 'No disponible'}
                  </div>
                </div>
              </div>

              {signal.evaluation_notes && (
                <div className="bg-slate-950/90 border border-slate-800 rounded-lg p-3 text-xs text-slate-300">
                  <strong>Nota del evaluador:</strong> {signal.evaluation_notes}
                </div>
              )}
            </>
          ) : (
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 text-xs text-slate-300 space-y-2">
              <div className="flex items-center gap-2 text-amber-300 font-semibold">
                <AlertCircle className="w-4 h-4" />
                <span>Mensaje guardado como «Sin interpretar»</span>
              </div>
              <p className="text-slate-400">
                Motivo: {signal.parse_notes || 'El texto no contiene niveles completos de entrada, SL y TP.'}
              </p>
              <p className="text-slate-500">
                Por política de integridad de datos, el sistema nunca inventa precios ni parámetros faltantes.
              </p>
            </div>
          )}
        </div>

        {/* Mensaje Original de Telegram */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col">
          <h2 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2 mb-4">
            <MessageSquare className="w-4 h-4 text-amber-400" />
            <span>Mensaje Original Publicado en Telegram</span>
          </h2>

          <div className="flex-1 bg-slate-950 border border-slate-800 rounded-xl p-4 font-mono text-xs sm:text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">
            {signal.raw_text}
          </div>

          <div className="mt-4 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Canal: @{signal.channel_username}</span>
            <span>Modo Solo Lectura · Texto íntegro sin modificar</span>
          </div>
        </div>
      </div>
    </div>
  );
}
