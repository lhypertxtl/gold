import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.config import settings

COOKIE_NAME = "gold_session"
ALGORITHM = "HS256"
bearer_scheme = HTTPBearer(auto_error=False)


def _get_jwt_secret() -> str:
    if not settings.JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Autenticación no configurada: defina ADMIN_USERNAME, ADMIN_PASSWORD y JWT_SECRET en .env",
        )
    return settings.JWT_SECRET


def verify_admin_credentials(username: str, password: str) -> bool:
    if not settings.is_auth_configured:
        return False
    user_ok = hmac.compare_digest(username.strip(), settings.ADMIN_USERNAME.strip())
    pass_ok = hmac.compare_digest(password, settings.ADMIN_PASSWORD)
    return user_ok and pass_ok


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": username,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, _get_jwt_secret(), algorithm=ALGORITHM)


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> str:
    token: Optional[str] = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    else:
        token = request.cookies.get(COOKIE_NAME)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión no iniciada o expirada",
        )

    try:
        payload = jwt.decode(token, _get_jwt_secret(), algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if not username or username != settings.ADMIN_USERNAME:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no autorizado",
            )
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión ha expirado. Inicia sesión nuevamente.",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de sesión inválido",
        )
