/**
 * Formulario para crear y editar usuarios
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Box,
  Typography,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton
} from '@mui/material';
import {
  Save as SaveIcon,
  Cancel as CancelIcon,
  PersonAdd as PersonAddIcon,
  Edit as EditIcon,
  Visibility,
  VisibilityOff
} from '@mui/icons-material';

import { User, usersService, USER_ROLES, CreateUserRequest, UpdateUserRequest } from '../../services/usersService';

interface UserFormProps {
  open: boolean;
  onClose: () => void;
  onSave: () => void;
  user?: User | null;
}

interface FormData {
  email: string;
  nombre: string;
  rol: string;
  password: string;
  confirmPassword: string;
  is_active: boolean;
}

interface FormErrors {
  email?: string;
  nombre?: string;
  rol?: string;
  password?: string;
  confirmPassword?: string;
  general?: string;
}

const UserForm: React.FC<UserFormProps> = ({
  open,
  onClose,
  onSave,
  user
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [formData, setFormData] = useState<FormData>({
    email: '',
    nombre: '',
    rol: USER_ROLES.VENDEDOR,
    password: '',
    confirmPassword: '',
    is_active: true
  });

  const [errors, setErrors] = useState<FormErrors>({});

  const isEditing = !!user;

  // Cargar datos del usuario al abrir el modal en modo edición
  useEffect(() => {
    if (open) {
      if (user) {
        setFormData({
          email: user.email,
          nombre: user.nombre,
          rol: user.rol,
          password: '',
          confirmPassword: '',
          is_active: user.is_active
        });
      } else {
        setFormData({
          email: '',
          nombre: '',
          rol: USER_ROLES.VENDEDOR,
          password: '',
          confirmPassword: '',
          is_active: true
        });
      }
      setErrors({});
      setError(null);
    }
  }, [open, user]);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Validar email
    if (!formData.email.trim()) {
      newErrors.email = 'El email es requerido';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'El email no tiene un formato válido';
    }

    // Validar nombre
    if (!formData.nombre.trim()) {
      newErrors.nombre = 'El nombre es requerido';
    } else if (formData.nombre.length < 2) {
      newErrors.nombre = 'El nombre debe tener al menos 2 caracteres';
    } else if (formData.nombre.length > 100) {
      newErrors.nombre = 'El nombre no puede tener más de 100 caracteres';
    }

    // Validar rol
    if (!formData.rol) {
      newErrors.rol = 'El rol es requerido';
    }

    // Validar contraseña (solo para usuarios nuevos o si se especifica)
    if (!isEditing || formData.password) {
      if (!formData.password) {
        newErrors.password = 'La contraseña es requerida';
      } else if (formData.password.length < 8) {
        newErrors.password = 'La contraseña debe tener al menos 8 caracteres';
      }

      if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = 'Las contraseñas no coinciden';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: keyof FormData) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | { target: { value: unknown } }
  ) => {
    const value = event.target.value;
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Limpiar error cuando el usuario empiece a escribir
    if (errors[field as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  const handleSwitchChange = (field: keyof FormData) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = event.target.checked;
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (isEditing && user) {
        // Actualizar usuario existente
        const updateData: UpdateUserRequest = {
          email: formData.email,
          nombre: formData.nombre,
          rol: formData.rol,
          is_active: formData.is_active
        };

        // Solo incluir contraseña si se especificó
        if (formData.password) {
          await usersService.changeUserPassword(user.id, {
            new_password: formData.password
          });
        }

        await usersService.updateUser(user.id, updateData);
      } else {
        // Crear nuevo usuario
        const createData: CreateUserRequest = {
          email: formData.email,
          nombre: formData.nombre,
          rol: formData.rol,
          password: formData.password
        };

        await usersService.createUser(createData);
      }

      onSave();
    } catch (error: any) {
      console.error('Error al guardar usuario:', error);
      setError(error.message || 'Error al guardar el usuario');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: '60vh' }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={2}>
          {isEditing ? <EditIcon color="primary" /> : <PersonAddIcon color="primary" />}
          <Typography variant="h6">
            {isEditing ? 'Editar Usuario' : 'Crear Nuevo Usuario'}
          </Typography>
        </Box>
      </DialogTitle>

      <DialogContent dividers sx={{ p: 3 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3}>
          {/* Información Personal */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom color="primary">
              Información Personal
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Nombre Completo *"
              value={formData.nombre}
              onChange={handleInputChange('nombre')}
              error={!!errors.nombre}
              helperText={errors.nombre}
              disabled={loading}
              placeholder="Ej: Juan Pérez"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Email *"
              type="email"
              value={formData.email}
              onChange={handleInputChange('email')}
              error={!!errors.email}
              helperText={errors.email}
              disabled={loading}
              placeholder="usuario@empresa.com"
            />
          </Grid>

          {/* Configuración de Acceso */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom color="primary" sx={{ mt: 2 }}>
              Configuración de Acceso
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth error={!!errors.rol}>
              <InputLabel>Rol del Usuario *</InputLabel>
              <Select
                value={formData.rol}
                label="Rol del Usuario *"
                onChange={handleInputChange('rol')}
                disabled={loading}
              >
                {Object.entries(USER_ROLES).map(([key, value]) => (
                  <MenuItem key={value} value={value}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {usersService.getRoleLabel(value)}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
              {errors.rol && (
                <Typography variant="caption" color="error" sx={{ ml: 2, mt: 0.5 }}>
                  {errors.rol}
                </Typography>
              )}
            </FormControl>
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_active}
                  onChange={handleSwitchChange('is_active')}
                  disabled={loading}
                />
              }
              label="Usuario Activo"
            />
            <Typography variant="caption" color="text.secondary" display="block">
              Los usuarios inactivos no pueden acceder al sistema
            </Typography>
          </Grid>

          {/* Contraseña */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom color="primary" sx={{ mt: 2 }}>
              {isEditing ? 'Cambiar Contraseña (Opcional)' : 'Contraseña de Acceso'}
            </Typography>
            {isEditing && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Deja en blanco si no quieres cambiar la contraseña actual
              </Typography>
            )}
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label={isEditing ? 'Nueva Contraseña' : 'Contraseña *'}
              type={showPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={handleInputChange('password')}
              error={!!errors.password}
              helperText={errors.password}
              disabled={loading}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label={isEditing ? 'Confirmar Nueva Contraseña' : 'Confirmar Contraseña *'}
              type={showConfirmPassword ? 'text' : 'password'}
              value={formData.confirmPassword}
              onChange={handleInputChange('confirmPassword')}
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
          </Grid>
        </Grid>
      </DialogContent>

      <DialogActions sx={{ p: 3 }}>
        <Button
          onClick={onClose}
          disabled={loading}
          startIcon={<CancelIcon />}
        >
          Cancelar
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading}
          startIcon={loading ? <CircularProgress size={16} /> : <SaveIcon />}
        >
          {loading ? 'Guardando...' : (isEditing ? 'Actualizar' : 'Crear Usuario')}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default UserForm;