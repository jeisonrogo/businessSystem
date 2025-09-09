/**
 * Contexto Multi-Tenant para React
 * 
 * Maneja el estado global del contexto de tenant (tienda/local),
 * permisos del usuario y funciones para cambiar entre contextos.
 */

import React, { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import { UserRole } from '../types/index';
import { 
  TenantContext as ITenantContext,
  Tienda, 
  Local, 
  UsuarioLocal,
  TipoContextoTenant,
  CambiarContextoRequest
} from '../types/multiTenant';
import { User } from '../types';
import { useAuth } from './AuthContext';
import { TenantService } from '../services/tenantService';
import LocalSelectionDialog from '../components/tenant/LocalSelectionDialog';

// ============================================================================
// INTERFACES DEL CONTEXTO
// ============================================================================

interface TenantContextType {
  // Estado actual del contexto
  currentContext: ITenantContext | null;
  isLoading: boolean;
  error: string | null;

  // Tiendas y locales disponibles
  availableStores: Tienda[];
  availableLocals: Local[];
  userPermissions: UsuarioLocal[];

  // Estado de selección actual
  selectedStore: Tienda | null;
  selectedLocal: Local | null;

  // Funciones de contexto
  switchContext: (request: CambiarContextoRequest) => Promise<void>;
  refreshContext: () => Promise<void>;
  loadUserStores: () => Promise<void>;
  loadStoreLocals: (storeId: string) => Promise<void>;

  // Utilidades de permisos
  hasPermission: (permission: string, localId?: string) => boolean;
  canAccessLocal: (localId: string) => boolean;
  isStoreManager: () => boolean;
  isLocalResponsible: (localId?: string) => boolean;

  // Estado de UI
  showStoreSwitcher: boolean;
  setShowStoreSwitcher: (show: boolean) => void;
  
  // Estado de selección de local inicial
  needsLocalSelection: boolean;
}

// ============================================================================
// CONTEXTO Y PROVIDER
// ============================================================================

const TenantContext = createContext<TenantContextType | undefined>(undefined);

interface TenantProviderProps {
  children: ReactNode;
}

export const TenantProvider: React.FC<TenantProviderProps> = ({ children }) => {
  // Estado del contexto
  const [currentContext, setCurrentContext] = useState<ITenantContext | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Estados de datos
  const [availableStores, setAvailableStores] = useState<Tienda[]>([]);
  const [availableLocals, setAvailableLocals] = useState<Local[]>([]);
  const [userPermissions, setUserPermissions] = useState<UsuarioLocal[]>([]);

  // Estado de selección
  const [selectedStore, setSelectedStore] = useState<Tienda | null>(null);
  const [selectedLocal, setSelectedLocal] = useState<Local | null>(null);

  // Estado de UI
  const [showStoreSwitcher, setShowStoreSwitcher] = useState(false);
  const [needsLocalSelection, setNeedsLocalSelection] = useState(false);
  const [localSelectionLoading, setLocalSelectionLoading] = useState(false);
  const [localSelectionError, setLocalSelectionError] = useState<string | null>(null);

  const { user, isAuthenticated } = useAuth();

  // ============================================================================
  // INICIALIZACIÓN Y EFECTOS
  // ============================================================================

  useEffect(() => {
    if (isAuthenticated && user) {
      initializeTenantContext();
    } else {
      resetTenantContext();
    }
  }, [isAuthenticated, user]);

  // Efecto para restaurar contexto desde localStorage al montar el componente
  useEffect(() => {
    const restoreContextFromStorage = () => {
      try {
        const storedContext = localStorage.getItem('tenant_context');
        if (storedContext && isAuthenticated && user) {
          const context = JSON.parse(storedContext);
          setCurrentContext(context);
          
          // Actualizar también los estados de selección
          if (context.local_id && availableLocals.length > 0) {
            const local = availableLocals.find(l => l.id === context.local_id);
            setSelectedLocal(local || null);
          }
          
          if (context.tienda_id && availableStores.length > 0) {
            const store = availableStores.find(s => s.id === context.tienda_id);
            setSelectedStore(store || null);
          }
          
          console.log('✅ Contexto restaurado desde localStorage:', context);
        }
      } catch (error) {
        console.warn('Error al restaurar contexto desde localStorage:', error);
        localStorage.removeItem('tenant_context');
      }
    };

    restoreContextFromStorage();
  }, [isAuthenticated, user, availableLocals, availableStores]);

  const initializeTenantContext = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Cargar tiendas disponibles primero
      await loadUserStores();
      
      // Cargar locales disponibles basados en el rol del usuario
      const userLocals = await TenantService.getAvailableLocals();
      setAvailableLocals(userLocals);

      // Decidir el flujo según el rol y locales disponibles  
      if (user?.rol === UserRole.ADMINISTRADOR || user?.rol === UserRole.GERENTE_VENTAS) {
        // Para administradores y gerentes, usar el primer local disponible
        if (userLocals.length > 0) {
          await switchToLocal(userLocals[0].id);
        }
      } else {
        // Para usuarios regulares, necesitan selección de local obligatoria
        if (userLocals.length === 0) {
          // Usuario sin locales asignados - mostrar mensaje de error
          setNeedsLocalSelection(true);
          setError('No tienes locales asignados. Contacta al administrador.');
        } else if (userLocals.length === 1) {
          // Usuario con un solo local - auto-seleccionar
          await switchToLocal(userLocals[0].id);
        } else {
          // Usuario con múltiples locales - mostrar selector
          setNeedsLocalSelection(true);
        }
      }

      // Intentar cargar contexto actual existente si no se configuró uno nuevo
      if (!currentContext) {
        try {
          const context = await TenantService.getCurrentContext();
          setCurrentContext(context);
          
          // Persistir contexto en localStorage para los interceptors de API
          localStorage.setItem('tenant_context', JSON.stringify(context));
        } catch (contextErr: any) {
          console.warn('No se pudo cargar el contexto inicial del usuario:', contextErr.message);
        }
      }
    } catch (err: any) {
      console.error('Error al inicializar contexto de tenant:', err);
      setError(err.message || 'Error al cargar contexto de tenant');
    } finally {
      setIsLoading(false);
    }
  };

  const resetTenantContext = () => {
    setCurrentContext(null);
    setAvailableStores([]);
    setAvailableLocals([]);
    setUserPermissions([]);
    setSelectedStore(null);
    setSelectedLocal(null);
    setIsLoading(false);
    setError(null);
    setNeedsLocalSelection(false);
    setLocalSelectionLoading(false);
    setLocalSelectionError(null);

    // Limpiar contexto del localStorage
    localStorage.removeItem('tenant_context');
  };

  // ============================================================================
  // FUNCIONES DEL CONTEXTO
  // ============================================================================

  const refreshContext = async (): Promise<void> => {
    try {
      const context = await TenantService.getCurrentContext();
      setCurrentContext(context);

      // Persistir contexto en localStorage para los interceptors de API
      localStorage.setItem('tenant_context', JSON.stringify(context));

      // Actualizar store y local seleccionados basado en el contexto
      if (context.tienda_id) {
        const store = availableStores.find(s => s.id === context.tienda_id);
        setSelectedStore(store || null);
      }

      if (context.local_id) {
        const local = availableLocals.find(l => l.id === context.local_id);
        setSelectedLocal(local || null);
      }
    } catch (err: any) {
      console.error('Error al obtener contexto actual:', err);
      throw err;
    }
  };

  const loadUserStores = async (): Promise<void> => {
    try {
      const stores = await TenantService.getUserStores();
      const storesList = Array.isArray(stores) ? stores : [];
      setAvailableStores(storesList);
      
      // Si no hay store seleccionada pero hay contexto, seleccionar la primera
      if (!selectedStore && storesList.length > 0 && currentContext?.tienda_id) {
        const contextStore = storesList.find(s => s.id === currentContext.tienda_id);
        setSelectedStore(contextStore || storesList[0]);
      }
    } catch (err: any) {
      console.error('Error al cargar tiendas del usuario:', err);
      // No re-throw the error, just set empty array and continue
      setAvailableStores([]);
    }
  };

  const loadStoreLocals = async (storeId: string): Promise<void> => {
    try {
      // Buscar la tienda seleccionada y actualizar el estado
      const selectedStoreObj = availableStores.find(store => store.id === storeId);
      if (selectedStoreObj) {
        setSelectedStore(selectedStoreObj);
      }
      
      // Cargar locales siempre
      const locals = await TenantService.getStoreLocals(storeId);
      setAvailableLocals(locals);
      
      // Intentar cargar permisos solo si el usuario tiene contexto local
      try {
        if (currentContext?.tiene_contexto_local) {
          const permissions = await TenantService.getUserPermissions(storeId);
          setUserPermissions(permissions);
        } else {
          setUserPermissions([]);
        }
      } catch (permissionsErr) {
        console.warn('No se pudieron cargar permisos de usuario:', permissionsErr);
        setUserPermissions([]);
      }
    } catch (err: any) {
      console.error('Error al cargar locales de la tienda:', err);
      // No re-throw, just set empty arrays
      setAvailableLocals([]);
      setUserPermissions([]);
    }
  };

  const switchContext = async (request: CambiarContextoRequest): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      // Realizar cambio de contexto en el backend
      const newContext = await TenantService.switchContext(request);
      setCurrentContext(newContext);

      // Persistir contexto en localStorage para los interceptors de API
      localStorage.setItem('tenant_context', JSON.stringify(newContext));

      // Actualizar estados locales
      if (request.local_id) {
        const local = availableLocals.find(l => l.id === request.local_id);
        setSelectedLocal(local || null);
      } else {
        setSelectedLocal(null);
      }

      // Cerrar el selector si estaba abierto
      setShowStoreSwitcher(false);
    } catch (err: any) {
      console.error('Error al cambiar contexto:', err);
      setError(err.message || 'Error al cambiar contexto');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Función auxiliar para cambiar a un local específico
  const switchToLocal = async (localId: string): Promise<void> => {
    await switchContext({ local_id: localId });
    setNeedsLocalSelection(false); // Ocultar selector después de la selección exitosa
  };

  // Manejador para la selección de local desde el diálogo
  const handleLocalSelection = async (localId: string): Promise<void> => {
    setLocalSelectionLoading(true);
    setLocalSelectionError(null);

    try {
      await switchToLocal(localId);
    } catch (error: any) {
      console.error('Error al seleccionar local:', error);
      setLocalSelectionError(error.message || 'Error al seleccionar el local');
    } finally {
      setLocalSelectionLoading(false);
    }
  };

  // ============================================================================
  // UTILIDADES DE PERMISOS
  // ============================================================================

  const hasPermission = useCallback((permission: string, localId?: string): boolean => {
    if (!currentContext || !user) return false;

    // Los administradores tienen todos los permisos
    if (user.rol === UserRole.ADMINISTRADOR) return true;

    // Si se especifica un local, verificar permisos específicos
    if (localId) {
      const localPermissions = userPermissions.find(up => up.local_id === localId);
      if (!localPermissions || !localPermissions.is_active) return false;

      return checkSpecificPermission(localPermissions, permission);
    }

    // Si hay contexto de local, verificar permisos en ese local
    if (currentContext.tiene_contexto_local && currentContext.local_id) {
      const localPermissions = userPermissions.find(up => up.local_id === currentContext.local_id);
      if (!localPermissions || !localPermissions.is_active) return false;

      return checkSpecificPermission(localPermissions, permission);
    }

    // Permisos a nivel de tienda para gerentes
    if (user.rol === UserRole.GERENTE_VENTAS) {
      return ['ver_reportes', 'consulta_stock', 'gestion_usuarios'].includes(permission);
    }

    return currentContext.permisos_disponibles.includes(permission);
  }, [currentContext, user, userPermissions]);

  const canAccessLocal = useCallback((localId: string): boolean => {
    if (!user || !currentContext) return false;
    
    // Los administradores pueden acceder a cualquier local
    if (user.rol === UserRole.ADMINISTRADOR) return true;

    // Verificar si el usuario tiene permisos en ese local
    const localPermissions = userPermissions.find(up => up.local_id === localId && up.is_active);
    return !!localPermissions;
  }, [user, currentContext, userPermissions]);

  const isStoreManager = useCallback((): boolean => {
    return user?.rol === UserRole.ADMINISTRADOR || user?.rol === UserRole.GERENTE_VENTAS;
  }, [user]);

  const isLocalResponsible = useCallback((localId?: string): boolean => {
    if (!user || !currentContext) return false;
    
    if (user.rol === UserRole.ADMINISTRADOR) return true;

    const targetLocalId = localId || currentContext.local_id;
    if (!targetLocalId) return false;

    const localPermissions = userPermissions.find(up => up.local_id === targetLocalId);
    return localPermissions?.es_responsable || false;
  }, [user, currentContext, userPermissions]);

  // ============================================================================
  // UTILIDADES HELPER
  // ============================================================================

  const checkSpecificPermission = (permissions: UsuarioLocal, permission: string): boolean => {
    const permissionMap: { [key: string]: keyof UsuarioLocal } = {
      'venta': 'puede_vender',
      'consulta_stock': 'puede_ver_stock',
      'transferencia': 'puede_transferir',
      'modificar_precios': 'puede_modificar_precios',
      'aplicar_descuentos': 'puede_aplicar_descuentos',
      'ver_reportes': 'puede_ver_reportes',
      'gestion_usuarios': 'puede_gestionar_usuarios'
    };

    const permissionField = permissionMap[permission];
    if (!permissionField) return false;

    return permissions[permissionField] as boolean;
  };

  // ============================================================================
  // VALOR DEL CONTEXTO
  // ============================================================================

  const value: TenantContextType = {
    // Estado actual
    currentContext,
    isLoading,
    error,

    // Datos disponibles
    availableStores,
    availableLocals,
    userPermissions,

    // Selección actual
    selectedStore,
    selectedLocal,

    // Funciones
    switchContext,
    refreshContext,
    loadUserStores,
    loadStoreLocals,

    // Utilidades de permisos
    hasPermission,
    canAccessLocal,
    isStoreManager,
    isLocalResponsible,

    // Estado de UI
    showStoreSwitcher,
    setShowStoreSwitcher,
    
    // Estado de selección de local inicial
    needsLocalSelection
  };

  return (
    <TenantContext.Provider value={value}>
      {children}
      
      {/* Diálogo de selección de local inicial */}
      {needsLocalSelection && user && (
        <LocalSelectionDialog
          open={needsLocalSelection}
          user={{
            id: user.id,
            nombre: user.nombre,
            rol: user.rol
          }}
          availableLocals={availableLocals}
          onLocalSelected={handleLocalSelection}
          loading={localSelectionLoading}
          error={localSelectionError}
        />
      )}
    </TenantContext.Provider>
  );
};

// ============================================================================
// HOOK PERSONALIZADO
// ============================================================================

export const useTenant = (): TenantContextType => {
  const context = useContext(TenantContext);
  if (context === undefined) {
    throw new Error('useTenant debe ser usado dentro de un TenantProvider');
  }
  return context;
};

// ============================================================================
// HOOKS DE CONVENIENCIA
// ============================================================================

export const useCurrentStore = () => {
  const { selectedStore, currentContext } = useTenant();
  return selectedStore;
};

export const useCurrentLocal = () => {
  const { selectedLocal, currentContext } = useTenant();
  return selectedLocal;
};

export const useHasPermission = (permission: string, localId?: string) => {
  const { hasPermission } = useTenant();
  return hasPermission(permission, localId);
};

export const useIsStoreManager = () => {
  const { isStoreManager } = useTenant();
  return isStoreManager();
};

export const useCanAccessLocal = (localId: string) => {
  const { canAccessLocal } = useTenant();
  return canAccessLocal(localId);
};