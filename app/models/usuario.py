from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.models.base import Base
import enum


class RolEnum(str, enum.Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    MECANICO = "mecanico"
    CLIENTE = "cliente"


class Usuario(Base):
    __tablename__ = "usuario"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(150), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    telefono = Column(String(20), nullable=True)
    url_img = Column(String(255), nullable=True)
    rol = Column(String(20), nullable=False, default=RolEnum.CLIENTE)
    estado = Column(Boolean, default=True, nullable=False)
    fcm_token = Column(String(255), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
