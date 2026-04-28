from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.usuario import Usuario, RolEnum
from app.models.mecanico import Mecanico
from app.schemas.usuario import UsuarioUpdate
from app.services.authServices import hashearPassword

async def listarUsuarios(db: AsyncSession):
    """Listar todos los usuarios del sistema."""
    query = select(Usuario)
    result = await db.execute(query)
    return result.scalars().all()

async def obtenerUsuario(db: AsyncSession, usuario_id: int):
    """Obtener un usuario por ID."""
    query = select(Usuario).where(Usuario.id == usuario_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def actualizarUsuario(db: AsyncSession, usuario_id: int, datos: UsuarioUpdate):
    """Actualiza datos del usuario por el superadmin."""
    usuario = await obtenerUsuario(db, usuario_id)
    if not usuario:
        return None

    if datos.nombre is not None: usuario.nombre = datos.nombre
    if datos.telefono is not None: usuario.telefono = datos.telefono
    if datos.url_img is not None: usuario.url_img = datos.url_img
    if datos.rol is not None: usuario.rol = datos.rol
    if datos.estado is not None: usuario.estado = datos.estado

    await db.commit()
    await db.refresh(usuario)
    return usuario

async def eliminarUsuario(db: AsyncSession, usuario_id: int):
    """Eliminación lógica de un usuario. Si es mecánico, se desactiva su entidad correspondiente."""
    usuario = await obtenerUsuario(db, usuario_id)
    if not usuario:
        return None

    # Desactivar usuario
    usuario.estado = False

    # Actualizar ambas tablas si es rol mecánico
    if usuario.rol == RolEnum.MECANICO:
        query_mec = select(Mecanico).where(Mecanico.usuario_id == usuario.id)
        mecanico = (await db.execute(query_mec)).scalar_one_or_none()
        if mecanico:
            mecanico.estado = False

    await db.commit()
    await db.refresh(usuario)
    return usuario
