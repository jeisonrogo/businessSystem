/**
 * Componente para proteger rutas que requieren autenticación
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTenant } from '../../context/TenantContext';
import { CircularProgress, Box, Alert } from '@mui/material';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
  requiredPermissions?: string[];
  requireTenantContext?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRoles = [],
  requiredPermissions = [],
  requireTenantContext = false
}) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const { currentContext, hasPermission, isLoading: tenantLoading, needsLocalSelection } = useTenant();
  const location = useLocation();

  // Mostrar loading mientras se carga la autenticación o contexto
  if (isLoading || tenantLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  // Redirigir al login si no está autenticado
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Bloquear acceso si se necesita selección de local
  // El diálogo de selección se mostrará desde el TenantProvider
  if (needsLocalSelection) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  // Verificar roles si se especificaron
  if (requiredRoles.length > 0 && user) {
    const hasRequiredRole = requiredRoles.includes(user.rol);
    if (!hasRequiredRole) {
      return <Navigate to="/unauthorized" replace />;
    }
  }

  // Verificar contexto multi-tenant si se requiere
  if (requireTenantContext && !currentContext) {
    return (
      <Box p={3}>
        <Alert severity="warning">
          Se requiere seleccionar un contexto de tienda/local para acceder a esta página.
        </Alert>
      </Box>
    );
  }

  // Verificar permisos específicos si se especificaron
  if (requiredPermissions.length > 0) {
    const hasAllPermissions = requiredPermissions.every(permission => 
      hasPermission(permission)
    );
    if (!hasAllPermissions) {
      return (
        <Box p={3}>
          <Alert severity="error">
            No tienes permisos suficientes para acceder a esta página en el contexto actual.
          </Alert>
        </Box>
      );
    }
  }

  return <>{children}</>;
};

export default ProtectedRoute;