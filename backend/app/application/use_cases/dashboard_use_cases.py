"""
Casos de uso para el dashboard y reportes gerenciales.
Orquesta la lógica de negocio para generar métricas consolidadas.
"""

from typing import List, Optional
from datetime import date
from decimal import Decimal

from app.application.services.i_dashboard_repository import IDashboardRepository
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


# Excepciones específicas para Dashboard
class DashboardError(Exception):
    """Excepción base para errores del dashboard."""
    pass


class PeriodoInvalidoError(DashboardError):
    """Error cuando el período especificado es inválido."""
    pass


class DatosInsuficientesError(DashboardError):
    """Error cuando no hay suficientes datos para generar el dashboard."""
    pass


class FiltrosInvalidosError(DashboardError):
    """Error cuando los filtros proporcionados son inválidos."""
    pass


# Casos de uso principales

class GetDashboardCompletoUseCase:
    """Caso de uso para obtener el dashboard completo."""

    def __init__(self, dashboard_repository: IDashboardRepository):
        self.dashboard_repository = dashboard_repository

    async def execute(self, filtros: Optional[FiltrosDashboard] = None) -> DashboardCompleto:
        """
        Obtiene el dashboard completo con todas las métricas.
        
        Args:
            filtros: Filtros para personalizar el dashboard
            
        Returns:
            DashboardCompleto: Dashboard con todas las métricas
            
        Raises:
            FiltrosInvalidosError: Si los filtros son inválidos
            DashboardError: Si hay error generando el dashboard
        """
        try:
            # Usar filtros por defecto si no se proporcionan
            if filtros is None:
                filtros = FiltrosDashboard()
            
            # Validar filtros
            await self._validar_filtros(filtros)
            
            # Obtener dashboard completo
            dashboard = await self.dashboard_repository.get_dashboard_completo(filtros)
            
            return dashboard
            
        except Exception as e:
            if isinstance(e, (FiltrosInvalidosError, PeriodoInvalidoError)):
                raise
            raise DashboardError(f"Error generando dashboard completo: {str(e)}")

    async def _validar_filtros(self, filtros: FiltrosDashboard) -> None:
        """Valida que los filtros sean correctos."""
        if filtros.periodo == PeriodoReporte.PERSONALIZADO:
            if not filtros.fecha_inicio or not filtros.fecha_fin:
                raise FiltrosInvalidosError("Para período personalizado se requieren fecha_inicio y fecha_fin")
            
            if filtros.fecha_inicio > filtros.fecha_fin:
                raise FiltrosInvalidosError("La fecha de inicio debe ser anterior a la fecha de fin")
        
        if filtros.limite_tops <= 0:
            raise FiltrosInvalidosError("El límite para rankings debe ser mayor a 0")


class GetMetricasRapidasUseCase:
    """Caso de uso para obtener métricas rápidas del dashboard."""

    def __init__(self, dashboard_repository: IDashboardRepository):
        self.dashboard_repository = dashboard_repository

    async def execute(self) -> MetricasRapidas:
        """
        Obtiene las métricas rápidas para widgets pequeños.
        
        Returns:
            MetricasRapidas: Métricas básicas del sistema
        """
        try:
            metricas = await self.dashboard_repository.get_metricas_rapidas()
            return metricas
        except Exception as e:
            raise DashboardError(f"Error obteniendo métricas rápidas: {str(e)}")


class GetKPIsPrincipalesUseCase:
    """Caso de uso para obtener los KPIs principales."""

    def __init__(self, dashboard_repository: IDashboardRepository):
        self.dashboard_repository = dashboard_repository

    async def execute(
        self, 
        fecha_inicio: date, 
        fecha_fin: date,
        incluir_comparacion: bool = True
    ) -> KPIDashboard:
        """
        Obtiene los KPIs principales del dashboard.
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            incluir_comparacion: Si incluir comparación con período anterior
            
        Returns:
            KPIDashboard: Indicadores clave de rendimiento
        """
        try:
            # Validar fechas
            if fecha_inicio > fecha_fin:
                raise PeriodoInvalidoError("La fecha de inicio debe ser anterior a la fecha de fin")
            
            kpis = await self.dashboard_repository.get_kpis_principales(
                fecha_inicio, fecha_fin, incluir_comparacion
            )
            
            return kpis
            
        except PeriodoInvalidoError:
            raise
        except Exception as e:
            raise DashboardError(f"Error obteniendo KPIs principales: {str(e)}")


