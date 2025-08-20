"""
Punto de entrada principal del Sistema de Gestión Empresarial.
Este archivo inicializa la aplicación FastAPI siguiendo los principios de Clean Architecture.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

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

app = FastAPI(
    title="Sistema de Gestión Empresarial Multi-Tenant",
    description="API para gestión de inventario, contabilidad, facturación y ventas con soporte multi-tenant",
    version="2.0.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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