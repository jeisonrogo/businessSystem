/**
 * Página de configuración de usuario
 * Permite al usuario gestionar su perfil, contraseña y preferencias
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Alert,
  Divider,
  Chip,
  Avatar
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Person as PersonIcon,
  VpnKey as VpnKeyIcon,
  Palette as PaletteIcon,
  Info as InfoIcon
} from '@mui/icons-material';

import { useAuth } from '../context/AuthContext';
import { usersService } from '../services/usersService';
import ProfileSettings from '../components/settings/ProfileSettings';
import PasswordSettings from '../components/settings/PasswordSettings';
import PreferencesSettings from '../components/settings/PreferencesSettings';
import AccountInfo from '../components/settings/AccountInfo';

const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const clearMessages = () => {
    setError(null);
    setSuccess(null);
  };

  const handleSuccess = (message: string) => {
    setSuccess(message);
    setError(null);
    setTimeout(() => setSuccess(null), 5000);
  };

  const handleError = (message: string) => {
    setError(message);
    setSuccess(null);
  };

  if (!user) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          No se pudo cargar la información del usuario.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <SettingsIcon fontSize="large" color="primary" />
          Configuración
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Gestiona tu perfil, contraseña y preferencias del sistema
        </Typography>
      </Box>

      {/* Mensajes de estado */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={clearMessages}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={clearMessages}>
          {success}
        </Alert>
      )}

      {/* Resumen del Usuario */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
          <Avatar
            sx={{
              width: 80,
              height: 80,
              bgcolor: usersService.getRoleColor(user.rol) + '.main',
              fontSize: '2rem',
              fontWeight: 'bold'
            }}
          >
            {user.nombre.split(' ').map(word => word.charAt(0)).join('').slice(0, 2)}
          </Avatar>
          
          <Box sx={{ flex: 1 }}>
            <Typography variant="h5" gutterBottom>
              {user.nombre}
            </Typography>
            <Typography variant="body1" color="text.secondary" gutterBottom>
              {user.email}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <Chip
                label={usersService.getRoleLabel(user.rol)}
                color={usersService.getRoleColor(user.rol)}
                size="small"
              />
              <Chip
                label={user.is_active ? 'Activo' : 'Inactivo'}
                color={user.is_active ? 'success' : 'error'}
                size="small"
                variant="outlined"
              />
            </Box>
          </Box>
        </Box>
      </Paper>

      {/* Configuraciones */}
      <Grid container spacing={3}>
        {/* Perfil */}
        <Grid item xs={12} lg={6}>
          <Card sx={{ height: '100%' }}>
            <CardHeader
              avatar={<PersonIcon color="primary" />}
              title="Información del Perfil"
              subheader="Actualiza tu información personal"
            />
            <CardContent>
              <ProfileSettings
                user={user}
                onSuccess={handleSuccess}
                onError={handleError}
                loading={loading}
                setLoading={setLoading}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Contraseña */}
        <Grid item xs={12} lg={6}>
          <Card sx={{ height: '100%' }}>
            <CardHeader
              avatar={<VpnKeyIcon color="primary" />}
              title="Cambiar Contraseña"
              subheader="Actualiza tu contraseña de acceso"
            />
            <CardContent>
              <PasswordSettings
                userId={user.id}
                onSuccess={handleSuccess}
                onError={handleError}
                loading={loading}
                setLoading={setLoading}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Preferencias */}
        <Grid item xs={12} lg={6}>
          <Card sx={{ height: '100%' }}>
            <CardHeader
              avatar={<PaletteIcon color="primary" />}
              title="Preferencias"
              subheader="Personaliza tu experiencia"
            />
            <CardContent>
              <PreferencesSettings
                onSuccess={handleSuccess}
                onError={handleError}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Información de la Cuenta */}
        <Grid item xs={12} lg={6}>
          <Card sx={{ height: '100%' }}>
            <CardHeader
              avatar={<InfoIcon color="primary" />}
              title="Información de la Cuenta"
              subheader="Detalles y estadísticas de tu cuenta"
            />
            <CardContent>
              <AccountInfo user={user} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SettingsPage;