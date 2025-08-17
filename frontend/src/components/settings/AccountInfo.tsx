/**
 * Componente para mostrar información de la cuenta del usuario
 */

import React from 'react';
import {
  Box,
  Typography,
  Divider,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper
} from '@mui/material';
import {
  Person as PersonIcon,
  Email as EmailIcon,
  Badge as BadgeIcon,
  CalendarToday as CalendarIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';

import { User, usersService } from '../../services/usersService';

interface AccountInfoProps {
  user: User;
}

const AccountInfo: React.FC<AccountInfoProps> = ({ user }) => {
  const formatDate = (dateString: string): string => {
    return usersService.formatCreatedDate(dateString);
  };

  const getDaysActive = (createdAt: string): number => {
    const created = new Date(createdAt);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - created.getTime());
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  };

  const getAccountAge = (createdAt: string): string => {
    const days = getDaysActive(createdAt);
    
    if (days < 30) {
      return `${days} días`;
    } else if (days < 365) {
      const months = Math.floor(days / 30);
      return `${months} ${months === 1 ? 'mes' : 'meses'}`;
    } else {
      const years = Math.floor(days / 365);
      const remainingMonths = Math.floor((days % 365) / 30);
      return `${years} ${years === 1 ? 'año' : 'años'}${remainingMonths > 0 ? ` y ${remainingMonths} ${remainingMonths === 1 ? 'mes' : 'meses'}` : ''}`;
    }
  };

  const getRolePermissions = (role: string): string[] => {
    switch (role) {
      case 'administrador':
        return [
          'Gestión completa del sistema',
          'Administración de usuarios',
          'Configuración del sistema',
          'Acceso a todos los módulos',
          'Reportes avanzados'
        ];
      case 'gerente_ventas':
        return [
          'Gestión de ventas',
          'Administración de clientes',
          'Facturación',
          'Reportes de ventas',
          'Supervisión de vendedores'
        ];
      case 'contador':
        return [
          'Módulo de contabilidad',
          'Asientos contables',
          'Reportes financieros',
          'Plan de cuentas',
          'Facturación'
        ];
      case 'vendedor':
        return [
          'Gestión de productos',
          'Creación de facturas',
          'Gestión de clientes',
          'Consulta de inventario'
        ];
      default:
        return ['Permisos básicos'];
    }
  };

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Información detallada sobre tu cuenta y permisos.
      </Typography>

      <Divider sx={{ mb: 3 }} />

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* Información básica */}
        <List dense>
          <ListItem>
            <ListItemIcon>
              <PersonIcon color="primary" />
            </ListItemIcon>
            <ListItemText
              primary="ID de Usuario"
              secondary={user.id}
            />
          </ListItem>

          <ListItem>
            <ListItemIcon>
              <EmailIcon color="primary" />
            </ListItemIcon>
            <ListItemText
              primary="Email de acceso"
              secondary={user.email}
            />
          </ListItem>

          <ListItem>
            <ListItemIcon>
              <BadgeIcon color="primary" />
            </ListItemIcon>
            <ListItemText
              primary="Rol en el sistema"
              secondary={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                  <Chip
                    label={usersService.getRoleLabel(user.rol)}
                    color={usersService.getRoleColor(user.rol)}
                    size="small"
                  />
                </Box>
              }
            />
          </ListItem>

          <ListItem>
            <ListItemIcon>
              <CalendarIcon color="primary" />
            </ListItemIcon>
            <ListItemText
              primary="Fecha de registro"
              secondary={formatDate(user.created_at)}
            />
          </ListItem>

          <ListItem>
            <ListItemIcon>
              <ScheduleIcon color="primary" />
            </ListItemIcon>
            <ListItemText
              primary="Antigüedad en el sistema"
              secondary={getAccountAge(user.created_at)}
            />
          </ListItem>

          <ListItem>
            <ListItemIcon>
              <CheckCircleIcon color={user.is_active ? 'success' : 'error'} />
            </ListItemIcon>
            <ListItemText
              primary="Estado de la cuenta"
              secondary={
                <Chip
                  label={user.is_active ? 'Activa' : 'Inactiva'}
                  color={user.is_active ? 'success' : 'error'}
                  size="small"
                  variant="outlined"
                />
              }
            />
          </ListItem>
        </List>

        {/* Permisos del rol */}
        <Box>
          <Typography variant="h6" gutterBottom>
            Permisos de tu rol
          </Typography>
          
          <Paper variant="outlined" sx={{ p: 2 }}>
            <List dense>
              {getRolePermissions(user.rol).map((permission, index) => (
                <ListItem key={index} sx={{ py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <CheckCircleIcon color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary={permission}
                    primaryTypographyProps={{ variant: 'body2' }}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Box>

        {/* Estadísticas */}
        <Box>
          <Typography variant="h6" gutterBottom>
            Estadísticas de la cuenta
          </Typography>
          
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 2 }}>
            <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="primary">
                {getDaysActive(user.created_at)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Días activo
              </Typography>
            </Paper>
            
            <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="success.main">
                {user.is_active ? '100%' : '0%'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Disponibilidad
              </Typography>
            </Paper>
          </Box>
        </Box>

        {/* Información de seguridad */}
        <Box>
          <Typography variant="h6" gutterBottom>
            Seguridad
          </Typography>
          
          <List dense>
            <ListItem>
              <ListItemText
                primary="Última actualización de perfil"
                secondary="Información no disponible"
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="Último cambio de contraseña"
                secondary="Información no disponible"
              />
            </ListItem>
          </List>
          
          <Typography variant="caption" color="text.secondary">
            Para mayor seguridad, se recomienda cambiar la contraseña regularmente.
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default AccountInfo;