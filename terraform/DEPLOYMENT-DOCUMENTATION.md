# 📋 DOCUMENTACIÓN DE DESPLIEGUE AWS - Business System

## 🎯 Resumen Ejecutivo

Este documento detalla el proceso completo de despliegue del sistema Business System en AWS, incluyendo la creación de la infraestructura con Terraform, construcción y despliegue de la imagen Docker del backend en ECR, y configuración de acceso a la base de datos RDS desde IP pública.

**Fecha de despliegue:** 10 de Octubre, 2025
**Región AWS:** us-east-1 (Norte de Virginia)
**Cuenta AWS:** 327568102873
**Perfil AWS CLI:** personal
**Ambiente:** Development (dev)

---

## 📦 1. CREACIÓN Y CONFIGURACIÓN DEL REPOSITORIO ECR

### 1.1 Repositorio Creado

**Nombre:** `business-system/backend`
**URI:** `327568102873.dkr.ecr.us-east-1.amazonaws.com/business-system/backend`
**ARN:** `arn:aws:ecr:us-east-1:327568102873:repository/business-system/backend`
**Configuración:**
- Image Scanning: Habilitado (scanOnPush: true)
- Encryption: AES256 (por defecto)
- Tag Mutability: MUTABLE
- Fecha de creación: 2025-10-10 17:32:14

### 1.2 Comando de Creación

```bash
aws ecr create-repository \
  --repository-name business-system/backend \
  --image-scanning-configuration scanOnPush=true \
  --region us-east-1 \
  --profile personal
```

---

## 🐳 2. CONSTRUCCIÓN Y DESPLIEGUE DE LA IMAGEN DOCKER

### 2.1 Imagen Docker del Backend

**Base Image:** `python:3.11-slim`
**Directorio de construcción:** `/Users/fitideas/Documents/proyectosJeison/git/businessSystem/backend`
**Dockerfile:** Ubicado en `backend/Dockerfile`

**Características de la imagen:**
- Usuario no-root (appuser) para seguridad
- Puerto expuesto: 8000
- Dependencias instaladas desde requirements.txt
- Variables de entorno configuradas
- Servidor: Uvicorn con FastAPI

### 2.2 Construcción de la Imagen

```bash
cd backend
docker build -t business-system-backend:latest .
```

**Resultado:**
- Tamaño aproximado de la imagen: ~800MB
- Layers: 19 capas
- Digest: sha256:c0e5e1ba2d876342924d3bdd4992f4ad99e7fc934dabe9555b1610d2b999b462

### 2.3 Autenticación en ECR

```bash
aws ecr get-login-password --region us-east-1 --profile personal | \
  docker login --username AWS --password-stdin \
  327568102873.dkr.ecr.us-east-1.amazonaws.com
```

### 2.4 Etiquetado y Push a ECR

```bash
# Etiquetar imagen para ECR
docker tag business-system-backend:latest \
  327568102873.dkr.ecr.us-east-1.amazonaws.com/business-system/backend:latest

docker tag business-system-backend:latest \
  327568102873.dkr.ecr.us-east-1.amazonaws.com/business-system/backend:v1.0.0

# Push a ECR
docker push 327568102873.dkr.ecr.us-east-1.amazonaws.com/business-system/backend:latest
docker push 327568102873.dkr.ecr.us-east-1.amazonaws.com/business-system/backend:v1.0.0
```

**Versiones desplegadas:**
- `latest` - Imagen más reciente para desarrollo
- `v1.0.0` - Primera versión estable etiquetada

---

## ⚙️ 3. CONFIGURACIÓN DE TERRAFORM

### 3.1 Variables de Entorno Identificadas

Las siguientes variables de entorno son requeridas por el backend:

1. **DATABASE_URL** - Construida dinámicamente con credenciales de RDS
2. **JWT_SECRET_KEY** - Generada con `openssl rand -hex 32`
3. **AWS_REGION** - us-east-1
4. **AWS_S3_BUCKET** - Bucket de archivos creado por Terraform
5. **ENVIRONMENT** - dev
6. **ALLOWED_ORIGINS** - CloudFront domain

### 3.2 JWT Secret Generado

```bash
openssl rand -hex 32
```

**Secret generado:** `b5ffd302d6d34e19cd24ebf18267730846f137d449ac34ef3d9942c481729287`

