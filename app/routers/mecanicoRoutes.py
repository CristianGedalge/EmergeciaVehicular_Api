from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.config.db import get_db
from app.dependencies.auth import obtenerUsuarioActual
from app.dependencies.rolCheck import RequireRole
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
    usuario: dict = Depends(RequireRole(["admin", "superadmin", "mecanico"]))
):
    """Listar mecánicos (Admin/Mecánico ve su taller, SuperAdmin ve todos)."""
    taller_id = usuario.get("tallerId")
    rol = usuario.get("rol")

    if rol == "superadmin":
        return await listarMecanicos(db, taller_id)
    
    if not taller_id:
        raise HTTPException(status_code=403, detail="No tienes un taller asignado")
    
    return await listarMecanicos(db, taller_id)


@router.get("/{mecanico_id}", response_model=MecanicoResponse)
async def obtener(
    mecanico_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["admin", "superadmin", "mecanico"]))
):
    """Obtener un mecánico por ID."""
    mecanico = await obtenerMecanico(db, mecanico_id)
    if not mecanico:
        raise HTTPException(status_code=404, detail="Mecánico no encontrado")
    
    rol = usuario.get("rol")
    taller_id = usuario.get("tallerId")

    if rol != "superadmin" and mecanico.taller_id != taller_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver este mecánico")
        
    return mecanico


@router.post("/", response_model=MecanicoResponse, status_code=201)
async def crear(
    datos: MecanicoCreate,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["admin", "superadmin"]))
):
    """Registrar un mecánico."""
    taller_id = usuario.get("tallerId")
    mecanico = await crearMecanico(db, taller_id, datos)
    if not mecanico:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    return mecanico


@router.put("/{mecanico_id}", response_model=MecanicoResponse)
async def actualizar(
    mecanico_id: int,
    datos: MecanicoUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["admin", "superadmin", "mecanico"]))
):
    """Actualizar mecánico."""
    mecanico = await obtenerMecanico(db, mecanico_id)
    if not mecanico:
        raise HTTPException(status_code=404, detail="Mecánico no encontrado")

    rol = usuario.get("rol")
    taller_id = usuario.get("tallerId")

    if rol != "superadmin" and mecanico.taller_id != taller_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar este mecánico")

    mecanico_upd = await actualizarMecanico(db, mecanico_id, datos)
    return mecanico_upd


@router.delete("/{mecanico_id}", response_model=MecanicoResponse)
async def eliminar(
    mecanico_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["admin", "superadmin"]))
):
    """Eliminación lógica de mecánico."""
    mecanico = await obtenerMecanico(db, mecanico_id)
    if not mecanico:
        raise HTTPException(status_code=404, detail="Mecánico no encontrado")

    rol = usuario.get("rol")
    taller_id = usuario.get("tallerId")

    if rol != "superadmin" and mecanico.taller_id != taller_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este mecánico")

    return await eliminarMecanico(db, mecanico_id)
