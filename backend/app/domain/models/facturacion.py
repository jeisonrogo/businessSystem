"""
Modelos de dominio para el sistema de facturación.

Este módulo define las entidades principales para la facturación:
- Factura: Documento de venta principal
- DetalleFactura: Items individuales de la factura
- Cliente: Información del cliente (puede ser persona o empresa)

Implementa validaciones de negocio para:
- Cálculo automático de subtotales, IVA y totales
- Numeración consecutiva de facturas
- Validación de stock disponible
- Integración con inventario y contabilidad
"""

from datetime import datetime, UTC
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, computed_field
from sqlmodel import SQLModel, Field as SQLField, Column, DECIMAL, Relationship


class TipoCliente(str, Enum):
    """Tipo de cliente para facturación."""
    PERSONA_NATURAL = "PERSONA_NATURAL"
    EMPRESA = "EMPRESA"


class TipoDocumento(str, Enum):
    """Tipos de documento de identificación."""
    CEDULA = "CEDULA"
    NIT = "NIT"
    PASAPORTE = "PASAPORTE"
    CEDULA_EXTRANJERIA = "CEDULA_EXTRANJERIA"


class EstadoFactura(str, Enum):
    """Estados posibles de una factura."""
    BORRADOR = "BORRADOR"
    EMITIDA = "EMITIDA"
    PAGADA = "PAGADA"
    ANULADA = "ANULADA"
    VENCIDA = "VENCIDA"


class TipoFactura(str, Enum):
    """Tipos de factura según la DIAN."""
    VENTA = "VENTA"
    DEVOLUCION = "DEVOLUCION"
    NOTA_CREDITO = "NOTA_CREDITO"
    NOTA_DEBITO = "NOTA_DEBITO"


# ==================== ENTIDADES SQLMODEL ====================

class Cliente(SQLModel, table=True):
    """
    Modelo de dominio para clientes.
    
    Maneja información de clientes tanto personas naturales como empresas,
    con los campos requeridos para facturación electrónica en Colombia.
    """
    __tablename__ = "clientes"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    tipo_cliente: TipoCliente = SQLField(nullable=False, description="Tipo de cliente")
    tipo_documento: TipoDocumento = SQLField(nullable=False, description="Tipo de documento")
    numero_documento: str = SQLField(max_length=20, unique=True, index=True, nullable=False,
                                    description="Número de documento único")
    
    # Información básica
    nombre_completo: str = SQLField(max_length=255, nullable=False, 
                                   description="Nombre completo o razón social")
    email: Optional[str] = SQLField(max_length=255, description="Email del cliente")
    telefono: Optional[str] = SQLField(max_length=20, description="Teléfono de contacto")
    
    # Dirección
    direccion: Optional[str] = SQLField(max_length=255, description="Dirección completa")
    ciudad: Optional[str] = SQLField(max_length=100, description="Ciudad")
    departamento: Optional[str] = SQLField(max_length=100, description="Departamento")
    codigo_postal: Optional[str] = SQLField(max_length=10, description="Código postal")
    
    # Información adicional para empresas
    nombre_comercial: Optional[str] = SQLField(max_length=255, 
                                              description="Nombre comercial (para empresas)")
    regimen_tributario: Optional[str] = SQLField(max_length=50, 
                                                description="Régimen tributario")
    
    # Control
    is_active: bool = SQLField(default=True, description="Estado activo del cliente")
    created_at: datetime = SQLField(default_factory=lambda: datetime.now(UTC))
    updated_at: Optional[datetime] = SQLField(default=None)
    
    # Relaciones
    facturas: List["Factura"] = Relationship(back_populates="cliente")


