from pydantic import BaseModel
from typing import List, Optional

class CobroExtraCreate(BaseModel):
    concepto: str
    monto: float

class CrearPaymentIntentRequest(BaseModel):
    solicitud_id: int
    cobros_extra: List[CobroExtraCreate] = []

class PaymentIntentResponse(BaseModel):
    client_secret: str
    precio_estimado: float
    total_extra: float
    precio_final: float

class ConfirmarPagoRequest(BaseModel):
    solicitud_id: int
    stripe_payment_id: str
