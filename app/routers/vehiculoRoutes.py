from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.config.db import get_db
from app.dependencies.auth import obtenerUsuarioActual
from app.dependencies.rolCheck import RequireRole
from app.schemas.vehiculo import VehiculoCreate, VehiculoUpdate, VehiculoResponse
from app.services.vehiculoServices import (
    listarVehiculos, obtenerVehiculo, crearVehiculo, actualizarVehiculo, eliminarVehiculo
)

router = APIRouter(
    prefix="/vehiculos",
    tags=["Vehículos"]
)


@router.get("/", response_model=List[VehiculoResponse])
async def listarVehiculosRoute(
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["cliente", "superadmin"]))
):
    """Listar mis vehículos (como cliente)."""
    clienteId = int(usuario["sub"])
    return await listarVehiculos(db, clienteId)


@router.post("/", response_model=VehiculoResponse, status_code=201)
async def crearVehiculoRoute(
    datos: VehiculoCreate,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["cliente"]))
):
    """Registrar un nuevo vehículo."""
    clienteId = int(usuario["sub"])
    vehiculo = await crearVehiculo(db, clienteId, datos)
    if not vehiculo:
        raise HTTPException(status_code=400, detail="La placa ya está registrada")
    return vehiculo


@router.put("/{vehiculoId}", response_model=VehiculoResponse)
async def actualizarVehiculoRoute(
    vehiculoId: int,
    datos: VehiculoUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["cliente", "superadmin"]))
):
    """Actualizar mis datos de vehículo."""
    clienteId = int(usuario["sub"])
    rol = usuario.get("rol")
    
    vehiculo = await obtenerVehiculo(db, vehiculoId)
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    
    # Validar propiedad
    if rol != "superadmin" and vehiculo.cliente_id != clienteId:
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar este vehículo")

    return await actualizarVehiculo(db, vehiculoId, datos)


@router.delete("/{vehiculoId}", response_model=VehiculoResponse)
async def eliminarVehiculoRoute(
    vehiculoId: int,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["cliente", "superadmin"]))
):
    """Eliminar un vehículo (lógico)."""
    clienteId = int(usuario["sub"])
    rol = usuario.get("rol")

    vehiculo = await obtenerVehiculo(db, vehiculoId)
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    
    # Validar propiedad
    if rol != "superadmin" and vehiculo.cliente_id != clienteId:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este vehículo")

    return await eliminarVehiculo(db, vehiculoId)
