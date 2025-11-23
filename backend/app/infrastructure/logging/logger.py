"""
Sistema de Logging Centralizado con Mejores Prácticas.

Este módulo proporciona:
- Logging estructurado con contexto
- Decoradores para tracing automático
- Formateo consistente de logs
- Niveles de log configurables
- Correlación de requests
"""

import logging
import sys
import json
import traceback
from functools import wraps
from typing import Any, Callable, Optional
from datetime import datetime
from contextvars import ContextVar
import uuid

# Context variable para request ID (permite tracking a través de la request)
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


class StructuredFormatter(logging.Formatter):
    """
    Formateador que produce logs en formato JSON estructurado.

    Formato incluye:
    - timestamp: ISO 8601
    - level: nivel de log
    - logger: nombre del logger
    - message: mensaje del log
    - request_id: ID de la request (si existe)
    - extras: campos adicionales
    """

    def format(self, record: logging.LogRecord) -> str:
        """Formatea el record como JSON estructurado."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Agregar request_id si existe
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        # Agregar información de excepción si existe
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Agregar campos extra personalizados
        if hasattr(record, 'extras'):
            log_data["extras"] = record.extras

        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """
    Formateador con colores para desarrollo local.
    Más legible que JSON en consola.
    """

    # Códigos de color ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Verde
        'WARNING': '\033[33m',    # Amarillo
        'ERROR': '\033[31m',      # Rojo
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Formatea el record con colores."""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # Request ID
        request_id = request_id_var.get()
        req_id_str = f"[{request_id[:8]}]" if request_id else "[--------]"

        # Formato base
        log_msg = (
            f"{color}{record.levelname:8}{reset} "
            f"{req_id_str} "
            f"{record.name:30} | "
            f"{record.getMessage()}"
        )

        # Agregar extras si existen
        if hasattr(record, 'extras'):
            log_msg += f" | {json.dumps(record.extras, ensure_ascii=False)}"

        # Agregar excepción si existe
        if record.exc_info:
            log_msg += f"\n{self.formatException(record.exc_info)}"

        return log_msg


def setup_logging(
    level: str = "INFO",
    use_json: bool = False,
    log_file: Optional[str] = None
) -> None:
    """
    Configura el sistema de logging de la aplicación.

    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Si True, usa formato JSON. Si False, usa formato con colores
        log_file: Ruta opcional para guardar logs en archivo
    """
    # Configurar nivel
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Limpiar handlers existentes
    root_logger.handlers.clear()

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Usar formatter apropiado
    if use_json:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(ColoredFormatter())

    root_logger.addHandler(console_handler)

    # Handler para archivo si se especifica
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(StructuredFormatter())  # Siempre JSON en archivo
        root_logger.addHandler(file_handler)

    # Silenciar logs muy verbosos de librerías externas
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger configurado para el módulo especificado.

    Args:
        name: Nombre del logger (típicamente __name__)

    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


def log_with_context(logger: logging.Logger, level: str, message: str, **kwargs) -> None:
    """
    Registra un log con contexto adicional.

    Args:
        logger: Logger a usar
        level: Nivel del log (debug, info, warning, error, critical)
        message: Mensaje del log
        **kwargs: Campos extra para agregar al log
    """
    log_func = getattr(logger, level.lower())

    # Crear un record con extras
    extra = {'extras': kwargs} if kwargs else {}
    log_func(message, extra=extra)


