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
    const response = await apiRequest.get<ProductListResponse>(ENDPOINTS.PRODUCTS.BASE, params);
    return response.data;
  }

  /**
   * Obtener producto por ID
   */
  static async getProductById(id: string): Promise<Product> {
    const response = await apiRequest.get<Product>(`${ENDPOINTS.PRODUCTS.BASE}/${id}`);
    return response.data;
  }

  /**
   * Obtener producto por SKU
   */
  static async getProductBySKU(sku: string): Promise<Product> {
    const response = await apiRequest.get<Product>(ENDPOINTS.PRODUCTS.BY_SKU(sku));
    return response.data;
  }

  /**
   * Crear nuevo producto
   */
  static async createProduct(product: ProductCreate): Promise<Product> {
    const response = await apiRequest.post<Product>(ENDPOINTS.PRODUCTS.BASE, product);
    return response.data;
  }

  /**
   * Actualizar producto existente
   */
  static async updateProduct(id: string, product: ProductUpdate): Promise<Product> {
    const response = await apiRequest.put<Product>(`${ENDPOINTS.PRODUCTS.BASE}/${id}`, product);
    return response.data;
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
    const response = await apiRequest.get<Product[]>(ENDPOINTS.PRODUCTS.LOW_STOCK, params);
    return response.data;
  }
}