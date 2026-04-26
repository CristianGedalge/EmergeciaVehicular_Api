"""
Dependencias de autenticación y autorización.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.config.auth import verificar_token

# Esquema OAuth2 – apunta al endpoint de login para la documentación interactiva
# Al usar root_path="/api", la ruta relativa /auth/login es suficiente.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def obtenerUsuarioActual(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Inyecta el payload del token decodificado en la ruta.
    """
    return verificar_token(token)


