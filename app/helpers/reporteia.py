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
        # Definición detallada y exacta del esquema de base de datos real
        schema = """
        Tablas y columnas:
        - `usuario`: id, nombre, correo, rol ('admin', 'mecanico', 'cliente'), telefono, estado (boolean), fecha_creacion
        - `taller`: id, nombre, direccion, telefono, latitud, longitud, admin_id (relaciona a usuario.id), puntaje, estado (boolean)
        - `mecanico`: id, usuario_id (relaciona a usuario.id), taller_id (relaciona a taller.id), disponible (boolean), estado (boolean)
        - `mecanico_especialidad`: id, mecanico_id (relaciona a mecanico.id), tipo_servicio_id (relaciona a tipo_servicio.id)
        - `tipo_servicio`: id, nombre, descripcion, palabras_clave, estado (boolean)
        - `vehiculo`: id, cliente_id (relaciona a usuario.id), marca, modelo, anio, placa, color, estado (boolean)
        - `solicitud`: id, cliente_id (relaciona a usuario.id), vehiculo_id (relaciona a vehiculo.id), taller_id (relaciona a taller.id), mecanico_id (relaciona a mecanico.id), tipo_servicio_id (relaciona a tipo_servicio.id), descripcion, precio_estimado (float), precio_final (float), estado ('PENDIENTE', 'CLASIFICADO', 'PUBLICADO', 'ACEPTADO', 'ASIGNADO', 'EN_CAMINO', 'EN_SITIO', 'FINALIZADO', 'CANCELADO'), fecha_creacion, fecha_finalizado, fecha_cancelado
        - `pago`: id, solicitud_id (relaciona a solicitud.id), monto (numeric), metodo_pago ('QR', 'TARJETA', 'EFECTIVO'), estado_pago ('PENDIENTE', 'COMPLETADO', 'FALLIDO'), fecha_pago

        Relaciones importantes:
        - Para obtener el nombre del mecánico: JOIN mecanico ON ... JOIN usuario ON usuario.id = mecanico.usuario_id
        - Para obtener el nombre del cliente: JOIN usuario ON usuario.id = solicitud.cliente_id
        - Las especialidades de un mecánico se obtienen a través de `mecanico_especialidad` haciendo JOIN con `tipo_servicio`.
        """

        regla_seguridad = ""
        if taller_id:
            regla_seguridad = (
                f"REGLA DE ORO 1 (Seguridad): El SQL DEBE incluir siempre la condición de filtrado por tu taller: "
                f"'(solicitud.taller_id = {taller_id})' o '(mecanico.taller_id = {taller_id})' o '(taller.id = {taller_id})' "
                f"dependiendo de las tablas que uses. Esto garantiza seguridad de datos.\n"
            )
        else:
            regla_seguridad = (
                "REGLA DE ORO 1: Eres un SUPERADMINISTRADOR. NO FILTRES POR TALLER, muestra la información de "
                "todos los talleres del sistema de manera global.\n"
            )

        diccionario_sinonimos = """
        DICCIONARIO DE SINÓNIMOS Y MAPEOS (LENGUAJE COLOQUIAL):
        - "plata", "dinero", "ganancias", "ingresos", "caja", "recaudación", "cobrado", "total pagado" -> Tabla `pago`, columna `monto`. Para saber lo efectivamente cobrado, filtrar por `pago.estado_pago = 'COMPLETADO'`.
        - "servicios", "trabajos", "auxilios", "emergencias", "solicitudes", "chambas", "pedidos", "atenciones" -> Tabla `solicitud`.
        - "autos", "carros", "vehículos", "movilidades", "coches", "máquinas" -> Tabla `vehiculo`.
        - "mecánicos", "técnicos", "meca", "operarios", "personal", "trabajadores" -> Tabla `mecanico` unida con `usuario` para obtener el nombre.
        - "clientes", "conductores", "personas", "afectados", "usuarios" -> Tabla `usuario` con rol = 'cliente'.
        - "pagado con tarjeta", "tarjeta", "stripe" -> `pago.metodo_pago = 'TARJETA'`.
        - "pagado con qr", "qr", "transferencia", "simple" -> `pago.metodo_pago = 'QR'`.
        - "efectivo", "en mano", "cash" -> `pago.metodo_pago = 'EFECTIVO'`.
        - "terminados", "finalizados", "hechos", "listos", "completados" -> `solicitud.estado = 'FINALIZADO'`.
        - "cancelados", "anulados", "rechazados" -> `solicitud.estado = 'CANCELADO'`.
        - "en curso", "haciendo", "activos", "atendiendo", "en camino" -> `solicitud.estado` en ('ASIGNADO', 'EN_CAMINO', 'EN_SITIO').
        """

        instrucciones = (
            "Eres un experto analista de datos de PostgreSQL. Te daré el esquema de nuestra base de datos, un diccionario de modismos y la solicitud de un usuario. "
            "Tu tarea es generar la consulta SQL 'SELECT' exacta que responda a lo solicitado.\n\n"
            f"Esquema de Base de Datos:\n{schema}\n\n"
            f"Diccionario de Mapeos:\n{diccionario_sinonimos}\n\n"
            f"{regla_seguridad}"
            "REGLAS ADICIONALES:\n"
            "- REGLA 2: Devuelve ÚNICAMENTE la consulta SQL pura. NADA de explicaciones, NADA de formato markdown, NADA de bloques ```sql. Tu respuesta debe empezar con SELECT.\n"
            "- REGLA 3: Usa alias claros y amigables en español para las columnas seleccionadas (ej. 'SELECT u.nombre AS \"Nombre del Cliente\"') para que el frontend renderice la tabla de forma entendible.\n"
            "- REGLA 4: Flexibilidad de lenguaje. Los usuarios usarán lenguaje natural relajado, términos informales, faltas de ortografía o jergas latinoamericanas. Usa el DICCIONARIO DE SINÓNIMOS para interpretar qué tablas y columnas del esquema se adaptan a su intención semántica. Sé muy flexible y no busques concordancia exacta.\n\n"
            "Ejemplos de traducción a lenguaje natural:\n"
            "Ejemplo 1:\n"
            "Entrada: 'dame la lista de mis mecanicos con su telefono y disponibilidad'\n"
            f"Salida: SELECT u.nombre AS \"Nombre del Mecánico\", u.telefono AS \"Teléfono\", m.disponible AS \"Disponible\" FROM mecanico m JOIN usuario u ON u.id = m.usuario_id WHERE m.taller_id = {taller_id if taller_id else 'm.taller_id'} AND m.estado = true;\n\n"
            "Ejemplo 2:\n"
            "Entrada: 'cuanta plata hemos ganado con tarjeta y QR'\n"
            f"Salida: SELECT p.metodo_pago AS \"Método de Pago\", SUM(p.monto) AS \"Total Recaudado\" FROM pago p JOIN solicitud s ON s.id = p.solicitud_id WHERE s.taller_id = {taller_id if taller_id else 's.taller_id'} AND p.estado_pago = 'COMPLETADO' GROUP BY p.metodo_pago;\n\n"
            "Ejemplo 3:\n"
            "Entrada: 'que autos tienen mis clientes registrados'\n"
            f"Salida: SELECT u.nombre AS \"Cliente\", v.marca AS \"Marca\", v.modelo AS \"Modelo\", v.placa AS \"Placa\" FROM vehiculo v JOIN usuario u ON u.id = v.cliente_id;\n\n"
            f"Solicitud actual del usuario: '{prompt}'"
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