⚠️ **IMPORTANTE:** Este secret debe ser guardado de forma segura y NO debe ser compartido.

### 3.3 Configuración de IP Pública para Acceso RDS

**IP del desarrollador:** `186.86.32.243`

Esta IP fue agregada al Security Group de RDS para permitir acceso directo desde el entorno local.

### 3.4 Cambios en terraform.tfvars

**Archivo:** `terraform/environments/dev/terraform.tfvars`

```hcl
# ECR image URI - Updated with actual backend image
backend_image_uri = "327568102873.dkr.ecr.us-east-1.amazonaws.com/business-system/backend:latest"

# Secure JWT secret key generated with openssl rand -hex 32
jwt_secret_key = "b5ffd302d6d34e19cd24ebf18267730846f137d449ac34ef3d9942c481729287"

# Public RDS access configuration (development only)
allow_public_rds_access = true
allowed_cidr_blocks     = ["186.86.32.243/32"]  # Developer IP for RDS access
```

### 3.5 Nuevas Variables Agregadas

**Archivo:** `terraform/variables.tf`

```hcl
variable "allowed_cidr_blocks" {
  description = "List of CIDR blocks allowed to access RDS"
  type        = list(string)
  default     = []

  validation {
    condition = alltrue([
      for cidr in var.allowed_cidr_blocks : can(cidrhost(cidr, 0))
    ])
    error_message = "All CIDR blocks must be valid IPv4 CIDR notation."
  }
}
```

### 3.6 Cambios en el Módulo RDS

**Archivo:** `terraform/modules/rds/variables.tf`

```hcl
variable "allow_public_access" {
  description = "Allow public access to RDS"
  type        = bool
  default     = false
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access RDS when public access is enabled"
  type        = list(string)
  default     = []
}
```

**Archivo:** `terraform/modules/rds/main.tf`

1. **Security Group - Regla de ingreso dinámica:**

```hcl
# Conditional ingress rule for public access from specific IPs
dynamic "ingress" {
  for_each = var.allow_public_access && length(var.allowed_cidr_blocks) > 0 ? [1] : []
  content {
    description = "PostgreSQL from allowed CIDR blocks"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }
}
```

2. **RDS Instance - publicly_accessible:**

```hcl
publicly_accessible = var.allow_public_access
```

### 3.7 Paso de Variables desde main.tf

**Archivo:** `terraform/main.tf`

```hcl
module "rds" {
  source = "./modules/rds"

  # ... otras configuraciones ...

  # Public access configuration (development only)
  allow_public_access  = var.allow_public_rds_access
  allowed_cidr_blocks  = var.allowed_cidr_blocks

  tags = local.common_tags
}
```

---

## 🚀 4. APLICACIÓN DE TERRAFORM

### 4.1 Plan de Terraform

```bash
terraform plan -var-file="environments/dev/terraform.tfvars" -out=tfplan
```

**Recursos a modificar/crear:**
- ✅ `module.app_runner.aws_apprunner_service.main` - Reemplazar con nueva imagen ECR
- ✅ `module.rds.aws_db_instance.main` - Actualizar publicly_accessible = true
- ✅ `module.rds.aws_security_group.rds` - Agregar regla de ingreso para IP específica
- ✅ `module.s3_files.aws_cloudfront_distribution.frontend` - Habilitar distribución

**Resumen del plan:**
- 1 recurso a agregar (App Runner recreado)
- 3 recursos a modificar (RDS instance, Security Group, CloudFront)
- 1 recurso a eliminar (App Runner anterior)

### 4.2 Aplicación de Cambios

```bash
terraform apply tfplan
```

**Tiempo total de aplicación:** ~7 minutos

**Resultados:**
1. ✅ App Runner service anterior eliminado (7s)
2. ✅ Security Group de RDS actualizado (1s)
3. ✅ RDS instance modificada para acceso público (2m 33s)
4. ✅ CloudFront distribución habilitada (3m 22s)
5. ⚠️ App Runner service nuevo - FAILED (6m 40s)

### 4.3 Diagnóstico del Fallo de App Runner

**Estado:** CREATE_FAILED
**ARN:** `arn:aws:apprunner:us-east-1:327568102873:service/business-system-dev-backend/e4c9572914c64f3b9a348b0e9201a02a`

