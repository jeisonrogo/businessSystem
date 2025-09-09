/**
 * Servicio para gestión de usuarios del sistema
 * Proporciona funciones para operaciones CRUD de usuarios por administradores
 */

import apiClient from './api';

// Interfaces para tipos de usuario
export interface User {
  id: string;
  email: string;
  nombre: string;
  rol: string;
  created_at: string;
  is_active: boolean;
  tienda_id?: string;
  local_principal_id?: string;
  locales_asignados?: LocalAssignment[];
  total_locales_asignados?: number;
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

// Interfaces para asignación de locales
export interface LocalAssignment {
  assignment_id: string;
  local_id: string;
  local_nombre: string;
  local_codigo: string;
  puede_vender: boolean;
  puede_ver_stock: boolean;
  puede_transferir: boolean;
  es_responsable: boolean;
  puede_modificar_precios: boolean;
  puede_aplicar_descuentos: boolean;
  puede_ver_reportes: boolean;
  puede_gestionar_usuarios: boolean;
  limite_descuento_porcentaje?: number;
  limite_credito_monto?: number;
  is_active: boolean;
  created_at: string;
}

export interface AvailableLocal {
  id: string;
  nombre: string;
  codigo: string;
  direccion?: string;
  ciudad?: string;
  is_active: boolean;
}

export interface CreateLocalAssignmentRequest {
  user_id: string;
  local_id: string;
  puede_vender?: boolean;
  puede_ver_stock?: boolean;
  puede_transferir?: boolean;
  es_responsable?: boolean;
  puede_modificar_precios?: boolean;
  puede_aplicar_descuentos?: boolean;
  puede_ver_reportes?: boolean;
  puede_gestionar_usuarios?: boolean;
  limite_descuento_porcentaje?: number;
  limite_credito_monto?: number;
}

export interface UpdateLocalAssignmentRequest {
  puede_vender?: boolean;
  puede_ver_stock?: boolean;
  puede_transferir?: boolean;
  es_responsable?: boolean;
  puede_modificar_precios?: boolean;
  puede_aplicar_descuentos?: boolean;
  puede_ver_reportes?: boolean;
  puede_gestionar_usuarios?: boolean;
  limite_descuento_porcentaje?: number;
  limite_credito_monto?: number;
  is_active?: boolean;
}

export const PERMISSION_PROFILES = {
  VENDEDOR: 'VENDEDOR',
  RESPONSABLE_LOCAL: 'RESPONSABLE_LOCAL',
  GERENTE_VENTAS: 'GERENTE_VENTAS',
  CONTADOR: 'CONTADOR',
  ADMINISTRADOR: 'ADMINISTRADOR'
} as const;

export const PERMISSION_PROFILE_LABELS = {
  [PERMISSION_PROFILES.VENDEDOR]: 'Vendedor',
  [PERMISSION_PROFILES.RESPONSABLE_LOCAL]: 'Responsable de Local',
  [PERMISSION_PROFILES.GERENTE_VENTAS]: 'Gerente de Ventas',
  [PERMISSION_PROFILES.CONTADOR]: 'Contador',
  [PERMISSION_PROFILES.ADMINISTRADOR]: 'Administrador'
};

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

