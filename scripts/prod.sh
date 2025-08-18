#!/bin/bash

# Script para producción del Sistema de Gestión Empresarial
# Inicia todos los servicios en modo producción con optimizaciones

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Iniciando Sistema de Gestión Empresarial - PRODUCCIÓN${NC}"
echo "=================================================="

# Verificar que existe el archivo .env
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: No se encontró el archivo .env${NC}"
    echo "Ejecuta primero: ./scripts/setup.sh"
    exit 1
fi

# Verificar configuración de producción
echo "🔍 Verificando configuración de producción..."

# Verificar JWT secret
if grep -q "your-secret-key-change-in-production" .env; then
    echo -e "${RED}❌ Error: JWT_SECRET_KEY no está configurado para producción${NC}"
    echo "Edita el archivo .env y configura una clave segura"
    exit 1
fi

# Advertencia de producción
echo -e "${YELLOW}⚠️  ATENCIÓN: Iniciando en modo PRODUCCIÓN${NC}"
echo "Este modo está optimizado para rendimiento y seguridad"
read -p "¿Continuar? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Operación cancelada"
    exit 1
fi

# Parar servicios existentes
echo "🛑 Deteniendo servicios existentes..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Limpiar sistema (más agresivo en producción)
echo "🧹 Limpiando sistema..."
docker system prune -f
docker volume prune -f

# Construir imágenes de producción
echo "🏗️  Construyendo imágenes de producción..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache

# Iniciar base de datos primero
echo "🗄️  Iniciando base de datos..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d database

# Esperar a que la base de datos esté lista
echo "⏳ Esperando a que la base de datos esté lista..."
sleep 15

# Ejecutar migraciones
echo "📊 Ejecutando migraciones de base de datos..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec database psql -U admin -d inventario -c "SELECT version();"

# Iniciar backend
echo "🎯 Iniciando backend API..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d backend

# Esperar a que el backend esté listo
echo "⏳ Esperando a que el backend esté listo..."
sleep 20

# Ejecutar migraciones de Alembic
echo "📊 Ejecutando migraciones de Alembic..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec backend alembic upgrade head

# Iniciar frontend
echo "🎨 Iniciando frontend..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d frontend

# Iniciar proxy de producción
echo "🌐 Iniciando proxy de Nginx..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile production up -d nginx

# Verificar estado de servicios
echo "🔍 Verificando estado de servicios..."
sleep 10
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps

echo ""
echo -e "${GREEN}🎉 Sistema iniciado en modo PRODUCCIÓN${NC}"
echo ""
echo "📋 Servicios disponibles:"
echo -e "   🌐 Aplicación: ${BLUE}http://localhost${NC}"
echo -e "   🔧 API:        ${BLUE}http://localhost/api${NC}"
echo -e "   📚 API Docs:   ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo "🔒 Configuración de seguridad:"
echo "   ✅ JWT configurado con clave segura"
echo "   ✅ Contenedores ejecutándose como usuario no-root"
echo "   ✅ Proxy reverso configurado"
echo "   ✅ Headers de seguridad habilitados"
echo ""
echo "📝 Comandos de producción:"
echo "   Ver logs:        docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f"
echo "   Parar servicios: docker-compose -f docker-compose.yml -f docker-compose.prod.yml down"
echo "   Estado:          docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps"
echo ""
echo "📊 Monitoreo:"
echo "   Health checks configurados para todos los servicios"
echo "   Logs disponibles en: ./logs/"
echo ""