**Causa probable:**
El backend NO tiene implementado el endpoint `/health` que App Runner requiere para health checks.

**Configuración de Health Check en App Runner:**
```hcl
health_check_configuration {
  protocol            = "HTTP"
  path                = "/health"
  interval            = 10
  timeout             = 5
  healthy_threshold   = 1
  unhealthy_threshold = 5
}
```

**Solución requerida:**
Agregar endpoint `/health` al backend FastAPI antes de volver a desplegar.

---

## 📊 5. RECURSOS DESPLEGADOS EXITOSAMENTE

### 5.1 Red (VPC)
- **VPC ID:** vpc-0df64b04c75bad907
- **CIDR:** 10.0.0.0/16
- **Subnets públicas:** 2 (Multi-AZ)
- **Subnets privadas:** 2 (Multi-AZ)
- **Internet Gateway:** igw-05afe2ca4fc21c926
- **NAT Gateway:** nat-05ff774062e3d8a8d (single para costo)

### 5.2 Base de Datos (RDS PostgreSQL)
- **Instance ID:** db-M433WSINJSXXLDEMYMATQLJYCU
- **Endpoint:** `business-system-dev-db.cqrk2ecg4sic.us-east-1.rds.amazonaws.com:5432`
- **Engine:** PostgreSQL 15.7
- **Instance Class:** db.t3.micro (Free Tier eligible)
- **Storage:** 20GB gp3 (encrypted)
- **Multi-AZ:** false (costo optimizado)
- **Publicly Accessible:** ✅ true
- **Database Name:** business_system_dev
- **Username:** business_admin
- **Password:** Almacenado en AWS Secrets Manager

**Security Group de RDS:**
- **ID:** sg-01b583fbb385606a4
- **Reglas de ingreso:**
  1. PostgreSQL (5432) desde App Runner Security Group
  2. PostgreSQL (5432) desde IP 186.86.32.243/32 (desarrollo)

### 5.3 Frontend (S3 + CloudFront)
- **S3 Bucket:** business-system-dev-frontend-20251010213119586000000008
- **CloudFront Distribution:** E15062Q3FMZXMF
- **Frontend URL:** https://d242g1l7hltahp.cloudfront.net
- **Price Class:** PriceClass_100 (costo optimizado)

### 5.4 Almacenamiento de Archivos (S3 + CloudFront)
- **S3 Bucket:** business-system-dev-files-frontend-2025101021312027830000000a
- **CloudFront Distribution:** E1827YXXXRS19N
- **Versioning:** Habilitado
- **Lifecycle Rules:** Configuradas (IA a 30 días, Glacier a 90 días)

### 5.5 Monitoring (CloudWatch)
- **Dashboard:** business-system-dev-dashboard
- **SNS Topic:** arn:aws:sns:us-east-1:327568102873:business-system-dev-alerts-2025101021312043100000000c
- **Alarmas configuradas:**
  - RDS CPU High
  - RDS Connections High
  - RDS Storage Low
  - CloudFront Error Rate
  - Billing Threshold ($25)
- **Log Groups:**
  - /aws/apprunner/business-system-dev-20251010213119583400000003
  - /aws/rds/business-system-dev-20251010213119583900000005

### 5.6 Secrets Manager
- **Secret Name:** business-system-dev-db-password
- **ARN:** arn:aws:secretsmanager:us-east-1:327568102873:secret:business-system-dev-db-password-dlrSCP
- **Contenido (JSON):**
```json
{
  "username": "business_admin",
  "password": "[REDACTED]",
  "host": "business-system-dev-db.cqrk2ecg4sic.us-east-1.rds.amazonaws.com:5432",
  "port": 5432,
  "dbname": "business_system_dev"
}
```

---

## 🔐 6. ACCESO A LA BASE DE DATOS RDS

### 6.1 Desde el Entorno Local

**Comando de conexión con psql:**
```bash
psql -h business-system-dev-db.cqrk2ecg4sic.us-east-1.rds.amazonaws.com \
     -p 5432 \
     -U business_admin \
     -d business_system_dev
```

**Obtener password desde Secrets Manager:**
```bash
aws secretsmanager get-secret-value \
  --secret-id business-system-dev-db-password \
  --query SecretString \
  --output text \
  --profile personal \
  --region us-east-1 | jq -r '.password'
```

