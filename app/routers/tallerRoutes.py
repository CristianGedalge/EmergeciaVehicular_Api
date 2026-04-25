from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.config.db import get_db
from app.dependencies.auth import obtenerUsuarioActual
from app.schemas.taller import TallerCreate, TallerUpdate, TallerResponse
from app.services.tallerServices import (
    listarTalleres, obtenerTaller, crearTaller, actualizarTaller, eliminarTaller
)

router = APIRouter(
    prefix="/talleres",
    tags=["Talleres"]
)


@router.get("/", response_model=List[TallerResponse])
async def listar(db: AsyncSession = Depends(get_db)):
    """Obtener todos los talleres activos."""
    return await listarTalleres(db)


@router.get("/{taller_id}", response_model=TallerResponse)
async def obtener(taller_id: int, db: AsyncSession = Depends(get_db)):
    """Obtener un taller por ID."""
    taller = await obtenerTaller(db, taller_id)
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    return taller


@router.post("/", response_model=TallerResponse, status_code=201)
async def crear(
    datos: TallerCreate,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(obtenerUsuarioActual)
):
    """Crear un taller (solo admins). El admin_id se toma del token."""
    if usuario.get("rol") != "admin":
        raise HTTPException(status_code=403, detail="Solo los admins pueden crear talleres")
    return await crearTaller(db, datos, admin_id=int(usuario["sub"]))


@router.put("/{taller_id}", response_model=TallerResponse)
async def actualizar(
    taller_id: int,
    datos: TallerUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(obtenerUsuarioActual)
):
    """Actualizar un taller."""
    taller = await actualizarTaller(db, taller_id, datos)
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    return taller


@router.delete("/{taller_id}", response_model=TallerResponse)
async def eliminar(
    taller_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(obtenerUsuarioActual)
):
    """Eliminación lógica de un taller."""
    taller = await eliminarTaller(db, taller_id)
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    return taller
