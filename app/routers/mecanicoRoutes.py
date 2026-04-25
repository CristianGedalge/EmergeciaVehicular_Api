from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.config.db import get_db
from app.dependencies.auth import obtenerUsuarioActual
from app.schemas.mecanico import MecanicoCreate, MecanicoUpdate, MecanicoResponse
from app.services.mecanicoServices import (
    listarMecanicos, obtenerMecanico, crearMecanico, actualizarMecanico, eliminarMecanico
)

router = APIRouter(
    prefix="/mecanicos",
    tags=["Mecánicos"]
)


@router.get("/", response_model=List[MecanicoResponse])
async def listar(
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(obtenerUsuarioActual)
):
    """Listar mecánicos del taller del admin autenticado."""
    taller_id = usuario.get("tallerId")
    if not taller_id:
        raise HTTPException(status_code=403, detail="No tenés un taller asignado")
    return await listarMecanicos(db, taller_id)


@router.get("/{mecanico_id}", response_model=MecanicoResponse)
async def obtener(
    mecanico_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(obtenerUsuarioActual)
):
    """Obtener un mecánico por ID."""
    mecanico = await obtenerMecanico(db, mecanico_id)
    if not mecanico:
        raise HTTPException(status_code=404, detail="Mecánico no encontrado")
    return mecanico


@router.post("/", response_model=MecanicoResponse, status_code=201)
async def crear(
    datos: MecanicoCreate,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(obtenerUsuarioActual)
):
    """Registrar un mecánico (solo admin). El tallerId se toma del token."""
    if usuario.get("rol") != "admin":
        raise HTTPException(status_code=403, detail="Solo admins pueden registrar mecánicos")
    taller_id = usuario.get("tallerId")
    if not taller_id:
        raise HTTPException(status_code=403, detail="No tenés un taller asignado")
    mecanico = await crearMecanico(db, taller_id, datos)
    if not mecanico:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    return mecanico


@router.put("/{mecanico_id}", response_model=MecanicoResponse)
async def actualizar(
    mecanico_id: int,
    datos: MecanicoUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(obtenerUsuarioActual)
):
    """Actualizar mecánico (ubicación, disponibilidad, especialidades)."""
    mecanico = await actualizarMecanico(db, mecanico_id, datos)
    if not mecanico:
        raise HTTPException(status_code=404, detail="Mecánico no encontrado")
    return mecanico


@router.delete("/{mecanico_id}", response_model=MecanicoResponse)
async def eliminar(
    mecanico_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(obtenerUsuarioActual)
):
    """Eliminación lógica de mecánico."""
    if usuario.get("rol") != "admin":
        raise HTTPException(status_code=403, detail="Solo admins pueden eliminar mecánicos")
    mecanico = await eliminarMecanico(db, mecanico_id)
    if not mecanico:
        raise HTTPException(status_code=404, detail="Mecánico no encontrado")
    return mecanico
