/**
 * Indicador de Contexto Multi-Tenant
 * 
 * Muestra el contexto actual del usuario (tienda/local) en la barra de navegación
 * y proporciona acceso rápido al selector de contexto.
 */

import React from 'react';
import {
  Box,
  Button,
  Typography,
  Avatar,
  Chip,
  Tooltip,
  CircularProgress,
  Alert,
  Collapse,
  IconButton,
  Paper,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  Business as BusinessIcon,
  LocationOn as LocationIcon,
  Store as StoreIcon,
  SwapHoriz as SwapIcon,
  ExpandLess,
  ExpandMore,
  Info as InfoIcon,
  Security as SecurityIcon,
  Group as GroupIcon,
  Inventory as InventoryIcon
} from '@mui/icons-material';

import { useTenant } from '../../context/TenantContext';
import { TipoLocal } from '../../types/multiTenant';

// ============================================================================
// INTERFACES
// ============================================================================

interface TenantIndicatorProps {
  variant?: 'compact' | 'expanded' | 'detailed';
  onSwitchClick?: () => void;
  showPermissions?: boolean;
}

// ============================================================================
// COMPONENTE PRINCIPAL
// ============================================================================

export const TenantIndicator: React.FC<TenantIndicatorProps> = ({
  variant = 'compact',
  onSwitchClick,
  showPermissions = false
}) => {
  const {
    currentContext,
    selectedStore,
    selectedLocal,
    isLoading,
    error,
    hasPermission,
    isStoreManager,
    setShowStoreSwitcher
  } = useTenant();

  const [expanded, setExpanded] = React.useState(false);

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const handleSwitchClick = () => {
    if (onSwitchClick) {
      onSwitchClick();
    } else {
      setShowStoreSwitcher(true);
    }
  };

  const toggleExpanded = () => {
    setExpanded(!expanded);
  };

  // ============================================================================
  // RENDER HELPERS
  // ============================================================================

  const renderCompactView = () => {
    if (isLoading) {
      return (
        <Box display="flex" alignItems="center" gap={1}>
          <CircularProgress size={16} />
          <Typography variant="body2">Cargando contexto...</Typography>
        </Box>
      );
    }

    if (error) {
      return (
        <Tooltip title={`Error en el contexto multi-tenant: ${error}`}>
          <Chip
            icon={<InfoIcon />}
            label="Error de contexto"
            color="error"
            variant="outlined"
            size="small"
          />
        </Tooltip>
      );
    }

    if (!currentContext) {
      return (
        <Tooltip title="Selecciona una tienda y local para comenzar">
          <Chip
            icon={<SwapIcon />}
            label="Seleccionar contexto"
            color="primary"
            variant="outlined"
            size="small"
            onClick={handleSwitchClick}
            clickable
          />
        </Tooltip>
      );
    }

    return (
      <Box display="flex" alignItems="center" gap={1}>
        <Avatar sx={{ width: 24, height: 24, bgcolor: 'primary.main' }}>
          {currentContext.tiene_contexto_local ? (
            <LocationIcon fontSize="small" />
          ) : (
            <BusinessIcon fontSize="small" />
          )}
        </Avatar>
        
        <Box>
          <Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>
            {currentContext.tienda_nombre}
          </Typography>
          {currentContext.tiene_contexto_local && currentContext.local_nombre && (
            <Typography variant="caption" color="text.secondary" noWrap sx={{ maxWidth: 150 }}>
              → {currentContext.local_nombre}
            </Typography>
          )}
        </Box>
        
        <Tooltip title="Cambiar contexto">
          <IconButton size="small" onClick={handleSwitchClick} sx={{ ml: 1 }}>
            <SwapIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
    );
  };

  const renderExpandedView = () => {
    if (isLoading) {
      return (
        <Paper sx={{ p: 2 }}>
          <Box display="flex" alignItems="center" gap={2}>
            <CircularProgress size={24} />
            <Typography>Cargando contexto multi-tenant...</Typography>
          </Box>
        </Paper>
      );
    }

    if (error || !currentContext) {
      return (
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="subtitle2">Error en el contexto</Typography>
          <Typography variant="body2">{error || 'No se pudo cargar el contexto'}</Typography>
        </Alert>
      );
    }

    return (
      <Paper sx={{ p: 2 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
          <Typography variant="h6" color="primary">
            Contexto actual
          </Typography>
          <Button
            variant="outlined"
            size="small"
            startIcon={<SwapIcon />}
            onClick={handleSwitchClick}
          >
            Cambiar
          </Button>
        </Box>
        
        <Box display="flex" alignItems="start" gap={2}>
          <Avatar sx={{ bgcolor: 'primary.main' }}>
            <BusinessIcon />
          </Avatar>
          
          <Box flex={1}>
            <Typography variant="subtitle1">
              {currentContext.tienda_nombre}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Código: {currentContext.tienda_codigo}
            </Typography>
            
            {currentContext.tiene_contexto_local && (
              <Box sx={{ mt: 1, pl: 2, borderLeft: 2, borderColor: 'primary.light' }}>
                <Box display="flex" alignItems="center" gap={1}>
                  <LocationIcon color="action" fontSize="small" />
                  <Typography variant="subtitle2">
                    {currentContext.local_nombre}
                  </Typography>
                </Box>
                <Typography variant="caption" color="text.secondary">
                  Código: {currentContext.local_codigo}
                </Typography>
                {selectedLocal && (
                  <Chip
                    label={selectedLocal.tipo_local || 'Local'}
                    size="small"
                    variant="outlined"
                    sx={{ ml: 1, mt: 0.5 }}
                  />
                )}
              </Box>
            )}
          </Box>
        </Box>
        
        {showPermissions && (
          <Box sx={{ mt: 2 }}>
            <Button
              size="small"
              onClick={toggleExpanded}
              endIcon={expanded ? <ExpandLess /> : <ExpandMore />}
              sx={{ mb: 1 }}
            >
              Permisos ({currentContext.permisos_disponibles.length})
            </Button>
            
            <Collapse in={expanded}>
              <Paper variant="outlined" sx={{ p: 1 }}>
                {renderPermissionsList()}
              </Paper>
            </Collapse>
          </Box>
        )}
      </Paper>
    );
  };

  const renderDetailedView = () => {
    if (isLoading) {
      return (
        <Box display="flex" justifyContent="center" p={3}>
          <CircularProgress />
        </Box>
      );
    }

    if (error || !currentContext) {
      return (
        <Alert severity="error">
          <Typography variant="h6">Error en el contexto</Typography>
          <Typography>{error || 'No se pudo cargar el contexto multi-tenant'}</Typography>
        </Alert>
      );
    }

    return (
      <Paper sx={{ p: 3 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
          <Typography variant="h5" color="primary">
            Información del contexto
          </Typography>
          <Button
            variant="contained"
            startIcon={<SwapIcon />}
            onClick={handleSwitchClick}
          >
            Cambiar contexto
          </Button>
        </Box>

        {/* Información de la tienda */}
        <Box sx={{ mb: 3 }}>
          <Box display="flex" alignItems="center" gap={2} mb={2}>
            <Avatar sx={{ bgcolor: 'primary.main', width: 48, height: 48 }}>
              <BusinessIcon />
            </Avatar>
            <Box>
              <Typography variant="h6">{currentContext.tienda_nombre}</Typography>
              <Typography variant="body2" color="text.secondary">
                Código: {currentContext.tienda_codigo}
              </Typography>
            </Box>
          </Box>
          
          {selectedStore && (
            <Box sx={{ pl: 7 }}>
              <Typography variant="body2" color="text.secondary">
                {selectedStore.descripcion}
              </Typography>
              {selectedStore.direccion && (
                <Typography variant="body2" color="text.secondary">
                  📍 {selectedStore.direccion}
                </Typography>
              )}
            </Box>
          )}
        </Box>

        {/* Información del local */}
        {currentContext.tiene_contexto_local && (
          <Box sx={{ mb: 3 }}>
            <Divider sx={{ mb: 2 }} />
            <Box display="flex" alignItems="center" gap={2} mb={2}>
              <Avatar sx={{ bgcolor: getLocalColor(), width: 48, height: 48 }}>
                {getLocalIcon()}
              </Avatar>
              <Box>
                <Typography variant="h6">{currentContext.local_nombre}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Código: {currentContext.local_codigo}
                </Typography>
                {selectedLocal && (
                  <Chip
                    label={selectedLocal.tipo_local || 'Local'}
                    size="small"
                    color="primary"
                    variant="outlined"
                    sx={{ mt: 0.5 }}
                  />
                )}
              </Box>
            </Box>
            
            {selectedLocal && (
              <Box sx={{ pl: 7 }}>
                {selectedLocal.descripcion && (
                  <Typography variant="body2" color="text.secondary">
                    {selectedLocal.descripcion}
                  </Typography>
                )}
                {(selectedLocal.direccion || selectedLocal.ciudad) && (
                  <Typography variant="body2" color="text.secondary">
                    📍 {selectedLocal.direccion || 'Sin dirección'}{selectedLocal.ciudad ? `, ${selectedLocal.ciudad}` : ''}
                  </Typography>
                )}
                <Box display="flex" gap={3} mt={1}>
                  <Typography variant="body2">
                    💼 {selectedLocal.total_productos || 0} productos
                  </Typography>
                  {selectedLocal.valor_inventario && (
                    <Typography variant="body2">
                      💰 ${selectedLocal.valor_inventario.toLocaleString()}
                    </Typography>
                  )}
                </Box>
              </Box>
            )}
          </Box>
        )}

        {/* Lista de permisos */}
        <Box>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Permisos disponibles
          </Typography>
          {renderPermissionsList()}
        </Box>
      </Paper>
    );
  };

  const renderPermissionsList = () => {
    if (!currentContext) return null;

    const permissions = [
      { key: 'venta', label: 'Realizar ventas', icon: <StoreIcon /> },
      { key: 'consulta_stock', label: 'Consultar inventario', icon: <InventoryIcon /> },
      { key: 'transferencia', label: 'Gestionar transferencias', icon: <SwapIcon /> },
      { key: 'modificar_precios', label: 'Modificar precios', icon: <InfoIcon /> },
      { key: 'ver_reportes', label: 'Ver reportes', icon: <InfoIcon /> },
      { key: 'gestion_usuarios', label: 'Gestionar usuarios', icon: <GroupIcon /> }
    ];

    return (
      <List dense>
        {permissions.map(({ key, label, icon }) => {
          const hasThisPermission = hasPermission(key);
          return (
            <ListItem key={key}>
              <ListItemIcon sx={{ color: hasThisPermission ? 'success.main' : 'text.disabled' }}>
                {icon}
              </ListItemIcon>
              <ListItemText
                primary={label}
                sx={{
                  color: hasThisPermission ? 'text.primary' : 'text.disabled',
                  textDecoration: hasThisPermission ? 'none' : 'line-through'
                }}
              />
              <Chip
                label={hasThisPermission ? 'SÍ' : 'NO'}
                size="small"
                color={hasThisPermission ? 'success' : 'default'}
                variant={hasThisPermission ? 'filled' : 'outlined'}
              />
            </ListItem>
          );
        })}
        
        {isStoreManager() && (
          <ListItem>
            <ListItemIcon sx={{ color: 'warning.main' }}>
              <SecurityIcon />
            </ListItemIcon>
            <ListItemText
              primary="Administrador de tienda"
              secondary="Acceso completo a todas las funciones"
            />
            <Chip
              label="ADMIN"
              size="small"
              color="warning"
              variant="filled"
            />
          </ListItem>
        )}
      </List>
    );
  };

  // ============================================================================
  // UTILIDADES
  // ============================================================================

  const getLocalIcon = () => {
    if (!selectedLocal) return <LocationIcon />;
    
    switch (selectedLocal.tipo_local || 'SUCURSAL') {
      case TipoLocal.SUCURSAL:
        return <StoreIcon />;
      case TipoLocal.ALMACEN:
        return <InventoryIcon />;
      case TipoLocal.SHOWROOM:
        return <BusinessIcon />;
      case TipoLocal.VIRTUAL:
        return <LocationIcon />;
      default:
        return <LocationIcon />;
    }
  };

  const getLocalColor = () => {
    if (!selectedLocal) return 'secondary.main';
    
    switch (selectedLocal.tipo_local || 'SUCURSAL') {
      case TipoLocal.SUCURSAL:
        return 'primary.main';
      case TipoLocal.ALMACEN:
        return 'secondary.main';
      case TipoLocal.SHOWROOM:
        return 'warning.main';
      case TipoLocal.VIRTUAL:
        return 'info.main';
      default:
        return 'grey.500';
    }
  };

  // ============================================================================
  // RENDER PRINCIPAL
  // ============================================================================

  switch (variant) {
    case 'compact':
      return renderCompactView();
    case 'expanded':
      return renderExpandedView();
    case 'detailed':
      return renderDetailedView();
    default:
      return renderCompactView();
  }
};

export default TenantIndicator;