from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    authenticated: bool
    username: str
    token: str


class SignalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel_username: str
    channel_title: Optional[str] = None
    telegram_message_id: int
    published_at: datetime
    raw_text: str
    is_demo: bool
    is_parsed: bool
    parse_notes: Optional[str] = None
    direction: Optional[str] = None
    instrument: Optional[str] = None
    entry_price: Optional[float] = None
    entry_range_low: Optional[float] = None
    entry_range_high: Optional[float] = None
    stop_loss: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    tp3: Optional[float] = None
    tp4: Optional[float] = None
    status: str
    evaluated_at: Optional[datetime] = None
    price_source: Optional[str] = None
    entry_triggered_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    exit_price: Optional[float] = None
    highest_tp_hit: Optional[str] = None
    result_pips: Optional[float] = None
    result_percent: Optional[float] = None
    duration_minutes: Optional[int] = None
    evaluation_notes: Optional[str] = None
    price_path_json: Optional[list[dict]] = None
    created_at: datetime


class EquityPoint(BaseModel):
    signal_id: int
    date: str
    channel: str
    direction: str
    pips: float
    cumulative_pips: float
    percent: float
    cumulative_percent: float


class DashboardMetricsOut(BaseModel):
    total_messages: int
    parsed_signals: int
    unparsed_messages: int
    won_count: int
    lost_count: int
    pending_count: int
    expired_count: int
    unavailable_count: int
    win_rate_percent: Optional[float]
    total_pips: float
    cumulative_percent: float
    avg_win_pips: Optional[float]
    avg_loss_pips: Optional[float]
    avg_duration_minutes: Optional[int]
    has_demo_data: bool
    has_real_data: bool
    channels: list[str]
    equity_curve: list[EquityPoint]
