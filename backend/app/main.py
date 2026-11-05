from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.auth import (
    COOKIE_NAME,
    create_access_token,
    get_current_user,
    verify_admin_credentials,
)
from app.config import ROOT_DIR, settings
from app.database import Base, engine, get_db
from app.evaluator import evaluate_signal_record
from app.models import ChannelSyncState, Signal
from app.schemas import (
    DashboardMetricsOut,
    EquityPoint,
    LoginRequest,
    LoginResponse,
    SignalOut,
)

# Crear tablas al iniciar
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Gold Signals API",
    description="Tablero en modo solo lectura de señales de oro (XAUUSD / GC)",
    version="1.0.0",
    docs_url=f"{settings.APP_BASE_PATH}/api/docs" if settings.APP_ENV != "production" else None,
    redoc_url=None,
)

api_router = APIRouter()


@api_router.get("/health")
def health_check():
    return {
        "status": "ok",
        "mode": "read_only",
        "base_path": settings.APP_BASE_PATH,
    }


@api_router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response):
    if not settings.is_auth_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Credenciales de administrador no configuradas en variables de entorno (.env)",
        )
    if not verify_admin_credentials(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )
    token = create_access_token(settings.ADMIN_USERNAME)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=(settings.APP_ENV == "production"),
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
        path="/",
    )
    return LoginResponse(
        authenticated=True,
        username=settings.ADMIN_USERNAME,
        token=token,
    )


@api_router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"authenticated": False}


@api_router.get("/auth/me")
def get_me(username: str = Depends(get_current_user)):
    return {
        "authenticated": True,
        "username": username,
        "read_only": True,
    }


def _apply_signal_filters(
    query,
    channel: Optional[str],
    status_filter: Optional[str],
    instrument: Optional[str],
    direction: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
    data_mode: str,
):
    if data_mode == "real":
        query = query.filter(Signal.is_demo.is_(False))
    elif data_mode == "demo":
        query = query.filter(Signal.is_demo.is_(True))

    if channel and channel != "ALL":
        query = query.filter(Signal.channel_username == channel.strip().lstrip("@").lower())
    if status_filter and status_filter != "ALL":
        query = query.filter(Signal.status == status_filter)
    if instrument and instrument != "ALL":
        query = query.filter(Signal.instrument == instrument)
    if direction and direction != "ALL":
        query = query.filter(Signal.direction == direction)

    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from)
            query = query.filter(Signal.published_at >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to)
            # Si viene solo fecha YYYY-MM-DD, incluir hasta el final del día
            if len(date_to) == 10:
                dt_to = dt_to.replace(hour=23, minute=59, second=59)
            query = query.filter(Signal.published_at <= dt_to)
        except ValueError:
            pass

    return query


@api_router.get("/signals", response_model=list[SignalOut])
def list_signals(
    channel: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    instrument: Optional[str] = Query(default=None),
    direction: Optional[str] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    data_mode: str = Query(default="all", pattern="^(all|real|demo)$"),
    limit: int = Query(default=200, ge=1, le=1000),
    _user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Signal)
    q = _apply_signal_filters(q, channel, status_filter, instrument, direction, date_from, date_to, data_mode)
    return q.order_by(Signal.published_at.desc(), Signal.id.desc()).limit(limit).all()


