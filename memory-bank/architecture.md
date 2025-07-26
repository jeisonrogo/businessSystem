# Arquitectura del Sistema - Documentación de Implementación

Este documento explica la arquitectura actual implementada del Sistema de Gestión Empresarial, describiendo qué hace cada archivo y cómo se organizan los componentes siguiendo los principios de Clean Architecture.

## 📋 Principios Arquitectónicos Aplicados

### Clean Architecture
- **Separación de responsabilidades** por capas bien definidas
- **Inversión de dependencias** - las capas internas no conocen las externas
- **Independencia de frameworks** - la lógica de negocio no depende de FastAPI o PostgreSQL
- **Facilidad para testing** - cada capa puede probarse de forma aislada

### Inyección de Dependencias
- **FastAPI Depends** para inyección automática de dependencias
- **Repositorios abstractos** para desacoplar la lógica de negocio del acceso a datos

---

## 🏗️ Estructura de Archivos Implementada

### `/backend/main.py` - Punto de Entrada Principal
**Propósito:** Archivo de arranque de la aplicación FastAPI

**Funciones:**
- Inicializa la aplicación FastAPI con metadatos (título, descripción, versión)
- Configura middleware de CORS para permitir peticiones del frontend
- Define endpoints básicos:
  - `GET /` - Información básica de la API
  - `GET /health` - Endpoint de verificación de salud del servicio
- Configuración para ejecutar con Uvicorn cuando se ejecuta directamente

**Dependencias:** FastAPI, FastAPI CORS middleware

---

### `/backend/app/infrastructure/database/session.py` - Configuración de Base de Datos
**Propósito:** Maneja la conexión y configuración de la base de datos

**Funciones:**
- Define `DATABASE_URL` desde variables de entorno con fallback por defecto
- Crea el `engine` de SQLAlchemy con configuración optimizada:
  - `echo=True` para debugging (mostrar queries SQL)
  - `pool_pre_ping=True` para verificar conexiones antes de usar
  - `pool_recycle=300` para reciclar conexiones cada 5 minutos
- `create_db_and_tables()` - Función para crear tablas desde metadatos de SQLModel
- `get_session()` - Generador para inyección de dependencias de sesiones de BD

**Dependencias:** SQLModel, SQLAlchemy

---

### `/backend/alembic.ini` - Configuración de Migraciones
**Propósito:** Archivo de configuración principal de Alembic

**Configuraciones:**
- `script_location = alembic` - Ubicación de scripts de migración
- `sqlalchemy.url` - URL de conexión a PostgreSQL
- Configuración de logging para migraciones
- Templates para nombres de archivos de migración

---

### `/backend/alembic/env.py` - Entorno de Migraciones
**Propósito:** Script de entorno que conecta Alembic con SQLModel

**Funciones:**
- `get_database_url()` - Obtiene URL de BD desde variables de entorno
- `run_migrations_offline()` - Ejecuta migraciones sin conexión activa a BD
- `run_migrations_online()` - Ejecuta migraciones con conexión activa a BD
- Integración con `SQLModel.metadata` para auto-detección de modelos
- Importa configuración de sesión del proyecto

**Dependencias:** Alembic, SQLModel, configuración de session del proyecto

---

### `/backend/requirements.txt` - Dependencias del Proyecto
**Propósito:** Define todas las librerías Python necesarias

**Dependencias principales:**
- **fastapi** - Framework web principal
- **uvicorn[standard]** - Servidor ASGI con extras (watchfiles, etc.)
- **sqlmodel** - ORM que combina SQLAlchemy y Pydantic
- **psycopg[binary]** - Driver optimizado para PostgreSQL
- **alembic** - Sistema de migraciones de base de datos
- **pydantic>=2.6.0** - Validación y serialización de datos
- **python-jose[cryptography]** - Manejo de tokens JWT
- **passlib[bcrypt]** - Hashing seguro de contraseñas
- **pytest + pytest-cov + pytest-asyncio** - Framework de testing completo
- **python-multipart** - Manejo de formularios multipart

---

## 📁 Estructura de Directorios por Capas

### Capa de Presentación - `/backend/app/api/`
**Estado:** Estructura creada, pendiente de implementación

**Propósito:** Punto de entrada HTTP, validación de requests, formato de responses
- `/v1/endpoints/` - Endpoints REST organizados por módulo
- `/v1/schemas/` - Esquemas Pydantic para validación de datos de entrada/salida

### Capa de Aplicación - `/backend/app/application/`
**Estado:** Estructura creada, pendiente de implementación

