import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de Google Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def clasificarSolicitudConIA(descripcion: str, urlsFotos: list) -> str:
    """
    Analiza la descripción (Speech-to-Text de Flutter) y las fotos subidas
    para determinar el tipo de servicio necesario.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Construimos el prompt dinámico
        prompt = f"""
        Actúa como un experto en triaje de emergencias vehiculares. 
        Analiza el siguiente reporte del cliente: 
        
        Descripción: "{descripcion}"
        URLs de Imágenes: {urlsFotos}
        
        Basado en esto, clasifica la emergencia en UNA de las siguientes categorías exactas:
        - GRÚA
        - LLANTAS
        - BATERÍA
        - MECÁNICA LIGERA
        
        Responde exclusivamente con el nombre de la categoría, sin texto adicional. 
        Si no estás seguro, responde: MECÁNICA LIGERA.
        """
        
        # Generar respuesta
        response = await model.generate_content_async(prompt)
        return response.text.strip().upper()
        
    except Exception as e:
        print(f"Error en clasificación IA: {e}")
        return "MECÁNICA LIGERA" # Fallback por defecto
