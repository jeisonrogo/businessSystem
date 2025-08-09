/**
 * Servicio de Productos
 */

import { Product, ProductCreate, ProductUpdate, ProductListResponse, QueryParams } from '../types';
import { ENDPOINTS } from '../config/api';
import { apiRequest } from './api';

export class ProductService {
  /**
   * Obtener lista de productos con paginación
   */
  static async getProducts(params?: QueryParams): Promise<ProductListResponse> {
    const response = await apiRequest.get<any>(ENDPOINTS.PRODUCTS.BASE, params);
    
    // Transformar la respuesta del backend al formato esperado por el frontend
    return {
      items: response.data.products.map((product: any) => ({
        ...product,
        precio_base: Number(product.precio_base),
        precio_publico: Number(product.precio_publico),
      })),
      total: response.data.total,
      page: response.data.page,
      limit: response.data.limit,
      has_next: response.data.has_next,
      has_prev: response.data.has_prev,
    };
  }

  /**
   * Obtener producto por ID
   */
  static async getProductById(id: string): Promise<Product> {
    const response = await apiRequest.get<any>(`${ENDPOINTS.PRODUCTS.BASE}/${id}`);
    return {
      ...response.data,
      precio_base: Number(response.data.precio_base),
      precio_publico: Number(response.data.precio_publico),
    };
  }

  /**
   * Obtener producto por SKU
   */
  static async getProductBySKU(sku: string): Promise<Product> {
    const response = await apiRequest.get<any>(ENDPOINTS.PRODUCTS.BY_SKU(sku));
    return {
      ...response.data,
      precio_base: Number(response.data.precio_base),
      precio_publico: Number(response.data.precio_publico),
    };
  }

  /**
   * Crear nuevo producto
   */
  static async createProduct(product: ProductCreate): Promise<Product> {
    try {
      const response = await apiRequest.post<any>(ENDPOINTS.PRODUCTS.BASE, product);
      return {
        ...response.data,
        precio_base: Number(response.data.precio_base),
        precio_publico: Number(response.data.precio_publico),
      };
    } catch (error: any) {
      // Transformar errores del backend a mensajes más amigables
      throw this.handleApiError(error, 'Error al crear producto');
    }
  }

  /**
   * Actualizar producto existente
   */
  static async updateProduct(id: string, product: ProductUpdate): Promise<Product> {
    try {
      const response = await apiRequest.put<any>(`${ENDPOINTS.PRODUCTS.BASE}/${id}`, product);
      return {
        ...response.data,
        precio_base: Number(response.data.precio_base),
        precio_publico: Number(response.data.precio_publico),
      };
    } catch (error: any) {
      throw this.handleApiError(error, 'Error al actualizar producto');
    }
  }

  /**
   * Eliminar producto (soft delete)
   */
  static async deleteProduct(id: string): Promise<{ message: string }> {
    const response = await apiRequest.delete<{ message: string }>(`${ENDPOINTS.PRODUCTS.BASE}/${id}`);
    return response.data;
  }

  /**
   * Actualizar solo el stock de un producto
   */
  static async updateStock(id: string, stock: number): Promise<{
    message: string;
    stock_anterior: number;
    stock_nuevo: number;
  }> {
    try {
      const response = await apiRequest.patch<{
        message: string;
        stock_anterior: number;
        stock_nuevo: number;
      }>(ENDPOINTS.PRODUCTS.UPDATE_STOCK(id), { stock });
      return response.data;
    } catch (error: any) {
      throw this.handleApiError(error, 'Error al actualizar stock');
    }
  }

  /**
   * Obtener productos con stock bajo
   */
  static async getLowStockProducts(threshold?: number): Promise<Product[]> {
    const params = threshold ? { threshold } : undefined;
    const response = await apiRequest.get<any>(ENDPOINTS.PRODUCTS.LOW_STOCK, params);
    return response.data.map((product: any) => ({
      ...product,
      precio_base: Number(product.precio_base),
      precio_publico: Number(product.precio_publico),
    }));
  }

  /**
   * Manejar errores de la API y transformarlos en mensajes amigables
   */
  private static handleApiError(error: any, defaultMessage: string): Error {
    console.error('Error en ProductService:', error);

    // Si es un error de red o conexión
    if (!error.response) {
      return new Error('Error de conexión. Verifica tu conexión a internet.');
    }

    const { status, data } = error.response;

    // Errores específicos por código de estado
    switch (status) {
      case 400:
        // Error de validación - extraer mensaje específico
        if (data?.detail) {
          if (typeof data.detail === 'string') {
            return new Error(data.detail);
          }
          // Si es un array de errores de validación
          if (Array.isArray(data.detail)) {
            const messages = data.detail.map((err: any) => {
              if (err.msg && err.loc) {
                const field = err.loc[err.loc.length - 1];
                return `${field}: ${err.msg}`;
              }
              return err.msg || JSON.stringify(err);
            });
            return new Error(messages.join(', '));
          }
        }
        return new Error('Datos inválidos. Verifica la información ingresada.');
      
      case 401:
        return new Error('No tienes permisos para realizar esta acción.');
      
      case 403:
        return new Error('Acceso denegado.');
      
      case 404:
        return new Error('Producto no encontrado.');
      
      case 409:
        // Conflicto - típicamente SKU duplicado
        return new Error(data?.detail || 'El SKU ya existe. Usa un SKU diferente.');
      
      case 422:
        // Error de validación de FastAPI
        if (data?.detail) {
          if (Array.isArray(data.detail)) {
            const messages = data.detail.map((err: any) => {
              const field = err.loc ? err.loc[err.loc.length - 1] : 'campo';
              return `${field}: ${err.msg}`;
            });
            return new Error(messages.join(', '));
          }
          return new Error(data.detail);
        }
        return new Error('Error de validación en los datos enviados.');
      
      case 500:
        return new Error('Error interno del servidor. Contacta al administrador.');
      
      default:
        return new Error(data?.detail || defaultMessage);
    }
  }
}