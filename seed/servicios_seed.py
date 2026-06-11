import asyncio
import os
import sys

# Agregar el directorio padre al sys.path para poder importar módulos de la app si es necesario
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.config.db import async_engine

servicios = [
    ("Gomería Móvil", "Cambio, parchado y calibración de llantas a domicilio o en la vía."),
    ("Servicio de Grúa Ligera", "Remolque de automóviles, camionetas y motocicletas pequeñas."),
    ("Electricista Automotriz", "Revisión de cableado, luces, alternador y sistema eléctrico general."),
    ("Recarga y Cambio de Batería", "Asistencia con cables (puente) o instalación de batería nueva en sitio."),
    ("Cambio de Aceite a Domicilio", "Cambio de aceite de motor y filtros directamente en tu garaje."),
    ("Mecánica Rápida (Frenos)", "Cambio de pastillas, revisión de discos y purga de líquido de frenos."),
    ("Apertura de Vehículos (Cerrajería)", "Apertura segura de puertas de autos cuando las llaves quedan adentro."),
    ("Abastecimiento de Combustible", "Llevamos galones de gasolina o diésel de emergencia a tu ubicación."),
    ("Diagnóstico con Escáner OBD2", "Escaneo computarizado para identificar códigos de error (Check Engine)."),
    ("Chaperío Rápido y Sacabollos", "Reparación de abolladuras menores sin necesidad de repintar."),
    ("Asistencia de Suspensión", "Revisión rápida de amortiguadores, tijerales y ruidos en la calle."),
    ("Reparación de Aire Acondicionado", "Recarga de gas refrigerante y revisión de fugas a domicilio."),
    ("Cambio de Correas en Vía", "Reemplazo de correas de alternador o correas de accesorios reventadas."),
    ("Auxilio Mecánico de Motos", "Reparación rápida, pinchazos y fallas de encendido para motocicletas."),
    ("Limpieza de Inyectores", "Limpieza del sistema de inyección de combustible a domicilio."),
    ("Inspección Pre-Compra", "Revisión mecánica, de chasis y eléctrica completa antes de comprar un auto."),
    ("Alineación y Balanceo Móvil", "Servicio especializado de alineación con equipo portátil de precisión."),
    ("Cambio de Bujías y Bobinas", "Reemplazo rápido para solucionar tirones y problemas de encendido."),
    ("Reparación de Bomba de Gasolina", "Diagnóstico y cambio de la bomba de combustible en el lugar del incidente."),
    ("Rescate 4x4 (Barro / Arena)", "Servicio de winch y tracción 4x4 para desatascar vehículos.")
]

async def seed_db():
    try:
        async with async_engine.begin() as conn:
            print(f"Insertando {len(servicios)} servicios de emergencia...")
            for nombre, descripcion in servicios:
                query = text("""
                    INSERT INTO tipo_servicio (nombre, descripcion, estado) 
                    VALUES (:nombre, :descripcion, true)
                """)
                await conn.execute(query, {"nombre": nombre, "descripcion": descripcion})
            print("¡Todos los servicios se insertaron con éxito!")
    except Exception as e:
        print("Error al insertar:", e)
    finally:
        await async_engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_db())
