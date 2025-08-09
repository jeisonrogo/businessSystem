/**
 * Servicio para gestión de clientes
 * Maneja todas las operaciones CRUD y funcionalidades especializadas
 */

import { apiRequest } from './api';
import { ENDPOINTS } from '../config/api';
import {
  Client,
  ClientType,
  DocumentType,
  PaginatedResponse,
  QueryParams
} from '../types';

// Interfaces específicas para clientes
export interface ClientCreate {
  tipo_documento: DocumentType;
  numero_documento: string;
  nombre_completo: string;
  nombre_comercial?: string;
  email?: string;
  telefono?: string;
  direccion?: string;
  tipo_cliente: ClientType;
}

export interface ClientUpdate {
  nombre_completo?: string;
  nombre_comercial?: string;
  email?: string;
  telefono?: string;
  direccion?: string;
  tipo_cliente?: ClientType;
}

export interface ClientListParams extends QueryParams {
  tipo_cliente?: ClientType;
  tipo_documento?: DocumentType;
}

export interface ClientQuickSearch {
  id: string;
  nombre_completo: string;
  numero_documento: string;
  tipo_cliente: ClientType;
}

export interface ClientStats {
  total_facturas: number;
  total_compras: number;
  ultima_compra: string | null;
  promedio_compra: number;
  estado_cartera: 'AL_DIA' | 'VENCIDA' | 'PARCIAL';
  saldo_pendiente: number;
}

export interface FrequentClient {
  cliente_id: string;
  nombre_completo: string;
  numero_documento: string;
  total_facturas: number;
  valor_total_compras: number;
}

export class ClientsService {
  /**
   * Crear un nuevo cliente
   */
  static async createClient(clientData: ClientCreate): Promise<Client> {
    try {
      const response = await apiRequest.post<Client>(ENDPOINTS.CLIENTS.BASE, clientData);
      return response.data;
    } catch (error: any) {
      console.error('Error al crear cliente:', error);
      const errorMessage = error.response?.data?.detail || 'Error al crear el cliente';
      throw new Error(Array.isArray(errorMessage) ? errorMessage[0]?.msg || 'Error de validación' : errorMessage);
    }
  }

  /**
   * Obtener cliente por ID
   */
  static async getClientById(clientId: string): Promise<Client> {
    try {
      const response = await apiRequest.get<Client>(`${ENDPOINTS.CLIENTS.BASE}/${clientId}`);
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener cliente:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener el cliente');
    }
  }

  /**
   * Buscar cliente por número de documento
   */
  static async getClientByDocument(numeroDocumento: string): Promise<Client> {
    try {
      const response = await apiRequest.get<Client>(`${ENDPOINTS.CLIENTS.BASE}/documento/${numeroDocumento}`);
      return response.data;
    } catch (error: any) {
      console.error('Error al buscar cliente por documento:', error);
      throw new Error(error.response?.data?.detail || 'Cliente no encontrado');
    }
  }

