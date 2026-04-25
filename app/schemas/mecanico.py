from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class MecanicoCreate(BaseModel):
    nombre: str
    correo: str
    password: str
    telefono: Optional[str] = None
    especialidades: List[int] = []  # IDs de tipo_servicio


class MecanicoUpdate(BaseModel):
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    disponible: Optional[bool] = None
    especialidades: Optional[List[int]] = None


class MecanicoResponse(BaseModel):
    id: int
    usuario_id: int
    taller_id: int
    latitud: Optional[float]
    longitud: Optional[float]
    disponible: bool
    estado: bool
    fecha_creacion: datetime

    model_config = {"from_attributes": True}
