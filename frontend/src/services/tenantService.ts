/**
 * Servicio Multi-Tenant
 * 
 * Maneja las comunicaciones con el backend para funcionalidades
 * multi-tenant: tiendas, locales, stock, transferencias y permisos.
 */

import { apiRequest } from './api';
import {
  TenantContext,
  Tienda,
  TiendaCreate,
  TiendaUpdate,
  TiendaListResponse,
  Local,
  LocalCreate,
  LocalUpdate,
  LocalListResponse,
  StockLocal,
  StockLocalUpdate,
  StockLocalMovimiento,
  StockLocalListResponse,
  TransferenciaInventario,
  TransferenciaCreate,
  TransferenciaUpdate,
  TransferenciaListResponse,
  UsuarioLocal,
  UsuarioLocalCreate,
  UsuarioLocalUpdate,
  UsuarioLocalListResponse,
  CambiarContextoRequest,
  EstadisticasTienda,
  EstadisticasLocal,
  ResumenTransferencias,
  FiltroMultiTenant,
  FiltroTransferencias,
  FiltroStockLocal,
  ValidacionStock
} from '../types/multiTenant';

// ============================================================================
// SERVICIO PRINCIPAL DE TENANT
// ============================================================================

export class TenantService {
  
  // ============================================================================
  // CONTEXTO DE TENANT
  // ============================================================================

  /**
   * Obtiene el contexto actual del usuario autenticado
   */
  static async getCurrentContext(): Promise<TenantContext> {
    const response = await apiRequest.get<TenantContext>('/tenant-context/current');
    return response.data;
  }

  /**
   * Cambia el contexto del usuario a una tienda/local específico
   */
  static async switchContext(request: CambiarContextoRequest): Promise<TenantContext> {
    const response = await apiRequest.post<TenantContext>('/tenant-context/cambiar-contexto', request);
    return response.data;
  }

  /**
   * Obtiene información detallada del tenant actual
   */
  static async getTenantInfo(): Promise<any> {
    const response = await apiRequest.get('/tenant-context/info');
    return response.data;
  }

  /**
   * Obtiene los permisos detallados del usuario
   */
  static async getDetailedPermissions(): Promise<any> {
    const response = await apiRequest.get('/tenant-context/permisos');
    return response.data;
  }

  /**
   * Valida un permiso específico
   */
  static async validatePermission(permission: string, localId?: string): Promise<any> {
    const params = localId ? { local_id: localId } : {};
    const response = await apiRequest.get(`/tenant-context/validar-permiso/${permission}`, params);
    return response.data;
  }

  // ============================================================================
  // GESTIÓN DE TIENDAS
  // ============================================================================

  /**
   * Obtiene las tiendas disponibles para el usuario
   */
  static async getUserStores(): Promise<Tienda[]> {
    const response = await apiRequest.get<Tienda[]>('/tiendas/');
    return Array.isArray(response.data) ? response.data : [];
  }

  /**
   * Crea una nueva tienda
   */
  static async createStore(tienda: TiendaCreate): Promise<Tienda> {
    const response = await apiRequest.post<Tienda>('/tiendas/', tienda);
    return response.data;
  }

  /**
   * Obtiene una tienda por ID
   */
  static async getStore(tiendaId: string): Promise<Tienda> {
    const response = await apiRequest.get<Tienda>(`/tiendas/${tiendaId}`);
    return response.data;
  }

  /**
   * Actualiza una tienda
   */
  static async updateStore(tiendaId: string, updates: TiendaUpdate): Promise<Tienda> {
    const response = await apiRequest.put<Tienda>(`/tiendas/${tiendaId}`, updates);
    return response.data;
  }

  /**
   * Obtiene estadísticas de una tienda
   */
  static async getStoreStats(tiendaId: string): Promise<EstadisticasTienda> {
    const response = await apiRequest.get<EstadisticasTienda>(`/tiendas/${tiendaId}/estadisticas`);
    return response.data;
  }

  /**
   * Genera el siguiente número de factura para una tienda
   */
  static async generateInvoiceNumber(tiendaId: string): Promise<string> {
    const response = await apiRequest.post<{ numero_factura: string }>(`/tiendas/${tiendaId}/generar-numero-factura`);
    return response.data.numero_factura;
  }

  // ============================================================================
  // GESTIÓN DE LOCALES
  // ============================================================================

  /**
   * Obtiene los locales de una tienda
   */
  static async getStoreLocals(tiendaId: string): Promise<Local[]> {
    const response = await apiRequest.get<Local[]>('/locales/', {
      tienda_id: tiendaId
    });
    return Array.isArray(response.data) ? response.data : [];
  }

