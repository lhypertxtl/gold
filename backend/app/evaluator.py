import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
import httpx
from sqlalchemy.orm import Session
from app.config import settings
from app.models import Signal

logger = logging.getLogger("gold.evaluator")

# En XAUUSD / Oro Spot estándar de trading, 1 pip = $0.10 USD de movimiento (1 USD = 10 pips)
PIP_SIZE_USD = 0.10


@dataclass
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass
class EvaluationOutcome:
    status: str  # PENDIENTE | GANADA | PERDIDA | EXPIRADA | NO_DISPONIBLE
    price_source: Optional[str] = None
    entry_triggered_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    exit_price: Optional[float] = None
    highest_tp_hit: Optional[str] = None
    result_pips: Optional[float] = None
    result_percent: Optional[float] = None
    duration_minutes: Optional[int] = None
    evaluation_notes: Optional[str] = None
    price_path: Optional[list[dict]] = None


def price_diff_to_pips(diff_usd: float) -> float:
    return round(diff_usd / PIP_SIZE_USD, 1)


def fetch_gold_candles_yahoo(
    start_dt: datetime,
    end_dt: datetime,
    instrument: str = "XAUUSD",
) -> tuple[list[Candle], Optional[str]]:
    """
    Obtiene velas OHLC reales desde la API pública de Yahoo Finance (query1.finance.yahoo.com).
    Intenta primero con el ticker apropiado ('GC=F' o 'XAUUSD=X') y su fallback.
    Nunca inventa ni simula precios: si la fuente pública no devuelve velas para el periodo,
    retorna lista vacía.
    """
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)

    age_days = (datetime.now(timezone.utc) - start_dt).total_seconds() / 86400.0
    if age_days <= 6.5:
        interval = "5m"
    elif age_days <= 55:
        interval = "15m"
    else:
        interval = "1h"

    period1 = int((start_dt - timedelta(minutes=15)).timestamp())
    period2 = int((end_dt + timedelta(minutes=15)).timestamp())

    tickers = (
        [settings.PRICE_PRIMARY_TICKER, settings.PRICE_FALLBACK_TICKER]
        if instrument == "GC"
        else [settings.PRICE_FALLBACK_TICKER, settings.PRICE_PRIMARY_TICKER]
    )
    # Eliminar duplicados manteniendo orden
    seen = set()
    ordered_tickers = [t for t in tickers if not (t in seen or seen.add(t))]

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    for ticker in ordered_tickers:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        params = {
            "period1": period1,
            "period2": period2,
            "interval": interval,
            "includePrePost": "true",
        }
        try:
            with httpx.Client(timeout=10.0, headers=headers) as client:
                resp = client.get(url, params=params)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                result_list = data.get("chart", {}).get("result")
                if not result_list:
                    continue
                res = result_list[0]
                timestamps = res.get("timestamp") or []
                quote = (res.get("indicators", {}).get("quote") or [{}])[0]
                opens = quote.get("open") or []
                highs = quote.get("high") or []
                lows = quote.get("low") or []
                closes = quote.get("close") or []

                candles: list[Candle] = []
                for ts, o, h, l, c in zip(timestamps, opens, highs, lows, closes):
                    if None in (ts, o, h, l, c):
                        continue
                    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                    if dt < start_dt - timedelta(minutes=15):
                        continue
                    candles.append(
                        Candle(
                            timestamp=dt,
                            open=round(float(o), 2),
                            high=round(float(h), 2),
                            low=round(float(l), 2),
                            close=round(float(c), 2),
                        )
                    )
                if candles:
                    return candles, f"Yahoo Finance ({ticker}, {interval})"
        except Exception as exc:
            logger.warning("Error consultando precios públicos (%s): %s", ticker, exc)
            continue

    return [], None


