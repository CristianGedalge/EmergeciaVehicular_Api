import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config.db import async_engine
from app.services.authServices import hashearPassword

nombres_latinos = [
    "Juan", "María", "Carlos", "Ana", "Luis", "Elena", "Pedro", "Sofía", "Diego", "Carmen",
    "Javier", "Laura", "Miguel", "Isabel", "Fernando", "Lucía", "Jorge", "Marta", "Roberto", "Paula",
    "Ricardo", "Patricia", "Manuel", "Camila", "Alejandro", "Valeria", "José", "Daniela", "Raúl", "Natalia",
    "Andrés", "Gabriela", "Hugo", "Valentina", "Martín", "Antonia", "Eduardo", "Sara", "Gabriel", "Victoria",
    "Héctor", "Claudia", "Julio", "Rosa", "Marcos", "Teresa", "Alberto", "Silvia", "Mario", "Beatriz"
]

apellidos_latinos = [
    "García", "Rodríguez", "González", "Fernández", "López", "Martínez", "Sánchez", "Pérez", "Gómez", "Martín",
    "Jiménez", "Ruiz", "Hernández", "Díaz", "Moreno", "Muñoz", "Álvarez", "Romero", "Alonso", "Gutiérrez",
    "Navarro", "Torres", "Domínguez", "Vázquez", "Ramos", "Gil", "Ramírez", "Serrano", "Blanco", "Molina",
    "Morales", "Suárez", "Ortega", "Delgado", "Castro", "Ortiz", "Rubio", "Marín", "Sanz", "Núñez",
    "Iglesias", "Medina", "Garrido", "Cortes", "Castillo", "Santos", "Lozano", "Guerrero", "Cano", "Prieto"
]

async def seed_clientes():
    print("Hasheando la contraseña '12345678' (esto puede tardar un par de segundos)...")
    password_comun = "12345678"
    hashed_password = hashearPassword(password_comun)
    print("Contraseña hasheada lista.")

    import unicodedata

    def remover_acentos(texto):
        return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    clientes = []
    for i in range(50):
        nombre = nombres_latinos[i % len(nombres_latinos)]
        apellido = apellidos_latinos[i % len(apellidos_latinos)]
        nombre_completo = f"{nombre} {apellido}"
        
        # Generar correo basado en el nombre (ej: juangarcia@gmail.com)
        # Limpiamos acentos y pasamos a minúsculas
        nombre_limpio = remover_acentos(nombre).lower()
        apellido_limpio = remover_acentos(apellido).lower()
        correo = f"{nombre_limpio}{apellido_limpio}@gmail.com"
        
        # Para evitar duplicados en correos muy comunes
        if i >= len(nombres_latinos):
            correo = f"{nombre_limpio}{apellido_limpio}{i}@gmail.com"
            
        telefono = f"+591 7000{i:04d}"
        
        clientes.append((nombre_completo, correo, hashed_password, telefono))

    try:
        async with async_engine.begin() as conn:
            print(f"Insertando {len(clientes)} clientes en la base de datos AWS...")
            for nombre, correo, pwd, telefono in clientes:
                query = text("""
                    INSERT INTO usuario (nombre, correo, password, rol, telefono, estado) 
                    VALUES (:nombre, :correo, :password, 'cliente', :telefono, true)
                """)
                await conn.execute(query, {
                    "nombre": nombre,
                    "correo": correo,
                    "password": pwd,
                    "telefono": telefono
                })
            print("¡Los 50 clientes se registraron con éxito!")
    except Exception as e:
        print("Error al insertar clientes:", e)
    finally:
        await async_engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_clientes())
