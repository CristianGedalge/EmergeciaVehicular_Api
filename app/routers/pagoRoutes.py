from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.db import get_db
from app.schemas.pago import CrearPaymentIntentRequest, PaymentIntentResponse, ConfirmarPagoRequest
from app.services.pagoServices import PagoService

router = APIRouter(prefix="/pagos", tags=["Pagos (Stripe)"])

@router.post("/intent", response_model=PaymentIntentResponse)
async def create_payment_intent(req: CrearPaymentIntentRequest, db: AsyncSession = Depends(get_db)):
    """
    Crea un PaymentIntent en Stripe. Guarda los cobros extra en la BD y calcula el precio final.
    """
    return await PagoService.create_payment_intent(db, req)

@router.post("/confirmar")
async def confirmar_pago(req: ConfirmarPagoRequest, db: AsyncSession = Depends(get_db)):
    """
    Se llama desde la app móvil cuando Stripe confirma que el pago con tarjeta fue exitoso.
    Cambia el estado de la solicitud a FINALIZADO y registra el pago en la BD.
    """
    return await PagoService.confirmar_pago(db, req)
