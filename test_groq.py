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
    
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "user",
                "content": "Hola, ¿estás funcionando? Responde en una oración corta."
            }
        ]
    }
    
    print("Enviando petición a Groq API...")
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            respuesta_ia = result["choices"][0]["message"]["content"]
            print("\n✅ ¡Éxito! Groq API respondió:")
            print(f"> {respuesta_ia}")
        else:
            print("\n❌ Error en la API:")
            print(f"Status Code: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"\n❌ Error de conexión: {e}")

if __name__ == "__main__":
    test_groq()
