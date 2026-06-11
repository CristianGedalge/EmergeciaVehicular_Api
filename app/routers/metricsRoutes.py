from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.db import get_db
from app.dependencies.rolCheck import RequireRole
from app.services.metricsServices import obtenerMetricasTaller, obtenerMetricasGlobales

router = APIRouter(prefix="/metricas", tags=["Métricas / KPIs"])


@router.get("/taller")
async def metricasTallerRoute(
    dias: int = Query(default=30, ge=1, le=365, description="Rango de días para las métricas"),
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["admin"]))
):
    """KPIs del taller del admin logueado."""
    tallerId = usuario.get("tallerId")
    return await obtenerMetricasTaller(db, tallerId, dias)


@router.get("/global")
async def metricasGlobalesRoute(
    dias: int = Query(default=30, ge=1, le=365, description="Rango de días para las métricas"),
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["superadmin"]))
):
    """KPIs globales de toda la plataforma (solo Superadmin)."""
    return await obtenerMetricasGlobales(db, dias)
