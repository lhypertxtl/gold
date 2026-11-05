export interface SignalItem {
  id: number;
  channel_username: string;
  channel_title: string | null;
  telegram_message_id: number;
  published_at: string;
  raw_text: string;
  is_demo: boolean;
  is_parsed: boolean;
  parse_notes: string | null;
  direction: 'COMPRA' | 'VENTA' | null;
  instrument: 'XAUUSD' | 'GC' | null;
  entry_price: number | null;
  entry_range_low: number | null;
  entry_range_high: number | null;
  stop_loss: number | null;
  tp1: number | null;
  tp2: number | null;
  tp3: number | null;
  tp4: number | null;
  status: 'SIN_INTERPRETAR' | 'PENDIENTE' | 'GANADA' | 'PERDIDA' | 'EXPIRADA' | 'NO_DISPONIBLE';
  evaluated_at: string | null;
  price_source: string | null;
  entry_triggered_at: string | null;
  closed_at: string | null;
  exit_price: number | null;
  highest_tp_hit: string | null;
  result_pips: number | null;
  result_percent: number | null;
  duration_minutes: number | null;
  evaluation_notes: string | null;
  price_path_json: Array<{
    t: string;
    o: number;
    h: number;
    l: number;
    c: number;
  }> | null;
  created_at: string;
}

export interface EquityPoint {
  signal_id: number;
  date: string;
  channel: string;
  direction: string;
  pips: number;
  cumulative_pips: number;
  percent: number;
  cumulative_percent: number;
}

export interface DashboardMetrics {
  total_messages: number;
  parsed_signals: number;
  unparsed_messages: number;
  won_count: number;
  lost_count: number;
  pending_count: number;
  expired_count: number;
  unavailable_count: number;
  win_rate_percent: number | null;
  total_pips: number;
  cumulative_percent: number;
  avg_win_pips: number | null;
  avg_loss_pips: number | null;
  avg_duration_minutes: number | null;
  has_demo_data: boolean;
  has_real_data: boolean;
  channels: string[];
  equity_curve: EquityPoint[];
}

export interface SignalFilters {
  channel: string;
  status: string;
  instrument: string;
  direction: string;
  date_from: string;
  date_to: string;
  data_mode: 'all' | 'real' | 'demo';
}

const API_BASE = '/gold/api';
const TOKEN_KEY = 'gold_signals_token';

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string | null) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    credentials: 'include',
  });

  if (res.status === 401) {
    setStoredToken(null);
    throw new Error('UNAUTHORIZED');
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Error HTTP ${res.status}`);
  }

  return res.json();
}

export async function loginApi(username: string, password: string) {
  const data = await apiFetch<{ authenticated: boolean; username: string; token: string }>(
    '/auth/login',
    {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }
  );
  setStoredToken(data.token);
  return data;
}

export async function logoutApi() {
  await apiFetch('/auth/logout', { method: 'POST' }).catch(() => {});
  setStoredToken(null);
}

export async function checkSessionApi() {
  return apiFetch<{ authenticated: boolean; username: string; read_only: boolean }>('/auth/me');
}

function buildQuery(filters: Partial<SignalFilters>): string {
  const params = new URLSearchParams();
  if (filters.channel && filters.channel !== 'ALL') params.set('channel', filters.channel);
  if (filters.status && filters.status !== 'ALL') params.set('status', filters.status);
  if (filters.instrument && filters.instrument !== 'ALL') params.set('instrument', filters.instrument);
  if (filters.direction && filters.direction !== 'ALL') params.set('direction', filters.direction);
  if (filters.date_from) params.set('date_from', filters.date_from);
  if (filters.date_to) params.set('date_to', filters.date_to);
  if (filters.data_mode) params.set('data_mode', filters.data_mode);
  const qs = params.toString();
  return qs ? `?${qs}` : '';
}

export async function fetchSignals(filters: Partial<SignalFilters>): Promise<SignalItem[]> {
  return apiFetch<SignalItem[]>(`/signals${buildQuery(filters)}`);
}

export async function fetchMetrics(filters: Partial<SignalFilters>): Promise<DashboardMetrics> {
  return apiFetch<DashboardMetrics>(`/metrics${buildQuery(filters)}`);
}

export async function fetchSignalDetail(id: number): Promise<SignalItem> {
  return apiFetch<SignalItem>(`/signals/${id}`);
}

export async function triggerEvaluateSignal(id: number): Promise<SignalItem> {
  return apiFetch<SignalItem>(`/signals/${id}/evaluate`, { method: 'POST' });
}

export async function fetchSyncStatus(): Promise<{
  read_only: boolean;
  configured_channels: string[];
  channels: Array<{
    channel_username: string;
    last_message_id: number;
    last_sync_at: string | null;
    status_message: string | null;
  }>;
}> {
  return apiFetch('/sync-status');
}
