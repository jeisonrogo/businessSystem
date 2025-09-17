from datetime import datetime, UTC
from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator
from sqlmodel import SQLModel, Field as SQLField, Column, String, Integer, DECIMAL, Relationship


class Product(SQLModel, table=True):
    """
    Modelo de dominio para productos del catálogo multi-tenant.
    
    Reglas de negocio implementadas:
    - BR-02: SKU único que no puede ser modificado una vez creado
    - BR-01: Stock no puede ser negativo (validado en repositorio)
    - Multi-tenant: Productos pertenecen a una tienda específica
    - Stock se maneja independientemente por local (tabla stock_por_local)
    """
    __tablename__ = "products"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    sku: str = SQLField(sa_column=Column(String(50), unique=True, nullable=False))
    nombre: str = SQLField(max_length=255)
    descripcion: Optional[str] = SQLField(default=None)
    imagen_path: Optional[str] = SQLField(default=None, max_length=512, description="Ruta relativa a la imagen del producto")
    precio_base: Decimal = SQLField(sa_column=Column(DECIMAL(10, 2), nullable=False))  # Costo para el negocio
    precio_publico: Decimal = SQLField(sa_column=Column(DECIMAL(10, 2), nullable=False))  # Precio de venta
    
    # Relaciones multi-tenant
    tienda_id: UUID = SQLField(foreign_key="tiendas.id", nullable=False, index=True,
                              description="ID de la tienda a la que pertenece el producto")
    
    # NOTA: El campo 'stock' se eliminó porque ahora se maneja por local en la tabla stock_por_local
    
    # Campos de control
    is_active: bool = SQLField(default=True)  # Para soft delete
    created_at: datetime = SQLField(default_factory=lambda: datetime.now(UTC))
    updated_at: Optional[datetime] = SQLField(default=None)
    
    # Campos calculados multi-tenant (no se persisten en DB, se calculan dinámicamente)
    # Estos campos se agregan dinámicamente en los endpoints según el contexto del usuario
    
    # Relaciones
    tienda: "Tienda" = Relationship(back_populates="productos")
    stock_locales: List["StockLocal"] = Relationship(back_populates="producto", cascade_delete=True)
    transferencias: List["TransferenciaInventario"] = Relationship(back_populates="producto")
    
    # Relaciones con otros módulos (se actualizarán más adelante)
    # movimientos_inventario: List["MovimientoInventario"] = Relationship(back_populates="producto")
    # detalles_factura: List["DetalleFactura"] = Relationship(back_populates="producto")
    
    def get_stock_total_tienda(self) -> int:
        """
        Calcula el stock total del producto en todos los locales de su tienda.
        
        Returns:
            int: Stock total consolidado
        """
        return sum(stock.cantidad for stock in self.stock_locales)
    
    def get_stock_en_local(self, local_id: UUID) -> int:
        """
        Obtiene el stock del producto en un local específico.
        
        Args:
            local_id: ID del local
            
        Returns:
            int: Stock en el local o 0 si no existe
        """
        for stock in self.stock_locales:
            if stock.local_id == local_id:
                return stock.cantidad
        return 0
    
    def get_stock_local_object(self, local_id: UUID) -> Optional["StockLocal"]:
        """
        Obtiene el objeto StockLocal para un local específico.
        
        Args:
            local_id: ID del local
            
        Returns:
            StockLocal o None si no existe
        """
        for stock in self.stock_locales:
            if stock.local_id == local_id:
                return stock
        return None
    
    def esta_disponible_en_local(self, local_id: UUID, cantidad: int = 1) -> bool:
        """
        Verifica si hay suficiente stock disponible en un local.
        
        Args:
            local_id: ID del local
            cantidad: Cantidad requerida
            
        Returns:
            bool: True si hay stock suficiente
        """
        stock_disponible = self.get_stock_en_local(local_id)
        return stock_disponible >= cantidad
    
    def get_locales_con_stock(self) -> List[UUID]:
        """
        Retorna lista de locales que tienen stock del producto.
        
        Returns:
            List[UUID]: IDs de locales con stock > 0
        """
        return [
            stock.local_id 
            for stock in self.stock_locales 
            if stock.cantidad > 0
        ]
    
    def get_valor_total_inventario(self) -> Decimal:
        """
        Calcula el valor total del inventario del producto en todos los locales.
        
        Returns:
            Decimal: Valor total del inventario
        """
        return sum(stock.valor_total_inventario for stock in self.stock_locales)
    
    def get_imagen_url(self, base_url: str = "") -> Optional[str]:
        """
        Obtiene la URL completa para acceder a la imagen del producto.
        
        Args:
            base_url: URL base del servidor
            
        Returns:
            URL completa de la imagen o None si no tiene imagen
        """
        if not self.imagen_path:
            return None
        return f"{base_url.rstrip('/')}/uploads/{self.imagen_path}"
    
    def actualizar_timestamp(self) -> None:
        """Actualiza el timestamp de modificación."""
        self.updated_at = datetime.now(UTC)


