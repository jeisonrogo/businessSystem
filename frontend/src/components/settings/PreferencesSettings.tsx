/**
 * Componente para configuración de preferencias del usuario
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  FormControl,
  FormControlLabel,
  Switch,
  Select,
  MenuItem,
  InputLabel,
  Typography,
  Divider,
  Button,
  Chip
} from '@mui/material';
import {
  Save as SaveIcon,
  Palette as PaletteIcon,
  Language as LanguageIcon,
  Notifications as NotificationsIcon
} from '@mui/icons-material';

interface PreferencesSettingsProps {
  onSuccess: (message: string) => void;
  onError: (message: string) => void;
}

interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: 'es' | 'en';
  notifications: {
    email: boolean;
    desktop: boolean;
    marketing: boolean;
  };
  dashboard: {
    autoRefresh: boolean;
    refreshInterval: number;
  };
}

const PreferencesSettings: React.FC<PreferencesSettingsProps> = ({
  onSuccess,
  onError
}) => {
  const [preferences, setPreferences] = useState<UserPreferences>({
    theme: 'light',
    language: 'es',
    notifications: {
      email: true,
      desktop: false,
      marketing: false
    },
    dashboard: {
      autoRefresh: true,
      refreshInterval: 30
    }
  });

  const [hasChanges, setHasChanges] = useState(false);

  // Cargar preferencias del localStorage al inicializar
  useEffect(() => {
    const savedPreferences = localStorage.getItem('userPreferences');
    if (savedPreferences) {
      try {
        const parsed = JSON.parse(savedPreferences);
        setPreferences(parsed);
      } catch (error) {
        console.error('Error al cargar preferencias guardadas:', error);
      }
    }
  }, []);

  // Detectar cambios
  useEffect(() => {
    const savedPreferences = localStorage.getItem('userPreferences');
    const currentPreferencesStr = JSON.stringify(preferences);
    const hasChanged = !savedPreferences || savedPreferences !== currentPreferencesStr;
    setHasChanges(hasChanged);
  }, [preferences]);

  const handleThemeChange = (event: any) => {
    setPreferences(prev => ({
      ...prev,
      theme: event.target.value
    }));
  };

  const handleLanguageChange = (event: any) => {
    setPreferences(prev => ({
      ...prev,
      language: event.target.value
    }));
  };

  const handleNotificationChange = (key: keyof UserPreferences['notifications']) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setPreferences(prev => ({
      ...prev,
      notifications: {
        ...prev.notifications,
        [key]: event.target.checked
      }
    }));
  };

  const handleDashboardChange = (key: keyof UserPreferences['dashboard']) => (event: any) => {
    setPreferences(prev => ({
      ...prev,
      dashboard: {
        ...prev.dashboard,
        [key]: key === 'autoRefresh' ? event.target.checked : event.target.value
      }
    }));
  };

  const handleSave = () => {
    try {
      localStorage.setItem('userPreferences', JSON.stringify(preferences));
      setHasChanges(false);
      onSuccess('Preferencias guardadas exitosamente');
      
      // Aplicar tema si es necesario (en una implementación real)
      // applyTheme(preferences.theme);
    } catch (error) {
      console.error('Error al guardar preferencias:', error);
      onError('Error al guardar las preferencias');
    }
  };

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Personaliza tu experiencia en el sistema.
      </Typography>

      <Divider sx={{ mb: 3 }} />

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* Tema */}
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <PaletteIcon color="primary" fontSize="small" />
            <Typography variant="h6">Apariencia</Typography>
          </Box>
          
          <FormControl fullWidth size="small">
            <InputLabel>Tema</InputLabel>
            <Select
              value={preferences.theme}
              label="Tema"
              onChange={handleThemeChange}
            >
              <MenuItem value="light">Claro</MenuItem>
              <MenuItem value="dark">Oscuro</MenuItem>
              <MenuItem value="auto">Automático</MenuItem>
            </Select>
          </FormControl>
          
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            El tema automático se ajusta según las preferencias del sistema.
          </Typography>
        </Box>

        {/* Idioma */}
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <LanguageIcon color="primary" fontSize="small" />
            <Typography variant="h6">Idioma</Typography>
            <Chip label="Próximamente" size="small" variant="outlined" color="info" />
          </Box>
          
          <FormControl fullWidth size="small">
            <InputLabel>Idioma de la interfaz</InputLabel>
            <Select
              value={preferences.language}
              label="Idioma de la interfaz"
              onChange={handleLanguageChange}
              disabled
            >
              <MenuItem value="es">Español</MenuItem>
              <MenuItem value="en">English</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {/* Notificaciones */}
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <NotificationsIcon color="primary" fontSize="small" />
            <Typography variant="h6">Notificaciones</Typography>
          </Box>
          
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={preferences.notifications.email}
                  onChange={handleNotificationChange('email')}
                />
              }
              label="Notificaciones por email"
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={preferences.notifications.desktop}
                  onChange={handleNotificationChange('desktop')}
                  disabled
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  Notificaciones de escritorio
                  <Chip label="Próximamente" size="small" variant="outlined" color="info" />
                </Box>
              }
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={preferences.notifications.marketing}
                  onChange={handleNotificationChange('marketing')}
                />
              }
              label="Emails promocionales"
            />
          </Box>
        </Box>

        {/* Dashboard */}
        <Box>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Dashboard
          </Typography>
          
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={preferences.dashboard.autoRefresh}
                  onChange={handleDashboardChange('autoRefresh')}
                />
              }
              label="Actualización automática"
            />
            
            {preferences.dashboard.autoRefresh && (
              <FormControl size="small" sx={{ width: 200 }}>
                <InputLabel>Intervalo (segundos)</InputLabel>
                <Select
                  value={preferences.dashboard.refreshInterval}
                  label="Intervalo (segundos)"
                  onChange={handleDashboardChange('refreshInterval')}
                >
                  <MenuItem value={15}>15 segundos</MenuItem>
                  <MenuItem value={30}>30 segundos</MenuItem>
                  <MenuItem value={60}>1 minuto</MenuItem>
                  <MenuItem value={300}>5 minutos</MenuItem>
                </Select>
              </FormControl>
            )}
          </Box>
        </Box>

        <Divider />

        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            onClick={handleSave}
            disabled={!hasChanges}
            startIcon={<SaveIcon />}
            variant="contained"
          >
            Guardar Preferencias
          </Button>
        </Box>
      </Box>
    </Box>
  );
};

export default PreferencesSettings;