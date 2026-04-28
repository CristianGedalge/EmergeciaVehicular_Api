from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.config.db import get_db
from app.dependencies.rolCheck import RequireRole
from app.schemas.usuario import UsuarioUpdate, UsuarioResponse
from app.services.usuarioServices import (
    listarUsuarios, obtenerUsuario, actualizarUsuario, eliminarUsuario
)

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)


@router.get("/", response_model=List[UsuarioResponse])
async def listar(
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["superadmin"]))
):
    """Listar todos los usuarios. Solo disponible para superadmin."""
    return await listarUsuarios(db)


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def obtener(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["superadmin"]))
):
    """Obtener un usuario por ID."""
    user = await obtenerUsuario(db, usuario_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def actualizar(
    usuario_id: int,
    datos: UsuarioUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["superadmin"]))
):
    """Actualizar datos generales de un usuario."""
    user = await actualizarUsuario(db, usuario_id, datos)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.delete("/{usuario_id}", response_model=UsuarioResponse)
async def eliminar(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["superadmin"]))
):
    """Eliminación lógica de un usuario (Actualiza tabla Mecanico en cascada si aplica)."""
    user = await eliminarUsuario(db, usuario_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user
