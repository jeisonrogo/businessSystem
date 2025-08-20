"""
Middleware para gestión del contexto multi-tenant en FastAPI.

Intercepta las requests para establecer y propagar el contexto de tenant
a través de toda la aplicación.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Optional, Dict, Any
from uuid import UUID
import json
import logging

from app.domain.models.tenant_context import (
    TenantContext, 
    TenantContextError,
    PermisoInsuficienteError,
    ContextoInvalidoError
)
from app.application.services.tenant_context_service import TenantContextService

logger = logging.getLogger(__name__)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware para gestión automática del contexto multi-tenant.
    
    Se ejecuta en cada request para:
    1. Extraer información de tenant del token/headers
    2. Crear y validar el contexto de tenant
    3. Propagar el contexto a través de la aplicación
    4. Manejar errores de contexto/permisos
    """

    def __init__(
        self,
        app: ASGIApp,
        tenant_context_service: TenantContextService,
        exclude_paths: Optional[list] = None
    ):
        super().__init__(app)
        self.tenant_context_service = tenant_context_service
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register"
        ]

    async def dispatch(self, request: Request, call_next):
        """
        Procesa cada request para gestionar el contexto multi-tenant.

        Args:
            request: Request de FastAPI
            call_next: Siguiente middleware/handler

        Returns:
            Response con contexto de tenant configurado
        """
        # Saltar middleware para rutas excluidas
        if self._should_skip_middleware(request):
            return await call_next(request)

        try:
            # Extraer usuario de la request (debe haberse ejecutado auth middleware)
            usuario = getattr(request.state, 'current_user', None)
            if not usuario:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Usuario no autenticado"}
                )

            # Extraer local_id del header o query params si está presente
            local_id = self._extract_local_id(request)

            # Crear contexto de tenant para el usuario
            tenant_context = self.tenant_context_service.crear_contexto_para_usuario(
                usuario=usuario,
                local_id=local_id
            )

            # Almacenar contexto en el estado de la request
            request.state.tenant_context = tenant_context

            # Agregar headers de contexto para debugging
            response = await call_next(request)
            self._add_context_headers(response, tenant_context)

            return response

        except ContextoInvalidoError as e:
            logger.warning(f"Contexto inválido para usuario {getattr(usuario, 'id', 'unknown')}: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": "Contexto de tenant inválido",
                    "error_type": "contexto_invalido",
                    "message": str(e)
                }
            )

        except PermisoInsuficienteError as e:
            logger.warning(f"Permiso insuficiente para usuario {getattr(usuario, 'id', 'unknown')}: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": "Permisos insuficientes",
                    "error_type": "permiso_insuficiente",
                    "permiso_requerido": e.permiso_requerido,
                    "local_id": str(e.local_id) if e.local_id else None
                }
            )

        except TenantContextError as e:
            logger.error(f"Error de contexto tenant: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Error interno del sistema multi-tenant",
                    "error_type": "tenant_context_error"
                }
            )

        except Exception as e:
            logger.error(f"Error inesperado en tenant middleware: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Error interno del servidor"}
            )

    def _should_skip_middleware(self, request: Request) -> bool:
        """
        Determina si se debe saltar el middleware para esta request.

        Args:
            request: Request de FastAPI

        Returns:
            bool: True si debe saltarse, False si no
        """
        path = request.url.path
        
        # Rutas excluidas explícitamente
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True

        # Rutas de archivos estáticos
        if path.startswith("/static/") or path.startswith("/media/"):
            return True

        return False

    def _extract_local_id(self, request: Request) -> Optional[UUID]:
        """
        Extrae el local_id del header X-Local-ID o query parameter.

        Args:
            request: Request de FastAPI

        Returns:
            UUID del local o None si no está presente
        """
        # Intentar desde header personalizado
        local_id_header = request.headers.get("X-Local-ID")
        if local_id_header:
            try:
                return UUID(local_id_header)
            except ValueError:
                logger.warning(f"Header X-Local-ID inválido: {local_id_header}")

        # Intentar desde query parameter
        local_id_param = request.query_params.get("local_id")
        if local_id_param:
            try:
                return UUID(local_id_param)
            except ValueError:
                logger.warning(f"Query param local_id inválido: {local_id_param}")

        return None

    def _add_context_headers(self, response, tenant_context: TenantContext) -> None:
        """
        Agrega headers informativos sobre el contexto actual.

        Args:
            response: Response de FastAPI
            tenant_context: Contexto actual
        """
        if hasattr(response, 'headers'):
            response.headers["X-Tenant-Store"] = tenant_context.tienda_codigo
            
            if tenant_context.tiene_contexto_local:
                response.headers["X-Tenant-Local"] = tenant_context.local_codigo
            
            # Header con información del contexto para debugging (solo en desarrollo)
            # response.headers["X-Tenant-Context"] = json.dumps({
            #     "tienda_id": str(tenant_context.tienda_id),
            #     "local_id": str(tenant_context.local_id) if tenant_context.local_id else None,
            #     "tipo_contexto": tenant_context.tipo_contexto.value
            # })


