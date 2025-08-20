# Application services package

# Repository interfaces - existing
from .i_user_repository import IUserRepository
from .i_product_repository import IProductRepository
from .i_inventario_repository import IInventarioRepository
from .i_dashboard_repository import IDashboardRepository
from .i_cliente_repository import IClienteRepository
from .i_factura_repository import IFacturaRepository
from .i_cuenta_contable_repository import ICuentaContableRepository
from .i_asiento_contable_repository import IAsientoContableRepository

# Repository interfaces - multi-tenant
from .i_tienda_repository import ITiendaRepository
from .i_local_repository import ILocalRepository
from .i_stock_local_repository import IStockLocalRepository
from .i_transferencia_repository import ITransferenciaRepository
from .i_usuario_local_repository import IUsuarioLocalRepository

# Services
from .tenant_context_service import TenantContextService
from .integracion_contable_service import IntegracionContableService

__all__ = [
    # Existing repository interfaces
    "IUserRepository",
    "IProductRepository", 
    "IInventarioRepository",
    "IDashboardRepository",
    "IClienteRepository",
    "IFacturaRepository",
    "ICuentaContableRepository",
    "IAsientoContableRepository",
    
    # Multi-tenant repository interfaces
    "ITiendaRepository",
    "ILocalRepository",
    "IStockLocalRepository", 
    "ITransferenciaRepository",
    "IUsuarioLocalRepository",
    
    # Services
    "TenantContextService",
    "IntegracionContableService",
] 