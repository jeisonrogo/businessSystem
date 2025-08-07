"""
Implementación del repositorio de dashboard usando PostgreSQL.
Consolida datos de múltiples módulos para generar reportes gerenciales.
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlmodel import Session, select, func, text, or_, and_
from sqlalchemy import extract, case

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
    MetricaPeriodo,
    PeriodoReporte
)

# Importar modelos para queries
from app.domain.models.facturacion import Factura, DetalleFactura, Cliente, EstadoFactura
from app.domain.models.product import Product
from app.domain.models.movimiento_inventario import MovimientoInventario, TipoMovimiento
from app.domain.models.contabilidad import CuentaContable, AsientoContable, DetalleAsiento
from app.domain.models.user import User


class SQLDashboardRepository(IDashboardRepository):
    """Implementación del repositorio de dashboard usando SQLModel y PostgreSQL."""

    def __init__(self, session: Session):
        self.session = session

    async def get_dashboard_completo(self, filtros: FiltrosDashboard) -> DashboardCompleto:
        """Obtiene el dashboard completo con todas las métricas."""
        # Calcular fechas según el período
        fecha_inicio, fecha_fin = await self._calcular_fechas_periodo(filtros.periodo, filtros.fecha_inicio, filtros.fecha_fin)
        
        # Generar KPIs principales
        kpis = await self.get_kpis_principales(fecha_inicio, fecha_fin, filtros.incluir_comparacion_periodos)
        
        # Obtener datos para gráficos
        ventas_por_periodo = await self.get_ventas_por_periodo(fecha_inicio, fecha_fin, "mes")
        productos_top = await self.get_productos_top_ventas(fecha_inicio, fecha_fin, filtros.limite_tops)
        clientes_top = await self.get_clientes_top_ventas(fecha_inicio, fecha_fin, filtros.limite_tops)
        
        # Datos de inventario
        movimientos_inventario = await self.get_resumen_inventario(fecha_inicio, fecha_fin)
        
        # Datos contables
        balance_principales = await self.get_balance_contable_resumen(fecha_inicio, fecha_fin, True)
        
        # Alertas
        alertas = await self.get_alertas_dashboard()

        return DashboardCompleto(
            fecha_generacion=datetime.now(),
            periodo=filtros.periodo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            kpis=kpis,
            ventas_por_periodo=ventas_por_periodo,
            productos_top=productos_top,
            clientes_top=clientes_top,
            movimientos_inventario=movimientos_inventario,
            balance_principales=balance_principales,
            alertas=alertas
        )

    async def get_metricas_rapidas(self) -> MetricasRapidas:
        """Obtiene métricas rápidas para widgets pequeños."""
        hoy = date.today()
        inicio_mes = date(hoy.year, hoy.month, 1)
        
        # Ventas de hoy
        ventas_hoy_query = select(func.coalesce(func.sum(Factura.total_factura), 0)).where(
            and_(
                func.date(Factura.fecha_emision) == hoy,
                Factura.estado != EstadoFactura.ANULADA
            )
        )
        ventas_hoy = self.session.exec(ventas_hoy_query).first() or Decimal('0')

        # Ventas del mes
        ventas_mes_query = select(func.coalesce(func.sum(Factura.total_factura), 0)).where(
            and_(
                Factura.fecha_emision >= inicio_mes,
                Factura.fecha_emision <= hoy,
                Factura.estado != EstadoFactura.ANULADA
            )
        )
        ventas_mes = self.session.exec(ventas_mes_query).first() or Decimal('0')

        # Facturas pendientes de pago
        facturas_pendientes_query = select(func.count(Factura.id)).where(
            Factura.estado == EstadoFactura.EMITIDA
        )
        facturas_pendientes = self.session.exec(facturas_pendientes_query).first() or 0

        # Productos con stock crítico (menor a 10)
        stock_critico_query = select(func.count(Product.id)).where(
            and_(
                Product.stock < 10,
                Product.is_active == True
            )
        )
        stock_critico = self.session.exec(stock_critico_query).first() or 0

        # Nuevos clientes del mes
        nuevos_clientes_query = select(func.count(Cliente.id)).where(
            and_(
                func.date(Cliente.created_at) >= inicio_mes,
                func.date(Cliente.created_at) <= hoy,
                Cliente.is_active == True
            )
        )
        nuevos_clientes = self.session.exec(nuevos_clientes_query).first() or 0

        return MetricasRapidas(
            ventas_hoy=ventas_hoy,
            ventas_mes=ventas_mes,
            facturas_pendientes=facturas_pendientes,
            stock_critico=stock_critico,
            nuevos_clientes_mes=nuevos_clientes
        )

    async def get_kpis_principales(
        self, 
        fecha_inicio: date, 
        fecha_fin: date,
        incluir_comparacion: bool = True
    ) -> KPIDashboard:
        """Obtiene los KPIs principales del dashboard."""
        # Calcular período anterior para comparaciones
        fecha_inicio_anterior, fecha_fin_anterior = await self.calcular_periodo_anterior(fecha_inicio, fecha_fin)

        # 1. Ventas del período
        ventas_actual = await self._get_ventas_periodo(fecha_inicio, fecha_fin)
        ventas_anterior = await self._get_ventas_periodo(fecha_inicio_anterior, fecha_fin_anterior) if incluir_comparacion else None
        ventas_del_periodo = await self.calcular_metrica_con_comparacion(ventas_actual, ventas_anterior)

        # 2. Número de facturas
        facturas_actual = await self._get_numero_facturas_periodo(fecha_inicio, fecha_fin)
        facturas_anterior = await self._get_numero_facturas_periodo(fecha_inicio_anterior, fecha_fin_anterior) if incluir_comparacion else None
        numero_facturas = await self.calcular_metrica_con_comparacion(Decimal(facturas_actual), Decimal(facturas_anterior) if facturas_anterior else None)

        # 3. Ticket promedio
        ticket_actual = ventas_actual / Decimal(facturas_actual) if facturas_actual > 0 else Decimal('0')
        ticket_anterior = (ventas_anterior / Decimal(facturas_anterior)) if (facturas_anterior and facturas_anterior > 0) else None
        ticket_promedio = await self.calcular_metrica_con_comparacion(ticket_actual, ticket_anterior)

        # 4. Cartera pendiente y vencida
        cartera_pendiente, cartera_vencida = await self._get_cartera_info()

        # 5. Inventario
        valor_inventario = await self._get_valor_inventario()
        productos_activos = await self._get_productos_activos()
        productos_sin_stock = await self._get_productos_sin_stock()
        productos_stock_bajo = await self._get_productos_stock_bajo()
        rotacion_inventario = await self.calcular_rotacion_inventario(fecha_inicio, fecha_fin)

        # 6. Clientes
        clientes_activos = await self._get_clientes_activos()
        nuevos_clientes_actual = await self._get_nuevos_clientes_periodo(fecha_inicio, fecha_fin)
        nuevos_clientes_anterior = await self._get_nuevos_clientes_periodo(fecha_inicio_anterior, fecha_fin_anterior) if incluir_comparacion else None
        clientes_nuevos = await self.calcular_metrica_con_comparacion(Decimal(nuevos_clientes_actual), Decimal(nuevos_clientes_anterior) if nuevos_clientes_anterior else None)

        # 7. Contabilidad
        ingresos_actual = await self._get_ingresos_periodo(fecha_inicio, fecha_fin)
        ingresos_anterior = await self._get_ingresos_periodo(fecha_inicio_anterior, fecha_fin_anterior) if incluir_comparacion else None
        ingresos_periodo = await self.calcular_metrica_con_comparacion(ingresos_actual, ingresos_anterior)

        gastos_actual = await self._get_gastos_periodo(fecha_inicio, fecha_fin)
        gastos_anterior = await self._get_gastos_periodo(fecha_inicio_anterior, fecha_fin_anterior) if incluir_comparacion else None
        gastos_periodo = await self.calcular_metrica_con_comparacion(gastos_actual, gastos_anterior)

        utilidad_actual = ingresos_actual - gastos_actual
        utilidad_anterior = (ingresos_anterior - gastos_anterior) if (ingresos_anterior and gastos_anterior) else None
        utilidad_bruta = await self.calcular_metrica_con_comparacion(utilidad_actual, utilidad_anterior)

        margen_utilidad = await self.calcular_margen_utilidad(fecha_inicio, fecha_fin)

        return KPIDashboard(
            ventas_del_periodo=ventas_del_periodo,
            numero_facturas=numero_facturas,
            ticket_promedio=ticket_promedio,
            cartera_pendiente=cartera_pendiente,
            cartera_vencida=cartera_vencida,
            valor_inventario=valor_inventario,
            productos_activos=productos_activos,
            productos_sin_stock=productos_sin_stock,
            productos_stock_bajo=productos_stock_bajo,
            rotacion_inventario=rotacion_inventario,
            clientes_activos=clientes_activos,
            clientes_nuevos=clientes_nuevos,
            ingresos_periodo=ingresos_periodo,
            gastos_periodo=gastos_periodo,
            utilidad_bruta=utilidad_bruta,
            margen_utilidad=margen_utilidad
        )

    async def get_ventas_por_periodo(
        self, 
        fecha_inicio: date, 
        fecha_fin: date,
        agrupacion: str = "mes"
    ) -> List[VentasPorPeriodo]:
        """Obtiene ventas agrupadas por período."""
        if agrupacion == "mes":
            # Agrupar por mes
            query = select(
                extract('year', Factura.fecha_emision).label('anio'),
                extract('month', Factura.fecha_emision).label('mes'),
                func.sum(Factura.total_factura).label('total_ventas'),
                func.count(Factura.id).label('numero_facturas')
            ).where(
                and_(
                    Factura.fecha_emision >= fecha_inicio,
                    Factura.fecha_emision <= fecha_fin,
                    Factura.estado != EstadoFactura.ANULADA
                )
            ).group_by('anio', 'mes').order_by('anio', 'mes')

            results = self.session.exec(query).all()
            
            ventas_por_periodo = []
            for row in results:
                anio, mes = int(row.anio), int(row.mes)
                fecha_inicio_mes = date(anio, mes, 1)
                fecha_fin_mes = date(anio + (mes // 12), (mes % 12) + 1, 1) - timedelta(days=1) if mes < 12 else date(anio + 1, 1, 1) - timedelta(days=1)
                
                total_ventas = row.total_ventas or Decimal('0')
                numero_facturas = row.numero_facturas or 0
                ticket_promedio = total_ventas / Decimal(numero_facturas) if numero_facturas > 0 else Decimal('0')

                meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                
                ventas_por_periodo.append(VentasPorPeriodo(
                    periodo=f"{meses[mes-1]} {anio}",
                    fecha_inicio=fecha_inicio_mes,
                    fecha_fin=fecha_fin_mes,
                    total_ventas=total_ventas,
                    numero_facturas=numero_facturas,
                    ticket_promedio=ticket_promedio
                ))

            return ventas_por_periodo
        
        # Para otros tipos de agrupación, implementar lógica similar
        return []

    async def get_productos_top_ventas(
        self, 
        fecha_inicio: date, 
        fecha_fin: date,
        limite: int = 10
    ) -> List[ProductoTopVentas]:
        """Obtiene los productos más vendidos."""
        query = select(
            Product.id,
            Product.sku,
            Product.nombre,
            func.sum(DetalleFactura.cantidad).label('cantidad_vendida'),
            func.sum(DetalleFactura.total_item).label('total_ventas'),
            func.count(func.distinct(Factura.id)).label('numero_facturas')
        ).join(
            DetalleFactura, Product.id == DetalleFactura.producto_id
        ).join(
            Factura, DetalleFactura.factura_id == Factura.id
        ).where(
            and_(
                Factura.fecha_emision >= fecha_inicio,
                Factura.fecha_emision <= fecha_fin,
                Factura.estado != EstadoFactura.ANULADA,
                Product.is_active == True
            )
        ).group_by(
            Product.id, Product.sku, Product.nombre
        ).order_by(
            func.sum(DetalleFactura.total_item).desc()
        ).limit(limite)

        results = self.session.exec(query).all()
        
        productos_top = []
        for row in results:
            cantidad_vendida = row.cantidad_vendida or 0
            total_ventas = row.total_ventas or Decimal('0')
            numero_facturas = row.numero_facturas or 0
            ticket_promedio = total_ventas / Decimal(numero_facturas) if numero_facturas > 0 else Decimal('0')

            productos_top.append(ProductoTopVentas(
                producto_id=str(row.id),
                sku=row.sku,
                nombre=row.nombre,
                cantidad_vendida=cantidad_vendida,
                total_ventas=total_ventas,
                numero_facturas=numero_facturas,
                ticket_promedio=ticket_promedio
            ))

        return productos_top

    async def get_clientes_top_ventas(
        self, 
        fecha_inicio: date, 
        fecha_fin: date,
        limite: int = 10
    ) -> List[ClienteTopVentas]:
        """Obtiene los clientes con más compras."""
        query = select(
            Cliente.id,
            Cliente.numero_documento,
            Cliente.nombre_completo,
            func.sum(Factura.total_factura).label('total_compras'),
            func.count(Factura.id).label('numero_facturas'),
            func.max(Factura.fecha_emision).label('ultima_compra')
        ).join(
            Factura, Cliente.id == Factura.cliente_id
        ).where(
            and_(
                Factura.fecha_emision >= fecha_inicio,
                Factura.fecha_emision <= fecha_fin,
                Factura.estado != EstadoFactura.ANULADA,
                Cliente.is_active == True
            )
        ).group_by(
            Cliente.id, Cliente.numero_documento, Cliente.nombre_completo
        ).order_by(
            func.sum(Factura.total_factura).desc()
        ).limit(limite)

        results = self.session.exec(query).all()
        
        clientes_top = []
        for row in results:
            total_compras = row.total_compras or Decimal('0')
            numero_facturas = row.numero_facturas or 0
            ticket_promedio = total_compras / Decimal(numero_facturas) if numero_facturas > 0 else Decimal('0')

            clientes_top.append(ClienteTopVentas(
                cliente_id=str(row.id),
                numero_documento=row.numero_documento,
                nombre_completo=row.nombre_completo,
                total_compras=total_compras,
                numero_facturas=numero_facturas,
                ticket_promedio=ticket_promedio,
                ultima_compra=row.ultima_compra
            ))

        return clientes_top

    async def get_resumen_inventario(
        self, 
        fecha_inicio: date, 
        fecha_fin: date
    ) -> List[MovimientoInventarioResumen]:
        """Obtiene resumen de movimientos de inventario."""
        query = select(
            MovimientoInventario.tipo_movimiento,
            func.count(MovimientoInventario.id).label('cantidad_movimientos'),
            func.sum(MovimientoInventario.cantidad).label('cantidad_total'),
            func.sum(MovimientoInventario.cantidad * MovimientoInventario.precio_unitario).label('valor_total')
        ).where(
            and_(
                func.date(MovimientoInventario.created_at) >= fecha_inicio,
                func.date(MovimientoInventario.created_at) <= fecha_fin
            )
        ).group_by(MovimientoInventario.tipo_movimiento)

        results = self.session.exec(query).all()
        
        resumen = []
        for row in results:
            resumen.append(MovimientoInventarioResumen(
                tipo_movimiento=row.tipo_movimiento,
                cantidad_movimientos=row.cantidad_movimientos or 0,
                cantidad_total=row.cantidad_total or 0,
                valor_total=row.valor_total or Decimal('0')
            ))

        return resumen

    async def get_balance_contable_resumen(
        self, 
        fecha_inicio: date, 
        fecha_fin: date,
        solo_principales: bool = True
    ) -> List[BalanceContableResumen]:
        """Obtiene resumen del balance contable."""
        where_conditions = [
            func.date(AsientoContable.fecha) >= fecha_inicio,
            func.date(AsientoContable.fecha) <= fecha_fin
        ]
        
        if solo_principales:
            where_conditions.append(func.length(CuentaContable.codigo) <= 4)  # Solo cuentas principales

        query = select(
            CuentaContable.codigo,
            CuentaContable.nombre,
            CuentaContable.tipo_cuenta.label('tipo'),
            func.sum(
                case(
                    (DetalleAsiento.tipo_movimiento == 'DEBITO', DetalleAsiento.monto),
                    else_=0
                )
            ).label('total_debitos'),
            func.sum(
                case(
                    (DetalleAsiento.tipo_movimiento == 'CREDITO', DetalleAsiento.monto),
                    else_=0
                )
            ).label('total_creditos')
        ).join(
            DetalleAsiento, CuentaContable.id == DetalleAsiento.cuenta_id
        ).join(
            AsientoContable, DetalleAsiento.asiento_id == AsientoContable.id
        ).where(
            and_(*where_conditions)
        ).group_by(
            CuentaContable.codigo, CuentaContable.nombre, CuentaContable.tipo_cuenta
        ).order_by(CuentaContable.codigo)

        results = self.session.exec(query).all()
        
        balance = []
        for row in results:
            total_debitos = row.total_debitos or Decimal('0')
            total_creditos = row.total_creditos or Decimal('0')
            saldo = total_debitos - total_creditos

            balance.append(BalanceContableResumen(
                codigo_cuenta=row.codigo,
                nombre_cuenta=row.nombre,
                tipo_cuenta=str(row.tipo),
                total_debitos=total_debitos,
                total_creditos=total_creditos,
                saldo=saldo
            ))

        return balance

    async def get_alertas_dashboard(self) -> List[AlertaDashboard]:
        """Obtiene alertas relevantes para mostrar en el dashboard."""
        alertas = await self.generar_alertas_automaticas()
        return alertas

    # Métodos auxiliares

    async def calcular_periodo_anterior(
        self, 
        fecha_inicio: date, 
        fecha_fin: date
    ) -> Tuple[date, date]:
        """Calcula las fechas del período anterior."""
        dias_periodo = (fecha_fin - fecha_inicio).days + 1
        fecha_fin_anterior = fecha_inicio - timedelta(days=1)
        fecha_inicio_anterior = fecha_fin_anterior - timedelta(days=dias_periodo - 1)
        return fecha_inicio_anterior, fecha_fin_anterior

    async def calcular_metrica_con_comparacion(
        self, 
        valor_actual: Decimal, 
        valor_anterior: Optional[Decimal]
    ) -> MetricaPeriodo:
        """Calcula una métrica con comparación de períodos."""
        porcentaje_cambio = None
        tendencia = None

        if valor_anterior is not None and valor_anterior != 0:
            porcentaje_cambio = ((valor_actual - valor_anterior) / valor_anterior) * 100
            if porcentaje_cambio > 5:
                tendencia = "up"
            elif porcentaje_cambio < -5:
                tendencia = "down"
            else:
                tendencia = "stable"

        return MetricaPeriodo(
            valor_actual=valor_actual,
            valor_anterior=valor_anterior,
            porcentaje_cambio=porcentaje_cambio,
            tendencia=tendencia
        )

    async def _calcular_fechas_periodo(
        self,
        periodo: PeriodoReporte,
        fecha_inicio_custom: Optional[date] = None,
        fecha_fin_custom: Optional[date] = None
    ) -> Tuple[date, date]:
        """Calcula las fechas según el tipo de período."""
        hoy = date.today()
        
        if periodo == PeriodoReporte.PERSONALIZADO:
            if fecha_inicio_custom and fecha_fin_custom:
                return fecha_inicio_custom, fecha_fin_custom
            else:
                periodo = PeriodoReporte.MES  # Default a mes si no hay fechas custom
        
        if periodo == PeriodoReporte.HOY:
            return hoy, hoy
        elif periodo == PeriodoReporte.SEMANA:
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            return inicio_semana, hoy
        elif periodo == PeriodoReporte.MES:
            inicio_mes = date(hoy.year, hoy.month, 1)
            return inicio_mes, hoy
        elif periodo == PeriodoReporte.TRIMESTRE:
            mes_inicio_trimestre = ((hoy.month - 1) // 3) * 3 + 1
            inicio_trimestre = date(hoy.year, mes_inicio_trimestre, 1)
            return inicio_trimestre, hoy
        elif periodo == PeriodoReporte.SEMESTRE:
            mes_inicio_semestre = 1 if hoy.month <= 6 else 7
            inicio_semestre = date(hoy.year, mes_inicio_semestre, 1)
            return inicio_semestre, hoy
        elif periodo == PeriodoReporte.ANO:
            inicio_ano = date(hoy.year, 1, 1)
            return inicio_ano, hoy
        
        # Default: mes actual
        inicio_mes = date(hoy.year, hoy.month, 1)
        return inicio_mes, hoy

    # Métodos privados para obtener datos específicos

    async def _get_ventas_periodo(self, fecha_inicio: date, fecha_fin: date) -> Decimal:
        """Obtiene el total de ventas del período."""
        query = select(func.coalesce(func.sum(Factura.total_factura), 0)).where(
            and_(
                Factura.fecha_emision >= fecha_inicio,
                Factura.fecha_emision <= fecha_fin,
                Factura.estado != EstadoFactura.ANULADA
            )
        )
        result = self.session.exec(query).first()
        return Decimal(str(result)) if result else Decimal('0')

    async def _get_numero_facturas_periodo(self, fecha_inicio: date, fecha_fin: date) -> int:
        """Obtiene el número de facturas del período."""
        query = select(func.count(Factura.id)).where(
            and_(
                Factura.fecha_emision >= fecha_inicio,
                Factura.fecha_emision <= fecha_fin,
                Factura.estado != EstadoFactura.ANULADA
            )
        )
        return self.session.exec(query).first() or 0

    async def _get_cartera_info(self) -> Tuple[Decimal, Decimal]:
        """Obtiene información de cartera pendiente y vencida."""
        hoy = date.today()
        
        # Cartera pendiente total
        pendiente_query = select(func.coalesce(func.sum(Factura.total_factura), 0)).where(
            Factura.estado == EstadoFactura.EMITIDA
        )
        cartera_pendiente = Decimal(str(self.session.exec(pendiente_query).first() or 0))

        # Cartera vencida
        vencida_query = select(func.coalesce(func.sum(Factura.total_factura), 0)).where(
            and_(
                Factura.estado == EstadoFactura.EMITIDA,
                or_(
                    Factura.fecha_vencimiento.is_(None),  # Facturas sin fecha de vencimiento se consideran vencidas después de 30 días
                    Factura.fecha_vencimiento < hoy
                )
            )
        )
        cartera_vencida = Decimal(str(self.session.exec(vencida_query).first() or 0))

        return cartera_pendiente, cartera_vencida

    async def _get_valor_inventario(self) -> Decimal:
        """Obtiene el valor total del inventario."""
        query = select(func.coalesce(func.sum(Product.stock * Product.precio_base), 0)).where(
            Product.is_active == True
        )
        result = self.session.exec(query).first()
        return Decimal(str(result)) if result else Decimal('0')

    async def _get_productos_activos(self) -> int:
        """Obtiene el número de productos activos."""
        query = select(func.count(Product.id)).where(Product.is_active == True)
        return self.session.exec(query).first() or 0

    async def _get_productos_sin_stock(self) -> int:
        """Obtiene el número de productos sin stock."""
        query = select(func.count(Product.id)).where(
            and_(Product.stock == 0, Product.is_active == True)
        )
        return self.session.exec(query).first() or 0

    async def _get_productos_stock_bajo(self) -> int:
        """Obtiene el número de productos con stock bajo."""
        query = select(func.count(Product.id)).where(
            and_(Product.stock > 0, Product.stock < 10, Product.is_active == True)
        )
        return self.session.exec(query).first() or 0

    async def _get_clientes_activos(self) -> int:
        """Obtiene el número de clientes activos."""
        query = select(func.count(Cliente.id)).where(Cliente.is_active == True)
        return self.session.exec(query).first() or 0

    async def _get_nuevos_clientes_periodo(self, fecha_inicio: date, fecha_fin: date) -> int:
        """Obtiene el número de nuevos clientes del período."""
        query = select(func.count(Cliente.id)).where(
            and_(
                func.date(Cliente.created_at) >= fecha_inicio,
                func.date(Cliente.created_at) <= fecha_fin,
                Cliente.is_active == True
            )
        )
        return self.session.exec(query).first() or 0

    async def _get_ingresos_periodo(self, fecha_inicio: date, fecha_fin: date) -> Decimal:
        """Obtiene los ingresos del período desde contabilidad."""
        # Cuentas de ingresos (código 4)
        query = select(func.coalesce(func.sum(DetalleAsiento.monto), 0)).join(
            AsientoContable, DetalleAsiento.asiento_id == AsientoContable.id
        ).join(
            CuentaContable, DetalleAsiento.cuenta_id == CuentaContable.id
        ).where(
            and_(
                func.date(AsientoContable.fecha) >= fecha_inicio,
                func.date(AsientoContable.fecha) <= fecha_fin,
                CuentaContable.codigo.like('4%'),  # Cuentas de ingresos
                DetalleAsiento.tipo_movimiento == 'CREDITO'
            )
        )
        result = self.session.exec(query).first()
        return Decimal(str(result)) if result else Decimal('0')

    async def _get_gastos_periodo(self, fecha_inicio: date, fecha_fin: date) -> Decimal:
        """Obtiene los gastos del período desde contabilidad."""
        # Cuentas de gastos (código 5)
        query = select(func.coalesce(func.sum(DetalleAsiento.monto), 0)).join(
            AsientoContable, DetalleAsiento.asiento_id == AsientoContable.id
        ).join(
            CuentaContable, DetalleAsiento.cuenta_id == CuentaContable.id
        ).where(
            and_(
                func.date(AsientoContable.fecha) >= fecha_inicio,
                func.date(AsientoContable.fecha) <= fecha_fin,
                CuentaContable.codigo.like('5%'),  # Cuentas de gastos
                DetalleAsiento.tipo_movimiento == 'DEBITO'
            )
        )
        result = self.session.exec(query).first()
        return Decimal(str(result)) if result else Decimal('0')

    # Implementación de métodos restantes

    async def get_datos_ventas_periodo(self, fecha_inicio: date, fecha_fin: date) -> dict:
        """Obtiene datos de ventas para el período especificado."""
        total_ventas = await self._get_ventas_periodo(fecha_inicio, fecha_fin)
        numero_facturas = await self._get_numero_facturas_periodo(fecha_inicio, fecha_fin)
        ticket_promedio = total_ventas / Decimal(numero_facturas) if numero_facturas > 0 else Decimal('0')
        
        return {
            "total_ventas": total_ventas,
            "numero_facturas": numero_facturas,
            "ticket_promedio": ticket_promedio
        }

    async def get_datos_inventario_periodo(self, fecha_inicio: date, fecha_fin: date) -> dict:
        """Obtiene datos de inventario para el período especificado."""
        valor_total = await self._get_valor_inventario()
        productos_activos = await self._get_productos_activos()
        sin_stock = await self._get_productos_sin_stock()
        stock_bajo = await self._get_productos_stock_bajo()
        
        return {
            "valor_inventario": valor_total,
            "productos_activos": productos_activos,
            "productos_sin_stock": sin_stock,
            "productos_stock_bajo": stock_bajo
        }

    async def get_datos_contables_periodo(self, fecha_inicio: date, fecha_fin: date) -> dict:
        """Obtiene datos contables para el período especificado."""
        ingresos = await self._get_ingresos_periodo(fecha_inicio, fecha_fin)
        gastos = await self._get_gastos_periodo(fecha_inicio, fecha_fin)
        utilidad = ingresos - gastos
        
        return {
            "ingresos": ingresos,
            "gastos": gastos,
            "utilidad_bruta": utilidad
        }

    async def get_datos_clientes_periodo(self, fecha_inicio: date, fecha_fin: date) -> dict:
        """Obtiene datos de clientes para el período especificado."""
        activos = await self._get_clientes_activos()
        nuevos = await self._get_nuevos_clientes_periodo(fecha_inicio, fecha_fin)
        
        return {
            "clientes_activos": activos,
            "nuevos_clientes": nuevos
        }

    async def calcular_rotacion_inventario(self, fecha_inicio: date, fecha_fin: date) -> Optional[Decimal]:
        """Calcula el índice de rotación de inventario."""
        # Costo de mercancía vendida en el período
        costo_vendido_query = select(func.coalesce(func.sum(
            DetalleFactura.cantidad * Product.precio_base
        ), 0)).join(
            Product, DetalleFactura.producto_id == Product.id
        ).join(
            Factura, DetalleFactura.factura_id == Factura.id
        ).where(
            and_(
                Factura.fecha_emision >= fecha_inicio,
                Factura.fecha_emision <= fecha_fin,
                Factura.estado != EstadoFactura.ANULADA
            )
        )
        
        costo_vendido = self.session.exec(costo_vendido_query).first()
        if not costo_vendido or costo_vendido == 0:
            return None
        
        # Inventario promedio
        inventario_actual = await self._get_valor_inventario()
        if inventario_actual == 0:
            return None
        
        # Rotación = Costo vendido / Inventario promedio
        rotacion = Decimal(str(costo_vendido)) / inventario_actual
        return rotacion

    async def calcular_margen_utilidad(self, fecha_inicio: date, fecha_fin: date) -> Optional[Decimal]:
        """Calcula el margen de utilidad para el período."""
        ingresos = await self._get_ingresos_periodo(fecha_inicio, fecha_fin)
        gastos = await self._get_gastos_periodo(fecha_inicio, fecha_fin)
        
        if ingresos == 0:
            return None
        
        utilidad = ingresos - gastos
        margen = (utilidad / ingresos) * 100
        return margen

    async def generar_alertas_automaticas(self) -> List[AlertaDashboard]:
        """Genera alertas automáticas basadas en reglas del negocio."""
        alertas = []
        
        # Alerta de productos sin stock
        productos_sin_stock = await self._get_productos_sin_stock()
        if productos_sin_stock > 0:
            alertas.append(AlertaDashboard(
                tipo="warning",
                titulo="Productos sin stock",
                mensaje=f"Hay {productos_sin_stock} productos sin stock disponible",
                fecha=datetime.now(),
                modulo="inventario",
                requiere_accion=True
            ))
        
        # Alerta de stock bajo
        productos_stock_bajo = await self._get_productos_stock_bajo()
        if productos_stock_bajo > 0:
            alertas.append(AlertaDashboard(
                tipo="info",
                titulo="Stock bajo",
                mensaje=f"{productos_stock_bajo} productos tienen stock bajo (menos de 10 unidades)",
                fecha=datetime.now(),
                modulo="inventario",
                requiere_accion=False
            ))
        
        # Alerta de cartera vencida
        cartera_pendiente, cartera_vencida = await self._get_cartera_info()
        if cartera_vencida > 0:
            alertas.append(AlertaDashboard(
                tipo="danger",
                titulo="Cartera vencida",
                mensaje=f"Hay ${cartera_vencida:,.2f} en cartera vencida por cobrar",
                fecha=datetime.now(),
                modulo="facturacion",
                requiere_accion=True
            ))
        
        # Alerta de facturas pendientes
        facturas_pendientes_query = select(func.count(Factura.id)).where(
            Factura.estado == EstadoFactura.EMITIDA
        )
        facturas_pendientes = self.session.exec(facturas_pendientes_query).first() or 0
        
        if facturas_pendientes > 10:
            alertas.append(AlertaDashboard(
                tipo="warning",
                titulo="Muchas facturas pendientes",
                mensaje=f"Tienes {facturas_pendientes} facturas pendientes de pago",
                fecha=datetime.now(),
                modulo="facturacion",
                requiere_accion=False
            ))
        
        return alertas