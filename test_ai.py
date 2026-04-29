import os
import asyncio
from dotenv import load_dotenv
from google import genai
from sqlalchemy.future import select
from app.config.db import AsyncSessionLocal
from app.models.tipo_servicio import TipoServicio

load_dotenv()

async def probar_ia_con_db():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: No se encontró GEMINI_API_KEY")
        return

    # 1. Obtener servicios de la base de datos REAL
    print("🔍 Conectando a la base de datos para traer servicios...")
    async with AsyncSessionLocal() as db:
        query = select(TipoServicio.nombre)
        result = await db.execute(query)
        servicios = result.scalars().all()
    
    if not servicios:
        print("⚠️ Advertencia: No hay servicios en la tabla tipo_servicio.")
        servicios = ["MECANICA LIGERA"] # Fallback
    
    print(f"✅ Servicios encontrados en DB: {servicios}")

    # 2. Configurar IA
    client = genai.Client(
        api_key=api_key,
        http_options={'api_version': 'v1beta'}
    )
    
    MODELO = "gemini-2.5-flash"
    descripcion = "Mi auto se quedó sin batería en medio de la calle."

    prompt = (
        "Actúa como un experto en mecánica. Analiza este reporte: "
        f"'{descripcion}'. "
        f"Elige una categoría de esta lista: {servicios}. "
        "Responde solo el nombre de la categoría exactamente como aparece."
    )

    # 3. Consultar IA
    try:
        print(f"🚀 Enviando a {MODELO}...")
        response = client.models.generate_content(
            model=MODELO,
            contents=prompt
        )
        print(f"\n🤖 RESULTADO DE LA IA: {response.text.strip()}")
        print("\n✅ ¡PRUEBA EXITOSA CON DATOS REALES!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(probar_ia_con_db())