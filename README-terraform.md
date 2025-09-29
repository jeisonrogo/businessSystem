# 🚀 AWS Deployment con Terraform

## 📋 Resumen Ejecutivo

Sistema completo de despliegue para la aplicación de gestión empresarial multi-tenant en AWS, optimizado para costos mínimos y máximo aprovechamiento del Free Tier.

## 💰 Costos Estimados

### Primer Año (Con Free Tier)
- **Costo mensual**: $17-20 USD
- **Costo anual**: ~$204-240 USD

### Después del Free Tier
- **Costo mensual**: $30-35 USD
- **Costo anual**: ~$360-420 USD

## 🏗️ Arquitectura Desplegada

```
Internet
    ↓
CloudFront CDN (Frontend React)
    ↓
App Runner (FastAPI Backend) ←→ RDS PostgreSQL
    ↓
S3 (File Storage)
```

## 📁 Estructura de Archivos

```
terraform/
├── main.tf                 # Configuración principal
├── variables.tf            # Variables de entrada
├── outputs.tf             # Outputs del despliegue
├── modules/               # Módulos reutilizables
│   ├── vpc/              # Red y subnets
│   ├── rds/              # Base de datos
│   ├── app-runner/       # Backend application
│   ├── s3-frontend/      # Frontend hosting
│   └── monitoring/       # CloudWatch y alertas
├── environments/
│   ├── dev/
│   │   └── terraform.tfvars
│   └── prod/
│       └── terraform.tfvars
└── scripts/
    └── deploy.sh         # Script de despliegue automático
```

## 🛠️ Pre-requisitos

### Herramientas Requeridas
```bash
# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# jq (para procesamiento JSON)
sudo apt-get install jq
```

### Configuración AWS
```bash
# Configurar credenciales AWS para el perfil 'personal'
aws configure --profile personal

# Verificar configuración
aws sts get-caller-identity --profile personal

# Verificar que el perfil existe
aws configure list-profiles

# Validar configuración completa (recomendado)
./terraform/scripts/validate-aws-profile.sh
```

## 🚀 Despliegue Rápido

### Opción 1: Script Automático (Recomendado)
```bash
# Clonar repositorio y navegar
cd businessSystem/terraform

# Ejecutar despliegue completo
./scripts/deploy.sh dev

# Para producción
./scripts/deploy.sh prod
```

### Opción 2: Manual
```bash
# 1. Inicializar Terraform
cd terraform
terraform init

# 2. Planificar despliegue
terraform plan -var-file="environments/dev/terraform.tfvars"

# 3. Aplicar cambios
terraform apply -var-file="environments/dev/terraform.tfvars"

# 4. Subir frontend
aws s3 sync ../frontend/build s3://$(terraform output -raw s3_frontend_bucket_name)

# 5. Invalidar CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw cloudfront_distribution_id) \
  --paths "/*"
```

## ⚙️ Configuración del Entorno

### Variables Principales (terraform.tfvars)

```hcl
# Configuración general
project_name = "business-system"
environment  = "dev"
aws_region   = "us-east-1"
aws_profile  = "personal"

# Base de datos (Free Tier)
db_instance_class = "db.t3.micro"
db_allocated_storage = 20

# Backend (Mínimo costo)
app_runner_cpu = 256
app_runner_memory = 512
app_runner_min_size = 1

# Frontend
domain_name = ""  # Opcional: tu-dominio.com
ssl_certificate_arn = ""  # Opcional: ARN del certificado SSL

# Alertas
alert_email = "tu-email@empresa.com"
billing_alert_threshold = 25
```

### Variables de Entorno Backend

Después del despliegue, configurar estas variables:

```bash
# Obtener información de conexión
DATABASE_URL=$(terraform output -raw database_connection_info | jq -r .host)
AWS_S3_BUCKET=$(terraform output -raw s3_files_bucket_name)

# Obtener password de la base de datos
aws secretsmanager get-secret-value \
  --secret-id $(terraform output -raw secrets_manager_secret_name) \
  --query SecretString --output text
```

## 🔄 CI/CD y Automatización

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Deploy with script
        run: ./terraform/scripts/deploy.sh prod
```

### Comandos Útiles Post-Despliegue

```bash
# Ver logs del backend
aws logs tail /aws/apprunner/business-system-prod-service/application --follow --profile personal

# Actualizar frontend
aws s3 sync frontend/build s3://BUCKET_NAME --profile personal
aws cloudfront create-invalidation --distribution-id DISTRIBUTION_ID --paths "/*" --profile personal

