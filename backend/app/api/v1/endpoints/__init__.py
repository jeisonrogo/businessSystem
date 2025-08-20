# API endpoints package

# Existing endpoints
from . import auth
from . import users
from . import products
from . import inventario
from . import dashboard
from . import clientes
from . import facturas
from . import contabilidad
from . import asientos

# Multi-tenant endpoints - temporarily disabled for middleware setup
# from . import tiendas
# from . import locales
# from . import stock_local
# from . import transferencias
# from . import usuario_locales
# from . import tenant_context

__all__ = [
    # Existing endpoints
    "auth",
    "users", 
    "products",
    "inventario",
    "dashboard",
    "clientes",
    "facturas",
    "contabilidad",
    "asientos",
    
    # Multi-tenant endpoints
    "tiendas",
    "locales",
    "stock_local",
    "transferencias",
    "usuario_locales",
    "tenant_context",
] 