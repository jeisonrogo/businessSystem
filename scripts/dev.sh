#!/bin/bash

# Script para desarrollo del Sistema de Gestión Empresarial
# Inicia todos los servicios en modo desarrollo con hot reload

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛠️  Iniciando Sistema de Gestión Empresarial - DESARROLLO${NC}"
echo "=================================================="

# Verificar que existe el archivo .env
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: No se encontró el archivo .env${NC}"
    echo "Ejecuta primero: ./scripts/setup.sh"
    exit 1
fi

# Parar servicios existentes
echo "🛑 Deteniendo servicios existentes..."
docker-compose down

# Limpiar contenedores e imágenes huérfanas (opcional)
echo "🧹 Limpiando contenedores huérfanos..."
docker system prune -f

# Construir y iniciar servicios en modo desarrollo
echo "🏗️  Construyendo imágenes..."
docker-compose build

echo "🚀 Iniciando servicios en modo desarrollo..."
docker-compose up -d database

# Esperar a que la base de datos esté lista
echo "⏳ Esperando a que la base de datos esté lista..."
sleep 10

# Iniciar backend
echo "🎯 Iniciando backend API..."
docker-compose up -d backend

# Esperar a que el backend esté listo
echo "⏳ Esperando a que el backend esté listo..."
sleep 15

# Ejecutar migraciones de Alembic
echo "📊 Ejecutando migraciones de base de datos..."
docker-compose exec backend alembic upgrade head

# Inicializar base de datos con datos completos
read -p "¿Deseas inicializar la base de datos con datos completos? (usuarios, contabilidad, productos) (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "📁 Inicializando base de datos con datos completos..."
    docker-compose exec backend python scripts/init_database.py
else
    # Opcional: Solo poblar datos básicos de demostración
    read -p "¿Deseas poblar solo datos básicos de demostración? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📁 Poblando datos básicos de demostración..."
        docker-compose exec backend python populate_demo_data.py
    fi
fi

# Iniciar frontend
echo "🎨 Iniciando frontend..."
docker-compose up -d frontend

echo ""
echo -e "${GREEN}🎉 Sistema iniciado en modo desarrollo${NC}"
echo ""
echo "📋 Servicios disponibles:"
echo -e "   🌐 Frontend:  ${BLUE}http://localhost:3000${NC}"
echo -e "   🔧 Backend:   ${BLUE}http://localhost:8000${NC}"
echo -e "   📚 API Docs:  ${BLUE}http://localhost:8000/docs${NC}"
echo -e "   🗄️  Database: ${BLUE}localhost:5432${NC}"
echo ""
echo "📝 Comandos útiles:"
echo "   Ver logs:        docker-compose logs -f [servicio]"
echo "   Parar servicios: docker-compose down"
echo "   Reiniciar:       docker-compose restart [servicio]"
echo ""
echo "🔍 Para ver logs en tiempo real:"
echo "   docker-compose logs -f"
echo ""