**Connection String para aplicaciones:**
```
postgresql://business_admin:[PASSWORD]@business-system-dev-db.cqrk2ecg4sic.us-east-1.rds.amazonaws.com:5432/business_system_dev
```

### 6.2 Configuración de Security Group

**Acceso permitido desde:**
1. **App Runner Security Group** (sg-0acfd393f302859c0) - Puerto 5432
2. **IP del Desarrollador** (186.86.32.243/32) - Puerto 5432

⚠️ **NOTA DE SEGURIDAD:** El acceso público a RDS está habilitado SOLO para desarrollo. En producción, esto debe ser deshabilitado y el acceso debe ser únicamente desde la VPC.

---

## 💰 7. ESTIMACIÓN DE COSTOS

### 7.1 Costos Mensuales Estimados (con Free Tier - primeros 12 meses)

| Servicio | Configuración | Costo Mensual (Free Tier) | Costo Mensual (Sin Free Tier) |
|----------|---------------|---------------------------|--------------------------------|
| RDS PostgreSQL | db.t3.micro, 20GB | $0.00 | $13.70 |
| App Runner | 0.25 vCPU, 0.5GB RAM | $8-15 | $8-15 |
| NAT Gateway | Single gateway | $3.50 | $3.50 |
| CloudFront | PriceClass_100 | $0.00 | $1.00 |
| S3 Storage | ~10GB | $0.00 | $0.50 |
| CloudWatch Logs | Basic retention | $1.00 | $1.00 |
| Data Transfer | Estimado | $2.00 | $2.00 |
| **TOTAL** | | **$14-22/mes** | **$29-36/mes** |

### 7.2 Servicios Incluidos en Free Tier
- ✅ RDS db.t3.micro (750 horas/mes)
- ✅ RDS Storage (20GB/mes)
- ✅ CloudFront (1TB de transferencia/mes)
- ✅ S3 Storage (5GB/mes)
- ✅ S3 Requests (20,000 GET, 2,000 PUT/mes)

---

## ⚡ 8. PRÓXIMOS PASOS REQUERIDOS

### 8.1 CRÍTICO: Agregar Endpoint /health al Backend

**Ubicación:** `backend/main.py`

```python
@app.get("/health")
async def health_check():
    """Health check endpoint for App Runner"""
    return {
        "status": "healthy",
        "service": "business-system-backend",
        "version": "1.0.0"
    }
```

**Después de agregar:**
1. Reconstruir imagen Docker
2. Push a ECR con nuevo tag
3. Actualizar terraform.tfvars con nuevo tag (o usar :latest)
4. Volver a aplicar Terraform

### 8.2 Verificar Backend en App Runner

Una vez desplegado exitosamente:
```bash
# Ver logs
aws logs tail /aws/apprunner/business-system-dev-20251010213119583400000003 \
  --follow \
  --profile personal \
  --region us-east-1

# Verificar health endpoint
curl https://[APP_RUNNER_URL]/health
```

### 8.3 Ejecutar Migraciones de Base de Datos

```bash
# Desde el directorio backend/
cd backend

# Configurar DATABASE_URL con credenciales de RDS
export DATABASE_URL="postgresql://business_admin:[PASSWORD]@business-system-dev-db.cqrk2ecg4sic.us-east-1.rds.amazonaws.com:5432/business_system_dev"

# Ejecutar migraciones
alembic upgrade head

# Poblar datos de prueba (opcional)
python populate_multi_tenant_demo.py
```

### 8.4 Desplegar Frontend

```bash
# Desde el directorio frontend/
cd frontend

# Build de producción
npm run build

# Sync a S3
aws s3 sync build/ s3://business-system-dev-frontend-20251010213119586000000008 \
  --delete \
  --profile personal \
  --region us-east-1

# Invalidar caché de CloudFront
aws cloudfront create-invalidation \
  --distribution-id E15062Q3FMZXMF \
  --paths '/*' \
  --profile personal
```

### 8.5 Configurar Variables de Entorno en Frontend

Actualizar el archivo de configuración del frontend para apuntar al backend de App Runner una vez esté funcionando.

---

## 🔧 9. COMANDOS ÚTILES

### 9.1 ECR

