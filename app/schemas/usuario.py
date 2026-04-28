from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.usuario import RolEnum

class UsuarioBase(BaseModel):
    nombre: str
    correo: EmailStr
    telefono: Optional[str] = None
    url_img: Optional[str] = None
    rol: RolEnum

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    url_img: Optional[str] = None
    rol: Optional[RolEnum] = None
    estado: Optional[bool] = None

class UsuarioResponse(UsuarioBase):
    id: int
    estado: bool
    fecha_creacion: datetime

    model_config = {"from_attributes": True}
