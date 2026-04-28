import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ ERROR: No se encontró GEMINI_API_KEY en el archivo .env")
    exit()

print(f"Configurando IA con la llave: {api_key[:5]}...{api_key[-5:]}")
genai.configure(api_key=api_key)

print("\n--- 1. Listando modelos disponibles ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ Modelo encontrado: {m.name}")
except Exception as e:
    print(f"❌ Error al listar modelos: {e}")

print("\n--- 2. Probando generación simple ---")
try:
    # Intentamos con el modelo más común
    model_name = 'gemini-1.5-flash'
    print(f"Probando con {model_name}...")
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Hola, dime 'Funciona' si puedes leer esto.")
    print(f"🤖 Respuesta de la IA: {response.text}")
except Exception as e:
    print(f"❌ Error en la prueba de generación: {e}")
