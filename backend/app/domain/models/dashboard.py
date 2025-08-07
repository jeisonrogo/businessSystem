"""
Modelos de dominio para el dashboard y reportes gerenciales.
Proporciona estructuras de datos para métricas consolidadas y visualizaciones.
"""

from sqlmodel import SQLModel
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class PeriodoReporte(str, Enum):
    """Períodos disponibles para reportes."""
    HOY = "hoy"
    SEMANA = "semana"
    MES = "mes"
    TRIMESTRE = "trimestre"
    SEMESTRE = "semestre"
    ANO = "ano"
    PERSONALIZADO = "personalizado"


class TipoMetrica(str, Enum):
    """Tipos de métricas disponibles."""
    VENTAS = "ventas"
    INVENTARIO = "inventario"
    CONTABILIDAD = "contabilidad"
    CLIENTES = "clientes"
    PRODUCTOS = "productos"
    FINANCIERO = "financiero"


class MetricaPeriodo(BaseModel):
    """Métrica con comparación de períodos."""
    valor_actual: Decimal = Field(description="Valor del período actual")
    valor_anterior: Optional[Decimal] = Field(None, description="Valor del período anterior")
    porcentaje_cambio: Optional[Decimal] = Field(None, description="Porcentaje de cambio")
    tendencia: Optional[str] = Field(None, description="up, down, stable")

    class Config:
        from_attributes = True


class KPIDashboard(BaseModel):
    """KPIs principales del dashboard."""
    # Ventas y Facturación
    ventas_del_periodo: MetricaPeriodo = Field(description="Ventas totales del período")
    numero_facturas: MetricaPeriodo = Field(description="Número de facturas emitidas")
    ticket_promedio: MetricaPeriodo = Field(description="Ticket promedio por factura")
    cartera_pendiente: Decimal = Field(description="Valor total de cartera por cobrar")
    cartera_vencida: Decimal = Field(description="Valor de cartera vencida")
    
    # Inventario
    valor_inventario: Decimal = Field(description="Valor total del inventario")
    productos_activos: int = Field(description="Número de productos activos")
    productos_sin_stock: int = Field(description="Productos sin stock")
    productos_stock_bajo: int = Field(description="Productos con stock bajo")
    rotacion_inventario: Optional[Decimal] = Field(None, description="Índice de rotación")
    
    # Clientes
    clientes_activos: int = Field(description="Número de clientes activos")
    clientes_nuevos: MetricaPeriodo = Field(description="Nuevos clientes del período")
    
    # Contabilidad
    ingresos_periodo: MetricaPeriodo = Field(description="Ingresos del período")
    gastos_periodo: MetricaPeriodo = Field(description="Gastos del período")
    utilidad_bruta: MetricaPeriodo = Field(description="Utilidad bruta del período")
    margen_utilidad: Optional[Decimal] = Field(None, description="Margen de utilidad %")

    class Config:
        from_attributes = True


class VentasPorPeriodo(BaseModel):
    """Ventas agrupadas por período."""
    periodo: str = Field(description="Etiqueta del período (ej: '2025-01', 'Enero')")
    fecha_inicio: date = Field(description="Fecha inicio del período")
    fecha_fin: date = Field(description="Fecha fin del período")
    total_ventas: Decimal = Field(description="Total de ventas del período")
    numero_facturas: int = Field(description="Número de facturas")
    ticket_promedio: Decimal = Field(description="Ticket promedio")

    class Config:
        from_attributes = True


class ProductoTopVentas(BaseModel):
    """Producto top en ventas."""
    producto_id: str = Field(description="ID del producto")
    sku: str = Field(description="SKU del producto")
    nombre: str = Field(description="Nombre del producto")
    cantidad_vendida: int = Field(description="Cantidad vendida")
    total_ventas: Decimal = Field(description="Total de ventas del producto")
    numero_facturas: int = Field(description="Número de facturas que incluyen este producto")
    ticket_promedio: Decimal = Field(description="Ticket promedio del producto")

    class Config:
        from_attributes = True


class ClienteTopVentas(BaseModel):
    """Cliente top en ventas."""
    cliente_id: str = Field(description="ID del cliente")
    numero_documento: str = Field(description="Documento del cliente")
    nombre_completo: str = Field(description="Nombre del cliente")
    total_compras: Decimal = Field(description="Total de compras del cliente")
    numero_facturas: int = Field(description="Número de facturas del cliente")
    ticket_promedio: Decimal = Field(description="Ticket promedio del cliente")
    ultima_compra: Optional[date] = Field(None, description="Fecha de última compra")

    class Config:
        from_attributes = True


