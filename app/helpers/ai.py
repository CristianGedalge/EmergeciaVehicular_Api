import google.generativeai as genai
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Configuración de Google Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def clasificarSolicitudConIA(descripcion: str, urlsFotos: list, listaServicios: list) -> str:
    """
    Clasifica la emergencia basándose ÚNICAMENTE en la descripción textual.
    """
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Actúa como un experto en triaje de emergencias vehiculares. 
        Analiza el siguiente reporte del cliente: 
        
        Reporte: "{descripcion}"
        
        Basado en esto, clasifica la emergencia en UNA de las siguientes categorías disponibles:
        [{", ".join(listaServicios)}]
        
        Responde exclusivamente con el nombre de la categoría, exactamente como aparece en la lista, sin texto adicional. 
        Si no puedes clasificarlo, responde: MECÁNICA LIGERA.
        """
        
        response = await model.generate_content_async(prompt)
        return response.text.strip().upper()
        
    except Exception as e:
        print(f"Error en clasificación IA: {e}")
        return "MECÁNICA LIGERA"
