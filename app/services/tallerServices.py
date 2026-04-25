from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.taller import Taller
from app.schemas.taller import TallerCreate, TallerUpdate


async def listarTalleres(db: AsyncSession):
    """Obtener todos los talleres activos."""
    query = select(Taller).where(Taller.estado == True)
    result = await db.execute(query)
    return result.scalars().all()


async def obtenerTaller(db: AsyncSession, taller_id: int):
    """Obtener un taller por ID (solo activo)."""
    query = select(Taller).where(Taller.id == taller_id, Taller.estado == True)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def crearTaller(db: AsyncSession, datos: TallerCreate, admin_id: int):
    """Crear un nuevo taller asignado al admin autenticado."""
    nuevo_taller = Taller(
        nombre=datos.nombre,
        direccion=datos.direccion,
        telefono=datos.telefono,
        latitud=datos.latitud,
        longitud=datos.longitud,
        admin_id=admin_id
    )
    db.add(nuevo_taller)
    await db.commit()
    await db.refresh(nuevo_taller)
    return nuevo_taller


async def actualizarTaller(db: AsyncSession, taller_id: int, datos: TallerUpdate):
    """Actualizar un taller existente."""
    taller = await obtenerTaller(db, taller_id)
    if not taller:
        return None

    if datos.nombre is not None:
        taller.nombre = datos.nombre
    if datos.direccion is not None:
        taller.direccion = datos.direccion
    if datos.telefono is not None:
        taller.telefono = datos.telefono
    if datos.latitud is not None:
        taller.latitud = datos.latitud
    if datos.longitud is not None:
        taller.longitud = datos.longitud

    await db.commit()
    await db.refresh(taller)
    return taller


async def eliminarTaller(db: AsyncSession, taller_id: int):
    """Eliminación lógica: estado = False."""
    taller = await obtenerTaller(db, taller_id)
    if not taller:
        return None

    taller.estado = False
    await db.commit()
    await db.refresh(taller)
    return taller
