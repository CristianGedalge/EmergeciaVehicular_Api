from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.encoders import jsonable_encoder
from app.models.tipo_servicio import TipoServicio
from app.models.mecanico import Mecanico, mecanico_especialidad
from app.helpers.socket_manager import socket_manager
from typing import List

from app.config.db import get_db
from app.dependencies.auth import obtenerUsuarioActual
from app.dependencies.rolCheck import RequireRole
from app.schemas.solicitud import SolicitudResponse, AceptarSolicitudRequest, AsignarMecanicoRequest
from app.helpers.cloudinary import subirImagen
from app.helpers.ai import clasificarSolicitudConIA
from app.helpers.firebase_push import enviarPushNotification
from app.models.usuario import Usuario
from app.models.notificacion import Notificacion
from app.services.solicitudServices import (
    crearSolicitud, clasificarYPublicar, listarSolicitudesParaTalleres, 
    aceptarSolicitud, asignarMecanico, listarHistorialTaller,
    listarSolicitudesCliente, listarSolicitudesMecanico,
    iniciarViaje, llegarASitio
)

router = APIRouter(
    prefix="/solicitudes",
    tags=["Solicitudes"]
)

async def procesarIA(db: AsyncSession, solicitudId: int, descripcion: str, urls: List[str]):
    """Tarea en segundo plano para clasificar con IA y notificar a talleres interesados."""
    try:
        # 1. Obtener todos los nombres de servicios disponibles para la IA (limpios de espacios)
        query_servicios = select(TipoServicio.nombre)
        res_servicios = await db.execute(query_servicios)
        lista_servicios = [n.strip() for n in res_servicios.scalars().all()]
        
        # 2. Llamar a la IA
        categoria = await clasificarSolicitudConIA(descripcion, urls, lista_servicios)
        
        # 3. Vincular y publicar solicitud
        solicitud = await clasificarYPublicar(db, solicitudId, categoria)
        
        if solicitud:
            # 4. BUSCAR TALLERES INTERESADOS (que tengan mecánicos con esa especialidad)
            query_talleres = select(Mecanico.taller_id).join(
                mecanico_especialidad, Mecanico.id == mecanico_especialidad.c.mecanico_id
            ).where(
                mecanico_especialidad.c.tipo_servicio_id == solicitud.tipo_servicio_id
            )
            res_talleres = await db.execute(query_talleres)
            talleres_ids = res_talleres.scalars().unique().all()

            # 5. NOTIFICAR POR WEBSOCKET
            mensaje = {
                "evento": "NUEVA_EMERGENCIA",
                "datos": jsonable_encoder(solicitud)
            }
            for t_id in talleres_ids:
                await socket_manager.send_to_taller(t_id, mensaje)
                
            print(f"📢 Notificación enviada a {len(talleres_ids)} talleres para la solicitud {solicitudId}")

    except Exception as e:
        print(f"Error procesando IA y notificaciones: {e}")

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

@router.get("/historial", response_model=List[SolicitudResponse])
async def listarHistorialRoute(
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["admin"]))
):
    """Listar todo el historial de servicios de este taller."""
    tallerId = usuario.get("tallerId")
    if not tallerId:
        raise HTTPException(status_code=400, detail="El usuario no tiene un taller asociado")
        
    return await listarHistorialTaller(db, tallerId)

@router.get("/cliente", response_model=List[SolicitudResponse])
async def listarSolicitudesClienteRoute(
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["cliente"]))
):
    """Listar todas las solicitudes del cliente logueado."""
    clienteId = int(usuario["sub"])
    return await listarSolicitudesCliente(db, clienteId)

@router.get("/mecanico", response_model=List[SolicitudResponse])
async def listarSolicitudesMecanicoRoute(
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["mecanico"]))
):
    """Listar todas las solicitudes asignadas al mecánico logueado."""
    # Para el mecánico, necesitamos su ID de la tabla 'mecanico', no solo el usuario_id
    query_mec = select(Mecanico.id).where(Mecanico.usuario_id == int(usuario["sub"]))
    res_mec = await db.execute(query_mec)
    mecanicoId = res_mec.scalar_one_or_none()
    
    if not mecanicoId:
        raise HTTPException(status_code=404, detail="El usuario no está registrado como mecánico")
        
    return await listarSolicitudesMecanico(db, mecanicoId)

@router.post("/{solicitudId}/iniciar-viaje", response_model=SolicitudResponse)
async def iniciarViajeRoute(
    solicitudId: int,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["mecanico"]))
):
    """El mecánico indica que está en camino."""
    query_mec = select(Mecanico.id).where(Mecanico.usuario_id == int(usuario["sub"]))
    res_mec = await db.execute(query_mec)
    mecanicoId = res_mec.scalar_one_or_none()
    
    solicitud = await iniciarViaje(db, solicitudId, mecanicoId)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    # --- NOTIFICACIÓN PUSH AL CLIENTE ---
    try:
        # Obtener datos del cliente
        query_cli = select(Usuario.fcm_token, Usuario.nombre).where(Usuario.id == solicitud.cliente_id)
        res_cli = await db.execute(query_cli)
        fcm_token, nombre_cliente = res_cli.one()

        if fcm_token:
            await enviarPushNotification(
                fcm_token=fcm_token,
                titulo="🚀 ¡Mecánico en camino!",
                cuerpo=f"El mecánico ya inició el viaje para atender tu solicitud #{solicitud.id}.",
                data={"solicitud_id": str(solicitud.id), "tipo": "ESTADO_VIAJE", "estado": "EN_CAMINO"}
            )
    except Exception as e:
        print(f"Error enviando push al cliente: {e}")

    # Notificar también por WebSocket (si está conectado)
    await socket_manager.send_to_user(solicitud.cliente_id, {
        "evento": "ESTADO_ACTUALIZADO",
        "datos": {"solicitud_id": solicitud.id, "estado": "EN_CAMINO"}
    })
    return solicitud

@router.post("/{solicitudId}/llegar-sitio", response_model=SolicitudResponse)
async def llegarASitioRoute(
    solicitudId: int,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["mecanico"]))
):
    """El mecánico indica que ya llegó al lugar."""
    query_mec = select(Mecanico.id).where(Mecanico.usuario_id == int(usuario["sub"]))
    res_mec = await db.execute(query_mec)
    mecanicoId = res_mec.scalar_one_or_none()
    
    solicitud = await llegarASitio(db, solicitudId, mecanicoId)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    # --- NOTIFICACIÓN PUSH AL CLIENTE ---
    try:
        query_cli = select(Usuario.fcm_token).where(Usuario.id == solicitud.cliente_id)
        res_cli = await db.execute(query_cli)
        fcm_token = res_cli.scalar_one_or_none()

        if fcm_token:
            await enviarPushNotification(
                fcm_token=fcm_token,
                titulo="📍 ¡El mecánico ha llegado!",
                cuerpo=f"El técnico ya se encuentra en tu ubicación para la solicitud #{solicitud.id}.",
                data={"solicitud_id": str(solicitud.id), "tipo": "ESTADO_VIAJE", "estado": "EN_SITIO"}
            )
    except Exception as e:
        print(f"Error enviando push al cliente: {e}")

    await socket_manager.send_to_user(solicitud.cliente_id, {
        "evento": "ESTADO_ACTUALIZADO",
        "datos": {"solicitud_id": solicitud.id, "estado": "EN_SITIO"}
    })
    return solicitud
