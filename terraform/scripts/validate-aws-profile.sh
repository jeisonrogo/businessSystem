#!/bin/bash

# =============================================================================
# AWS PROFILE VALIDATION SCRIPT
# Validates that the 'personal' AWS profile is configured correctly
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

AWS_PROFILE="${AWS_PROFILE:-personal}"

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

log "Validando configuración del perfil AWS: $AWS_PROFILE"
echo "============================================================="

# 1. Check if AWS CLI is installed
log "1. Verificando instalación de AWS CLI..."
if ! command -v aws &> /dev/null; then
    error "AWS CLI no está instalado. Instálalo con: curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip'"
fi

aws_version=$(aws --version)
success "AWS CLI instalado: $aws_version"

# 2. List all profiles
log "2. Listando perfiles disponibles..."
if aws configure list-profiles &> /dev/null; then
    echo "Perfiles configurados:"
    aws configure list-profiles | while read profile; do
        echo "  - $profile"
    done
else
    warning "No se pudieron listar los perfiles"
fi

# 3. Check if personal profile exists
log "3. Verificando perfil '$AWS_PROFILE'..."
if aws configure list-profiles | grep -q "^$AWS_PROFILE$"; then
    success "Perfil '$AWS_PROFILE' encontrado"
else
    error "Perfil '$AWS_PROFILE' no encontrado. Configúralo con: aws configure --profile $AWS_PROFILE"
fi

# 4. Show profile configuration
log "4. Mostrando configuración del perfil..."
echo "Configuración del perfil '$AWS_PROFILE':"
aws configure list --profile "$AWS_PROFILE" || error "No se pudo obtener la configuración del perfil"

# 5. Test credentials
log "5. Probando credenciales..."
if aws sts get-caller-identity --profile "$AWS_PROFILE" &> /dev/null; then
    identity=$(aws sts get-caller-identity --profile "$AWS_PROFILE")
    success "Credenciales válidas"

    echo "Información de la cuenta:"
    echo "$identity" | jq -r '"  Account: " + .Account'
    echo "$identity" | jq -r '"  User: " + .Arn'
    echo "$identity" | jq -r '"  UserId: " + .UserId'
else
    error "Credenciales inválidas para el perfil '$AWS_PROFILE'. Reconfigura con: aws configure --profile $AWS_PROFILE"
fi

# 6. Check region
log "6. Verificando región..."
region=$(aws configure get region --profile "$AWS_PROFILE" || echo "")
if [[ -n "$region" ]]; then
    success "Región configurada: $region"

    # Recommend us-east-1 for cost optimization
    if [[ "$region" != "us-east-1" ]]; then
        warning "Para máximo aprovechamiento del Free Tier, se recomienda us-east-1"
        echo "  Cambiar región: aws configure set region us-east-1 --profile $AWS_PROFILE"
    fi
else
    warning "No se encontró región configurada"
    echo "  Configurar región: aws configure set region us-east-1 --profile $AWS_PROFILE"
fi

# 7. Check permissions (basic test)
log "7. Verificando permisos básicos..."

# Test S3 permissions
if aws s3 ls --profile "$AWS_PROFILE" &> /dev/null; then
    success "Permisos S3: OK"
else
    warning "Permisos S3: Limitados o no disponibles"
fi

# Test EC2 permissions
if aws ec2 describe-regions --profile "$AWS_PROFILE" &> /dev/null; then
    success "Permisos EC2: OK"
else
    warning "Permisos EC2: Limitados o no disponibles"
fi

# Test RDS permissions
if aws rds describe-db-instances --profile "$AWS_PROFILE" &> /dev/null; then
    success "Permisos RDS: OK"
else
    warning "Permisos RDS: Limitados o no disponibles"
fi

# 8. Environment variable check
log "8. Verificando variables de entorno..."
if [[ -n "${AWS_PROFILE:-}" ]]; then
    if [[ "$AWS_PROFILE" == "personal" ]]; then
        success "Variable AWS_PROFILE configurada correctamente: $AWS_PROFILE"
    else
        warning "Variable AWS_PROFILE configurada pero no es 'personal': $AWS_PROFILE"
    fi
else
    warning "Variable AWS_PROFILE no configurada"
    echo "  Configurar con: export AWS_PROFILE=personal"
fi

echo ""
echo "============================================================="
success "Validación completada para el perfil '$AWS_PROFILE'"

# Summary and recommendations
echo ""
echo "📋 RESUMEN Y RECOMENDACIONES:"
echo ""

# Check if everything is ready for deployment
all_checks_passed=true

if ! aws configure list-profiles | grep -q "^$AWS_PROFILE$"; then
    all_checks_passed=false
fi

if ! aws sts get-caller-identity --profile "$AWS_PROFILE" &> /dev/null; then
    all_checks_passed=false
fi

region=$(aws configure get region --profile "$AWS_PROFILE" || echo "")
if [[ -z "$region" ]]; then
    all_checks_passed=false
fi

if [[ "$all_checks_passed" == "true" ]]; then
    success "✅ Perfil listo para despliegue"
    echo ""
    echo "Comandos para usar:"
    echo "  # Desplegar en desarrollo"
    echo "  ./terraform/scripts/deploy.sh dev"
    echo ""
    echo "  # Verificar configuración Terraform"
    echo "  cd terraform && terraform plan -var-file='environments/dev/terraform.tfvars'"
else
    error "❌ Configuración incompleta"
    echo ""
    echo "Pasos pendientes:"

    if ! aws configure list-profiles | grep -q "^$AWS_PROFILE$"; then
        echo "  1. aws configure --profile $AWS_PROFILE"
    fi

    if [[ -z "$region" ]]; then
        echo "  2. aws configure set region us-east-1 --profile $AWS_PROFILE"
    fi

    echo "  3. Verificar permisos IAM en la consola AWS"
fi

echo ""
echo "Para más información, consulta: README-terraform.md"