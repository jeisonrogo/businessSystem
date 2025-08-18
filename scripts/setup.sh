#!/bin/bash

# Script de configuración inicial para el Sistema de Gestión Empresarial
# Este script prepara el entorno para el primer despliegue

set -e

echo "🚀 Configuración inicial del Sistema de Gestión Empresarial"
echo "=================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar dependencias
check_dependency() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ Error: $1 no está instalado${NC}"
        echo "Por favor instala $1 y vuelve a ejecutar este script"
        exit 1
    else
        echo -e "${GREEN}✅ $1 encontrado${NC}"
    fi
}

echo "🔍 Verificando dependencias..."
check_dependency "docker"
check_dependency "docker-compose"

# Crear archivo .env si no existe
if [ ! -f .env ]; then
    echo "📝 Creando archivo .env desde .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Por favor, edita el archivo .env con tus configuraciones específicas${NC}"
else
    echo -e "${GREEN}✅ Archivo .env ya existe${NC}"
fi

# Generar JWT secret si no está configurado
if grep -q "your-secret-key-change-in-production" .env; then
    echo "🔑 Generando JWT secret key..."
    JWT_SECRET=$(openssl rand -hex 32)
    # Crear archivo temporal para compatibilidad con macOS
    sed "s/your-secret-key-change-in-production/$JWT_SECRET/g" .env > .env.tmp && mv .env.tmp .env
    echo -e "${GREEN}✅ JWT secret key generado${NC}"
fi

# Crear directorios necesarios
echo "📁 Creando directorios necesarios..."
mkdir -p nginx/conf.d
mkdir -p ssl
mkdir -p logs

# Crear configuración básica de nginx para producción
if [ ! -f nginx/nginx.conf ]; then
    echo "⚙️ Creando configuración de Nginx..."
    cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }
    
    upstream frontend {
        server frontend:80;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        location /api/ {
            proxy_pass http://backend/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        location / {
            proxy_pass http://frontend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF
    echo -e "${GREEN}✅ Configuración de Nginx creada${NC}"
fi

# Configurar permisos
echo "🔒 Configurando permisos..."
chmod +x scripts/*.sh

echo ""
echo -e "${GREEN}🎉 Configuración inicial completada${NC}"
echo ""
echo "📋 Próximos pasos:"
echo "1. Revisa y ajusta el archivo .env según tus necesidades"
echo "2. Para desarrollo, ejecuta: ./scripts/dev.sh"
echo "3. Para producción, ejecuta: ./scripts/prod.sh"
echo ""
echo "📚 Documentación disponible en:"
echo "   - README.md"
echo "   - memory-bank/progress.md"
echo ""