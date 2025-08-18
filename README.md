# Sistema de Gestión Empresarial

Un sistema completo de gestión empresarial desarrollado con **Clean Architecture**, **FastAPI** y **React TypeScript**, containerizado con **Docker** para fácil despliegue y escalabilidad.

## 🚀 Características Principales

### ✅ Módulos Completamente Implementados
- **👤 Gestión de Usuarios**: Administración completa con roles y permisos
- **⚙️ Configuración Personal**: Perfil de usuario y cambio de contraseñas
- **📦 Gestión de Productos**: CRUD completo con validaciones de negocio
- **📊 Control de Inventario**: Movimientos, kardex y costeo promedio ponderado
- **📋 Contabilidad**: Plan de cuentas colombiano y asientos contables
- **🙋‍♂️ Gestión de Clientes**: Base de datos completa con estadísticas
- **🧾 Facturación**: Sistema completo con integración contable
- **📈 Dashboard Gerencial**: Métricas y reportes ejecutivos

### 🏗️ Arquitectura y Tecnologías
- **Backend**: FastAPI con Python 3.11, SQLModel, PostgreSQL
- **Frontend**: React 18, TypeScript, Material-UI
- **Base de Datos**: PostgreSQL 17.2 con Alembic para migraciones
- **Autenticación**: JWT con roles granulares
- **Containerización**: Docker y Docker Compose
- **Testing**: 70+ pruebas automatizadas

## 📋 Requisitos Previos

- **Docker** 20.10 o superior
- **Docker Compose** 2.0 o superior
- **Git**

## 🚀 Inicio Rápido

### 1. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/business-system.git
cd business-system
```

### 2. Configuración Inicial
```bash
# Ejecutar script de configuración
./scripts/setup.sh
```

Este script:
- ✅ Verifica dependencias (Docker, Docker Compose)
- ✅ Crea archivo `.env` desde plantilla
- ✅ Genera JWT secret key seguro
- ✅ Crea directorios necesarios
- ✅ Configura Nginx para producción

### 3. Desarrollo Local
```bash
# Iniciar en modo desarrollo
./scripts/dev.sh
```

**Servicios disponibles:**
- 🌐 Frontend: http://localhost:3000
- 🔧 Backend API: http://localhost:8000
- 📚 Documentación API: http://localhost:8000/docs
- 🗄️ Base de Datos: localhost:5432

### 4. Producción
```bash
# Iniciar en modo producción
./scripts/prod.sh
```

**Servicios disponibles:**
- 🌐 Aplicación: http://localhost
- 🔧 API: http://localhost/api
- 📊 Métricas: Logs en `./logs/`

## 📊 Gestión y Mantenimiento

### Backup y Restauración
```bash
# Sistema de backup completo
./scripts/backup.sh

# Opciones disponibles:
# 1) Backup completo (BD + configuraciones)
# 2) Solo backup de base de datos
# 3) Solo backup de configuraciones
# 4) Limpiar backups antiguos
# 5) Mostrar información de backups
```

### Comandos Útiles

#### Desarrollo
```bash
# Ver logs en tiempo real
docker-compose logs -f

# Reiniciar un servicio específico
docker-compose restart backend

# Acceder al contenedor
docker-compose exec backend bash

# Ejecutar migraciones
docker-compose exec backend alembic upgrade head

# Poblar datos demo
docker-compose exec backend python populate_demo_data.py
```

#### Producción
```bash
# Ver estado de servicios
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Ver logs de producción
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# Parar servicios
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
```

## 🔧 Configuración

### Variables de Entorno Principales
```bash
# Base de Datos
DATABASE_URL=postgresql+psycopg://admin:admin@database:5432/inventario
POSTGRES_DB=inventario
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin

