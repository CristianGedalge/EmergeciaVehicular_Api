import os
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

async def clasificarSolicitudConIA(descripcion: str, urlsFotos: list, listaServicios: list) -> str:
    """
    Clasifica la emergencia basándose únicamente en la descripción textual
    usando el modelo Llama 3.1 8B a través de la API de Groq.
    """
    try:
        servicios_str = ", ".join(listaServicios)
        
        prompt = (
            "Actúa como un experto en triaje de emergencias vehiculares. "
            f'Analiza el siguiente reporte del cliente: "{descripcion}". '
            f"Clasifica la emergencia en UNA de las siguientes categorías disponibles: [{servicios_str}]. "
            "Responde exclusivamente con el nombre de la categoría, exactamente como aparece en la lista, sin texto adicional. "
            "Si no puedes clasificarlo, responde exactamente con la frase: MECÁNICA LIGERA"
        )
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.0, # Temperatura 0 para que sea estricto y no invente cosas
            "max_tokens": 30
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            respuesta = result["choices"][0]["message"]["content"].strip()
            # A veces Llama responde entre comillas, las quitamos por si acaso
            respuesta = respuesta.replace('"', '').replace("'", "")
            return respuesta
        else:
            print(f"Error en Groq API ({response.status_code}): {response.text}")
            return "MECÁNICA LIGERA"
            
    except Exception as e:
        print(f"Error de conexión en clasificación IA (Groq): {e}")
        return "MECÁNICA LIGERA"
