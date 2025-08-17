/**
 * Configuración de la API del Sistema de Gestión Empresarial
 */

export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  API_VERSION: '/api/v1',
  TIMEOUT: 10000,
};

export const ENDPOINTS = {
  // Autenticación
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    ME: '/auth/me',
    CHANGE_PASSWORD: '/auth/change-password',
  },
  // Productos
  PRODUCTS: {
    BASE: '/products',
    BY_SKU: (sku: string) => `/products/sku/${sku}`,
    LOW_STOCK: '/products/low-stock',
    UPDATE_STOCK: (id: string) => `/products/${id}/stock`,
  },
  // Inventario
  INVENTORY: {
    MOVEMENTS: '/inventario/movimientos/',
    MOVEMENTS_BY_ID: (movementId: string) => `/inventario/movimientos/${movementId}`,
    KARDEX: (productId: string) => `/inventario/kardex/${productId}`,
    SUMMARY: '/inventario/resumen/',
    STATS: '/inventario/estadisticas/',
    VALIDATE_STOCK: '/inventario/validar-stock/',
    RECALCULATE_COSTS: (productId: string) => `/inventario/recalcular-costos/${productId}`,
  },
  // Contabilidad
  ACCOUNTING: {
    BASE: '/cuentas',
    BY_CODE: (code: string) => `/cuentas/codigo/${code}`,
    HIERARCHY: '/cuentas/plan-jerarquico/',
    MAIN_ACCOUNTS: '/cuentas/principales/',
    SUB_ACCOUNTS: (parentId: string) => `/cuentas/${parentId}/subcuentas/`,
    SEED_COLOMBIA: '/cuentas/seed-colombia/',
  },
  // Asientos Contables
  ENTRIES: {
    BASE: '/asientos',
  },
  // Clientes
  CLIENTS: {
    BASE: '/clientes',
    BY_DOCUMENT: (numeroDocumento: string) => `/clientes/documento/${numeroDocumento}`,
    QUICK_SEARCH: '/clientes/search/quick',
    FREQUENT: '/clientes/frecuentes/top',
    BY_TYPE: (tipoCliente: string) => `/clientes/tipo/${tipoCliente}`,
    STATS: (clientId: string) => `/clientes/${clientId}/estadisticas`,
    ACTIVATE: (clientId: string) => `/clientes/${clientId}/activate`,
  },
  // Facturas
  INVOICES: {
    BASE: '/facturas',
    BY_NUMBER: (numeroFactura: string) => `/facturas/numero/${numeroFactura}`,
    MARK_AS_PAID: (invoiceId: string) => `/facturas/${invoiceId}/marcar-pagada`,
    OVERDUE: '/facturas/vencidas/lista',
    BY_CLIENT: (clientId: string) => `/facturas/cliente/${clientId}/lista`,
    REPORTS: {
      SALES_SUMMARY: '/facturas/reportes/resumen-ventas',
      TOP_PRODUCTS: '/facturas/reportes/productos-mas-vendidos',
      TOP_CLIENTS: '/facturas/reportes/clientes-top',
      PORTFOLIO_VALUE: '/facturas/reportes/valor-cartera',
      COMPLETE_STATS: '/facturas/reportes/estadisticas-completas',
    },
    CONFIG: {
      VALIDATE_ACCOUNTING: '/facturas/configuracion/validar-integracion-contable',
    },
  },
  // Dashboard
  DASHBOARD: {
    OVERVIEW: '/dashboard/resumen',
    SALES_CHART: '/dashboard/ventas-por-mes',
    INVENTORY_VALUE: '/dashboard/valor-inventario',
  },
};

/**
 * URL completa del endpoint de la API
 */
export const getApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${API_CONFIG.API_VERSION}${endpoint}`;
};