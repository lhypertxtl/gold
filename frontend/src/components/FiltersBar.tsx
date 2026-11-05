import { Filter, RotateCcw } from 'lucide-react';
import { SignalFilters } from '../api/client';

interface FiltersBarProps {
  filters: SignalFilters;
  channels: string[];
  hasDemoData: boolean;
  hasRealData: boolean;
  onChange: (next: SignalFilters) => void;
  onReset: () => void;
}

export function FiltersBar({
  filters,
  channels,
  hasDemoData,
  hasRealData,
  onChange,
  onReset,
}: FiltersBarProps) {
  const update = (patch: Partial<SignalFilters>) => {
    onChange({ ...filters, ...patch });
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 mb-6">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-300">
          <Filter className="w-3.5 h-3.5 text-amber-400" />
          <span>Filtros de Operaciones</span>
        </div>
        <button
          onClick={onReset}
          className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-amber-300 transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Limpiar filtros</span>
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
        {/* Canal */}
        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Canal de Telegram</label>
          <select
            value={filters.channel}
            onChange={(e) => update({ channel: e.target.value })}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
          >
            <option value="ALL">Todos los canales</option>
            {channels.map((ch) => (
              <option key={ch} value={ch}>
                @{ch}
              </option>
            ))}
          </select>
        </div>

        {/* Estado */}
        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Estado de Evaluación</label>
          <select
            value={filters.status}
            onChange={(e) => update({ status: e.target.value })}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
          >
            <option value="ALL">Todos los estados</option>
            <option value="GANADA">Ganada (TP alcanzado)</option>
            <option value="PERDIDA">Perdida (SL tocado)</option>
            <option value="PENDIENTE">Pendiente / En curso</option>
            <option value="EXPIRADA">Expirada</option>
            <option value="SIN_INTERPRETAR">Sin interpretar</option>
            <option value="NO_DISPONIBLE">Precio no disponible</option>
          </select>
        </div>

        {/* Instrumento */}
        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Instrumento</label>
          <select
            value={filters.instrument}
            onChange={(e) => update({ instrument: e.target.value })}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
          >
            <option value="ALL">Todos (XAUUSD + GC)</option>
            <option value="XAUUSD">XAUUSD (Oro Spot)</option>
            <option value="GC">GC (Futuros de Oro)</option>
          </select>
        </div>

        {/* Origen de datos (Real vs Ejemplo) */}
        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Origen de Datos</label>
          <select
            value={filters.data_mode}
            onChange={(e) => update({ data_mode: e.target.value as SignalFilters['data_mode'] })}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
          >
            <option value="all">
              Todos ({hasRealData ? 'Reales' : ''}{hasRealData && hasDemoData ? ' + ' : ''}{hasDemoData ? 'Ejemplo' : ''})
            </option>
            <option value="real">Solo Señales Reales (Telegram)</option>
            <option value="demo">Solo Datos de Ejemplo [DEMO]</option>
          </select>
        </div>

        {/* Fecha Desde */}
        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Desde Fecha</label>
          <input
            type="date"
            value={filters.date_from}
            onChange={(e) => update({ date_from: e.target.value })}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
          />
        </div>

        {/* Fecha Hasta */}
        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Hasta Fecha</label>
          <input
            type="date"
            value={filters.date_to}
            onChange={(e) => update({ date_to: e.target.value })}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
          />
        </div>
      </div>
    </div>
  );
}
