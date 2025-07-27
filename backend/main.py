"""
Punto de entrada principal del Sistema de Gestión Empresarial.
Este archivo inicializa la aplicación FastAPI siguiendo los principios de Clean Architecture.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.products import router as products_router

app = FastAPI(
    title="Sistema de Gestión Empresarial",
    description="API para gestión de inventario, contabilidad, facturación y ventas",
    version="1.0.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(products_router, prefix="/api/v1/products", tags=["products"])


@app.get("/")
async def root():
    """Endpoint raíz que proporciona información básica de la API."""
    return {
        "message": "Sistema de Gestión Empresarial API",
        "version": "1.0.0",
        "status": "active",
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