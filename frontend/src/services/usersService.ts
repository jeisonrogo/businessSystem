/**
 * Servicio para gestión de usuarios del sistema
 * Proporciona funciones para operaciones CRUD de usuarios por administradores
 */

import { api } from './api';

// Interfaces para tipos de usuario
export interface User {
  id: string;
  email: string;
  nombre: string;
  rol: string;
  created_at: string;
  is_active: boolean;
}

export interface CreateUserRequest {
  email: string;
  nombre: string;
  rol: string;
  password: string;
}

export interface UpdateUserRequest {
  email?: string;
  nombre?: string;
  rol?: string;
  is_active?: boolean;
}

export interface ChangePasswordRequest {
  new_password: string;
}

export interface UserStats {
  total_users: number;
  active_users: number;
  users_by_role: Record<string, number>;
}

export interface UsersListParams {
  page?: number;
  limit?: number;
  search?: string;
  role?: string;
  is_active?: boolean;
}

// Constantes para roles
export const USER_ROLES = {
  ADMINISTRADOR: 'administrador',
  GERENTE_VENTAS: 'gerente_ventas',
  CONTADOR: 'contador',
  VENDEDOR: 'vendedor'
} as const;

export const USER_ROLE_LABELS = {
  [USER_ROLES.ADMINISTRADOR]: 'Administrador',
  [USER_ROLES.GERENTE_VENTAS]: 'Gerente de Ventas',
  [USER_ROLES.CONTADOR]: 'Contador',
  [USER_ROLES.VENDEDOR]: 'Vendedor'
};

class UsersService {
  /**
   * Obtener lista de usuarios con filtros y paginación
   */
  async getUsers(params: UsersListParams = {}): Promise<User[]> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', params.page.toString());
      if (params.limit) queryParams.append('limit', params.limit.toString());
      if (params.search) queryParams.append('search', params.search);
      if (params.role) queryParams.append('role', params.role);
      if (params.is_active !== undefined) queryParams.append('is_active', params.is_active.toString());

      const response = await api.get(`/users?${queryParams.toString()}`);
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener usuarios:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener la lista de usuarios');
    }
  }

  /**
   * Obtener un usuario por ID
   */
  async getUserById(userId: string): Promise<User> {
    try {
      const response = await api.get(`/users/${userId}`);
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener usuario:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener el usuario');
    }
  }

  /**
   * Crear un nuevo usuario
   */
  async createUser(userData: CreateUserRequest): Promise<User> {
    try {
      const response = await api.post('/users/', userData);
      return response.data;
    } catch (error: any) {
      console.error('Error al crear usuario:', error);
      throw new Error(error.response?.data?.detail || 'Error al crear el usuario');
    }
  }

  /**
   * Actualizar un usuario existente
   */
  async updateUser(userId: string, userData: UpdateUserRequest): Promise<User> {
    try {
      const response = await api.put(`/users/${userId}`, userData);
      return response.data;
    } catch (error: any) {
      console.error('Error al actualizar usuario:', error);
      throw new Error(error.response?.data?.detail || 'Error al actualizar el usuario');
    }
  }

  /**
   * Desactivar un usuario (soft delete)
   */
  async deleteUser(userId: string): Promise<void> {
    try {
      await api.delete(`/users/${userId}`);
    } catch (error: any) {
      console.error('Error al desactivar usuario:', error);
      throw new Error(error.response?.data?.detail || 'Error al desactivar el usuario');
    }
  }

  /**
   * Activar un usuario desactivado
   */
  async activateUser(userId: string): Promise<void> {
    try {
      await api.post(`/users/${userId}/activate`);
    } catch (error: any) {
      console.error('Error al activar usuario:', error);
      throw new Error(error.response?.data?.detail || 'Error al activar el usuario');
    }
  }

  /**
   * Cambiar contraseña de un usuario
   */
  async changeUserPassword(userId: string, passwordData: ChangePasswordRequest): Promise<void> {
    try {
      await api.post(`/users/${userId}/change-password`, passwordData);
    } catch (error: any) {
      console.error('Error al cambiar contraseña:', error);
      throw new Error(error.response?.data?.detail || 'Error al cambiar la contraseña');
    }
  }

  /**
   * Obtener estadísticas de usuarios
   */
  async getUserStats(): Promise<UserStats> {
    try {
      const response = await api.get('/users/stats/summary');
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener estadísticas:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener las estadísticas');
    }
  }

  /**
   * Obtener roles disponibles
   */
  async getAvailableRoles(): Promise<string[]> {
    try {
      const response = await api.get('/users/roles/available');
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener roles:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener los roles disponibles');
    }
  }

  /**
   * Validar datos de usuario
   */
  validateUserData(userData: Partial<CreateUserRequest | UpdateUserRequest>): string[] {
    const errors: string[] = [];

    if ('email' in userData && userData.email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(userData.email)) {
        errors.push('El email no tiene un formato válido');
      }
    }

    if ('nombre' in userData && userData.nombre) {
      if (userData.nombre.length < 2) {
        errors.push('El nombre debe tener al menos 2 caracteres');
      }
      if (userData.nombre.length > 100) {
        errors.push('El nombre no puede tener más de 100 caracteres');
      }
    }

    if ('password' in userData && userData.password) {
      if (userData.password.length < 8) {
        errors.push('La contraseña debe tener al menos 8 caracteres');
      }
    }

    if ('rol' in userData && userData.rol) {
      const validRoles = Object.values(USER_ROLES);
      if (!validRoles.includes(userData.rol as any)) {
        errors.push('El rol seleccionado no es válido');
      }
    }

    return errors;
  }

  /**
   * Formatear fecha de creación
   */
  formatCreatedDate(dateString: string): string {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('es-CO', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      return 'Fecha inválida';
    }
  }

  /**
   * Obtener color para el rol
   */
  getRoleColor(role: string): 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' {
    switch (role) {
      case USER_ROLES.ADMINISTRADOR:
        return 'error';
      case USER_ROLES.GERENTE_VENTAS:
        return 'warning';
      case USER_ROLES.CONTADOR:
        return 'info';
      case USER_ROLES.VENDEDOR:
        return 'success';
      default:
        return 'secondary';
    }
  }

  /**
   * Obtener etiqueta del rol
   */
  getRoleLabel(role: string): string {
    return USER_ROLE_LABELS[role as keyof typeof USER_ROLE_LABELS] || role;
  }
}

// Exportar instancia única del servicio
export const usersService = new UsersService();
export default usersService;