def evaluate_candles_for_signal(
    direction: str,
    entry_price: float,
    entry_range_low: Optional[float],
    entry_range_high: Optional[float],
    stop_loss: float,
    tps: list[Optional[float]],
    published_at: datetime,
    candles: list[Candle],
    price_source: Optional[str],
    expiry_hours: int = 48,
) -> EvaluationOutcome:
    """
    Evalúa determinísticamente el recorrido de precios posteriores a una señal.
    Reglas:
    - Sin velas disponibles -> NO_DISPONIBLE.
    - Verifica primero la activación de la entrada (rango [entry_low, entry_high] con tolerancia de $1.50).
    - Una vez activada la entrada, revisa vela a vela si se alcanza primero el Stop Loss o TP1..TP4.
    - Si en una misma vela se tocan tanto SL como TP1 (vela de alta volatilidad), se aplica criterio conservador (PERDIDA por SL).
    """
    if not candles:
        return EvaluationOutcome(
            status="NO_DISPONIBLE",
            evaluation_notes="No se encontraron datos públicos de precio para el periodo de esta señal.",
        )

    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)

    valid_tps = [tp for tp in tps if tp is not None]
    if not valid_tps or stop_loss is None or entry_price is None:
        return EvaluationOutcome(
            status="SIN_INTERPRETAR",
            evaluation_notes="Faltan niveles de entrada, Stop Loss o Take Profit para evaluar.",
        )

    low_band = (entry_range_low if entry_range_low is not None else entry_price) - 1.50
    high_band = (entry_range_high if entry_range_high is not None else entry_price) + 1.50

    entry_triggered_at: Optional[datetime] = None
    highest_tp_idx: int = -1  # 0 -> TP1, 1 -> TP2, etc.
    highest_tp_price: Optional[float] = None
    highest_tp_time: Optional[datetime] = None
    sl_hit_time: Optional[datetime] = None

    expiry_dt = published_at + timedelta(hours=expiry_hours)

    # Construir serie compacta de precios para el gráfico de detalle (máximo 60 puntos)
    step = max(1, len(candles) // 60)
    price_path = [
        {
            "t": c.timestamp.isoformat(),
            "o": c.open,
            "h": c.high,
            "l": c.low,
            "c": c.close,
        }
        for c in candles[::step]
    ]

    for idx, c in enumerate(candles):
        if c.timestamp < published_at - timedelta(minutes=5):
            continue

        # 1. Fase previa a activación de entrada
        if entry_triggered_at is None:
            # En la primera vela posterior al mensaje o si el rango de la vela toca la banda de entrada
            if idx == 0 and low_band <= c.open <= high_band:
                entry_triggered_at = c.timestamp
            elif c.low <= high_band and c.high >= low_band:
                entry_triggered_at = c.timestamp
            elif c.timestamp > expiry_dt:
                return EvaluationOutcome(
                    status="EXPIRADA",
                    price_source=price_source,
                    evaluation_notes=f"El precio no tocó la zona de entrada ({entry_price}) dentro de {expiry_hours}h.",
                    price_path=price_path,
                )
            else:
                continue

        # 2. Fase con operación activa: comprobar SL y TPs en orden cronológico
        if direction == "COMPRA":
            sl_touched = c.low <= stop_loss
            tp1_touched = c.high >= valid_tps[0]

            # Si aún no había tocado TP1 y en esta vela toca SL:
            if highest_tp_idx == -1 and sl_touched:
                # Incluso si también tocó TP1 en la misma vela, criterio conservador: SL primero
                diff = stop_loss - entry_price
                duration = max(1, int((c.timestamp - entry_triggered_at).total_seconds() // 60))
                return EvaluationOutcome(
                    status="PERDIDA",
                    price_source=price_source,
                    entry_triggered_at=entry_triggered_at,
                    closed_at=c.timestamp,
                    exit_price=stop_loss,
                    highest_tp_hit="SL",
                    result_pips=price_diff_to_pips(diff),
                    result_percent=round((diff / entry_price) * 100.0, 3),
                    duration_minutes=duration,
                    evaluation_notes=f"Stop Loss alcanzado en {stop_loss:.2f} USD.",
                    price_path=price_path,
                )

            # Comprobar qué TPs alcanza esta vela
            for tp_i, tp_val in enumerate(valid_tps):
                if c.high >= tp_val and tp_i > highest_tp_idx:
                    highest_tp_idx = tp_i
                    highest_tp_price = tp_val
                    highest_tp_time = c.timestamp

            # Si ya alcanzó el último TP disponible o si después de asegurar TP1 el precio retrocede al SL/BE
            if highest_tp_idx == len(valid_tps) - 1 or (highest_tp_idx >= 0 and sl_touched):
                break

        elif direction == "VENTA":
            sl_touched = c.high >= stop_loss
            tp1_touched = c.low <= valid_tps[0]

            if highest_tp_idx == -1 and sl_touched:
                diff = entry_price - stop_loss
                duration = max(1, int((c.timestamp - entry_triggered_at).total_seconds() // 60))
                return EvaluationOutcome(
                    status="PERDIDA",
                    price_source=price_source,
                    entry_triggered_at=entry_triggered_at,
                    closed_at=c.timestamp,
                    exit_price=stop_loss,
                    highest_tp_hit="SL",
                    result_pips=price_diff_to_pips(diff),
                    result_percent=round((diff / entry_price) * 100.0, 3),
                    duration_minutes=duration,
                    evaluation_notes=f"Stop Loss alcanzado en {stop_loss:.2f} USD.",
                    price_path=price_path,
                )

            for tp_i, tp_val in enumerate(valid_tps):
                if c.low <= tp_val and tp_i > highest_tp_idx:
                    highest_tp_idx = tp_i
                    highest_tp_price = tp_val
                    highest_tp_time = c.timestamp

            if highest_tp_idx == len(valid_tps) - 1 or (highest_tp_idx >= 0 and sl_touched):
                break

    # Si al finalizar las velas ya se había alcanzado al menos TP1 -> GANADA
    if highest_tp_idx >= 0 and highest_tp_price is not None and highest_tp_time is not None and entry_triggered_at is not None:
        tp_label = f"TP{highest_tp_idx + 1}"
        diff = (
            (highest_tp_price - entry_price)
            if direction == "COMPRA"
            else (entry_price - highest_tp_price)
        )
        duration = max(1, int((highest_tp_time - entry_triggered_at).total_seconds() // 60))
        return EvaluationOutcome(
            status="GANADA",
            price_source=price_source,
            entry_triggered_at=entry_triggered_at,
            closed_at=highest_tp_time,
            exit_price=highest_tp_price,
            highest_tp_hit=tp_label,
            result_pips=price_diff_to_pips(diff),
            result_percent=round((diff / entry_price) * 100.0, 3),
            duration_minutes=duration,
            evaluation_notes=f"Objetivo {tp_label} alcanzado en {highest_tp_price:.2f} USD.",
            price_path=price_path,
        )

    # Si no se activó la entrada y aún no expiró
    last_candle = candles[-1]
    if entry_triggered_at is None:
        if last_candle.timestamp > expiry_dt:
            return EvaluationOutcome(
                status="EXPIRADA",
                price_source=price_source,
                evaluation_notes=f"Orden no activada tras {expiry_hours}h.",
                price_path=price_path,
            )
        return EvaluationOutcome(
            status="PENDIENTE",
            price_source=price_source,
            evaluation_notes=f"Esperando entrada en {entry_price:.2f}. Último precio: {last_candle.close:.2f} USD.",
            price_path=price_path,
        )

    # Entrada activada pero ni SL ni TP1 han sido tocados todavía -> PENDIENTE (en curso)
    floating_diff = (
        (last_candle.close - entry_price)
        if direction == "COMPRA"
        else (entry_price - last_candle.close)
    )
    duration = max(1, int((last_candle.timestamp - entry_triggered_at).total_seconds() // 60))
    return EvaluationOutcome(
        status="PENDIENTE",
        price_source=price_source,
        entry_triggered_at=entry_triggered_at,
        exit_price=last_candle.close,
        result_pips=price_diff_to_pips(floating_diff),
        result_percent=round((floating_diff / entry_price) * 100.0, 3),
        duration_minutes=duration,
        evaluation_notes=f"En curso. Precio actual de referencia: {last_candle.close:.2f} USD.",
        price_path=price_path,
    )


def evaluate_signal_record(db: Session, signal: Signal) -> Signal:
    """Evalúa una señal almacenada en base de datos contra precios públicos reales."""
    if not signal.is_parsed:
        signal.status = "SIN_INTERPRETAR"
        db.commit()
        return signal

    now = datetime.now(timezone.utc)
    pub = signal.published_at
    if pub.tzinfo is None:
        pub = pub.replace(tzinfo=timezone.utc)

    end_window = min(now, pub + timedelta(hours=settings.SIGNAL_EXPIRY_HOURS + 24))
    candles, source = fetch_gold_candles_yahoo(
        start_dt=pub,
        end_dt=end_window,
        instrument=signal.instrument or "XAUUSD",
    )

    outcome = evaluate_candles_for_signal(
        direction=signal.direction or "COMPRA",
        entry_price=signal.entry_price or 0.0,
        entry_range_low=signal.entry_range_low,
        entry_range_high=signal.entry_range_high,
        stop_loss=signal.stop_loss or 0.0,
        tps=[signal.tp1, signal.tp2, signal.tp3, signal.tp4],
        published_at=pub,
        candles=candles,
        price_source=source,
        expiry_hours=settings.SIGNAL_EXPIRY_HOURS,
    )

    signal.status = outcome.status
    signal.evaluated_at = now
    signal.price_source = outcome.price_source
    signal.entry_triggered_at = outcome.entry_triggered_at
    signal.closed_at = outcome.closed_at
    signal.exit_price = outcome.exit_price
    signal.highest_tp_hit = outcome.highest_tp_hit
    signal.result_pips = outcome.result_pips
    signal.result_percent = outcome.result_percent
    signal.duration_minutes = outcome.duration_minutes
    signal.evaluation_notes = outcome.evaluation_notes
    if outcome.price_path is not None:
        signal.price_path_json = outcome.price_path

    db.commit()
    db.refresh(signal)
    return signal
