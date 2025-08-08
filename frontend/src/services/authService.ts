/**
 * Servicio de Autenticación
 */

import { LoginRequest, LoginResponse, User } from '../types';
import { ENDPOINTS } from '../config/api';
import { apiRequest } from './api';

export class AuthService {
  /**
   * Iniciar sesión
   */
  static async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await apiRequest.post<LoginResponse>(
      ENDPOINTS.AUTH.LOGIN, 
      credentials
    );
    
    const { access_token, user } = response.data;
    
    // Guardar token y usuario en localStorage
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('user', JSON.stringify(user));
    
    return response.data;
  }

  /**
   * Cerrar sesión
   */
  static logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  }

  /**
   * Obtener información del usuario actual
   */
  static async getCurrentUser(): Promise<User> {
    const response = await apiRequest.get<User>(ENDPOINTS.AUTH.ME);
    return response.data;
  }

  /**
   * Verificar si el usuario está autenticado
   */
  static isAuthenticated(): boolean {
    const token = localStorage.getItem('access_token');
    return !!token;
  }

  /**
   * Obtener el token de acceso
   */
  static getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  /**
   * Obtener el usuario actual del localStorage
   */
  static getCurrentUserFromStorage(): User | null {
    const userJson = localStorage.getItem('user');
    if (!userJson) return null;
    
    try {
      return JSON.parse(userJson) as User;
    } catch {
      return null;
    }
  }

  /**
   * Verificar si el usuario tiene un rol específico
   */
  static hasRole(requiredRole: string): boolean {
    const user = this.getCurrentUserFromStorage();
    return user?.rol === requiredRole;
  }

  /**
   * Verificar si el usuario tiene alguno de los roles especificados
   */
  static hasAnyRole(roles: string[]): boolean {
    const user = this.getCurrentUserFromStorage();
    return user ? roles.includes(user.rol) : false;
  }
}