class TenantContextDependency:
    """
    Dependency para inyectar el contexto de tenant en endpoints.
    
    Extrae el contexto desde el estado de la request establecido
    por el middleware.
    """

    def __call__(self, request: Request) -> TenantContext:
        """
        Obtiene el contexto de tenant de la request.

        Args:
            request: Request de FastAPI

        Returns:
            TenantContext: Contexto actual

        Raises:
            HTTPException: Si no hay contexto disponible
        """
        tenant_context = getattr(request.state, 'tenant_context', None)
        
        if not tenant_context:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Contexto de tenant no disponible"
            )

        return tenant_context


class LocalContextDependency:
    """
    Dependency que requiere contexto de local específico.
    
    Valida que el contexto actual incluya un local activo.
    """

    def __call__(self, request: Request) -> TenantContext:
        """
        Obtiene el contexto de local requerido.

        Args:
            request: Request de FastAPI

        Returns:
            TenantContext: Contexto con local activo

        Raises:
            HTTPException: Si no hay contexto de local
        """
        tenant_context = getattr(request.state, 'tenant_context', None)
        
        if not tenant_context:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Contexto de tenant no disponible"
            )

        if not tenant_context.tiene_contexto_local:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta operación requiere contexto de local específico",
                headers={"X-Required-Header": "X-Local-ID"}
            )

        return tenant_context


class PermissionRequiredDependency:
    """
    Dependency que valida permisos específicos en el contexto actual.
    """

    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(self, request: Request) -> TenantContext:
        """
        Valida el permiso requerido en el contexto actual.

        Args:
            request: Request de FastAPI

        Returns:
            TenantContext: Contexto validado

        Raises:
            HTTPException: Si no tiene el permiso requerido
        """
        tenant_context = getattr(request.state, 'tenant_context', None)
        
        if not tenant_context:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Contexto de tenant no disponible"
            )

        # Validar operación en contexto actual
        if not tenant_context.validar_operacion_en_contexto_actual(self.required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso insuficiente: se requiere '{self.required_permission}'"
            )

        return tenant_context


# Instancias de dependencies para uso en endpoints
get_tenant_context = TenantContextDependency()
require_local_context = LocalContextDependency()

# Factory functions para permisos específicos
def require_permission(permission: str):
    """Factory para crear dependency de permiso específico."""
    return PermissionRequiredDependency(permission)

# Dependencies comunes pre-configurados
require_venta_permission = require_permission("venta")
require_transferencia_permission = require_permission("transferencia")
require_ver_stock_permission = require_permission("consulta_stock")
require_modificar_precios_permission = require_permission("modificar_precios")
require_ver_reportes_permission = require_permission("ver_reportes")
require_gestionar_usuarios_permission = require_permission("gestion_usuarios")