"""
Configuración y utilidades JWT.
Firma los tokens con la clave SECRET_KEY definida en .env.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from dotenv import load_dotenv
from jose import JWTError, jwt
from fastapi import HTTPException, status

load_dotenv()

# ── Configuración JWT ──────────────────────────────────────────────
SECRET_KEY: str = os.getenv("SECRET_KEY", "icorebiz")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS: int = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "12")
)
RESET_TOKEN_EXPIRE_MINUTES: int = int(
    os.getenv("RESET_TOKEN_EXPIRE_MINUTES", "30")
)


# ── Crear token ────────────────────────────────────────────────────
def crear_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Genera un JWT firmado.
    `data` debe contener al menos {"sub": <user_id o email>}.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ── Verificar / decodificar token ─────────────────────────────────
def verificar_token(token: str) -> dict:
    """Decodifica y valida un JWT. Lanza HTTPException 401 si falla."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
