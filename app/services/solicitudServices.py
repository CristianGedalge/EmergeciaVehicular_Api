from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, func
from sqlalchemy.orm import aliased
from typing import List
from datetime import datetime, timezone

from app.models.solicitud import Solicitud, EstadoSolicitudEnum
from app.models.mecanico import Mecanico, mecanico_especialidad
from app.models.taller import Taller
from app.models.tipo_servicio import TipoServicio
from app.models.vehiculo import Vehiculo
from app.models.usuario import Usuario
from app.models.notificacion import Notificacion
from app.models.pago import Pago
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
    from sqlalchemy import or_, and_
    
    # Subconsulta para verificar si el taller tiene algún mecánico disponible con la especialidad
    subq = (
        select(1)
        .select_from(Mecanico)
        .join(mecanico_especialidad, Mecanico.id == mecanico_especialidad.c.mecanico_id)
        .where(
            Mecanico.taller_id == tallerId,
            Mecanico.disponible == True,
            Mecanico.estado == True,
            mecanico_especialidad.c.tipo_servicio_id == Solicitud.tipo_servicio_id
        )
    )

    query = (
        select(Solicitud, Vehiculo.placa, TipoServicio.nombre)
        .join(Vehiculo, Solicitud.vehiculo_id == Vehiculo.id)
        .outerjoin(TipoServicio, Solicitud.tipo_servicio_id == TipoServicio.id)
        .where(
            or_(
                and_(
                    Solicitud.estado == EstadoSolicitudEnum.PUBLICADO,
                    subq.exists()
                ),
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
    solicitud.fecha_aceptado = datetime.now(timezone.utc)
    
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
    
    # Cambiar disponibilidad del mecánico a False (ocupado)
    query_mec_obj = select(Mecanico).where(Mecanico.id == mecanicoId)
    res_mec_obj = await db.execute(query_mec_obj)
    mecanico_obj = res_mec_obj.scalar_one_or_none()
    if mecanico_obj:
        mecanico_obj.disponible = False
        print(f"💼 Mecánico ID {mecanicoId} marcado como NO DISPONIBLE (disponible=False).")
        
    # Sumar 5 puntos al taller por la asignación
    query_taller = select(Taller).where(Taller.id == tallerId)
    res_taller = await db.execute(query_taller)
    taller_obj = res_taller.scalar_one_or_none()
    if taller_obj:
        taller_obj.puntaje = (taller_obj.puntaje or 0) + 5
        print(f"🌟 Taller ID {tallerId} sumó 5 puntos. Nuevo puntaje: {taller_obj.puntaje}")
    
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
    MecanicoUsuario = aliased(Usuario)
    query = (
        select(Solicitud, Vehiculo.placa, Vehiculo.marca, Vehiculo.modelo, Vehiculo.anio, Vehiculo.color, TipoServicio.nombre, Pago.estado_pago, Usuario.nombre.label("cliente_nombre"), MecanicoUsuario.nombre.label("mecanico_nombre"))
        .join(Vehiculo, Solicitud.vehiculo_id == Vehiculo.id)
        .join(Usuario, Solicitud.cliente_id == Usuario.id)
        .outerjoin(TipoServicio, Solicitud.tipo_servicio_id == TipoServicio.id)
        .outerjoin(Pago, Solicitud.id == Pago.solicitud_id)
        .outerjoin(Mecanico, Solicitud.mecanico_id == Mecanico.id)
        .outerjoin(MecanicoUsuario, Mecanico.usuario_id == MecanicoUsuario.id)
        .where(Solicitud.taller_id == tallerId)
        .order_by(Solicitud.fecha_creacion.desc())
    )
    result = await db.execute(query)
    
    lista = []
    for sol, placa, marca, modelo, anio, color, nombre_serv, estado_pago, cliente_nombre, mecanico_nombre in result.all():
        sol.placa_vehiculo = placa
        sol.vehiculo_marca = marca
        sol.vehiculo_modelo = modelo
        sol.vehiculo_anio = anio
        sol.vehiculo_color = color
        sol.nombre_servicio = nombre_serv
        if estado_pago:
            sol.estado_pago = estado_pago.value if hasattr(estado_pago, 'value') else estado_pago
        
        # Pydantic va a ignorar esto si no lo mapeamos, pero agreguemos al diccionario o como atributos
        sol.cliente_nombre = cliente_nombre
        sol.nombre_mecanico = mecanico_nombre
        
        lista.append(sol)
    return lista

async def listarServiciosEnVivoTaller(db: AsyncSession, tallerId: int):
    """Listar las solicitudes EN VIVO de un taller (que no están finalizadas ni completadas ni canceladas)."""
    MecanicoUsuario = aliased(Usuario)
    query = (
        select(Solicitud, Vehiculo.placa, Vehiculo.marca, Vehiculo.modelo, Vehiculo.anio, Vehiculo.color, TipoServicio.nombre, Pago.estado_pago, Usuario.nombre.label("cliente_nombre"), MecanicoUsuario.nombre.label("mecanico_nombre"))
        .join(Vehiculo, Solicitud.vehiculo_id == Vehiculo.id)
        .join(Usuario, Solicitud.cliente_id == Usuario.id)
        .outerjoin(TipoServicio, Solicitud.tipo_servicio_id == TipoServicio.id)
        .outerjoin(Pago, Solicitud.id == Pago.solicitud_id)
        .outerjoin(Mecanico, Solicitud.mecanico_id == Mecanico.id)
        .outerjoin(MecanicoUsuario, Mecanico.usuario_id == MecanicoUsuario.id)
        .where(
            Solicitud.taller_id == tallerId,
            Solicitud.estado.notin_([EstadoSolicitudEnum.FINALIZADO, EstadoSolicitudEnum.CANCELADO])
        )
        .order_by(Solicitud.fecha_creacion.desc())
    )
    result = await db.execute(query)
    
    lista = []
    for sol, placa, marca, modelo, anio, color, nombre_serv, estado_pago, cliente_nombre, mecanico_nombre in result.all():
        sol.placa_vehiculo = placa
        sol.vehiculo_marca = marca
        sol.vehiculo_modelo = modelo
        sol.vehiculo_anio = anio
        sol.vehiculo_color = color
        sol.nombre_servicio = nombre_serv
        if estado_pago:
            sol.estado_pago = estado_pago.value if hasattr(estado_pago, 'value') else estado_pago
        
        sol.cliente_nombre = cliente_nombre
        sol.nombre_mecanico = mecanico_nombre
        lista.append(sol)
    return lista

async def listarSolicitudesCliente(db: AsyncSession, clienteId: int):
    """Listar todas las solicitudes creadas por un cliente específico."""
    query = (
        select(Solicitud, Vehiculo.placa, TipoServicio.nombre, Pago.estado_pago, Taller.nombre, Usuario.nombre, Usuario.telefono)
        .join(Vehiculo, Solicitud.vehiculo_id == Vehiculo.id)
        .outerjoin(TipoServicio, Solicitud.tipo_servicio_id == TipoServicio.id)
        .outerjoin(Pago, Solicitud.id == Pago.solicitud_id)
        .outerjoin(Taller, Solicitud.taller_id == Taller.id)
        .outerjoin(Mecanico, Solicitud.mecanico_id == Mecanico.id)
        .outerjoin(Usuario, Mecanico.usuario_id == Usuario.id)
        .where(Solicitud.cliente_id == clienteId)
        .order_by(Solicitud.fecha_creacion.desc())
    )
    result = await db.execute(query)
    
    lista = []
    for sol, placa, nombre_serv, estado_pago, taller_nombre, nombre_mecanico, telefono_mecanico in result.all():
        sol.placa_vehiculo = placa
        sol.nombre_servicio = nombre_serv
        sol.taller_nombre = taller_nombre
        sol.nombre_mecanico = nombre_mecanico
        sol.telefono_mecanico = telefono_mecanico
        if estado_pago:
            sol.estado_pago = estado_pago.value if hasattr(estado_pago, 'value') else estado_pago
        lista.append(sol)
    return lista

async def listarSolicitudesMecanico(db: AsyncSession, mecanicoId: int):
    """Listar todas las solicitudes asignadas a un mecánico específico."""
    query = (
        select(Solicitud, Vehiculo.placa, TipoServicio.nombre, Usuario.nombre.label("cliente_nombre"))
        .join(Vehiculo, Solicitud.vehiculo_id == Vehiculo.id)
        .join(Usuario, Solicitud.cliente_id == Usuario.id)
        .outerjoin(TipoServicio, Solicitud.tipo_servicio_id == TipoServicio.id)
        .where(Solicitud.mecanico_id == mecanicoId)
        .order_by(Solicitud.fecha_creacion.desc())
    )
    result = await db.execute(query)
    
    lista = []
    for sol, placa, nombre_serv, cliente_nombre in result.all():
        sol.placa_vehiculo = placa
        sol.nombre_servicio = nombre_serv
        sol.cliente_nombre = cliente_nombre
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
    solicitud.fecha_en_camino = datetime.now(timezone.utc)
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
    solicitud.fecha_en_sitio = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(solicitud)
    return solicitud

from app.models.pago import Pago, MetodoPagoEnum, EstadoPagoEnum

async def finalizarServicio(db: AsyncSession, solicitudId: int, mecanicoId: int, precio_final: float, metodo_pago: str):
    """Cambia el estado a FINALIZADO y registra pago."""
    query = select(Solicitud).where(Solicitud.id == solicitudId, Solicitud.mecanico_id == mecanicoId)
    res = await db.execute(query)
    solicitud = res.scalar_one_or_none()
    
    if not solicitud:
        return None

    # Actualizar solicitud
    solicitud.precio_final = precio_final
    solicitud.estado = EstadoSolicitudEnum.FINALIZADO
    solicitud.fecha_finalizado = datetime.now(timezone.utc)

    # Crear el Pago pendiente
    metodo = MetodoPagoEnum.TARJETA
    estado_pago = EstadoPagoEnum.PENDIENTE
    
    if metodo_pago.upper() == "EFECTIVO":
        metodo = MetodoPagoEnum.EFECTIVO
        estado_pago = EstadoPagoEnum.COMPLETADO
    elif metodo_pago.upper() == "QR":
        metodo = MetodoPagoEnum.QR
        estado_pago = EstadoPagoEnum.PENDIENTE # O COMPLETADO si se simula acreditación

    nuevo_pago = Pago(
        solicitud_id=solicitud.id,
        monto=precio_final,
        metodo_pago=metodo,
        estado_pago=estado_pago
    )
    db.add(nuevo_pago)

    # El mecanico vuelve a estar disponible
    query_mec_obj = select(Mecanico).where(Mecanico.id == mecanicoId)
    res_mec_obj = await db.execute(query_mec_obj)
    mecanico_obj = res_mec_obj.scalar_one_or_none()
    if mecanico_obj:
        mecanico_obj.disponible = True

    await db.commit()
    await db.refresh(solicitud)
    return solicitud

async def cancelarSolicitud(db: AsyncSession, solicitudId: int, clienteId: int):
    """Cambia el estado a CANCELADO, libera al mecánico y cancela el flujo."""
    query = select(Solicitud).where(Solicitud.id == solicitudId, Solicitud.cliente_id == clienteId)
    res = await db.execute(query)
    solicitud = res.scalar_one_or_none()
    
    if not solicitud:
        return None

    if solicitud.estado in [EstadoSolicitudEnum.FINALIZADO, EstadoSolicitudEnum.CANCELADO]:
        return None

    # Liberar mecanico si estaba asignado
    if solicitud.mecanico_id:
        query_mec = select(Mecanico).where(Mecanico.id == solicitud.mecanico_id)
        res_mec = await db.execute(query_mec)
        mecanico_obj = res_mec.scalar_one_or_none()
        if mecanico_obj:
            mecanico_obj.disponible = True

    solicitud.estado = EstadoSolicitudEnum.CANCELADO
    solicitud.fecha_cancelado = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(solicitud)
    return solicitud