def log_function_call(
    logger: Optional[logging.Logger] = None,
    log_args: bool = True,
    log_result: bool = True,
    log_exceptions: bool = True
):
    """
    Decorador para logging automático de llamadas a funciones.

    Registra:
    - Entrada a la función con argumentos
    - Salida de la función con resultado
    - Excepciones si ocurren

    Args:
        logger: Logger a usar (si None, usa el del módulo de la función)
        log_args: Si True, registra los argumentos
        log_result: Si True, registra el resultado
        log_exceptions: Si True, registra las excepciones

    Ejemplo:
        @log_function_call()
        def my_function(user_id: int):
            return f"User {user_id}"
    """
    def decorator(func: Callable) -> Callable:
        # Usar logger del módulo de la función si no se especifica
        func_logger = logger or get_logger(func.__module__)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Información de entrada
            func_name = f"{func.__module__}.{func.__name__}"
            extras = {"function": func_name}

            if log_args:
                # Sanitizar argumentos sensibles
                safe_args = _sanitize_args(args, kwargs)
                extras["args"] = safe_args

            log_with_context(func_logger, "debug", f"→ Entering {func_name}", **extras)

            try:
                # Ejecutar función
                result = await func(*args, **kwargs)

                # Información de salida
                if log_result:
                    # Sanitizar resultado si es necesario
                    safe_result = _sanitize_value(result)
                    log_with_context(
                        func_logger,
                        "debug",
                        f"← Exiting {func_name}",
                        function=func_name,
                        result=safe_result
                    )
                else:
                    log_with_context(func_logger, "debug", f"← Exiting {func_name}", function=func_name)

                return result

            except Exception as e:
                if log_exceptions:
                    log_with_context(
                        func_logger,
                        "error",
                        f"✗ Exception in {func_name}: {str(e)}",
                        function=func_name,
                        error_type=type(e).__name__,
                        error_message=str(e)
                    )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Misma lógica para funciones síncronas
            func_name = f"{func.__module__}.{func.__name__}"
            extras = {"function": func_name}

            if log_args:
                safe_args = _sanitize_args(args, kwargs)
                extras["args"] = safe_args

            log_with_context(func_logger, "debug", f"→ Entering {func_name}", **extras)

            try:
                result = func(*args, **kwargs)

                if log_result:
                    safe_result = _sanitize_value(result)
                    log_with_context(
                        func_logger,
                        "debug",
                        f"← Exiting {func_name}",
                        function=func_name,
                        result=safe_result
                    )
                else:
                    log_with_context(func_logger, "debug", f"← Exiting {func_name}", function=func_name)

                return result

            except Exception as e:
                if log_exceptions:
                    log_with_context(
                        func_logger,
                        "error",
                        f"✗ Exception in {func_name}: {str(e)}",
                        function=func_name,
                        error_type=type(e).__name__,
                        error_message=str(e)
                    )
                raise

        # Retornar wrapper apropiado según si es async o no
        import inspect
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator


def _sanitize_args(args: tuple, kwargs: dict) -> dict:
    """Sanitiza argumentos para no loggear información sensible."""
    sensitive_keys = {'password', 'token', 'secret', 'api_key', 'authorization'}

    sanitized = {
        "positional": [_sanitize_value(arg) for arg in args],
        "keyword": {}
    }

    for key, value in kwargs.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized["keyword"][key] = "***REDACTED***"
        else:
            sanitized["keyword"][key] = _sanitize_value(value)

    return sanitized


def _sanitize_value(value: Any, max_length: int = 200) -> Any:
    """Sanitiza un valor para logging."""
    # Si es string muy largo, truncar
    if isinstance(value, str) and len(value) > max_length:
        return value[:max_length] + "..."

    # Si es dict, sanitizar recursivamente
    if isinstance(value, dict):
        return {k: _sanitize_value(v, max_length) for k, v in value.items()}

    # Si es list, sanitizar elementos
    if isinstance(value, list):
        return [_sanitize_value(item, max_length) for item in value[:10]]  # Max 10 elementos

    # Tipos seguros
    if isinstance(value, (int, float, bool, type(None))):
        return value

    # Para objetos complejos, usar repr
    try:
        return str(value)[:max_length]
    except:
        return "<object>"


def set_request_id(request_id: Optional[str] = None) -> str:
    """
    Establece el request ID en el contexto.

    Args:
        request_id: ID de la request (si None, genera uno nuevo)

    Returns:
        El request ID establecido
    """
    if request_id is None:
        request_id = str(uuid.uuid4())

    request_id_var.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """Obtiene el request ID del contexto actual."""
    return request_id_var.get()


def clear_request_id() -> None:
    """Limpia el request ID del contexto."""
    request_id_var.set(None)
