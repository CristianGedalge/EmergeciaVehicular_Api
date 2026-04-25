from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.usuario import RolEnum


class LoginRequest(BaseModel):
    correo: EmailStr
    password: str


class RegisterRequest(BaseModel):
    nombre: str
    correo: EmailStr
    password: str
    telefono: Optional[str] = None
    rol: Optional[RolEnum] = RolEnum.CLIENTE
    fcm_token: Optional[str] = None
    url_img: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    correo: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    nueva_password: str


class TallerInfo(BaseModel):
    nombre: str
    direccion: str
    telefono: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None


class RegisterAdminRequest(BaseModel):
    nombre: str
    correo: EmailStr
    password: str
    telefono: Optional[str] = None
    taller: TallerInfo
    fcm_token: Optional[str] = None
    url_img: Optional[str] = None


class TokenUpdateRequest(BaseModel):
    fcm_token: str

