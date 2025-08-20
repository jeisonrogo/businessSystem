"""
Modelo de dominio para Stock por Local en el sistema multi-tenant.

El Stock Local mantiene el inventario independiente de cada producto
en cada local específico de una tienda.
"""

from datetime import datetime, UTC
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator
from sqlmodel import SQLModel, Field as SQLField, Column, DECIMAL, Relationship


class StockLocal(SQLModel, table=True):
    """
    Modelo de dominio para Stock por Local.
    
    Maneja el inventario independiente de cada producto en cada local:
    - Cantidad disponible actual
    - Stock mínimo y máximo para alertas
    - Costo promedio ponderado por local
    - Historial de última actualización
    """
    __tablename__ = "stock_por_local"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    producto_id: UUID = SQLField(foreign_key="products.id", nullable=False, index=True,
                                description="ID del producto")
    local_id: UUID = SQLField(foreign_key="locales.id", nullable=False, index=True,
                             description="ID del local")
    
    # Cantidades de stock
    cantidad: int = SQLField(default=0, ge=0,
                           description="Cantidad actual disponible en el local")
    stock_minimo: int = SQLField(default=0, ge=0,
                               description="Cantidad mínima antes de alerta")
    stock_maximo: Optional[int] = SQLField(default=None, ge=0,
                                         description="Cantidad máxima recomendada")
    
    # Costos y valorización
    costo_promedio: Decimal = SQLField(
        sa_column=Column(DECIMAL(10, 2), nullable=False, server_default="0"),
        description="Costo promedio ponderado del producto en este local"
    )
    valor_total_inventario: Decimal = SQLField(
        sa_column=Column(DECIMAL(12, 2), nullable=False, server_default="0"),
        description="Valor total del inventario (cantidad * costo_promedio)"
    )
    
    # Control de cambios
    updated_at: datetime = SQLField(default_factory=lambda: datetime.now(UTC),
                                   description="Última actualización del stock")
    updated_by: Optional[UUID] = SQLField(foreign_key="users.id", default=None,
                                        description="Usuario que realizó la última actualización")
    
    # Relaciones
    producto: "Product" = Relationship(back_populates="stock_locales")
    local: "Local" = Relationship(back_populates="stock_productos")
    usuario_actualizacion: Optional["User"] = Relationship()
    
    # Índice único: un producto solo puede tener un registro de stock por local
    __table_args__ = (
        {"extend_existing": True},
    )

    def actualizar_stock(
        self, 
        nueva_cantidad: int, 
        nuevo_costo: Optional[Decimal] = None,
        usuario_id: Optional[UUID] = None
    ) -> None:
        """
        Actualiza el stock del producto en el local.
        
        Args:
            nueva_cantidad: Nueva cantidad de stock
            nuevo_costo: Nuevo costo unitario (opcional)
            usuario_id: ID del usuario que realiza la actualización
        """
        if nueva_cantidad < 0:
            raise ValueError("La cantidad no puede ser negativa")
        
        # Si se proporciona nuevo costo, recalcular costo promedio ponderado
        if nuevo_costo is not None and nuevo_costo > 0:
            if self.cantidad > 0:
                # Costo promedio ponderado
                valor_actual = self.cantidad * self.costo_promedio
                valor_nuevo = nueva_cantidad * nuevo_costo
                total_cantidad = self.cantidad + nueva_cantidad
                
                if total_cantidad > 0:
                    self.costo_promedio = (valor_actual + valor_nuevo) / total_cantidad
            else:
                # Si no hay stock previo, usar el nuevo costo directamente
                self.costo_promedio = nuevo_costo
        
        # Actualizar cantidad
        self.cantidad = nueva_cantidad
        
        # Recalcular valor total
        self.valor_total_inventario = self.cantidad * self.costo_promedio
        
        # Actualizar metadatos
        self.updated_at = datetime.now(UTC)
        self.updated_by = usuario_id

    def incrementar_stock(
        self, 
        cantidad_incremento: int, 
        costo_unitario: Optional[Decimal] = None,
        usuario_id: Optional[UUID] = None
    ) -> None:
        """
        Incrementa el stock actual con cálculo de costo promedio ponderado.
        
        Args:
            cantidad_incremento: Cantidad a agregar al stock
            costo_unitario: Costo del stock que se está agregando
            usuario_id: ID del usuario que realiza la operación
        """
        if cantidad_incremento <= 0:
            raise ValueError("El incremento debe ser positivo")
        
        nueva_cantidad = self.cantidad + cantidad_incremento
        self.actualizar_stock(nueva_cantidad, costo_unitario, usuario_id)

    def decrementar_stock(
        self, 
        cantidad_decremento: int,
        usuario_id: Optional[UUID] = None
    ) -> None:
        """
        Decrementa el stock actual.
        
        Args:
            cantidad_decremento: Cantidad a restar del stock
            usuario_id: ID del usuario que realiza la operación
        """
        if cantidad_decremento <= 0:
            raise ValueError("El decremento debe ser positivo")
        
        nueva_cantidad = self.cantidad - cantidad_decremento
        if nueva_cantidad < 0:
            raise ValueError(f"Stock insuficiente. Disponible: {self.cantidad}, Solicitado: {cantidad_decremento}")
        
        self.actualizar_stock(nueva_cantidad, None, usuario_id)

    def esta_bajo_minimo(self) -> bool:
        """Verifica si el stock está por debajo del mínimo."""
        return self.cantidad <= self.stock_minimo

    def esta_sobre_maximo(self) -> bool:
        """Verifica si el stock está por encima del máximo."""
        return self.stock_maximo is not None and self.cantidad >= self.stock_maximo

    def get_status_stock(self) -> str:
        """
        Retorna el estado del stock según los límites configurados.
        
        Returns:
            str: 'bajo', 'normal', 'alto', 'agotado'
        """
        if self.cantidad == 0:
            return "agotado"
        elif self.esta_bajo_minimo():
            return "bajo"
        elif self.esta_sobre_maximo():
            return "alto"
        else:
            return "normal"


