"""
Modelos de dominio para el sistema contable.

Este módulo define las entidades contables principales:
- CuentaContable: Plan de cuentas de la empresa
- AsientoContable: Registro contable con fecha y descripción
- DetalleAsiento: Movimientos de débito y crédito por cuenta

Implementa los principios de contabilidad de doble partida donde:
- Cada asiento debe estar balanceado (débitos = créditos)
- Cada transacción afecta al menos dos cuentas
"""

from datetime import datetime, UTC
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator
from sqlmodel import SQLModel, Field as SQLField, Column, String, DECIMAL, Relationship


class TipoCuenta(str, Enum):
    """Tipos principales de cuentas contables."""
    ACTIVO = "ACTIVO"
    PASIVO = "PASIVO"
    PATRIMONIO = "PATRIMONIO"
    INGRESO = "INGRESO"
    EGRESO = "EGRESO"


class TipoMovimiento(str, Enum):
    """Tipo de movimiento en un detalle de asiento."""
    DEBITO = "DEBITO"
    CREDITO = "CREDITO"


class CuentaContable(SQLModel, table=True):
    """
    Modelo de dominio para el plan de cuentas.
    
    Permite organizar las cuentas en una estructura jerárquica
    con cuentas padre e hijos para mayor organización contable.
    """
    __tablename__ = "cuentas_contables"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    codigo: str = SQLField(max_length=20, unique=True, index=True, nullable=False,
                          description="Código único de la cuenta (ej: 1105)")
    nombre: str = SQLField(max_length=255, nullable=False,
                          description="Nombre descriptivo de la cuenta")
    tipo_cuenta: TipoCuenta = SQLField(nullable=False,
                                     description="Tipo de cuenta contable")
    cuenta_padre_id: Optional[UUID] = SQLField(default=None, foreign_key="cuentas_contables.id",
                                              description="ID de la cuenta padre (subcuentas)")
    is_active: bool = SQLField(default=True, description="Estado activo de la cuenta")
    created_at: datetime = SQLField(default_factory=lambda: datetime.now(UTC))
    
    # Relaciones
    subcuentas: List["CuentaContable"] = Relationship(back_populates="cuenta_padre")
    cuenta_padre: Optional["CuentaContable"] = Relationship(
        back_populates="subcuentas",
        sa_relationship_kwargs={"remote_side": "CuentaContable.id"}
    )


class AsientoContable(SQLModel, table=True):
    """
    Modelo de dominio para asientos contables.
    
    Un asiento contable es un registro de una transacción financiera
    que debe cumplir con el principio de doble partida.
    """
    __tablename__ = "asientos_contables"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    fecha: datetime = SQLField(nullable=False, description="Fecha del asiento contable")
    comprobante: Optional[str] = SQLField(max_length=50, index=True,
                                         description="Número de comprobante único")
    descripcion: str = SQLField(max_length=500, nullable=False,
                               description="Descripción del asiento contable")
    origen_tipo: Optional[str] = SQLField(max_length=50, 
                                         description="Tipo de documento origen (FACTURA, INVENTARIO, MANUAL)")
    origen_id: Optional[UUID] = SQLField(description="ID del documento origen")
    total_debito: Decimal = SQLField(sa_column=Column(DECIMAL(15, 2)), default=Decimal("0.00"))
    total_credito: Decimal = SQLField(sa_column=Column(DECIMAL(15, 2)), default=Decimal("0.00"))
    is_balanced: bool = SQLField(default=False, description="Si el asiento está balanceado")
    created_by: Optional[UUID] = SQLField(foreign_key="users.id", description="Usuario que creó el asiento")
    created_at: datetime = SQLField(default_factory=lambda: datetime.now(UTC))
    
    # Relaciones
    detalles: List["DetalleAsiento"] = Relationship(back_populates="asiento", cascade_delete=True)


