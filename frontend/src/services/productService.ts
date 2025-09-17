/**
 * Servicio de Productos
 */

import { Product, ProductCreate, ProductUpdate, ProductListResponse, QueryParams } from '../types';
import { ENDPOINTS, API_CONFIG } from '../config/api';
import { apiRequest } from './api';

export class ProductService {
  /**
   * Obtener lista de productos con paginación y filtrado por contexto local
   */
  static async getProducts(params?: QueryParams & {
    local_id?: string;
    todos_los_locales?: boolean;
  }): Promise<ProductListResponse> {
    const response = await apiRequest.get<any>(ENDPOINTS.PRODUCTS.BASE, params);
    
    // Transformar la respuesta del backend al formato esperado por el frontend
    return {
      items: response.data.products.map((product: any) => ({
        ...product,
        precio_base: Number(product.precio_base),
        precio_publico: Number(product.precio_publico),
        // Nuevos campos de stock local-específico
        stock_local_actual: product.stock_local_actual || 0,
        stock_total_tienda: product.stock_total_tienda || 0,
        costo_promedio_local: product.costo_promedio_local || 0,
        valor_total_inventario: product.valor_total_inventario || 0,
        local_id: product.local_id,
        local_nombre: product.local_nombre,
        locales_stock: product.locales_stock || [], // Para vista de todos los locales
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
  static async updateStock(id: string, stock: number, localId?: string): Promise<{
    message: string;
    stock_anterior: number;
    stock_nuevo: number;
  }> {
    try {
      // Construir URL con parámetros de query si se proporciona localId
      const baseUrl = ENDPOINTS.PRODUCTS.UPDATE_STOCK(id);
      const url = localId ? `${baseUrl}?local_id=${localId}` : baseUrl;
      
      const response = await apiRequest.patch<{
        message: string;
        stock_anterior: number;
        stock_nuevo: number;
      }>(url, { stock });
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

  /**
   * Subir imagen de producto
   */
  static async uploadProductImage(productId: string, file: File): Promise<string> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const token = localStorage.getItem('access_token');
      const uploadUrl = `${API_CONFIG.BASE_URL}${API_CONFIG.API_VERSION}${ENDPOINTS.UPLOAD.PRODUCT_IMAGE(productId)}`;
      
      console.log('📤 Uploading to:', uploadUrl);
      console.log('🔐 Token exists:', !!token);
      
      const response = await fetch(uploadUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Error ${response.status}: ${errorText}`);
      }

      const result = await response.json();
      return result.image_path;
    } catch (error: any) {
      console.error('Error uploading image:', error);
      throw new Error(`Error al subir la imagen: ${error.message}`);
    }
  }
}