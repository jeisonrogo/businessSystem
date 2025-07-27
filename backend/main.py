"""
Punto de entrada principal del Sistema de Gestión Empresarial.
Este archivo inicializa la aplicación FastAPI siguiendo los principios de Clean Architecture.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints.auth import router as auth_router

app = FastAPI(
    title="Sistema de Gestión Empresarial",
    description="API para la gestión integral de productos, inventario, facturación y contabilidad",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuración de CORS para permitir el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend en desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers de la API
app.include_router(auth_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Endpoint raíz que proporciona información básica de la API."""
    return {
        "message": "Sistema de Gestión Empresarial API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud del servicio."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 