# Esquemas para la API
class ProductBase(BaseModel):
    """Campos base compartidos para crear y actualizar productos multi-tenant."""
    sku: str = Field(..., min_length=1, max_length=50, description="Código único del producto (SKU)")
    nombre: str = Field(..., min_length=1, max_length=255, description="Nombre del producto")
    descripcion: Optional[str] = Field(None, description="Descripción detallada del producto")
    imagen_path: Optional[str] = Field(None, max_length=512, description="Ruta relativa a la imagen del producto")
    precio_base: Decimal = Field(..., gt=0, description="Costo del producto para el negocio")
    precio_publico: Decimal = Field(..., gt=0, description="Precio de venta al público")


class ProductCreate(ProductBase):
    """Esquema para crear un nuevo producto multi-tenant."""
    tienda_id: UUID = Field(..., description="ID de la tienda a la que pertenece el producto")
    stock_inicial: Optional[int] = Field(0, ge=0, description="Stock inicial para distribución en locales")
    
    @field_validator('precio_publico')
    @classmethod
    def precio_publico_mayor_que_base(cls, v, info):
        """Validar que el precio público sea mayor o igual al precio base."""
        if hasattr(info, 'data') and 'precio_base' in info.data and v < info.data['precio_base']:
            raise ValueError('El precio público debe ser mayor o igual al precio base')
        return v


class ProductUpdate(BaseModel):
    """Esquema para actualizar un producto existente."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    descripcion: Optional[str] = Field(None)
    imagen_path: Optional[str] = Field(None, max_length=512)
    precio_base: Optional[Decimal] = Field(None, gt=0)
    precio_publico: Optional[Decimal] = Field(None, gt=0)
    # Nota: SKU no se puede modificar (BR-02)
    # Nota: stock se modifica a través de movimientos de inventario
    
    @field_validator('precio_publico')
    @classmethod
    def precio_publico_mayor_que_base(cls, v, info):
        """Validar que el precio público sea mayor o igual al precio base."""
        if v is not None and hasattr(info, 'data') and 'precio_base' in info.data and info.data['precio_base'] is not None:
            if v < info.data['precio_base']:
                raise ValueError('El precio público debe ser mayor o igual al precio base')
        return v


class ProductResponse(BaseModel):
    """Esquema para respuestas de la API con información del producto multi-tenant."""
    id: UUID
    sku: str
    nombre: str
    descripcion: Optional[str]
    imagen_path: Optional[str]
    imagen_url: Optional[str] = None  # URL completa calculada dinámicamente
    precio_base: Decimal
    precio_publico: Decimal
    tienda_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Campos calculados (se llenan desde los métodos del modelo)
    stock_local_actual: int = 0  # Stock en el local actual del usuario
    stock_total_tienda: int = 0
    valor_total_inventario: Decimal = Decimal("0.00")
    locales_con_stock: List[UUID] = []
    
    # Campos adicionales para contexto local-específico
    costo_promedio_local: Optional[Decimal] = Decimal("0.00")
    local_id: Optional[str] = None
    local_nombre: Optional[str] = None
    locales_stock: List[dict] = []  # Para vista de todos los locales
    
    class Config:
        from_attributes = True


class ProductWithStock(ProductResponse):
    """Producto con información detallada de stock por local."""
    stock_locales: List["StockLocalResponse"] = []
    
    
class ProductWithTienda(ProductResponse):
    """Producto con información de su tienda."""
    tienda: Optional["TiendaResponse"] = None


class ProductListResponse(BaseModel):
    """Esquema para respuestas de lista paginada de productos."""
    products: list[ProductResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


# Constantes para tipos de productos (si se necesitan en el futuro)
class ProductStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued" 