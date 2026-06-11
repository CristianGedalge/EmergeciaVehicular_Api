from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case, extract, and_, or_
from sqlalchemy.orm import aliased
from datetime import datetime, timezone, timedelta

from app.models.solicitud import Solicitud, EstadoSolicitudEnum
from app.models.taller import Taller
from app.models.tipo_servicio import TipoServicio
from app.models.vehiculo import Vehiculo
from app.models.mecanico import Mecanico
from app.models.pago import Pago


async def obtenerMetricasTaller(db: AsyncSession, tallerId: int, dias: int = 30):
    """Calcula KPIs para un taller específico en un rango de días."""
    desde = datetime.now(timezone.utc) - timedelta(days=dias)

    # --- Consulta base de solicitudes del taller en el período ---
    query_base = select(Solicitud).where(
        Solicitud.taller_id == tallerId,
        Solicitud.fecha_creacion >= desde
    )
    result = await db.execute(query_base)
    solicitudes = result.scalars().all()

    total = len(solicitudes)
    finalizadas = [s for s in solicitudes if s.estado == EstadoSolicitudEnum.FINALIZADO]
    canceladas = [s for s in solicitudes if s.estado == EstadoSolicitudEnum.CANCELADO]
    en_curso = [s for s in solicitudes if s.estado not in [
        EstadoSolicitudEnum.FINALIZADO, EstadoSolicitudEnum.CANCELADO
    ]]

    # --- KPI: Tiempo promedio de asignación (creacion → aceptado) ---
    tiempos_asignacion = []
    for s in solicitudes:
        if s.fecha_aceptado and s.fecha_creacion:
            delta = (s.fecha_aceptado - s.fecha_creacion).total_seconds() / 60
            tiempos_asignacion.append(delta)
    
    tiempo_prom_asignacion = (
        round(sum(tiempos_asignacion) / len(tiempos_asignacion), 1)
        if tiempos_asignacion else None
    )

    # --- KPI: Tiempo promedio de llegada (en_camino → en_sitio) ---
    tiempos_llegada = []
    for s in solicitudes:
        if s.fecha_en_sitio and s.fecha_en_camino:
            delta = (s.fecha_en_sitio - s.fecha_en_camino).total_seconds() / 60
            tiempos_llegada.append(delta)

    tiempo_prom_llegada = (
        round(sum(tiempos_llegada) / len(tiempos_llegada), 1)
        if tiempos_llegada else None
    )

    # --- KPI: Tiempo promedio de servicio (en_sitio → finalizado) ---
    tiempos_servicio = []
    for s in finalizadas:
        if s.fecha_finalizado and s.fecha_en_sitio:
            delta = (s.fecha_finalizado - s.fecha_en_sitio).total_seconds() / 60
            tiempos_servicio.append(delta)

    tiempo_prom_servicio = (
        round(sum(tiempos_servicio) / len(tiempos_servicio), 1)
        if tiempos_servicio else None
    )

    # --- KPI: Tasa de cancelación ---
    tasa_cancelacion = round((len(canceladas) / total * 100), 1) if total > 0 else 0

    # --- KPI: Servicios por tipo (incidentes) ---
    query_tipos = (
        select(TipoServicio.nombre, func.count(Solicitud.id).label("total"))
        .outerjoin(TipoServicio, Solicitud.tipo_servicio_id == TipoServicio.id)
        .where(Solicitud.taller_id == tallerId, Solicitud.fecha_creacion >= desde)
        .group_by(TipoServicio.nombre)
        .order_by(func.count(Solicitud.id).desc())
    )
    res_tipos = await db.execute(query_tipos)
    tipos_incidente = [
        {"nombre": row.nombre or "Sin categoría", "total": row.total}
        for row in res_tipos.all()
    ]

    # --- KPI: Ingresos del período ---
    ingresos = sum(s.precio_final or 0 for s in finalizadas)

    return {
        "periodo_dias": dias,
        "total_solicitudes": total,
        "finalizadas": len(finalizadas),
        "canceladas": len(canceladas),
        "en_curso": len(en_curso),
        "tasa_cancelacion_pct": tasa_cancelacion,
        "tiempo_prom_asignacion_min": tiempo_prom_asignacion,
        "tiempo_prom_llegada_min": tiempo_prom_llegada,
        "tiempo_prom_servicio_min": tiempo_prom_servicio,
        "ingresos_periodo": round(ingresos, 2),
        "tipos_incidente": tipos_incidente,
    }


