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
    const response = await apiRequest.post<any>(ENDPOINTS.PRODUCTS.BASE, product);
    return {
      ...response.data,
      precio_base: Number(response.data.precio_base),
      precio_publico: Number(response.data.precio_publico),
    };
  }

  /**
   * Actualizar producto existente
   */
  static async updateProduct(id: string, product: ProductUpdate): Promise<Product> {
    const response = await apiRequest.put<any>(`${ENDPOINTS.PRODUCTS.BASE}/${id}`, product);
    return {
      ...response.data,
      precio_base: Number(response.data.precio_base),
      precio_publico: Number(response.data.precio_publico),
    };
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
    const response = await apiRequest.patch<{
      message: string;
      stock_anterior: number;
      stock_nuevo: number;
    }>(ENDPOINTS.PRODUCTS.UPDATE_STOCK(id), { stock });
    return response.data;
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
}