"""
Esquemas Pydantic para las entidades multi-tenant.

Define los modelos de datos de entrada y salida para los endpoints
de tiendas, locales, stock por local, transferencias y permisos de usuario.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, validator


# Enums para validación
class EstadoTransferenciaEnum(str, Enum):
    PENDIENTE = "PENDIENTE"
    ENVIADO = "ENVIADO"
    RECIBIDO = "RECIBIDO"
    CANCELADO = "CANCELADO"


class PerfilPermisoEnum(str, Enum):
    VENDEDOR = "VENDEDOR"
    RESPONSABLE_LOCAL = "RESPONSABLE_LOCAL"
    GERENTE_VENTAS = "GERENTE_VENTAS"
    CONTADOR = "CONTADOR"
    ADMINISTRADOR = "ADMINISTRADOR"


# ============ ESQUEMAS DE TIENDA ============

class TiendaBase(BaseModel):
    """Esquema base para Tienda."""
    codigo: str = Field(..., min_length=2, max_length=20, description="Código único de la tienda")
    nombre: str = Field(..., min_length=3, max_length=255, description="Nombre de la tienda")
    descripcion: Optional[str] = Field(None, description="Descripción de la tienda")
    dominio: Optional[str] = Field(None, max_length=100, description="Dominio para multi-tenancy")
    configuracion: Optional[Dict[str, Any]] = Field(None, description="Configuración JSON de la tienda")
    prefijo_facturas: str = Field(default="F", max_length=10, description="Prefijo para numeración de facturas")


class TiendaCreate(TiendaBase):
    """Esquema para crear una tienda."""
    consecutivo_facturas: int = Field(default=1, ge=1, description="Número inicial de consecutivo de facturas")


class TiendaUpdate(BaseModel):
    """Esquema para actualizar una tienda."""
    codigo: Optional[str] = Field(None, min_length=2, max_length=20)
    nombre: Optional[str] = Field(None, min_length=3, max_length=255)
    descripcion: Optional[str] = Field(None)
    dominio: Optional[str] = Field(None, max_length=100)
    configuracion: Optional[Dict[str, Any]] = Field(None)
    prefijo_facturas: Optional[str] = Field(None, max_length=10)
    is_active: Optional[bool] = Field(None)


class TiendaResponse(TiendaBase):
    """Esquema para respuesta de tienda."""
    id: UUID = Field(..., description="ID único de la tienda")
    consecutivo_facturas: int = Field(..., description="Consecutivo actual de facturas")
    is_active: bool = Field(..., description="Estado activo de la tienda")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")
    
    # Campo calculado dinámicamente en los endpoints
    total_locales: int = Field(default=0, description="Número total de locales de la tienda")

    class Config:
        from_attributes = True


class TiendaEstadisticas(BaseModel):
    """Esquema para estadísticas de tienda."""
    tienda_id: UUID = Field(..., description="ID de la tienda")
    total_locales: int = Field(..., description="Total de locales")
    locales_activos: int = Field(..., description="Locales activos")
    total_productos: int = Field(..., description="Total de productos")
    total_usuarios: int = Field(..., description="Total de usuarios")


# ============ ESQUEMAS DE LOCAL ============

class LocalBase(BaseModel):
    """Esquema base para Local."""
    codigo: str = Field(..., min_length=2, max_length=20, description="Código del local")
    nombre: str = Field(..., min_length=3, max_length=255, description="Nombre del local")
    direccion: Optional[str] = Field(None, max_length=500, description="Dirección del local")
    ciudad: Optional[str] = Field(None, max_length=100, description="Ciudad")
    departamento: Optional[str] = Field(None, max_length=100, description="Departamento/Estado")
    codigo_postal: Optional[str] = Field(None, max_length=10, description="Código postal")
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono de contacto")
    email: Optional[str] = Field(None, max_length=255, description="Email de contacto")
    configuracion: Optional[Dict[str, Any]] = Field(None, description="Configuración JSON del local")


class LocalCreate(LocalBase):
    """Esquema para crear un local."""
    tienda_id: UUID = Field(..., description="ID de la tienda propietaria")


class LocalUpdate(BaseModel):
    """Esquema para actualizar un local."""
    codigo: Optional[str] = Field(None, min_length=2, max_length=20)
    nombre: Optional[str] = Field(None, min_length=3, max_length=255)
    direccion: Optional[str] = Field(None, max_length=500)
    ciudad: Optional[str] = Field(None, max_length=100)
    departamento: Optional[str] = Field(None, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=10)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    configuracion: Optional[Dict[str, Any]] = Field(None)
    is_active: Optional[bool] = Field(None)


class LocalResponse(LocalBase):
    """Esquema para respuesta de local."""
    id: UUID = Field(..., description="ID único del local")
    tienda_id: UUID = Field(..., description="ID de la tienda")
    is_active: bool = Field(..., description="Estado activo del local")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")
    
    # Estadísticas del local
    total_productos: Optional[int] = Field(0, description="Total de productos con stock en el local")
    valor_inventario: Optional[float] = Field(0, description="Valor total del inventario en el local")

    class Config:
        from_attributes = True


class LocalEstadisticas(BaseModel):
    """Esquema para estadísticas de local."""
    local_id: UUID = Field(..., description="ID del local")
    total_productos: int = Field(..., description="Total de productos con stock")
    total_stock: int = Field(..., description="Stock total en el local")
    valor_inventario: Decimal = Field(..., description="Valor total del inventario")
    productos_bajo_minimo: int = Field(..., description="Productos bajo stock mínimo")
    total_usuarios: int = Field(..., description="Usuarios con permisos en el local")
    transferencias_pendientes: int = Field(..., description="Transferencias pendientes")


# ============ ESQUEMAS DE STOCK LOCAL ============

class StockLocalBase(BaseModel):
    """Esquema base para StockLocal."""
    cantidad: int = Field(..., ge=0, description="Cantidad en stock")
    stock_minimo: int = Field(..., ge=0, description="Stock mínimo requerido")
    stock_maximo: Optional[int] = Field(None, ge=0, description="Stock máximo permitido")
    costo_promedio: Decimal = Field(..., ge=0, description="Costo promedio ponderado")


class StockLocalCreate(StockLocalBase):
    """Esquema para crear stock en local."""
    producto_id: UUID = Field(..., description="ID del producto")
    local_id: UUID = Field(..., description="ID del local")


class StockLocalUpdate(BaseModel):
    """Esquema para actualizar configuración de stock."""
    stock_minimo: Optional[int] = Field(None, ge=0)
    stock_maximo: Optional[int] = Field(None, ge=0)
    
    @validator('stock_maximo')
    def validar_stock_maximo(cls, v, values):
        if v is not None and 'stock_minimo' in values and values['stock_minimo'] is not None:
            if v < values['stock_minimo']:
                raise ValueError('Stock máximo debe ser mayor al mínimo')
        return v


class StockLocalAjuste(BaseModel):
    """Esquema para ajustar stock (operaciones manuales)."""
    nueva_cantidad: int = Field(..., ge=0, description="Nueva cantidad de stock")
    nuevo_costo: Optional[Decimal] = Field(None, ge=0, description="Nuevo costo (opcional)")
    motivo: str = Field(..., min_length=5, description="Motivo del ajuste")


class StockLocalResponse(StockLocalBase):
    """Esquema para respuesta de stock local."""
    id: UUID = Field(..., description="ID único del registro")
    producto_id: UUID = Field(..., description="ID del producto")
    local_id: UUID = Field(..., description="ID del local")
    valor_total_inventario: Decimal = Field(..., description="Valor total del inventario")
    updated_at: datetime = Field(..., description="Fecha de última actualización")
    updated_by: Optional[UUID] = Field(None, description="Usuario que realizó la última actualización")

    class Config:
        from_attributes = True


class StockLocalResumen(BaseModel):
    """Esquema para resumen de inventario por local."""
    local_id: UUID = Field(..., description="ID del local")
    total_productos: int = Field(..., description="Total de productos")
    productos_con_stock: int = Field(..., description="Productos con stock > 0")
    productos_bajo_minimo: int = Field(..., description="Productos bajo mínimo")
    productos_agotados: int = Field(..., description="Productos agotados")
    valor_total_inventario: Decimal = Field(..., description="Valor total del inventario")


# ============ ESQUEMAS DE TRANSFERENCIA ============

class TransferenciaBase(BaseModel):
    """Esquema base para Transferencia."""
    producto_id: UUID = Field(..., description="ID del producto a transferir")
    local_origen_id: UUID = Field(..., description="ID del local origen")
    local_destino_id: UUID = Field(..., description="ID del local destino")
    cantidad_solicitada: int = Field(..., gt=0, description="Cantidad solicitada")
    observaciones: Optional[str] = Field(None, max_length=1000, description="Observaciones")


class TransferenciaCreate(TransferenciaBase):
    """Esquema para crear transferencia."""
    usuario_solicita_id: UUID = Field(..., description="Usuario que solicita la transferencia")


class TransferenciaEnvio(BaseModel):
    """Esquema para marcar transferencia como enviada."""
    cantidad_enviada: int = Field(..., gt=0, description="Cantidad efectivamente enviada")
    observaciones: Optional[str] = Field(None, max_length=1000, description="Observaciones del envío")


class TransferenciaRecepcion(BaseModel):
    """Esquema para marcar transferencia como recibida."""
    cantidad_recibida: int = Field(..., gt=0, description="Cantidad efectivamente recibida")
    observaciones: Optional[str] = Field(None, max_length=1000, description="Observaciones de la recepción")


class TransferenciaCancelacion(BaseModel):
    """Esquema para cancelar transferencia."""
    motivo_cancelacion: str = Field(..., min_length=10, description="Motivo de la cancelación")


class TransferenciaResponse(TransferenciaBase):
    """Esquema para respuesta de transferencia."""
    id: UUID = Field(..., description="ID único de la transferencia")
    numero_transferencia: str = Field(..., description="Número único de transferencia")
    cantidad_enviada: int = Field(..., description="Cantidad enviada")
    cantidad_recibida: int = Field(..., description="Cantidad recibida")
    estado: EstadoTransferenciaEnum = Field(..., description="Estado actual")
    usuario_solicita_id: UUID = Field(..., description="Usuario que solicitó")
    usuario_envia_id: Optional[UUID] = Field(None, description="Usuario que envió")
    usuario_recibe_id: Optional[UUID] = Field(None, description="Usuario que recibió")
    fecha_solicitud: datetime = Field(..., description="Fecha de solicitud")
    fecha_envio: Optional[datetime] = Field(None, description="Fecha de envío")
    fecha_recepcion: Optional[datetime] = Field(None, description="Fecha de recepción")

    class Config:
        from_attributes = True


class TransferenciaEstadisticas(BaseModel):
    """Esquema para estadísticas de transferencias."""
    tienda_id: UUID = Field(..., description="ID de la tienda")
    total_transferencias: int = Field(..., description="Total de transferencias")
    transferencias_por_estado: Dict[str, int] = Field(..., description="Conteo por estado")
    transferencias_por_local: Dict[str, int] = Field(..., description="Conteo por local")
    productos_mas_transferidos: List[Dict[str, Any]] = Field(..., description="Top productos")
    tiempo_promedio_procesamiento: float = Field(..., description="Tiempo promedio en horas")


# ============ ESQUEMAS DE USUARIO LOCAL ============

class UsuarioLocalBase(BaseModel):
    """Esquema base para UsuarioLocal."""
    puede_vender: bool = Field(default=False, description="Puede realizar ventas")
    puede_ver_stock: bool = Field(default=True, description="Puede ver stock")
    puede_transferir: bool = Field(default=False, description="Puede hacer transferencias")
    es_responsable: bool = Field(default=False, description="Es responsable del local")
    puede_modificar_precios: bool = Field(default=False, description="Puede modificar precios")
    puede_aplicar_descuentos: bool = Field(default=False, description="Puede aplicar descuentos")
    puede_ver_reportes: bool = Field(default=False, description="Puede ver reportes")
    puede_gestionar_usuarios: bool = Field(default=False, description="Puede gestionar usuarios")
    limite_descuento_porcentaje: Optional[float] = Field(None, ge=0, le=100, description="Límite de descuento %")
    limite_credito_monto: Optional[float] = Field(None, ge=0, description="Límite de crédito")


class UsuarioLocalCreate(UsuarioLocalBase):
    """Esquema para crear permisos usuario-local."""
    user_id: UUID = Field(..., description="ID del usuario")
    local_id: UUID = Field(..., description="ID del local")


class UsuarioLocalUpdate(BaseModel):
    """Esquema para actualizar permisos."""
    puede_vender: Optional[bool] = Field(None)
    puede_ver_stock: Optional[bool] = Field(None)
    puede_transferir: Optional[bool] = Field(None)
    es_responsable: Optional[bool] = Field(None)
    puede_modificar_precios: Optional[bool] = Field(None)
    puede_aplicar_descuentos: Optional[bool] = Field(None)
    puede_ver_reportes: Optional[bool] = Field(None)
    puede_gestionar_usuarios: Optional[bool] = Field(None)
    limite_descuento_porcentaje: Optional[float] = Field(None, ge=0, le=100)
    limite_credito_monto: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = Field(None)


class UsuarioLocalAsignarPerfil(BaseModel):
    """Esquema para asignar perfil de permisos."""
    user_id: UUID = Field(..., description="ID del usuario")
    local_id: UUID = Field(..., description="ID del local")
    perfil: PerfilPermisoEnum = Field(..., description="Perfil de permisos a asignar")


class UsuarioLocalResponse(UsuarioLocalBase):
    """Esquema para respuesta de permisos usuario-local."""
    id: UUID = Field(..., description="ID único de la asignación")
    user_id: UUID = Field(..., description="ID del usuario")
    local_id: UUID = Field(..., description="ID del local")
    is_active: bool = Field(..., description="Estado activo de la asignación")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")
    created_by: Optional[UUID] = Field(None, description="Usuario que creó la asignación")

    class Config:
        from_attributes = True


class UsuarioLocalEstadisticas(BaseModel):
    """Esquema para estadísticas de permisos."""
    tienda_id: UUID = Field(..., description="ID de la tienda")
    total_asignaciones: int = Field(..., description="Total de asignaciones activas")
    usuarios_unicos: int = Field(..., description="Usuarios únicos con permisos")
    responsables_por_local: Dict[str, int] = Field(..., description="Responsables por local")
    permisos_mas_asignados: Dict[str, int] = Field(..., description="Permisos más comunes")
    usuarios_sin_asignacion: int = Field(..., description="Usuarios sin permisos en locales")


# ============ ESQUEMAS DE CONTEXTO ============

class TenantContextResponse(BaseModel):
    """Esquema para respuesta de contexto de tenant."""
    tienda_id: UUID = Field(..., description="ID de la tienda")
    tienda_codigo: str = Field(..., description="Código de la tienda")
    tienda_nombre: str = Field(..., description="Nombre de la tienda")
    local_id: Optional[UUID] = Field(None, description="ID del local (si aplica)")
    local_codigo: Optional[str] = Field(None, description="Código del local (si aplica)")
    local_nombre: Optional[str] = Field(None, description="Nombre del local (si aplica)")
    tiene_contexto_local: bool = Field(..., description="Si tiene contexto de local específico")
    permisos_disponibles: List[str] = Field(..., description="Permisos del usuario en el contexto")


class CambiarContextoRequest(BaseModel):
    """Esquema para cambiar contexto de local."""
    local_id: Optional[UUID] = Field(None, description="Nuevo local (null para solo tienda)")


# ============ ESQUEMAS DE RESPUESTA PAGINADA ============

class PaginatedResponse(BaseModel):
    """Esquema base para respuestas paginadas."""
    items: List[Any] = Field(..., description="Lista de elementos")
    total: int = Field(..., description="Total de elementos")
    page: int = Field(..., description="Página actual")
    size: int = Field(..., description="Tamaño de página")
    pages: int = Field(..., description="Total de páginas")

    @validator('pages', always=True)
    def calculate_pages(cls, v, values):
        if 'total' in values and 'size' in values and values['size'] > 0:
            return (values['total'] + values['size'] - 1) // values['size']
        return 0


# ============ ESQUEMAS DE ERROR ============

class ErrorDetail(BaseModel):
    """Esquema para detalle de error."""
    field: Optional[str] = Field(None, description="Campo que causó el error")
    message: str = Field(..., description="Mensaje de error")
    code: Optional[str] = Field(None, description="Código de error")


class ErrorResponse(BaseModel):
    """Esquema para respuesta de error."""
    detail: str = Field(..., description="Mensaje principal del error")
    error_type: Optional[str] = Field(None, description="Tipo de error")
    errors: Optional[List[ErrorDetail]] = Field(None, description="Lista de errores detallados")