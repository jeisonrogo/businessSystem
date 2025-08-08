/**
 * Cliente HTTP para el Sistema de Gestión Empresarial
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { API_CONFIG, getApiUrl } from '../config/api';

// Crear instancia de axios con configuración base
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_CONFIG.BASE_URL}${API_CONFIG.API_VERSION}`,
  timeout: API_CONFIG.TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para requests - agregar token JWT
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para responses - manejar errores globales
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    // Si es 401 Unauthorized, limpiar token y redirigir al login
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;

// Helpers para requests comunes
export const apiRequest = {
  get: <T>(url: string, params?: any): Promise<AxiosResponse<T>> => 
    apiClient.get(url, { params }),
  
  post: <T>(url: string, data?: any): Promise<AxiosResponse<T>> => 
    apiClient.post(url, data),
  
  put: <T>(url: string, data?: any): Promise<AxiosResponse<T>> => 
    apiClient.put(url, data),
  
  patch: <T>(url: string, data?: any): Promise<AxiosResponse<T>> => 
    apiClient.patch(url, data),
  
  delete: <T>(url: string): Promise<AxiosResponse<T>> => 
    apiClient.delete(url),
};