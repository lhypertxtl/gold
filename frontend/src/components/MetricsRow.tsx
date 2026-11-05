import { Trophy, TrendingUp, Clock, CheckCircle2, XCircle, HelpCircle } from 'lucide-react';
import { DashboardMetrics } from '../api/client';

export function MetricsRow({ metrics }: { metrics: DashboardMetrics }) {
  const formatDuration = (mins: number | null) => {
    if (mins === null || mins === undefined) return 'N/D';
    if (mins < 60) return `${mins} min`;
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    return m > 0 ? `${h}h ${m}m` : `${h}h`;
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* Tasa de Aciertos */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
        <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
          <span>TASA DE ACIERTO (WIN RATE)</span>
          <Trophy className="w-4 h-4 text-amber-400" />
        </div>
        <div className="text-2xl font-bold text-white">
          {metrics.win_rate_percent !== null ? `${metrics.win_rate_percent}%` : 'Sin cerradas'}
        </div>
        <div className="mt-2 flex items-center gap-3 text-xs">
          <span className="inline-flex items-center gap-1 text-emerald-400">
            <CheckCircle2 className="w-3.5 h-3.5" /> {metrics.won_count} ganadas
          </span>
          <span className="inline-flex items-center gap-1 text-rose-400">
            <XCircle className="w-3.5 h-3.5" /> {metrics.lost_count} perdidas
          </span>
        </div>
      </div>

      {/* Resultado Neto Acumulado (Pips y %) */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
        <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
          <span>GANANCIA ACUMULADA HIPOTÉTICA</span>
          <TrendingUp className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="flex items-baseline gap-2">
          <span
            className={`text-2xl font-bold ${
              metrics.total_pips > 0
                ? 'text-emerald-400'
                : metrics.total_pips < 0
                ? 'text-rose-400'
                : 'text-slate-200'
            }`}
          >
            {metrics.total_pips > 0 ? `+${metrics.total_pips}` : metrics.total_pips} pips
          </span>
          <span
            className={`text-sm font-semibold ${
              metrics.cumulative_percent >= 0 ? 'text-emerald-300' : 'text-rose-300'
            }`}
          >
            ({metrics.cumulative_percent >= 0 ? `+${metrics.cumulative_percent}` : metrics.cumulative_percent}%)
          </span>
        </div>
        <div className="mt-2 text-xs text-slate-400">
          Promedio: {metrics.avg_win_pips !== null ? `+${metrics.avg_win_pips}p` : 'N/D'} /{' '}
          {metrics.avg_loss_pips !== null ? `${metrics.avg_loss_pips}p` : 'N/D'}
        </div>
      </div>

      {/* Estado de Señales */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
        <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
          <span>SEÑALES INTERPRETADAS</span>
          <HelpCircle className="w-4 h-4 text-sky-400" />
        </div>
        <div className="text-2xl font-bold text-white">
          {metrics.parsed_signals}{' '}
          <span className="text-sm font-normal text-slate-400">/ {metrics.total_messages} msjs</span>
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-400">
          <span className="text-amber-300">{metrics.pending_count} pendientes</span>·
          <span>{metrics.expired_count} expiradas</span>·
          <span>{metrics.unparsed_messages} sin interpretar</span>
        </div>
      </div>

      {/* Tiempo promedio hasta objetivo o stop */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
        <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
          <span>TIEMPO MEDIO A TP / SL</span>
          <Clock className="w-4 h-4 text-purple-400" />
        </div>
        <div className="text-2xl font-bold text-white">
          {formatDuration(metrics.avg_duration_minutes)}
        </div>
        <div className="mt-2 text-xs text-slate-400">
          1 pip en XAUUSD = $0.10 USD de recorrido
        </div>
      </div>
    </div>
  );
}
