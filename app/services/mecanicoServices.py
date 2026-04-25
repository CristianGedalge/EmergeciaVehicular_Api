from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import insert, delete

from app.models.mecanico import Mecanico, mecanico_especialidad
from app.models.usuario import Usuario, RolEnum
from app.schemas.mecanico import MecanicoCreate, MecanicoUpdate
from app.services.authServices import hashearPassword


async def listarMecanicos(db: AsyncSession, taller_id: int):
    """Listar mecánicos activos de un taller."""
    query = select(Mecanico).where(
        Mecanico.taller_id == taller_id,
        Mecanico.estado == True
    )
    result = await db.execute(query)
    return result.scalars().all()


async def obtenerMecanico(db: AsyncSession, mecanico_id: int):
    """Obtener un mecánico por ID (solo activo)."""
    query = select(Mecanico).where(Mecanico.id == mecanico_id, Mecanico.estado == True)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def crearMecanico(db: AsyncSession, taller_id: int, datos: MecanicoCreate):
    """Crear usuario con rol mecánico + vincularlo al taller + asignar especialidades."""
    # 1. Verificar que el correo no exista
    query = select(Usuario).where(Usuario.correo == datos.correo)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        return None  # Correo ya registrado

    # 2. Crear usuario con rol mecánico
    nuevo_usuario = Usuario(
        nombre=datos.nombre,
        correo=datos.correo,
        password=hashearPassword(datos.password),
        telefono=datos.telefono,
        rol=RolEnum.MECANICO
    )
    db.add(nuevo_usuario)
    await db.flush()  # Para obtener el ID sin hacer commit aún

    # 3. Crear registro de mecánico vinculado al taller
    nuevo_mecanico = Mecanico(
        usuario_id=nuevo_usuario.id,
        taller_id=taller_id
    )
    db.add(nuevo_mecanico)
    await db.flush()

    # 4. Asignar especialidades
    for tipo_servicio_id in datos.especialidades:
        await db.execute(
            insert(mecanico_especialidad).values(
                mecanico_id=nuevo_mecanico.id,
                tipo_servicio_id=tipo_servicio_id
            )
        )

    await db.commit()
    await db.refresh(nuevo_mecanico)
    return nuevo_mecanico


async def actualizarMecanico(db: AsyncSession, mecanico_id: int, datos: MecanicoUpdate):
    """Actualizar ubicación, disponibilidad y/o especialidades."""
    mecanico = await obtenerMecanico(db, mecanico_id)
    if not mecanico:
        return None

    if datos.latitud is not None:
        mecanico.latitud = datos.latitud
    if datos.longitud is not None:
        mecanico.longitud = datos.longitud
    if datos.disponible is not None:
        mecanico.disponible = datos.disponible

    # Actualizar especialidades si se envían
    if datos.especialidades is not None:
        # Borrar las anteriores
        await db.execute(
            delete(mecanico_especialidad).where(
                mecanico_especialidad.c.mecanico_id == mecanico_id
            )
        )
        # Insertar las nuevas
        for tipo_servicio_id in datos.especialidades:
            await db.execute(
                insert(mecanico_especialidad).values(
                    mecanico_id=mecanico_id,
                    tipo_servicio_id=tipo_servicio_id
                )
            )

    await db.commit()
    await db.refresh(mecanico)
    return mecanico


async def eliminarMecanico(db: AsyncSession, mecanico_id: int):
    """Eliminación lógica: desactiva mecánico y su usuario."""
    mecanico = await obtenerMecanico(db, mecanico_id)
    if not mecanico:
        return None

    # Desactivar mecánico
    mecanico.estado = False

    # Desactivar usuario asociado
    query = select(Usuario).where(Usuario.id == mecanico.usuario_id)
    result = await db.execute(query)
    usuario = result.scalar_one_or_none()
    if usuario:
        usuario.estado = False

    await db.commit()
    await db.refresh(mecanico)
    return mecanico
