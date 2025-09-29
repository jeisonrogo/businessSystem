/**
 * Componente Selector de Tienda/Local (Tenant Switcher)
 * 
 * Permite al usuario cambiar entre diferentes tiendas y locales
 * según sus permisos. Muestra el contexto actual y opciones disponibles.
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  Avatar,
  List,
  ListItemAvatar,
  ListItemText,
  ListItemButton,
  Chip,
  Alert,
  CircularProgress,
  Grid,
  IconButton,
  Badge
} from '@mui/material';
import {
  Store as StoreIcon,
  LocationOn as LocationIcon,
  Business as BusinessIcon,
  Close as CloseIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon,
  Group as GroupIcon,
  Inventory as InventoryIcon,
  SwapHoriz as SwapIcon
} from '@mui/icons-material';

import { useTenant } from '../../context/TenantContext';
import { Tienda, Local, TipoLocal } from '../../types/multiTenant';
import { formatCurrency } from '../../utils/formatters';

// ============================================================================
// INTERFACES
// ============================================================================

interface TenantSwitcherProps {
  open: boolean;
  onClose: () => void;
}

// ============================================================================
// COMPONENTE PRINCIPAL
// ============================================================================

export const TenantSwitcher: React.FC<TenantSwitcherProps> = ({ open, onClose }) => {
  const {
    currentContext,
    availableStores,
    availableLocals,
    selectedStore,
    isLoading,
    error,
    switchContext,
    loadStoreLocals
  } = useTenant();

  const [localLoading, setLocalLoading] = useState<string | null>(null);
  const [switchLoading, setSwitchLoading] = useState(false);

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const handleStoreSelect = async (store: Tienda) => {
    if (store.id === selectedStore?.id) return;
    
    setLocalLoading(store.id);
    try {
      await loadStoreLocals(store.id);
    } catch (err) {
      console.error('Error loading store locals:', err);
    } finally {
      setLocalLoading(null);
    }
  };

  const handleContextSwitch = async (localId?: string) => {
    setSwitchLoading(true);
    try {
      await switchContext({ local_id: localId });
      onClose();
    } catch (err) {
      console.error('Error switching context:', err);
    } finally {
      setSwitchLoading(false);
    }
  };

  const handleStoreOnlySwitch = () => {
    handleContextSwitch(undefined);
  };

  // ============================================================================
  // RENDER HELPERS
  // ============================================================================

  const renderStoreCard = (store: Tienda) => {
    const isSelected = store.id === selectedStore?.id;
    const isCurrentStore = store.id === currentContext?.tienda_id;
    const isLoadingLocals = localLoading === store.id;

    return (
      <Card
        key={store.id}
        variant={isSelected ? "elevation" : "outlined"}
        sx={{
          mb: 2,
          border: isCurrentStore ? '2px solid #1976d2' : undefined,
          cursor: 'pointer',
          transition: 'all 0.2s ease-in-out',
          '&:hover': { transform: 'translateY(-2px)', boxShadow: 3 }
        }}
        onClick={() => handleStoreSelect(store)}
      >
        <CardHeader
          avatar={
            <Badge
              badgeContent={isCurrentStore ? <CheckCircleIcon fontSize="small" /> : 0}
              color="primary"
              invisible={!isCurrentStore}
            >
              <Avatar sx={{ bgcolor: 'primary.main' }}>
                <BusinessIcon />
              </Avatar>
            </Badge>
          }
          title={
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="h6">{store.nombre}</Typography>
              {isCurrentStore && <Chip label="Actual" color="primary" size="small" />}
            </Box>
          }
          subheader={`Código: ${store.codigo}`}
          action={
            isLoadingLocals && (
              <CircularProgress size={24} />
            )
          }
        />
        
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Box display="flex" alignItems="center" gap={1}>
                <LocationIcon fontSize="small" color="action" />
                <Typography variant="body2">
                  {store.total_locales || 0} locales
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box display="flex" alignItems="center" gap={1}>
                <GroupIcon fontSize="small" color="action" />
                <Typography variant="body2">
                  {store.direccion && `${store.direccion.substring(0, 30)}...`}
                </Typography>
              </Box>
            </Grid>
          </Grid>
          
          {store.descripcion && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {store.descripcion}
            </Typography>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderLocalList = () => {
    if (!selectedStore) {
      return (
        <Alert severity="info" sx={{ mt: 2 }}>
          Selecciona una tienda para ver sus locales disponibles
        </Alert>
      );
    }

    if (localLoading) {
      return (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress />
        </Box>
      );
    }

    if ((availableLocals || []).length === 0) {
      return (
        <Alert severity="warning" sx={{ mt: 2 }}>
          No tienes acceso a ningún local en esta tienda
        </Alert>
      );
    }

    return (
      <Box sx={{ mt: 2 }}>
        <Typography variant="h6" gutterBottom>
          Locales disponibles en {selectedStore.nombre}
        </Typography>
        
        {/* Opción para contexto solo tienda */}
        <Card variant="outlined" sx={{ mb: 2 }}>
          <ListItemButton
            onClick={handleStoreOnlySwitch}
            selected={currentContext?.tienda_id === selectedStore.id && !currentContext?.tiene_contexto_local}
            disabled={switchLoading}
          >
            <ListItemAvatar>
              <Avatar sx={{ bgcolor: 'secondary.main' }}>
                <BusinessIcon />
              </Avatar>
            </ListItemAvatar>
            <ListItemText
              primary="Toda la tienda"
              secondary="Acceso general a la tienda sin restricción de local"
            />
            {currentContext?.tienda_id === selectedStore.id && !currentContext?.tiene_contexto_local && (
              <CheckCircleIcon color="primary" />
            )}
          </ListItemButton>
        </Card>

        {/* Lista de locales */}
        <List>
          {(availableLocals || []).map((local) => renderLocalItem(local))}
        </List>
      </Box>
    );
  };

  const renderLocalItem = (local: Local) => {
    const isCurrentLocal = local.id === currentContext?.local_id;
    const typeIcon = getLocalTypeIcon(local.tipo_local);
    
    return (
      <Card key={local.id} variant="outlined" sx={{ mb: 1 }}>
        <ListItemButton
          onClick={() => handleContextSwitch(local.id)}
          selected={isCurrentLocal}
          disabled={switchLoading}
        >
          <ListItemAvatar>
            <Badge
              badgeContent={isCurrentLocal ? <CheckCircleIcon fontSize="small" /> : 0}
              color="primary"
              invisible={!isCurrentLocal}
            >
              <Avatar sx={{ bgcolor: getLocalTypeColor(local.tipo_local) }}>
                {typeIcon}
              </Avatar>
            </Badge>
          </ListItemAvatar>
          
          <ListItemText
            primary={
              <Box display="flex" alignItems="center" gap={1}>
                <Typography variant="subtitle1">{local.nombre}</Typography>
                <Chip 
                  label={local.tipo_local || 'Local'} 
                  size="small" 
                  variant="outlined"
                  color={getLocalTypeChipColor(local.tipo_local)}
                />
              </Box>
            }
            secondary={`Código: ${local.codigo}${local.direccion || local.ciudad ? ` • 📍 ${local.direccion || 'Sin dirección'}, ${local.ciudad || 'Sin ciudad'}` : ''} • 💼 ${local.total_productos || 0} productos${local.valor_inventario ? ` • 💰 ${formatCurrency(local.valor_inventario)}` : ''}`}
          />
          
          {isCurrentLocal && (
            <CheckCircleIcon color="primary" />
          )}
        </ListItemButton>
      </Card>
    );
  };

  // ============================================================================
  // UTILIDADES
  // ============================================================================

  const getLocalTypeIcon = (tipo?: TipoLocal) => {
    switch (tipo) {
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

  const getLocalTypeColor = (tipo?: TipoLocal) => {
    switch (tipo) {
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

  const getLocalTypeChipColor = (tipo?: TipoLocal): 'primary' | 'secondary' | 'warning' | 'info' | 'default' => {
    switch (tipo) {
      case TipoLocal.SUCURSAL:
        return 'primary';
      case TipoLocal.ALMACEN:
        return 'secondary';
      case TipoLocal.SHOWROOM:
        return 'warning';
      case TipoLocal.VIRTUAL:
        return 'info';
      default:
        return 'default';
    }
  };

  // ============================================================================
  // RENDER PRINCIPAL
  // ============================================================================

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: '80vh' }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="between">
          <Box display="flex" alignItems="center" gap={2}>
            <SwapIcon color="primary" />
            <Typography variant="h5">Cambiar contexto</Typography>
          </Box>
          <IconButton onClick={onClose} edge="end">
            <CloseIcon />
          </IconButton>
        </Box>
        
        {currentContext && (
          <Box sx={{ mt: 2 }}>
            <Alert 
              severity="info" 
              icon={<InfoIcon />}
              sx={{ '& .MuiAlert-message': { width: '100%' } }}
            >
              <Box>
                <Typography variant="body2">
                  <strong>Contexto actual:</strong> {currentContext?.tienda_nombre || 'Cargando...'}
                  {currentContext?.tiene_contexto_local && currentContext?.local_nombre && ` → ${currentContext.local_nombre}`}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {currentContext.permisos_disponibles?.length || 0} permisos disponibles
                </Typography>
              </Box>
            </Alert>
          </Box>
        )}
      </DialogTitle>

      <DialogContent dividers>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3}>
          {/* Panel de tiendas */}
          <Grid item xs={12} md={6}>
            <Typography variant="h6" gutterBottom>
              Tiendas disponibles
            </Typography>
            
            {isLoading ? (
              <Box display="flex" justifyContent="center" py={4}>
                <CircularProgress />
              </Box>
            ) : (availableStores || []).length === 0 ? (
              <Alert severity="warning">
                No tienes acceso a ninguna tienda
              </Alert>
            ) : (
              (availableStores || []).map(renderStoreCard)
            )}
          </Grid>

          {/* Panel de locales */}
          <Grid item xs={12} md={6}>
            {renderLocalList()}
          </Grid>
        </Grid>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={switchLoading}>
          Cerrar
        </Button>
        {switchLoading && (
          <Box display="flex" alignItems="center" gap={2}>
            <CircularProgress size={20} />
            <Typography variant="body2">Cambiando contexto...</Typography>
          </Box>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default TenantSwitcher;