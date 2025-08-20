# Infrastructure repositories package

# Existing repositories
from .user_repository import UserRepository
from .product_repository import ProductRepository
from .inventario_repository import InventarioRepository
from .dashboard_repository import DashboardRepository
from .cliente_repository import ClienteRepository
from .factura_repository import FacturaRepository
from .cuenta_contable_repository import CuentaContableRepository
from .asiento_contable_repository import AsientoContableRepository

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