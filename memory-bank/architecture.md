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
- **✅ NUEVO:** Incluye router de autenticación (`/api/v1/auth`)
- Define endpoints básicos:
  - `GET /` - Información básica de la API
  - `GET /health` - Endpoint de verificación de salud del servicio
- Configuración para ejecutar con Uvicorn cuando se ejecuta directamente

**Dependencias:** FastAPI, FastAPI CORS middleware, router de autenticación

---

## 📁 Capa de Dominio - Modelos de Negocio

### `/backend/app/domain/models/user.py` - Modelo de Usuario
**Propósito:** Define la entidad User y esquemas relacionados siguiendo Domain-Driven Design

**Componentes implementados:**
- **`UserBase`** - Campos base compartidos (email, nombre, rol)
- **`User`** - Entidad principal con tabla SQLModel:
  - `id: UUID` - Identificador único
  - `email: str` - Email único con índice
  - `nombre: str` - Nombre completo (2-100 caracteres)
  - `rol: str` - Rol del usuario (defecto: "vendedor")
  - `hashed_password: str` - Contraseña hasheada con bcrypt
  - `created_at: datetime` - Fecha de creación (UTC)
  - `is_active: bool` - Estado activo (defecto: True)
- **`UserCreate`** - Schema para creación (incluye password en texto plano)
- **`UserRead`** - Schema de lectura (excluye password)
- **`UserUpdate`** - Schema de actualización (campos opcionales)
- **`UserRole`** - Constantes de roles:
  - `ADMINISTRADOR` - Acceso total al sistema
  - `GERENTE_VENTAS` - Gestión de ventas y facturación
  - `CONTADOR` - Gestión contable y reportes
  - `VENDEDOR` - Rol básico por defecto

**Reglas de negocio implementadas:**
- BR-06: Usuarios solo acceden a funciones permitidas por su rol
- Email único obligatorio
- Contraseñas siempre hasheadas, nunca en texto plano
- Uso de `datetime.now(UTC)` para evitar deprecation warnings

**Dependencias:** SQLModel, Pydantic, UUID, datetime

---

## 📁 Capa de Aplicación - Lógica de Negocio

### `/backend/app/application/services/i_user_repository.py` - Interfaz de Repositorio
**Propósito:** Define el contrato abstracto para el acceso a datos de usuarios

**Métodos implementados:**
- `create(user_data: UserCreate) -> User` - Crear usuario
- `get_by_id(user_id: UUID) -> Optional[User]` - Buscar por ID
- `get_by_email(email: str) -> Optional[User]` - Buscar por email
- `get_all(skip: int, limit: int) -> List[User]` - Listar con paginación
- `update(user_id: UUID, user_data: UserUpdate) -> Optional[User]` - Actualizar
- `delete(user_id: UUID) -> bool` - Eliminar (soft delete)
- `exists_by_email(email: str) -> bool` - Verificar existencia
- `count_total() -> int` - Contar usuarios activos

**Principios aplicados:**
- Dependency Inversion Principle (DIP)
- Repository Pattern
- Interface Segregation Principle (ISP)

**Dependencias:** ABC, UUID, domain models

### `/backend/app/application/use_cases/auth_use_cases.py` - Casos de Uso de Autenticación
**Propósito:** Implementa la lógica de negocio para autenticación

**Casos de uso implementados:**

1. **`LoginUseCase`**:
   - Autentica credenciales (email + password)
   - Verifica usuario activo
   - Genera token JWT
   - Retorna token + información del usuario

2. **`RegisterUseCase`**:
   - Valida rol de usuario
   - Verifica unicidad de email
   - Crea usuario con contraseña hasheada
   - Genera token JWT para auto-login
   - Retorna token + usuario creado

3. **`GetCurrentUserUseCase`**:
   - Valida token JWT
   - Obtiene usuario actualizado de BD
   - Verifica estado activo
   - Retorna información del usuario

**Excepciones personalizadas:**
- `AuthenticationError` - Credenciales inválidas, usuario inactivo
- `RegistrationError` - Errores en registro (email duplicado, rol inválido)

**Dependencias:** IUserRepository, AuthenticationUtils, domain models

---

## 📁 Capa de Infraestructura - Implementaciones Concretas

### `/backend/app/infrastructure/database/session.py` - Configuración de Base de Datos
**Propósito:** Maneja la conexión y configuración de la base de datos

