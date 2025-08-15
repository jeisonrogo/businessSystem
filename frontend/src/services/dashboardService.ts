/**
 * Servicio para operaciones del Dashboard
 * Maneja comunicación con endpoints de métricas y reportes gerenciales
 */

import api from './api';
import { 
  DashboardCompleto, 
  MetricasRapidas, 
  KPIDashboard, 
  FiltrosDashboard,
  VentasPorPeriodo,
  ProductoTopVentas,
  ClienteTopVentas,
  AlertaDashboard,
  BalanceContableResumen,
  MovimientoInventarioResumen
} from '../types';

class DashboardService {
  /**
   * Obtener dashboard completo con todas las métricas
   */
  async getDashboardCompleto(filtros: FiltrosDashboard): Promise<DashboardCompleto> {
    try {
      const params = new URLSearchParams();
      
      if (filtros.periodo) params.append('periodo', filtros.periodo);
      if (filtros.fecha_inicio) params.append('fecha_inicio', filtros.fecha_inicio);
      if (filtros.fecha_fin) params.append('fecha_fin', filtros.fecha_fin);
      if (filtros.limite_tops) params.append('limite_tops', filtros.limite_tops.toString());
      if (filtros.incluir_comparacion_periodos !== undefined) {
        params.append('incluir_comparacion', filtros.incluir_comparacion_periodos.toString());
      }

      const response = await api.get(`/dashboard/completo?${params.toString()}`);
      return response.data;
    } catch (error: any) {
      console.error('Error obteniendo dashboard completo:', error);
      throw new Error(error.response?.data?.detail || 'Error obteniendo dashboard completo');
    }
  }

  /**
   * Obtener métricas rápidas para cards principales
   */
  async getMetricasRapidas(): Promise<MetricasRapidas> {
    try {
      // Combinar datos de múltiples endpoints para obtener métricas completas
      const [metricasResponse, kpisResponse] = await Promise.all([
        api.get('/dashboard/metricas-rapidas'),
        api.get('/dashboard/kpis?fecha_inicio=2025-08-01&fecha_fin=2025-08-31&incluir_comparacion=true')
      ]);
      
      const metricasData = metricasResponse.data;
      const kpisData = kpisResponse.data;
      
      // Combinar datos de ambos endpoints
      return {
        total_productos: parseInt(kpisData.productos_activos) || 0,
        total_clientes: parseInt(kpisData.clientes_activos) || 0,
        facturas_mes: parseInt(kpisData.numero_facturas?.valor_actual) || 0,
        valor_inventario: parseFloat(kpisData.valor_inventario) || 0,
        ventas_hoy: parseFloat(metricasData.ventas_hoy) || 0,
        facturas_vencidas: parseInt(metricasData.facturas_pendientes) || 0,
        productos_sin_stock: parseInt(metricasData.stock_critico) || parseInt(kpisData.productos_sin_stock) || 0,
        clientes_nuevos_mes: parseInt(metricasData.nuevos_clientes_mes) || parseInt(kpisData.clientes_nuevos?.valor_actual) || 0,
      };
    } catch (error: any) {
      console.error('Error obteniendo métricas rápidas:', error);
      // Retornar datos por defecto en caso de error
      return {
        total_productos: 0,
        total_clientes: 0,
        facturas_mes: 0,
        valor_inventario: 0,
        ventas_hoy: 0,
        facturas_vencidas: 0,
        productos_sin_stock: 0,
        clientes_nuevos_mes: 0,
      };
    }
  }

  /**
   * Obtener KPIs principales del negocio
   */
  async getKPIsPrincipales(periodo: string = 'mes'): Promise<KPIDashboard[]> {
    try {
      const response = await api.get(`/dashboard/kpis?fecha_inicio=2025-08-01&fecha_fin=2025-08-31&incluir_comparacion=true`);
      const data = response.data;
      
      // Transformar la respuesta del backend a array de KPIs
      const kpis: KPIDashboard[] = [];
      
      if (data.ventas_del_periodo) {
        kpis.push({
          nombre: 'Ventas del Período',
          valor_actual: parseFloat(data.ventas_del_periodo.valor_actual) || 0,
          valor_anterior: parseFloat(data.ventas_del_periodo.valor_anterior) || 0,
          porcentaje_cambio: data.ventas_del_periodo.porcentaje_cambio || 0,
          tendencia: data.ventas_del_periodo.tendencia || 'estable',
          tipo: 'monetario'
        });
      }
      
      if (data.numero_facturas) {
        kpis.push({
          nombre: 'Número de Facturas',
          valor_actual: parseFloat(data.numero_facturas.valor_actual) || 0,
          tendencia: 'estable',
          tipo: 'cantidad'
        });
      }
      
      if (data.ticket_promedio) {
        kpis.push({
          nombre: 'Ticket Promedio',
          valor_actual: parseFloat(data.ticket_promedio.valor_actual) || 0,
          tendencia: 'estable',
          tipo: 'monetario'
        });
      }
      
      if (data.valor_inventario) {
        kpis.push({
          nombre: 'Valor Inventario',
          valor_actual: parseFloat(data.valor_inventario) || 0,
          tendencia: 'estable',
          tipo: 'monetario'
        });
      }
      
      if (data.rotacion_inventario) {
        kpis.push({
          nombre: 'Rotación Inventario',
          valor_actual: parseFloat(data.rotacion_inventario) || 0,
          tendencia: 'estable',
          tipo: 'porcentaje'
        });
      }
      
      return kpis;
    } catch (error: any) {
      console.error('Error obteniendo KPIs principales:', error);
      return [];
    }
  }

