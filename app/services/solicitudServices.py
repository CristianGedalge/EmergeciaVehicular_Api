from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from typing import List

from app.models.solicitud import Solicitud, EstadoSolicitudEnum
from app.models.mecanico import Mecanico, mecanico_especialidad
from app.models.taller import Taller
from app.models.tipo_servicio import TipoServicio

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
    return nueva

async def clasificarYPublicar(db: AsyncSession, solicitudId: int, categoriaIA: str):
    """Asocia el tipo de servicio detectado por la IA y cambia el estado."""
    # Buscar el ID del tipo de servicio que coincida con el nombre de la IA
    query = select(TipoServicio).where(TipoServicio.nombre == categoriaIA)
    tipo = (await db.execute(query)).scalar_one_or_none()
    
    if tipo:
        stmt = update(Solicitud).where(Solicitud.id == solicitudId).values(
            tipo_servicio_id=tipo.id,
            estado=EstadoSolicitudEnum.PUBLICADO
        )
        await db.execute(stmt)
        await db.commit()
        return True
    return False

async def listarSolicitudesParaTalleres(db: AsyncSession, tallerId: int):
    """Listar solicitudes que están PUBLICADAS y que el taller puede atender."""
    # Nota: Aquí después filtraremos por cercanía y especialidad
    query = select(Solicitud).where(Solicitud.estado == EstadoSolicitudEnum.PUBLICADO)
    result = await db.execute(query)
    return result.scalars().all()

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
    """El taller asigna un mecánico a la solicitud aceptada."""
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
    return solicitud