**Funciones actualizadas:**
- **✅ NUEVO:** Import del modelo User para Alembic
- Define `DATABASE_URL` con PostgreSQL: `postgresql+psycopg://admin:admin@localhost:5432/inventario`
- Crea el `engine` de SQLAlchemy con configuración optimizada
- `create_db_and_tables()` - Función para crear tablas desde metadatos
- `get_session()` - Generador para inyección de dependencias

**Dependencias:** SQLModel, SQLAlchemy, User model

### `/backend/app/infrastructure/repositories/user_repository.py` - Repositorio de Usuarios
**Propósito:** Implementación concreta del repositorio usando PostgreSQL

**Características implementadas:**
- Implementa todas las operaciones de `IUserRepository`
- **Hash automático de contraseñas** con bcrypt
- **Validación de unicidad** de emails
- **Soft delete** - marca como inactivo en lugar de eliminar
- **Manejo robusto de transacciones** con rollback automático
- **Paginación** en consultas de listado
- **Manejo de excepciones** específicas (IntegrityError, ValueError)

**Métodos implementados:**
- Hash y verificación de contraseñas con `passlib`
- Búsquedas con filtros de usuario activo donde corresponde
- Validaciones de negocio antes de operaciones de BD
- Queries optimizadas con SQLModel/SQLAlchemy

**Dependencias:** SQLModel, SQLAlchemy, passlib, IUserRepository

### `/backend/app/infrastructure/auth/auth_utils.py` - Utilidades de Autenticación
**Propósito:** Maneja JWT tokens y operaciones criptográficas

**Configuración:**
- `SECRET_KEY` - Desde variable de entorno
- `ALGORITHM` - HS256 para JWT
- `ACCESS_TOKEN_EXPIRE_MINUTES` - 30 minutos por defecto

**Métodos implementados:**
- `hash_password(password)` - Hash con bcrypt
- `verify_password(plain, hashed)` - Verificación de contraseña
- `create_access_token(data, expires_delta)` - Crear JWT
- `verify_token(token)` - Validar y decodificar JWT
- `authenticate_user(email, password, user)` - Validar credenciales
- `create_user_token(user)` - JWT específico para usuario
- `get_user_from_token(token)` - Extraer datos del usuario desde JWT

**Clases de datos:**
- `TokenData` - Representación de datos del token
- `LoginCredentials` - Credenciales de login

**Dependencias:** python-jose, passlib, datetime, User model

---

## 📁 Capa de Presentación - API REST

### `/backend/app/api/v1/schemas.py` - Esquemas Pydantic
**Propósito:** Define modelos de entrada y salida para la API

**Esquemas de autenticación:**
- `LoginRequest` - Email + password con validaciones
- `LoginResponse` - Token + tipo + información del usuario
- `RegisterRequest` - Datos completos de registro
- `RegisterResponse` - Token + usuario + mensaje de confirmación
- `UserResponse` - Información de usuario sin datos sensibles

**Esquemas de error:**
- `ErrorResponse` - Manejo consistente de errores
- `ValidationErrorResponse` - Errores de validación específicos

**Esquemas generales:**
- `TokenResponse` - Solo token y tipo
- `HealthResponse` - Estado del servicio
- `MessageResponse` - Respuestas con mensaje simple

**Validaciones implementadas:**
- `EmailStr` para emails válidos
- Longitudes mínimas/máximas para campos
- Campos requeridos vs opcionales
- Descripciones para documentación automática

**Dependencias:** Pydantic, datetime, UUID

### `/backend/app/api/v1/endpoints/auth.py` - Endpoints de Autenticación
**Propósito:** Maneja las rutas HTTP para autenticación

**Endpoints implementados:**

1. **`POST /api/v1/auth/register`** (201 Created):
   - Registra nuevos usuarios
   - Validaciones de entrada con Pydantic
   - Manejo de errores: 400 (datos inválidos), 409 (email duplicado), 422 (validación)

2. **`POST /api/v1/auth/login`** (200 OK):
   - Autenticación con email/password
   - Retorna JWT token
   - Manejo de errores: 401 (credenciales inválidas), 422 (validación)

3. **`GET /api/v1/auth/me`** (200 OK):
   - Información del usuario autenticado
   - Requiere Bearer token en Authorization header
   - Manejo de errores: 401 (token inválido), 404 (usuario no encontrado)

**Características:**
- **HTTPBearer security** para autenticación con tokens
- **Inyección de dependencias** con `get_user_repository`
- **Manejo de errores consistente** con códigos HTTP apropiados
- **Documentación automática** con OpenAPI/Swagger
- **Validación automática** de requests con Pydantic

**Dependencias:** FastAPI, HTTPBearer, casos de uso, repositorio, esquemas

