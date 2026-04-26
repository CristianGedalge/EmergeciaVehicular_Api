from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class VehiculoBase(BaseModel):
    marca: str
    modelo: str
    anio: int
    placa: str
    color: Optional[str] = None

class VehiculoCreate(VehiculoBase):
    pass

class VehiculoUpdate(BaseModel):
    marca: Optional[str] = None
    modelo: Optional[str] = None
    anio: Optional[int] = None
    placa: Optional[str] = None
    color: Optional[str] = None

class VehiculoResponse(VehiculoBase):
    id: int
    cliente_id: int
    estado: bool
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)
