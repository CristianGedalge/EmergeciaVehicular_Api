from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, func
from typing import List

from app.models.solicitud import Solicitud, EstadoSolicitudEnum
from app.models.mecanico import Mecanico, mecanico_especialidad
from app.models.taller import Taller
from app.models.tipo_servicio import TipoServicio
from app.models.vehiculo import Vehiculo
from app.models.usuario import Usuario
from app.models.notificacion import Notificacion
from app.helpers.firebase_push import enviarPushNotification

async def crearSolicitud(
    db: AsyncSession, 
    clienteId: int, 
    vehiculoId: int, 
    descripcion: str, 
    lat: float, 
    lng: float, 
    urlsFotos: List[str],
    tipoServicioId: int = None
):
    """Crea la solicitud inicial en la base de datos."""
    nueva = Solicitud(
        cliente_id=clienteId,
        vehiculo_id=vehiculoId,
        descripcion=descripcion,
        latitud=lat,
        longitud=lng,
        urls_fotos=urlsFotos,
        tipo_servicio_id=tipoServicioId,
        estado=EstadoSolicitudEnum.PENDIENTE
    )
    db.add(nueva)
    await db.commit()
    await db.refresh(nueva)
    
    # Obtener placa para la respuesta inicial
    res_veh = await db.execute(select(Vehiculo.placa).where(Vehiculo.id == vehiculoId))
    nueva.placa_vehiculo = res_veh.scalar()
    
    return nueva

async def clasificarYPublicar(db: AsyncSession, solicitudId: int, categoriaIA: str):
    """Asocia el tipo de servicio detectado por la IA y cambia el estado."""
    print(f"\n--- DEBUG CLASIFICACIÓN ---")
    print(f"1. IA respondió: '{categoriaIA}'")
    
    # Listar todos los servicios para ver qué hay en la DB
    todos = (await db.execute(select(TipoServicio))).scalars().all()
    print(f"2. Servicios en DB: {[t.nombre for t in todos]}")
    
    # Buscar el ID ignorando mayúsculas/minúsculas y quitando espacios en blanco (TRIM)
    query = select(TipoServicio).where(func.trim(func.lower(TipoServicio.nombre)) == func.trim(func.lower(categoriaIA)))
    tipo = (await db.execute(query)).scalar_one_or_none()
    
    if tipo:
        print(f"3. Match exitoso: {tipo.nombre} (ID: {tipo.id})")
        query_sol = select(Solicitud).where(Solicitud.id == solicitudId)
        solicitud = (await db.execute(query_sol)).scalar_one_or_none()
        
        if solicitud:
            solicitud.tipo_servicio_id = tipo.id
            solicitud.estado = EstadoSolicitudEnum.PUBLICADO
            await db.commit()
            await db.refresh(solicitud)
            print(f"4. Solicitud {solicitudId} actualizada a PUBLICADO")
            return solicitud
    else:
        print(f"3. ❌ ERROR: No se encontró ningún match para '{categoriaIA}'")
            
    return None

async def listarSolicitudesParaTalleres(db: AsyncSession, tallerId: int):
    """Listar solicitudes PUBLICADAS y ACEPTADAS (del taller) con datos de vehículo y servicio."""
    from sqlalchemy import or_
    
    query = (
        select(Solicitud, Vehiculo.placa, TipoServicio.nombre)
        .join(Vehiculo, Solicitud.vehiculo_id == Vehiculo.id)
        .outerjoin(TipoServicio, Solicitud.tipo_servicio_id == TipoServicio.id)
        .where(
            or_(
                Solicitud.estado == EstadoSolicitudEnum.PUBLICADO,
                (Solicitud.estado == EstadoSolicitudEnum.ACEPTADO) & (Solicitud.taller_id == tallerId)
            )
        )
        .order_by(Solicitud.fecha_creacion.desc())
    )
    result = await db.execute(query)
    
    lista = []
    for sol, placa, nombre_serv in result.all():
        sol.placa_vehiculo = placa
        sol.nombre_servicio = nombre_serv
        lista.append(sol)
    return lista

async def aceptarSolicitud(db: AsyncSession, solicitudId: int, tallerId: int, precioEstimado: float):
    """El taller acepta la solicitud si sigue disponible."""
    query = select(Solicitud).where(
        Solicitud.id == solicitudId, 
        Solicitud.estado == EstadoSolicitudEnum.PUBLICADO
    )
    solicitud = (await db.execute(query)).scalar_one_or_none()
    
    if not solicitud:
        return None # Ya fue tomada o no existe
        
    solicitud.taller_id = tallerId
    solicitud.precio_estimado = precioEstimado
    solicitud.estado = EstadoSolicitudEnum.ACEPTADO
    
    await db.commit()
    await db.refresh(solicitud)
    return solicitud

