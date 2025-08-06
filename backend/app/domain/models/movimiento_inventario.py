"""
Modelo de dominio para movimientos de inventario.

Este módulo define la entidad MovimientoInventario y esquemas relacionados
para el registro de entradas, salidas y mermas de productos, implementando
la lógica de costo promedio ponderado (BR-11).
"""

from datetime import datetime, UTC
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator
from sqlmodel import SQLModel, Field as SQLField, Column, String, DECIMAL, Relationship


class TipoMovimiento(str, Enum):
    """
    Tipos de movimientos de inventario permitidos.
    
    - ENTRADA: Compra a proveedores, devoluciones de clientes
    - SALIDA: Ventas a clientes, devoluciones a proveedores
    - MERMA: Pérdidas por daño, vencimiento, robo
    - AJUSTE: Ajustes por inventario físico
    """
    ENTRADA = "entrada"
    SALIDA = "salida" 
    MERMA = "merma"
    AJUSTE = "ajuste"


class MovimientoInventario(SQLModel, table=True):
    """
    Modelo de dominio para movimientos de inventario.
    
    Registra todas las entradas, salidas y mermas de productos,
    implementando la lógica de costo promedio ponderado (BR-11).
    
    Reglas de negocio implementadas:
    - BR-11: Método de costo promedio ponderado para valoración de inventario
    - BR-01: Stock no puede ser negativo (validado en servicio)
    """
    __tablename__ = "movimientos_inventario"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    producto_id: UUID = SQLField(foreign_key="products.id", nullable=False)
    tipo_movimiento: TipoMovimiento = SQLField(sa_column=Column(String(10), nullable=False))
    cantidad: int = SQLField(ge=1)  # Cantidad siempre positiva
    precio_unitario: Decimal = SQLField(sa_column=Column(DECIMAL(10, 2), nullable=False))  # Precio de compra/venta
    costo_unitario: Optional[Decimal] = SQLField(sa_column=Column(DECIMAL(10, 2), nullable=True))  # Costo promedio al momento
    stock_anterior: int = SQLField(ge=0)  # Stock antes del movimiento
    stock_posterior: int = SQLField(ge=0)  # Stock después del movimiento
    referencia: Optional[str] = SQLField(default=None, max_length=100)  # Número de factura, orden, etc.
    observaciones: Optional[str] = SQLField(default=None, max_length=500)
    created_at: datetime = SQLField(default_factory=lambda: datetime.now(UTC))
    created_by: Optional[UUID] = SQLField(default=None, nullable=True)  # Usuario que registró
    
    # Relaciones
    # producto: "Product" = Relationship(back_populates="movimientos_inventario")
    # usuario: Optional["User"] = Relationship()


# Esquemas para la API
class MovimientoInventarioBase(BaseModel):
    """Campos base compartidos para crear movimientos."""
    producto_id: UUID = Field(..., description="ID del producto")
    tipo_movimiento: TipoMovimiento = Field(..., description="Tipo de movimiento")
    cantidad: int = Field(..., gt=0, description="Cantidad del movimiento (positiva)")
    precio_unitario: Decimal = Field(..., gt=0, description="Precio unitario de compra/venta")
    referencia: Optional[str] = Field(None, max_length=100, description="Referencia (factura, orden, etc.)")
    observaciones: Optional[str] = Field(None, max_length=500, description="Observaciones adicionales")


class MovimientoInventarioCreate(MovimientoInventarioBase):
    """Esquema para crear un nuevo movimiento de inventario."""
    
    @field_validator('cantidad')
    @classmethod
    def cantidad_debe_ser_positiva(cls, v):
        """Validar que la cantidad sea positiva."""
        if v <= 0:
            raise ValueError('La cantidad debe ser mayor a cero')
        return v
    
    @field_validator('precio_unitario')
    @classmethod
    def precio_unitario_debe_ser_positivo(cls, v):
        """Validar que el precio unitario sea positivo."""
        if v <= 0:
            raise ValueError('El precio unitario debe ser mayor a cero')
        return v


class MovimientoInventarioResponse(BaseModel):
    """Esquema para respuestas de la API con información del movimiento."""
    id: UUID
    producto_id: UUID
    tipo_movimiento: TipoMovimiento
    cantidad: int
    precio_unitario: Decimal
    costo_unitario: Optional[Decimal]
    stock_anterior: int
    stock_posterior: int
    referencia: Optional[str]
    observaciones: Optional[str]
    created_at: datetime
    created_by: Optional[UUID]
    
    class Config:
        from_attributes = True
    
    @property
    def valor_total(self) -> Decimal:
        """Calcular el valor total del movimiento."""
        return Decimal(str(self.cantidad)) * self.precio_unitario


class MovimientoInventarioListResponse(BaseModel):
    """Esquema para respuestas de lista paginada de movimientos."""
    movimientos: list[MovimientoInventarioResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class KardexResponse(BaseModel):
    """Esquema para respuesta del kardex de un producto."""
    producto_id: UUID
    movimientos: list[MovimientoInventarioResponse]
    stock_actual: int
    costo_promedio_actual: Decimal
    valor_inventario: Decimal
    total_movimientos: int


class InventarioResumenResponse(BaseModel):
    """Esquema para respuesta del resumen de inventario."""
    total_productos: int
    valor_total_inventario: Decimal
    productos_sin_stock: int
    productos_stock_bajo: int
    ultimo_movimiento: Optional[datetime]


class CostoPromedioCalculation(BaseModel):
    """Esquema para el cálculo de costo promedio ponderado."""
    stock_anterior: int
    costo_anterior: Decimal
    cantidad_entrada: int
    precio_entrada: Decimal
    stock_nuevo: int
    costo_promedio_nuevo: Decimal
    
    class Config:
        from_attributes = True


# Constantes para tipos de referencia
class TipoReferencia:
    """Constantes para tipos de referencia en movimientos."""
    FACTURA_COMPRA = "FC"
    FACTURA_VENTA = "FV"
    ORDEN_COMPRA = "OC"
    DEVOLUCION = "DEV"
    AJUSTE_INVENTARIO = "AJ"
    MERMA = "MER"


# Esquemas para consultas y filtros
class MovimientoInventarioFilter(BaseModel):
    """Esquema para filtros de consulta de movimientos."""
    producto_id: Optional[UUID] = Field(None, description="Filtrar por producto")
    tipo_movimiento: Optional[TipoMovimiento] = Field(None, description="Filtrar por tipo")
    fecha_desde: Optional[datetime] = Field(None, description="Fecha desde")
    fecha_hasta: Optional[datetime] = Field(None, description="Fecha hasta")
    referencia: Optional[str] = Field(None, description="Filtrar por referencia")
    created_by: Optional[UUID] = Field(None, description="Filtrar por usuario")


class EstadisticasInventario(BaseModel):
    """Esquema para estadísticas de inventario."""
    total_entradas_mes: int
    total_salidas_mes: int
    total_mermas_mes: int
    valor_entradas_mes: Decimal
    valor_salidas_mes: Decimal
    valor_mermas_mes: Decimal
    productos_mas_movidos: list[dict]  # [{"producto_id": UUID, "nombre": str, "total_movimientos": int}]
    
    class Config:
        from_attributes = True 