# Conectar a la base de datos
psql $(terraform output -raw database_connection_info | jq -r '"postgresql://\(.username):\(.password)@\(.host):\(.port)/\(.database)"')

# Ver métricas en CloudWatch
aws cloudwatch get-metric-statistics \
  --namespace AWS/AppRunner \
  --metric-name CPUUtilization \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 3600 \
  --statistics Average \
  --profile personal
```

## 📊 Monitoreo y Alertas

### CloudWatch Dashboards Incluidos
- CPU y memoria del App Runner
- Conexiones y performance de RDS
- Requests y errores de CloudFront
- Costos y facturación

### Alertas Configuradas
- CPU alto en App Runner (>70%)
- Conexiones RDS altas (>80%)
- Errores HTTP 5xx
- Threshold de costos mensuales

### Acceder al Dashboard
```bash
# URL del dashboard
terraform output cloudwatch_dashboard_url
```

## 🔒 Seguridad

### Medidas Implementadas
- VPC privada con subnets aisladas
- Security Groups restrictivos
- Encryption en reposo (RDS, S3)
- SSL/TLS en tránsito
- IAM roles con least privilege
- Secrets Manager para passwords

### Revisión de Seguridad
```bash
# Verificar Security Groups
aws ec2 describe-security-groups --group-ids $(terraform output -json resource_arns | jq -r .rds_security_group_id)

# Verificar encryption
aws rds describe-db-instances --db-instance-identifier $(terraform output -raw rds_instance_id)
```

## 💾 Backup y Recuperación

### Configuración de Backups
- **RDS**: Backup automático 7 días
- **S3**: Versioning habilitado
- **Terraform State**: Recomendado backend remoto

### Restaurar desde Backup
```bash
# Listar backups disponibles
aws rds describe-db-snapshots --db-instance-identifier $(terraform output -raw rds_instance_id) --profile personal

# Restaurar RDS
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier business-system-restored \
  --db-snapshot-identifier SNAPSHOT_ID \
  --profile personal
```

## 📈 Escalabilidad

### Auto Scaling Configurado
- **App Runner**: 1-10 instancias automático
- **RDS**: Storage auto-scaling hasta 100GB
- **CloudFront**: Global automático

### Escalar Manualmente
```bash
# Aumentar instancias App Runner
terraform apply -var="app_runner_max_size=20"

# Aumentar RDS instance class
terraform apply -var="db_instance_class=db.t3.small"
```

## 🛠️ Troubleshooting

### Errores Comunes

#### 1. "Insufficient IAM permissions"
```bash
# Verificar políticas IAM
aws iam list-attached-user-policies --user-name YOUR_USERNAME --profile personal

# Verificar perfil configurado
aws configure list --profile personal
```

#### 2. "App Runner build failed"
```bash
# Verificar logs de build
aws apprunner list-operations --service-arn $(terraform output -raw app_runner_service_arn)
```

#### 3. "RDS connection timeout"
```bash
# Verificar Security Groups
aws ec2 describe-security-groups --filters "Name=group-name,Values=*rds*" --profile personal
```

### Logs y Debugging
```bash
# App Runner logs
aws logs describe-log-groups --log-group-name-prefix "/aws/apprunner" --profile personal

# CloudFront logs (si habilitado)
aws s3 ls s3://cloudfront-logs-bucket/ --profile personal

# VPC Flow Logs (si habilitado)
aws logs describe-log-streams --log-group-name "/aws/vpc/flow-logs/business-system-dev" --profile personal
```

## 🗑️ Limpieza y Destrucción

### Destruir Infraestructura
```bash
# Destruir todo (CUIDADO: No reversible)
terraform destroy -var-file="environments/dev/terraform.tfvars"

# Destruir recursos específicos
terraform destroy -target=module.app_runner
```

### Limpieza de Costos
```bash
# Detener App Runner temporalmente
aws apprunner pause-service --service-arn $(terraform output -raw app_runner_service_arn) --profile personal

# Eliminar snapshots antiguos
aws rds delete-db-snapshot --db-snapshot-identifier SNAPSHOT_ID --profile personal
```

## 📞 Soporte y Recursos

### Documentación AWS
- [App Runner Pricing](https://aws.amazon.com/apprunner/pricing/)
- [RDS Free Tier](https://aws.amazon.com/rds/free/)
- [CloudFront Pricing](https://aws.amazon.com/cloudfront/pricing/)

### Contacto
- **Issues**: Crear issue en GitHub
- **Emergencias**: Revisar CloudWatch Alarms
- **Costos**: AWS Cost Explorer

---

**Generado por**: Claude Code Analysis
**Fecha**: $(date)
**Versión**: 1.0