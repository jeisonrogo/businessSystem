# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Multi-Tenant Business Management System** (Sistema de Gestión Empresarial Multi-Tienda) built with Clean Architecture principles. The system handles inventory management, accounting, invoicing, and sales operations for small to medium businesses with multiple locations in Colombia.

**Current Status**: **Phase 4 Completed** - Multi-tenant foundation with local-based data isolation and tenant-aware filtering implemented across all modules.

## Development Commands

### Backend Setup and Development
```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start development server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Alternative start method
python main.py
```

### Database Management (Alembic)
```bash
# From backend/ directory with venv activated
# Create new migration
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head

# View migration history
alembic history

# Check current migration status
alembic current

# Downgrade to previous migration
alembic downgrade -1
```

### Docker Services
```bash
# Start PostgreSQL database
docker-compose up -d database

# Stop all services
docker-compose down

# View logs
docker-compose logs database
```

### Testing
```bash
# Run all tests (50+ tests implemented)
pytest

# Run specific test modules
pytest tests/test_infrastructure/test_user_repository.py
pytest tests/test_infrastructure/test_product_repository.py
pytest tests/test_api/test_auth_endpoints.py
pytest tests/test_api/test_products_endpoints.py

# Run tests with coverage report
pytest --cov=app --cov-report=html

# Run integration tests
pytest tests/test_integration_complete.py
```

### Demo Data Population
```bash
# Populate database with demo data
python populate_demo_data.py

# Populate multi-tenant demo data with stores and locals
python populate_multi_tenant_demo.py
```

## Architecture

This system follows **Clean Architecture** with strict separation of concerns:

### Layer Structure
```
backend/app/
├── domain/models/              # Entities and business rules (innermost layer)
├── application/
│   ├── services/              # Repository interfaces (ports)
│   └── use_cases/            # Business logic orchestration
├── infrastructure/
│   ├── repositories/         # Repository implementations (adapters)
│   ├── database/            # Database configuration
│   └── auth/               # Authentication utilities
└── api/v1/endpoints/       # FastAPI REST endpoints (outermost layer)
```

### Key Principles Applied
- **Dependency Inversion**: Inner layers define interfaces, outer layers implement them
- **Repository Pattern**: Data access abstracted through interfaces
- **Use Cases**: Business logic encapsulated in specific use case classes
- **Domain-Driven Design**: Rich domain models with business rules
- **Multi-Tenancy**: Local-based data isolation with tenant context middleware
- **Clean API Design**: Tenant-aware endpoints with automatic filtering

### Current Implementation Status
✅ **Completed Modules:**
- **Multi-Tenant Foundation**: Complete local-based data isolation
- **User Authentication**: JWT-based with role-based access control
- **Store & Local Management**: Multi-location support with hierarchical structure
- **Product Management**: CRUD operations with tenant-aware filtering
- **Inventory Management**: Movements, kardex, and statistics per local
- **Invoice Management**: Local-specific invoicing with inventory integration
- **Dashboard**: KPIs and metrics filtered by selected local context

✅ **Multi-Tenant Features Implemented:**
- **Tenant Context Middleware**: Automatic local selection and validation
- **Local-Based Filtering**: All endpoints filter data by selected local
- **Stock Management**: Per-local inventory tracking with StockLocal model
- **User-Local Assignments**: Users can be assigned to specific locals
- **Unified Views**: Option to view consolidated data across all locals

⏳ **Planned:**
- Accounting module with chart of accounts
- Financial reporting and closing processes
- Advanced multi-tenant reporting and analytics

## Business Rules Implemented

### Product Management
- **BR-01**: Stock cannot be negative (validated at model and repository level)
- **BR-02**: SKU must be unique and cannot be modified after creation
- **BR-04**: Price history tracking (prepared for implementation)

### Inventory Management
- **BR-11**: Weighted average cost method for inventory valuation
- Automatic stock updates with audit trail (stock_anterior/stock_posterior)