---

## 🧪 Sistema de Pruebas Implementado

### `/backend/tests/test_infrastructure/test_user_repository.py` - Pruebas de Repositorio
**Propósito:** 15 pruebas unitarias del repositorio de usuarios

**Cobertura de pruebas:**
- ✅ Creación exitosa de usuarios
- ✅ Validación de email duplicado
- ✅ Búsquedas por ID y email (exitosas y fallidas)
- ✅ Listado con paginación
- ✅ Actualización de datos y contraseñas
- ✅ Eliminación (soft delete)
- ✅ Verificación de existencia y conteo

**Configuración de pruebas:**
- SQLite en memoria para aislamiento
- Fixtures con engine, session, repositorio y datos de ejemplo
- Configuración independiente por cada prueba

### `/backend/tests/test_api/test_auth_endpoints.py` - Pruebas de Endpoints
**Propósito:** 15 pruebas de integración de la API

**Cobertura de pruebas:**
- ✅ Registro exitoso y validaciones
- ✅ Login exitoso y credenciales inválidas
- ✅ Usuario inactivo y emails inexistentes
- ✅ Endpoint `/me` con tokens válidos e inválidos
- ✅ Validaciones de formularios (emails, contraseñas)
- ✅ Flujo completo de autenticación
- ✅ Manejo de errores HTTP apropiados

**Configuración de pruebas:**
- TestClient de FastAPI con base de datos en memoria
- Override de dependencias para aislamiento
- Fixtures para cliente, sesión y datos de ejemplo

---

## 🗄️ Migraciones de Base de Datos

### `/backend/alembic/versions/4e467837c286_add_users_table.py` - Migración de Usuarios
**Propósito:** Crea la tabla users en PostgreSQL

**Estructura creada:**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    rol VARCHAR NOT NULL DEFAULT 'vendedor',
    hashed_password VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE UNIQUE INDEX ix_users_email ON users (email);
```

**Corrección aplicada:**
- Agregado `import sqlmodel` para resolver dependencias de tipos

---

## 🔄 Flujo de Datos Implementado

### Endpoint de Registro - Ejemplo de Flujo Completo

```mermaid
graph TD
    A[Cliente HTTP] -->|POST /auth/register| B[FastAPI Endpoint]
    B --> C[Validación Pydantic]
    C --> D[RegisterUseCase]
    D --> E[Validar Rol]
    E --> F[Verificar Email Único]
    F --> G[SQLUserRepository.create]
    G --> H[Hash Password con bcrypt]
    H --> I[Insert en PostgreSQL]
    I --> J[AuthUtils.create_user_token]
    J --> K[JWT Token Generado]
    K --> L[Response con Token + User]
    L --> A
```

### Endpoint de Login - Flujo de Autenticación

```mermaid
graph TD
    A[Cliente HTTP] -->|POST /auth/login| B[FastAPI Endpoint]
    B --> C[Validación Pydantic]
    C --> D[LoginUseCase]
    D --> E[SQLUserRepository.get_by_email]
    E --> F[Verificar Usuario Activo]
    F --> G[AuthUtils.verify_password]
    G --> H[AuthUtils.create_user_token]
    H --> I[JWT Token Generado]
    I --> J[Response con Token + User]
    J --> A
```

### Endpoint `/me` - Flujo de Autorización

```mermaid
graph TD
    A[Cliente HTTP] -->|GET /auth/me + Bearer Token| B[HTTPBearer Security]
    B --> C[GetCurrentUserUseCase]
    C --> D[AuthUtils.get_user_from_token]
    D --> E[Validar Token JWT]
    E --> F[SQLUserRepository.get_by_id]
    F --> G[Verificar Usuario Activo]  
    G --> H[Response con User Info]
    H --> A
```

---

## 🔧 Configuración y Variables de Entorno

### Variables de Entorno Implementadas

| Variable | Valor Actual | Propósito |
|----------|--------------|-----------|
| `DATABASE_URL` | `postgresql+psycopg://admin:admin@localhost:5432/inventario` | Conexión a PostgreSQL |
| `JWT_SECRET_KEY` | `your-secret-key-change-in-production` | Clave para firmar JWT |
| `ALGORITHM` | `HS256` | Algoritmo de firma JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Tiempo de vida del token |

### Dependencias Instaladas (requirements.txt)

