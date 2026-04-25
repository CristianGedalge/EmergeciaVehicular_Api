"""
Dependencias de autenticación para rutas protegidas.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.config.auth import verificar_token

# Esquema OAuth2 – apunta al endpoint de login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def obtenerUsuarioActual(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Inyecta en la ruta el payload del usuario autenticado.
    Uso:
        @router.get("/ruta-protegida")
        async def ruta(usuario: dict = Depends(obtenerUsuarioActual)):
            ...
    """
    return verificar_token(token)
