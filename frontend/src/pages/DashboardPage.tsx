import { useEffect, useState, useCallback } from 'react';
import { RefreshCw, Radio, FlaskConical } from 'lucide-react';
import {
  DashboardMetrics,
  SignalFilters,
  SignalItem,
  fetchMetrics,
  fetchSignals,
  fetchSyncStatus,
} from '../api/client';
import { MetricsRow } from '../components/MetricsRow';
import { EquityChart } from '../components/EquityChart';
import { FiltersBar } from '../components/FiltersBar';
import { SignalCard } from '../components/SignalCard';

const INITIAL_FILTERS: SignalFilters = {
  channel: 'ALL',
  status: 'ALL',
  instrument: 'ALL',
  direction: 'ALL',
  date_from: '',
  date_to: '',
  data_mode: 'all',
};

export function DashboardPage({
  onMetaChange,
}: {
  onMetaChange?: (meta: { hasDemo: boolean; hasReal: boolean }) => void;
}) {
  const [filters, setFilters] = useState<SignalFilters>(INITIAL_FILTERS);
  const [signals, setSignals] = useState<SignalItem[]>([]);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [syncInfo, setSyncInfo] = useState<{
    configured_channels: string[];
    channels: Array<{
      channel_username: string;
      last_message_id: number;
      last_sync_at: string | null;
      status_message: string | null;
    }>;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [sigList, met, sync] = await Promise.all([
        fetchSignals(filters),
        fetchMetrics(filters),
        fetchSyncStatus(),
      ]);
      setSignals(sigList);
      setMetrics(met);
      setSyncInfo(sync);
      if (onMetaChange) {
        onMetaChange({ hasDemo: met.has_demo_data, hasReal: met.has_real_data });
      }
    } catch (err: any) {
      setError(err?.message || 'Error cargando datos del tablero');
    } finally {
      setLoading(false);
    }
  }, [filters, onMetaChange]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return (
    <div>
      {/* Aviso explícito si hay datos de ejemplo visibles */}
      {metrics?.has_demo_data && filters.data_mode !== 'real' && (
        <div className="mb-6 bg-purple-500/10 border border-purple-500/30 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-start sm:items-center gap-3">
            <FlaskConical className="w-5 h-5 text-purple-300 shrink-0 mt-0.5 sm:mt-0" />
            <div className="text-xs text-purple-200">
              <strong>Modo Preview con Datos de Ejemplo:</strong> Las señales con la etiqueta{' '}
              <span className="px-1.5 py-0.5 rounded bg-purple-500/25 font-bold">🧪 Ejemplo</span> son datos de demostración para validar el diseño antes de conectar la sesión real de Telegram.
            </div>
          </div>
          {metrics.has_real_data && (
            <button
              onClick={() => setFilters((f) => ({ ...f, data_mode: 'real' }))}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-purple-500/20 hover:bg-purple-500/30 text-purple-200 border border-purple-500/40 shrink-0"
            >
              Ver solo señales reales
            </button>
          )}
        </div>
      )}

      {/* Estado de sincronización con Telegram */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
          <Radio className="w-4 h-4 text-emerald-400" />
          <span>Canales monitoreados:</span>
          {(syncInfo?.configured_channels || ['tagsignals']).map((ch) => (
            <span
              key={ch}
              className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-amber-300 font-medium"
            >
              @{ch}
            </span>
          ))}
          {syncInfo?.channels?.[0]?.status_message && (
            <span className="text-slate-500 hidden md:inline">
              · {syncInfo.channels[0].status_message}
            </span>
          )}
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-amber-400' : ''}`} />
          <span>Actualizar tablero</span>
        </button>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs rounded-xl p-4 mb-6">
          {error}
        </div>
      )}

      {/* Métricas de desempeño */}
      {metrics && <MetricsRow metrics={metrics} />}

      {/* Curva de evolución acumulada */}
      {metrics && <EquityChart points={metrics.equity_curve} />}

      {/* Barra de filtros */}
      <FiltersBar
        filters={filters}
        channels={metrics?.channels || ['tagsignals']}
        hasDemoData={Boolean(metrics?.has_demo_data)}
        hasRealData={Boolean(metrics?.has_real_data)}
        onChange={setFilters}
        onReset={() => setFilters(INITIAL_FILTERS)}
      />

      {/* Lista de tarjetas de operaciones */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-400 px-1">
          <span>
            Mostrando <strong className="text-white">{signals.length}</strong> registros
          </span>
          <span>Ordenado del más reciente al más antiguo</span>
        </div>

        {loading && signals.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-10 text-center text-sm text-slate-400">
            Cargando señales de oro...
          </div>
        ) : signals.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-10 text-center text-sm text-slate-400">
            No se encontraron señales para los filtros seleccionados.
          </div>
        ) : (
          signals.map((sig) => <SignalCard key={sig.id} signal={sig} />)
        )}
      </div>
    </div>
  );
}