```bash
# Login a ECR
aws ecr get-login-password --region us-east-1 --profile personal | \
  docker login --username AWS --password-stdin 327568102873.dkr.ecr.us-east-1.amazonaws.com

# Listar imágenes
aws ecr list-images \
  --repository-name business-system/backend \
  --profile personal \
  --region us-east-1

# Eliminar una imagen
aws ecr batch-delete-image \
  --repository-name business-system/backend \
  --image-ids imageTag=v1.0.0 \
  --profile personal \
  --region us-east-1
```

### 9.2 Terraform

```bash
# Ver outputs
terraform output -json | jq '.'

# Ver estado
terraform show

# Destruir todo (CUIDADO!)
terraform destroy -var-file="environments/dev/terraform.tfvars"
```

### 9.3 RDS

```bash
# Obtener endpoint
aws rds describe-db-instances \
  --db-instance-identifier business-system-dev-db \
  --profile personal \
  --region us-east-1 | jq -r '.DBInstances[0].Endpoint.Address'

# Ver snapshot más reciente
aws rds describe-db-snapshots \
  --db-instance-identifier business-system-dev-db \
  --profile personal \
  --region us-east-1 | jq '.DBSnapshots | sort_by(.SnapshotCreateTime) | reverse | .[0]'
```

### 9.4 App Runner

```bash
# Ver estado del servicio
aws apprunner describe-service \
  --service-arn [SERVICE_ARN] \
  --profile personal \
  --region us-east-1 | jq '.Service.Status'

# Pausar servicio (ahorrar costos)
aws apprunner pause-service \
  --service-arn [SERVICE_ARN] \
  --profile personal \
  --region us-east-1

# Reanudar servicio
aws apprunner resume-service \
  --service-arn [SERVICE_ARN] \
  --profile personal \
  --region us-east-1
```

---

## 📝 10. NOTAS Y RECOMENDACIONES

### 10.1 Seguridad

1. ✅ **JWT Secret:** Generado con alta entropía (256 bits)
2. ⚠️ **RDS Público:** Solo para desarrollo - Deshabilitar en producción
3. ✅ **Encryption:** RDS storage encriptado con AES256
4. ✅ **Security Groups:** Restrictivos - Solo IPs/Security Groups específicos
5. ⚠️ **Secrets:** Almacenados en Secrets Manager, pero rotation no configurada

### 10.2 Optimización de Costos

1. ✅ NAT Gateway único (ahorro ~$45/mes vs. Multi-AZ)
2. ✅ RDS en Free Tier (db.t3.micro)
3. ✅ App Runner mínimo (0.25 vCPU, 0.5GB)
4. ✅ CloudFront PriceClass_100
5. ✅ S3 Lifecycle rules configuradas
6. ⚠️ Considerar pausar App Runner cuando no esté en uso

### 10.3 Monitoreo

1. ✅ CloudWatch Dashboard configurado
2. ✅ Alarmas para RDS (CPU, Connections, Storage)
3. ✅ Alarms CloudFront (Error Rate)
4. ✅ Billing alarm ($25 threshold)
5. ⚠️ SNS subscription requiere confirmación de email

### 10.4 Backup y Recuperación

1. ✅ RDS Automated Backups (7 días retention)
2. ✅ S3 Versioning habilitado en bucket de archivos
3. ⚠️ Manual snapshots no configurados
4. ⚠️ Disaster recovery plan no documentado

---

## 📞 11. INFORMACIÓN DE CONTACTO Y SOPORTE

**Cuenta AWS:** 327568102873
**Región Principal:** us-east-1
**Perfil AWS CLI:** personal
**Proyecto:** business-system
**Ambiente:** dev

**Terraform State:**
- Ubicación: Local
- Archivo: `/Users/fitideas/Documents/proyectosJeison/git/businessSystem/terraform/terraform.tfstate`
- ⚠️ Considerar mover a S3 backend para producción

---

## 📚 12. REFERENCIAS

- [AWS App Runner Documentation](https://docs.aws.amazon.com/apprunner/)
- [Amazon RDS for PostgreSQL](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)
- [Amazon ECR User Guide](https://docs.aws.amazon.com/ecr/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [FastAPI Health Checks](https://fastapi.tiangolo.com/advanced/custom-response/)

---

**Documento generado:** 2025-10-10
**Última actualización:** 2025-10-10
**Estado del despliegue:** ⚠️ Parcial (RDS ✅, ECR ✅, CloudFront ✅, App Runner ⚠️ Requiere endpoint /health)
