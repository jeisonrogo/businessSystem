/**
 * Componente para cambio de contraseña del usuario
 */

import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  CircularProgress,
  Typography,
  Divider,
  InputAdornment,
  IconButton,
  Alert
} from '@mui/material';
import {
  VpnKey as VpnKeyIcon,
  Visibility,
  VisibilityOff,
  Save as SaveIcon
} from '@mui/icons-material';

import { authService } from '../../services/authService';

interface PasswordSettingsProps {
  userId: string;
  onSuccess: (message: string) => void;
  onError: (message: string) => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
}

interface PasswordFormData {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

const PasswordSettings: React.FC<PasswordSettingsProps> = ({
  userId,
  onSuccess,
  onError,
  loading,
  setLoading
}) => {
  const [formData, setFormData] = useState<PasswordFormData>({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false
  });

  const [errors, setErrors] = useState<{
    currentPassword?: string;
    newPassword?: string;
    confirmPassword?: string;
  }>({});

  const validateForm = (): boolean => {
    const newErrors: typeof errors = {};

    if (!formData.currentPassword) {
      newErrors.currentPassword = 'La contraseña actual es requerida';
    }

    if (!formData.newPassword) {
      newErrors.newPassword = 'La nueva contraseña es requerida';
    } else if (formData.newPassword.length < 8) {
      newErrors.newPassword = 'La nueva contraseña debe tener al menos 8 caracteres';
    } else if (formData.newPassword === formData.currentPassword) {
      newErrors.newPassword = 'La nueva contraseña debe ser diferente a la actual';
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Confirma la nueva contraseña';
    } else if (formData.newPassword !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Las contraseñas no coinciden';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: keyof PasswordFormData) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = event.target.value;
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Limpiar error cuando el usuario empiece a escribir
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  const togglePasswordVisibility = (field: keyof typeof showPasswords) => {
    setShowPasswords(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      await authService.changePassword({
        current_password: formData.currentPassword,
        new_password: formData.newPassword
      });

      // Limpiar formulario
      setFormData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      });
      setErrors({});

      onSuccess('Contraseña actualizada exitosamente');
    } catch (error: any) {
      console.error('Error al cambiar contraseña:', error);
      onError(error.message || 'Error al cambiar la contraseña');
    } finally {
      setLoading(false);
    }
  };

  const getPasswordStrength = (password: string): { strength: number; text: string; color: string } => {
    if (password.length === 0) return { strength: 0, text: '', color: '' };
    
    let score = 0;
    
    // Longitud
    if (password.length >= 8) score += 1;
    if (password.length >= 12) score += 1;
    
    // Complejidad
    if (/[a-z]/.test(password)) score += 1;
    if (/[A-Z]/.test(password)) score += 1;
    if (/[0-9]/.test(password)) score += 1;
    if (/[^A-Za-z0-9]/.test(password)) score += 1;
    
    if (score <= 2) return { strength: score, text: 'Débil', color: 'error.main' };
    if (score <= 4) return { strength: score, text: 'Media', color: 'warning.main' };
    return { strength: score, text: 'Fuerte', color: 'success.main' };
  };

  const passwordStrength = getPasswordStrength(formData.newPassword);

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Cambia tu contraseña de acceso al sistema.
      </Typography>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>Recomendaciones:</strong> Usa al menos 8 caracteres, incluye mayúsculas, minúsculas, números y símbolos.
        </Typography>
      </Alert>

      <Divider sx={{ mb: 3 }} />

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        <TextField
          fullWidth
          label="Contraseña Actual"
          type={showPasswords.current ? 'text' : 'password'}
          value={formData.currentPassword}
          onChange={handleInputChange('currentPassword')}
          error={!!errors.currentPassword}
          helperText={errors.currentPassword}
          disabled={loading}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={() => togglePasswordVisibility('current')}
                  edge="end"
                >
                  {showPasswords.current ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />

        <TextField
          fullWidth
          label="Nueva Contraseña"
          type={showPasswords.new ? 'text' : 'password'}
          value={formData.newPassword}
          onChange={handleInputChange('newPassword')}
          error={!!errors.newPassword}
          helperText={errors.newPassword}
          disabled={loading}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={() => togglePasswordVisibility('new')}
                  edge="end"
                >
                  {showPasswords.new ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />

        {/* Indicador de fortaleza de contraseña */}
        {formData.newPassword && (
          <Box sx={{ ml: 1 }}>
            <Typography variant="caption" sx={{ color: passwordStrength.color }}>
              Fortaleza: {passwordStrength.text}
            </Typography>
            <Box
              sx={{
                width: '100%',
                height: 4,
                backgroundColor: 'grey.300',
                borderRadius: 2,
                mt: 0.5,
                overflow: 'hidden'
              }}
            >
              <Box
                sx={{
                  width: `${(passwordStrength.strength / 6) * 100}%`,
                  height: '100%',
                  backgroundColor: passwordStrength.color,
                  transition: 'width 0.3s ease'
                }}
              />
            </Box>
          </Box>
        )}

        <TextField
          fullWidth
          label="Confirmar Nueva Contraseña"
          type={showPasswords.confirm ? 'text' : 'password'}
          value={formData.confirmPassword}
          onChange={handleInputChange('confirmPassword')}
          error={!!errors.confirmPassword}
          helperText={errors.confirmPassword}
          disabled={loading}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={() => togglePasswordVisibility('confirm')}
                  edge="end"
                >
                  {showPasswords.confirm ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />

        <Divider />

        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            onClick={handleSubmit}
            disabled={loading || !formData.currentPassword || !formData.newPassword || !formData.confirmPassword}
            startIcon={loading ? <CircularProgress size={16} /> : <VpnKeyIcon />}
            variant="contained"
          >
            {loading ? 'Cambiando...' : 'Cambiar Contraseña'}
          </Button>
        </Box>
      </Box>
    </Box>
  );
};

export default PasswordSettings;