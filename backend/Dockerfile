# Backend Dockerfile para Sistema de Gestión Empresarial
# Usa Python 3.11 slim para optimizar el tamaño
FROM python:3.11-slim

# Información del mantenedor
LABEL maintainer="Sistema de Gestión Empresarial"
LABEL description="Backend API para sistema empresarial con FastAPI"

# Establecer directorio de trabajo
WORKDIR /app

# Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivo de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Exponer puerto
EXPOSE 8000

# Variables de entorno por defecto
ENV DATABASE_URL="postgresql+psycopg://admin:admin@database:5432/inventario" \
    JWT_SECRET_KEY="your-secret-key-change-in-production" \
    ALGORITHM="HS256" \
    ACCESS_TOKEN_EXPIRE_MINUTES="30"

# Comando de inicio
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]