class GetVentasPorPeriodoUseCase:
    """Caso de uso para obtener ventas agrupadas por período."""

    def __init__(self, dashboard_repository: IDashboardRepository):
        self.dashboard_repository = dashboard_repository

    async def execute(
        self, 
        fecha_inicio: date, 
        fecha_fin: date,
        agrupacion: str = "mes"
    ) -> List[VentasPorPeriodo]:
        """
        Obtiene ventas agrupadas por período.
        
        Args:
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin
            agrupacion: Tipo de agrupación (dia, semana, mes, trimestre)
            
        Returns:
            List[VentasPorPeriodo]: Lista de ventas por período
        """
        try:
            # Validar fechas
            if fecha_inicio > fecha_fin:
                raise PeriodoInvalidoError("La fecha de inicio debe ser anterior a la fecha de fin")
            
            # Validar tipo de agrupación
            agrupaciones_validas = ["dia", "semana", "mes", "trimestre"]
            if agrupacion not in agrupaciones_validas:
                raise FiltrosInvalidosError(f"Agrupación debe ser una de: {', '.join(agrupaciones_validas)}")
            
            ventas = await self.dashboard_repository.get_ventas_por_periodo(
                fecha_inicio, fecha_fin, agrupacion
            )
            
            return ventas
            
        except (PeriodoInvalidoError, FiltrosInvalidosError):
            raise
        except Exception as e:
            raise DashboardError(f"Error obteniendo ventas por período: {str(e)}")


class GetProductosTopVentasUseCase:
    """Caso de uso para obtener productos más vendidos."""

    def __init__(self, dashboard_repository: IDashboardRepository):
        self.dashboard_repository = dashboard_repository

    async def execute(
        self, 
        fecha_inicio: date, 
        fecha_fin: date,
        limite: int = 10
    ) -> List[ProductoTopVentas]:
        """
        Obtiene los productos más vendidos.
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            limite: Número máximo de productos a retornar
            
        Returns:
            List[ProductoTopVentas]: Lista de productos más vendidos
        """
        try:
            # Validar fechas
            if fecha_inicio > fecha_fin:
                raise PeriodoInvalidoError("La fecha de inicio debe ser anterior a la fecha de fin")
            
            # Validar límite
            if limite <= 0:
                raise FiltrosInvalidosError("El límite debe ser mayor a 0")
            
            productos = await self.dashboard_repository.get_productos_top_ventas(
                fecha_inicio, fecha_fin, limite
            )
            
            return productos
            
        except (PeriodoInvalidoError, FiltrosInvalidosError):
            raise
        except Exception as e:
            raise DashboardError(f"Error obteniendo productos top ventas: {str(e)}")


class GetClientesTopVentasUseCase:
    """Caso de uso para obtener clientes con más compras."""

    def __init__(self, dashboard_repository: IDashboardRepository):
        self.dashboard_repository = dashboard_repository

    async def execute(
        self, 
        fecha_inicio: date, 
        fecha_fin: date,
        limite: int = 10
    ) -> List[ClienteTopVentas]:
        """
        Obtiene los clientes con más compras.
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            limite: Número máximo de clientes a retornar
            
        Returns:
            List[ClienteTopVentas]: Lista de mejores clientes
        """
        try:
            # Validar fechas
            if fecha_inicio > fecha_fin:
                raise PeriodoInvalidoError("La fecha de inicio debe ser anterior a la fecha de fin")
            
            # Validar límite
            if limite <= 0:
                raise FiltrosInvalidosError("El límite debe ser mayor a 0")
            
            clientes = await self.dashboard_repository.get_clientes_top_ventas(
                fecha_inicio, fecha_fin, limite
            )
            
            return clientes
            
        except (PeriodoInvalidoError, FiltrosInvalidosError):
            raise
        except Exception as e:
            raise DashboardError(f"Error obteniendo clientes top ventas: {str(e)}")


