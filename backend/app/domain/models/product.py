from datetime import datetime, UTC
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator
from sqlmodel import SQLModel, Field as SQLField, Column, String, Integer, DECIMAL


class Product(SQLModel, table=True):
    """
    Modelo de dominio para productos del catálogo.
    
    Reglas de negocio implementadas:
    - BR-02: SKU único que no puede ser modificado una vez creado
    - BR-01: Stock no puede ser negativo (validado en repositorio)
    """
    __tablename__ = "products"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    sku: str = SQLField(sa_column=Column(String(50), unique=True, nullable=False))
    nombre: str = SQLField(max_length=255)
    descripcion: Optional[str] = SQLField(default=None)
    url_foto: Optional[str] = SQLField(default=None, max_length=512)
    precio_base: Decimal = SQLField(sa_column=Column(DECIMAL(10, 2), nullable=False))  # Costo para el negocio
    precio_publico: Decimal = SQLField(sa_column=Column(DECIMAL(10, 2), nullable=False))  # Precio de venta
    stock: int = SQLField(default=0, ge=0)  # No puede ser negativo
    is_active: bool = SQLField(default=True)  # Para soft delete
    created_at: datetime = SQLField(default_factory=lambda: datetime.now(UTC))


# Esquemas para la API
class ProductBase(BaseModel):
    """Campos base compartidos para crear y actualizar productos."""
    sku: str = Field(..., min_length=1, max_length=50, description="Código único del producto (SKU)")
    nombre: str = Field(..., min_length=1, max_length=255, description="Nombre del producto")
    descripcion: Optional[str] = Field(None, description="Descripción detallada del producto")
    url_foto: Optional[str] = Field(None, max_length=512, description="URL de la imagen del producto")
    precio_base: Decimal = Field(..., gt=0, description="Costo del producto para el negocio")
    precio_publico: Decimal = Field(..., gt=0, description="Precio de venta al público")


class ProductCreate(ProductBase):
    """Esquema para crear un nuevo producto."""
    stock: int = Field(0, ge=0, description="Cantidad inicial en inventario")
    
    @validator('precio_publico')
    def precio_publico_mayor_que_base(cls, v, values):
        """Validar que el precio público sea mayor o igual al precio base."""
        if 'precio_base' in values and v < values['precio_base']:
            raise ValueError('El precio público debe ser mayor o igual al precio base')
        return v


class ProductUpdate(BaseModel):
    """Esquema para actualizar un producto existente."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    descripcion: Optional[str] = Field(None)
    url_foto: Optional[str] = Field(None, max_length=512)
    precio_base: Optional[Decimal] = Field(None, gt=0)
    precio_publico: Optional[Decimal] = Field(None, gt=0)
    # Nota: SKU no se puede modificar (BR-02)
    # Nota: stock se modifica a través de movimientos de inventario
    
    @validator('precio_publico')
    def precio_publico_mayor_que_base(cls, v, values):
        """Validar que el precio público sea mayor o igual al precio base."""
        if v is not None and 'precio_base' in values and values['precio_base'] is not None:
            if v < values['precio_base']:
                raise ValueError('El precio público debe ser mayor o igual al precio base')
        return v


class ProductResponse(BaseModel):
    """Esquema para respuestas de la API con información del producto."""
    id: UUID
    sku: str
    nombre: str
    descripcion: Optional[str]
    url_foto: Optional[str]
    precio_base: Decimal
    precio_publico: Decimal
    stock: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


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