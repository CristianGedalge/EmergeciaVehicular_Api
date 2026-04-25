from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from app.models.base import Base
import enum


class EstadoSolicitudEnum(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    CLASIFICADO = "CLASIFICADO"
    PUBLICADO = "PUBLICADO"
    ASIGNADO = "ASIGNADO"
    EN_CAMINO = "EN_CAMINO"
    EN_SITIO = "EN_SITIO"
    FINALIZADO = "FINALIZADO"
    CANCELADO = "CANCELADO"


class SolicitudAuxilio(Base):
    __tablename__ = "solicitud_auxilio"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    vehiculo_id = Column(Integer, ForeignKey("vehiculo.id"), nullable=False)
    tipo_servicio_id = Column(Integer, ForeignKey("tipo_servicio.id"), nullable=True) # Mapped later by IA
    descripcion = Column(Text, nullable=True)
    url_img = Column(Text, nullable=True)
    url_audio = Column(Text, nullable=True)
    latitud = Column(Numeric(10, 7), nullable=False)
    longitud = Column(Numeric(10, 7), nullable=False)
    estado = Column(SQLEnum(EstadoSolicitudEnum), default=EstadoSolicitudEnum.PENDIENTE, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
