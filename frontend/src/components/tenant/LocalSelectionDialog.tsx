/**
 * Componente para seleccionar local de trabajo al iniciar sesión
 * Se muestra cuando el usuario tiene múltiples locales asignados
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Card,
  CardContent,
  CardActionArea,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  FormLabel,
  Alert,
  CircularProgress,
  Chip
} from '@mui/material';
import {
  Store as StoreIcon,
  LocationOn as LocationIcon,
  Person as PersonIcon
} from '@mui/icons-material';
import { Local } from '../../types/multiTenant';

interface LocalSelectionDialogProps {
  open: boolean;
  user: {
    id: string;
    nombre: string;
    rol: string;
  };
  availableLocals: Local[];
  onLocalSelected: (localId: string) => void;
  loading?: boolean;
  error?: string | null;
}

const LocalSelectionDialog: React.FC<LocalSelectionDialogProps> = ({
  open,
  user,
  availableLocals,
  onLocalSelected,
  loading = false,
  error = null
}) => {
  const [selectedLocalId, setSelectedLocalId] = useState<string>('');

  useEffect(() => {
    // Auto-seleccionar si solo hay un local
    if (availableLocals.length === 1) {
      setSelectedLocalId(availableLocals[0].id);
    } else {
      setSelectedLocalId('');
    }
  }, [availableLocals]);

  const handleConfirm = () => {
    if (selectedLocalId) {
      onLocalSelected(selectedLocalId);
    }
  };

  const selectedLocal = availableLocals.find(local => local.id === selectedLocalId);

  if (availableLocals.length === 0) {
    return (
      <Dialog
        open={open}
        disableEscapeKeyDown
        PaperProps={{
          sx: { minWidth: 400 }
        }}
      >
        <DialogTitle sx={{ textAlign: 'center' }}>
          <StoreIcon color="error" sx={{ fontSize: 48, mb: 2 }} />
          <Typography variant="h6" component="div">
            Sin Locales Asignados
          </Typography>
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            No tienes locales asignados para trabajar. Contacta al administrador para que te asigne al menos un local.
          </Alert>
          <Typography variant="body2" color="textSecondary">
            Usuario: {user.nombre}
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Rol: {user.rol}
          </Typography>
        </DialogContent>
      </Dialog>
    );
  }

  if (availableLocals.length === 1) {
    return (
      <Dialog
        open={open}
        disableEscapeKeyDown
        PaperProps={{
          sx: { minWidth: 450 }
        }}
      >
        <DialogTitle sx={{ textAlign: 'center' }}>
          <StoreIcon color="primary" sx={{ fontSize: 48, mb: 2 }} />
          <Typography variant="h6" component="div">
            Bienvenido, {user.nombre}
          </Typography>
          <Chip 
            label={user.rol} 
            size="small" 
            color="primary" 
            variant="outlined"
            sx={{ mt: 1 }}
          />
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 3 }}>
            Tienes un local asignado. Serás dirigido automáticamente.
          </Alert>
          
          <Card variant="outlined" sx={{ mb: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <LocationIcon color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography variant="h6">
                    {availableLocals[0].nombre}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Código: {availableLocals[0].codigo}
                  </Typography>
                </Box>
              </Box>
              
              {(availableLocals[0].direccion || availableLocals[0].ciudad) && (
                <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                  📍 {availableLocals[0].direccion || 'Sin dirección'}{availableLocals[0].ciudad ? `, ${availableLocals[0].ciudad}` : ''}
                </Typography>
              )}
            </CardContent>
          </Card>

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </DialogContent>
        
        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button
            onClick={handleConfirm}
            variant="contained"
            color="primary"
            fullWidth
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : <StoreIcon />}
          >
            {loading ? 'Configurando...' : 'Continuar al Sistema'}
          </Button>
        </DialogActions>
      </Dialog>
    );
  }

  return (
    <Dialog
      open={open}
      disableEscapeKeyDown
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: 400 }
      }}
    >
      <DialogTitle sx={{ textAlign: 'center' }}>
        <PersonIcon color="primary" sx={{ fontSize: 48, mb: 2 }} />
        <Typography variant="h6" component="div">
          Bienvenido, {user.nombre}
        </Typography>
        <Chip 
          label={user.rol} 
          size="small" 
          color="primary" 
          variant="outlined"
          sx={{ mt: 1 }}
        />
      </DialogTitle>
      
      <DialogContent>
        <Alert severity="info" sx={{ mb: 3 }}>
          Selecciona el local donde vas a trabajar. Podrás cambiar de local más tarde desde el menú principal.
        </Alert>

        <FormControl component="fieldset" fullWidth>
          <FormLabel component="legend" sx={{ mb: 2, fontWeight: 'bold' }}>
            Locales Disponibles ({availableLocals.length})
          </FormLabel>
          
          <RadioGroup
            value={selectedLocalId}
            onChange={(e) => setSelectedLocalId(e.target.value)}
          >
            <Box sx={{ display: 'grid', gap: 2, mt: 1 }}>
              {availableLocals.map((local) => (
                <Card 
                  key={local.id} 
                  variant="outlined"
                  sx={{
                    border: selectedLocalId === local.id ? 2 : 1,
                    borderColor: selectedLocalId === local.id ? 'primary.main' : 'divider',
                    backgroundColor: selectedLocalId === local.id ? 'action.selected' : 'transparent'
                  }}
                >
                  <CardActionArea onClick={() => setSelectedLocalId(local.id)}>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                          <LocationIcon 
                            color={selectedLocalId === local.id ? "primary" : "action"} 
                            sx={{ mr: 2 }} 
                          />
                          <Box>
                            <Typography variant="h6" component="div">
                              {local.nombre}
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              Código: {local.codigo}
                            </Typography>
                            {(local.direccion || local.ciudad) && (
                              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                                📍 {local.direccion || 'Sin dirección'}{local.ciudad ? `, ${local.ciudad}` : ''}
                              </Typography>
                            )}
                          </Box>
                        </Box>
                        
                        <FormControlLabel
                          value={local.id}
                          control={<Radio />}
                          label=""
                        />
                      </Box>
                    </CardContent>
                  </CardActionArea>
                </Card>
              ))}
            </Box>
          </RadioGroup>
        </FormControl>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </DialogContent>
      
      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button
          onClick={handleConfirm}
          variant="contained"
          color="primary"
          fullWidth
          disabled={!selectedLocalId || loading}
          startIcon={loading ? <CircularProgress size={20} /> : <StoreIcon />}
          size="large"
        >
          {loading ? 'Configurando Local...' : `Trabajar en ${selectedLocal?.nombre || 'Local Seleccionado'}`}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default LocalSelectionDialog;