class DetalleAsiento(SQLModel, table=True):
    """
    Modelo de dominio para detalles de asientos contables.
    
    Representa cada línea de un asiento contable con su cuenta,
    tipo de movimiento (débito/crédito) y monto.
    """
    __tablename__ = "detalles_asiento"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    asiento_id: UUID = SQLField(foreign_key="asientos_contables.id", nullable=False)
    cuenta_id: UUID = SQLField(foreign_key="cuentas_contables.id", nullable=False)
    tipo_movimiento: TipoMovimiento = SQLField(nullable=False)
    monto: Decimal = SQLField(sa_column=Column(DECIMAL(15, 2)), gt=0)
    descripcion: Optional[str] = SQLField(max_length=255, description="Descripción específica del movimiento")
    
    # Relaciones
    asiento: AsientoContable = Relationship(back_populates="detalles")
    cuenta: CuentaContable = Relationship()


# ==================== ESQUEMAS PYDANTIC ====================

class CuentaContableBase(BaseModel):
    """Campos base compartidos para cuentas contables."""
    codigo: str = Field(..., min_length=1, max_length=20, description="Código único de la cuenta")
    nombre: str = Field(..., min_length=1, max_length=255, description="Nombre de la cuenta")
    tipo_cuenta: TipoCuenta = Field(..., description="Tipo de cuenta")
    cuenta_padre_id: Optional[UUID] = Field(None, description="ID de la cuenta padre")


class CuentaContableCreate(CuentaContableBase):
    """Esquema para crear una nueva cuenta contable."""
    
    @field_validator('codigo')
    @classmethod
    def validar_formato_codigo(cls, v: str) -> str:
        """Validar que el código tenga formato numérico válido."""
        if not v.isdigit():
            raise ValueError('El código de cuenta debe ser numérico')
        if len(v) < 1 or len(v) > 8:
            raise ValueError('El código debe tener entre 1 y 8 dígitos')
        return v


