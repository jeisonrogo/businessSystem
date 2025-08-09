/**
 * Servicio de Inventario
 * Maneja las operaciones CRUD de movimientos de inventario, kardex y estadísticas
 */

import { 
  InventoryMovement,
  InventoryMovementCreate,
  InventoryMovementListResponse,
  KardexResponse,
  InventorySummary,
  InventoryStats,
  StockValidation,
  MovementType,
  QueryParams 
} from '../types';
import { ENDPOINTS } from '../config/api';
import { apiRequest } from './api';

export interface InventoryQueryParams extends QueryParams {
  producto_id?: string;
  tipo_movimiento?: MovementType;
  fecha_desde?: string;
  fecha_hasta?: string;
  referencia?: string;
}

export interface StockValidationRequest {
  producto_id: string;
  cantidad_solicitada: number;
}

export class InventoryService {
  /**
   * Registrar un nuevo movimiento de inventario
   */
  static async createMovement(movementData: InventoryMovementCreate): Promise<InventoryMovement> {
    try {
      const response = await apiRequest.post<InventoryMovement>(ENDPOINTS.INVENTORY.MOVEMENTS, movementData);
      return response.data;
    } catch (error: any) {
      console.error('Error al crear movimiento de inventario:', error);
      throw new Error(error.response?.data?.detail || 'Error al crear el movimiento de inventario');
    }
  }

  /**
   * Obtener lista de movimientos de inventario con filtros y paginación
   */
  static async getMovements(params?: InventoryQueryParams): Promise<InventoryMovementListResponse> {
    try {
      const response = await apiRequest.get<InventoryMovementListResponse>(ENDPOINTS.INVENTORY.MOVEMENTS, params);
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener movimientos de inventario:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener los movimientos de inventario');
    }
  }

  /**
   * Obtener movimiento específico por ID
   */
  static async getMovementById(movementId: string): Promise<InventoryMovement> {
    try {
      const response = await apiRequest.get<InventoryMovement>(ENDPOINTS.INVENTORY.MOVEMENTS_BY_ID(movementId));
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener movimiento:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener el movimiento');
    }
  }

  /**
   * Obtener kardex de un producto específico
   */
  static async getKardex(productId: string): Promise<KardexResponse> {
    try {
      const response = await apiRequest.get<KardexResponse>(ENDPOINTS.INVENTORY.KARDEX(productId));
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener kardex:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener el kardex del producto');
    }
  }

  /**
   * Obtener resumen general del inventario
   */
  static async getInventorySummary(): Promise<InventorySummary> {
    try {
      const response = await apiRequest.get<InventorySummary>(ENDPOINTS.INVENTORY.SUMMARY);
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener resumen de inventario:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener el resumen de inventario');
    }
  }

  /**
   * Obtener estadísticas de inventario para un período
   */
  static async getInventoryStats(fechaDesde?: string, fechaHasta?: string): Promise<InventoryStats> {
    try {
      const params: any = {};
      if (fechaDesde) params.fecha_desde = fechaDesde;
      if (fechaHasta) params.fecha_hasta = fechaHasta;

      const response = await apiRequest.get<InventoryStats>(ENDPOINTS.INVENTORY.STATS, params);
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener estadísticas de inventario:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener las estadísticas de inventario');
    }
  }

  /**
   * Validar disponibilidad de stock para una operación
   */
  static async validateStock(validation: StockValidationRequest): Promise<StockValidation> {
    try {
      const response = await apiRequest.post<StockValidation>(ENDPOINTS.INVENTORY.VALIDATE_STOCK, validation);
      return response.data;
    } catch (error: any) {
      console.error('Error al validar stock:', error);
      throw new Error(error.response?.data?.detail || 'Error al validar el stock');
    }
  }

  /**
   * Recalcular costos promedio de un producto
   */
  static async recalculateCosts(productId: string): Promise<{ message: string }> {
    try {
      const response = await apiRequest.post<{ message: string }>(ENDPOINTS.INVENTORY.RECALCULATE_COSTS(productId), {});
      return response.data;
    } catch (error: any) {
      console.error('Error al recalcular costos:', error);
      throw new Error(error.response?.data?.detail || 'Error al recalcular los costos');
    }
  }

  /**
   * Obtener etiquetas de tipos de movimiento en español
   */
  static getMovementTypeLabels(): Record<MovementType, string> {
    return {
      [MovementType.ENTRADA]: 'Entrada',
      [MovementType.SALIDA]: 'Salida',
      [MovementType.MERMA]: 'Merma',
      [MovementType.AJUSTE]: 'Ajuste',
    };
  }

  /**
   * Obtener colores para tipos de movimiento
   */
  static getMovementTypeColors(): Record<MovementType, string> {
    return {
      [MovementType.ENTRADA]: '#4caf50',    // Verde - entrada de productos
      [MovementType.SALIDA]: '#f44336',     // Rojo - salida de productos  
      [MovementType.MERMA]: '#ff9800',      // Naranja - pérdidas
      [MovementType.AJUSTE]: '#2196f3',     // Azul - ajustes de inventario
    };
  }

  /**
   * Obtener iconos para tipos de movimiento
   */
  static getMovementTypeIcons(): Record<MovementType, string> {
    return {
      [MovementType.ENTRADA]: 'trending_up',
      [MovementType.SALIDA]: 'trending_down',
      [MovementType.MERMA]: 'report_problem',
      [MovementType.AJUSTE]: 'tune',
    };
  }

  /**
   * Formatear cantidad con signo según tipo de movimiento
   */
  static formatQuantityWithSign(tipo: MovementType, cantidad: number): string {
    const sign = tipo === MovementType.ENTRADA || tipo === MovementType.AJUSTE ? '+' : '-';
    return `${sign}${cantidad}`;
  }

  /**
   * Formatear valor monetario
   */
  static formatCurrency(value: number): string {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  }

  /**
   * Calcular valor total de un movimiento
   */
  static calculateMovementValue(movement: InventoryMovement): number {
    const unitCost = movement.costo_unitario || movement.precio_unitario || 0;
    return unitCost * movement.cantidad;
  }
}