# Guía de Despliegue - Sistema de Gestión Empresarial

Esta guía proporciona instrucciones detalladas para desplegar el Sistema de Gestión Empresarial en diferentes entornos.

## 📋 Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Despliegue Local (Desarrollo)](#despliegue-local-desarrollo)
3. [Despliegue en Servidor (Producción)](#despliegue-en-servidor-producción)
4. [Despliegue en la Nube](#despliegue-en-la-nube)
5. [Configuración de SSL](#configuración-de-ssl)
6. [Monitoreo y Mantenimiento](#monitoreo-y-mantenimiento)
7. [Troubleshooting](#troubleshooting)

## 🔧 Requisitos Previos

### Mínimos del Sistema
- **CPU**: 2 cores
- **RAM**: 4GB (mínimo), 8GB (recomendado)
- **Almacenamiento**: 20GB libre
- **OS**: Linux, macOS, Windows con WSL2

### Software Requerido
- **Docker**: 20.10 o superior
- **Docker Compose**: 2.0 o superior
- **Git**: Para clonar el repositorio

### Verificación de Requisitos
```bash
# Verificar Docker
docker --version
docker-compose --version

# Verificar recursos del sistema
docker system info
```

## 🛠️ Despliegue Local (Desarrollo)

### 1. Preparación del Entorno
```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/business-system.git
cd business-system

# Ejecutar configuración inicial
./scripts/setup.sh
```

### 2. Configurar Variables de Entorno
```bash
# Editar archivo .env
nano .env

# Variables importantes para desarrollo:
DATABASE_URL=postgresql+psycopg://admin:admin@database:5432/inventario
JWT_SECRET_KEY=development-secret-key-not-for-production
REACT_APP_API_URL=http://localhost:8000
```

### 3. Iniciar Servicios de Desarrollo
```bash
# Modo desarrollo con hot reload
./scripts/dev.sh

# Verificar servicios
docker-compose ps
```

### 4. Poblar Datos de Prueba
```bash
# Poblar base de datos con datos demo
docker-compose exec backend python populate_demo_data.py
```

### 5. Acceder a la Aplicación
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Backend**: http://localhost:8000

## 🚀 Despliegue en Servidor (Producción)

### 1. Preparación del Servidor

#### Ubuntu/Debian
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Agregar usuario al grupo docker
sudo usermod -aG docker $USER
newgrp docker
```

#### CentOS/RHEL
```bash
# Instalar Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Configuración de Producción
```bash
# Clonar en el servidor
git clone https://github.com/tu-usuario/business-system.git
cd business-system

# Ejecutar configuración
./scripts/setup.sh

# Configurar variables de producción
cp .env.example .env
nano .env
```

#### Variables Críticas de Producción
```bash
# .env para producción
DATABASE_URL=postgresql+psycopg://secure_user:secure_password@database:5432/production_db
JWT_SECRET_KEY=super-secure-key-minimum-32-characters-long-for-production-use
REACT_APP_API_URL=https://tu-dominio.com
POSTGRES_DB=production_db
POSTGRES_USER=secure_user
POSTGRES_PASSWORD=secure_password_with_special_chars!123
```

### 3. Configurar Firewall
```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 4. Desplegar en Producción
```bash
# Iniciar en modo producción
./scripts/prod.sh

# Verificar servicios
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Ver logs
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

### 5. Configurar Dominio (Opcional)
```bash
# Editar configuración de Nginx
nano nginx/nginx.conf

# Cambiar server_name
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;
    # ... resto de configuración
}

# Reiniciar proxy
docker-compose restart nginx
```

## ☁️ Despliegue en la Nube

### AWS EC2

#### 1. Crear Instancia EC2
```bash
# Recomendaciones:
# - t3.medium o superior (2 vCPU, 4GB RAM)
# - Ubuntu 22.04 LTS
# - Almacenamiento: 30GB gp3
# - Security Group: puertos 22, 80, 443
```

#### 2. Conectar y Configurar
```bash
# Conectar via SSH
ssh -i tu-key.pem ubuntu@tu-ip-publica

# Instalar dependencias
sudo apt update
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker ubuntu

# Clonar y desplegar
git clone https://github.com/tu-usuario/business-system.git
cd business-system
./scripts/setup.sh
./scripts/prod.sh
```

### Google Cloud Platform

#### 1. Crear VM Instance
```bash
# Configuración recomendada:
# - Machine type: e2-standard-2
# - OS: Ubuntu 22.04 LTS
# - Boot disk: 30GB SSD
# - Firewall: Allow HTTP/HTTPS traffic
```

#### 2. Configurar y Desplegar
```bash
# Conectar via Cloud Shell o SSH
gcloud compute ssh tu-instancia

# Seguir pasos similares a AWS
sudo apt update && sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER

# Clonar y desplegar
git clone https://github.com/tu-usuario/business-system.git
cd business-system
./scripts/setup.sh
./scripts/prod.sh
```

### Digital Ocean

#### 1. Crear Droplet
```bash
# Configuración:
# - Ubuntu 22.04 LTS
# - Basic plan: 2 GB RAM, 1 vCPU
# - Agregar SSH key
```

#### 2. Configurar Droplet
```bash
# Conectar via SSH
ssh root@tu-ip-droplet

# Instalar Docker (Digital Ocean tiene imagen con Docker preinstalado)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Clonar y desplegar
git clone https://github.com/tu-usuario/business-system.git
cd business-system
./scripts/setup.sh
./scripts/prod.sh
```

## 🔐 Configuración de SSL

### 1. Con Let's Encrypt (Certbot)
```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Verificar renovación automática
sudo certbot renew --dry-run
```

### 2. Configuración Manual de SSL
```bash
# Crear directorio SSL
mkdir -p ssl

# Copiar certificados (ejemplo)
cp /path/to/cert.pem ssl/
cp /path/to/key.pem ssl/

# Actualizar configuración de Nginx
nano nginx/nginx.conf
```

#### Configuración Nginx con SSL
```nginx
server {
    listen 80;
    server_name tu-dominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # Configuración SSL moderna
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    
    # Proxy a aplicación
    location / {
        proxy_pass http://frontend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/ {
        proxy_pass http://backend/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📊 Monitoreo y Mantenimiento

### 1. Health Checks
```bash
# Verificar estado de servicios
curl http://localhost/api/health
curl http://localhost:8000/health

# Estado de contenedores
docker-compose ps
docker stats
```

### 2. Logs
```bash
# Ver logs en tiempo real
docker-compose logs -f

# Logs por servicio
docker-compose logs backend
docker-compose logs frontend
docker-compose logs database

# Logs con timestamps
docker-compose logs -t --since="1h"
```

### 3. Backups Automatizados
```bash
# Configurar cron para backups automáticos
crontab -e

# Agregar línea para backup diario a las 2 AM
0 2 * * * /path/to/business-system/scripts/backup.sh

# Backup manual
./scripts/backup.sh
```

### 4. Monitoreo de Recursos
```bash
# Uso de recursos por contenedor
docker stats

# Espacio en disco
df -h
docker system df

# Memoria y CPU del sistema
free -h
top
```

### 5. Actualizaciones
```bash
# Actualizar código
git pull origin main

# Reconstruir y reiniciar servicios
docker-compose build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Ejecutar migraciones si hay cambios
docker-compose exec backend alembic upgrade head
```

## 🔧 Troubleshooting

### Problemas Comunes

#### 1. Puerto Ocupado
```bash
# Verificar puertos en uso
netstat -tulpn | grep :80
netstat -tulpn | grep :443
netstat -tulpn | grep :5432

# Matar proceso que usa puerto
sudo kill -9 $(sudo lsof -t -i:80)
```

#### 2. Contenedor No Inicia
```bash
# Ver logs detallados
docker-compose logs [servicio]

# Verificar configuración
docker-compose config

# Reconstruir imagen
docker-compose build --no-cache [servicio]
```

#### 3. Problemas de Base de Datos
```bash
# Verificar conectividad
docker-compose exec backend python -c "
import psycopg
conn = psycopg.connect('postgresql://admin:admin@database:5432/inventario')
print('✅ Conexión exitosa')
"

# Recrear base de datos
docker-compose exec database psql -U admin -c "DROP DATABASE inventario;"
docker-compose exec database psql -U admin -c "CREATE DATABASE inventario;"
```

#### 4. Problemas de Permisos
```bash
# Verificar usuario en contenedores
docker-compose exec backend whoami

# Ajustar permisos de archivos
chmod +x scripts/*.sh
chown -R $USER:$USER ./
```

#### 5. Problemas de SSL
```bash
# Verificar certificados
openssl x509 -in ssl/cert.pem -text -noout

# Renovar certificados Let's Encrypt
sudo certbot renew

# Verificar configuración SSL
nginx -t
```

### Comandos de Diagnóstico
```bash
# Estado completo del sistema
docker system info
docker-compose ps
docker stats --no-stream

# Espacio utilizado
docker system df
du -sh .

# Logs de sistema
journalctl -u docker.service
dmesg | tail
```

### Recuperación de Emergencia
```bash
# Parar todos los servicios
docker-compose down

# Limpiar sistema completo
docker system prune -a --volumes

# Reiniciar desde cero
./scripts/setup.sh
./scripts/prod.sh

# Restaurar backup
docker-compose exec -T database psql -U admin -d inventario < backup.sql
```

## 📞 Soporte

Si necesitas ayuda adicional:

1. **Revisa los logs**: `docker-compose logs -f`
2. **Verifica la configuración**: `docker-compose config`
3. **Consulta la documentación**: `memory-bank/progress.md`
4. **Verifica health checks**: `curl http://localhost:8000/health`

---

### ✅ Lista de Verificación Post-Despliegue

- [ ] Servicios iniciados correctamente
- [ ] Health checks pasando
- [ ] SSL configurado (producción)
- [ ] Backups programados
- [ ] Monitoreo configurado
- [ ] Logs accesibles
- [ ] Variables de entorno seguras
- [ ] Firewall configurado
- [ ] Dominio apuntando al servidor
- [ ] Usuario administrador creado

**¡Tu Sistema de Gestión Empresarial está listo para usar!** 🎉