class GetResumenInventarioUseCase:
    """Caso de uso para obtener resumen de inventario."""

    def __init__(self, dashboard_repository: IDashboardRepository):
        self.dashboard_repository = dashboard_repository

    async def execute(
        self, 
        fecha_inicio: date, 
        fecha_fin: date
    ) -> List[MovimientoInventarioResumen]:
        """
        Obtiene resumen de movimientos de inventario.
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            
        Returns:
            List[MovimientoInventarioResumen]: Resumen por tipo de movimiento
        """
        try:
            # Validar fechas
            if fecha_inicio > fecha_fin:
                raise PeriodoInvalidoError("La fecha de inicio debe ser anterior a la fecha de fin")
            
            resumen = await self.dashboard_repository.get_resumen_inventario(fecha_inicio, fecha_fin)
            
            return resumen
            
        except PeriodoInvalidoError:
            raise
        except Exception as e:
            raise DashboardError(f"Error obteniendo resumen de inventario: {str(e)}")


class GetBalanceContableResumenUseCase:
    """Caso de uso para obtener resumen del balance contable."""

    def __init__(self, dashboard_repository: IDashboardRepository):
        self.dashboard_repository = dashboard_repository

    async def execute(
        self, 
        fecha_inicio: date, 
        fecha_fin: date,
        solo_principales: bool = True
    ) -> List[BalanceContableResumen]:
        """
        Obtiene resumen del balance contable.
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            solo_principales: Si solo incluir cuentas principales
            
        Returns:
            List[BalanceContableResumen]: Balance de cuentas contables
        """
        try:
            # Validar fechas
            if fecha_inicio > fecha_fin:
                raise PeriodoInvalidoError("La fecha de inicio debe ser anterior a la fecha de fin")
            
            balance = await self.dashboard_repository.get_balance_contable_resumen(
                fecha_inicio, fecha_fin, solo_principales
            )
            
            return balance
            
        except PeriodoInvalidoError:
            raise
        except Exception as e:
            raise DashboardError(f"Error obteniendo balance contable: {str(e)}")


class GetAlertasDashboardUseCase:
    """Caso de uso para obtener alertas del dashboard."""

    def __init__(self, dashboard_repository: IDashboardRepository):
        self.dashboard_repository = dashboard_repository

    async def execute(self) -> List[AlertaDashboard]:
        """
        Obtiene alertas relevantes para mostrar en el dashboard.
        
        Returns:
            List[AlertaDashboard]: Lista de alertas del sistema
        """
        try:
            alertas = await self.dashboard_repository.get_alertas_dashboard()
            return alertas
        except Exception as e:
            raise DashboardError(f"Error obteniendo alertas: {str(e)}")


# Casos de uso especializados para análisis

class AnalisisRentabilidadUseCase:
    """Caso de uso para análisis de rentabilidad."""

    def __init__(self, dashboard_repository: IDashboardRepository):
        self.dashboard_repository = dashboard_repository

    async def execute(self, fecha_inicio: date, fecha_fin: date) -> dict:
        """
        Realiza análisis de rentabilidad del período.
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            
        Returns:
            dict: Análisis de rentabilidad completo
        """
        try:
            # Validar fechas
            if fecha_inicio > fecha_fin:
                raise PeriodoInvalidoError("La fecha de inicio debe ser anterior a la fecha de fin")
            
            # Obtener datos base
            datos_ventas = await self.dashboard_repository.get_datos_ventas_periodo(fecha_inicio, fecha_fin)
            datos_contables = await self.dashboard_repository.get_datos_contables_periodo(fecha_inicio, fecha_fin)
            
            # Calcular métricas de rentabilidad
            ingresos = datos_contables.get("ingresos", Decimal('0'))
            gastos = datos_contables.get("gastos", Decimal('0'))
            utilidad_bruta = ingresos - gastos
            
            margen_bruto = await self.dashboard_repository.calcular_margen_utilidad(fecha_inicio, fecha_fin)
            rotacion_inventario = await self.dashboard_repository.calcular_rotacion_inventario(fecha_inicio, fecha_fin)
            
            # Obtener top productos y clientes
            productos_top = await self.dashboard_repository.get_productos_top_ventas(fecha_inicio, fecha_fin, 5)
            clientes_top = await self.dashboard_repository.get_clientes_top_ventas(fecha_inicio, fecha_fin, 5)
            
            return {
                "periodo": {
                    "fecha_inicio": fecha_inicio,
                    "fecha_fin": fecha_fin
                },
                "metricas_financieras": {
                    "ingresos_totales": ingresos,
                    "gastos_totales": gastos,
                    "utilidad_bruta": utilidad_bruta,
                    "margen_bruto_porcentaje": margen_bruto,
                    "rotacion_inventario": rotacion_inventario
                },
                "metricas_ventas": datos_ventas,
                "productos_mas_rentables": productos_top,
                "clientes_mas_rentables": clientes_top
            }
            
        except PeriodoInvalidoError:
            raise
        except Exception as e:
            raise DashboardError(f"Error en análisis de rentabilidad: {str(e)}")


