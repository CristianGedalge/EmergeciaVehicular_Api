import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Inicializamos el cliente de Google GenAI con la versión v1beta
# que es la que soporta los modelos 2.5
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options={'api_version': 'v1beta'}
)

async def clasificarSolicitudConIA(descripcion: str, urlsFotos: list, listaServicios: list) -> str:
    """
    Clasifica la emergencia basándose únicamente en la descripción textual
    usando el modelo Gemini 2.5 Flash.
    """
    try:
        # Usamos el modelo más avanzado detectado en tus pruebas
        model_id = 'gemini-2.5-flash'
        
        servicios_str = ", ".join(listaServicios)
        
        prompt = (
            "Actúa como un experto en triaje de emergencias vehiculares. "
            f'Analiza el siguiente reporte del cliente: "{descripcion}". '
            f"Clasifica la emergencia en UNA de las siguientes categorías disponibles: [{servicios_str}]. "
            "Responde exclusivamente con el nombre de la categoría, exactamente como aparece en la lista, sin texto adicional. "
            "Si no puedes clasificarlo, responde: MECÁNICA LIGERA."
        )
        
        # Generar respuesta usando la nueva sintaxis del cliente
        response = client.models.generate_content(
            model=model_id,
            contents=prompt
        )
        
        return response.text.strip()
        
    except Exception as e:
        print(f"Error en clasificación IA (Gemini 2.5): {e}")
        return "MECÁNICA LIGERA"