  /**
   * Obtiene los locales disponibles para el usuario actual (basado en rol y permisos)
   * - ADMINISTRADOR/GERENTE: Todos los locales de la tienda
   * - Otros roles: Solo locales asignados específicamente
   */
  static async getAvailableLocals(): Promise<Local[]> {
    const response = await apiRequest.get<Local[]>('/tenant-context/mis-locales');
    return response.data;
  }

  /**
   * Crea un nuevo local
   */
  static async createLocal(local: LocalCreate): Promise<Local> {
    const response = await apiRequest.post<Local>('/locales/', local);
    return response.data;
  }

  /**
   * Obtiene un local por ID
   */
  static async getLocal(localId: string): Promise<Local> {
    const response = await apiRequest.get<Local>(`/locales/${localId}`);
    return response.data;
  }

  /**
   * Actualiza un local
   */
  static async updateLocal(localId: string, updates: LocalUpdate): Promise<Local> {
    const response = await apiRequest.put<Local>(`/locales/${localId}`, updates);
    return response.data;
  }

  /**
   * Obtiene estadísticas de un local
   */
  static async getLocalStats(localId: string): Promise<EstadisticasLocal> {
    const response = await apiRequest.get<EstadisticasLocal>(`/locales/${localId}/estadisticas`);
    return response.data;
  }

  // ============================================================================
  // GESTIÓN DE STOCK POR LOCAL
  // ============================================================================

  /**
   * Obtiene el stock de un local
   */
  static async getLocalStock(localId: string, filters?: FiltroStockLocal): Promise<StockLocal[]> {
    const params = { ...filters, local_id: localId };
    const response = await apiRequest.get<StockLocalListResponse>('/stock-local/', params);
    return response.data.stock_items;
  }

  /**
   * Obtiene el stock de un producto en un local específico
   */
  static async getProductLocalStock(localId: string, productoId: string): Promise<StockLocal> {
    const response = await apiRequest.get<StockLocal>(`/stock-local/local/${localId}/producto/${productoId}`);
    return response.data;
  }

  /**
   * Actualiza el stock de un producto en un local
   */
  static async updateLocalStock(stockId: string, updates: StockLocalUpdate): Promise<StockLocal> {
    const response = await apiRequest.put<StockLocal>(`/stock-local/${stockId}`, updates);
    return response.data;
  }

  /**
   * Realiza un movimiento de stock en un local
   */
  static async createStockMovement(movimiento: StockLocalMovimiento): Promise<any> {
    const response = await apiRequest.post('/stock-local/movimiento', movimiento);
    return response.data;
  }

  /**
   * Obtiene productos con stock bajo en un local
   */
  static async getLowStockProducts(localId: string): Promise<StockLocal[]> {
    const response = await apiRequest.get<StockLocal[]>(`/stock-local/local/${localId}/stock-bajo`);
    return response.data;
  }

  /**
   * Valida disponibilidad de stock para una venta
   */
  static async validateStock(localId: string, productoId: string, cantidad: number): Promise<ValidacionStock> {
    const response = await apiRequest.post<ValidacionStock>('/stock-local/validar-stock', {
      local_id: localId,
      producto_id: productoId,
      cantidad
    });
    return response.data;
  }

  // ============================================================================
  // GESTIÓN DE TRANSFERENCIAS
  // ============================================================================

  /**
   * Obtiene las transferencias con filtros opcionales
   */
  static async getTransfers(filters?: FiltroTransferencias): Promise<TransferenciaInventario[]> {
    const response = await apiRequest.get<TransferenciaListResponse>('/transferencias/', { params: filters });
    return response.data.transferencias;
  }

  /**
   * Crea una nueva transferencia
   */
  static async createTransfer(transferencia: TransferenciaCreate): Promise<TransferenciaInventario> {
    const response = await apiRequest.post<TransferenciaInventario>('/transferencias/', transferencia);
    return response.data;
  }

  /**
   * Obtiene una transferencia por ID
   */
  static async getTransfer(transferenciaId: string): Promise<TransferenciaInventario> {
    const response = await apiRequest.get<TransferenciaInventario>(`/transferencias/${transferenciaId}`);
    return response.data;
  }

  /**
   * Confirma el envío de una transferencia
   */
  static async confirmTransferSent(transferenciaId: string, observaciones?: string): Promise<TransferenciaInventario> {
    const response = await apiRequest.post<TransferenciaInventario>(
      `/transferencias/${transferenciaId}/confirmar-envio`,
      { observaciones_origen: observaciones }
    );
    return response.data;
  }

