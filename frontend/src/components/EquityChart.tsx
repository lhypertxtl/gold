import { EquityPoint } from '../api/client';

export function EquityChart({ points }: { points: EquityPoint[] }) {
  if (!points || points.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6 text-center text-sm text-slate-400">
        No hay operaciones cerradas en el filtro actual para graficar la curva de evolución.
      </div>
    );
  }

  // Añadir origen en 0 para visualizar la evolución desde el inicio
  const series = [
    {
      label: 'Inicio',
      cumPips: 0,
      cumPct: 0,
      deltaPips: 0,
    },
    ...points.map((p) => ({
      label: p.date,
      cumPips: p.cumulative_pips,
      cumPct: p.cumulative_percent,
      deltaPips: p.pips,
    })),
  ];

  const values = series.map((s) => s.cumPips);
  const minVal = Math.min(0, ...values);
  const maxVal = Math.max(0, ...values);
  const range = Math.max(20, maxVal - minVal);

  const width = 800;
  const height = 210;
  const padX = 48;
  const padY = 24;
  const innerW = width - padX * 2;
  const innerH = height - padY * 2;

  const getX = (idx: number) =>
    series.length === 1 ? padX + innerW / 2 : padX + (idx / (series.length - 1)) * innerW;
  const getY = (val: number) => padY + innerH - ((val - minVal) / range) * innerH;

  const zeroY = getY(0);
  const polylinePoints = series.map((s, idx) => `${getX(idx)},${getY(s.cumPips)}`).join(' ');
  const areaPoints = `${getX(0)},${zeroY} ${polylinePoints} ${getX(series.length - 1)},${zeroY}`;
  const lastVal = series[series.length - 1].cumPips;
  const strokeColor = lastVal >= 0 ? '#fbbf24' : '#f43f5e';

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <h2 className="text-sm font-semibold text-white uppercase tracking-wider">
            Curva de Evolución Hipotética Acumulada (Pips)
          </h2>
          <p className="text-xs text-slate-400">
            Secuencia cronológica de señales cerradas (Ganadas vs Perdidas) según precio posterior real
          </p>
        </div>
        <div className="text-right">
          <span className="text-xs text-slate-400 mr-2">Balance acumulado:</span>
          <span
            className={`text-sm font-bold px-2.5 py-1 rounded-md ${
              lastVal >= 0
                ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                : 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
            }`}
          >
            {lastVal >= 0 ? `+${lastVal}` : lastVal} pips
          </span>
        </div>
      </div>

      <div className="w-full overflow-x-auto">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-52 overflow-visible">
          <defs>
            <linearGradient id="goldAreaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={strokeColor} stopOpacity="0.32" />
              <stop offset="100%" stopColor={strokeColor} stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Línea base 0 pips */}
          <line
            x1={padX}
            y1={zeroY}
            x2={width - padX}
            y2={zeroY}
            stroke="#334155"
            strokeDasharray="4 4"
            strokeWidth="1"
          />
          <text x={8} y={zeroY + 4} fill="#94a3b8" fontSize="11">
            0p
          </text>
          <text x={8} y={padY + 4} fill="#94a3b8" fontSize="11">
            +{Math.round(maxVal)}p
          </text>
          {minVal < 0 && (
            <text x={8} y={height - padY} fill="#94a3b8" fontSize="11">
              {Math.round(minVal)}p
            </text>
          )}

          {/* Área bajo la curva */}
          <polygon points={areaPoints} fill="url(#goldAreaGrad)" />

          {/* Línea de evolución */}
          <polyline
            fill="none"
            stroke={strokeColor}
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={polylinePoints}
          />

          {/* Puntos interactivos */}
          {series.map((s, idx) => {
            const cx = getX(idx);
            const cy = getY(s.cumPips);
            return (
              <g key={idx}>
                <circle
                  cx={cx}
                  cy={cy}
                  r={4.5}
                  fill={s.deltaPips >= 0 ? '#10b981' : '#f43f5e'}
                  stroke="#0f172a"
                  strokeWidth="1.5"
                >
                  <title>{`${s.label}: ${s.cumPips >= 0 ? '+' : ''}${s.cumPips} pips (${s.cumPct}%)`}</title>
                </circle>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
