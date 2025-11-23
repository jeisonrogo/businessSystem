"""
Módulo de logging infrastructure.

Exports:
- setup_logging: Configura el sistema de logging
- get_logger: Obtiene un logger configurado
- log_function_call: Decorador para logging de funciones
- log_with_context: Log con contexto adicional
- set_request_id: Establece request ID
- get_request_id: Obtiene request ID actual
"""

from .logger import (
    setup_logging,
    get_logger,
    log_function_call,
    log_with_context,
    set_request_id,
    get_request_id,
    clear_request_id
)

__all__ = [
    "setup_logging",
    "get_logger",
    "log_function_call",
    "log_with_context",
    "set_request_id",
    "get_request_id",
    "clear_request_id"
]
