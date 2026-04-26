from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from app.models.base import Base
import enum


class EstadoSolicitudEnum(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    CLASIFICADO = "CLASIFICADO"
    PUBLICADO = "PUBLICADO"
    ACEPTADO = "ACEPTADO"
    ASIGNADO = "ASIGNADO"
    EN_CAMINO = "EN_CAMINO"
    EN_SITIO = "EN_SITIO"
    FINALIZADO = "FINALIZADO"
    CANCELADO = "CANCELADO"


class Solicitud(Base):
    __tablename__ = "solicitud"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    vehiculo_id = Column(Integer, ForeignKey("vehiculo.id"), nullable=False)
    taller_id = Column(Integer, ForeignKey("taller.id"), nullable=True)
    mecanico_id = Column(Integer, ForeignKey("mecanico.id"), nullable=True)
    tipo_servicio_id = Column(Integer, ForeignKey("tipo_servicio.id"), nullable=True)

    descripcion = Column(Text, nullable=True)
    # Campo tipo Arreglo para múltiples fotos en una sola fila
    urls_fotos = Column(ARRAY(Text), nullable=True)
    
    latitud = Column(Numeric(10, 7), nullable=False)
    longitud = Column(Numeric(10, 7), nullable=False)
    
    precio_estimado = Column(Float, nullable=True)
    precio_final = Column(Float, nullable=True)

    estado = Column(SQLEnum(EstadoSolicitudEnum), default=EstadoSolicitudEnum.PENDIENTE, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