# Autenticación
JWT_SECRET_KEY=your-super-secure-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Frontend
REACT_APP_API_URL=http://localhost:8000
```

### Configuración de Producción

Para producción, asegúrate de:

1. **Cambiar credenciales por defecto**:
   - JWT_SECRET_KEY (mínimo 32 caracteres)
   - Credenciales de base de datos
   - Configurar dominio real en REACT_APP_API_URL

2. **Configurar SSL** (opcional):
   ```bash
   # Copiar certificados SSL
   cp cert.pem ssl/
   cp key.pem ssl/
   
   # Activar proxy Nginx con SSL
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile production up
   ```

## 👥 Usuarios por Defecto

Después de poblar datos demo:

| Email | Contraseña | Rol |
|-------|------------|-----|
| admin@example.com | admin123 | Administrador |
| gerente@example.com | gerente123 | Gerente de Ventas |
| contador@example.com | contador123 | Contador |
| vendedor@example.com | vendedor123 | Vendedor |

## 🔐 Roles y Permisos

### Roles Disponibles
- **👑 ADMINISTRADOR**: Acceso completo al sistema
- **📊 GERENTE_VENTAS**: Ventas, clientes, facturas, inventario
- **💰 CONTADOR**: Contabilidad, reportes financieros
- **🛒 VENDEDOR**: Ventas básicas y consulta de productos

### Control de Acceso
- **Rutas protegidas** por rol en frontend
- **Middleware de autorización** en backend
- **Validación JWT** en cada endpoint

## 🧪 Testing

```bash
# Ejecutar todas las pruebas
docker-compose exec backend pytest

# Pruebas con cobertura
docker-compose exec backend pytest --cov=app --cov-report=html

# Pruebas específicas
docker-compose exec backend pytest tests/test_api/test_auth_endpoints.py
```

**Cobertura actual**: 70+ pruebas implementadas
- ✅ Tests de API endpoints
- ✅ Tests de repositorios
- ✅ Tests de casos de uso
- ✅ Tests de integración

## 📊 Monitoreo y Logs

### Health Checks
Todos los servicios incluyen health checks:
- **Database**: `pg_isready`
- **Backend**: `GET /health`
- **Frontend**: `curl localhost:80`

### Logs
```bash
# Logs por servicio
docker-compose logs backend
docker-compose logs frontend
docker-compose logs database

# Logs en tiempo real
docker-compose logs -f

# Logs con timestamps
docker-compose logs -t
```

## 🔧 Solución de Problemas

### Problemas Comunes

#### Puerto ocupado
```bash
# Verificar puertos en uso
docker ps
lsof -i :8000
lsof -i :3000
lsof -i :5432

# Parar contenedores existentes
docker-compose down
```

#### Problemas de dependencias
```bash
# Reconstruir imágenes
docker-compose build --no-cache

# Limpiar sistema Docker
docker system prune -f
docker volume prune -f
```

#### Problemas de migraciones
```bash
# Crear tablas manualmente
docker-compose exec backend python -c "
from sqlmodel import SQLModel, create_engine
from app.domain.models.user import User
engine = create_engine('postgresql+psycopg://admin:admin@database:5432/inventario')
SQLModel.metadata.create_all(engine)
"
```

#### Problemas de permisos
```bash
# Verificar permisos de scripts
chmod +x scripts/*.sh

# Verificar usuario en contenedores
docker-compose exec backend whoami
```

## 📚 Documentación Adicional

- **📋 Progreso del Desarrollo**: `memory-bank/progress.md`
- **🏗️ Arquitectura del Sistema**: `memory-bank/architecture.md`
- **📊 Plan de Implementación**: `memory-bank/implementation-plan.md`
- **🔧 Configuración Técnica**: `CLAUDE.md`

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -m 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 🆘 Soporte

Si encuentras problemas o tienes preguntas:

1. **Revisa la documentación** en `memory-bank/`
2. **Consulta los logs** con `docker-compose logs`
3. **Verifica la configuración** en `.env`
4. **Ejecuta health checks** en http://localhost:8000/health

---

### 🎉 ¡Sistema Listo para Producción!

El Sistema de Gestión Empresarial está completamente containerizado y listo para ser desplegado en cualquier entorno que soporte Docker. 

**Características destacadas**:
- ✅ Arquitectura escalable y mantenible
- ✅ Seguridad empresarial con JWT y roles
- ✅ Base de datos robusta con PostgreSQL
- ✅ Interfaz moderna con React y Material-UI
- ✅ Documentación completa y scripts de automatización
- ✅ Testing comprehensivo
- ✅ Containerización completa con Docker