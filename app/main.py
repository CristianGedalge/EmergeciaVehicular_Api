from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config.db import async_engine
from app.models.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas al iniciar la app
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Tablas creadas / verificadas correctamente.")
    except Exception as e:
        print("Error al conectar con la base de datos:", e)
    yield
    # Cleanup al cerrar


app = FastAPI(
    title="API Emergencia Vehicular",
    description="API con eliminación lógica",
    version="1.0.0",
    lifespan=lifespan,
    root_path="/api"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from app.routers import authRoutes, tallerRoutes, mecanicoRoutes, tipoServicioRoutes, vehiculoRoutes, solicitudRoutes, usuarioRoutes
app.include_router(authRoutes.router)
app.include_router(tallerRoutes.router)
app.include_router(mecanicoRoutes.router)
app.include_router(tipoServicioRoutes.router)
app.include_router(vehiculoRoutes.router)
app.include_router(solicitudRoutes.router)
app.include_router(usuarioRoutes.router)


@app.get("/")
def root():
    return {"message": "API de Emergencia Vehicular funcionando"}
