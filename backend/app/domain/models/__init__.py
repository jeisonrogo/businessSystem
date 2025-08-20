# Domain models package

# Import all domain models for SQLModel metadata creation
from .user import User, UserCreate, UserRead, UserUpdate, UserResponse, UserWithPermissions, UserWithTienda
from .product import Product, ProductCreate, ProductUpdate, ProductResponse, ProductWithStock, ProductWithTienda

# Multi-tenant models
from .tienda import Tienda, TiendaCreate, TiendaUpdate, TiendaResponse, TiendaWithLocales
from .local import Local, LocalCreate, LocalUpdate, LocalResponse, LocalWithStock, LocalWithPermisos
from .stock_local import StockLocal, StockLocalCreate, StockLocalUpdate, StockLocalResponse, StockLocalConProducto
from .transferencia import TransferenciaInventario, TransferenciaInventarioCreate, TransferenciaInventarioResponse
from .usuario_local import UsuarioLocal, UsuarioLocalCreate, UsuarioLocalUpdate, UsuarioLocalResponse
from .tenant_context import TenantContext, TenantContextResponse, ContextoDisponibleResponse

# Import existing models from other modules
try:
    from .facturacion import Cliente, Factura, DetalleFactura
except ImportError:
    # Models may not exist yet
    pass

try:
    from .contabilidad import CuentaContable, AsientoContable, DetalleAsiento
except ImportError:
    # Models may not exist yet
    pass

try:
    from .inventario import MovimientoInventario
except ImportError:
    # Models may not exist yet
    pass

__all__ = [
    # Core models
    "User", "UserCreate", "UserRead", "UserUpdate", "UserResponse", "UserWithPermissions", "UserWithTienda",
    "Product", "ProductCreate", "ProductUpdate", "ProductResponse", "ProductWithStock", "ProductWithTienda",
    
    # Multi-tenant models
    "Tienda", "TiendaCreate", "TiendaUpdate", "TiendaResponse", "TiendaWithLocales",
    "Local", "LocalCreate", "LocalUpdate", "LocalResponse", "LocalWithStock", "LocalWithPermisos",
    "StockLocal", "StockLocalCreate", "StockLocalUpdate", "StockLocalResponse", "StockLocalConProducto",
    "TransferenciaInventario", "TransferenciaInventarioCreate", "TransferenciaInventarioResponse",
    "UsuarioLocal", "UsuarioLocalCreate", "UsuarioLocalUpdate", "UsuarioLocalResponse",
    "TenantContext", "TenantContextResponse", "ContextoDisponibleResponse",
] 