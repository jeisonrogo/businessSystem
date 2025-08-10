/**
 * Servicio para gestión de facturas
 * Maneja todas las operaciones CRUD, reportes y funcionalidades especializadas
 */

import { apiRequest } from './api';
import { ENDPOINTS } from '../config/api';
import {
  Invoice,
  InvoiceDetail,
  InvoiceStatus,
  InvoiceType,
  Client,
  Product,
  PaginatedResponse,
  QueryParams,
  DateRangeParams
} from '../types';

// Interfaces específicas para facturas
export interface InvoiceCreate {
  cliente_id: string;
  tipo_factura: InvoiceType;
  fecha_emision: string;
  fecha_vencimiento?: string;
  observaciones?: string;
  detalles: InvoiceDetailCreate[];
}

export interface InvoiceDetailCreate {
  producto_id: string;
  descripcion_producto: string;
  cantidad: number;
  precio_unitario: number;
  descuento_porcentaje: number;
  impuesto_porcentaje: number;
}

export interface InvoiceUpdate {
  fecha_vencimiento?: string;
  observaciones?: string;
  detalles?: InvoiceDetailCreate[];
}

export interface InvoiceListParams extends QueryParams, DateRangeParams {
  cliente_id?: string;
  estado?: InvoiceStatus;
  tipo_factura?: InvoiceType;
  numero_factura?: string;
}

export interface SalesReportParams extends DateRangeParams {
  agrupar_por?: 'dia' | 'semana' | 'mes';
}

export interface SalesSummary {
  total_facturas: number;
  total_ventas: number;
  total_impuestos: number;
  total_descuentos: number;
  promedio_factura: number;
  periodo: string;
}

export interface TopProduct {
  producto_id: string;
  nombre: string;
  sku: string;
  cantidad_vendida: number;
  valor_vendido: number;
  numero_facturas: number;
}

export interface TopClient {
  cliente_id: string;
  nombre_completo: string;
  numero_documento: string;
  total_facturas: number;
  valor_total_compras: number;
  ultima_compra: string;
}

export interface PortfolioValue {
  total_cartera: number;
  cartera_vigente: number;
  cartera_vencida: number;
  numero_facturas_pendientes: number;
  cliente_mayor_deuda?: {
    cliente_id: string;
    nombre: string;
    valor_pendiente: number;
  };
}

export interface InvoiceStatistics {
  total_facturas_emitidas: number;
  total_facturas_pagadas: number;
  total_facturas_anuladas: number;
  valor_total_ventas: number;
  valor_pendiente_cobro: number;
  promedio_dias_pago: number;
  productos_mas_vendidos: TopProduct[];
  clientes_top: TopClient[];
}

export interface PaymentData {
  forma_pago: string;
  fecha_pago?: string;
  observaciones?: string;
  valor_recibido?: number;
}

