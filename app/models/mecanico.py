from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey, Table
from sqlalchemy.sql import func
from app.models.base import Base


# Tabla intermedia: mecánico ↔ tipo_servicio (muchos a muchos)
mecanico_especialidad = Table(
    "mecanico_especialidad",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("mecanico_id", Integer, ForeignKey("mecanico.id"), nullable=False),
    Column("tipo_servicio_id", Integer, ForeignKey("tipo_servicio.id"), nullable=False),
)


class Mecanico(Base):
    __tablename__ = "mecanico"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    taller_id = Column(Integer, ForeignKey("taller.id"), nullable=False)
    latitud = Column(Numeric(10, 7), nullable=True)
    longitud = Column(Numeric(10, 7), nullable=True)
    disponible = Column(Boolean, default=True, nullable=False)
    estado = Column(Boolean, default=True, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
