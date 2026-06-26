import asyncio
from sqlalchemy import select
from app.config.db import AsyncSessionLocal
from app.models.usuario import Usuario, RolEnum
from app.services.authServices import hashearPassword

async def create_superadmin():
    if AsyncSessionLocal is None:
        print("Error: AsyncSessionLocal es None. La conexión a la base de datos falló.")
        return
        
    async with AsyncSessionLocal() as session:
        try:
            # Verificar si el usuario ya existe
            query = select(Usuario).where(Usuario.correo == "maykol@gmail.com")
            result = await session.execute(query)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"El usuario {existing_user.correo} ya existe con rol: {existing_user.rol}.")
                # Actualizar a superadmin con los datos correctos
                existing_user.rol = RolEnum.SUPERADMIN.value
                existing_user.password = hashearPassword("123456789")
                existing_user.nombre = "maykol Villazon"
                await session.commit()
                print("Se actualizó el usuario existente a Superadmin con la nueva contraseña.")
                return
            
            superadmin = Usuario(
                nombre="maykol Villazon",
                correo="maykol@gmail.com",
                password=hashearPassword("123456789"),
                rol=RolEnum.SUPERADMIN.value,
                estado=True
            )
            session.add(superadmin)
            await session.commit()
            print("¡Superadmin creado exitosamente!")
        except Exception as e:
            await session.rollback()
            print(f"Error al crear superadmin: {e}")

if __name__ == "__main__":
    asyncio.run(create_superadmin())
