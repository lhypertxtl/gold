from datetime import datetime, timedelta, timezone
from app.evaluator import Candle, evaluate_candles_for_signal


def test_evaluate_winning_buy_signal():
    pub = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
    candles = [
        Candle(timestamp=pub, open=2734.0, high=2736.0, low=2732.5, close=2735.0),
        Candle(timestamp=pub + timedelta(minutes=15), open=2735.0, high=2743.0, low=2734.0, close=2742.5),
        Candle(timestamp=pub + timedelta(minutes=30), open=2742.5, high=2751.0, low=2740.0, close=2750.2),
    ]
    outcome = evaluate_candles_for_signal(
        direction="COMPRA",
        entry_price=2733.5,
        entry_range_low=2732.0,
        entry_range_high=2735.0,
        stop_loss=2724.0,
        tps=[2742.0, 2750.0, 2762.0],
        published_at=pub,
        candles=candles,
        price_source="Test Feed",
    )
    assert outcome.status == "GANADA"
    assert outcome.highest_tp_hit == "TP2"
    assert outcome.exit_price == 2750.0
    assert outcome.result_pips == 165.0
    assert outcome.duration_minutes == 30


def test_evaluate_losing_sell_signal():
    pub = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
    candles = [
        Candle(timestamp=pub, open=2758.5, high=2760.0, low=2756.0, close=2759.0),
        Candle(timestamp=pub + timedelta(minutes=20), open=2759.0, high=2769.2, low=2758.0, close=2768.8),
    ]
    outcome = evaluate_candles_for_signal(
        direction="VENTA",
        entry_price=2758.5,
        entry_range_low=2758.5,
        entry_range_high=2758.5,
        stop_loss=2768.5,
        tps=[2748.5, 2738.0],
        published_at=pub,
        candles=candles,
        price_source="Test Feed",
    )
    assert outcome.status == "PERDIDA"
    assert outcome.highest_tp_hit == "SL"
    assert outcome.result_pips == -100.0
    assert outcome.duration_minutes == 20


def test_evaluate_no_candles_returns_unavailable():
    pub = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
    outcome = evaluate_candles_for_signal(
        direction="COMPRA",
        entry_price=2750.0,
        entry_range_low=2750.0,
        entry_range_high=2750.0,
        stop_loss=2740.0,
        tps=[2760.0],
        published_at=pub,
        candles=[],
        price_source=None,
    )
    assert outcome.status == "NO_DISPONIBLE"
    assert outcome.result_pips is None
