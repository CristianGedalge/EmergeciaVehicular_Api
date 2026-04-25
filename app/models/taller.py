from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class Taller(Base):
    __tablename__ = "taller"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(150), nullable=False)
    direccion = Column(String(255), nullable=False)
    telefono = Column(String(20), nullable=True)
    latitud = Column(Numeric(10, 7), nullable=True)
    longitud = Column(Numeric(10, 7), nullable=True)
    admin_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    estado = Column(Boolean, default=True, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