@api_router.get("/signals/{signal_id}", response_model=SignalOut)
def get_signal_detail(
    signal_id: int,
    _user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sig = db.query(Signal).filter(Signal.id == signal_id).first()
    if not sig:
        raise HTTPException(status_code=404, detail="Señal no encontrada")
    return sig


@api_router.post("/signals/{signal_id}/evaluate", response_model=SignalOut)
def trigger_signal_evaluation(
    signal_id: int,
    _user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sig = db.query(Signal).filter(Signal.id == signal_id).first()
    if not sig:
        raise HTTPException(status_code=404, detail="Señal no encontrada")
    if sig.is_demo:
        return sig
    return evaluate_signal_record(db, sig)


@api_router.get("/metrics", response_model=DashboardMetricsOut)
def get_dashboard_metrics(
    channel: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    instrument: Optional[str] = Query(default=None),
    direction: Optional[str] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    data_mode: str = Query(default="all", pattern="^(all|real|demo)$"),
    _user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    all_channels = [
        r[0] for r in db.query(Signal.channel_username).distinct().order_by(Signal.channel_username).all()
    ]
    has_demo = db.query(Signal.id).filter(Signal.is_demo.is_(True)).first() is not None
    has_real = db.query(Signal.id).filter(Signal.is_demo.is_(False)).first() is not None

    q = db.query(Signal)
    q = _apply_signal_filters(q, channel, status_filter, instrument, direction, date_from, date_to, data_mode)
    records: list[Signal] = q.order_by(Signal.published_at.asc(), Signal.id.asc()).all()

    total_messages = len(records)
    parsed_signals = sum(1 for r in records if r.is_parsed)
    unparsed_messages = sum(1 for r in records if not r.is_parsed or r.status == "SIN_INTERPRETAR")
    won_count = sum(1 for r in records if r.status == "GANADA")
    lost_count = sum(1 for r in records if r.status == "PERDIDA")
    pending_count = sum(1 for r in records if r.status == "PENDIENTE")
    expired_count = sum(1 for r in records if r.status == "EXPIRADA")
    unavailable_count = sum(1 for r in records if r.status == "NO_DISPONIBLE")

    closed_total = won_count + lost_count
    win_rate = round((won_count / closed_total) * 100.0, 1) if closed_total > 0 else None

    win_pips_list = [r.result_pips for r in records if r.status == "GANADA" and r.result_pips is not None]
    loss_pips_list = [r.result_pips for r in records if r.status == "PERDIDA" and r.result_pips is not None]
    durations = [
        r.duration_minutes
        for r in records
        if r.status in ("GANADA", "PERDIDA") and r.duration_minutes is not None
    ]

    avg_win = round(sum(win_pips_list) / len(win_pips_list), 1) if win_pips_list else None
    avg_loss = round(sum(loss_pips_list) / len(loss_pips_list), 1) if loss_pips_list else None
    avg_duration = int(round(sum(durations) / len(durations))) if durations else None

    equity_curve: list[EquityPoint] = []
    cum_pips = 0.0
    cum_pct = 0.0

    for r in records:
        if r.status in ("GANADA", "PERDIDA") and r.result_pips is not None and r.result_percent is not None:
            cum_pips = round(cum_pips + r.result_pips, 1)
            cum_pct = round(cum_pct + r.result_percent, 3)
            equity_curve.append(
                EquityPoint(
                    signal_id=r.id,
                    date=r.published_at.strftime("%Y-%m-%d %H:%M"),
                    channel=r.channel_username,
                    direction=r.direction or "",
                    pips=r.result_pips,
                    cumulative_pips=cum_pips,
                    percent=r.result_percent,
                    cumulative_percent=cum_pct,
                )
            )

    return DashboardMetricsOut(
        total_messages=total_messages,
        parsed_signals=parsed_signals,
        unparsed_messages=unparsed_messages,
        won_count=won_count,
        lost_count=lost_count,
        pending_count=pending_count,
        expired_count=expired_count,
        unavailable_count=unavailable_count,
        win_rate_percent=win_rate,
        total_pips=cum_pips,
        cumulative_percent=cum_pct,
        avg_win_pips=avg_win,
        avg_loss_pips=avg_loss,
        avg_duration_minutes=avg_duration,
        has_demo_data=has_demo,
        has_real_data=has_real,
        channels=all_channels or settings.TELEGRAM_CHANNELS,
        equity_curve=equity_curve,
    )


@api_router.get("/sync-status")
def get_sync_status(
    _user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    states = db.query(ChannelSyncState).all()
    return {
        "read_only": True,
        "configured_channels": settings.TELEGRAM_CHANNELS,
        "channels": [
            {
                "channel_username": s.channel_username,
                "last_message_id": s.last_message_id,
                "last_sync_at": s.last_sync_at,
                "status_message": s.status_message,
            }
            for s in states
        ],
    }


# Registrar el router tanto en /gold/api como en /api (por si un proxy inverso recorta o conserva /gold)
app.include_router(api_router, prefix=f"{settings.APP_BASE_PATH}/api")
app.include_router(api_router, prefix="/api")

# Servir el frontend compilado (React + Vite) bajo /gold/
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"

if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount(
            f"{settings.APP_BASE_PATH}/assets",
            StaticFiles(directory=str(assets_dir)),
            name="gold-assets",
        )

    @app.get("/")
    def root_redirect():
        return RedirectResponse(url=f"{settings.APP_BASE_PATH}/")

    @app.get(f"{settings.APP_BASE_PATH}")
    def base_redirect():
        return RedirectResponse(url=f"{settings.APP_BASE_PATH}/")

    @app.get(f"{settings.APP_BASE_PATH}/{{full_path:path}}")
    def serve_spa(full_path: str):
        candidate = (FRONTEND_DIST / full_path).resolve()
        if full_path and candidate.is_file() and str(candidate).startswith(str(FRONTEND_DIST.resolve())):
            return FileResponse(str(candidate))
        return FileResponse(str(FRONTEND_DIST / "index.html"))
