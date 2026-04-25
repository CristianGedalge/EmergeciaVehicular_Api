from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.db import get_db
from app.schemas.auth import (
    LoginRequest, RegisterRequest, TokenResponse,
    ForgotPasswordRequest, ResetPasswordRequest, RegisterAdminRequest, TokenUpdateRequest
)
from app.services.authServices import (
    autenticarUsuario, registrarUsuario,
    solicitarResetPassword, resetearPassword, registrarAdmin, actualizarFcmToken
)
from app.dependencies.auth import obtenerUsuarioActual


router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"]
)


@router.post("/register", status_code=201)
async def register(datos: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Registrar un nuevo usuario."""
    usuario = await registrarUsuario(db, datos)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo ya está registrado"
        )
    return {"message": "Usuario registrado exitosamente"}


@router.post("/login", response_model=TokenResponse)
async def login(datos: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Iniciar sesión y obtener token JWT."""
    token = await autenticarUsuario(db, datos.correo, datos.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=token)


@router.post("/forgot-password")
async def forgot_password(datos: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Solicitar recuperación de contraseña. Envía email con enlace de reset."""
    await solicitarResetPassword(db, datos.correo)
    # Siempre responde ok para no revelar si el correo existe o no (seguridad)
    return {"message": "Si el correo existe, se envió un enlace de recuperación"}


@router.post("/reset-password")
async def reset_password(datos: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Restablecer contraseña con el token recibido por email."""
    result = await resetearPassword(db, datos.token, datos.nueva_password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o expirado"
        )
    return {"message": "Contraseña actualizada exitosamente"}


@router.post("/register-admin", status_code=201)
async def register_admin(datos: RegisterAdminRequest, db: AsyncSession = Depends(get_db)):
    """Registrar un admin junto con su taller."""
    resultado = await registrarAdmin(db, datos)
    if not resultado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo ya está registrado"
        )
    return {
        "message": "Admin y taller registrados exitosamente",
        "accessToken": resultado["accessToken"]
    }


@router.put("/update-fcm-token")
async def update_fcm_token(
    datos: TokenUpdateRequest,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(obtenerUsuarioActual)
):
    """Actualizar el fcm_token para notificaciones push."""
    usuario_id = int(usuario.get("sub"))
    result = await actualizarFcmToken(db, usuario_id, datos.fcm_token)
    if not result:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"message": "Token FCM actualizado correctamente"}