class TendenciasVentasUseCase:
    """Caso de uso para análisis de tendencias de ventas."""

    def __init__(self, dashboard_repository: IDashboardRepository):
        self.dashboard_repository = dashboard_repository

    async def execute(self, fecha_inicio: date, fecha_fin: date, agrupacion: str = "mes") -> dict:
        """
        Analiza tendencias de ventas en el período.
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            agrupacion: Tipo de agrupación para el análisis
            
        Returns:
            dict: Análisis de tendencias completo
        """
        try:
            # Validar fechas
            if fecha_inicio > fecha_fin:
                raise PeriodoInvalidoError("La fecha de inicio debe ser anterior a la fecha de fin")
            
            # Obtener ventas por período
            ventas_periodo = await self.dashboard_repository.get_ventas_por_periodo(
                fecha_inicio, fecha_fin, agrupacion
            )
            
            if not ventas_periodo:
                raise DatosInsuficientesError("No hay datos suficientes para analizar tendencias")
            
            # Calcular tendencias
            tendencia_ventas = self._calcular_tendencia_ventas(ventas_periodo)
            crecimiento_promedio = self._calcular_crecimiento_promedio(ventas_periodo)
            mejor_periodo = max(ventas_periodo, key=lambda x: x.total_ventas)
            peor_periodo = min(ventas_periodo, key=lambda x: x.total_ventas)
            
            return {
                "periodo_analisis": {
                    "fecha_inicio": fecha_inicio,
                    "fecha_fin": fecha_fin,
                    "agrupacion": agrupacion,
                    "periodos_analizados": len(ventas_periodo)
                },
                "tendencia_general": tendencia_ventas,
                "crecimiento_promedio": crecimiento_promedio,
                "mejor_periodo": {
                    "periodo": mejor_periodo.periodo,
                    "total_ventas": mejor_periodo.total_ventas,
                    "numero_facturas": mejor_periodo.numero_facturas
                },
                "peor_periodo": {
                    "periodo": peor_periodo.periodo,
                    "total_ventas": peor_periodo.total_ventas,
                    "numero_facturas": peor_periodo.numero_facturas
                },
                "datos_detallados": ventas_periodo
            }
            
        except (PeriodoInvalidoError, DatosInsuficientesError):
            raise
        except Exception as e:
            raise DashboardError(f"Error en análisis de tendencias: {str(e)}")

    def _calcular_tendencia_ventas(self, ventas_periodo: List[VentasPorPeriodo]) -> str:
        """Calcula la tendencia general de las ventas."""
        if len(ventas_periodo) < 2:
            return "insuficientes_datos"
        
        # Calcular pendiente de la línea de tendencia
        n = len(ventas_periodo)
        sum_x = sum(range(n))
        sum_y = sum(float(v.total_ventas) for v in ventas_periodo)
        sum_xy = sum(i * float(v.total_ventas) for i, v in enumerate(ventas_periodo))
        sum_x2 = sum(i * i for i in range(n))
        
        pendiente = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        if pendiente > 1000:  # Crecimiento significativo
            return "creciente"
        elif pendiente < -1000:  # Decrecimiento significativo
            return "decreciente"
        else:
            return "estable"

    def _calcular_crecimiento_promedio(self, ventas_periodo: List[VentasPorPeriodo]) -> Optional[Decimal]:
        """Calcula el crecimiento promedio entre períodos."""
        if len(ventas_periodo) < 2:
            return None
        
        crecimientos = []
        for i in range(1, len(ventas_periodo)):
            actual = ventas_periodo[i].total_ventas
            anterior = ventas_periodo[i-1].total_ventas
            
            if anterior > 0:
                crecimiento = ((actual - anterior) / anterior) * 100
                crecimientos.append(float(crecimiento))
        
        if crecimientos:
            return Decimal(str(sum(crecimientos) / len(crecimientos)))
        return None


