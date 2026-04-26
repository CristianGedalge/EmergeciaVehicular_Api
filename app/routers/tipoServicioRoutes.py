from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.config.db import get_db
from app.dependencies.auth import obtenerUsuarioActual
from app.dependencies.rolCheck import RequireRole
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
async def listarTipos(db: AsyncSession = Depends(get_db)):
    """Listar todos los tipos de servicio activos."""
    return await listarTiposServicio(db)


@router.get("/{tipoId}", response_model=TipoServicioResponse)
async def obtenerTipo(tipoId: int, db: AsyncSession = Depends(get_db)):
    """Obtener un tipo de servicio por ID."""
    tipo = await obtenerTipoServicio(db, tipoId)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de servicio no encontrado")
    return tipo


@router.post("/", response_model=TipoServicioResponse, status_code=201)
async def crearTipo(
    datos: TipoServicioCreate,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["superadmin"]))
):
    """Crear un tipo de servicio (solo superadmins)."""
    return await crearTipoServicio(db, datos)


@router.put("/{tipoId}", response_model=TipoServicioResponse)
async def actualizarTipo(
    tipoId: int,
    datos: TipoServicioUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["superadmin"]))
):
    """Actualizar un tipo de servicio (solo superadmins)."""
    tipo = await actualizarTipoServicio(db, tipoId, datos)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de servicio no encontrado")
    return tipo


@router.delete("/{tipoId}", response_model=TipoServicioResponse)
async def eliminarTipo(
    tipoId: int,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["superadmin"]))
):
    """Eliminación lógica (solo superadmins)."""
    tipo = await eliminarTipoServicio(db, tipoId)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de servicio no encontrado")
    return tipo