### User Management
- **BR-06**: Role-based access control (roles defined: ADMINISTRADOR, GERENTE_VENTAS, CONTADOR, VENDEDOR)
- **BR-07**: Users can be assigned to specific locals for data access control

### Multi-Tenant Architecture
- **MT-01**: All business data is isolated by local (tienda -> local hierarchy)
- **MT-02**: Stock tracking is maintained separately per local using StockLocal model
- **MT-03**: Inventory movements are local-specific with proper tenant context
- **MT-04**: Invoice creation requires local context for proper stock deduction
- **MT-05**: Dashboard metrics filter by selected local or show unified view

## Database Configuration

### Connection Details
- **Host**: localhost:5432
- **Database**: inventario
- **Username**: admin
- **Password**: admin
- **Engine**: PostgreSQL 17.2 with SQLModel/SQLAlchemy

### Key Tables
- `users` - User accounts with role-based permissions
- `products` - Product catalog with pricing and stock
- `movimientos_inventario` - Inventory movements with cost tracking and local_id
- `tiendas` - Store definitions (top-level tenant boundary)
- `locales` - Physical locations within stores
- `stock_local` - Per-local stock tracking with separate quantities per location
- `usuarios_locales` - User-to-local assignments for access control
- `facturas` - Invoices with local_id for tenant isolation
- `clientes` - Customer database

## API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /register` - Register new user
- `POST /login` - Authenticate user (returns JWT)
- `GET /me` - Get current user info (requires Bearer token)

### Products (`/api/v1/products`)
- `POST /` - Create product
- `GET /` - List products (paginated, searchable)
- `GET /{id}` - Get product by ID
- `GET /sku/{sku}` - Get product by SKU
- `PUT /{id}` - Update product (SKU immutable)
- `DELETE /{id}` - Soft delete product
- `PATCH /{id}/stock` - Update stock only
- `GET /low-stock/` - Get products below threshold

### Inventory (`/api/v1/inventario`) - **Tenant-Aware**
- `POST /movimientos/` - Create inventory movement (requires local context)
- `GET /movimientos/` - List movements (filtered by selected local)
- `GET /movimientos/{id}` - Get specific movement
- `GET /kardex/{producto_id}` - Get product kardex (local-specific)
- `GET /resumen/` - Get inventory summary (per local or unified)
- `GET /estadisticas/` - Get inventory statistics (filtered by local)

### Invoices (`/api/v1/facturas`) - **Tenant-Aware**
- `POST /` - Create invoice (requires local context for stock updates)
- `GET /` - List invoices (filtered by selected local)
- `GET /{id}` - Get specific invoice
- `PUT /{id}` - Update invoice
- `DELETE /{id}` - Cancel invoice

### Stores & Locals (`/api/v1/tiendas`, `/api/v1/locales`)
- `GET /tiendas/` - List all stores
- `GET /tiendas/{id}` - Get store details
- `GET /locales/` - List locals (filtered by user permissions)
- `GET /locales/{id}` - Get local details
- `GET /locales/disponibles` - Get available locals for current user

### Tenant Context (`/api/v1/tenant-context`)
- `POST /select-local` - Select active local context
- `GET /current` - Get current tenant context
- `DELETE /clear` - Clear local selection (view all data)

### Dashboard (`/api/v1/dashboard`) - **Tenant-Aware**
- `GET /kpis` - Get KPIs (filtered by selected local or unified)
- `GET /productos-top` - Get top products (local-specific)
- `GET /clientes-top` - Get top clients (local-specific)
- `GET /ventas-por-periodo` - Get sales by period (local-filtered)

### User Management (`/api/v1/users`) - **Enhanced**
- `GET /` - List users with local assignment counts
- `POST /{user_id}/locales` - Assign user to locals
- `GET /{user_id}/locales` - Get user's assigned locals
- `DELETE /{user_id}/locales/{local_id}` - Remove user from local

## Multi-Tenant Architecture Details

