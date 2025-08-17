"""
Esquemas Pydantic para la API.
Define los modelos de datos de entrada y salida para los endpoints.
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


# Esquemas de autenticación
class LoginRequest(BaseModel):
    """
    Esquema para la solicitud de login.
    """
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=8, description="Contraseña del usuario")


class TokenResponse(BaseModel):
    """
    Esquema para la respuesta de token JWT.
    """
    access_token: str = Field(..., description="Token JWT de acceso")
    token_type: str = Field(default="bearer", description="Tipo de token")


class UserResponse(BaseModel):
    """
    Esquema para la respuesta de información de usuario.
    """
    id: str = Field(..., description="ID único del usuario")
    email: str = Field(..., description="Email del usuario")
    nombre: str = Field(..., description="Nombre completo del usuario")
    rol: str = Field(..., description="Rol del usuario")
    is_active: bool = Field(..., description="Estado activo del usuario")
    created_at: str = Field(..., description="Fecha de creación en formato ISO")


class LoginResponse(BaseModel):
    """
    Esquema para la respuesta completa de login.
    """
    access_token: str = Field(..., description="Token JWT de acceso")
    token_type: str = Field(default="bearer", description="Tipo de token")
    user: UserResponse = Field(..., description="Información del usuario")


class RegisterRequest(BaseModel):
    """
    Esquema para la solicitud de registro de usuario.
    """
    email: EmailStr = Field(..., description="Email único del usuario")
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre completo del usuario")
    rol: str = Field(default="vendedor", description="Rol del usuario en el sistema")
    password: str = Field(..., min_length=8, description="Contraseña del usuario")


class RegisterResponse(BaseModel):
    """
    Esquema para la respuesta de registro de usuario.
    """
    access_token: str = Field(..., description="Token JWT de acceso")
    token_type: str = Field(default="bearer", description="Tipo de token")
    user: UserResponse = Field(..., description="Información del usuario creado")
    message: str = Field(..., description="Mensaje de confirmación")


class ProfileUpdateRequest(BaseModel):
    """
    Esquema para la solicitud de actualización de perfil.
    """
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre completo del usuario")
    email: EmailStr = Field(..., description="Email del usuario")


class ChangePasswordRequest(BaseModel):
    """
    Esquema para la solicitud de cambio de contraseña.
    """
    current_password: str = Field(..., min_length=8, description="Contraseña actual")
    new_password: str = Field(..., min_length=8, description="Nueva contraseña")


# Esquemas de error
class ErrorResponse(BaseModel):
    """
    Esquema para respuestas de error.
    """
    detail: str = Field(..., description="Descripción del error")
    error_code: Optional[str] = Field(None, description="Código de error específico")


class ValidationErrorResponse(BaseModel):
    """
    Esquema para errores de validación.
    """
    detail: str = Field(..., description="Descripción del error")
    field_errors: Optional[dict] = Field(None, description="Errores específicos de campos")


# Esquemas generales
class HealthResponse(BaseModel):
    """
    Esquema para la respuesta del endpoint de salud.
    """
    status: str = Field(default="ok", description="Estado del servicio")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp de la respuesta")


class MessageResponse(BaseModel):
    """
    Esquema para respuestas con mensaje simple.
    """
    message: str = Field(..., description="Mensaje de respuesta")
    success: bool = Field(default=True, description="Indica si la operación fue exitosa")


# Esquemas de productos
# Re-exportamos los esquemas del dominio para mantener la separación de capas
from app.domain.models.product import (
    ProductCreate as DomainProductCreate,
    ProductUpdate as DomainProductUpdate,
    ProductResponse as DomainProductResponse,
    ProductListResponse as DomainProductListResponse
)


# Esquemas específicos para la API de productos
class ProductCreateRequest(DomainProductCreate):
    """
    Esquema para la solicitud de creación de producto.
    Hereda de DomainProductCreate para mantener la consistencia.
    """
    pass


class ProductUpdateRequest(DomainProductUpdate):
    """
    Esquema para la solicitud de actualización de producto.
    Hereda de DomainProductUpdate para mantener la consistencia.
    """
    pass


class ProductResponse(DomainProductResponse):
    """
    Esquema para la respuesta de información de producto.
    Hereda de DomainProductResponse para mantener la consistencia.
    """
    pass


class ProductListResponse(DomainProductListResponse):
    """
    Esquema para la respuesta de lista paginada de productos.
    Hereda de DomainProductListResponse para mantener la consistencia.
    """
    pass


class ProductStockUpdateRequest(BaseModel):
    """
    Esquema para la solicitud de actualización de stock.
    """
    stock: int = Field(..., ge=0, description="Nueva cantidad de stock (no puede ser negativo)")


class ProductStockUpdateResponse(BaseModel):
    """
    Esquema para la respuesta de actualización de stock.
    """
    product_id: UUID = Field(..., description="ID del producto actualizado")
    previous_stock: int = Field(..., description="Stock anterior")
    new_stock: int = Field(..., description="Stock actualizado")
    message: str = Field(..., description="Mensaje de confirmación")


class LowStockThresholdRequest(BaseModel):
    """
    Esquema para la solicitud de productos con stock bajo.
    """
    threshold: int = Field(10, ge=0, description="Umbral mínimo de stock")


class ProductDeleteResponse(BaseModel):
    """
    Esquema para la respuesta de eliminación de producto.
    """
    product_id: UUID = Field(..., description="ID del producto eliminado")
    message: str = Field(..., description="Mensaje de confirmación")
    success: bool = Field(default=True, description="Indica si la operación fue exitosa")


# Esquemas de inventario
# Re-exportamos los esquemas del dominio para mantener la separación de capas
from app.domain.models.movimiento_inventario import (
    MovimientoInventarioCreate as DomainMovimientoInventarioCreate,
    MovimientoInventarioResponse as DomainMovimientoInventarioResponse,
    MovimientoInventarioListResponse as DomainMovimientoInventarioListResponse,
    KardexResponse as DomainKardexResponse,
    InventarioResumenResponse as DomainInventarioResumenResponse,
    EstadisticasInventario as DomainEstadisticasInventario,
    TipoMovimiento,
    MovimientoInventarioFilter
)


# Esquemas específicos para la API de inventario
class MovimientoInventarioCreateRequest(DomainMovimientoInventarioCreate):
    """
    Esquema para la solicitud de creación de movimiento de inventario.
    Hereda de DomainMovimientoInventarioCreate para mantener la consistencia.
    """
    pass


class MovimientoInventarioResponse(DomainMovimientoInventarioResponse):
    """
    Esquema para la respuesta de información de movimiento.
    Hereda de DomainMovimientoInventarioResponse para mantener la consistencia.
    """
    pass


class MovimientoInventarioListResponse(DomainMovimientoInventarioListResponse):
    """
    Esquema para la respuesta de lista paginada de movimientos.
    Hereda de DomainMovimientoInventarioListResponse para mantener la consistencia.
    """
    pass


class KardexResponse(DomainKardexResponse):
    """
    Esquema para la respuesta del kardex de un producto.
    Hereda de DomainKardexResponse para mantener la consistencia.
    """
    pass


class InventarioResumenResponse(DomainInventarioResumenResponse):
    """
    Esquema para la respuesta del resumen de inventario.
    Hereda de DomainInventarioResumenResponse para mantener la consistencia.
    """
    pass


class EstadisticasInventarioResponse(DomainEstadisticasInventario):
    """
    Esquema para la respuesta de estadísticas de inventario.
    Hereda de DomainEstadisticasInventario para mantener la consistencia.
    """
    pass


class ValidarStockRequest(BaseModel):
    """
    Esquema para la solicitud de validación de stock.
    """
    producto_id: UUID = Field(..., description="ID del producto")
    cantidad_requerida: int = Field(..., gt=0, description="Cantidad requerida")


class ValidarStockResponse(BaseModel):
    """
    Esquema para la respuesta de validación de stock.
    """
    producto_id: UUID = Field(..., description="ID del producto")
    stock_actual: int = Field(..., description="Stock actual del producto")
    cantidad_requerida: int = Field(..., description="Cantidad requerida")
    stock_suficiente: bool = Field(..., description="Si hay stock suficiente")
    cantidad_disponible: int = Field(..., description="Cantidad disponible después de la operación")


class MovimientoInventarioFilterRequest(BaseModel):
    """
    Esquema para filtros de búsqueda de movimientos.
    """
    producto_id: Optional[UUID] = Field(None, description="Filtrar por producto")
    tipo_movimiento: Optional[TipoMovimiento] = Field(None, description="Filtrar por tipo")
    fecha_desde: Optional[datetime] = Field(None, description="Fecha desde")
    fecha_hasta: Optional[datetime] = Field(None, description="Fecha hasta")
    referencia: Optional[str] = Field(None, description="Filtrar por referencia")
    created_by: Optional[UUID] = Field(None, description="Filtrar por usuario")


# Esquemas de contabilidad
# Re-exportamos los esquemas del dominio para mantener la separación de capas
from app.domain.models.contabilidad import (
    CuentaContableCreate as DomainCuentaContableCreate,
    CuentaContableUpdate as DomainCuentaContableUpdate,
    CuentaContableResponse as DomainCuentaContableResponse,
    AsientoContableCreate as DomainAsientoContableCreate,
    AsientoContableResponse as DomainAsientoContableResponse,
    AsientoContableListResponse as DomainAsientoContableListResponse,
    DetalleAsientoCreate as DomainDetalleAsientoCreate,
    DetalleAsientoResponse as DomainDetalleAsientoResponse,
    TipoCuenta,
    TipoMovimiento as TipoMovimientoContable
)


# Esquemas específicos para la API de contabilidad
class CuentaContableCreateRequest(DomainCuentaContableCreate):
    """
    Esquema para la solicitud de creación de cuenta contable.
    Hereda de DomainCuentaContableCreate para mantener la consistencia.
    """
    pass


class CuentaContableUpdateRequest(DomainCuentaContableUpdate):
    """
    Esquema para la solicitud de actualización de cuenta contable.
    Hereda de DomainCuentaContableUpdate para mantener la consistencia.
    """
    pass


class CuentaContableResponse(DomainCuentaContableResponse):
    """
    Esquema para la respuesta de información de cuenta contable.
    Hereda de DomainCuentaContableResponse para mantener la consistencia.
    """
    pass


class CuentaContableListResponse(BaseModel):
    """
    Esquema para la respuesta de lista paginada de cuentas contables.
    """
    cuentas: list[CuentaContableResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class AsientoContableCreateRequest(DomainAsientoContableCreate):
    """
    Esquema para la solicitud de creación de asiento contable.
    Hereda de DomainAsientoContableCreate para mantener la consistencia.
    """
    pass


class AsientoContableResponse(DomainAsientoContableResponse):
    """
    Esquema para la respuesta de información de asiento contable.
    Hereda de DomainAsientoContableResponse para mantener la consistencia.
    """
    pass


class AsientoContableListResponse(DomainAsientoContableListResponse):
    """
    Esquema para la respuesta de lista paginada de asientos contables.
    Hereda de DomainAsientoContableListResponse para mantener la consistencia.
    """
    pass


class DetalleAsientoCreateRequest(DomainDetalleAsientoCreate):
    """
    Esquema para la solicitud de creación de detalle de asiento.
    Hereda de DomainDetalleAsientoCreate para mantener la consistencia.
    """
    pass


class DetalleAsientoResponse(DomainDetalleAsientoResponse):
    """
    Esquema para la respuesta de información de detalle de asiento.
    Hereda de DomainDetalleAsientoResponse para mantener la consistencia.
    """
    pass


# Esquemas específicos para contabilidad
class PlanCuentasJerarquicoResponse(BaseModel):
    """
    Esquema para la respuesta del plan de cuentas jerárquico.
    """
    plan_cuentas: list[dict] = Field(..., description="Plan de cuentas en formato jerárquico")


class SeedPlanCuentasResponse(BaseModel):
    """
    Esquema para la respuesta del seeding del plan de cuentas.
    """
    mensaje: str = Field(..., description="Mensaje de confirmación")
    cuentas_creadas: int = Field(..., description="Número de cuentas creadas")
    total_procesadas: int = Field(..., description="Total de cuentas procesadas")


class CuentasPrincipalesResponse(BaseModel):
    """
    Esquema para la respuesta de cuentas principales por tipo.
    """
    cuentas: list[CuentaContableResponse] = Field(..., description="Lista de cuentas principales")
    tipo_cuenta: Optional[TipoCuenta] = Field(None, description="Tipo de cuenta filtrado")


class SubcuentasResponse(BaseModel):
    """
    Esquema para la respuesta de subcuentas.
    """
    subcuentas: list[CuentaContableResponse] = Field(..., description="Lista de subcuentas")
    cuenta_padre_id: UUID = Field(..., description="ID de la cuenta padre")
    total_subcuentas: int = Field(..., description="Total de subcuentas")


# Esquemas específicos para asientos contables
class AsientoContableListResponse(BaseModel):
    """
    Esquema para la respuesta de lista paginada de asientos contables.
    """
    asientos: list[AsientoContableResponse] = Field(..., description="Lista de asientos contables")
    total: int = Field(..., description="Total de asientos")
    page: int = Field(..., description="Página actual")
    limit: int = Field(..., description="Elementos por página")
    has_next: bool = Field(..., description="Si hay página siguiente")
    has_prev: bool = Field(..., description="Si hay página anterior")


class ValidacionBalanceRequest(BaseModel):
    """
    Esquema para la solicitud de validación de balance.
    """
    detalles: list[DetalleAsientoCreateRequest] = Field(..., description="Lista de detalles del asiento")


class ValidacionBalanceResponse(BaseModel):
    """
    Esquema para la respuesta de validación de balance.
    """
    esta_balanceado: bool = Field(..., description="Si el asiento está balanceado")
    total_debitos: float = Field(..., description="Total de débitos")
    total_creditos: float = Field(..., description="Total de créditos")
    diferencia: float = Field(..., description="Diferencia entre débitos y créditos")
    cantidad_detalles: int = Field(..., description="Número de detalles")


class BalanceCuentaResponse(BaseModel):
    """
    Esquema para la respuesta del balance de una cuenta.
    """
    cuenta_id: UUID = Field(..., description="ID de la cuenta")
    total_debitos: float = Field(..., description="Total de débitos")
    total_creditos: float = Field(..., description="Total de créditos")
    saldo: float = Field(..., description="Saldo de la cuenta")
    cantidad_movimientos: int = Field(..., description="Número de movimientos")
    fecha_hasta: Optional[str] = Field(None, description="Fecha hasta la cual se calculó")


class LibroDiarioRequest(BaseModel):
    """
    Esquema para la solicitud del libro diario.
    """
    fecha_desde: str = Field(..., description="Fecha desde en formato YYYY-MM-DD")
    fecha_hasta: str = Field(..., description="Fecha hasta en formato YYYY-MM-DD")


class LibroDiarioResponse(BaseModel):
    """
    Esquema para la respuesta del libro diario.
    """
    asientos: list[AsientoContableResponse] = Field(..., description="Lista de asientos contables")
    fecha_desde: str = Field(..., description="Fecha desde")
    fecha_hasta: str = Field(..., description="Fecha hasta")
    total_asientos: int = Field(..., description="Total de asientos en el período")


# Re-exportar esquemas de dashboard desde el dominio
from app.domain.models.dashboard import (
    # Modelos principales
    DashboardCompleto,
    FiltrosDashboard,
    KPIDashboard,
    VentasPorPeriodo,
    ProductoTopVentas,
    ClienteTopVentas,
    MovimientoInventarioResumen,
    BalanceContableResumen,
    AlertaDashboard,
    MetricasRapidas,
    MetricaPeriodo,
    
    # Enums
    PeriodoReporte,
    TipoMetrica,
    
    # Esquemas para API
    DashboardRequest,
    DashboardResponse
)

# Esquemas específicos para endpoints de dashboard
class DashboardCompletoRequest(BaseModel):
    """Esquema para solicitud de dashboard completo."""
    periodo: PeriodoReporte = Field(PeriodoReporte.MES, description="Período del reporte")
    fecha_inicio: Optional[date] = Field(None, description="Fecha inicio personalizada")
    fecha_fin: Optional[date] = Field(None, description="Fecha fin personalizada")
    limite_tops: int = Field(10, ge=1, le=50, description="Límite para rankings")
    incluir_comparacion: bool = Field(True, description="Incluir comparación con período anterior")

class AnalisisRentabilidadResponse(BaseModel):
    """Esquema para respuesta de análisis de rentabilidad."""
    periodo: dict = Field(description="Información del período analizado")
    metricas_financieras: dict = Field(description="Métricas financieras calculadas")
    metricas_ventas: dict = Field(description="Métricas de ventas")
    productos_mas_rentables: List[ProductoTopVentas] = Field(description="Productos más rentables")
    clientes_mas_rentables: List[ClienteTopVentas] = Field(description="Clientes más rentables")

class TendenciasVentasResponse(BaseModel):
    """Esquema para respuesta de análisis de tendencias."""
    periodo_analisis: dict = Field(description="Información del período analizado")
    tendencia_general: str = Field(description="Tendencia general (creciente, decreciente, estable)")
    crecimiento_promedio: Optional[Decimal] = Field(description="Crecimiento promedio en porcentaje")
    mejor_periodo: dict = Field(description="Mejor período de ventas")
    peor_periodo: dict = Field(description="Peor período de ventas")
    datos_detallados: List[VentasPorPeriodo] = Field(description="Datos detallados por período")

class EstadoSistemaResponse(BaseModel):
    """Esquema para respuesta del estado del sistema."""
    fecha_consulta: date = Field(description="Fecha de la consulta")
    metricas_rapidas: MetricasRapidas = Field(description="Métricas rápidas del sistema")
    salud_sistema: dict = Field(description="Índice de salud del sistema")
    alertas: dict = Field(description="Resumen de alertas por tipo")
    resumen_modulos: dict = Field(description="Estado de cada módulo principal") 