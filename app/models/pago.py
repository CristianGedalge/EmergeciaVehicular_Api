from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from app.models.base import Base
import enum


class MetodoPagoEnum(str, enum.Enum):
    QR = "QR"
    TARJETA = "TARJETA"
    EFECTIVO = "EFECTIVO"


class EstadoPagoEnum(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    COMPLETADO = "COMPLETADO"
    FALLIDO = "FALLIDO"


class Pago(Base):
    __tablename__ = "pago"

    id = Column(Integer, primary_key=True, autoincrement=True)
    solicitud_id = Column(Integer, ForeignKey("solicitud.id"), nullable=False, unique=True)
    monto = Column(Numeric(10, 2), nullable=False)
    metodo_pago = Column(SQLEnum(MetodoPagoEnum), nullable=False)
    estado_pago = Column(SQLEnum(EstadoPagoEnum), default=EstadoPagoEnum.PENDIENTE, nullable=False)
    stripe_payment_id = Column(String(255), nullable=True)
    fecha_pago = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
