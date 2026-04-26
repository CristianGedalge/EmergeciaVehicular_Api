from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.vehiculo import Vehiculo
from app.schemas.vehiculo import VehiculoCreate, VehiculoUpdate

async def listarVehiculos(db: AsyncSession, clienteId: int):
    """Listar vehículos activos de un cliente."""
    query = select(Vehiculo).where(Vehiculo.cliente_id == clienteId, Vehiculo.estado == True)
    result = await db.execute(query)
    return result.scalars().all()

async def obtenerVehiculo(db: AsyncSession, vehiculoId: int):
    """Obtener un vehículo por ID."""
    query = select(Vehiculo).where(Vehiculo.id == vehiculoId, Vehiculo.estado == True)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def crearVehiculo(db: AsyncSession, clienteId: int, datos: VehiculoCreate):
    """Registrar un nuevo vehículo vinculado a un cliente."""
    # Verificar si la placa ya existe
    query = select(Vehiculo).where(Vehiculo.placa == datos.placa)
    if (await db.execute(query)).scalar_one_or_none():
        return None

    nuevo = Vehiculo(
        cliente_id=clienteId,
        marca=datos.marca,
        modelo=datos.modelo,
        anio=datos.anio,
        placa=datos.placa.upper(),
        color=datos.color
    )
    db.add(nuevo)
    await db.commit()
    await db.refresh(nuevo)
    return nuevo

async def actualizarVehiculo(db: AsyncSession, vehiculoId: int, datos: VehiculoUpdate):
    """Actualizar datos de un vehículo."""
    vehiculo = await obtenerVehiculo(db, vehiculoId)
    if not vehiculo:
        return None

    if datos.marca is not None: vehiculo.marca = datos.marca
    if datos.modelo is not None: vehiculo.modelo = datos.modelo
    if datos.anio is not None: vehiculo.anio = datos.anio
    if datos.placa is not None: vehiculo.placa = datos.placa.upper()
    if datos.color is not None: vehiculo.color = datos.color

    await db.commit()
    await db.refresh(vehiculo)
    return vehiculo

async def eliminarVehiculo(db: AsyncSession, vehiculoId: int):
    """Eliminación lógica de un vehículo."""
    vehiculo = await obtenerVehiculo(db, vehiculoId)
    if not vehiculo:
        return None

    vehiculo.estado = False
    await db.commit()
    await db.refresh(vehiculo)
    return vehiculo
