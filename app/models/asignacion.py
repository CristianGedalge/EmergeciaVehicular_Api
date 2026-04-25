from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class AsignacionAuxilio(Base):
    __tablename__ = "asignacion_auxilio"

    id = Column(Integer, primary_key=True, autoincrement=True)
    solicitud_id = Column(Integer, ForeignKey("solicitud_auxilio.id"), nullable=False, unique=True)
    taller_id = Column(Integer, ForeignKey("taller.id"), nullable=False)
    mecanico_id = Column(Integer, ForeignKey("mecanico.id"), nullable=False)
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_fin = Column(DateTime(timezone=True), nullable=True)
