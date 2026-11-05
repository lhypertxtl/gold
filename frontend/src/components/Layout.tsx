import { ShieldAlert, Eye, LogOut, Coins } from 'lucide-react';
import { Link } from 'react-router-dom';

interface LayoutProps {
  username: string;
  onLogout: () => void;
  hasDemoData?: boolean;
  hasRealData?: boolean;
  children: React.ReactNode;
}

export function Layout({ username, onLogout, hasDemoData, hasRealData, children }: LayoutProps) {
  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      {/* Barra superior de advertencia modo solo lectura + no asesoría financiera */}
      <div className="bg-amber-500/10 border-b border-amber-500/30 px-4 py-2 text-xs text-amber-200 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            <strong>No es asesoría financiera.</strong> Registro estadístico e hipotético de señales públicas de oro (XAUUSD y futuros GC).
          </span>
        </div>
        <div className="flex items-center gap-2 text-emerald-300 font-medium">
          <Eye className="w-3.5 h-3.5" />
          <span>Modo Estrictamente Solo Lectura (sin envío de mensajes ni ejecución de órdenes)</span>
        </div>
      </div>

      {/* Navbar principal */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3.5 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center text-slate-950 shadow-lg shadow-amber-500/20">
              <Coins className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg tracking-tight text-white group-hover:text-amber-300 transition-colors">
                  Gold Signals
                </span>
                <span className="text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30">
                  XAUUSD · GC
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Auditoría en tiempo real de señales de Telegram (@tagsignals)
              </p>
            </div>
          </Link>

          <div className="flex items-center gap-3">
            {hasDemoData && !hasRealData && (
              <span className="hidden sm:inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-md bg-purple-500/15 text-purple-300 border border-purple-500/30">
                🧪 Vista Previa con Datos de Ejemplo
              </span>
            )}
            <div className="text-right hidden sm:block">
              <div className="text-xs text-slate-400">Sesión activa</div>
              <div className="text-xs font-medium text-slate-200">{username}</div>
            </div>
            <button
              onClick={onLogout}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
              title="Cerrar sesión"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Salir</span>
            </button>
          </div>
        </div>
      </header>

      {/* Contenido */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6">
        {children}
      </main>

      {/* Pie de página con descargo legal */}
      <footer className="border-t border-slate-800/80 bg-slate-900/40 py-4 px-4 sm:px-6 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>
            <strong>Gold Signals</strong> — Monitoreo pasivo de canales de Telegram.
          </span>
          <span className="text-amber-300/90 font-medium">
            No es asesoría financiera · Los resultados pasados o hipotéticos no garantizan rendimientos futuros.
          </span>
        </div>
      </footer>
    </div>
  );
}
