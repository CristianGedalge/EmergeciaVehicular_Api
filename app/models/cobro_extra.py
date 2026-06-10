from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.models.base import Base

class CobroExtra(Base):
    __tablename__ = "cobro_extra"

    id = Column(Integer, primary_key=True, autoincrement=True)
    solicitud_id = Column(Integer, ForeignKey("solicitud.id"), nullable=False)
    concepto = Column(String(255), nullable=False)
    monto = Column(Float, nullable=False)
