from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.tipo_servicio import TipoServicio
from app.schemas.tipo_servicio import TipoServicioCreate, TipoServicioUpdate


async def listarTiposServicio(db: AsyncSession):
    """Listar todos los tipos de servicio activos."""
    query = select(TipoServicio).where(TipoServicio.estado == True)
    result = await db.execute(query)
    return result.scalars().all()


async def obtenerTipoServicio(db: AsyncSession, tipo_id: int):
    """Obtener un tipo de servicio por ID."""
    query = select(TipoServicio).where(TipoServicio.id == tipo_id, TipoServicio.estado == True)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def crearTipoServicio(db: AsyncSession, datos: TipoServicioCreate):
    """Crear un nuevo tipo de servicio."""
    nuevo = TipoServicio(
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        palabras_clave=datos.palabras_clave
    )
    db.add(nuevo)
    await db.commit()
    await db.refresh(nuevo)
    return nuevo


async def actualizarTipoServicio(db: AsyncSession, tipo_id: int, datos: TipoServicioUpdate):
    """Actualizar un tipo de servicio."""
    tipo = await obtenerTipoServicio(db, tipo_id)
    if not tipo:
        return None

    if datos.nombre is not None:
        tipo.nombre = datos.nombre
    if datos.descripcion is not None:
        tipo.descripcion = datos.descripcion
    if datos.palabras_clave is not None:
        tipo.palabras_clave = datos.palabras_clave

    await db.commit()
    await db.refresh(tipo)
    return tipo


async def eliminarTipoServicio(db: AsyncSession, tipo_id: int):
    """Eliminación lógica."""
    tipo = await obtenerTipoServicio(db, tipo_id)
    if not tipo:
        return None

    tipo.estado = False
    await db.commit()
    await db.refresh(tipo)
    return tipo
