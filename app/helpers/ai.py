import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de Google Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def clasificarSolicitudConIA(descripcion: str, urlsFotos: list, listaServicios: list) -> str:
    """
    Analiza la descripción y las fotos usando la lista dinámica de servicios
    obtenida de la base de datos.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        servicios_str = ", ".join(listaServicios)
        
        prompt = f"""
        Actúa como un experto en triaje de emergencias vehiculares. 
        Analiza el siguiente reporte del cliente: 
        
        Descripción: "{descripcion}"
        URLs de Imágenes: {urlsFotos}
        
        Basado en esto, clasifica la emergencia en UNA de las siguientes categorías disponibles:
        [{servicios_str}]
        
        Responde exclusivamente con el nombre de la categoría, exactamente como aparece en la lista, sin texto adicional. 
        Si no puedes clasificarlo en ninguna de esas categorías, responde: MECÁNICA LIGERA.
        """
        
        response = await model.generate_content_async(prompt)
        return response.text.strip().upper()
        
    except Exception as e:
        print(f"Error en clasificación IA: {e}")
        return "MECÁNICA LIGERA"