class Factura(SQLModel, table=True):
    """
    Modelo de dominio para facturas de venta.
    
    Representa el documento principal de facturación con todos
    los campos necesarios para cumplir con la normativa colombiana.
    """
    __tablename__ = "facturas"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    
    # Numeración
    numero_factura: str = SQLField(max_length=20, unique=True, index=True, nullable=False,
                                  description="Número consecutivo único de factura")
    prefijo: Optional[str] = SQLField(max_length=10, description="Prefijo de la factura (ej: FV)")
    
    # Información del cliente
    cliente_id: UUID = SQLField(foreign_key="clientes.id", nullable=False)
    
    # Fechas
    fecha_emision: datetime = SQLField(nullable=False, description="Fecha de emisión")
    fecha_vencimiento: Optional[datetime] = SQLField(description="Fecha de vencimiento del pago")
    
    # Tipo y estado
    tipo_factura: TipoFactura = SQLField(default=TipoFactura.VENTA, 
                                        description="Tipo de factura")
    estado: EstadoFactura = SQLField(default=EstadoFactura.BORRADOR,
                                    description="Estado actual de la factura")
    
    # Totales calculados
    subtotal: Decimal = SQLField(sa_column=Column(DECIMAL(15, 2), default=0.00),
                                description="Subtotal antes de impuestos")
    total_descuento: Decimal = SQLField(sa_column=Column(DECIMAL(15, 2), default=0.00),
                                       description="Total de descuentos aplicados")
    total_impuestos: Decimal = SQLField(sa_column=Column(DECIMAL(15, 2), default=0.00),
                                       description="Total de impuestos (IVA)")
    total_factura: Decimal = SQLField(sa_column=Column(DECIMAL(15, 2), default=0.00),
                                     description="Total final de la factura")
    
    # Información adicional
    observaciones: Optional[str] = SQLField(max_length=1000, description="Observaciones de la factura")
    terminos_condiciones: Optional[str] = SQLField(max_length=1000, 
                                                  description="Términos y condiciones")
    metodo_pago: Optional[str] = SQLField(max_length=50, description="Método de pago")
    
    # Control y auditoría
    created_by: Optional[UUID] = SQLField(foreign_key="users.id", description="Usuario creador")
    created_at: datetime = SQLField(default_factory=lambda: datetime.now(UTC))
    updated_at: Optional[datetime] = SQLField(default=None)
    
    # Integración contable
    asiento_contable_id: Optional[UUID] = SQLField(foreign_key="asientos_contables.id",
                                                  description="Asiento contable generado")
    
    # Relaciones
    cliente: Cliente = Relationship(back_populates="facturas")
    detalles: List["DetalleFactura"] = Relationship(back_populates="factura", 
                                                   cascade_delete=True)


class DetalleFactura(SQLModel, table=True):
    """
    Modelo de dominio para detalles de factura.
    
    Representa cada item individual en una factura con
    cálculos automáticos de subtotales e impuestos.
    """
    __tablename__ = "detalles_factura"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    factura_id: UUID = SQLField(foreign_key="facturas.id", nullable=False)
    producto_id: UUID = SQLField(foreign_key="products.id", nullable=False)
    
    # Información del producto en el momento de la venta
    descripcion_producto: str = SQLField(max_length=255, nullable=False,
                                        description="Descripción del producto vendido")
    codigo_producto: str = SQLField(max_length=50, nullable=False,
                                   description="SKU del producto en el momento de venta")
    
    # Cantidades y precios
    cantidad: int = SQLField(gt=0, description="Cantidad vendida")
    precio_unitario: Decimal = SQLField(sa_column=Column(DECIMAL(10, 2), nullable=False),
                                       description="Precio unitario de venta")
    descuento_porcentaje: Decimal = SQLField(sa_column=Column(DECIMAL(5, 2), default=0.00),
                                            description="Porcentaje de descuento aplicado")
    descuento_valor: Decimal = SQLField(sa_column=Column(DECIMAL(10, 2), default=0.00),
                                       description="Valor del descuento aplicado")
    
    # Impuestos
    porcentaje_iva: Decimal = SQLField(sa_column=Column(DECIMAL(5, 2), default=19.00),
                                      description="Porcentaje de IVA aplicado")
    
    # Totales calculados
    subtotal_item: Decimal = SQLField(sa_column=Column(DECIMAL(15, 2), default=0.00),
                                     description="Subtotal del item (cantidad × precio)")
    valor_descuento: Decimal = SQLField(sa_column=Column(DECIMAL(15, 2), default=0.00),
                                       description="Valor total del descuento")
    base_gravable: Decimal = SQLField(sa_column=Column(DECIMAL(15, 2), default=0.00),
                                     description="Base gravable para IVA")
    valor_iva: Decimal = SQLField(sa_column=Column(DECIMAL(15, 2), default=0.00),
                                 description="Valor del IVA calculado")
    total_item: Decimal = SQLField(sa_column=Column(DECIMAL(15, 2), default=0.00),
                                  description="Total del item incluyendo IVA")
    
    # Relaciones
    factura: Factura = Relationship(back_populates="detalles")
    producto: "Product" = Relationship()


