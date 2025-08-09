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
    MOVEMENTS: '/inventario/movimientos',
    KARDEX: (productId: string) => `/inventario/kardex/${productId}`,
    SUMMARY: '/inventario/resumen',
    STATS: '/inventario/estadisticas',
  },
  // Contabilidad
  ACCOUNTING: {
    BASE: '/cuentas',
    BY_CODE: (code: string) => `/cuentas/codigo/${code}`,
    HIERARCHY: '/cuentas/plan-jerarquico',
    MAIN_ACCOUNTS: '/cuentas/principales',
    SUB_ACCOUNTS: (parentId: string) => `/cuentas/${parentId}/subcuentas`,
    SEED_COLOMBIA: '/cuentas/seed-colombia',
  },
  // Asientos Contables
  ENTRIES: {
    BASE: '/asientos',
  },
  // Clientes
  CLIENTS: {
    BASE: '/clientes',
  },
  // Facturas
  INVOICES: {
    BASE: '/facturas',
    STATS: '/facturas/estadisticas',
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