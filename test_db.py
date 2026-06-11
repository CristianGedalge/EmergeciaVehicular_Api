import asyncio
from sqlalchemy.future import select
from app.config.db import AsyncSessionLocal
from app.models.taller import TipoServicio

async def test():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(TipoServicio))
        for t in res.scalars().all():
            print(f"ID: {t.id}, Nombre: '{t.nombre}'")

if __name__ == "__main__":
    asyncio.run(test())
