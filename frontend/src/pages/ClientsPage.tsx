/**
 * Página principal del módulo de gestión de clientes
 * Incluye dashboard con estadísticas y navegación por tabs
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Tabs,
  Tab,
  Fab,
  Alert,
  CircularProgress,
  Chip
} from '@mui/material';
import {
  Add as AddIcon,
  People as PeopleIcon,
  Business as BusinessIcon,
  PersonAdd as PersonAddIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  AccountBalance as AccountBalanceIcon
} from '@mui/icons-material';
import { ClientsService, FrequentClient } from '../services/clientsService';
import { ClientType, Client } from '../types';
import ClientsList from '../components/clients/ClientsList';
import ClientForm from '../components/clients/ClientForm';

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
      id={`clients-tabpanel-${index}`}
      aria-labelledby={`clients-tab-${index}`}
      {...other}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
}

interface ClientsStats {
  total_clientes: number;
  personas_naturales: number;
  empresas: number;
  clientes_activos: number;
  clientes_inactivos: number;
  nuevos_este_mes: number;
}

const ClientsPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  
  // Estados para estadísticas
  const [stats, setStats] = useState<ClientsStats | null>(null);
  const [frequentClients, setFrequentClients] = useState<FrequentClient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Cargar datos en paralelo
      const [allClients, frequentClientsData] = await Promise.all([
        ClientsService.getClients({ limit: 100, page: 1 }), // Para calcular estadísticas
        ClientsService.getFrequentClients(5)
      ]);

      // Calcular estadísticas del lado del cliente
      const clientsList = allClients.items;
      const now = new Date();
      const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);

      const calculatedStats: ClientsStats = {
        total_clientes: allClients.total,
        personas_naturales: clientsList.filter(c => c.tipo_cliente === ClientType.PERSONA_NATURAL).length,
        empresas: clientsList.filter(c => c.tipo_cliente === ClientType.EMPRESA).length,
        clientes_activos: clientsList.filter(c => c.is_active).length,
        clientes_inactivos: clientsList.filter(c => !c.is_active).length,
        nuevos_este_mes: clientsList.filter(c => new Date(c.created_at) >= startOfMonth).length
      };

      setStats(calculatedStats);
      setFrequentClients(frequentClientsData);
    } catch (error: any) {
      console.error('Error al cargar datos del dashboard:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleOpenForm = (client?: Client) => {
    setSelectedClient(client || null);
    setIsFormOpen(true);
  };

  const handleCloseForm = () => {
    setIsFormOpen(false);
    setSelectedClient(null);
  };

  const handleClientSaved = () => {
    handleCloseForm();
    loadDashboardData(); // Recargar estadísticas
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {/* Header */}
      <Paper elevation={2} sx={{ p: 3, mb: 3, bgcolor: 'primary.main', color: 'white' }}>
        <Box display="flex" alignItems="center" gap={2}>
          <PeopleIcon sx={{ fontSize: 40 }} />
          <Box>
            <Typography variant="h4" component="h1" fontWeight="bold">
              Gestión de Clientes
            </Typography>
            <Typography variant="subtitle1" sx={{ opacity: 0.9 }}>
              Administra tu cartera de clientes, personas naturales y empresas
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Statistics Cards */}
      {stats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={2}>
            <Card sx={{ bgcolor: 'primary.main', color: 'white', height: '100%' }}>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography variant="h6" fontWeight="bold">
                      {stats.total_clientes.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      Total Clientes
                    </Typography>
                  </Box>
                  <PeopleIcon sx={{ fontSize: 40, opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={2}>
            <Card sx={{ bgcolor: 'success.main', color: 'white', height: '100%' }}>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography variant="h6" fontWeight="bold">
                      {stats.personas_naturales.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      Personas Naturales
                    </Typography>
                  </Box>
                  <PersonAddIcon sx={{ fontSize: 40, opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={2}>
            <Card sx={{ bgcolor: 'info.main', color: 'white', height: '100%' }}>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography variant="h6" fontWeight="bold">
                      {stats.empresas.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      Empresas
                    </Typography>
                  </Box>
                  <BusinessIcon sx={{ fontSize: 40, opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={2}>
            <Card sx={{ bgcolor: 'warning.main', color: 'white', height: '100%' }}>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography variant="h6" fontWeight="bold">
                      {stats.clientes_activos.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      Activos
                    </Typography>
                  </Box>
                  <TrendingUpIcon sx={{ fontSize: 40, opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={2}>
            <Card sx={{ bgcolor: 'secondary.main', color: 'white', height: '100%' }}>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography variant="h6" fontWeight="bold">
                      {stats.nuevos_este_mes.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      Nuevos Este Mes
                    </Typography>
                  </Box>
                  <AssessmentIcon sx={{ fontSize: 40, opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={2}>
            <Card sx={{ bgcolor: 'error.main', color: 'white', height: '100%' }}>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography variant="h6" fontWeight="bold">
                      {stats.clientes_inactivos.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      Inactivos
                    </Typography>
                  </Box>
                  <AccountBalanceIcon sx={{ fontSize: 40, opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Frequent Clients Card */}
      {frequentClients.length > 0 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TrendingUpIcon /> Clientes Más Frecuentes
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {frequentClients.map((client) => (
              <Chip
                key={client.cliente_id}
                label={`${client.nombre_completo} (${client.total_facturas} facturas)`}
                variant="outlined"
                sx={{ 
                  fontSize: '0.875rem',
                  '& .MuiChip-label': { px: 2 }
                }}
              />
            ))}
          </Box>
        </Paper>
      )}

      {/* Tabs Navigation */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          sx={{
            borderBottom: 1,
            borderColor: 'divider',
            '& .MuiTab-root': {
              minWidth: 160,
              fontWeight: 'medium',
            },
          }}
        >
          <Tab label="Lista de Clientes" />
        </Tabs>

        {/* Tab Panels */}
        <TabPanel value={tabValue} index={0}>
          <ClientsList 
            onEditClient={handleOpenForm}
            onRefresh={loadDashboardData}
          />
        </TabPanel>
      </Paper>

      {/* Floating Action Button */}
      <Fab
        color="primary"
        aria-label="add client"
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          zIndex: 1000,
        }}
        onClick={() => handleOpenForm()}
      >
        <AddIcon />
      </Fab>

      {/* Client Form Dialog */}
      <ClientForm
        open={isFormOpen}
        onClose={handleCloseForm}
        onSave={handleClientSaved}
        client={selectedClient}
      />
    </Box>
  );
};

export default ClientsPage;