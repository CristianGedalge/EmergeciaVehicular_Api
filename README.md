# EmergenciaVehicular_API

API para la gestión de emergencias vehiculares.

---

## Requisitos Previos

- **Python 3.x**
- **UV** (gestor de entornos y dependencias)

Instala UV globalmente (solo este paso es con pip):

```
pip install uv
```

---

## Configuración y Ejecución

1. **Crear el entorno virtual y sincronizar dependencias:**

```
uv venv
uv sync
```

2. **Activar el entorno virtual:**

                - **Windows:**
                        ```
                        .venv\Scripts\activate
                        ```
                - **macOS/Linux:**
                        ```
                        source .venv/bin/activate
                        ```

3. **Configura tus variables de entorno:**

        Copia el archivo `.env.template` a `.env` y completa los datos de conexión a tu base de datos PostgreSQL.

4. **Ejecutar la aplicación:**

```
uv run fastapi dev app/main.py
```