async def obtenerMetricasGlobales(db: AsyncSession, dias: int = 30):
    """Calcula KPIs globales (superadmin) en un rango de días."""
    desde = datetime.now(timezone.utc) - timedelta(days=dias)

    result = await db.execute(
        select(Solicitud).where(Solicitud.fecha_creacion >= desde)
    )
    solicitudes = result.scalars().all()

    total = len(solicitudes)
    finalizadas = [s for s in solicitudes if s.estado == EstadoSolicitudEnum.FINALIZADO]
    canceladas = [s for s in solicitudes if s.estado == EstadoSolicitudEnum.CANCELADO]

    # --- Top talleres por cantidad de servicios finalizados ---
    query_talleres = (
        select(Taller.nombre, func.count(Solicitud.id).label("total"))
        .join(Solicitud, Solicitud.taller_id == Taller.id)
        .where(
            Solicitud.estado == EstadoSolicitudEnum.FINALIZADO,
            Solicitud.fecha_creacion >= desde
        )
        .group_by(Taller.nombre)
        .order_by(func.count(Solicitud.id).desc())
        .limit(10)
    )
    res_talleres = await db.execute(query_talleres)
    top_talleres = [
        {"taller": row.nombre, "finalizados": row.total}
        for row in res_talleres.all()
    ]

    # --- Tipos de incidente globales ---
    query_tipos = (
        select(TipoServicio.nombre, func.count(Solicitud.id).label("total"))
        .outerjoin(TipoServicio, Solicitud.tipo_servicio_id == TipoServicio.id)
        .where(Solicitud.fecha_creacion >= desde)
        .group_by(TipoServicio.nombre)
        .order_by(func.count(Solicitud.id).desc())
    )
    res_tipos = await db.execute(query_tipos)
    tipos_incidente = [
        {"nombre": row.nombre or "Sin categoría", "total": row.total}
        for row in res_tipos.all()
    ]

    # --- Tiempos promedio globales ---
    tiempos_asignacion = []
    tiempos_llegada = []
    tiempos_servicio = []
    for s in solicitudes:
        if s.fecha_aceptado and s.fecha_creacion:
            tiempos_asignacion.append((s.fecha_aceptado - s.fecha_creacion).total_seconds() / 60)
        if s.fecha_en_sitio and s.fecha_en_camino:
            tiempos_llegada.append((s.fecha_en_sitio - s.fecha_en_camino).total_seconds() / 60)
    for s in finalizadas:
        if s.fecha_finalizado and s.fecha_en_sitio:
            tiempos_servicio.append((s.fecha_finalizado - s.fecha_en_sitio).total_seconds() / 60)

    return {
        "periodo_dias": dias,
        "total_solicitudes": total,
        "finalizadas": len(finalizadas),
        "canceladas": len(canceladas),
        "tasa_cancelacion_pct": round(len(canceladas) / total * 100, 1) if total > 0 else 0,
        "tiempo_prom_asignacion_min": round(sum(tiempos_asignacion) / len(tiempos_asignacion), 1) if tiempos_asignacion else None,
        "tiempo_prom_llegada_min": round(sum(tiempos_llegada) / len(tiempos_llegada), 1) if tiempos_llegada else None,
        "tiempo_prom_servicio_min": round(sum(tiempos_servicio) / len(tiempos_servicio), 1) if tiempos_servicio else None,
        "top_talleres": top_talleres,
        "tipos_incidente": tipos_incidente,
    }
