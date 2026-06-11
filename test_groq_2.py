import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

def test_groq():
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    servicios_str = "Neumáticos, Mecánica Ligera, Batería, Cerrajería, Grúa, Electricidad Automotriz"
    descripcion = "las luces de parqueo no funcionan"
    
    prompt = (
        "Actúa como un experto en triaje de emergencias vehiculares. "
        f'Analiza el siguiente reporte del cliente: "{descripcion}". '
        f"Clasifica la emergencia en UNA de las siguientes categorías disponibles: [{servicios_str}]. "
        "Responde exclusivamente con el nombre de la categoría, exactamente como aparece en la lista, sin texto adicional. "
        "Si no puedes clasificarlo, responde exactamente con la frase: MECÁNICA LIGERA"
    )
    
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.0,
        "max_tokens": 30
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        respuesta_ia = result["choices"][0]["message"]["content"].strip().replace('"', '').replace("'", "")
        print(f"Respuesta IA: '{respuesta_ia}'")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_groq()
