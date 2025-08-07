"""
Endpoints REST para el dashboard y reportes gerenciales.
Proporciona endpoints para métricas consolidadas y visualizaciones.
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.application.use_cases.dashboard_use_cases import (
    GetDashboardCompletoUseCase,
    GetMetricasRapidasUseCase,
    GetKPIsPrincipalesUseCase,
    GetVentasPorPeriodoUseCase,
    GetProductosTopVentasUseCase,
    GetClientesTopVentasUseCase,
    GetResumenInventarioUseCase,
    GetBalanceContableResumenUseCase,
    GetAlertasDashboardUseCase,
    AnalisisRentabilidadUseCase,
    TendenciasVentasUseCase,
    EstadoSistemaUseCase,
    # Excepciones
    DashboardError,
    PeriodoInvalidoError,
    DatosInsuficientesError,
    FiltrosInvalidosError
)

from app.domain.models.dashboard import (
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
    PeriodoReporte
)

from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.dashboard_repository import SQLDashboardRepository


router = APIRouter()


# Funciones de dependencia
def get_dashboard_repository(session: Session = Depends(get_session)) -> SQLDashboardRepository:
    """Función de dependencia para crear una instancia del repositorio de dashboard."""
    return SQLDashboardRepository(session)


# Endpoints principales del dashboard

@router.get(
    "/test",
    status_code=status.HTTP_200_OK,
    summary="Test endpoint", 
    description="Simple test endpoint for debugging"
)
async def test_dashboard():
    """Test endpoint."""
    from datetime import datetime
    return {"status": "dashboard endpoints working", "timestamp": str(datetime.now())}


@router.get(
    "/completo",
    response_model=DashboardCompleto,
    status_code=status.HTTP_200_OK,
    summary="Obtener dashboard completo",
    description="Obtiene el dashboard completo con todas las métricas y visualizaciones configuradas."
)
async def get_dashboard_completo(
    periodo: PeriodoReporte = Query(PeriodoReporte.MES, description="Período del reporte"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio (requerida para período personalizado)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin (requerida para período personalizado)"),
    limite_tops: int = Query(10, ge=1, le=50, description="Límite para rankings (1-50)"),
    incluir_comparacion: bool = Query(True, description="Incluir comparación con período anterior"),
    dashboard_repository: SQLDashboardRepository = Depends(get_dashboard_repository)
):
    """
    Obtiene el dashboard completo con todas las métricas.
    
    - **periodo**: Período del reporte (hoy, semana, mes, trimestre, etc.)
    - **fecha_inicio**: Fecha inicio para período personalizado
    - **fecha_fin**: Fecha fin para período personalizado
    - **limite_tops**: Número de elementos en rankings
    - **incluir_comparacion**: Si incluir comparación con período anterior
    """
    try:
        # Crear filtros
        filtros = FiltrosDashboard(
            periodo=periodo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            limite_tops=limite_tops,
            incluir_comparacion_periodos=incluir_comparacion
        )
        
        # Ejecutar caso de uso
        use_case = GetDashboardCompletoUseCase(dashboard_repository)
        dashboard = await use_case.execute(filtros)
        
        return dashboard
        
    except FiltrosInvalidosError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PeriodoInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DashboardError as e:
        raise HTTPException(status_code=500, detail=f"Error generando dashboard: {str(e)}")


@router.get(
    "/metricas-rapidas",
    response_model=MetricasRapidas,
    status_code=status.HTTP_200_OK,
    summary="Obtener métricas rápidas",
    description="Obtiene métricas rápidas para widgets pequeños del dashboard."
)
async def get_metricas_rapidas(
    dashboard_repository: SQLDashboardRepository = Depends(get_dashboard_repository)
):
    """
    Obtiene métricas rápidas para widgets pequeños.
    
    Incluye:
    - Ventas de hoy y del mes
    - Facturas pendientes de pago
    - Productos con stock crítico
    - Nuevos clientes del mes
    """
    try:
        use_case = GetMetricasRapidasUseCase(dashboard_repository)
        metricas = await use_case.execute()
        return metricas
        
    except DashboardError as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo métricas rápidas: {str(e)}")


@router.get(
    "/kpis",
    response_model=KPIDashboard,
    status_code=status.HTTP_200_OK,
    summary="Obtener KPIs principales",
    description="Obtiene los indicadores clave de rendimiento (KPIs) del negocio."
)
async def get_kpis_principales(
    fecha_inicio: date = Query(description="Fecha de inicio del período"),
    fecha_fin: date = Query(description="Fecha de fin del período"),
    incluir_comparacion: bool = Query(True, description="Incluir comparación con período anterior"),
    dashboard_repository: SQLDashboardRepository = Depends(get_dashboard_repository)
):
    """
    Obtiene los KPIs principales del dashboard.
    
    Incluye métricas de:
    - Ventas y facturación
    - Inventario y productos
    - Clientes
    - Contabilidad y finanzas
    """
    try:
        use_case = GetKPIsPrincipalesUseCase(dashboard_repository)
        kpis = await use_case.execute(fecha_inicio, fecha_fin, incluir_comparacion)
        return kpis
        
    except PeriodoInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DashboardError as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo KPIs: {str(e)}")


@router.get(
    "/ventas-por-periodo",
    response_model=List[VentasPorPeriodo],
    status_code=status.HTTP_200_OK,
    summary="Obtener ventas por período",
    description="Obtiene las ventas agrupadas por período para gráficos de tendencias."
)
async def get_ventas_por_periodo(
    fecha_inicio: date = Query(description="Fecha de inicio del período"),
    fecha_fin: date = Query(description="Fecha de fin del período"),
    agrupacion: str = Query("mes", pattern="^(dia|semana|mes|trimestre)$", description="Tipo de agrupación"),
    dashboard_repository: SQLDashboardRepository = Depends(get_dashboard_repository)
):
    """
    Obtiene ventas agrupadas por período.
    
    - **agrupacion**: Tipo de agrupación (dia, semana, mes, trimestre)
    - Útil para generar gráficos de líneas de tendencias de ventas
    """
    try:
        use_case = GetVentasPorPeriodoUseCase(dashboard_repository)
        ventas = await use_case.execute(fecha_inicio, fecha_fin, agrupacion)
        return ventas
        
    except PeriodoInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FiltrosInvalidosError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DashboardError as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo ventas por período: {str(e)}")


@router.get(
    "/productos-top",
    response_model=List[ProductoTopVentas],
    status_code=status.HTTP_200_OK,
    summary="Obtener productos más vendidos",
    description="Obtiene el ranking de productos más vendidos del período."
)
async def get_productos_top_ventas(
    fecha_inicio: date = Query(description="Fecha de inicio del período"),
    fecha_fin: date = Query(description="Fecha de fin del período"),
    limite: int = Query(10, ge=1, le=50, description="Número máximo de productos (1-50)"),
    dashboard_repository: SQLDashboardRepository = Depends(get_dashboard_repository)
):
    """
    Obtiene el ranking de productos más vendidos.
    
    - Ordenados por total de ventas
    - Incluye cantidad vendida, ingresos y número de facturas
    - Útil para análisis de productos y decisiones de inventario
    """
    try:
        use_case = GetProductosTopVentasUseCase(dashboard_repository)
        productos = await use_case.execute(fecha_inicio, fecha_fin, limite)
        return productos
        
    except PeriodoInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FiltrosInvalidosError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DashboardError as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo productos top: {str(e)}")


@router.get(
    "/clientes-top",
    response_model=List[ClienteTopVentas],
    status_code=status.HTTP_200_OK,
    summary="Obtener mejores clientes",
    description="Obtiene el ranking de clientes con más compras del período."
)
async def get_clientes_top_ventas(
    fecha_inicio: date = Query(description="Fecha de inicio del período"),
    fecha_fin: date = Query(description="Fecha de fin del período"),
    limite: int = Query(10, ge=1, le=50, description="Número máximo de clientes (1-50)"),
    dashboard_repository: SQLDashboardRepository = Depends(get_dashboard_repository)
):
    """
    Obtiene el ranking de mejores clientes.
    
    - Ordenados por total de compras
    - Incluye número de facturas y ticket promedio
    - Útil para estrategias de fidelización y marketing
    """
    try:
        use_case = GetClientesTopVentasUseCase(dashboard_repository)
        clientes = await use_case.execute(fecha_inicio, fecha_fin, limite)
        return clientes
        
    except PeriodoInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FiltrosInvalidosError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DashboardError as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo clientes top: {str(e)}")


@router.get(
    "/inventario-resumen",
    response_model=List[MovimientoInventarioResumen],
    status_code=status.HTTP_200_OK,
    summary="Obtener resumen de inventario",
    description="Obtiene resumen de movimientos de inventario del período."
)
async def get_resumen_inventario(
    fecha_inicio: date = Query(description="Fecha de inicio del período"),
    fecha_fin: date = Query(description="Fecha de fin del período"),
    dashboard_repository: SQLDashboardRepository = Depends(get_dashboard_repository)
):
    """
    Obtiene resumen de movimientos de inventario.
    
    - Agrupado por tipo de movimiento (entrada, salida, merma, ajuste)
    - Incluye cantidad de movimientos y valores totales
    - Útil para análisis de operaciones de inventario
    """
    try:
        use_case = GetResumenInventarioUseCase(dashboard_repository)
        resumen = await use_case.execute(fecha_inicio, fecha_fin)
        return resumen
        
    except PeriodoInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DashboardError as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo resumen inventario: {str(e)}")


@router.get(
    "/balance-contable",
    response_model=List[BalanceContableResumen],
    status_code=status.HTTP_200_OK,
    summary="Obtener balance contable",
    description="Obtiene resumen del balance de cuentas contables del período."
)
async def get_balance_contable_resumen(
    fecha_inicio: date = Query(description="Fecha de inicio del período"),
    fecha_fin: date = Query(description="Fecha de fin del período"),
    solo_principales: bool = Query(True, description="Solo mostrar cuentas principales"),
    dashboard_repository: SQLDashboardRepository = Depends(get_dashboard_repository)
):
    """
    Obtiene resumen del balance contable.
    
    - **solo_principales**: Si True, solo muestra cuentas principales (4 dígitos o menos)
    - Incluye débitos, créditos y saldo por cuenta
    - Útil para análisis financiero y contable
    """
    try:
        use_case = GetBalanceContableResumenUseCase(dashboard_repository)
        balance = await use_case.execute(fecha_inicio, fecha_fin, solo_principales)
        return balance
        
    except PeriodoInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DashboardError as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo balance contable: {str(e)}")


@router.get(
    "/alertas",
    response_model=List[AlertaDashboard],
    status_code=status.HTTP_200_OK,
    summary="Obtener alertas del sistema",
    description="Obtiene alertas relevantes para mostrar en el dashboard."
)
async def get_alertas_dashboard(
    dashboard_repository: SQLDashboardRepository = Depends(get_dashboard_repository)
):
    """
    Obtiene alertas del sistema.
    
    Alertas automáticas incluyen:
    - Productos sin stock
    - Stock bajo
    - Cartera vencida
    - Facturas pendientes excesivas
    """
    try:
        use_case = GetAlertasDashboardUseCase(dashboard_repository)
        alertas = await use_case.execute()
        return alertas
        
    except DashboardError as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo alertas: {str(e)}")


# Endpoints de análisis avanzado

@router.get(
    "/analisis/rentabilidad",
    status_code=status.HTTP_200_OK,
    summary="Análisis de rentabilidad",
    description="Realiza análisis detallado de rentabilidad del período."
)
async def analisis_rentabilidad(
    fecha_inicio: date = Query(description="Fecha de inicio del período"),
    fecha_fin: date = Query(description="Fecha de fin del período"),
    dashboard_repository: SQLDashboardRepository = Depends(get_dashboard_repository)
):
    """
    Análisis completo de rentabilidad.
    
    Incluye:
    - Métricas financieras (ingresos, gastos, utilidad, margen)
    - Métricas de ventas y operaciones
    - Top productos y clientes más rentables
    - Índices de rotación
    """
    try:
        use_case = AnalisisRentabilidadUseCase(dashboard_repository)
        analisis = await use_case.execute(fecha_inicio, fecha_fin)
        return analisis
        
    except PeriodoInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DashboardError as e:
        raise HTTPException(status_code=500, detail=f"Error en análisis de rentabilidad: {str(e)}")


@router.get(
    "/analisis/tendencias-ventas",
    status_code=status.HTTP_200_OK,
    summary="Análisis de tendencias de ventas",
    description="Analiza las tendencias de ventas en el período especificado."
)
async def analisis_tendencias_ventas(
    fecha_inicio: date = Query(description="Fecha de inicio del período"),
    fecha_fin: date = Query(description="Fecha de fin del período"),
    agrupacion: str = Query("mes", pattern="^(dia|semana|mes|trimestre)$", description="Tipo de agrupación"),
    dashboard_repository: SQLDashboardRepository = Depends(get_dashboard_repository)
):
    """
    Análisis de tendencias de ventas.
    
    Incluye:
    - Tendencia general (creciente, decreciente, estable)
    - Crecimiento promedio entre períodos
    - Mejor y peor período
    - Datos detallados por período
    """
    try:
        use_case = TendenciasVentasUseCase(dashboard_repository)
        analisis = await use_case.execute(fecha_inicio, fecha_fin, agrupacion)
        return analisis
        
    except PeriodoInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatosInsuficientesError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DashboardError as e:
        raise HTTPException(status_code=500, detail=f"Error en análisis de tendencias: {str(e)}")


@router.get(
    "/estado-sistema",
    status_code=status.HTTP_200_OK,
    summary="Estado general del sistema",
    description="Obtiene un resumen del estado actual de todo el sistema."
)
async def get_estado_sistema(
    dashboard_repository: SQLDashboardRepository = Depends(get_dashboard_repository)
):
    """
    Estado general del sistema.
    
    Incluye:
    - Métricas rápidas actuales
    - Índice de salud del sistema
    - Resumen de alertas por tipo
    - Estado de cada módulo principal
    """
    try:
        use_case = EstadoSistemaUseCase(dashboard_repository)
        estado = await use_case.execute()
        return estado
        
    except DashboardError as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado del sistema: {str(e)}")


# Endpoints para exportación y configuración

@router.get(
    "/export/excel",
    status_code=status.HTTP_200_OK,
    summary="Exportar dashboard a Excel",
    description="Exporta los datos del dashboard en formato Excel."
)
async def export_dashboard_excel(
    periodo: PeriodoReporte = Query(PeriodoReporte.MES, description="Período del reporte"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha inicio personalizada"),
    fecha_fin: Optional[date] = Query(None, description="Fecha fin personalizada"),
    dashboard_repository: SQLDashboardRepository = Depends(get_dashboard_repository)
):
    """
    Exporta el dashboard completo a Excel.
    
    Genera un archivo Excel con múltiples hojas:
    - Resumen ejecutivo
    - KPIs principales
    - Ventas por período
    - Top productos y clientes
    - Balance contable
    
    TODO: Implementar generación de Excel
    """
    raise HTTPException(
        status_code=501, 
        detail="Funcionalidad de exportación a Excel no implementada aún"
    )


@router.get(
    "/configuracion/periodos",
    status_code=status.HTTP_200_OK,
    summary="Obtener períodos disponibles",
    description="Obtiene la lista de períodos disponibles para reportes."
)
async def get_periodos_disponibles():
    """
    Obtiene los períodos disponibles para reportes.
    
    Útil para interfaces de usuario que necesiten mostrar
    las opciones de período disponibles.
    """
    return {
        "periodos": [
            {"valor": "hoy", "etiqueta": "Hoy"},
            {"valor": "semana", "etiqueta": "Esta semana"},
            {"valor": "mes", "etiqueta": "Este mes"},
            {"valor": "trimestre", "etiqueta": "Este trimestre"},
            {"valor": "semestre", "etiqueta": "Este semestre"},
            {"valor": "ano", "etiqueta": "Este año"},
            {"valor": "personalizado", "etiqueta": "Período personalizado"}
        ]
    }