class CuentaContableUpdate(BaseModel):
    """Esquema para actualizar una cuenta contable."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    tipo_cuenta: Optional[TipoCuenta] = Field(None)
    cuenta_padre_id: Optional[UUID] = Field(None)
    is_active: Optional[bool] = Field(None)


class CuentaContableResponse(BaseModel):
    """Esquema para respuestas de cuenta contable."""
    id: UUID
    codigo: str
    nombre: str
    tipo_cuenta: TipoCuenta
    cuenta_padre_id: Optional[UUID]
    is_active: bool
    created_at: datetime
    
    # Información adicional
    nombre_cuenta_padre: Optional[str] = None
    tiene_subcuentas: bool = False


class DetalleAsientoBase(BaseModel):
    """Campos base para detalles de asiento."""
    cuenta_id: UUID = Field(..., description="ID de la cuenta contable")
    tipo_movimiento: TipoMovimiento = Field(..., description="Tipo de movimiento")
    monto: Decimal = Field(..., gt=0, description="Monto del movimiento")
    descripcion: Optional[str] = Field(None, max_length=255, description="Descripción del movimiento")


class DetalleAsientoCreate(DetalleAsientoBase):
    """Esquema para crear detalle de asiento."""
    pass


class DetalleAsientoResponse(BaseModel):
    """Esquema para respuesta de detalle de asiento."""
    id: UUID
    cuenta_id: UUID
    tipo_movimiento: TipoMovimiento
    monto: Decimal
    descripcion: Optional[str]
    
    # Información de la cuenta
    codigo_cuenta: str
    nombre_cuenta: str


class AsientoContableBase(BaseModel):
    """Campos base para asientos contables."""
    fecha: datetime = Field(..., description="Fecha del asiento")
    comprobante: Optional[str] = Field(None, max_length=50, description="Número de comprobante único")
    descripcion: str = Field(..., min_length=1, max_length=500, description="Descripción del asiento")
    origen_tipo: Optional[str] = Field(None, max_length=50)
    origen_id: Optional[UUID] = Field(None)


class AsientoContableCreate(AsientoContableBase):
    """Esquema para crear asiento contable."""
    detalles: List[DetalleAsientoCreate] = Field(..., min_length=2, description="Al menos 2 detalles requeridos")
    
    @field_validator('detalles')
    @classmethod
    def validar_balance(cls, detalles: List[DetalleAsientoCreate]) -> List[DetalleAsientoCreate]:
        """Validar que el asiento esté balanceado (débitos = créditos)."""
        if len(detalles) < 2:
            raise ValueError('Un asiento debe tener al menos 2 detalles')
        
        total_debito = sum(
            detalle.monto for detalle in detalles 
            if detalle.tipo_movimiento == TipoMovimiento.DEBITO
        )
        total_credito = sum(
            detalle.monto for detalle in detalles 
            if detalle.tipo_movimiento == TipoMovimiento.CREDITO
        )
        
        if total_debito != total_credito:
            raise ValueError(f'El asiento no está balanceado. Débitos: {total_debito}, Créditos: {total_credito}')
        
        return detalles


class AsientoContableResponse(BaseModel):
    """Esquema para respuesta de asiento contable."""
    id: UUID
    fecha: datetime
    descripcion: str
    origen_tipo: Optional[str]
    origen_id: Optional[UUID]
    total_debito: Decimal
    total_credito: Decimal
    is_balanced: bool
    created_by: Optional[UUID]
    created_at: datetime
    detalles: List[DetalleAsientoResponse]


class AsientoContableListResponse(BaseModel):
    """Esquema para lista paginada de asientos contables."""
    asientos: List[AsientoContableResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


# ==================== ESQUEMAS AUXILIARES ====================

class PlanCuentasSeeder(BaseModel):
    """Esquema para el seeding del plan de cuentas estándar de Colombia."""
    cuentas_principales: List[dict]
    subcuentas: List[dict]


class BalanceComprobacion(BaseModel):
    """Esquema para balance de comprobación."""
    cuenta_id: UUID
    codigo_cuenta: str
    nombre_cuenta: str
    tipo_cuenta: TipoCuenta
    saldo_debito: Decimal
    saldo_credito: Decimal
    saldo_final: Decimal


class LibroDiario(BaseModel):
    """Esquema para entradas del libro diario."""
    fecha_desde: datetime
    fecha_hasta: datetime
    asientos: List[AsientoContableResponse]
    total_asientos: int


class EstadoResultados(BaseModel):
    """Esquema para estado de resultados básico."""
    periodo_desde: datetime
    periodo_hasta: datetime
    total_ingresos: Decimal
    total_egresos: Decimal
    utilidad_perdida: Decimal
    detalle_ingresos: List[dict]
    detalle_egresos: List[dict]


# ==================== CONSTANTES ====================

class CodigosCuentasEstandar:
    """Códigos estándar del plan de cuentas colombiano."""
    
    # Activos
    ACTIVO = "1"
    ACTIVO_CORRIENTE = "11"
    EFECTIVO_Y_EQUIVALENTES = "1105"
    CAJA = "110505"
    BANCOS = "111005"
    INVENTARIOS = "1435"
    
    # Pasivos
    PASIVO = "2"
    PASIVO_CORRIENTE = "21"
    CUENTAS_POR_PAGAR = "2205"
    IVA_POR_PAGAR = "244095"
    
    # Patrimonio
    PATRIMONIO = "3"
    CAPITAL = "3115"
    UTILIDADES_RETENIDAS = "3605"
    
    # Ingresos
    INGRESOS = "4"
    INGRESOS_OPERACIONALES = "41"
    VENTAS = "4135"
    
    # Egresos
    EGRESOS = "5"
    COSTO_VENTAS = "6135"
    GASTOS_OPERACIONALES = "51"


class TiposOrigen:
    """Tipos de documentos que pueden originar asientos contables."""
    FACTURA_VENTA = "FACTURA_VENTA"
    COMPRA_INVENTARIO = "COMPRA_INVENTARIO"
    AJUSTE_INVENTARIO = "AJUSTE_INVENTARIO"
    ASIENTO_MANUAL = "ASIENTO_MANUAL"
    CIERRE_PERIODO = "CIERRE_PERIODO"