  /**
   * Confirma la recepción de una transferencia
   */
  static async confirmTransferReceived(transferenciaId: string, observaciones?: string): Promise<TransferenciaInventario> {
    const response = await apiRequest.post<TransferenciaInventario>(
      `/transferencias/${transferenciaId}/confirmar-recepcion`,
      { observaciones_destino: observaciones }
    );
    return response.data;
  }

  /**
   * Cancela una transferencia
   */
  static async cancelTransfer(transferenciaId: string, observaciones?: string): Promise<TransferenciaInventario> {
    const response = await apiRequest.post<TransferenciaInventario>(
      `/transferencias/${transferenciaId}/cancelar`,
      { observaciones_origen: observaciones }
    );
    return response.data;
  }

  /**
   * Obtiene resumen de transferencias
   */
  static async getTransferSummary(): Promise<ResumenTransferencias> {
    const response = await apiRequest.get<ResumenTransferencias>('/transferencias/resumen');
    return response.data;
  }

  // ============================================================================
  // GESTIÓN DE PERMISOS USUARIO-LOCAL
  // ============================================================================

  /**
   * Obtiene los permisos del usuario actual en la tienda
   */
  static async getUserPermissions(tiendaId?: string): Promise<UsuarioLocal[]> {
    const params = tiendaId ? { tienda_id: tiendaId } : {};
    const response = await apiRequest.get<UsuarioLocalListResponse>('/usuario-locales/', params);
    return response.data.asignaciones;
  }

  /**
   * Obtiene los permisos de un usuario específico
   */
  static async getUserLocalPermissions(userId: string): Promise<UsuarioLocal[]> {
    const response = await apiRequest.get<UsuarioLocalListResponse>(`/usuario-locales/usuario/${userId}`);
    return response.data.asignaciones;
  }

  /**
   * Obtiene los usuarios con permisos en un local
   */
  static async getLocalUsers(localId: string): Promise<UsuarioLocal[]> {
    const response = await apiRequest.get<UsuarioLocalListResponse>(`/usuario-locales/local/${localId}`);
    return response.data.asignaciones;
  }

  /**
   * Crea una nueva asignación de permisos
   */
  static async createUserLocalPermission(permission: UsuarioLocalCreate): Promise<UsuarioLocal> {
    const response = await apiRequest.post<UsuarioLocal>('/usuario-locales/', permission);
    return response.data;
  }

  /**
   * Actualiza los permisos de un usuario en un local
   */
  static async updateUserLocalPermission(permissionId: string, updates: UsuarioLocalUpdate): Promise<UsuarioLocal> {
    const response = await apiRequest.put<UsuarioLocal>(`/usuario-locales/${permissionId}`, updates);
    return response.data;
  }

  /**
   * Elimina los permisos de un usuario en un local
   */
  static async deleteUserLocalPermission(permissionId: string): Promise<void> {
    await apiRequest.delete(`/usuario-locales/${permissionId}`);
  }

  /**
   * Obtiene estadísticas de permisos en la tienda
   */
  static async getPermissionsStats(): Promise<any> {
    const response = await apiRequest.get('/usuario-locales/estadisticas');
    return response.data;
  }

  // ============================================================================
  // UTILIDADES DE HEADERS TENANT
  // ============================================================================

  /**
   * Configura headers con contexto de local para requests específicos
   */
  static async requestWithLocalContext<T>(
    requestFn: () => Promise<T>,
    localId: string
  ): Promise<T> {
    // Esto se podría implementar usando interceptors de axios
    // para agregar automáticamente el header X-Local-ID
    const originalHeaders = apiRequest.get;
    
    try {
      // Agregar header temporalmente
      return await requestFn();
    } finally {
      // Restaurar headers originales si es necesario
    }
  }
}

// ============================================================================
// SERVICIO DE CONFIGURACIÓN API
// ============================================================================

/**
 * Configura interceptors para agregar headers de contexto multi-tenant
 */
export const configureTenantHeaders = () => {
  // Interceptor que agrega el header X-Local-ID cuando hay contexto de local
  const addTenantHeaders = (config: any) => {
    const tenantContext = localStorage.getItem('tenant_context');
    if (tenantContext) {
      const context = JSON.parse(tenantContext);
      if (context.local_id) {
        config.headers['X-Local-ID'] = context.local_id;
      }
    }
    return config;
  };

  // Configurar interceptor si es necesario
  // apiClient.interceptors.request.use(addTenantHeaders);
};

export default TenantService;