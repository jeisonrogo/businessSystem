/**
 * Componente para configuración del perfil de usuario
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  CircularProgress,
  Typography,
  Divider
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';

import { User } from '../../services/usersService';
import { authService } from '../../services/authService';
import { useAuth } from '../../context/AuthContext';

interface ProfileSettingsProps {
  user: User;
  onSuccess: (message: string) => void;
  onError: (message: string) => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
}

interface ProfileFormData {
  nombre: string;
  email: string;
}

const ProfileSettings: React.FC<ProfileSettingsProps> = ({
  user,
  onSuccess,
  onError,
  loading,
  setLoading
}) => {
  const { updateUser } = useAuth();
  const [formData, setFormData] = useState<ProfileFormData>({
    nombre: user.nombre,
    email: user.email
  });
  const [hasChanges, setHasChanges] = useState(false);
  const [errors, setErrors] = useState<{
    nombre?: string;
    email?: string;
  }>({});

  // Detectar cambios en el formulario
  useEffect(() => {
    const changed = formData.nombre !== user.nombre || formData.email !== user.email;
    setHasChanges(changed);
  }, [formData, user]);

  const validateForm = (): boolean => {
    const newErrors: typeof errors = {};

    if (!formData.nombre.trim()) {
      newErrors.nombre = 'El nombre es requerido';
    } else if (formData.nombre.length < 2) {
      newErrors.nombre = 'El nombre debe tener al menos 2 caracteres';
    } else if (formData.nombre.length > 100) {
      newErrors.nombre = 'El nombre no puede tener más de 100 caracteres';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'El email es requerido';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'El email no tiene un formato válido';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: keyof ProfileFormData) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = event.target.value;
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Limpiar error cuando el usuario empiece a escribir
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    if (!hasChanges) {
      onError('No hay cambios para guardar');
      return;
    }

    setLoading(true);

    try {
      // Actualizar el perfil usando el servicio de auth
      const response = await authService.updateProfile({
        nombre: formData.nombre,
        email: formData.email
      });

      // Actualizar el contexto de usuario
      updateUser(response);

      onSuccess('Perfil actualizado exitosamente');
      setHasChanges(false);
    } catch (error: any) {
      console.error('Error al actualizar perfil:', error);
      onError(error.message || 'Error al actualizar el perfil');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFormData({
      nombre: user.nombre,
      email: user.email
    });
    setErrors({});
    setHasChanges(false);
  };

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Actualiza tu información personal visible en el sistema.
      </Typography>

      <Divider sx={{ mb: 3 }} />

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        <TextField
          fullWidth
          label="Nombre Completo"
          value={formData.nombre}
          onChange={handleInputChange('nombre')}
          error={!!errors.nombre}
          helperText={errors.nombre}
          disabled={loading}
          placeholder="Ej: Juan Pérez"
        />

        <TextField
          fullWidth
          label="Email"
          type="email"
          value={formData.email}
          onChange={handleInputChange('email')}
          error={!!errors.email}
          helperText={errors.email || 'Tu email de acceso al sistema'}
          disabled={loading}
          placeholder="usuario@empresa.com"
        />

        <Typography variant="caption" color="text.secondary">
          <strong>Nota:</strong> Si cambias tu email, deberás usar el nuevo email para iniciar sesión.
        </Typography>

        <Divider />

        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
          <Button
            onClick={handleReset}
            disabled={loading || !hasChanges}
            startIcon={<RefreshIcon />}
            variant="outlined"
          >
            Deshacer
          </Button>
          
          <Button
            onClick={handleSubmit}
            disabled={loading || !hasChanges}
            startIcon={loading ? <CircularProgress size={16} /> : <SaveIcon />}
            variant="contained"
          >
            {loading ? 'Guardando...' : 'Guardar Cambios'}
          </Button>
        </Box>
      </Box>
    </Box>
  );
};

export default ProfileSettings;