export class InvoicesService {
  /**
   * Crear una nueva factura
   */
  static async createInvoice(invoiceData: InvoiceCreate): Promise<Invoice> {
    try {
      const response = await apiRequest.post<Invoice>(ENDPOINTS.INVOICES.BASE, invoiceData);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 422 || error.response?.status === 404) {
        throw new Error('ENDPOINT_NOT_IMPLEMENTED');
      }
      console.error('Error al crear factura:', error);
      const errorMessage = error.response?.data?.detail || 'Error al crear la factura';
      throw new Error(Array.isArray(errorMessage) ? errorMessage[0]?.msg || 'Error de validación' : errorMessage);
    }
  }

  /**
   * Obtener factura por ID
   */
  static async getInvoiceById(invoiceId: string): Promise<Invoice> {
    try {
      const response = await apiRequest.get<Invoice>(`${ENDPOINTS.INVOICES.BASE}/${invoiceId}`);
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener factura:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener la factura');
    }
  }

  /**
   * Buscar factura por número
   */
  static async getInvoiceByNumber(numeroFactura: string): Promise<Invoice> {
    try {
      const response = await apiRequest.get<Invoice>(`${ENDPOINTS.INVOICES.BASE}/numero/${numeroFactura}`);
      return response.data;
    } catch (error: any) {
      console.error('Error al buscar factura por número:', error);
      throw new Error(error.response?.data?.detail || 'Factura no encontrada');
    }
  }

  /**
   * Listar facturas con paginación y filtros
   */
  static async getInvoices(params: InvoiceListParams = {}): Promise<PaginatedResponse<Invoice>> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page.toString());
      if (params.limit) queryParams.append('limit', Math.min(params.limit, 100).toString());
      if (params.search) queryParams.append('search', params.search);
      if (params.only_active !== undefined) queryParams.append('only_active', params.only_active.toString());
      if (params.cliente_id) queryParams.append('cliente_id', params.cliente_id);
      if (params.estado) queryParams.append('estado', params.estado);
      if (params.tipo_factura) queryParams.append('tipo_factura', params.tipo_factura);
      if (params.numero_factura) queryParams.append('numero_factura', params.numero_factura);
      if (params.fecha_inicio) queryParams.append('fecha_inicio', params.fecha_inicio);
      if (params.fecha_fin) queryParams.append('fecha_fin', params.fecha_fin);

      const url = queryParams.toString() ? 
        `${ENDPOINTS.INVOICES.BASE}?${queryParams.toString()}` : 
        ENDPOINTS.INVOICES.BASE;
      
      const response = await apiRequest.get<any>(url);
      
      // Transformar respuesta del backend al formato esperado
      return {
        items: response.data.facturas || response.data.items || [],
        total: response.data.total || 0,
        page: response.data.page || 1,
        limit: response.data.limit || 25,
        has_next: response.data.has_next || false,
        has_prev: response.data.has_prev || false,
      };
    } catch (error: any) {
      if (error.response?.status === 422 || error.response?.status === 404) {
        throw new Error('ENDPOINT_NOT_IMPLEMENTED');
      }
      console.error('Error al listar facturas:', error);
      throw new Error(error.response?.data?.detail || 'Error al cargar las facturas');
    }
  }

  /**
   * Actualizar una factura existente (solo estado EMITIDA)
   */
  static async updateInvoice(invoiceId: string, invoiceData: InvoiceUpdate): Promise<Invoice> {
    try {
      const response = await apiRequest.put<Invoice>(`${ENDPOINTS.INVOICES.BASE}/${invoiceId}`, invoiceData);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 422 || error.response?.status === 404) {
        throw new Error('ENDPOINT_NOT_IMPLEMENTED');
      }
      console.error('Error al actualizar factura:', error);
      const errorMessage = error.response?.data?.detail || 'Error al actualizar la factura';
      throw new Error(Array.isArray(errorMessage) ? errorMessage[0]?.msg || 'Error de validación' : errorMessage);
    }
  }

  /**
   * Anular factura con reversión contable y de stock
   */
  static async deleteInvoice(invoiceId: string): Promise<{ message: string }> {
    try {
      const response = await apiRequest.delete<{ message: string }>(`${ENDPOINTS.INVOICES.BASE}/${invoiceId}`);
      return response.data;
    } catch (error: any) {
      console.error('Error al anular factura:', error);
      throw new Error(error.response?.data?.detail || 'Error al anular la factura');
    }
  }

  /**
   * Marcar factura como pagada
   */
  static async markAsPaid(invoiceId: string, paymentData: PaymentData): Promise<Invoice> {
    try {
      const response = await apiRequest.post<Invoice>(`${ENDPOINTS.INVOICES.BASE}/${invoiceId}/marcar-pagada`, paymentData);
      return response.data;
    } catch (error: any) {
      console.error('Error al marcar factura como pagada:', error);
      throw new Error(error.response?.data?.detail || 'Error al procesar el pago');
    }
  }

  /**
   * Obtener facturas vencidas
   */
  static async getOverdueInvoices(fechaCorte?: string): Promise<Invoice[]> {
    try {
      const url = fechaCorte ? 
        `${ENDPOINTS.INVOICES.BASE}/vencidas/lista?fecha_corte=${fechaCorte}` :
        `${ENDPOINTS.INVOICES.BASE}/vencidas/lista`;
      
      const response = await apiRequest.get<Invoice[]>(url);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 422 || error.response?.status === 404) {
        throw new Error('ENDPOINT_NOT_IMPLEMENTED');
      }
      console.error('Error al obtener facturas vencidas:', error);
      throw new Error(error.response?.data?.detail || 'Error al cargar facturas vencidas');
    }
  }

  /**
   * Obtener facturas de un cliente específico
   */
  static async getInvoicesByClient(clientId: string, params: QueryParams = {}): Promise<PaginatedResponse<Invoice>> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page.toString());
      if (params.limit) queryParams.append('limit', Math.min(params.limit, 100).toString());
      if (params.only_active !== undefined) queryParams.append('only_active', params.only_active.toString());

      const url = queryParams.toString() ? 
        `${ENDPOINTS.INVOICES.BASE}/cliente/${clientId}/lista?${queryParams.toString()}` : 
        `${ENDPOINTS.INVOICES.BASE}/cliente/${clientId}/lista`;
      
      const response = await apiRequest.get<any>(url);
      
      return {
        items: response.data.facturas || response.data.items || [],
        total: response.data.total || 0,
        page: response.data.page || 1,
        limit: response.data.limit || 25,
        has_next: response.data.has_next || false,
        has_prev: response.data.has_prev || false,
      };
    } catch (error: any) {
      console.error('Error al obtener facturas del cliente:', error);
      throw new Error(error.response?.data?.detail || 'Error al cargar facturas del cliente');
    }
  }

  /**
   * Obtener resumen de ventas por período
   */
  static async getSalesSummary(params: SalesReportParams): Promise<SalesSummary> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.fecha_inicio) queryParams.append('fecha_inicio', params.fecha_inicio);
      if (params.fecha_fin) queryParams.append('fecha_fin', params.fecha_fin);
      if (params.agrupar_por) queryParams.append('agrupar_por', params.agrupar_por);

      const url = queryParams.toString() ? 
        `${ENDPOINTS.INVOICES.BASE}/reportes/resumen-ventas?${queryParams.toString()}` : 
        `${ENDPOINTS.INVOICES.BASE}/reportes/resumen-ventas`;

      const response = await apiRequest.get<SalesSummary>(url);
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener resumen de ventas:', error);
      throw new Error(error.response?.data?.detail || 'Error al generar reporte de ventas');
    }
  }

  /**
   * Obtener productos más vendidos
   */
  static async getTopProducts(params: SalesReportParams & { limit?: number }): Promise<TopProduct[]> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.fecha_inicio) queryParams.append('fecha_inicio', params.fecha_inicio);
      if (params.fecha_fin) queryParams.append('fecha_fin', params.fecha_fin);
      if (params.limit) queryParams.append('limit', params.limit.toString());

      const url = queryParams.toString() ? 
        `${ENDPOINTS.INVOICES.BASE}/reportes/productos-mas-vendidos?${queryParams.toString()}` : 
        `${ENDPOINTS.INVOICES.BASE}/reportes/productos-mas-vendidos`;

      const response = await apiRequest.get<TopProduct[]>(url);
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener productos más vendidos:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener ranking de productos');
    }
  }

  /**
   * Obtener mejores clientes
   */
  static async getTopClients(params: SalesReportParams & { limit?: number }): Promise<TopClient[]> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.fecha_inicio) queryParams.append('fecha_inicio', params.fecha_inicio);
      if (params.fecha_fin) queryParams.append('fecha_fin', params.fecha_fin);
      if (params.limit) queryParams.append('limit', params.limit.toString());

      const url = queryParams.toString() ? 
        `${ENDPOINTS.INVOICES.BASE}/reportes/clientes-top?${queryParams.toString()}` : 
        `${ENDPOINTS.INVOICES.BASE}/reportes/clientes-top`;

      const response = await apiRequest.get<TopClient[]>(url);
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener mejores clientes:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener ranking de clientes');
    }
  }

  /**
   * Obtener valor de cartera
   */
  static async getPortfolioValue(clienteId?: string): Promise<PortfolioValue> {
    try {
      const url = clienteId ? 
        `${ENDPOINTS.INVOICES.BASE}/reportes/valor-cartera?cliente_id=${clienteId}` :
        `${ENDPOINTS.INVOICES.BASE}/reportes/valor-cartera`;

      const response = await apiRequest.get<PortfolioValue>(url);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 422 || error.response?.status === 404) {
        throw new Error('ENDPOINT_NOT_IMPLEMENTED');
      }
      console.error('Error al obtener valor de cartera:', error);
      throw new Error(error.response?.data?.detail || 'Error al calcular cartera');
    }
  }

  /**
   * Obtener estadísticas completas de facturas
   */
  static async getCompleteStatistics(params: DateRangeParams = {}): Promise<InvoiceStatistics> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.fecha_inicio) queryParams.append('fecha_inicio', params.fecha_inicio);
      if (params.fecha_fin) queryParams.append('fecha_fin', params.fecha_fin);

      const url = queryParams.toString() ? 
        `${ENDPOINTS.INVOICES.BASE}/reportes/estadisticas-completas?${queryParams.toString()}` : 
        `${ENDPOINTS.INVOICES.BASE}/reportes/estadisticas-completas`;

      const response = await apiRequest.get<InvoiceStatistics>(url);
      return response.data;
    } catch (error: any) {
      // Si el endpoint no está implementado (422), lanzar error específico
      if (error.response?.status === 422 || error.response?.status === 404) {
        throw new Error('ENDPOINT_NOT_IMPLEMENTED');
      }
      console.error('Error al obtener estadísticas completas:', error);
      throw new Error(error.response?.data?.detail || 'Error al cargar estadísticas');
    }
  }

  /**
   * Validar configuración contable
   */
  static async validateAccountingConfiguration(): Promise<{ valid: boolean; message: string }> {
    try {
      const response = await apiRequest.get<{ valid: boolean; message: string }>(`${ENDPOINTS.INVOICES.BASE}/configuracion/validar-integracion-contable`);
      return response.data;
    } catch (error: any) {
      console.error('Error al validar configuración contable:', error);
      throw new Error(error.response?.data?.detail || 'Error al validar configuración');
    }
  }

  // Utilidades para el frontend
  static getInvoiceStatusLabel(status: InvoiceStatus): string {
    const labels = {
      [InvoiceStatus.EMITIDA]: 'Emitida',
      [InvoiceStatus.PAGADA]: 'Pagada',
      [InvoiceStatus.ANULADA]: 'Anulada'
    };
    return labels[status] || status;
  }

  static getInvoiceTypeLabel(type: InvoiceType): string {
    const labels = {
      [InvoiceType.VENTA]: 'Venta',
      [InvoiceType.SERVICIO]: 'Servicio'
    };
    return labels[type] || type;
  }

  static getInvoiceStatusColor(status: InvoiceStatus): 'success' | 'warning' | 'error' | 'default' {
    switch (status) {
      case InvoiceStatus.PAGADA:
        return 'success';
      case InvoiceStatus.EMITIDA:
        return 'warning';
      case InvoiceStatus.ANULADA:
        return 'error';
      default:
        return 'default';
    }
  }

  static formatCurrency(value: number): string {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  }

  static formatInvoiceNumber(numero: string, prefijo: string = 'FV'): string {
    return `${prefijo}-${numero.padStart(6, '0')}`;
  }

  static calculateLineTotal(cantidad: number, precioUnitario: number, descuentoPorcentaje: number, impuestoPorcentaje: number): {
    subtotal: number;
    descuento: number;
    impuesto: number;
    total: number;
  } {
    const subtotal = cantidad * precioUnitario;
    const descuento = subtotal * (descuentoPorcentaje / 100);
    const subtotalConDescuento = subtotal - descuento;
    const impuesto = subtotalConDescuento * (impuestoPorcentaje / 100);
    const total = subtotalConDescuento + impuesto;

    return {
      subtotal,
      descuento,
      impuesto,
      total
    };
  }

  static calculateInvoiceTotal(detalles: InvoiceDetailCreate[]): {
    subtotal: number;
    totalDescuentos: number;
    totalImpuestos: number;
    total: number;
  } {
    let subtotal = 0;
    let totalDescuentos = 0;
    let totalImpuestos = 0;

    detalles.forEach(detalle => {
      const lineTotal = this.calculateLineTotal(
        detalle.cantidad,
        detalle.precio_unitario,
        detalle.descuento_porcentaje,
        detalle.impuesto_porcentaje
      );

      subtotal += lineTotal.subtotal;
      totalDescuentos += lineTotal.descuento;
      totalImpuestos += lineTotal.impuesto;
    });

    const total = subtotal - totalDescuentos + totalImpuestos;

    return {
      subtotal,
      totalDescuentos,
      totalImpuestos,
      total
    };
  }

  static validateInvoiceDetails(detalles: InvoiceDetailCreate[]): string[] {
    const errors: string[] = [];

    if (detalles.length === 0) {
      errors.push('La factura debe tener al menos un detalle');
    }

    detalles.forEach((detalle, index) => {
      if (!detalle.producto_id) {
        errors.push(`Detalle ${index + 1}: Debe seleccionar un producto`);
      }
      if (detalle.cantidad <= 0) {
        errors.push(`Detalle ${index + 1}: La cantidad debe ser mayor a 0`);
      }
      if (detalle.precio_unitario <= 0) {
        errors.push(`Detalle ${index + 1}: El precio unitario debe ser mayor a 0`);
      }
      if (detalle.descuento_porcentaje < 0 || detalle.descuento_porcentaje > 100) {
        errors.push(`Detalle ${index + 1}: El descuento debe estar entre 0% y 100%`);
      }
      if (detalle.impuesto_porcentaje < 0 || detalle.impuesto_porcentaje > 100) {
        errors.push(`Detalle ${index + 1}: El impuesto debe estar entre 0% y 100%`);
      }
    });

    return errors;
  }
}