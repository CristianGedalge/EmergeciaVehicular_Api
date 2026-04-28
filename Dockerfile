# 1. Imagen base
FROM python:3.13-slim-bookworm

# 2. Instalar uv (Copiamos los binarios)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. DEFINIR EL DIRECTORIO DE TRABAJO PRIMERO
WORKDIR /app

# 4. Copiar los archivos de dependencias AL DIRECTORIO ACTUAL (.)
# Asegúrate de que estos archivos estén en la misma carpeta que el Dockerfile en GitHub
COPY pyproject.toml uv.lock ./

# 5. Instalar dependencias
ENV UV_COMPILE_BYTECODE=1
RUN uv sync --frozen --no-dev --no-install-project

# 6. Copiar el resto del código
COPY . .

# 7. Sincronización final del proyecto
RUN uv sync --frozen --no-dev

# 8. Configuración de ejecución
EXPOSE 8000
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

# Ejecutamos usando el path absoluto del venv para evitar fallos
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]