```
fastapi                     # Framework web principal
uvicorn[standard]          # Servidor ASGI
sqlmodel                   # ORM + validación
psycopg[binary]           # Driver PostgreSQL
alembic                    # Migraciones
pydantic>=2.6.0           # Validación de datos
python-jose[cryptography] # JWT tokens
passlib[bcrypt]           # Hash de contraseñas
pytest                     # Framework de testing
pytest-cov                # Cobertura de pruebas
pytest-asyncio           # Testing asíncrono
python-multipart          # Formularios multipart
email-validator           # Validación de emails
httpx                     # Cliente HTTP para pruebas
```

---

## 🚀 Comandos de Desarrollo Actualizados

### Servidor de Desarrollo
```bash
# Desde /backend
source venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Migraciones
```bash
# Crear nueva migración
alembic revision --autogenerate -m "descripción del cambio"

# Aplicar migraciones
alembic upgrade head

# Ver historial
alembic history

# Ver estado actual
alembic current
```

### Testing
```bash
# Todas las pruebas (30 pruebas)
pytest

# Solo repositorio (15 pruebas)
pytest tests/test_infrastructure/

# Solo API (15 pruebas)
pytest tests/test_api/

# Con cobertura detallada
pytest --cov=app --cov-report=html
```

### Pruebas de API Manual
```bash
# Registrar usuario
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "nombre": "Test User", "rol": "vendedor", "password": "password123"}'

# Hacer login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Obtener usuario actual (reemplazar TOKEN)
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer TOKEN_JWT_AQUI"
```

---

## 📋 Estado de Implementación por Componente

| Componente | Estado | Descripción |
|------------|--------|-------------|
| **FastAPI Base** | ✅ Implementado | Servidor con endpoints de auth |
| **Configuración BD** | ✅ Implementado | SQLModel + PostgreSQL funcionando |
| **Migraciones** | ✅ Implementado | Tabla users creada |
| **Modelo User** | ✅ Implementado | Entidad completa con roles |
| **Repositorio User** | ✅ Implementado | CRUD completo con validaciones |
| **Casos de Uso Auth** | ✅ Implementado | Login, Register, GetCurrentUser |
| **Endpoints Auth** | ✅ Implementado | 3 endpoints funcionando |
| **Sistema de Testing** | ✅ Implementado | 30 pruebas (100% pasando) |
| **Autenticación JWT** | ✅ Implementado | Tokens funcionando |
| **Autorización RBAC** | ⏳ Preparado | Roles definidos, middleware pendiente |
| **Gestión de Productos** | ⏳ Pendiente | Próxima fase |
| **Sistema de Inventario** | ⏳ Pendiente | Próxima fase |

---

## 🔍 Puntos de Extensión Preparados

### Para Implementar Autorización por Roles:
1. Crear middleware de autorización en `/app/infrastructure/auth/`
2. Decorator `@require_role()` para endpoints
3. Dependency `get_current_user_with_role()` para FastAPI

### Para Agregar Nuevos Modelos (Productos):
1. Crear entidad en `/app/domain/models/product.py`
2. Crear interfaz en `/app/application/services/i_product_repository.py`
3. Implementar en `/app/infrastructure/repositories/product_repository.py`
4. Generar migración con Alembic
5. Casos de uso en `/app/application/use_cases/product_use_cases.py`
6. Endpoints en `/app/api/v1/endpoints/products.py`
7. Esquemas en `/app/api/v1/schemas.py`
8. Pruebas en `/tests/`

### Para Implementar Middleware de Autorización:
```python
# Ejemplo de estructura preparada
async def get_current_active_user(token: str = Depends(oauth2_scheme)):
    # Usar GetCurrentUserUseCase
    pass

async def require_role(required_role: str):
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.rol != required_role:
            raise HTTPException(403, "Insufficient permissions")
        return current_user
    return role_checker
```

---

## 📊 Métricas del Sistema

### Cobertura de Código
- **30 pruebas** implementadas (100% exitosas)
- **15 pruebas** de infraestructura (repositorio)
- **15 pruebas** de presentación (API)
- **Cobertura esperada:** >95% en lógica de negocio

### Arquitectura Clean
- **4 capas** bien definidas con responsabilidades claras
- **Inversión de dependencias** aplicada correctamente
- **Separación de concerns** entre autenticación, persistencia y presentación
- **Testabilidad** máxima con mocks e inyección de dependencias

### Performance
- **JWT tokens** con expiración de 30 minutos
- **Connection pooling** configurado en PostgreSQL
- **Consultas optimizadas** con índices en campos clave
- **Soft delete** para mantener integridad referencial

El sistema está ahora completamente preparado para la **Fase 3: Gestión de Productos e Inventario** 🚀
