"""
Punto de entrada principal del Sistema de Gestión Empresarial.
Este archivo inicializa la aplicación FastAPI siguiendo los principios de Clean Architecture.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

# Configuration
from app.config import settings

# Middleware imports
from app.infrastructure.middleware.tenant_middleware import TenantContextMiddleware
from app.application.services.tenant_context_service import TenantContextService
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.tienda_repository import TiendaRepository
from app.infrastructure.repositories.local_repository import LocalRepository
from app.infrastructure.repositories.usuario_local_repository import UsuarioLocalRepository

# Existing endpoints
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.products import router as products_router
from app.api.v1.endpoints.inventario import router as inventario_router
from app.api.v1.endpoints.contabilidad import router as contabilidad_router
from app.api.v1.endpoints.asientos import router as asientos_router
from app.api.v1.endpoints.clientes import router as clientes_router
from app.api.v1.endpoints.facturas import router as facturas_router
from app.api.v1.endpoints.dashboard import router as dashboard_router

# Multi-tenant endpoints
from app.api.v1.endpoints.tiendas import router as tiendas_router
from app.api.v1.endpoints.locales import router as locales_router
from app.api.v1.endpoints.stock_local import router as stock_local_router
from app.api.v1.endpoints.transferencias import router as transferencias_router
from app.api.v1.endpoints.usuario_locales import router as usuario_locales_router
from app.api.v1.endpoints.tenant_context import router as tenant_context_router
from app.api.v1.endpoints.upload import router as upload_router

app = FastAPI(
    title="Sistema de Gestión Empresarial Multi-Tenant",
    description="API para gestión de inventario, contabilidad, facturación y ventas con soporte multi-tenant",
    version="2.0.0"
)

# Configuración de CORS desde settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

def create_tenant_service_for_session(session) -> TenantContextService:
    """Crea una instancia del servicio de contexto de tenant para una sesión específica."""
    tienda_repo = TiendaRepository(session)
    local_repo = LocalRepository(session)
    usuario_local_repo = UsuarioLocalRepository(session)
    
    return TenantContextService(
        tienda_repository=tienda_repo,
        local_repository=local_repo,
        usuario_local_repository=usuario_local_repo
    )

# Configuración del middleware de contexto multi-tenant
app.add_middleware(
    TenantContextMiddleware,
    tenant_context_service=None,  # Se creará dinámicamente por request
    exclude_paths=[
        "/docs",
        "/redoc", 
        "/openapi.json",
        "/health",
        "/",
        "/api/v1/auth/login",
        "/api/v1/auth/register"
    ]
)

# Incluir routers existentes
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(products_router, prefix="/api/v1/products", tags=["products"])
app.include_router(inventario_router, prefix="/api/v1/inventario", tags=["inventario"])
app.include_router(contabilidad_router, prefix="/api/v1/cuentas", tags=["contabilidad"])
app.include_router(asientos_router, prefix="/api/v1/asientos", tags=["asientos-contables"])
app.include_router(clientes_router, prefix="/api/v1/clientes", tags=["clientes"])
app.include_router(facturas_router, prefix="/api/v1/facturas", tags=["facturas"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["dashboard"])

# Incluir routers multi-tenant
app.include_router(tiendas_router, prefix="/api/v1")
app.include_router(locales_router, prefix="/api/v1")
app.include_router(stock_local_router, prefix="/api/v1")
app.include_router(transferencias_router, prefix="/api/v1")
app.include_router(usuario_locales_router, prefix="/api/v1")
app.include_router(tenant_context_router, prefix="/api/v1")
app.include_router(upload_router, prefix="/api/v1/upload", tags=["upload"])

# Static files serving for uploads
import os
uploads_path = "uploads"
if not os.path.exists(uploads_path):
    os.makedirs(uploads_path)
    
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")


@app.get("/")
async def root():
    """Endpoint raíz que proporciona información básica de la API."""
    return {
        "message": "Sistema de Gestión Empresarial Multi-Tenant API",
        "version": "2.0.0",
        "status": "active",
        "features": [
            "Multi-tenant architecture",
            "Independent inventory per location",
            "Inter-location transfers",
            "Granular user permissions",
            "Weighted average costing"
        ],
        "timestamp": datetime.now()
    }


@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud del servicio."""
    return {
        "status": "ok",
        "timestamp": datetime.now()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 