import os
import stripe
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models.solicitud import Solicitud, EstadoSolicitudEnum
from app.models.pago import Pago, MetodoPagoEnum, EstadoPagoEnum
from app.models.cobro_extra import CobroExtra
from app.schemas.pago import CrearPaymentIntentRequest, PaymentIntentResponse, ConfirmarPagoRequest
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class PagoService:
    @staticmethod
    async def create_payment_intent(db: AsyncSession, req: CrearPaymentIntentRequest) -> PaymentIntentResponse:
        # Verificar que la api key esté configurada
        if not stripe.api_key:
            raise HTTPException(status_code=500, detail="STRIPE_SECRET_KEY no configurado en .env")

        # Buscar solicitud
        result = await db.execute(select(Solicitud).where(Solicitud.id == req.solicitud_id))
        solicitud = result.scalars().first()
        
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
            
        # Permitir pagar si el estado es EN_SITIO o FINALIZADO
        if solicitud.estado not in [EstadoSolicitudEnum.EN_SITIO, EstadoSolicitudEnum.FINALIZADO]:
            raise HTTPException(status_code=400, detail="La solicitud no está en estado válido para pago")

        # Si ya está FINALIZADO, los cobros extra ya fueron guardados por el mecánico.
        # Si está EN_SITIO, el cliente está pagando antes de que el mecánico finalice.
        if solicitud.estado == EstadoSolicitudEnum.EN_SITIO:
            precio_estimado = float(solicitud.precio_estimado or 0.0)
            total_extra = sum(extra.monto for extra in req.cobros_extra)
            precio_final = precio_estimado + total_extra

            # Guardar cobros extra en la BD
            for extra in req.cobros_extra:
                nuevo_cobro = CobroExtra(
                    solicitud_id=solicitud.id,
                    concepto=extra.concepto,
                    monto=extra.monto
                )
                db.add(nuevo_cobro)

            # Actualizar precio final en la solicitud
            solicitud.precio_final = precio_final
            await db.commit()
        else:
            # Si ya está finalizado, usamos el precio que el mecánico definió
            precio_final = float(solicitud.precio_final or solicitud.precio_estimado or 0.0)
            precio_estimado = float(solicitud.precio_estimado or 0.0)
            total_extra = precio_final - precio_estimado

        # Crear PaymentIntent en Stripe
        try:
            # Stripe usa centavos (ej: 100 Bs = 10000)
            amount_in_cents = int(precio_final * 100)
            
            intent = stripe.PaymentIntent.create(
                amount=amount_in_cents,
                currency="bob", # bolivianos
                metadata={
                    "solicitud_id": solicitud.id,
                    "cliente_id": solicitud.cliente_id
                }
            )
            
            return PaymentIntentResponse(
                client_secret=intent.client_secret,
                precio_estimado=precio_estimado,
                total_extra=total_extra,
                precio_final=precio_final
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def confirmar_pago(db: AsyncSession, req: ConfirmarPagoRequest):
        # Buscar solicitud
        result = await db.execute(select(Solicitud).where(Solicitud.id == req.solicitud_id))
        solicitud = result.scalars().first()
        
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")

        # Verificar si ya existe un registro de Pago
        result_pago = await db.execute(select(Pago).where(Pago.solicitud_id == solicitud.id))
        pago_existente = result_pago.scalars().first()

        if pago_existente:
            pago_existente.estado_pago = EstadoPagoEnum.COMPLETADO
            pago_existente.stripe_payment_id = req.stripe_payment_id
            pago_existente.metodo_pago = MetodoPagoEnum.TARJETA
            pago_id = pago_existente.id
        else:
            # Crear registro de Pago
            nuevo_pago = Pago(
                solicitud_id=solicitud.id,
                monto=solicitud.precio_final,
                metodo_pago=MetodoPagoEnum.TARJETA,
                estado_pago=EstadoPagoEnum.COMPLETADO,
                stripe_payment_id=req.stripe_payment_id
            )
            db.add(nuevo_pago)
            pago_id = nuevo_pago.id

        # Cambiar estado de solicitud a FINALIZADO
        solicitud.estado = EstadoSolicitudEnum.FINALIZADO
        
        await db.commit()
        return {"mensaje": "Pago confirmado y servicio finalizado", "pago_id": pago_id}
