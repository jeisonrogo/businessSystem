/**
 * Servicio de Contabilidad
 * Maneja las operaciones CRUD del plan de cuentas contables
 */

import { 
  Account, 
  AccountCreate, 
  AccountUpdate, 
  AccountListResponse,
  AccountHierarchy,
  MainAccountsResponse,
  SubAccountsResponse,
  SeedAccountsResponse,
  AccountType,
  QueryParams 
} from '../types';
import { ENDPOINTS } from '../config/api';
import { apiRequest } from './api';

export interface AccountQueryParams extends QueryParams {
  tipo_cuenta?: AccountType;
  only_main_accounts?: boolean;
}

export class AccountingService {
  /**
   * Obtener lista de cuentas contables con paginación y filtros
   */
  static async getAccounts(params?: AccountQueryParams): Promise<AccountListResponse> {
    try {
      const response = await apiRequest.get<AccountListResponse>(ENDPOINTS.ACCOUNTING.BASE, params);
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener cuentas contables:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener las cuentas contables');
    }
  }

  /**
   * Obtener cuenta contable por ID
   */
  static async getAccountById(accountId: string): Promise<Account> {
    try {
      const response = await apiRequest.get<Account>(`${ENDPOINTS.ACCOUNTING.BASE}/${accountId}`);
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener cuenta contable:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener la cuenta contable');
    }
  }

  /**
   * Obtener cuenta contable por código
   */
  static async getAccountByCode(code: string): Promise<Account> {
    try {
      const response = await apiRequest.get<Account>(ENDPOINTS.ACCOUNTING.BY_CODE(code));
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener cuenta por código:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener la cuenta por código');
    }
  }

  /**
   * Crear nueva cuenta contable
   */
  static async createAccount(accountData: AccountCreate): Promise<Account> {
    try {
      const response = await apiRequest.post<Account>(ENDPOINTS.ACCOUNTING.BASE, accountData);
      return response.data;
    } catch (error: any) {
      console.error('Error al crear cuenta contable:', error);
      throw new Error(error.response?.data?.detail || 'Error al crear la cuenta contable');
    }
  }

  /**
   * Actualizar cuenta contable existente
   */
  static async updateAccount(accountId: string, accountData: AccountUpdate): Promise<Account> {
    try {
      const response = await apiRequest.put<Account>(`${ENDPOINTS.ACCOUNTING.BASE}/${accountId}`, accountData);
      return response.data;
    } catch (error: any) {
      console.error('Error al actualizar cuenta contable:', error);
      throw new Error(error.response?.data?.detail || 'Error al actualizar la cuenta contable');
    }
  }

  /**
   * Eliminar cuenta contable (soft delete)
   */
  static async deleteAccount(accountId: string): Promise<{ message: string }> {
    try {
      const response = await apiRequest.delete<{ message: string }>(`${ENDPOINTS.ACCOUNTING.BASE}/${accountId}`);
      return response.data;
    } catch (error: any) {
      console.error('Error al eliminar cuenta contable:', error);
      throw new Error(error.response?.data?.detail || 'Error al eliminar la cuenta contable');
    }
  }

  /**
   * Obtener plan de cuentas jerárquico
   */
  static async getAccountHierarchy(): Promise<AccountHierarchy> {
    try {
      const response = await apiRequest.get<AccountHierarchy>(ENDPOINTS.ACCOUNTING.HIERARCHY);
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener plan jerárquico:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener el plan de cuentas jerárquico');
    }
  }

  /**
   * Obtener cuentas principales (sin cuenta padre)
   */
  static async getMainAccounts(accountType?: AccountType): Promise<MainAccountsResponse> {
    try {
      const params = accountType ? { tipo_cuenta: accountType } : undefined;
      const response = await apiRequest.get<MainAccountsResponse>(ENDPOINTS.ACCOUNTING.MAIN_ACCOUNTS, params);
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener cuentas principales:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener las cuentas principales');
    }
  }

  /**
   * Obtener subcuentas de una cuenta padre
   */
  static async getSubAccounts(parentAccountId: string): Promise<SubAccountsResponse> {
    try {
      const response = await apiRequest.get<SubAccountsResponse>(ENDPOINTS.ACCOUNTING.SUB_ACCOUNTS(parentAccountId));
      return response.data;
    } catch (error: any) {
      console.error('Error al obtener subcuentas:', error);
      throw new Error(error.response?.data?.detail || 'Error al obtener las subcuentas');
    }
  }

  /**
   * Poblar base de datos con plan de cuentas estándar de Colombia
   */
  static async seedAccountsPlanColombia(): Promise<SeedAccountsResponse> {
    try {
      const response = await apiRequest.post<SeedAccountsResponse>(ENDPOINTS.ACCOUNTING.SEED_COLOMBIA, {});
      return response.data;
    } catch (error: any) {
      console.error('Error al poblar plan de cuentas:', error);
      throw new Error(error.response?.data?.detail || 'Error al poblar el plan de cuentas');
    }
  }

  /**
   * Validar código de cuenta (1-8 dígitos numéricos)
   */
  static validateAccountCode(code: string): { isValid: boolean; error?: string } {
    if (!code) {
      return { isValid: false, error: 'El código es requerido' };
    }

    if (!/^\d+$/.test(code)) {
      return { isValid: false, error: 'El código debe contener solo números' };
    }

    if (code.length < 1 || code.length > 8) {
      return { isValid: false, error: 'El código debe tener entre 1 y 8 dígitos' };
    }

    return { isValid: true };
  }

  /**
   * Obtener etiquetas de tipos de cuenta en español
   */
  static getAccountTypeLabels(): Record<AccountType, string> {
    return {
      [AccountType.ACTIVO]: 'Activo',
      [AccountType.PASIVO]: 'Pasivo',
      [AccountType.PATRIMONIO]: 'Patrimonio',
      [AccountType.INGRESO]: 'Ingreso',
      [AccountType.EGRESO]: 'Egreso',
    };
  }

  /**
   * Obtener colores para tipos de cuenta
   */
  static getAccountTypeColors(): Record<AccountType, string> {
    return {
      [AccountType.ACTIVO]: '#4caf50',      // Verde
      [AccountType.PASIVO]: '#f44336',      // Rojo
      [AccountType.PATRIMONIO]: '#9c27b0',  // Púrpura
      [AccountType.INGRESO]: '#2196f3',     // Azul
      [AccountType.EGRESO]: '#ff9800',      // Naranja
    };
  }
}