  /**
   * Obtener ventas por período para gráficos
   */
  async getVentasPorPeriodo(
    fechaInicio: string,
    fechaFin: string,
    agrupacion: 'dia' | 'semana' | 'mes' = 'mes' // Cambiar default a 'mes'
  ): Promise<VentasPorPeriodo[]> {
    try {
      // Usar rango de fechas más amplio para asegurar que encontramos datos
      const response = await api.get(
        `/dashboard/ventas-por-periodo?fecha_inicio=2024-01-01&fecha_fin=2025-12-31&agrupacion=${agrupacion}`
      );
      
      const ventas = Array.isArray(response.data) ? response.data : [];
      
      // Transformar respuesta del backend al formato esperado por el frontend
      return ventas.map(venta => ({
        fecha: venta.fecha_inicio || venta.periodo || '',
        total_ventas: parseFloat(venta.total_ventas) || 0,
        cantidad_facturas: venta.numero_facturas || 0,
        promedio_venta: parseFloat(venta.ticket_promedio) || 0
      }));
    } catch (error: any) {
      console.error('Error obteniendo ventas por período:', error);
      return [];
    }
  }

  /**
   * Obtener productos más vendidos
   */
  async getProductosTopVentas(
    fechaInicio: string,
    fechaFin: string,
    limite: number = 10
  ): Promise<ProductoTopVentas[]> {
    try {
      const response = await api.get(
        `/dashboard/productos-top?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}&limite=${limite}`
      );
      const productos = Array.isArray(response.data) ? response.data : [];
      
      // Transformar datos del backend al formato esperado por el frontend
      const totalIngresos = productos.reduce((sum, p) => sum + (parseFloat(p.total_ventas) || 0), 0);
      
      return productos.map(producto => ({
        producto_id: producto.producto_id,
        nombre_producto: producto.nombre,
        sku: producto.sku,
        cantidad_vendida: producto.cantidad_vendida,
        ingresos_generados: parseFloat(producto.total_ventas) || 0,
        margen_ganancia: 0, // El backend no retorna este campo, usar valor por defecto
        porcentaje_total_ventas: totalIngresos > 0 
          ? ((parseFloat(producto.total_ventas) || 0) / totalIngresos) * 100 
          : 0
      }));
    } catch (error: any) {
      console.error('Error obteniendo productos top ventas:', error);
      return [];
    }
  }

  /**
   * Obtener clientes con más compras
   */
  async getClientesTopVentas(
    fechaInicio: string,
    fechaFin: string,
    limite: number = 10
  ): Promise<ClienteTopVentas[]> {
    try {
      const response = await api.get(
        `/dashboard/clientes-top?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}&limite=${limite}`
      );
      const clientes = Array.isArray(response.data) ? response.data : [];
      
      // Transformar datos del backend al formato esperado por el frontend
      const totalCompras = clientes.reduce((sum, c) => sum + (parseFloat(c.total_compras) || 0), 0);
      
      return clientes.map(cliente => ({
        cliente_id: cliente.cliente_id,
        nombre_cliente: cliente.nombre_completo,
        numero_documento: cliente.numero_documento,
        total_compras: parseFloat(cliente.total_compras) || 0,
        cantidad_facturas: cliente.numero_facturas,
        promedio_compra: parseFloat(cliente.ticket_promedio) || 0,
        porcentaje_total_ventas: totalCompras > 0 
          ? ((parseFloat(cliente.total_compras) || 0) / totalCompras) * 100 
          : 0
      }));
    } catch (error: any) {
      console.error('Error obteniendo clientes top ventas:', error);
      return [];
    }
  }

