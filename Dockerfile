# Use a matching Python version
FROM python:3.13-slim-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy only the files needed for dependency installation
COPY pyproject.toml uv.lock ./

# Install dependencies without dynamic dev dependencies
# --frozen ensures we use the exact versions from uv.lock
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the application
COPY . .

# Final sync to install the project itself
RUN uv sync --frozen --no-dev

# Expose the port FastAPI runs on
EXPOSE 8000

# Set environment variables for better logging and behavior
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

# Command to run the application
# We use .venv/bin/uvicorn because uv sync creates a virtualenv in /app/.venv
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
