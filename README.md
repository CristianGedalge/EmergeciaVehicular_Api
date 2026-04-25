# EmergenciaVehicular_API

Este proyecto es una API para la gestión de emergencias vehiculares.


## Requisitos Previos

Para ejecutar este proyecto, asegúrate de tener instalado lo siguiente:

1.  **Python**: Tener instalado Python (versión 3.x).
2.  **UV**: Debe estar instalado de forma global. Abre una terminal y ejecuta:
        ```bash
        pip install uv
        ```
   (Solo este paso se hace con pip, todo lo demás se hace con UV)

## Ejecución del Proyecto


Sigue estos pasos para configurar y ejecutar el proyecto localmente:


1.  **Crear y sincronizar el entorno virtual y las dependencias:**
                ```bash
                uv venv
                uv sync
                ```

2.  **Activar el entorno virtual:**
                - En Windows:
                        ```bash
                        .venv\Scripts\activate
                        ```
                - En macOS/Linux:
                        ```bash
                        source .venv/bin/activate
                        ```

3.  **Ejecutar la aplicación:**
                ```bash
                uv run uvicorn app.main:app --reload
                ```

---
Desarrollado para SI2 - Semestre 1-2026.
