from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case, and_
from sqlalchemy.orm import aliased
from datetime import datetime, timezone, timedelta

from app.models.solicitud import Solicitud, EstadoSolicitudEnum
from app.models.taller import Taller
from app.models.tipo_servicio import TipoServicio
from app.models.vehiculo import Vehiculo
from app.models.mecanico import Mecanico
from app.models.usuario import Usuario

async def reporte_rendimiento_mecanicos(db: AsyncSession, taller_id: int, dias: int = 30):
    desde = datetime.now(timezone.utc) - timedelta(days=dias)
    query = (
        select(
            Mecanico.id,
            Usuario.nombre,
            func.count(Solicitud.id).label("total_servicios"),
            func.sum(case((Solicitud.estado == EstadoSolicitudEnum.FINALIZADO, 1), else_=0)).label("finalizados"),
            func.sum(case((Solicitud.estado == EstadoSolicitudEnum.CANCELADO, 1), else_=0)).label("cancelados"),
            func.sum(case((Solicitud.estado == EstadoSolicitudEnum.FINALIZADO, Solicitud.precio_final), else_=0)).label("ingresos")
        )
        .join(Usuario, Usuario.id == Mecanico.usuario_id)
        .outerjoin(Solicitud, and_(Solicitud.mecanico_id == Mecanico.id, Solicitud.fecha_creacion >= desde))
    )
    if taller_id:
        query = query.where(Mecanico.taller_id == taller_id)
        
    query = query.group_by(Mecanico.id, Usuario.nombre)
    
    result = await db.execute(query)
    data = []
    for row in result.all():
        data.append({
            "mecanico_id": row.id,
            "nombre": row.nombre,
            "total_servicios": row.total_servicios or 0,
            "finalizados": row.finalizados or 0,
            "cancelados": row.cancelados or 0,
            "ingresos": float(row.ingresos) if row.ingresos else 0.0
        })
    return data


async def reporte_historial_servicios(db: AsyncSession, taller_id: int, dias: int = 30):
    desde = datetime.now(timezone.utc) - timedelta(days=dias)
    cliente_alias = aliased(Usuario)
    mecanico_usuario_alias = aliased(Usuario)
    
    query = (
        select(
            Solicitud.id,
            Solicitud.fecha_creacion,
            cliente_alias.nombre.label("cliente_nombre"),
            Vehiculo.placa.label("vehiculo_placa"),
            TipoServicio.nombre.label("tipo_falla"),
            mecanico_usuario_alias.nombre.label("mecanico_nombre"),
            Solicitud.estado,
            Solicitud.precio_estimado,
            Solicitud.precio_final,
            Solicitud.fecha_aceptado,
            Solicitud.fecha_en_camino,
            Solicitud.fecha_en_sitio,
            Solicitud.fecha_finalizado,
            Solicitud.fecha_cancelado
        )
        .join(cliente_alias, cliente_alias.id == Solicitud.cliente_id)
        .join(Vehiculo, Vehiculo.id == Solicitud.vehiculo_id)
        .outerjoin(TipoServicio, TipoServicio.id == Solicitud.tipo_servicio_id)
        .outerjoin(Mecanico, Mecanico.id == Solicitud.mecanico_id)
        .outerjoin(mecanico_usuario_alias, mecanico_usuario_alias.id == Mecanico.usuario_id)
        .where(Solicitud.fecha_creacion >= desde)
    )
    if taller_id:
        query = query.where(Solicitud.taller_id == taller_id)
        
    query = query.order_by(Solicitud.fecha_creacion.desc())

    result = await db.execute(query)
    data = []
    for row in result.all():
        data.append({
            "solicitud_id": row.id,
            "fecha": row.fecha_creacion.isoformat() if row.fecha_creacion else None,
            "cliente": row.cliente_nombre or "Desconocido",
            "vehiculo": row.vehiculo_placa or "Sin placa",
            "servicio": row.tipo_falla or "Clasificación IA",
            "mecanico": row.mecanico_nombre or "Sin asignar",
            "estado": row.estado.value if hasattr(row.estado, 'value') else row.estado,
            "precio_estimado": float(row.precio_estimado) if row.precio_estimado else 0.0,
            "precio_final": float(row.precio_final) if row.precio_final else 0.0,
            "fecha_aceptado": row.fecha_aceptado.isoformat() if row.fecha_aceptado else None,
            "fecha_en_camino": row.fecha_en_camino.isoformat() if row.fecha_en_camino else None,
            "fecha_en_sitio": row.fecha_en_sitio.isoformat() if row.fecha_en_sitio else None,
            "fecha_finalizado": row.fecha_finalizado.isoformat() if row.fecha_finalizado else None,
            "fecha_cancelado": row.fecha_cancelado.isoformat() if row.fecha_cancelado else None
        })
    return data
