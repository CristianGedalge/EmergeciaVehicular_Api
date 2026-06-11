import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.config.db import async_engine
from app.services.authServices import hashearPassword

admins_data = [
    ("Alejandra Bustos", "alejandrabustos@gmail.com", "Taller Automotriz Bustos", "Av. Cristo Redentor 4to Anillo", -17.7523, -63.1678),
    ("Francisco Rivera", "franciscorivera@gmail.com", "Mecánica Rivera", "Av. Banzer 6to Anillo", -17.7334, -63.1631),
    ("Mónica Flores", "monicaflores@gmail.com", "Servicentro Flores", "Av. Santos Dumont 3er Anillo", -17.8091, -63.1834),
    ("Sergio Paredes", "sergioparedes@gmail.com", "Garaje Paredes 4x4", "Doble Vía a La Guardia Km 6", -17.8285, -63.2201),
    ("Natalia Silva", "nataliasilva@gmail.com", "Auto Servicio Silva", "Av. Roca y Coronado 2do Anillo", -17.7812, -63.1995),
    ("Cristian Vargas", "cristianvargas@gmail.com", "Taller Vargas Competición", "Av. Virgen de Cotoca 4to Anillo", -17.7718, -63.1412),
    ("Adrián Rojas", "adrianrojas@gmail.com", "Frenos y Suspensión Rojas", "Av. Tres Pasos al Frente 5to Anillo", -17.7954, -63.1367),
    ("Paola Cárdenas", "paolacardenas@gmail.com", "Electromecánica Cárdenas", "Av. Bush 2do Anillo", -17.7731, -63.1902),
    ("Felipe Martínez", "felipemartinez@gmail.com", "Clínica del Automóvil Martínez", "Av. Piraí 3er Anillo Interno", -17.7963, -63.2014),
    ("Carolina Castro", "carolinacastro@gmail.com", "Taller Integral Castro", "Av. Mutualista 3er Anillo", -17.7612, -63.1584),
    ("Ignacio Torres", "ignaciotorres@gmail.com", "Motores y Cajas Torres", "Av. Alemana 5to Anillo", -17.7421, -63.1511),
]

async def seed_talleres():
    print("Hasheando la contraseña '12345678' (esto puede tardar un par de segundos)...")
    password_comun = "12345678"
    hashed_password = hashearPassword(password_comun)
    print("Contraseña hasheada lista.")

    try:
        async with async_engine.begin() as conn:
            print(f"Insertando {len(admins_data)} admins y talleres en AWS...")
            for i, data in enumerate(admins_data):
                nombre_admin, correo, nombre_taller, direccion, lat, lng = data
                telefono = f"+591 7{1000000 + i}"

                # Insertar admin y obtener su ID
                query_admin = text("""
                    INSERT INTO usuario (nombre, correo, password, rol, telefono, estado) 
                    VALUES (:nombre, :correo, :password, 'admin', :telefono, true)
                    RETURNING id
                """)
                res = await conn.execute(query_admin, {
                    "nombre": nombre_admin,
                    "correo": correo,
                    "password": hashed_password,
                    "telefono": telefono
                })
                admin_id = res.scalar()

                # Insertar taller asociado al admin
                query_taller = text("""
                    INSERT INTO taller (nombre, direccion, telefono, latitud, longitud, admin_id, puntaje, estado) 
                    VALUES (:nombre_taller, :direccion, :telefono, :latitud, :longitud, :admin_id, 0, true)
                """)
                await conn.execute(query_taller, {
                    "nombre_taller": nombre_taller,
                    "direccion": direccion,
                    "telefono": telefono,
                    "latitud": lat,
                    "longitud": lng,
                    "admin_id": admin_id
                })

            print("¡Los 11 administradores y sus talleres se registraron con éxito!")
    except Exception as e:
        print("Error al insertar talleres:", e)
    finally:
        await async_engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_talleres())