# ==================== ESQUEMAS PYDANTIC ====================

class ClienteBase(BaseModel):
    """Campos base compartidos para clientes."""
    tipo_cliente: TipoCliente = Field(..., description="Tipo de cliente")
    tipo_documento: TipoDocumento = Field(..., description="Tipo de documento")
    numero_documento: str = Field(..., min_length=5, max_length=20, description="Número de documento")
    nombre_completo: str = Field(..., min_length=2, max_length=255, description="Nombre completo")
    email: Optional[str] = Field(None, max_length=255, description="Email del cliente")
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono")
    direccion: Optional[str] = Field(None, max_length=255, description="Dirección")
    ciudad: Optional[str] = Field(None, max_length=100, description="Ciudad")
    departamento: Optional[str] = Field(None, max_length=100, description="Departamento")
    codigo_postal: Optional[str] = Field(None, max_length=10, description="Código postal")
    nombre_comercial: Optional[str] = Field(None, max_length=255, description="Nombre comercial")
    regimen_tributario: Optional[str] = Field(None, max_length=50, description="Régimen tributario")


class ClienteCreate(ClienteBase):
    """Esquema para crear un nuevo cliente."""
    
    @field_validator('numero_documento')
    @classmethod
    def validar_numero_documento(cls, v: str, info) -> str:
        """Validar formato del número de documento."""
        # Remover espacios y caracteres especiales
        v = v.replace("-", "").replace(" ", "").replace(".", "")
        
        if not v.isdigit():
            raise ValueError('El número de documento debe contener solo dígitos')
        
        # Validaciones específicas por tipo de documento
        if hasattr(info, 'data') and 'tipo_documento' in info.data:
            tipo_doc = info.data['tipo_documento']
            if tipo_doc == TipoDocumento.CEDULA and (len(v) < 7 or len(v) > 10):
                raise ValueError('La cédula debe tener entre 7 y 10 dígitos')
            elif tipo_doc == TipoDocumento.NIT and (len(v) < 9 or len(v) > 15):
                raise ValueError('El NIT debe tener entre 9 y 15 dígitos')
        
        return v

    @field_validator('email')
    @classmethod
    def validar_email(cls, v: Optional[str]) -> Optional[str]:
        """Validar formato de email."""
        if v and '@' not in v:
            raise ValueError('Email inválido')
        return v


class ClienteUpdate(BaseModel):
    """Esquema para actualizar un cliente."""
    tipo_cliente: Optional[TipoCliente] = Field(None)
    nombre_completo: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    telefono: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = Field(None, max_length=255)
    ciudad: Optional[str] = Field(None, max_length=100)
    departamento: Optional[str] = Field(None, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=10)
    nombre_comercial: Optional[str] = Field(None, max_length=255)
    regimen_tributario: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = Field(None)


class ClienteResponse(BaseModel):
    """Esquema para respuestas de cliente."""
    id: UUID
    tipo_cliente: TipoCliente
    tipo_documento: TipoDocumento
    numero_documento: str
    nombre_completo: str
    email: Optional[str]
    telefono: Optional[str]
    direccion: Optional[str]
    ciudad: Optional[str]
    departamento: Optional[str]
    codigo_postal: Optional[str]
    nombre_comercial: Optional[str]
    regimen_tributario: Optional[str]
    is_active: bool
    created_at: datetime
    
    # Información adicional
    total_facturas: int = 0
    ultima_compra: Optional[datetime] = None