class MovimientoInventarioResumen(BaseModel):
    """Resumen de movimientos de inventario."""
    tipo_movimiento: str = Field(description="Tipo de movimiento")
    cantidad_movimientos: int = Field(description="Número de movimientos")
    cantidad_total: int = Field(description="Cantidad total movida")
    valor_total: Decimal = Field(description="Valor total de los movimientos")

    class Config:
        from_attributes = True


class BalanceContableResumen(BaseModel):
    """Resumen de balance contable."""
    codigo_cuenta: str = Field(description="Código de la cuenta")
    nombre_cuenta: str = Field(description="Nombre de la cuenta")
    tipo_cuenta: str = Field(description="Tipo de cuenta")
    total_debitos: Decimal = Field(description="Total de débitos")
    total_creditos: Decimal = Field(description="Total de créditos")
    saldo: Decimal = Field(description="Saldo de la cuenta")

    class Config:
        from_attributes = True


class AlertaDashboard(BaseModel):
    """Alerta para el dashboard."""
    tipo: str = Field(description="Tipo de alerta (warning, danger, info)")
    titulo: str = Field(description="Título de la alerta")
    mensaje: str = Field(description="Mensaje de la alerta")
    fecha: datetime = Field(description="Fecha de la alerta")
    modulo: str = Field(description="Módulo que genera la alerta")
    requiere_accion: bool = Field(False, description="Si requiere acción del usuario")

    class Config:
        from_attributes = True


class DashboardCompleto(BaseModel):
    """Dashboard completo con todas las métricas."""
    fecha_generacion: datetime = Field(description="Fecha de generación del dashboard")
    periodo: PeriodoReporte = Field(description="Período del reporte")
    fecha_inicio: date = Field(description="Fecha inicio del período")
    fecha_fin: date = Field(description="Fecha fin del período")
    
    # KPIs principales
    kpis: KPIDashboard = Field(description="Indicadores clave de rendimiento")
    
    # Gráficos y tendencias
    ventas_por_periodo: List[VentasPorPeriodo] = Field(description="Ventas por período")
    productos_top: List[ProductoTopVentas] = Field(description="Productos más vendidos")
    clientes_top: List[ClienteTopVentas] = Field(description="Mejores clientes")
    
    # Inventario
    movimientos_inventario: List[MovimientoInventarioResumen] = Field(description="Resumen movimientos")
    
    # Contabilidad
    balance_principales: List[BalanceContableResumen] = Field(description="Balance cuentas principales")
    
    # Alertas
    alertas: List[AlertaDashboard] = Field(description="Alertas del sistema")

    class Config:
        from_attributes = True


class FiltrosDashboard(BaseModel):
    """Filtros para personalizar el dashboard."""
    periodo: PeriodoReporte = Field(PeriodoReporte.MES, description="Período del reporte")
    fecha_inicio: Optional[date] = Field(None, description="Fecha inicio personalizada")
    fecha_fin: Optional[date] = Field(None, description="Fecha fin personalizada")
    incluir_metricas: List[TipoMetrica] = Field(default_factory=lambda: [
        TipoMetrica.VENTAS,
        TipoMetrica.INVENTARIO, 
        TipoMetrica.CONTABILIDAD,
        TipoMetrica.CLIENTES
    ], description="Tipos de métricas a incluir")
    limite_tops: int = Field(10, description="Límite de elementos en rankings")
    incluir_comparacion_periodos: bool = Field(True, description="Incluir comparación con período anterior")

    class Config:
        from_attributes = True


# Esquemas para endpoints API
class DashboardRequest(BaseModel):
    """Request para obtener dashboard."""
    filtros: Optional[FiltrosDashboard] = Field(None, description="Filtros del dashboard")

    class Config:
        from_attributes = True


class DashboardResponse(DashboardCompleto):
    """Response del dashboard (hereda de DashboardCompleto)."""
    pass


class MetricasRapidas(BaseModel):
    """Métricas rápidas para widgets pequeños."""
    ventas_hoy: Decimal = Field(description="Ventas de hoy")
    ventas_mes: Decimal = Field(description="Ventas del mes")
    facturas_pendientes: int = Field(description="Facturas por cobrar")
    stock_critico: int = Field(description="Productos con stock crítico")
    nuevos_clientes_mes: int = Field(description="Nuevos clientes este mes")
    
    class Config:
        from_attributes = True