### Tenant Context System

The system implements a sophisticated tenant context mechanism that provides automatic data filtering based on the selected local:

#### Tenant Context Middleware
- **Location**: `app/infrastructure/middleware/tenant_middleware.py`
- **Function**: Automatically injects tenant context into all API requests
- **Dependencies**: Available as `TenantContext` dependency in all endpoints

#### Local Selection Flow
1. **Frontend**: User selects local through TenantContext/LocalSwitcher components
2. **API Call**: Selection sent to `/api/v1/tenant-context/select-local`
3. **Session Storage**: Local selection stored in session/state
4. **Request Headers**: `X-Local-Id` header sent with subsequent requests
5. **Middleware**: Tenant middleware processes header and injects context
6. **Endpoints**: All tenant-aware endpoints automatically filter data

#### Data Isolation Strategy
- **Store Level**: Top-level tenant boundary (`tiendas` table)
- **Local Level**: Physical location within store (`locales` table)  
- **Stock Isolation**: Separate inventory tracking per local (`stock_local`)
- **Movement Tracking**: All inventory movements tagged with `local_id`
- **Invoice Isolation**: Invoices tied to specific local for proper stock deduction
- **User Access**: Users assigned to specific locals they can access

### Key Multi-Tenant Models

#### StockLocal Model
```python
class StockLocal(SQLModel, table=True):
    local_id: UUID  # Physical location
    producto_id: UUID  # Product reference
    cantidad: int  # Stock quantity for this local
    costo_promedio: Decimal  # Average cost per local
    stock_minimo: int  # Minimum stock level
    stock_maximo: Optional[int]  # Maximum stock level
```

#### MovimientoInventario with Local Context
```python
class MovimientoInventario(SQLModel, table=True):
    local_id: UUID  # Required for multi-tenant
    producto_id: UUID
    tipo_movimiento: TipoMovimiento
    cantidad: int
    stock_anterior: int  # Local-specific stock before
    stock_posterior: int  # Local-specific stock after
```

### Frontend Multi-Tenant Components

#### TenantContext Provider
- **Location**: `frontend/src/context/TenantContext.tsx`
- **Purpose**: Global state management for tenant context
- **Features**: Local selection, context persistence, automatic API integration

#### LocalSwitcher Component
- **Location**: `frontend/src/components/tenant/TenantSwitcher.tsx`
- **Purpose**: UI component for local selection
- **Features**: Dropdown with available locals, "Toda la tienda" option

#### TenantIndicator Component
- **Location**: `frontend/src/components/tenant/TenantIndicator.tsx`
- **Purpose**: Shows current local context in UI
- **Features**: Visual indicator of active local or unified view

### Critical Bug Fixes Implemented

#### 1. Double Inventory Deduction Fix
- **Problem**: Invoice creation was deducting inventory twice
- **Root Cause**: Both repository and use case creating inventory movements
- **Solution**: Removed duplicate movement creation from use case layer
- **Files**: `app/application/use_cases/factura_use_cases.py`

#### 2. Inventory Movement Registration Fix  
- **Problem**: Manual inventory movements not affecting stock or appearing in listings
- **Root Cause**: Missing tenant context and incorrect stock calculation across all locals
- **Solution**: Added tenant context validation and local-specific stock calculation
- **Files**: `app/api/v1/endpoints/inventario.py`, `app/infrastructure/repositories/inventario_repository.py`

#### 3. Dashboard Filtering Implementation
- **Problem**: Dashboard showed data from all locals regardless of selection
- **Root Cause**: Missing tenant context integration in dashboard endpoints
- **Solution**: Added local filtering to all dashboard metrics and KPIs
- **Files**: Dashboard endpoints, use cases, and repository methods

## Testing Strategy

### Test Coverage
- **Domain Layer**: Entity validation and business rule tests
- **Application Layer**: Use case logic and error handling
- **Infrastructure Layer**: Repository implementations and database operations
- **API Layer**: HTTP endpoint testing with full request/response validation

