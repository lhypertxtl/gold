"""
Semilla de señales de ejemplo para el preview local del tablero.
Todas las entradas están explícitamente marcadas con is_demo=True y la etiqueta [DATO DE EJEMPLO]
para que nunca se confundan con datos reales.
"""
from datetime import datetime, timedelta, timezone
from app.database import SessionLocal, engine
from app.models import Base, Signal, ChannelSyncState
from app.parser import parse_signal_message


def seed_demo_signals():
    Base.metadata.create_all(bind=engine)
    now = datetime.now(timezone.utc)

    demo_items = [
        {
            "msg_id": 900001,
            "channel": "tagsignals",
            "title": "TAG Signals Gold [EJEMPLO PREVIEW]",
            "published_at": now - timedelta(days=5, hours=4),
            "raw_text": (
                "🧪 [DATO DE EJEMPLO — PREVIEW LOCAL]\n"
                "GOLD (XAUUSD) BUY NOW @ 2735.00 - 2732.00\n\n"
                "🛑 SL: 2724.00\n"
                "🎯 TP1: 2742.00\n"
                "🎯 TP2: 2750.00\n"
                "🎯 TP3: 2762.00\n\n"
                "Gestión de riesgo recomendada. Señal de demostración."
            ),
            "status": "GANADA",
            "highest_tp_hit": "TP2",
            "exit_price": 2750.00,
            "result_pips": 165.0,
            "result_percent": 0.604,
            "duration_minutes": 85,
            "evaluation_notes": "[EJEMPLO] Objetivo TP2 alcanzado en 2750.00 USD tras 1h 25m.",
            "base_price": 2733.50,
            "end_price": 2750.00,
        },
        {
            "msg_id": 900002,
            "channel": "tagsignals",
            "title": "TAG Signals Gold [EJEMPLO PREVIEW]",
            "published_at": now - timedelta(days=4, hours=6),
            "raw_text": (
                "🧪 [DATO DE EJEMPLO — PREVIEW LOCAL]\n"
                "XAUUSD VENTA / SELL @ 2758.50\n"
                "Stop Loss: 2768.50\n"
                "Take Profit 1: 2748.50\n"
                "Take Profit 2: 2738.00\n"
                "Take Profit 3: 2725.00"
            ),
            "status": "PERDIDA",
            "highest_tp_hit": "SL",
            "exit_price": 2768.50,
            "result_pips": -100.0,
            "result_percent": -0.363,
            "duration_minutes": 42,
            "evaluation_notes": "[EJEMPLO] Stop Loss alcanzado en 2768.50 USD tras publicación de datos macro.",
            "base_price": 2758.50,
            "end_price": 2768.50,
        },
        {
            "msg_id": 900003,
            "channel": "tagsignals",
            "title": "TAG Signals Gold [EJEMPLO PREVIEW]",
            "published_at": now - timedelta(days=3, hours=2),
            "raw_text": (
                "🧪 [DATO DE EJEMPLO — PREVIEW LOCAL]\n"
                "🔥 Buenos días equipo, recuerden asegurar ganancias parciales y mover SL a Break Even cuando se toque el TP1. ¡Excelente semana para todos!"
            ),
            "status": "SIN_INTERPRETAR",
            "highest_tp_hit": None,
            "exit_price": None,
            "result_pips": None,
            "result_percent": None,
            "duration_minutes": None,
            "evaluation_notes": "[EJEMPLO] Mensaje informativo del canal sin parámetros operativos (guardado como 'Sin interpretar').",
            "base_price": None,
            "end_price": None,
        },
        {
            "msg_id": 900004,
            "channel": "tagsignals",
            "title": "TAG Signals Gold [EJEMPLO PREVIEW]",
            "published_at": now - timedelta(days=2, hours=10),
            "raw_text": (
                "🧪 [DATO DE EJEMPLO — PREVIEW LOCAL]\n"
                "FUTUROS ORO GC1! COMPRA @ 2744.00\n"
                "SL: 2734.00\n"
                "TP1: 2754.00\n"
                "TP2: 2766.00\n"
                "TP3: 2778.00"
            ),
            "status": "GANADA",
            "highest_tp_hit": "TP3",
            "exit_price": 2778.00,
            "result_pips": 340.0,
            "result_percent": 1.239,
            "duration_minutes": 210,
            "evaluation_notes": "[EJEMPLO] Objetivo TP3 alcanzado en 2778.00 USD tras 3h 30m.",
            "base_price": 2744.00,
            "end_price": 2778.00,
        },
        {
            "msg_id": 900005,
            "channel": "tagsignals",
            "title": "TAG Signals Gold [EJEMPLO PREVIEW]",
            "published_at": now - timedelta(days=1, hours=18),
            "raw_text": (
                "🧪 [DATO DE EJEMPLO — PREVIEW LOCAL]\n"
                "XAUUSD BUY LIMIT @ 2710.00 - 2708.00\n"
                "SL: 2699.00\n"
                "TP1: 2722.00\n"
                "TP2: 2735.00"
            ),
            "status": "EXPIRADA",
            "highest_tp_hit": None,
            "exit_price": None,
            "result_pips": 0.0,
            "result_percent": 0.0,
            "duration_minutes": None,
            "evaluation_notes": "[EJEMPLO] El precio no retrocedió hasta la zona límite (2709.00 USD) dentro de la ventana de validez.",
            "base_price": 2728.00,
            "end_price": 2740.00,
        },
        {
            "msg_id": 900006,
            "channel": "tagsignals",
            "title": "TAG Signals Gold [EJEMPLO PREVIEW]",
            "published_at": now - timedelta(hours=14),
            "raw_text": (
                "🧪 [DATO DE EJEMPLO — PREVIEW LOCAL]\n"
                "SELL XAU/USD @ 2764.00 - 2766.00\n"
                "SL: 2774.50\n"
                "TP1: 2754.00\n"
                "TP2: 2743.00"
            ),
            "status": "GANADA",
            "highest_tp_hit": "TP1",
            "exit_price": 2754.00,
            "result_pips": 110.0,
            "result_percent": 0.398,
            "duration_minutes": 65,
            "evaluation_notes": "[EJEMPLO] Objetivo TP1 alcanzado en 2754.00 USD.",
            "base_price": 2765.00,
            "end_price": 2754.00,
        },
        {
            "msg_id": 900007,
            "channel": "tagsignals",
            "title": "TAG Signals Gold [EJEMPLO PREVIEW]",
            "published_at": now - timedelta(hours=2),
            "raw_text": (
                "🧪 [DATO DE EJEMPLO — PREVIEW LOCAL]\n"
                "XAUUSD BUY @ 2752.00\n"
                "SL: 2742.00\n"
                "TP1: 2762.00\n"
                "TP2: 2772.00\n"
                "TP3: 2785.00"
            ),
            "status": "PENDIENTE",
            "highest_tp_hit": None,
            "exit_price": 2756.40,
            "result_pips": 44.0,
            "result_percent": 0.160,
            "duration_minutes": 115,
            "evaluation_notes": "[EJEMPLO] Operación activa en curso (+44 pips flotantes).",
            "base_price": 2752.00,
            "end_price": 2756.40,
        },
    ]

    with SessionLocal() as db:
        for item in demo_items:
            exists = (
                db.query(Signal)
                .filter(
                    Signal.channel_username == item["channel"],
                    Signal.telegram_message_id == item["msg_id"],
                )
                .first()
            )
            if exists:
                continue

            parsed = parse_signal_message(item["raw_text"], default_channel_is_gold=True)
            tps = parsed.take_profits

            # Construir pequeña curva ilustrativa etiquetada como demo para el detalle
            path_points = []
            if item["base_price"] is not None and item["end_price"] is not None:
                steps = 12
                for i in range(steps + 1):
                    ratio = i / steps
                    t_point = item["published_at"] + timedelta(minutes=i * 10)
                    interp = round(
                        item["base_price"] + (item["end_price"] - item["base_price"]) * ratio,
                        2,
                    )
                    path_points.append(
                        {
                            "t": t_point.isoformat(),
                            "o": interp,
                            "h": round(interp + 1.2, 2),
                            "l": round(interp - 1.2, 2),
                            "c": interp,
                        }
                    )

            sig = Signal(
                channel_username=item["channel"],
                channel_title=item["title"],
                telegram_message_id=item["msg_id"],
                published_at=item["published_at"],
                raw_text=item["raw_text"],
                is_demo=True,
                is_parsed=parsed.is_parsed,
                parse_notes=parsed.parse_notes,
                direction=parsed.direction,
                instrument=parsed.instrument,
                entry_price=parsed.entry_price,
                entry_range_low=parsed.entry_range_low,
                entry_range_high=parsed.entry_range_high,
                stop_loss=parsed.stop_loss,
                tp1=tps[0] if len(tps) > 0 else None,
                tp2=tps[1] if len(tps) > 1 else None,
                tp3=tps[2] if len(tps) > 2 else None,
                tp4=tps[3] if len(tps) > 3 else None,
                status=item["status"],
                evaluated_at=now,
                price_source="Datos de Ejemplo (Preview Local)",
                entry_triggered_at=(
                    item["published_at"] + timedelta(minutes=5)
                    if item["status"] in ("GANADA", "PERDIDA", "PENDIENTE")
                    else None
                ),
                closed_at=(
                    item["published_at"] + timedelta(minutes=(item["duration_minutes"] or 60) + 5)
                    if item["status"] in ("GANADA", "PERDIDA")
                    else None
                ),
                exit_price=item["exit_price"],
                highest_tp_hit=item["highest_tp_hit"],
                result_pips=item["result_pips"],
                result_percent=item["result_percent"],
                duration_minutes=item["duration_minutes"],
                evaluation_notes=item["evaluation_notes"],
                price_path_json=path_points if path_points else None,
            )
            db.add(sig)

        state = (
            db.query(ChannelSyncState)
            .filter(ChannelSyncState.channel_username == "tagsignals")
            .first()
        )
        if not state:
            state = ChannelSyncState(
                channel_username="tagsignals",
                last_message_id=900007,
                last_sync_at=now,
                status_message="Modo Preview Local (Datos de ejemplo cargados — pendiente conectar sesión real de Telegram)",
            )
            db.add(state)

        db.commit()
    print("✅ Datos de ejemplo ([DATO DE EJEMPLO]) cargados correctamente.")


if __name__ == "__main__":
    seed_demo_signals()
