from pydantic import BaseModel
from typing import List, Optional

class CrearPaymentIntentRequest(BaseModel):
    solicitud_id: int
    monto_pagar: float

class PaymentIntentResponse(BaseModel):
    client_secret: str
    precio_final: float

class ConfirmarPagoRequest(BaseModel):
    solicitud_id: int
    stripe_payment_id: str