class DetalleFacturaBase(BaseModel):
    """Campos base para detalles de factura."""
    producto_id: UUID = Field(..., description="ID del producto")
    cantidad: int = Field(..., gt=0, description="Cantidad a vender")
    precio_unitario: Decimal = Field(..., gt=0, description="Precio unitario de venta")
    descuento_porcentaje: Decimal = Field(default=Decimal("0.00"), ge=0, le=100,
                                         description="Porcentaje de descuento")
    porcentaje_iva: Decimal = Field(default=Decimal("19.00"), ge=0, le=100,
                                   description="Porcentaje de IVA")


class DetalleFacturaCreate(DetalleFacturaBase):
    """Esquema para crear detalle de factura."""
    pass


class DetalleFacturaResponse(BaseModel):
    """Esquema para respuesta de detalle de factura."""
    id: UUID
    producto_id: UUID
    descripcion_producto: str
    codigo_producto: str
    cantidad: int
    precio_unitario: Decimal
    descuento_porcentaje: Decimal
    descuento_valor: Decimal
    porcentaje_iva: Decimal
    subtotal_item: Decimal
    valor_descuento: Decimal
    base_gravable: Decimal
    valor_iva: Decimal
    total_item: Decimal


class FacturaBase(BaseModel):
    """Campos base para facturas."""
    cliente_id: UUID = Field(..., description="ID del cliente")
    fecha_emision: datetime = Field(default_factory=lambda: datetime.now(UTC),
                                   description="Fecha de emisión")
    fecha_vencimiento: Optional[datetime] = Field(None, description="Fecha de vencimiento")
    tipo_factura: TipoFactura = Field(default=TipoFactura.VENTA, description="Tipo de factura")
    observaciones: Optional[str] = Field(None, max_length=1000, description="Observaciones")
    terminos_condiciones: Optional[str] = Field(None, max_length=1000, 
                                               description="Términos y condiciones")
    metodo_pago: Optional[str] = Field(None, max_length=50, description="Método de pago")


