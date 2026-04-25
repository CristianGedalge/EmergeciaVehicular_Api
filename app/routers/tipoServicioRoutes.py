from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.config.db import get_db
from app.dependencies.auth import obtenerUsuarioActual
from app.schemas.tipo_servicio import TipoServicioCreate, TipoServicioUpdate, TipoServicioResponse
from app.services.tipoServicioServices import (
    listarTiposServicio, obtenerTipoServicio, crearTipoServicio,
    actualizarTipoServicio, eliminarTipoServicio
)

router = APIRouter(
    prefix="/tipos-servicio",
    tags=["Tipos de Servicio"]
)


@router.get("/", response_model=List[TipoServicioResponse])
async def listar(db: AsyncSession = Depends(get_db)):
    """Listar todos los tipos de servicio activos."""
    return await listarTiposServicio(db)


@router.get("/{tipo_id}", response_model=TipoServicioResponse)
async def obtener(tipo_id: int, db: AsyncSession = Depends(get_db)):
    """Obtener un tipo de servicio por ID."""
    tipo = await obtenerTipoServicio(db, tipo_id)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de servicio no encontrado")
    return tipo


@router.post("/", response_model=TipoServicioResponse, status_code=201)
async def crear(
    datos: TipoServicioCreate,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(obtenerUsuarioActual)
):
    """Crear un tipo de servicio (solo admins)."""
    if usuario.get("rol") != "admin":
        raise HTTPException(status_code=403, detail="Solo admins pueden crear tipos de servicio")
    return await crearTipoServicio(db, datos)


@router.put("/{tipo_id}", response_model=TipoServicioResponse)
async def actualizar(
    tipo_id: int,
    datos: TipoServicioUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(obtenerUsuarioActual)
):
    """Actualizar un tipo de servicio."""
    tipo = await actualizarTipoServicio(db, tipo_id, datos)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de servicio no encontrado")
    return tipo


@router.delete("/{tipo_id}", response_model=TipoServicioResponse)
async def eliminar(
    tipo_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(obtenerUsuarioActual)
):
    """Eliminación lógica."""
    tipo = await eliminarTipoServicio(db, tipo_id)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de servicio no encontrado")
    return tipo
