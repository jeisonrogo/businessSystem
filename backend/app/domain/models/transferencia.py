"""
Modelo de dominio para Transferencias de Inventario entre Locales.

Las transferencias permiten mover stock entre locales de la misma tienda,
manteniendo un registro completo del proceso desde solicitud hasta recepción.
"""

from datetime import datetime, UTC
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator
from sqlmodel import SQLModel, Field as SQLField, Column, String, Relationship


class EstadoTransferencia(str, Enum):
    """Estados posibles de una transferencia de inventario."""
    PENDIENTE = "PENDIENTE"        # Transferencia creada, esperando envío
    ENVIADO = "ENVIADO"           # Mercancía enviada desde origen
    RECIBIDO = "RECIBIDO"         # Mercancía recibida en destino
    CANCELADO = "CANCELADO"       # Transferencia cancelada


class TransferenciaInventario(SQLModel, table=True):
    """
    Modelo de dominio para Transferencias de Inventario.
    
    Gestiona el movimiento de productos entre locales de la misma tienda:
    - Control de estados del proceso (pendiente, enviado, recibido)
    - Trazabilidad completa con usuarios responsables
    - Validaciones de negocio (misma tienda, stock disponible)
    - Auditoría completa de cantidades
    """
    __tablename__ = "transferencias_inventario"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    numero_transferencia: str = SQLField(sa_column=Column(String(50), unique=True, nullable=False),
                                       description="Número único de transferencia")
    
    # Producto y locales involucrados
    producto_id: UUID = SQLField(foreign_key="products.id", nullable=False, index=True,
                                description="ID del producto a transferir")
    local_origen_id: UUID = SQLField(foreign_key="locales.id", nullable=False, index=True,
                                   description="ID del local que envía")
    local_destino_id: UUID = SQLField(foreign_key="locales.id", nullable=False, index=True,
                                     description="ID del local que recibe")
    
    # Cantidades
    cantidad_solicitada: int = SQLField(gt=0, description="Cantidad inicialmente solicitada")
    cantidad_enviada: int = SQLField(default=0, ge=0, description="Cantidad realmente enviada")
    cantidad_recibida: int = SQLField(default=0, ge=0, description="Cantidad recibida y verificada")
    
    # Estado y control
    estado: EstadoTransferencia = SQLField(default=EstadoTransferencia.PENDIENTE,
                                         description="Estado actual de la transferencia")
    observaciones: Optional[str] = SQLField(default=None, max_length=1000,
                                          description="Observaciones generales")
    
    # Usuarios responsables en cada etapa
    usuario_solicita_id: UUID = SQLField(foreign_key="users.id", nullable=False,
                                       description="Usuario que crea la transferencia")
    usuario_envia_id: Optional[UUID] = SQLField(foreign_key="users.id", default=None,
                                               description="Usuario que confirma el envío")
    usuario_recibe_id: Optional[UUID] = SQLField(foreign_key="users.id", default=None,
                                                description="Usuario que confirma la recepción")
    
    # Fechas de control
    fecha_solicitud: datetime = SQLField(default_factory=lambda: datetime.now(UTC),
                                       description="Fecha de creación de la transferencia")
    fecha_envio: Optional[datetime] = SQLField(default=None,
                                             description="Fecha de confirmación de envío")
    fecha_recepcion: Optional[datetime] = SQLField(default=None,
                                                 description="Fecha de confirmación de recepción")
    
    # Relaciones
    producto: "Product" = Relationship()
    local_origen: "Local" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "TransferenciaInventario.local_origen_id"}
    )
    local_destino: "Local" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "TransferenciaInventario.local_destino_id"}
    )
    usuario_solicita: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "TransferenciaInventario.usuario_solicita_id"}
    )
    usuario_envia: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "TransferenciaInventario.usuario_envia_id"}
    )
    usuario_recibe: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "TransferenciaInventario.usuario_recibe_id"}
    )
    movimientos_inventario: list["MovimientoInventario"] = Relationship(back_populates="transferencia")

    def confirmar_envio(
        self, 
        cantidad_enviada: int, 
        usuario_envia_id: UUID,
        observaciones_envio: Optional[str] = None
    ) -> None:
        """
        Confirma el envío de la transferencia desde el local origen.
        
        Args:
            cantidad_enviada: Cantidad realmente enviada
            usuario_envia_id: ID del usuario que confirma el envío
            observaciones_envio: Observaciones adicionales del envío
        """
        if self.estado != EstadoTransferencia.PENDIENTE:
            raise ValueError(f"No se puede enviar transferencia en estado {self.estado}")
        
        if cantidad_enviada <= 0:
            raise ValueError("La cantidad enviada debe ser mayor a cero")
        
        if cantidad_enviada > self.cantidad_solicitada:
            raise ValueError("No se puede enviar más cantidad de la solicitada")
        
        self.cantidad_enviada = cantidad_enviada
        self.estado = EstadoTransferencia.ENVIADO
        self.usuario_envia_id = usuario_envia_id
        self.fecha_envio = datetime.now(UTC)
        
        if observaciones_envio:
            self.observaciones = f"{self.observaciones or ''}\nEnvío: {observaciones_envio}".strip()

    def confirmar_recepcion(
        self, 
        cantidad_recibida: int, 
        usuario_recibe_id: UUID,
        observaciones_recepcion: Optional[str] = None
    ) -> None:
        """
        Confirma la recepción de la transferencia en el local destino.
        
        Args:
            cantidad_recibida: Cantidad realmente recibida
            usuario_recibe_id: ID del usuario que confirma la recepción
            observaciones_recepcion: Observaciones de la recepción
        """
        if self.estado != EstadoTransferencia.ENVIADO:
            raise ValueError(f"No se puede recibir transferencia en estado {self.estado}")
        
        if cantidad_recibida < 0:
            raise ValueError("La cantidad recibida no puede ser negativa")
        
        if cantidad_recibida > self.cantidad_enviada:
            raise ValueError("No se puede recibir más cantidad de la enviada")
        
        self.cantidad_recibida = cantidad_recibida
        self.estado = EstadoTransferencia.RECIBIDO
        self.usuario_recibe_id = usuario_recibe_id
        self.fecha_recepcion = datetime.now(UTC)
        
        if observaciones_recepcion:
            self.observaciones = f"{self.observaciones or ''}\nRecepción: {observaciones_recepcion}".strip()

    def cancelar_transferencia(
        self, 
        usuario_id: UUID, 
        motivo_cancelacion: str
    ) -> None:
        """
        Cancela la transferencia si está en estado válido.
        
        Args:
            usuario_id: ID del usuario que cancela
            motivo_cancelacion: Motivo de la cancelación
        """
        if self.estado in [EstadoTransferencia.RECIBIDO, EstadoTransferencia.CANCELADO]:
            raise ValueError(f"No se puede cancelar transferencia en estado {self.estado}")
        
        self.estado = EstadoTransferencia.CANCELADO
        self.observaciones = f"{self.observaciones or ''}\nCancelación: {motivo_cancelacion}".strip()

    def calcular_diferencia(self) -> int:
        """
        Calcula la diferencia entre enviado y recibido.
        
        Returns:
            int: Diferencia (positivo = faltante, negativo = sobrante)
        """
        if self.estado != EstadoTransferencia.RECIBIDO:
            return 0
        return self.cantidad_enviada - self.cantidad_recibida

    def tiene_diferencia(self) -> bool:
        """Verifica si hay diferencia entre enviado y recibido."""
        return self.calcular_diferencia() != 0

    @staticmethod
    def generar_numero_transferencia(tienda_codigo: str, secuencia: int) -> str:
        """
        Genera un número único de transferencia.
        
        Args:
            tienda_codigo: Código de la tienda
            secuencia: Número secuencial
            
        Returns:
            str: Número de transferencia formateado
        """
        return f"TRF-{tienda_codigo}-{secuencia:04d}"


