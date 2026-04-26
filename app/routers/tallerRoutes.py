from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.config.db import get_db
from app.dependencies.auth import obtenerUsuarioActual
from app.dependencies.rolCheck import RequireRole
from app.schemas.taller import TallerCreate, TallerUpdate, TallerResponse
from app.services.tallerServices import (
    listarTalleres, obtenerTaller, crearTaller, actualizarTaller, eliminarTaller
)

router = APIRouter(
    prefix="/talleres",
    tags=["Talleres"]
)


@router.get("/", response_model=List[TallerResponse])
async def listarTalleresRoute(
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["superadmin", "cliente"]))
):
    """Obtener todos los talleres activos (Requiere estar logueado)."""
    return await listarTalleres(db)


@router.get("/{tallerId}", response_model=TallerResponse)
async def obtenerTallerRoute(
    tallerId: int, 
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["superadmin", "admin", "cliente", "mecanico"]))
):
    """Obtener un taller por ID (Requiere estar logueado)."""
    taller = await obtenerTaller(db, tallerId)
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    return taller


@router.post("/", response_model=TallerResponse, status_code=201)
async def crearTallerRoute(
    datos: TallerCreate,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["admin"]))
):
    """Crear un taller (solo admins). El admin_id se toma del token."""
    return await crearTaller(db, datos, admin_id=int(usuario["sub"]))


@router.put("/{tallerId}", response_model=TallerResponse)
async def actualizarTallerRoute(
    tallerId: int,
    datos: TallerUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["admin", "superadmin"]))
):
    """Actualizar un taller (Solo SuperAdmin o Admin dueño del taller)."""
    rol = usuario.get("rol")
    userTallerId = usuario.get("tallerId")

    # Validación de propiedad
    if rol != "superadmin" and userTallerId != tallerId:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este taller"
        )

    taller = await actualizarTaller(db, tallerId, datos)
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    return taller


@router.delete("/{tallerId}", response_model=TallerResponse)
async def eliminarTallerRoute(
    tallerId: int,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["admin", "superadmin"]))
):
    """Eliminación lógica de un taller (Solo SuperAdmin o Admin dueño del taller)."""
    rol = usuario.get("rol")
    userTallerId = usuario.get("tallerId")

    # Validación de propiedad
    if rol != "superadmin" and userTallerId != tallerId:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este taller"
        )

    taller = await eliminarTaller(db, tallerId)
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    return taller
