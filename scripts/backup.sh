#!/bin/bash

# Script de backup para el Sistema de Gestión Empresarial
# Crea respaldos de la base de datos y configuraciones

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
BACKUP_DIR="./backups"
DATE=$(date +"%Y%m%d_%H%M%S")
DB_BACKUP_FILE="database_backup_${DATE}.sql"
CONFIG_BACKUP_FILE="config_backup_${DATE}.tar.gz"

echo -e "${BLUE}💾 Sistema de Backup - Gestión Empresarial${NC}"
echo "============================================="

# Crear directorio de backups si no existe
mkdir -p $BACKUP_DIR

# Función para backup de base de datos
backup_database() {
    echo "🗄️  Creando backup de base de datos..."
    
    # Verificar que la base de datos está corriendo
    if ! docker-compose ps database | grep -q "Up"; then
        echo -e "${RED}❌ Error: La base de datos no está ejecutándose${NC}"
        echo "Inicia los servicios primero con: ./scripts/dev.sh o ./scripts/prod.sh"
        exit 1
    fi
    
    # Crear backup
    docker-compose exec -T database pg_dump -U admin -d inventario > "${BACKUP_DIR}/${DB_BACKUP_FILE}"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Backup de base de datos creado: ${DB_BACKUP_FILE}${NC}"
        
        # Comprimir backup
        gzip "${BACKUP_DIR}/${DB_BACKUP_FILE}"
        echo -e "${GREEN}✅ Backup comprimido: ${DB_BACKUP_FILE}.gz${NC}"
    else
        echo -e "${RED}❌ Error al crear backup de base de datos${NC}"
        exit 1
    fi
}

# Función para backup de configuraciones
backup_configs() {
    echo "⚙️  Creando backup de configuraciones..."
    
    # Crear tar con archivos de configuración importantes
    tar -czf "${BACKUP_DIR}/${CONFIG_BACKUP_FILE}" \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env' \
        docker-compose*.yml \
        .env.example \
        nginx/ \
        scripts/ \
        CLAUDE.md \
        memory-bank/ \
        2>/dev/null || true
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Backup de configuraciones creado: ${CONFIG_BACKUP_FILE}${NC}"
    else
        echo -e "${RED}❌ Error al crear backup de configuraciones${NC}"
        exit 1
    fi
}

# Función para limpiar backups antiguos
cleanup_old_backups() {
    echo "🧹 Limpiando backups antiguos (más de 30 días)..."
    
    find $BACKUP_DIR -name "*.sql.gz" -type f -mtime +30 -delete 2>/dev/null || true
    find $BACKUP_DIR -name "*.tar.gz" -type f -mtime +30 -delete 2>/dev/null || true
    
    echo -e "${GREEN}✅ Limpieza completada${NC}"
}

# Función para mostrar información de backups
show_backup_info() {
    echo ""
    echo "📊 Información de backups:"
    echo "=========================="
    
    if [ -d "$BACKUP_DIR" ] && [ "$(ls -A $BACKUP_DIR)" ]; then
        echo "📁 Directorio de backups: $BACKUP_DIR"
        echo "📈 Espacio utilizado: $(du -sh $BACKUP_DIR | cut -f1)"
        echo ""
        echo "📋 Backups disponibles:"
        ls -lh $BACKUP_DIR | tail -n +2 | while read line; do
            echo "   $line"
        done
    else
        echo "📭 No hay backups disponibles"
    fi
}

# Menú principal
echo "Selecciona una opción:"
echo "1) Backup completo (base de datos + configuraciones)"
echo "2) Solo backup de base de datos"
echo "3) Solo backup de configuraciones"
echo "4) Limpiar backups antiguos"
echo "5) Mostrar información de backups"
echo "6) Salir"
echo ""
read -p "Opción [1-6]: " choice

case $choice in
    1)
        backup_database
        backup_configs
        cleanup_old_backups
        show_backup_info
        ;;
    2)
        backup_database
        ;;
    3)
        backup_configs
        ;;
    4)
        cleanup_old_backups
        show_backup_info
        ;;
    5)
        show_backup_info
        ;;
    6)
        echo "👋 Saliendo..."
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Opción inválida${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}🎉 Operación completada${NC}"
echo ""
echo "📝 Comandos útiles:"
echo "   Restaurar DB: docker-compose exec -T database psql -U admin -d inventario < backup.sql"
echo "   Ver backups:  ls -lh ${BACKUP_DIR}/"
echo ""