class FacturaCreate(FacturaBase):
    """Esquema para crear factura."""
    detalles: List[DetalleFacturaCreate] = Field(..., min_length=1, 
                                                description="Al menos 1 detalle requerido")
    
    @field_validator('detalles')
    @classmethod
    def validar_detalles(cls, detalles: List[DetalleFacturaCreate]) -> List[DetalleFacturaCreate]:
        """Validar que hay al menos un detalle."""
        if not detalles:
            raise ValueError('La factura debe tener al menos un item')
        return detalles

    @field_validator('fecha_vencimiento')
    @classmethod
    def validar_fecha_vencimiento(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validar que la fecha de vencimiento sea posterior a la emisión."""
        if v and hasattr(info, 'data') and 'fecha_emision' in info.data:
            fecha_emision = info.data['fecha_emision']
            if v <= fecha_emision:
                raise ValueError('La fecha de vencimiento debe ser posterior a la fecha de emisión')
        return v


class FacturaUpdate(BaseModel):
    """Esquema para actualizar factura."""
    fecha_vencimiento: Optional[datetime] = Field(None)
    estado: Optional[EstadoFactura] = Field(None)
    observaciones: Optional[str] = Field(None, max_length=1000)
    terminos_condiciones: Optional[str] = Field(None, max_length=1000)
    metodo_pago: Optional[str] = Field(None, max_length=50)


class FacturaResponse(BaseModel):
    """Esquema para respuesta de factura."""
    id: UUID
    numero_factura: str
    prefijo: Optional[str]
    cliente_id: UUID
    fecha_emision: datetime
    fecha_vencimiento: Optional[datetime]
    tipo_factura: TipoFactura
    estado: EstadoFactura
    subtotal: Decimal
    total_descuento: Decimal
    total_impuestos: Decimal
    total_factura: Decimal
    observaciones: Optional[str]
    terminos_condiciones: Optional[str]
    metodo_pago: Optional[str]
    created_by: Optional[UUID]
    created_at: datetime
    asiento_contable_id: Optional[UUID]
    
    # Información del cliente
    cliente_nombre: str = ""
    cliente_documento: str = ""
    
    # Detalles
    detalles: List[DetalleFacturaResponse] = []
    cantidad_items: int = 0


class FacturaListResponse(BaseModel):
    """Esquema para lista paginada de facturas."""
    facturas: List[FacturaResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


# ==================== ESQUEMAS AUXILIARES ====================

class ResumenVentas(BaseModel):
    """Esquema para resumen de ventas."""
    periodo_desde: datetime
    periodo_hasta: datetime
    total_facturas: int
    total_ventas: Decimal
    total_impuestos: Decimal
    promedio_venta: Decimal
    facturas_por_estado: dict
    top_productos: List[dict]
    top_clientes: List[dict]


class EstadisticasFacturacion(BaseModel):
    """Esquema para estadísticas de facturación."""
    total_facturas_mes: int
    total_ventas_mes: Decimal
    crecimiento_vs_mes_anterior: Decimal
    ticket_promedio: Decimal
    facturas_vencidas: int
    valor_cartera_vencida: Decimal


class ConfiguracionFacturacion(BaseModel):
    """Esquema para configuración de facturación."""
    prefijo_factura: str = "FV"
    consecutivo_inicial: int = 1
    consecutivo_actual: int = 1
    iva_por_defecto: Decimal = Decimal("19.00")
    terminos_condiciones_default: str = ""
    dias_vencimiento_default: int = 30
    cuenta_ventas_id: Optional[UUID] = None
    cuenta_iva_id: Optional[UUID] = None
    cuenta_clientes_id: Optional[UUID] = None


# ==================== CONSTANTES ====================

class MetodosPago:
    """Métodos de pago comunes."""
    EFECTIVO = "EFECTIVO"
    TRANSFERENCIA = "TRANSFERENCIA"
    TARJETA_CREDITO = "TARJETA_CREDITO"
    TARJETA_DEBITO = "TARJETA_DEBITO"
    CHEQUE = "CHEQUE"
    CREDITO = "CREDITO"


class CodigosFacturacion:
    """Códigos de facturación electrónica DIAN."""
    TIPO_DOCUMENTO_FACTURA = "01"
    TIPO_DOCUMENTO_NOTA_CREDITO = "91"
    TIPO_DOCUMENTO_NOTA_DEBITO = "92"
    TIPO_OPERACION_STANDAR = "10"
    AMBIENTE_PRUEBAS = "2"
    AMBIENTE_PRODUCCION = "1"


# ==================== FUNCIONES AUXILIARES ====================

def calcular_totales_factura(detalles: List[DetalleFacturaCreate]) -> dict:
    """
    Calcular los totales de una factura basado en sus detalles.
    
    Returns:
        dict con subtotal, total_descuento, total_impuestos, total_factura
    """
    subtotal = Decimal("0.00")
    total_descuento = Decimal("0.00")
    total_impuestos = Decimal("0.00")
    
    for detalle in detalles:
        # Subtotal del item
        subtotal_item = Decimal(str(detalle.cantidad)) * detalle.precio_unitario
        subtotal += subtotal_item
        
        # Calcular descuento
        if detalle.descuento_porcentaje > 0:
            valor_descuento = subtotal_item * (detalle.descuento_porcentaje / 100)
            total_descuento += valor_descuento
        
        # Base gravable después del descuento
        base_gravable = subtotal_item - (total_descuento if detalle.descuento_porcentaje > 0 else Decimal("0.00"))
        
        # Calcular IVA
        if detalle.porcentaje_iva > 0:
            valor_iva = base_gravable * (detalle.porcentaje_iva / 100)
            total_impuestos += valor_iva
    
    total_factura = subtotal - total_descuento + total_impuestos
    
    return {
        "subtotal": subtotal,
        "total_descuento": total_descuento,
        "total_impuestos": total_impuestos,
        "total_factura": total_factura
    }


def generar_numero_factura(prefijo: str = "FV", consecutivo: int = 1) -> str:
    """
    Generar número de factura con formato estándar.
    
    Args:
        prefijo: Prefijo de la factura (ej: FV, NC, ND)
        consecutivo: Número consecutivo
        
    Returns:
        Número de factura formateado (ej: FV-000001)
    """
    return f"{prefijo}-{consecutivo:06d}"