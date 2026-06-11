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
    fecha_aceptado: Optional[datetime] = None
    fecha_en_camino: Optional[datetime] = None
    fecha_en_sitio: Optional[datetime] = None
    
    # Campos adicionales para vista rápida
    placa_vehiculo: Optional[str] = None
    nombre_servicio: Optional[str] = None
    estado_pago: Optional[str] = None
    taller_nombre: Optional[str] = None
    nombre_mecanico: Optional[str] = None
    telefono_mecanico: Optional[str] = None
    cliente_nombre: Optional[str] = None
    vehiculo_marca: Optional[str] = None
    vehiculo_modelo: Optional[str] = None
    vehiculo_anio: Optional[int] = None
    vehiculo_color: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class AceptarSolicitudRequest(BaseModel):
    precio_estimado: float

class AsignarMecanicoRequest(BaseModel):
    mecanico_id: int

class CobroExtraSchema(BaseModel):
    concepto: str
    monto: float

class FinalizarServicioRequest(BaseModel):
    precio_final: float
    metodo_pago: str = "TARJETA" # TARJETA, EFECTIVO, QR
