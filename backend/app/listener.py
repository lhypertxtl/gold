import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from telethon import TelegramClient, events
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal, engine
from app.models import Base, Signal, ChannelSyncState
from app.parser import parse_signal_message
from app.evaluator import evaluate_signal_record

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("gold.listener")


def upsert_telegram_message(
    db: Session,
    channel_username: str,
    channel_title: Optional[str],
    message_id: int,
    published_at: datetime,
    raw_text: str,
    evaluate_immediately: bool = True,
) -> Optional[Signal]:
    """
    Registra un mensaje real proveniente de Telegram (is_demo=False),
    ejecuta el parser de señales y opcionalmente evalúa contra precios reales.
    """
    if not raw_text or not raw_text.strip():
        return None

    clean_channel = channel_username.strip().lstrip("@").lower()
    existing = (
        db.query(Signal)
        .filter(
            Signal.channel_username == clean_channel,
            Signal.telegram_message_id == message_id,
        )
        .first()
    )
    if existing:
        return existing

    parsed = parse_signal_message(raw_text, default_channel_is_gold=True)
    tps = parsed.take_profits

    sig = Signal(
        channel_username=clean_channel,
        channel_title=channel_title or f"@{clean_channel}",
        telegram_message_id=message_id,
        published_at=published_at if published_at.tzinfo else published_at.replace(tzinfo=timezone.utc),
        raw_text=raw_text.strip(),
        is_demo=False,
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
        status="PENDIENTE" if parsed.is_parsed else "SIN_INTERPRETAR",
    )
    db.add(sig)
    db.commit()
    db.refresh(sig)

    if evaluate_immediately and sig.is_parsed:
        evaluate_signal_record(db, sig)

    return sig


async def sync_channel_history(client: TelegramClient, channel_name: str, limit: int = 100):
    """Lee en modo solo lectura los últimos mensajes de un canal y actualiza el estado."""
    clean_channel = channel_name.strip().lstrip("@").lower()
    logger.info("Sincronizando historial en modo solo lectura de @%s (límite=%d)...", clean_channel, limit)

    entity = await client.get_entity(clean_channel)
    title = getattr(entity, "title", f"@{clean_channel}")

    messages = []
    async for msg in client.iter_messages(entity, limit=limit):
        if msg and getattr(msg, "message", None):
            messages.append(msg)

    # Procesar en orden cronológico (más antiguo primero)
    messages.reverse()
    new_count = 0
    max_msg_id = 0

    with SessionLocal() as db:
        for msg in messages:
            max_msg_id = max(max_msg_id, msg.id)
            created = upsert_telegram_message(
                db=db,
                channel_username=clean_channel,
                channel_title=title,
                message_id=msg.id,
                published_at=msg.date,
                raw_text=msg.message,
                evaluate_immediately=True,
            )
            if created:
                new_count += 1

        state = (
            db.query(ChannelSyncState)
            .filter(ChannelSyncState.channel_username == clean_channel)
            .first()
        )
        if not state:
            state = ChannelSyncState(channel_username=clean_channel)
            db.add(state)
        if max_msg_id > state.last_message_id:
            state.last_message_id = max_msg_id
        state.last_sync_at = datetime.now(timezone.utc)
        state.status_message = f"Conectado (Solo lectura). Última sincronización OK ({len(messages)} leídos)."
        db.commit()

    logger.info("Canal @%s sincronizado (%d mensajes procesados).", clean_channel, len(messages))


async def periodic_evaluation_loop():
    """Re-evalúa periódicamente las señales pendientes contra precios públicos reales."""
    while True:
        try:
            with SessionLocal() as db:
                pending_signals = (
                    db.query(Signal)
                    .filter(
                        Signal.is_parsed.is_(True),
                        Signal.is_demo.is_(False),
                        Signal.status.in_(["PENDIENTE", "NO_DISPONIBLE"]),
                    )
                    .all()
                )
                for sig in pending_signals:
                    evaluate_signal_record(db, sig)
        except Exception as exc:
            logger.error("Error en bucle de evaluación periódica: %s", exc)

        await asyncio.sleep(settings.EVALUATOR_INTERVAL_SECONDS)


async def run_listener():
    """
    Inicia el cliente Telethon en modo ESTRICTAMENTE SOLO LECTURA.
    Requiere que el archivo .session ya haya sido autenticado con scripts/auth_telegram.py.
    """
    Base.metadata.create_all(bind=engine)

    if not settings.is_telegram_configured:
        raise RuntimeError(
            "Faltan TELEGRAM_API_ID, TELEGRAM_API_HASH o TELEGRAM_PHONE en .env. "
            "Configúralos antes de iniciar el lector."
        )

    session_path = Path(settings.TELEGRAM_SESSION_PATH)
    session_file = session_path if session_path.suffix == ".session" else session_path.with_suffix(".session")
    if not session_file.exists():
        raise RuntimeError(
            f"No se encontró archivo de sesión en {session_file}. "
            "Ejecuta primero: python scripts/auth_telegram.py"
        )

    client = TelegramClient(
        str(session_path),
        int(settings.TELEGRAM_API_ID),
        settings.TELEGRAM_API_HASH,
    )

    await client.connect()
    if not await client.is_user_authorized():
        await client.disconnect()
        raise RuntimeError(
            "La sesión de Telegram no está autorizada o fue revocada. "
            "Ejecuta interactivamente: python scripts/auth_telegram.py"
        )

    logger.info("Sesión MTProto iniciada en MODO SOLO LECTURA. Canales: %s", settings.TELEGRAM_CHANNELS)

    # Sincronización inicial de cada canal configurado
    for ch in settings.TELEGRAM_CHANNELS:
        try:
            await sync_channel_history(client, ch, limit=settings.TELEGRAM_INITIAL_LIMIT)
        except Exception as exc:
            logger.error("Error sincronizando canal @%s: %s", ch, exc)

    # Suscripción en tiempo real a nuevos mensajes (SOLO LECTURA)
    @client.on(events.NewMessage(chats=settings.TELEGRAM_CHANNELS))
    async def on_new_channel_message(event):
        try:
            msg = event.message
            if not msg or not getattr(msg, "message", None):
                return
            chat = await event.get_chat()
            username = (getattr(chat, "username", None) or settings.TELEGRAM_CHANNELS[0]).lower()
            title = getattr(chat, "title", f"@{username}")
            logger.info("Nuevo mensaje detectado en @%s (id=%s)", username, msg.id)
            with SessionLocal() as db:
                upsert_telegram_message(
                    db=db,
                    channel_username=username,
                    channel_title=title,
                    message_id=msg.id,
                    published_at=msg.date,
                    raw_text=msg.message,
                    evaluate_immediately=True,
                )
                state = (
                    db.query(ChannelSyncState)
                    .filter(ChannelSyncState.channel_username == username)
                    .first()
                )
                if state:
                    state.last_message_id = max(state.last_message_id, msg.id)
                    state.last_sync_at = datetime.now(timezone.utc)
                    db.commit()
        except Exception as exc:
            logger.error("Error procesando nuevo mensaje en vivo: %s", exc)

    eval_task = asyncio.create_task(periodic_evaluation_loop())
    try:
        await client.run_until_disconnected()
    finally:
        eval_task.cancel()


if __name__ == "__main__":
    asyncio.run(run_listener())
