from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TallerCreate(BaseModel):
    nombre: str
    direccion: str
    telefono: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None


class TallerUpdate(BaseModel):
    nombre: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None


class TallerResponse(BaseModel):
    id: int
    nombre: str
    direccion: str
    telefono: Optional[str]
    latitud: Optional[float]
    longitud: Optional[float]
    admin_id: int
    estado: bool
    fecha_creacion: datetime

    model_config = {"from_attributes": True}
