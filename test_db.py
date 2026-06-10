import asyncio
from app.config.db import async_session
from sqlalchemy import select
from app.models.pago import Pago
from app.models.solicitud import Solicitud

async def main():
    async with async_session() as db:
        result = await db.execute(select(Pago))
        pagos = result.scalars().all()
        for p in pagos:
            print(f"Pago ID: {p.id}, Solicitud ID: {p.solicitud_id}, Estado: {p.estado_pago.value if p.estado_pago else None}, Metodo: {p.metodo_pago.value if p.metodo_pago else None}, Stripe ID: {p.stripe_payment_id}")
            
        result = await db.execute(select(Solicitud))
        solicitudes = result.scalars().all()
        for s in solicitudes:
            print(f"Solicitud ID: {s.id}, Estado: {s.estado.value if s.estado else None}")

asyncio.run(main())
