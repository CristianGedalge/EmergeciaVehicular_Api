import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

async def traducirPromptASQL(prompt: str, taller_id: int) -> str:
    """
    Toma un prompt en lenguaje natural del usuario (ej. 'dame los mecanicos con mas servicios finalizados')
    y utiliza Groq (Llama 3) para traducirlo a una consulta SQL válida en PostgreSQL.
    Aplica siempre el filtro de taller_id para seguridad.
    """
    try:
        # Definición del esquema de la BD en texto plano para el modelo
        schema = """
        Tabla `usuario`: id, nombre, correo
        Tabla `taller`: id, nombre
        Tabla `mecanico`: id, usuario_id, taller_id, especialidad (Para obtener el nombre del mecanico haz JOIN con usuario on usuario.id = mecanico.usuario_id)
        Tabla `vehiculo`: id, placa, marca, modelo, color
        Tabla `tipo_servicio`: id, nombre, precio_base
        Tabla `solicitud`: id, cliente_id (referencia a usuario.id), vehiculo_id, taller_id, mecanico_id, tipo_servicio_id, descripcion, precio_estimado, precio_final, estado (PENDIENTE, ACEPTADO, EN_CAMINO, EN_SITIO, FINALIZADO, CANCELADO), fecha_creacion, fecha_aceptado, fecha_en_camino, fecha_en_sitio, fecha_finalizado, fecha_cancelado
        """

        regla_seguridad = ""
        if taller_id:
            regla_seguridad = f"REGLA DE ORO 1: El SQL DEBE incluir siempre la condición 'solicitud.taller_id = {taller_id}' o 'mecanico.taller_id = {taller_id}' dependiendo de la tabla principal que uses, para garantizar que el admin solo vea datos de SU taller.\n"
        else:
            regla_seguridad = "REGLA DE ORO 1: El usuario que consulta es un SUPERADMINISTRADOR. NO FILTRES POR TALLER_ID, DEBES MOSTRAR LA INFORMACIÓN GLOBAL DE TODOS LOS TALLERES (salvo que el usuario pida explícitamente la de un taller específico).\n"

        instrucciones = (
            "Eres un experto analista de datos. Te daré un esquema de base de datos PostgreSQL y una solicitud de un usuario. "
            "Tu único trabajo es generar la consulta SQL 'SELECT' que responda a la solicitud del usuario. "
            f"\n\nEsquema:\n{schema}\n\n"
            f"{regla_seguridad}"
            "REGLA DE ORO 2: Devuelve ÚNICAMENTE la consulta SQL pura. NADA de markdown, NADA de explicaciones, NADA de bloques ```sql. Solamente el texto de la consulta que empiece con SELECT.\n"
            "REGLA DE ORO 3: Las columnas seleccionadas deben tener un alias entendible (usar AS) porque serán las columnas de la tabla en el frontend.\n"
            "REGLA DE ORO 4: NO uses funciones de fecha específicas que no sean ANSI SQL estándar o propias de Postgres (puedes usar COUNT, SUM, MAX, MIN, AVG, EXTRACT).\n\n"
            f"Solicitud del usuario: '{prompt}'"
        )
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "user",
                    "content": instrucciones
                }
            ],
            "temperature": 0.0,
            "max_tokens": 500
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            sql_query = result["choices"][0]["message"]["content"].strip()
            
            # Limpieza por si Llama 3 no obedece y pone markdown
            if sql_query.startswith("```sql"):
                sql_query = sql_query[6:]
            if sql_query.startswith("```"):
                sql_query = sql_query[3:]
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]
            
            sql_query = sql_query.strip()
            
            # Validacion básica de seguridad
            if not sql_query.upper().startswith("SELECT"):
                raise ValueError("La consulta generada no es un SELECT válido.")
            if any(forbidden in sql_query.upper() for forbidden in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]):
                raise ValueError("La consulta contiene palabras reservadas no permitidas.")
                
            return sql_query
        else:
            print(f"Error en Groq API ({response.status_code}): {response.text}")
            return None
            
    except Exception as e:
        print(f"Error en traduccion SQL (Groq): {e}")
        return None