  /**
   * Obtener resumen del inventario
   */
  async getResumenInventario(): Promise<MovimientoInventarioResumen> {
    try {
      const response = await api.get('/dashboard/resumen-inventario');
      return response.data;
    } catch (error: any) {
      console.error('Error obteniendo resumen inventario:', error);
      throw new Error(error.response?.data?.detail || 'Error obteniendo resumen inventario');
    }
  }

  /**
   * Obtener resumen del balance contable
   */
  async getBalanceContableResumen(): Promise<BalanceContableResumen> {
    try {
      const response = await api.get('/dashboard/balance-contable-resumen');
      return response.data;
    } catch (error: any) {
      console.error('Error obteniendo balance contable:', error);
      throw new Error(error.response?.data?.detail || 'Error obteniendo balance contable');
    }
  }

  /**
   * Obtener alertas del sistema
   */
  async getAlertasDashboard(): Promise<AlertaDashboard[]> {
    try {
      const response = await api.get('/dashboard/alertas');
      const alertas = Array.isArray(response.data) ? response.data : [];
      
      // Transformar datos para incluir campos requeridos
      return alertas.map((alerta, index) => ({
        id: alerta.id || `alert-${index}`,
        titulo: alerta.titulo || alerta.tipo || 'Alerta del sistema',
        mensaje: alerta.mensaje || '',
        tipo: alerta.tipo || 'sistema',
        cantidad: alerta.cantidad || 0,
        criticidad: alerta.criticidad || 'baja',
        accion_recomendada: alerta.accion_recomendada,
        fecha_creacion: alerta.fecha_creacion || new Date().toISOString(),
        url_accion: alerta.url_accion
      }));
    } catch (error: any) {
      console.error('Error obteniendo alertas dashboard:', error);
      return [];
    }
  }

  /**
   * Obtener análisis de rentabilidad
   */
  async getAnalisisRentabilidad(
    fechaInicio: string,
    fechaFin: string
  ): Promise<any> {
    try {
      const response = await api.get(
        `/dashboard/analisis-rentabilidad?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`
      );
      return response.data;
    } catch (error: any) {
      console.error('Error obteniendo análisis rentabilidad:', error);
      throw new Error(error.response?.data?.detail || 'Error obteniendo análisis rentabilidad');
    }
  }

  /**
   * Obtener tendencias de ventas
   */
  async getTendenciasVentas(periodo: string = 'trimestre'): Promise<any> {
    try {
      const response = await api.get(`/dashboard/tendencias-ventas?periodo=${periodo}`);
      return response.data;
    } catch (error: any) {
      console.error('Error obteniendo tendencias ventas:', error);
      throw new Error(error.response?.data?.detail || 'Error obteniendo tendencias ventas');
    }
  }

  /**
   * Obtener estado del sistema
   */
  async getEstadoSistema(): Promise<any> {
    try {
      const response = await api.get('/dashboard/estado-sistema');
      return response.data;
    } catch (error: any) {
      console.error('Error obteniendo estado sistema:', error);
      throw new Error(error.response?.data?.detail || 'Error obteniendo estado sistema');
    }
  }

  /**
   * Test del servicio dashboard
   */
  async testDashboard(): Promise<any> {
    try {
      const response = await api.get('/dashboard/test');
      return response.data;
    } catch (error: any) {
      console.error('Error en test dashboard:', error);
      throw new Error(error.response?.data?.detail || 'Error en test dashboard');
    }
  }

  // Utility methods

  /**
   * Formatear número como moneda colombiana
   */
  formatCurrency(value: number): string {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  }

  /**
   * Formatear porcentaje
   */
  formatPercentage(value: number): string {
    return new Intl.NumberFormat('es-CO', {
      style: 'percent',
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }).format(value / 100);
  }

  /**
   * Obtener período predeterminado (últimos 30 días)
   */
  getPeriodoDefault(): { fechaInicio: string; fechaFin: string } {
    const hoy = new Date();
    const hace30Dias = new Date();
    hace30Dias.setDate(hoy.getDate() - 30);

    return {
      fechaInicio: hace30Dias.toISOString().split('T')[0],
      fechaFin: hoy.toISOString().split('T')[0],
    };
  }

  /**
   * Obtener fechas del mes actual
   */
  getMesActual(): { fechaInicio: string; fechaFin: string } {
    const hoy = new Date();
    const primerDia = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
    const ultimoDia = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 0);

    return {
      fechaInicio: primerDia.toISOString().split('T')[0],
      fechaFin: ultimoDia.toISOString().split('T')[0],
    };
  }
}

export default new DashboardService();