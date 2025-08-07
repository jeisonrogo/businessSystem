"""
Interfaz del repositorio para operaciones de dashboard y reportes gerenciales.
Define los contratos para acceso a datos consolidados de múltiples módulos.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from datetime import date
from decimal import Decimal

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
    MetricaPeriodo,
    PeriodoReporte
)


class IDashboardRepository(ABC):
    """
    Interfaz para el repositorio de dashboard.
    Define los métodos para obtener datos consolidados de múltiples módulos.
    """

    @abstractmethod
    async def get_dashboard_completo(self, filtros: FiltrosDashboard) -> DashboardCompleto:
        """
        Obtiene el dashboard completo con todas las métricas.
        
        Args:
            filtros: Filtros para personalizar el dashboard
            
        Returns:
            DashboardCompleto: Dashboard con todas las métricas
        """
        pass

    @abstractmethod
    async def get_metricas_rapidas(self) -> MetricasRapidas:
        """
        Obtiene métricas rápidas para widgets pequeños.
        
        Returns:
            MetricasRapidas: Métricas básicas del sistema
        """
        pass

    @abstractmethod
    async def get_kpis_principales(
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
        pass

    @abstractmethod
    async def get_ventas_por_periodo(
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
        pass

    @abstractmethod
    async def get_productos_top_ventas(
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
        pass

    @abstractmethod
    async def get_clientes_top_ventas(
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
        pass

    @abstractmethod
    async def get_resumen_inventario(
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
        pass

    @abstractmethod
    async def get_balance_contable_resumen(
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
        pass

    @abstractmethod
    async def get_alertas_dashboard(self) -> List[AlertaDashboard]:
        """
        Obtiene alertas relevantes para mostrar en el dashboard.
        
        Returns:
            List[AlertaDashboard]: Lista de alertas del sistema
        """
        pass

    # Métodos auxiliares para cálculos de períodos

    @abstractmethod
    async def calcular_periodo_anterior(
        self, 
        fecha_inicio: date, 
        fecha_fin: date
    ) -> Tuple[date, date]:
        """
        Calcula las fechas del período anterior para comparaciones.
        
        Args:
            fecha_inicio: Fecha inicio del período actual
            fecha_fin: Fecha fin del período actual
            
        Returns:
            Tuple[date, date]: Fechas inicio y fin del período anterior
        """
        pass

    @abstractmethod
    async def calcular_metrica_con_comparacion(
        self, 
        valor_actual: Decimal, 
        valor_anterior: Optional[Decimal]
    ) -> MetricaPeriodo:
        """
        Calcula una métrica con comparación de períodos.
        
        Args:
            valor_actual: Valor del período actual
            valor_anterior: Valor del período anterior (opcional)
            
        Returns:
            MetricaPeriodo: Métrica con comparación
        """
        pass

    # Métodos para datos específicos de módulos

    @abstractmethod
    async def get_datos_ventas_periodo(
        self, 
        fecha_inicio: date, 
        fecha_fin: date
    ) -> dict:
        """
        Obtiene datos de ventas para el período especificado.
        
        Args:
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin
            
        Returns:
            dict: Datos de ventas del período
        """
        pass

    @abstractmethod
    async def get_datos_inventario_periodo(
        self, 
        fecha_inicio: date, 
        fecha_fin: date
    ) -> dict:
        """
        Obtiene datos de inventario para el período especificado.
        
        Args:
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin
            
        Returns:
            dict: Datos de inventario del período
        """
        pass

    @abstractmethod
    async def get_datos_contables_periodo(
        self, 
        fecha_inicio: date, 
        fecha_fin: date
    ) -> dict:
        """
        Obtiene datos contables para el período especificado.
        
        Args:
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin
            
        Returns:
            dict: Datos contables del período
        """
        pass

    @abstractmethod
    async def get_datos_clientes_periodo(
        self, 
        fecha_inicio: date, 
        fecha_fin: date
    ) -> dict:
        """
        Obtiene datos de clientes para el período especificado.
        
        Args:
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin
            
        Returns:
            dict: Datos de clientes del período
        """
        pass

    # Métodos de agregación y cálculos

    @abstractmethod
    async def calcular_rotacion_inventario(
        self, 
        fecha_inicio: date, 
        fecha_fin: date
    ) -> Optional[Decimal]:
        """
        Calcula el índice de rotación de inventario.
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            
        Returns:
            Optional[Decimal]: Índice de rotación (None si no hay suficientes datos)
        """
        pass

    @abstractmethod
    async def calcular_margen_utilidad(
        self, 
        fecha_inicio: date, 
        fecha_fin: date
    ) -> Optional[Decimal]:
        """
        Calcula el margen de utilidad para el período.
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            
        Returns:
            Optional[Decimal]: Margen de utilidad en porcentaje
        """
        pass

    @abstractmethod
    async def generar_alertas_automaticas(self) -> List[AlertaDashboard]:
        """
        Genera alertas automáticas basadas en reglas del negocio.
        
        Returns:
            List[AlertaDashboard]: Lista de alertas generadas
        """
        pass