**Propósito:** Orquestación de casos de uso, lógica de aplicación
- `/use_cases/` - Casos de uso específicos del negocio
- `/services/` - Interfaces (puertos) que implementará la capa de infraestructura

### Capa de Dominio - `/backend/app/domain/`
**Estado:** Estructura creada, pendiente de implementación

**Propósito:** Lógica de negocio pura, independiente de frameworks
- `/models/` - Entidades del negocio (Product, Invoice, User, etc.)
- `/exceptions/` - Excepciones específicas del dominio de negocio

### Capa de Infraestructura - `/backend/app/infrastructure/`
**Estado:** Base de datos configurada, repositorios pendientes

**Propósito:** Implementaciones concretas, acceso a datos, servicios externos
- `/database/` - Configuración de BD y modelos ORM
- `/repositories/` - Implementaciones concretas de los puertos del dominio

### Directorio de Pruebas - `/backend/tests/`
**Estado:** Estructura creada, pendiente de implementación

**Propósito:** Testing organizado por capas
- `/test_domain/` - Pruebas unitarias de lógica de negocio
- `/test_application/` - Pruebas de casos de uso
- `/test_api/` - Pruebas de integración de endpoints

---

## 🔄 Flujo de Datos Implementado (Actual)

### Endpoint `/health` - Ejemplo de Flujo Simple

```mermaid
graph TD
    A[Cliente HTTP] -->|GET /health| B[FastAPI main.py]
    B --> C[health_check function]
    C --> D[{"status": "ok"}]
    D --> E[Response HTTP 200]
    E --> A
```

**Descripción del flujo:**
1. Cliente realiza petición GET a `/health`
2. FastAPI en `main.py` recibe la petición
3. Se ejecuta la función `health_check()`
4. Retorna objeto JSON con status "ok"
5. FastAPI serializa y envía respuesta HTTP 200

---

## 🔧 Configuración y Variables de Entorno

### Variables de Entorno Soportadas

| Variable | Propósito | Valor por Defecto |
|----------|-----------|-------------------|
| `DATABASE_URL` | URL de conexión a PostgreSQL | `postgresql://user:password@localhost:5432/business_system` |
| `SECRET_KEY` | Clave secreta para JWT | *Requerida en producción* |
| `ALGORITHM` | Algoritmo para JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Tiempo de vida del token | `30` |

### Archivos de Configuración

- **`alembic.ini`** - Configuración de migraciones
- **`requirements.txt`** - Dependencias Python
- **`.env`** - Variables de entorno locales (no en Git)

---

## 🚀 Comandos de Desarrollo

### Servidor de Desarrollo
```bash
# Desde /backend
source ../venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Migraciones
```bash
# Crear nueva migración
alembic revision --autogenerate -m "descripción del cambio"

# Aplicar migraciones
alembic upgrade head

# Ver historial
alembic history
```

### Testing (Preparado, no implementado aún)
```bash
# Ejecutar todas las pruebas
pytest

# Con cobertura
pytest --cov=app --cov-report=html
```

---

## 📋 Estado de Implementación por Componente

| Componente | Estado | Descripción |
|------------|--------|-------------|
| **FastAPI Base** | ✅ Implementado | Servidor funcionando con endpoints básicos |
| **Configuración BD** | ✅ Implementado | SQLModel + PostgreSQL configurado |
| **Migraciones** | ✅ Implementado | Alembic configurado y funcionando |
| **Testing Framework** | ✅ Configurado | Pytest instalado, estructura preparada |
| **Modelos de Dominio** | ⏳ Pendiente | Entidades User, Product, Invoice, etc. |
| **Repositorios** | ⏳ Pendiente | Implementaciones de acceso a datos |
| **Casos de Uso** | ⏳ Pendiente | Lógica de aplicación |
| **Endpoints API** | ⏳ Pendiente | CRUD endpoints |
| **Autenticación** | ⏳ Pendiente | JWT, login, registro |

---

## 🔍 Puntos de Extensión Preparados

### Para Agregar Nuevos Modelos:
1. Crear entidad en `/app/domain/models/`
2. Crear repositorio en `/app/infrastructure/repositories/`
3. Generar migración con Alembic
4. Implementar casos de uso en `/app/application/use_cases/`
5. Crear endpoints en `/app/api/v1/endpoints/`

### Para Agregar Nuevos Servicios:
1. Definir interfaz en `/app/application/services/`
2. Implementar en `/app/infrastructure/`
3. Registrar en sistema de inyección de dependencias

### Para Testing:
1. Tests unitarios en `/tests/test_domain/`
2. Tests de integración en `/tests/test_application/`
3. Tests de API en `/tests/test_api/`