async def asignarMecanico(db: AsyncSession, solicitudId: int, tallerId: int, mecanicoId: int):
    """El taller asigna un mecánico a la solicitud aceptada y le envía push notification."""
    query = select(Solicitud).where(
        Solicitud.id == solicitudId, 
        Solicitud.taller_id == tallerId
    )
    solicitud = (await db.execute(query)).scalar_one_or_none()
    
    if not solicitud:
        return None
        
    solicitud.mecanico_id = mecanicoId
    solicitud.estado = EstadoSolicitudEnum.ASIGNADO
    
    await db.commit()
    await db.refresh(solicitud)
    
    # --- ENVIAR PUSH NOTIFICATION AL MECÁNICO ---
    try:
        # Buscar el usuario_id del mecánico y su fcm_token
        query_mec = select(Mecanico.usuario_id).where(Mecanico.id == mecanicoId)
        res_mec = await db.execute(query_mec)
        usuario_id = res_mec.scalar_one_or_none()
        
        if usuario_id:
            query_user = select(Usuario.fcm_token, Usuario.nombre).where(Usuario.id == usuario_id)
            res_user = await db.execute(query_user)
            row = res_user.first()
            
            if row:
                fcm_token, nombre_mecanico = row
                
                # 1. Guardar notificación en la base de datos
                notif = Notificacion(
                    usuario_id=usuario_id,
                    titulo="🚨 Nueva emergencia asignada",
                    mensaje=f"Se te ha asignado la solicitud #{solicitudId}. {solicitud.descripcion or 'Revisa los detalles en la app.'}"
                )
                db.add(notif)
                await db.commit()
                
                # 2. Enviar push notification al dispositivo
                if fcm_token:
                    await enviarPushNotification(
                        fcm_token=fcm_token,
                        titulo="🚨 Nueva emergencia asignada",
                        cuerpo=f"Solicitud #{solicitudId}: {solicitud.descripcion or 'Revisa los detalles.'}",
                        data={
                            "solicitud_id": solicitudId,
                            "tipo": "EMERGENCIA_ASIGNADA",
                            "latitud": str(solicitud.latitud),
                            "longitud": str(solicitud.longitud)
                        }
                    )
                    print(f"📲 Push enviado al mecánico {nombre_mecanico} (usuario {usuario_id})")
                else:
                    print(f"⚠️ El mecánico {nombre_mecanico} no tiene token FCM registrado.")
    except Exception as e:
        print(f"Error enviando push notification: {e}")
    
    return solicitud

async def listarHistorialTaller(db: AsyncSession, tallerId: int):
    """Listar TODAS las solicitudes asociadas a un taller (Historial)."""
    query = (
        select(Solicitud, Vehiculo.placa, TipoServicio.nombre)
        .join(Vehiculo, Solicitud.vehiculo_id == Vehiculo.id)
        .outerjoin(TipoServicio, Solicitud.tipo_servicio_id == TipoServicio.id)
        .where(Solicitud.taller_id == tallerId)
        .order_by(Solicitud.fecha_creacion.desc())
    )
    result = await db.execute(query)
    
    lista = []
    for sol, placa, nombre_serv in result.all():
        sol.placa_vehiculo = placa
        sol.nombre_servicio = nombre_serv
        lista.append(sol)
    return lista

async def listarSolicitudesCliente(db: AsyncSession, clienteId: int):
    """Listar todas las solicitudes creadas por un cliente específico."""
    query = (
        select(Solicitud, Vehiculo.placa, TipoServicio.nombre)
        .join(Vehiculo, Solicitud.vehiculo_id == Vehiculo.id)
        .outerjoin(TipoServicio, Solicitud.tipo_servicio_id == TipoServicio.id)
        .where(Solicitud.cliente_id == clienteId)
        .order_by(Solicitud.fecha_creacion.desc())
    )
    result = await db.execute(query)
    
    lista = []
    for sol, placa, nombre_serv in result.all():
        sol.placa_vehiculo = placa
        sol.nombre_servicio = nombre_serv
        lista.append(sol)
    return lista

async def listarSolicitudesMecanico(db: AsyncSession, mecanicoId: int):
    """Listar todas las solicitudes asignadas a un mecánico específico."""
    query = (
        select(Solicitud, Vehiculo.placa, TipoServicio.nombre)
        .join(Vehiculo, Solicitud.vehiculo_id == Vehiculo.id)
        .outerjoin(TipoServicio, Solicitud.tipo_servicio_id == TipoServicio.id)
        .where(Solicitud.mecanico_id == mecanicoId)
        .order_by(Solicitud.fecha_creacion.desc())
    )
    result = await db.execute(query)
    
    lista = []
    for sol, placa, nombre_serv in result.all():
        sol.placa_vehiculo = placa
        sol.nombre_servicio = nombre_serv
        lista.append(sol)
    return lista

async def iniciarViaje(db: AsyncSession, solicitudId: int, mecanicoId: int):
    """Cambia el estado a EN_CAMINO."""
    query = select(Solicitud).where(Solicitud.id == solicitudId, Solicitud.mecanico_id == mecanicoId)
    res = await db.execute(query)
    solicitud = res.scalar_one_or_none()
    
    if not solicitud:
        return None
        
    solicitud.estado = EstadoSolicitudEnum.EN_CAMINO
    await db.commit()
    await db.refresh(solicitud)
    return solicitud

async def llegarASitio(db: AsyncSession, solicitudId: int, mecanicoId: int):
    """Cambia el estado a EN_SITIO."""
    query = select(Solicitud).where(Solicitud.id == solicitudId, Solicitud.mecanico_id == mecanicoId)
    res = await db.execute(query)
    solicitud = res.scalar_one_or_none()
    
    if not solicitud:
        return None
        
    solicitud.estado = EstadoSolicitudEnum.EN_SITIO
    await db.commit()
    await db.refresh(solicitud)
    return solicitud