class EstadoSistemaUseCase:
    """Caso de uso para obtener el estado general del sistema."""

    def __init__(self, dashboard_repository: IDashboardRepository):
        self.dashboard_repository = dashboard_repository

    async def execute(self) -> dict:
        """
        Obtiene el estado general del sistema.
        
        Returns:
            dict: Estado completo del sistema
        """
        try:
            # Obtener métricas rápidas
            metricas = await self.dashboard_repository.get_metricas_rapidas()
            
            # Obtener alertas
            alertas = await self.dashboard_repository.get_alertas_dashboard()
            
            # Obtener datos de inventario
            hoy = date.today()
            datos_inventario = await self.dashboard_repository.get_datos_inventario_periodo(hoy, hoy)
            
            # Obtener datos de clientes
            datos_clientes = await self.dashboard_repository.get_datos_clientes_periodo(hoy, hoy)
            
            # Clasificar alertas por tipo
            alertas_criticas = [a for a in alertas if a.tipo == "danger"]
            alertas_advertencias = [a for a in alertas if a.tipo == "warning"]
            alertas_info = [a for a in alertas if a.tipo == "info"]
            
            # Calcular salud del sistema
            salud_sistema = self._calcular_salud_sistema(alertas_criticas, alertas_advertencias, datos_inventario)
            
            return {
                "fecha_consulta": hoy,
                "metricas_rapidas": metricas,
                "salud_sistema": salud_sistema,
                "alertas": {
                    "total": len(alertas),
                    "criticas": len(alertas_criticas),
                    "advertencias": len(alertas_advertencias),
                    "informativas": len(alertas_info)
                },
                "resumen_modulos": {
                    "inventario": {
                        "valor_total": datos_inventario.get("valor_inventario"),
                        "productos_activos": datos_inventario.get("productos_activos"),
                        "productos_sin_stock": datos_inventario.get("productos_sin_stock"),
                        "productos_stock_bajo": datos_inventario.get("productos_stock_bajo")
                    },
                    "clientes": {
                        "clientes_activos": datos_clientes.get("clientes_activos"),
                        "nuevos_clientes_hoy": datos_clientes.get("nuevos_clientes")
                    },
                    "ventas": {
                        "ventas_hoy": metricas.ventas_hoy,
                        "ventas_mes": metricas.ventas_mes,
                        "facturas_pendientes": metricas.facturas_pendientes
                    }
                }
            }
            
        except Exception as e:
            raise DashboardError(f"Error obteniendo estado del sistema: {str(e)}")

    def _calcular_salud_sistema(self, criticas: List[AlertaDashboard], advertencias: List[AlertaDashboard], datos_inventario: dict) -> dict:
        """Calcula un índice de salud del sistema."""
        puntuacion = 100
        
        # Penalizar por alertas críticas
        puntuacion -= len(criticas) * 15
        
        # Penalizar por alertas de advertencia
        puntuacion -= len(advertencias) * 5
        
        # Penalizar por productos sin stock
        productos_sin_stock = datos_inventario.get("productos_sin_stock", 0)
        if productos_sin_stock > 0:
            puntuacion -= min(productos_sin_stock * 2, 20)
        
        # Asegurar que esté entre 0 y 100
        puntuacion = max(0, min(100, puntuacion))
        
        # Clasificar salud
        if puntuacion >= 80:
            estado = "excelente"
            color = "green"
        elif puntuacion >= 60:
            estado = "bueno"
            color = "yellow"
        elif puntuacion >= 40:
            estado = "regular"
            color = "orange"
        else:
            estado = "critico"
            color = "red"
        
        return {
            "puntuacion": puntuacion,
            "estado": estado,
            "color": color,
            "descripcion": f"Sistema en estado {estado} ({puntuacion}/100)"
        }