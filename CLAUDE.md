# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Business Management System (Sistema de Gestión Empresarial) built with Clean Architecture principles. The system handles inventory management, accounting, invoicing, and sales operations for small to medium businesses in Colombia.

**Current Status**: Implementing Step 3.2 (Inventory Management Module) of the implementation plan.

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

### Current Implementation Status
✅ **Completed Modules:**
- User authentication and management (JWT-based)
- Product CRUD operations with business rule validation
- Inventory movements with weighted average cost calculation

🏗️ **In Progress:**
- Inventory management module (Step 3.2)
- Advanced inventory reporting

⏳ **Planned:**
- Accounting module with chart of accounts
- Invoicing with automatic journal entries
- Financial reporting and closing processes

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
- `movimientos_inventario` - Inventory movements with cost tracking

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

### Inventory (`/api/v1/inventario`)
- `POST /movimientos/` - Create inventory movement
- `GET /movimientos/` - List movements (paginated, filterable)
- `GET /movimientos/{id}` - Get specific movement
- `GET /kardex/{producto_id}` - Get product kardex
- `GET /resumen/` - Get inventory summary
- `GET /estadisticas/` - Get inventory statistics

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
1. Define domain model in `domain/models/`
2. Create repository interface in `application/services/`
3. Implement repository in `infrastructure/repositories/`
4. Create use cases in `application/use_cases/`
5. Add API schemas to `api/v1/schemas.py`
6. Implement endpoints in `api/v1/endpoints/`
7. Add dependency injection in endpoint functions
8. Write comprehensive tests

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

This project follows a detailed 7-phase implementation plan located in `memory-bank/implementation-plan.md`. Currently implementing:

- **Phase 3**: Product and Inventory Module
- **Step 3.2**: Inventory movements with weighted average cost calculation

Each step includes specific validation tests and business rule implementation requirements.