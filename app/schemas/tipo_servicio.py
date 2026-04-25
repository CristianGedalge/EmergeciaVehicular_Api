from pydantic import BaseModel
from typing import Optional


class TipoServicioCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    palabras_clave: Optional[str] = None


class TipoServicioUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    palabras_clave: Optional[str] = None


class TipoServicioResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    palabras_clave: Optional[str]
    estado: bool

    model_config = {"from_attributes": True}
