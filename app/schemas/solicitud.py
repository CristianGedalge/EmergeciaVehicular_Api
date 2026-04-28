from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.models.solicitud import EstadoSolicitudEnum

class SolicitudResponse(BaseModel):
    id: int
    cliente_id: int
    vehiculo_id: int
    taller_id: Optional[int] = None
    mecanico_id: Optional[int] = None
    tipo_servicio_id: Optional[int] = None
    
    descripcion: Optional[str] = None
    urls_fotos: Optional[List[str]] = None
    latitud: float
    longitud: float
    
    precio_estimado: Optional[float] = None
    precio_final: Optional[float] = None
    
    estado: EstadoSolicitudEnum
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)

class AceptarSolicitudRequest(BaseModel):
    precio_estimado: float

class AsignarMecanicoRequest(BaseModel):
    mecanico_id: int
