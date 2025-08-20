# Infrastructure repositories package

# Existing repositories - aliasing SQL* classes for backward compatibility
from .user_repository import SQLUserRepository as UserRepository
from .product_repository import SQLProductRepository as ProductRepository
from .inventario_repository import SQLInventarioRepository as InventarioRepository
from .dashboard_repository import SQLDashboardRepository as DashboardRepository
from .cliente_repository import SQLClienteRepository as ClienteRepository
from .factura_repository import SQLFacturaRepository as FacturaRepository
from .cuenta_contable_repository import SQLCuentaContableRepository as CuentaContableRepository
from .asiento_contable_repository import SQLAsientoContableRepository as AsientoContableRepository

# Multi-tenant repositories
from .tienda_repository import TiendaRepository
from .local_repository import LocalRepository
from .stock_local_repository import StockLocalRepository
from .transferencia_repository import TransferenciaRepository
from .usuario_local_repository import UsuarioLocalRepository

__all__ = [
    # Existing repositories
    "UserRepository",
    "ProductRepository",
    "InventarioRepository", 
    "DashboardRepository",
    "ClienteRepository",
    "FacturaRepository",
    "CuentaContableRepository",
    "AsientoContableRepository",
    
    # Multi-tenant repositories
    "TiendaRepository",
    "LocalRepository",
    "StockLocalRepository",
    "TransferenciaRepository", 
    "UsuarioLocalRepository",
] 