# Esquemas para la API
class TransferenciaInventarioBase(BaseModel):
    """Campos base para transferencias."""
    producto_id: UUID = Field(..., description="ID del producto a transferir")
    local_destino_id: UUID = Field(..., description="ID del local de destino")
    cantidad_solicitada: int = Field(..., gt=0, description="Cantidad a transferir")
    observaciones: Optional[str] = Field(None, max_length=1000, description="Observaciones")


class TransferenciaInventarioCreate(TransferenciaInventarioBase):
    """Esquema para crear una nueva transferencia."""
    local_origen_id: UUID = Field(..., description="ID del local de origen")
    
    @field_validator('cantidad_solicitada')
    @classmethod
    def validar_cantidad_positiva(cls, v: int) -> int:
        if v <= 0:
            raise ValueError('La cantidad debe ser mayor a cero')
        return v


class TransferenciaInventarioUpdate(BaseModel):
    """Esquema para actualizar transferencia (solo observaciones)."""
    observaciones: Optional[str] = Field(None, max_length=1000)


class TransferenciaEnvioRequest(BaseModel):
    """Esquema para confirmar envío de transferencia."""
    cantidad_enviada: int = Field(..., gt=0, description="Cantidad realmente enviada")
    observaciones_envio: Optional[str] = Field(None, max_length=500, description="Observaciones del envío")


