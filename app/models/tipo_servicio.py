from sqlalchemy import Column, Integer, String, Text, Boolean
from app.models.base import Base


class TipoServicio(Base):
    __tablename__ = "tipo_servicio"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=True)
    palabras_clave = Column(Text, nullable=True)  # Ayuda a la IA: "llanta,pinchada,rueda"
    estado = Column(Boolean, default=True, nullable=False)