### Test Configuration
- Uses SQLite in-memory databases for test isolation
- Fixtures provide clean test data for each test
- TestClient from FastAPI for API testing
- Pytest with coverage reporting

## Common Development Patterns

### Creating New Endpoints
1. Define domain model in `domain/models/` (include `local_id` if tenant-aware)
2. Create repository interface in `application/services/`
3. Implement repository in `infrastructure/repositories/` (add local filtering)
4. Create use cases in `application/use_cases/` (accept `local_id` parameter)
5. Add API schemas to `api/v1/schemas.py`
6. Implement endpoints in `api/v1/endpoints/` (add TenantContext dependency)
7. Add dependency injection in endpoint functions
8. Write comprehensive tests (including multi-tenant scenarios)

### Multi-Tenant Endpoint Pattern
```python
@router.get("/")
async def list_items(
    tenant_context: TenantContext = Depends(get_tenant_context),
    repository: Repository = Depends(get_repository)
):
    # Determine local filtering
    filter_local_id = tenant_context.local_id if tenant_context.tiene_contexto_local else None
    
    # Pass to use case
    use_case = ListItemsUseCase(repository)
    items = await use_case.execute(local_id=filter_local_id)
    return items
```

### Repository Multi-Tenant Pattern
```python
async def get_all(self, local_id: Optional[UUID] = None) -> List[Entity]:
    conditions = [Entity.is_active == True]
    if local_id:
        conditions.append(Entity.local_id == local_id)
    
    statement = select(Entity).where(and_(*conditions))
    return self.session.exec(statement).all()
```

### Database Migrations
Always create migrations when modifying models:
1. Modify the SQLModel class
2. Run `alembic revision --autogenerate -m "description"`
3. Review generated migration file
4. Apply with `alembic upgrade head`

### Error Handling
- Use custom exception classes for business rule violations
- Repository layer catches SQLAlchemy errors and converts to business exceptions
- Use cases handle business logic errors
- API layer converts exceptions to appropriate HTTP status codes

## Environment Variables

Set these in production:
```bash
DATABASE_URL=postgresql+psycopg://user:pass@host:port/dbname
JWT_SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Implementation Plan Context

This project follows a detailed 7-phase implementation plan located in `memory-bank/implementation-plan.md`.

### **COMPLETED PHASES:**

✅ **Phase 1**: Foundation and Authentication
- User authentication system with JWT
- Role-based access control
- Basic project structure with Clean Architecture

✅ **Phase 2**: Multi-Tenant Foundation  
- Store and Local entity models
- User-Local assignment system
- Tenant context middleware and API integration

✅ **Phase 3**: Product and Inventory Management
- Product CRUD operations with business rule validation
- Inventory movements with weighted average cost calculation
- Multi-tenant stock tracking with StockLocal model
- Kardex and inventory reporting

✅ **Phase 4**: Multi-Tenant Integration & Bug Fixes
- **Invoice Management**: Local-specific invoicing with proper inventory integration
- **Dashboard Implementation**: KPIs and metrics with tenant-aware filtering
- **Critical Bug Fixes**: Double inventory deduction, movement registration, dashboard filtering
- **Frontend Components**: TenantContext, LocalSwitcher, and TenantIndicator components

### **CURRENT STATUS**: 
**Phase 4 Completed** - Multi-tenant system fully operational with local-based data isolation

### **NEXT PHASES**:
⏳ **Phase 5**: Accounting Module
- Chart of accounts implementation
- Automatic journal entries from invoice operations
- Financial reporting per local

⏳ **Phase 6**: Advanced Reporting & Analytics
- Multi-tenant consolidated reporting
- Advanced inventory analytics
- Financial dashboards and KPIs

⏳ **Phase 7**: Production Deployment
- Environment configuration
- Performance optimization
- Security hardening

Each phase includes comprehensive testing and business rule validation requirements.