class TransferenciaRecepcionRequest(BaseModel):
    """Esquema para confirmar recepción de transferencia."""
    cantidad_recibida: int = Field(..., ge=0, description="Cantidad realmente recibida")
    observaciones_recepcion: Optional[str] = Field(None, max_length=500, description="Observaciones de la recepción")


class TransferenciaCancelacionRequest(BaseModel):
    """Esquema para cancelar transferencia."""
    motivo_cancelacion: str = Field(..., min_length=1, max_length=500, description="Motivo de la cancelación")


class TransferenciaInventarioResponse(BaseModel):
    """Esquema para respuestas de transferencias."""
    id: UUID
    numero_transferencia: str
    producto_id: UUID
    local_origen_id: UUID
    local_destino_id: UUID
    cantidad_solicitada: int
    cantidad_enviada: int
    cantidad_recibida: int
    estado: EstadoTransferencia
    observaciones: Optional[str]
    usuario_solicita_id: UUID
    usuario_envia_id: Optional[UUID]
    usuario_recibe_id: Optional[UUID]
    fecha_solicitud: datetime
    fecha_envio: Optional[datetime]
    fecha_recepcion: Optional[datetime]
    
    # Campos calculados
    diferencia: int = 0
    tiene_diferencia: bool = False
    
    class Config:
        from_attributes = True


class TransferenciaConDetalles(TransferenciaInventarioResponse):
    """Transferencia con detalles de producto y locales."""
    producto: "ProductResponse" = None
    local_origen: "LocalResponse" = None
    local_destino: "LocalResponse" = None
    usuario_solicita: "UserResponse" = None
    usuario_envia: Optional["UserResponse"] = None
    usuario_recibe: Optional["UserResponse"] = None


class TransferenciaListResponse(BaseModel):
    """Esquema para respuestas de lista paginada de transferencias."""
    transferencias: list[TransferenciaInventarioResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class TransferenciaResumenPorLocal(BaseModel):
    """Resumen de transferencias por local."""
    local_id: UUID
    local_nombre: str
    transferencias_enviadas: int
    transferencias_recibidas: int
    transferencias_pendientes: int
    cantidad_total_enviada: int
    cantidad_total_recibida: int


# Constantes
class TipoMovimientoTransferencia:
    """Tipos de movimiento relacionados con transferencias."""
    SALIDA_TRANSFERENCIA = "salida_transferencia"
    ENTRADA_TRANSFERENCIA = "entrada_transferencia"
    AJUSTE_DIFERENCIA_TRANSFERENCIA = "ajuste_diferencia_transferencia"