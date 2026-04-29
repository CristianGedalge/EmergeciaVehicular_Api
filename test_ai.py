import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ ERROR: No se encontró GEMINI_API_KEY en el archivo .env")
    exit()

# Inicializamos el cliente con la versión v1beta que es la que soporta 2.5
client = genai.Client(
    api_key=api_key,
    http_options={'api_version': 'v1beta'}
)

MODELO = "gemini-2.5-flash"

print(f"🚀 Probando el modelo más avanzado: {MODELO}")

servicios = ["GRUA", "LLANTAS", "BATERIA", "MECANICA LIGERA"]
descripcion = "Se me rompió el motor y está saliendo fuego, necesito que alguien venga a recoger el auto porque no se mueve."

prompt = (
    "Actúa como un experto en mecánica. Analiza este reporte: "
    f"'{descripcion}'. "
    f"Elige una categoría de esta lista: {servicios}. "
    "Responde solo el nombre de la categoría."
)

try:
    print("--- Enviando consulta a la IA ---")
    response = client.models.generate_content(
        model=MODELO,
        contents=prompt
    )
    print(f"\n🤖 RESULTADO DE LA IA: {response.text.strip()}")
    print("\n✅ ¡PRUEBA EXITOSA CON 2.5 FLASH!")
except Exception as e:
    print(f"❌ Error: {e}")