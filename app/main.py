
from fastapi import FastAPI, Depends
from app.routers import example_router
from app.config.db import async_engine

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código que se ejecuta al iniciar la app
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(lambda conn: None)
        print("Conexión a la base de datos exitosa.")
    except Exception as e:
        print("Error al conectar con la base de datos en el arranque:", e)
    yield
    # Código que se ejecuta al cerrar la app 
app = FastAPI(lifespan=lifespan)

# Incluye tus routers aquí
app.include_router(example_router.router)

@app.get("/")
def root():
    return {"message": "API de Emergencia Vehicular funcionando"}
