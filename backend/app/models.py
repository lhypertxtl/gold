from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    JSON,
    UniqueConstraint,
    Index,
)
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Signal(Base):
    """
    Representa un mensaje leído de un canal de Telegram y su interpretación
    como señal de oro (XAUUSD / GC), junto con su evaluación frente al precio posterior.
    """

    __tablename__ = "signals"
    __table_args__ = (
        UniqueConstraint("channel_username", "telegram_message_id", name="uq_channel_msg"),
        Index("ix_signals_published_at", "published_at"),
        Index("ix_signals_status", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Metadatos del mensaje en Telegram
    channel_username = Column(String(128), nullable=False, index=True)
    channel_title = Column(String(256), nullable=True)
    telegram_message_id = Column(Integer, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=False)
    raw_text = Column(Text, nullable=False)

    # Identificador de origen (True = semilla de ejemplo para preview; False = señal real de Telegram)
    is_demo = Column(Boolean, default=False, nullable=False, index=True)

    # Datos parseados de la señal (nulos si is_parsed == False)
    is_parsed = Column(Boolean, default=False, nullable=False)
    parse_notes = Column(String(512), nullable=True)

    # COMPRA | VENTA | None
    direction = Column(String(16), nullable=True, index=True)
    # XAUUSD | GC | None
    instrument = Column(String(32), nullable=True, index=True)

    # Entrada (precio único o punto medio + rango opcional)
    entry_price = Column(Float, nullable=True)
    entry_range_low = Column(Float, nullable=True)
    entry_range_high = Column(Float, nullable=True)

    # Stop Loss y Take Profits
    stop_loss = Column(Float, nullable=True)
    tp1 = Column(Float, nullable=True)
    tp2 = Column(Float, nullable=True)
    tp3 = Column(Float, nullable=True)
    tp4 = Column(Float, nullable=True)

    # Estado de evaluación:
    # SIN_INTERPRETAR | PENDIENTE | GANADA | PERDIDA | EXPIRADA | NO_DISPONIBLE
    status = Column(String(32), default="PENDIENTE", nullable=False)

    # Resultado real contra precio posterior
    evaluated_at = Column(DateTime(timezone=True), nullable=True)
    price_source = Column(String(64), nullable=True)
    entry_triggered_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    exit_price = Column(Float, nullable=True)
    highest_tp_hit = Column(String(16), nullable=True)  # TP1, TP2, TP3, TP4 o SL

    # Desempeño cuantitativo (1 pip en XAUUSD = $0.10 de movimiento)
    result_pips = Column(Float, nullable=True)
    result_percent = Column(Float, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    evaluation_notes = Column(String(512), nullable=True)

    # Serie resumida de precios posteriores para visualizar en la página de detalle
    price_path_json = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class ChannelSyncState(Base):
    """Guarda el último ID de mensaje leído por canal y estado del lector."""

    __tablename__ = "channel_sync_state"

    id = Column(Integer, primary_key=True)
    channel_username = Column(String(128), unique=True, nullable=False)
    last_message_id = Column(Integer, default=0, nullable=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    status_message = Column(String(256), nullable=True)
