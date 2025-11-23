"""
Middleware para logging automático de requests y responses.

Registra:
- Request entrante con método, path, headers
- Response saliente con status code, duración
- Errores y excepciones con traceback
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.infrastructure.logging import (
    get_logger,
    set_request_id,
    clear_request_id,
    log_with_context
)

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware que registra todas las requests y responses.

    Características:
    - Genera y trackea request_id único
    - Registra método, path, query params
    - Registra status code y tiempo de respuesta
    - Registra errores con traceback completo
    - Excluye endpoints de health check
    """

    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: list[str] = None
    ):
        """
        Inicializa el middleware.

        Args:
            app: Aplicación ASGI
            exclude_paths: Paths a excluir del logging (ej: /health, /metrics)
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Procesa la request y registra información relevante.

        Args:
            request: Request entrante
            call_next: Siguiente middleware/handler

        Returns:
            Response
        """
        # Generar y establecer request ID
        request_id = request.headers.get("X-Request-ID") or set_request_id()

        # Agregar request_id a los headers de respuesta
        request.state.request_id = request_id

        # Verificar si debemos loggear este path
        if self._should_exclude(request.url.path):
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

        # Información de la request
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        client_host = request.client.host if request.client else "unknown"

        # Log de request entrante
        log_with_context(
            logger,
            "info",
            f"→ {method} {path}",
            method=method,
            path=path,
            query_params=query_params if query_params else None,
            client_ip=client_host,
            user_agent=request.headers.get("user-agent", "unknown")
        )

        # Medir tiempo de procesamiento
        start_time = time.time()

        try:
            # Procesar request
            response = await call_next(request)

            # Calcular duración
            duration_ms = (time.time() - start_time) * 1000

            # Log de response exitosa
            log_level = "info" if response.status_code < 400 else "warning"
            log_with_context(
                logger,
                log_level,
                f"← {method} {path} - {response.status_code} ({duration_ms:.2f}ms)",
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2)
            )

            # Agregar headers de respuesta
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

            return response

        except Exception as e:
            # Calcular duración incluso en error
            duration_ms = (time.time() - start_time) * 1000

            # Log de error
            log_with_context(
                logger,
                "error",
                f"✗ {method} {path} - Exception: {str(e)} ({duration_ms:.2f}ms)",
                method=method,
                path=path,
                error_type=type(e).__name__,
                error_message=str(e),
                duration_ms=round(duration_ms, 2)
            )

            # Re-lanzar excepción para que FastAPI la maneje
            raise

        finally:
            # Limpiar request_id del contexto
            clear_request_id()

    def _should_exclude(self, path: str) -> bool:
        """
        Verifica si el path debe ser excluido del logging.

        Args:
            path: Path de la request

        Returns:
            True si debe excluirse
        """
        return any(path.startswith(excluded) for excluded in self.exclude_paths)