  /**
   * Listar clientes con paginación y filtros
   */
  static async getClients(params: ClientListParams = {}): Promise<PaginatedResponse<Client>> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page.toString());
      if (params.limit) queryParams.append('limit', Math.min(params.limit, 100).toString());
      if (params.search) queryParams.append('search', params.search);
      if (params.only_active !== undefined) queryParams.append('only_active', params.only_active.toString());
      if (params.tipo_cliente) queryParams.append('tipo_cliente', params.tipo_cliente);
      if (params.tipo_documento) queryParams.append('tipo_documento', params.tipo_documento);

      const url = queryParams.toString() ? 
        `${ENDPOINTS.CLIENTS.BASE}?${queryParams.toString()}` : 
        ENDPOINTS.CLIENTS.BASE;
      
      const response = await apiRequest.get<PaginatedResponse<Client>>(url);
      return response.data;
    } catch (error: any) {
      console.error('Error al listar clientes:', error);
      throw new Error(error.response?.data?.detail || 'Error al cargar los clientes');
    }
  }

  /**
   * Actualizar un cliente existente
   */
  static async updateClient(clientId: string, clientData: ClientUpdate): Promise<Client> {
    try {
      const response = await apiRequest.put<Client>(`${ENDPOINTS.CLIENTS.BASE}/${clientId}`, clientData);
      return response.data;
    } catch (error: any) {
      console.error('Error al actualizar cliente:', error);
      const errorMessage = error.response?.data?.detail || 'Error al actualizar el cliente';
      throw new Error(Array.isArray(errorMessage) ? errorMessage[0]?.msg || 'Error de validación' : errorMessage);
    }
  }

  /**
   * Desactivar cliente (soft delete)
   */
  static async deleteClient(clientId: string): Promise<{ message: string }> {
    try {
      const response = await apiRequest.delete<{ message: string }>(`${ENDPOINTS.CLIENTS.BASE}/${clientId}`);
      return response.data;
    } catch (error: any) {
      console.error('Error al desactivar cliente:', error);
      throw new Error(error.response?.data?.detail || 'Error al desactivar el cliente');
    }
  }

  /**
   * Reactivar cliente desactivado
   */
  static async activateClient(clientId: string): Promise<Client> {
    try {
      const response = await apiRequest.post<Client>(`${ENDPOINTS.CLIENTS.BASE}/${clientId}/activate`);
      return response.data;
    } catch (error: any) {
      console.error('Error al reactivar cliente:', error);
      throw new Error(error.response?.data?.detail || 'Error al reactivar el cliente');
    }
  }

  /**
   * Búsqueda rápida para autocompletado
   */
  static async quickSearch(query: string): Promise<ClientQuickSearch[]> {
    try {
      const response = await apiRequest.get<ClientQuickSearch[]>(
        `${ENDPOINTS.CLIENTS.BASE}/search/quick?q=${encodeURIComponent(query)}`
      );
      return response.data;
    } catch (error: any) {
      console.error('Error en búsqueda rápida:', error);
      throw new Error(error.response?.data?.detail || 'Error en la búsqueda');
    }
  }

  /**
   * Obtener clientes más frecuentes
   */
  static async getFrequentClients(limit: number = 10): Promise<FrequentClient[]> {
    try {
      const response = await apiRequest.get<FrequentClient[]>(
        `${ENDPOINTS.CLIENTS.BASE}/frecuentes/top?limit=${limit}`
      );
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener clientes frecuentes:', error);
      throw new Error(error.response?.data?.detail || 'Error al cargar clientes frecuentes');
    }
  }

  /**
   * Obtener estadísticas completas de un cliente
   */
  static async getClientStats(clientId: string): Promise<ClientStats> {
    try {
      const response = await apiRequest.get<ClientStats>(`${ENDPOINTS.CLIENTS.BASE}/${clientId}/estadisticas`);
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener estadísticas del cliente:', error);
      throw new Error(error.response?.data?.detail || 'Error al cargar estadísticas');
    }
  }

  /**
   * Filtrar clientes por tipo
   */
  static async getClientsByType(tipoCliente: ClientType, params: QueryParams = {}): Promise<PaginatedResponse<Client>> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page.toString());
      if (params.limit) queryParams.append('limit', Math.min(params.limit, 100).toString());
      if (params.search) queryParams.append('search', params.search);

      const url = queryParams.toString() ? 
        `${ENDPOINTS.CLIENTS.BASE}/tipo/${tipoCliente}?${queryParams.toString()}` : 
        `${ENDPOINTS.CLIENTS.BASE}/tipo/${tipoCliente}`;
      
      const response = await apiRequest.get<PaginatedResponse<Client>>(url);
      return response.data;
    } catch (error: any) {
      console.error('Error al filtrar clientes por tipo:', error);
      throw new Error(error.response?.data?.detail || 'Error al cargar clientes por tipo');
    }
  }

  // Utilidades para el frontend
  static getDocumentTypeLabel(type: DocumentType): string {
    const labels = {
      [DocumentType.CC]: 'Cédula de Ciudadanía',
      [DocumentType.NIT]: 'NIT',
      [DocumentType.CEDULA_EXTRANJERIA]: 'Cédula de Extranjería',
      [DocumentType.PASAPORTE]: 'Pasaporte'
    };
    return labels[type] || type;
  }

  static getClientTypeLabel(type: ClientType): string {
    const labels = {
      [ClientType.PERSONA_NATURAL]: 'Persona Natural',
      [ClientType.EMPRESA]: 'Empresa'
    };
    return labels[type] || type;
  }

  static getDocumentTypeLabels() {
    return {
      [DocumentType.CC]: 'Cédula de Ciudadanía',
      [DocumentType.NIT]: 'NIT',
      [DocumentType.CEDULA_EXTRANJERIA]: 'Cédula de Extranjería',
      [DocumentType.PASAPORTE]: 'Pasaporte'
    };
  }

  static getClientTypeLabels() {
    return {
      [ClientType.PERSONA_NATURAL]: 'Persona Natural',
      [ClientType.EMPRESA]: 'Empresa'
    };
  }

  static formatCurrency(value: number): string {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  }

  static validateDocumentNumber(type: DocumentType, number: string): boolean {
    switch (type) {
      case DocumentType.CC:
        return /^\d{6,10}$/.test(number);
      case DocumentType.NIT:
        return /^\d{9}-\d$/.test(number);
      case DocumentType.CEDULA_EXTRANJERIA:
        return /^[A-Z0-9]{6,10}$/.test(number);
      case DocumentType.PASAPORTE:
        return /^[A-Z0-9]{6,12}$/.test(number);
      default:
        return true;
    }
  }

  static formatDocumentNumber(type: DocumentType, number: string): string {
    if (type === DocumentType.NIT && number.length === 9) {
      // Auto-format NIT without verification digit
      return `${number}-${ClientsService.calculateNITVerificationDigit(number)}`;
    }
    return number;
  }

  static calculateNITVerificationDigit(nit: string): string {
    const weights = [71, 67, 59, 53, 47, 43, 41, 37, 29, 23, 19, 17, 13, 7, 3];
    let sum = 0;
    
    for (let i = 0; i < nit.length; i++) {
      sum += parseInt(nit[i]) * weights[weights.length - nit.length + i];
    }
    
    const remainder = sum % 11;
    if (remainder < 2) return remainder.toString();
    return (11 - remainder).toString();
  }
}