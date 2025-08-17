/**
 * Página de administración de usuarios
 * Proporciona interfaz completa para gestión de usuarios del sistema
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Chip
} from '@mui/material';
import {
  Add as AddIcon,
  People as PeopleIcon,
  PersonAdd as PersonAddIcon,
  Assessment as AssessmentIcon
} from '@mui/icons-material';

import { usersService, User, UserStats, USER_ROLES } from '../services/usersService';
import UsersList from '../components/users/UsersList';
import UserForm from '../components/users/UserForm';
import { useAuth } from '../context/AuthContext';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`users-tabpanel-${index}`}
      aria-labelledby={`users-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const UsersPage: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [tabValue, setTabValue] = useState(0);
  
  // Estados para modales
  const [userFormOpen, setUserFormOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  // Verificar permisos de administrador
  const isAdmin = user?.rol === USER_ROLES.ADMINISTRADOR;

  useEffect(() => {
    if (!isAdmin) {
      setError('No tienes permisos para acceder a esta página. Se requieren permisos de administrador.');
      return;
    }
    
    loadData();
  }, [isAdmin, refreshKey]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [usersData, statsData] = await Promise.all([
        usersService.getUsers({ limit: 100 }),
        usersService.getUserStats()
      ]);
      
      setUsers(usersData);
      setStats(statsData);
    } catch (error: any) {
      console.error('Error al cargar datos:', error);
      setError(error.message || 'Error al cargar los datos');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleCreateUser = () => {
    setEditingUser(null);
    setUserFormOpen(true);
  };

  const handleEditUser = (user: User) => {
    setEditingUser(user);
    setUserFormOpen(true);
  };

  const handleCloseUserForm = () => {
    setUserFormOpen(false);
    setEditingUser(null);
  };

  const handleUserSaved = () => {
    setUserFormOpen(false);
    setEditingUser(null);
    setRefreshKey(prev => prev + 1);
  };

  const handleUserDeleted = () => {
    setRefreshKey(prev => prev + 1);
  };

  if (!isAdmin) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          No tienes permisos para acceder a esta página. Se requieren permisos de administrador.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <PeopleIcon fontSize="large" color="primary" />
          Administración de Usuarios
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Gestiona usuarios del sistema, roles y permisos
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Estadísticas */}
      {stats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PeopleIcon color="primary" />
                  <Typography variant="h6">Total Usuarios</Typography>
                </Box>
                <Typography variant="h4" sx={{ mt: 1 }}>
                  {stats.total_users}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PersonAddIcon color="success" />
                  <Typography variant="h6">Usuarios Activos</Typography>
                </Box>
                <Typography variant="h4" sx={{ mt: 1 }}>
                  {stats.active_users}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AssessmentIcon color="info" />
                  <Typography variant="h6">Administradores</Typography>
                </Box>
                <Typography variant="h4" sx={{ mt: 1 }}>
                  {stats.users_by_role[USER_ROLES.ADMINISTRADOR] || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Usuarios por Rol</Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {Object.entries(stats.users_by_role).map(([role, count]) => (
                    <Chip
                      key={role}
                      label={`${usersService.getRoleLabel(role)}: ${count}`}
                      color={usersService.getRoleColor(role)}
                      size="small"
                      variant="outlined"
                    />
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab label="Lista de Usuarios" />
          <Tab label="Gestión de Roles" />
        </Tabs>
      </Paper>

      {/* Content */}
      <TabPanel value={tabValue} index={0}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5">Usuarios del Sistema</Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateUser}
            disabled={loading}
          >
            Crear Usuario
          </Button>
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <UsersList
            users={users}
            onEditUser={handleEditUser}
            onDeleteUser={handleUserDeleted}
            onRefresh={() => setRefreshKey(prev => prev + 1)}
          />
        )}
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Typography variant="h5" gutterBottom>Gestión de Roles</Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Los roles determinan los permisos y accesos que tienen los usuarios en el sistema.
        </Typography>

        <Grid container spacing={3}>
          {Object.entries(USER_ROLES).map(([key, role]) => (
            <Grid item xs={12} sm={6} md={4} key={role}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">{usersService.getRoleLabel(role)}</Typography>
                    <Chip
                      label={`${stats?.users_by_role[role] || 0} usuarios`}
                      color={usersService.getRoleColor(role)}
                      size="small"
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {getRoleDescription(role)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </TabPanel>

      {/* User Form Modal */}
      <UserForm
        open={userFormOpen}
        onClose={handleCloseUserForm}
        onSave={handleUserSaved}
        user={editingUser}
      />
    </Box>
  );
};

// Función auxiliar para obtener descripción del rol
function getRoleDescription(role: string): string {
  switch (role) {
    case USER_ROLES.ADMINISTRADOR:
      return 'Acceso completo al sistema. Puede gestionar usuarios, configuraciones y todos los módulos.';
    case USER_ROLES.GERENTE_VENTAS:
      return 'Acceso a módulos de ventas, facturación, clientes y reportes de ventas.';
    case USER_ROLES.CONTADOR:
      return 'Acceso a módulos de contabilidad, facturación, reportes financieros y asientos contables.';
    case USER_ROLES.VENDEDOR:
      return 'Acceso básico a ventas, productos, clientes y creación de facturas.';
    default:
      return 'Rol personalizado del sistema.';
  }
}

export default UsersPage;