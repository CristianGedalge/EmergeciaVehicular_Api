from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.config.db import get_db
from app.dependencies.auth import obtenerUsuarioActual
from app.dependencies.rolCheck import RequireRole
from app.schemas.solicitud import SolicitudResponse, AceptarSolicitudRequest, AsignarMecanicoRequest
from app.helpers.cloudinary import subirImagen
from app.helpers.ai import clasificarSolicitudConIA
from app.services.solicitudServices import (
    crearSolicitud, clasificarYPublicar, listarSolicitudesParaTalleres, 
    aceptarSolicitud, asignarMecanico
)

router = APIRouter(
    prefix="/solicitudes",
    tags=["Solicitudes"]
)

async def procesarIA(db: AsyncSession, solicitudId: int, descripcion: str, urls: List[str]):
    """Tarea en segundo plano para clasificar con IA y notificar."""
    categoria = await clasificarSolicitudConIA(descripcion, urls)
    await clasificarYPublicar(db, solicitudId, categoria)
    # Aquí después añadiremos el envío de Notificaciones Push/Sockets

@router.post("/", response_model=SolicitudResponse, status_code=201)
async def crearSolicitudRoute(
    background_tasks: BackgroundTasks,
    vehiculoId: int = Form(...),
    descripcion: str = Form(...),
    latitud: float = Form(...),
    longitud: float = Form(...),
    fotos: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["cliente"]))
):
    """
    Crear una nueva solicitud de auxilio. 
    Sube fotos a Cloudinary y clasifica con IA en segundo plano.
    """
    clienteId = int(usuario["sub"])
    
    # 1. Subir imágenes
    urls = []
    for foto in fotos:
        url = subirImagen(foto.file)
        if url: urls.append(url)
    
    # 2. Guardar solicitud inicial (Pendiente)
    nueva = await crearSolicitud(
        db, clienteId, vehiculoId, descripcion, latitud, longitud, urls
    )
    
    # 3. Lanzar clasificación IA en background para no bloquear al cliente
    background_tasks.add_task(procesarIA, db, nueva.id, descripcion, urls)
    
    return nueva

@router.get("/pendientes", response_model=List[SolicitudResponse])
async def listarPendientesRoute(
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["admin", "superadmin"]))
):
    """Listar todas las solicitudes disponibles para los talleres."""
    tallerId = usuario.get("tallerId")
    return await listarSolicitudesParaTalleres(db, tallerId)

@router.post("/{solicitudId}/aceptar", response_model=SolicitudResponse)
async def aceptarSolicitudRoute(
    solicitudId: int,
    datos: AceptarSolicitudRequest,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["admin"]))
):
    """Un taller acepta la emergencia y envía un precio estimado."""
    tallerId = usuario.get("tallerId")
    solicitud = await aceptarSolicitud(db, solicitudId, tallerId, datos.precio_estimado)
    
    if not solicitud:
        raise HTTPException(
            status_code=400, 
            detail="La solicitud ya no está disponible o ya fue aceptada."
        )
    return solicitud

@router.post("/{solicitudId}/asignar", response_model=SolicitudResponse)
async def asignarMecanicoRoute(
    solicitudId: int,
    datos: AsignarMecanicoRequest,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["admin"]))
):
    """El Admin del taller asigna a uno de sus mecánicos."""
    tallerId = usuario.get("tallerId")
    solicitud = await asignarMecanico(db, solicitudId, tallerId, datos.mecanico_id)
    
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada o no pertenece a tu taller")
    
    return solicitud
