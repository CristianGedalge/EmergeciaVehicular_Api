from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class Notificacion(Base):
    __tablename__ = "notificacion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    titulo = Column(String(150), nullable=False)
    mensaje = Column(Text, nullable=False)
    leido = Column(Boolean, default=False, nullable=False)
    fecha_envio = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
