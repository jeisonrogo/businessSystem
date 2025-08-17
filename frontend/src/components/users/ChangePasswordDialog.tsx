/**
 * Dialog para cambiar contraseña de usuario
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton
} from '@mui/material';
import {
  VpnKey as VpnKeyIcon,
  Visibility,
  VisibilityOff,
  Save as SaveIcon,
  Cancel as CancelIcon
} from '@mui/icons-material';

import { User, usersService } from '../../services/usersService';

interface ChangePasswordDialogProps {
  open: boolean;
  onClose: () => void;
  onPasswordChanged: () => void;
  user: User;
}

const ChangePasswordDialog: React.FC<ChangePasswordDialogProps> = ({
  open,
  onClose,
  onPasswordChanged,
  user
}) => {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errors, setErrors] = useState<{
    newPassword?: string;
    confirmPassword?: string;
  }>({});

  const validateForm = (): boolean => {
    const newErrors: typeof errors = {};

    if (!newPassword) {
      newErrors.newPassword = 'La nueva contraseña es requerida';
    } else if (newPassword.length < 8) {
      newErrors.newPassword = 'La contraseña debe tener al menos 8 caracteres';
    }

    if (!confirmPassword) {
      newErrors.confirmPassword = 'Confirma la nueva contraseña';
    } else if (newPassword !== confirmPassword) {
      newErrors.confirmPassword = 'Las contraseñas no coinciden';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await usersService.changeUserPassword(user.id, {
        new_password: newPassword
      });

      onPasswordChanged();
      handleClose();
    } catch (error: any) {
      console.error('Error al cambiar contraseña:', error);
      setError(error.message || 'Error al cambiar la contraseña');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setNewPassword('');
    setConfirmPassword('');
    setShowNewPassword(false);
    setShowConfirmPassword(false);
    setErrors({});
    setError(null);
    onClose();
  };

  const handleNewPasswordChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setNewPassword(event.target.value);
    if (errors.newPassword) {
      setErrors(prev => ({ ...prev, newPassword: undefined }));
    }
  };

  const handleConfirmPasswordChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setConfirmPassword(event.target.value);
    if (errors.confirmPassword) {
      setErrors(prev => ({ ...prev, confirmPassword: undefined }));
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={2}>
          <VpnKeyIcon color="primary" />
          <Typography variant="h6">
            Cambiar Contraseña
          </Typography>
        </Box>
      </DialogTitle>

      <DialogContent dividers sx={{ p: 3 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Box sx={{ mb: 3 }}>
          <Typography variant="body1" gutterBottom>
            Cambiar contraseña para: <strong>{user.nombre}</strong>
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {user.email}
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <TextField
            fullWidth
            label="Nueva Contraseña *"
            type={showNewPassword ? 'text' : 'password'}
            value={newPassword}
            onChange={handleNewPasswordChange}
            error={!!errors.newPassword}
            helperText={errors.newPassword || 'Mínimo 8 caracteres'}
            disabled={loading}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    edge="end"
                  >
                    {showNewPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <TextField
            fullWidth
            label="Confirmar Nueva Contraseña *"
            type={showConfirmPassword ? 'text' : 'password'}
            value={confirmPassword}
            onChange={handleConfirmPasswordChange}
            error={!!errors.confirmPassword}
            helperText={errors.confirmPassword}
            disabled={loading}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    edge="end"
                  >
                    {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
        </Box>

        <Alert severity="info" sx={{ mt: 3 }}>
          <Typography variant="body2">
            El usuario deberá usar la nueva contraseña en su próximo inicio de sesión.
          </Typography>
        </Alert>
      </DialogContent>

      <DialogActions sx={{ p: 3 }}>
        <Button
          onClick={handleClose}
          disabled={loading}
          startIcon={<CancelIcon />}
        >
          Cancelar
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading || !newPassword || !confirmPassword}
          startIcon={loading ? <CircularProgress size={16} /> : <SaveIcon />}
        >
          {loading ? 'Cambiando...' : 'Cambiar Contraseña'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ChangePasswordDialog;