      const response = await apiClient.get(`/users?${queryParams.toString()}`);
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener usuarios:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener la lista de usuarios');
    }
  }

  /**
   * Obtener un usuario por ID (información básica)
   */
  async getUserById(userId: string): Promise<User> {
    try {
      const response = await apiClient.get(`/users/${userId}`);
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
      const response = await apiClient.post('/users/', userData);
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
      const response = await apiClient.put(`/users/${userId}`, userData);
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
      await apiClient.delete(`/users/${userId}`);
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
      await apiClient.post(`/users/${userId}/activate`);
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
      await apiClient.post(`/users/${userId}/change-password`, passwordData);
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
      const response = await apiClient.get('/users/stats/summary');
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
      const response = await apiClient.get('/users/roles/available');
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

  // ================================
  // MÉTODOS PARA GESTIÓN DE LOCALES
  // ================================

  /**
   * Obtener las asignaciones de locales de un usuario
   */
  async getUserLocalAssignments(userId: string): Promise<LocalAssignment[]> {
    try {
      const response = await apiClient.get(`/users/${userId}/locales`);
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener asignaciones de locales:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener las asignaciones de locales');
    }
  }

  /**
   * Obtener locales disponibles para asignar a un usuario
   */
  async getAvailableLocalsForUser(userId: string): Promise<AvailableLocal[]> {
    try {
      const response = await apiClient.get(`/users/${userId}/locales/disponibles`);
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener locales disponibles:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener los locales disponibles');
    }
  }

  /**
   * Asignar un usuario a un local con permisos específicos
   */
  async assignUserToLocal(assignmentData: CreateLocalAssignmentRequest): Promise<LocalAssignment> {
    try {
      const response = await apiClient.post(`/users/${assignmentData.user_id}/locales`, assignmentData);
      return response.data;
    } catch (error: any) {
      console.error('Error al asignar usuario a local:', error);
      throw new Error(error.response?.data?.detail || 'Error al asignar el usuario al local');
    }
  }

  /**
   * Asignar un usuario a un local usando un perfil predefinido
   */
  async assignUserToLocalWithProfile(
    userId: string, 
    localId: string, 
    profile: keyof typeof PERMISSION_PROFILES
  ): Promise<LocalAssignment> {
    try {
      const response = await apiClient.post(`/users/${userId}/locales/perfil`, {
        local_id: localId,
        perfil: profile
      });
      return response.data;
    } catch (error: any) {
      console.error('Error al asignar perfil:', error);
      throw new Error(error.response?.data?.detail || 'Error al asignar el perfil al usuario');
    }
  }

  /**
   * Actualizar permisos de un usuario en un local
   */
  async updateUserLocalAssignment(
    userId: string,
    assignmentId: string,
    updateData: UpdateLocalAssignmentRequest
  ): Promise<LocalAssignment> {
    try {
      const response = await apiClient.put(`/users/${userId}/locales/${assignmentId}`, updateData);
      return response.data;
    } catch (error: any) {
      console.error('Error al actualizar asignación:', error);
      throw new Error(error.response?.data?.detail || 'Error al actualizar la asignación');
    }
  }

  /**
   * Remover un usuario de un local
   */
  async removeUserFromLocal(userId: string, assignmentId: string): Promise<void> {
    try {
      await apiClient.delete(`/users/${userId}/locales/${assignmentId}`);
    } catch (error: any) {
      console.error('Error al remover usuario del local:', error);
      throw new Error(error.response?.data?.detail || 'Error al remover el usuario del local');
    }
  }

  /**
   * Obtener información detallada de un usuario con sus asignaciones de locales
   */
  async getUserWithLocalAssignments(userId: string): Promise<User> {
    try {
      const response = await apiClient.get(`/users/${userId}`);
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener usuario con asignaciones:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener el usuario con sus asignaciones');
    }
  }

  /**
   * Obtener etiqueta de perfil de permisos
   */
  getPermissionProfileLabel(profile: string): string {
    return PERMISSION_PROFILE_LABELS[profile as keyof typeof PERMISSION_PROFILE_LABELS] || profile;
  }

  /**
   * Validar permisos de local
   */
  validateLocalPermissions(permissions: Partial<CreateLocalAssignmentRequest>): string[] {
    const errors: string[] = [];

    if (permissions.limite_descuento_porcentaje !== undefined) {
      if (permissions.limite_descuento_porcentaje < 0 || permissions.limite_descuento_porcentaje > 100) {
        errors.push('El límite de descuento debe estar entre 0% y 100%');
      }
    }

    if (permissions.limite_credito_monto !== undefined) {
      if (permissions.limite_credito_monto < 0) {
        errors.push('El límite de crédito no puede ser negativo');
      }
    }

    return errors;
  }

  /**
   * Formatear descripción de permisos
   */
  formatPermissionsDescription(assignment: LocalAssignment): string {
    const permissions = [];
    
    if (assignment.puede_vender) permissions.push('Vender');
    if (assignment.puede_ver_stock) permissions.push('Ver Stock');
    if (assignment.puede_transferir) permissions.push('Transferir');
    if (assignment.es_responsable) permissions.push('Responsable');
    if (assignment.puede_modificar_precios) permissions.push('Modificar Precios');
    if (assignment.puede_aplicar_descuentos) permissions.push('Aplicar Descuentos');
    if (assignment.puede_ver_reportes) permissions.push('Ver Reportes');
    if (assignment.puede_gestionar_usuarios) permissions.push('Gestionar Usuarios');

    return permissions.length > 0 ? permissions.join(', ') : 'Sin permisos específicos';
  }
}

// Exportar instancia única del servicio
export const usersService = new UsersService();
export default usersService;