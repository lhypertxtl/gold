from app.parser import parse_signal_message


def test_parse_standard_buy_range():
    raw = """
    GOLD (XAUUSD) BUY NOW @ 2735.00 - 2732.00

    🛑 SL: 2724.00
    🎯 TP1: 2742.00
    🎯 TP2: 2750.00
    🎯 TP3: 2762.00
    """
    res = parse_signal_message(raw)
    assert res.is_parsed is True
    assert res.direction == "COMPRA"
    assert res.instrument == "XAUUSD"
    assert res.entry_range_low == 2732.0
    assert res.entry_range_high == 2735.0
    assert res.entry_price == 2733.5
    assert res.stop_loss == 2724.0
    assert res.take_profits == [2742.0, 2750.0, 2762.0]


def test_parse_spanish_sell_single_entry():
    raw = """
    XAUUSD VENTA @ 2758.50
    Stop Loss: 2768.50
    Take Profit 1: 2748.50
    Take Profit 2: 2738.00
    """
    res = parse_signal_message(raw)
    assert res.is_parsed is True
    assert res.direction == "VENTA"
    assert res.instrument == "XAUUSD"
    assert res.entry_price == 2758.5
    assert res.stop_loss == 2768.5
    assert res.take_profits == [2748.5, 2738.0]


def test_parse_gc_futures():
    raw = """
    FUTUROS ORO GC1! COMPRA @ 2744.00
    SL: 2734.00
    TP1: 2754.00
    TP2: 2766.00
    """
    res = parse_signal_message(raw)
    assert res.is_parsed is True
    assert res.direction == "COMPRA"
    assert res.instrument == "GC"
    assert res.entry_price == 2744.0
    assert res.stop_loss == 2734.0
    assert res.take_profits == [2754.0, 2766.0]


def test_unparsed_chat_message_does_not_invent_data():
    raw = "🔥 Excelente día equipo, cerramos la semana con +350 pips en el canal VIP!"
    res = parse_signal_message(raw)
    assert res.is_parsed is False
    assert res.entry_price is None
    assert res.stop_loss is None
    assert res.take_profits == []


def test_invalid_sl_side_rejected():
    # Compra pero con SL por encima de la entrada -> inconsistente, no debe inventar ni aprobar
    raw = """
    XAUUSD BUY @ 2750.00
    SL: 2760.00
    TP1: 2770.00
    """
    res = parse_signal_message(raw)
    assert res.is_parsed is False
