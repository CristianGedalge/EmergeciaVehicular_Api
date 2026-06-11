from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.config.db import get_db
from app.dependencies.rolCheck import RequireRole
from app.services.reportesServices import reporte_rendimiento_mecanicos, reporte_historial_servicios
from app.helpers.reporteia import traducirPromptASQL
from sqlalchemy import text

router = APIRouter(prefix="/reportes", tags=["Reportes Tabulares"])

@router.get("/mecanicos")
async def get_reporte_mecanicos(
    dias: int = Query(default=30, ge=1, le=365, description="Rango de días"),
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["admin", "superadmin"]))
):
    """Reporte de rendimiento y ganancias por mecánico del taller o de todos si es superadmin."""
    taller_id = usuario.get("tallerId")
    return await reporte_rendimiento_mecanicos(db, taller_id, dias)

@router.get("/servicios")
async def get_reporte_servicios(
    dias: int = Query(default=30, ge=1, le=365, description="Rango de días"),
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["admin", "superadmin"]))
):
    """Reporte tabular histórico de todos los servicios del taller o de todos si es superadmin."""
    taller_id = usuario.get("tallerId")
    return await reporte_historial_servicios(db, taller_id, dias)

from pydantic import BaseModel

class PromptIA(BaseModel):
    prompt: str

@router.post("/ia")
async def get_reporte_ia(
    body: PromptIA,
    db: AsyncSession = Depends(get_db),
    usuario: dict = Depends(RequireRole(["admin", "superadmin"]))
):
    """Genera un reporte dinámico usando IA a partir de texto o transcripción de audio."""
    taller_id = usuario.get("tallerId")
    
    if not body.prompt.strip():
        return {"error": "El prompt está vacío"}
        
    sql_query = await traducirPromptASQL(body.prompt, taller_id)
    if not sql_query:
        return {"error": "La IA no pudo generar una consulta SQL válida."}
        
    try:
        result = await db.execute(text(sql_query))
        rows = result.mappings().all()
        # Convertir a lista de diccionarios, formateando floats o decimals si es necesario
        data = []
        for row in rows:
            fila = {}
            for k, v in row.items():
                if hasattr(v, 'isoformat'): # Fechas
                    fila[k] = v.isoformat()
                elif hasattr(v, '__float__'): # Numericos / Decimales
                    fila[k] = float(v)
                else:
                    fila[k] = str(v) if v is not None else None
            data.append(fila)
            
        return {
            "exito": True,
            "sql_ejecutado": sql_query,
            "data": data
        }
    except Exception as e:
        return {"error": f"Error al ejecutar la consulta generada: {str(e)}", "sql_ejecutado": sql_query}

