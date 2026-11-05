import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables desde .env en la raíz del proyecto o en el directorio actual
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()


class Settings:
    """Configuración centralizada leída exclusivamente desde variables de entorno."""

    APP_BASE_PATH: str = os.getenv("APP_BASE_PATH", "/gold").rstrip("/")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_HOST: str = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT: int = int(os.getenv("APP_PORT", "8010"))

    # Base de datos SQLite por defecto en ./data/gold_signals.db
    DEFAULT_DB_PATH = ROOT_DIR / "data" / "gold_signals.db"
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

    # Autenticación del tablero
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    # Credenciales de Telegram (Telethon MTProto modo solo lectura)
    TELEGRAM_API_ID: str = os.getenv("TELEGRAM_API_ID", "")
    TELEGRAM_API_HASH: str = os.getenv("TELEGRAM_API_HASH", "")
    TELEGRAM_PHONE: str = os.getenv("TELEGRAM_PHONE", "")
    TELEGRAM_SESSION_PATH: str = os.getenv(
        "TELEGRAM_SESSION_PATH", str(ROOT_DIR / "secrets" / "telegram_gold")
    )
    TELEGRAM_CHANNELS: list[str] = [
        ch.strip().lstrip("@")
        for ch in os.getenv("TELEGRAM_CHANNELS", "tagsignals").split(",")
        if ch.strip()
    ]
    TELEGRAM_INITIAL_LIMIT: int = int(os.getenv("TELEGRAM_INITIAL_LIMIT", "100"))

    # Evaluador de precios
    EVALUATOR_INTERVAL_SECONDS: int = int(os.getenv("EVALUATOR_INTERVAL_SECONDS", "300"))
    SIGNAL_EXPIRY_HOURS: int = int(os.getenv("SIGNAL_EXPIRY_HOURS", "48"))
    PRICE_PRIMARY_TICKER: str = os.getenv("PRICE_PRIMARY_TICKER", "GC=F")
    PRICE_FALLBACK_TICKER: str = os.getenv("PRICE_FALLBACK_TICKER", "XAUUSD=X")

    @property
    def is_telegram_configured(self) -> bool:
        return bool(self.TELEGRAM_API_ID and self.TELEGRAM_API_HASH and self.TELEGRAM_PHONE)

    @property
    def is_auth_configured(self) -> bool:
        return bool(self.ADMIN_USERNAME and self.ADMIN_PASSWORD and self.JWT_SECRET)


settings = Settings()