# Esquemas para la API
class StockLocalBase(BaseModel):
    """Campos base para stock por local."""
    cantidad: int = Field(..., ge=0, description="Cantidad disponible")
    stock_minimo: int = Field(0, ge=0, description="Stock mínimo")
    stock_maximo: Optional[int] = Field(None, ge=0, description="Stock máximo")
    costo_promedio: Decimal = Field(Decimal("0"), ge=0, description="Costo promedio")


class StockLocalCreate(StockLocalBase):
    """Esquema para crear stock inicial en un local."""
    producto_id: UUID = Field(..., description="ID del producto")
    local_id: UUID = Field(..., description="ID del local")


class StockLocalUpdate(BaseModel):
    """Esquema para actualizar stock existente."""
    cantidad: Optional[int] = Field(None, ge=0)
    stock_minimo: Optional[int] = Field(None, ge=0)
    stock_maximo: Optional[int] = Field(None, ge=0)
    costo_promedio: Optional[Decimal] = Field(None, ge=0)


class StockLocalAjuste(BaseModel):
    """Esquema para ajustes de inventario."""
    tipo_ajuste: str = Field(..., description="Tipo: 'entrada', 'salida', 'ajuste'")
    cantidad: int = Field(..., gt=0, description="Cantidad del ajuste")
    costo_unitario: Optional[Decimal] = Field(None, ge=0, description="Costo unitario si aplica")
    motivo: str = Field(..., min_length=1, description="Motivo del ajuste")


class StockLocalResponse(BaseModel):
    """Esquema para respuestas de stock por local."""
    id: UUID
    producto_id: UUID
    local_id: UUID
    cantidad: int
    stock_minimo: int
    stock_maximo: Optional[int]
    costo_promedio: Decimal
    valor_total_inventario: Decimal
    updated_at: datetime
    updated_by: Optional[UUID]
    
    # Campos calculados
    status_stock: str = "normal"
    esta_bajo_minimo: bool = False
    esta_sobre_maximo: bool = False
    
    class Config:
        from_attributes = True


class StockLocalConProducto(StockLocalResponse):
    """Stock local con información del producto."""
    producto: "ProductResponse" = None


class StockLocalConLocal(StockLocalResponse):
    """Stock local con información del local.""" 
    local: "LocalResponse" = None


class StockLocalCompleto(StockLocalResponse):
    """Stock local con información completa de producto y local."""
    producto: "ProductResponse" = None
    local: "LocalResponse" = None


class StockLocalResumen(BaseModel):
    """Resumen de stock por local."""
    local_id: UUID
    local_nombre: str
    total_productos: int
    productos_con_stock: int
    productos_bajo_minimo: int
    productos_agotados: int
    valor_total_inventario: Decimal


class StockGlobalProducto(BaseModel):
    """Stock global de un producto en todos los locales."""
    producto_id: UUID
    producto_nombre: str
    stock_total: int
    stock_por_local: List[StockLocalResponse]
    costo_promedio_global: Decimal
    valor_total_global: Decimal


# Constantes
class TipoAjusteStock:
    """Tipos de ajuste de inventario."""
    ENTRADA = "entrada"
    SALIDA = "salida"
    AJUSTE = "ajuste"
    TRANSFERENCIA_ENTRADA = "transferencia_entrada"
    TRANSFERENCIA_SALIDA = "transferencia_salida"
    VENTA = "venta"
    DEVOLUCION = "devolucion"


class StatusStock:
    """Estados del stock."""
    AGOTADO = "agotado"
    BAJO = "bajo"
    NORMAL = "normal"
    ALTO = "alto"