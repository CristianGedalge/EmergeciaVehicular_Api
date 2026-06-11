import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.config.db import async_engine
from app.services.authServices import hashearPassword
import unicodedata

# Nombres base para combinar
nombres = ["Carlos", "Mario", "Pedro", "Juan", "Diego", "Fernando", "Roberto", "Jose", "Luis", "Antonio", "Miguel", "Jorge", "Victor"]
apellidos = ["Rojas", "Salazar", "Mamani", "Choque", "Zeballos", "Cabrera", "Vaca", "Perez", "Gomez", "Condori", "Vargas", "Gutierrez"]

def remover_acentos(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

async def seed_mecanicos():
    print("Hasheando la contraseña '123456' para los mecánicos...")
    password_mecanicos = "123456"
    hashed_password = hashearPassword(password_mecanicos)
    print("Contraseña hasheada lista.")

    try:
        async with async_engine.begin() as conn:
            # Obtener los primeros 5 talleres
            res_talleres = await conn.execute(text("SELECT id FROM taller ORDER BY id ASC LIMIT 5"))
            talleres = [row[0] for row in res_talleres.fetchall()]
            
            if len(talleres) < 5:
                print("Advertencia: Hay menos de 5 talleres en la base de datos.")
            if len(talleres) == 0:
                print("Error: No hay talleres para asignar mecánicos.")
                return

            print(f"Insertando 7 mecánicos por taller para 5 talleres (Total 35 mecánicos)...")
            
            contador = 0
            for taller_id in talleres:
                for j in range(7):
                    # Generar nombre
                    nombre = nombres[(contador + j) % len(nombres)]
                    apellido = apellidos[(contador * j + 1) % len(apellidos)]
                    nombre_completo = f"{nombre} {apellido}"
                    
                    # Generar correo único (mec_carlosrojas0@gmail.com)
                    nombre_limpio = remover_acentos(nombre).lower()
                    apellido_limpio = remover_acentos(apellido).lower()
                    correo = f"mec_{nombre_limpio}{apellido_limpio}{contador}@gmail.com"
                    
                    telefono = f"+591 6000{contador:04d}"
                    
                    # Insertar en usuario
                    query_usuario = text("""
                        INSERT INTO usuario (nombre, correo, password, rol, telefono, estado) 
                        VALUES (:nombre, :correo, :password, 'mecanico', :telefono, true)
                        RETURNING id
                    """)
                    res_usuario = await conn.execute(query_usuario, {
                        "nombre": nombre_completo,
                        "correo": correo,
                        "password": hashed_password,
                        "telefono": telefono
                    })
                    usuario_id = res_usuario.scalar()
                    
                    # Insertar en mecanico
                    query_mecanico = text("""
                        INSERT INTO mecanico (usuario_id, taller_id, disponible, estado) 
                        VALUES (:usuario_id, :taller_id, true, true)
                    """)
                    await conn.execute(query_mecanico, {
                        "usuario_id": usuario_id,
                        "taller_id": taller_id
                    })
                    
                    contador += 1

            print(f"¡Se registraron exitosamente {contador} mecánicos en total!")
    except Exception as e:
        print("Error al insertar mecánicos:", e)
    finally:
        await async_engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_mecanicos())
