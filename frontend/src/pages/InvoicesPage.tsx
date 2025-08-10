/**
 * Página principal del módulo de facturación
 * Incluye dashboard con estadísticas, cartera y navegación por tabs
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
  Receipt as ReceiptIcon,
  AttachMoney as MoneyIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  AccountBalance as AccountBalanceIcon,
  Assessment as AssessmentIcon
} from '@mui/icons-material';
import { InvoicesService, InvoiceStatistics, PortfolioValue, TopClient } from '../services/invoicesService';
import { InvoiceStatus, Invoice } from '../types';
import InvoicesList from '../components/invoices/InvoicesList';
import InvoiceForm from '../components/invoices/InvoiceForm';

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
      id={`invoices-tabpanel-${index}`}
      aria-labelledby={`invoices-tab-${index}`}
      {...other}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
}

const InvoicesPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  
  // Estados para estadísticas
  const [stats, setStats] = useState<InvoiceStatistics | null>(null);
  const [portfolioValue, setPortfolioValue] = useState<PortfolioValue | null>(null);
  const [overdueInvoices, setOverdueInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dataLoaded, setDataLoaded] = useState(false);

  useEffect(() => {
    // Solo cargar datos una vez al montar el componente
    loadDashboardData();
  }, []); // Dependencias vacías para cargar solo una vez

  const loadDashboardData = async () => {
    if (dataLoaded && !loading) return; // Evitar cargas duplicadas
    
    try {
      setLoading(true);
      setError(null);

      // Cargar datos en paralelo con manejo de errores individual
      const [statsData, portfolioData, overdueData] = await Promise.all([
        InvoicesService.getCompleteStatistics().catch((error) => {
          if (error.message === 'ENDPOINT_NOT_IMPLEMENTED') {
            // Solo mostrar warning una vez para endpoints no implementados
            console.warn('🔧 Endpoint de estadísticas pendiente de implementación en el backend');
          } else {
            console.error('Error al cargar estadísticas:', error.message);
          }
          // Datos por defecto mientras se implementa el backend
          return {
            total_facturas_emitidas: 0,
            total_facturas_pagadas: 0,
            total_facturas_anuladas: 0,
            valor_total_ventas: 0,
            valor_pendiente_cobro: 0,
            promedio_dias_pago: 0,
            productos_mas_vendidos: [],
            clientes_top: []
          };
        }),
        InvoicesService.getPortfolioValue().catch((error) => {
          if (error.message === 'ENDPOINT_NOT_IMPLEMENTED') {
            console.warn('🔧 Endpoint de cartera pendiente de implementación en el backend');
          } else {
            console.error('Error al cargar cartera:', error.message);
          }
          return {
            total_cartera: 0,
            cartera_vigente: 0,
            cartera_vencida: 0,
            numero_facturas_pendientes: 0
          };
        }), 
        InvoicesService.getOverdueInvoices().catch((error) => {
          if (error.message === 'ENDPOINT_NOT_IMPLEMENTED') {
            console.warn('🔧 Endpoint de facturas vencidas pendiente de implementación en el backend');
          } else {
            console.error('Error al cargar facturas vencidas:', error.message);
          }
          return [];
        })
      ]);

      setStats(statsData);
      setPortfolioValue(portfolioData);
      setOverdueInvoices(overdueData);
      setDataLoaded(true);
    } catch (error: any) {
      console.error('Error al cargar datos del dashboard:', error);
      setError('Error al cargar el dashboard. Algunos datos pueden no estar disponibles.');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleOpenForm = (invoice?: Invoice) => {
    setSelectedInvoice(invoice || null);
    setIsFormOpen(true);
  };

  const handleCloseForm = () => {
    setIsFormOpen(false);
    setSelectedInvoice(null);
  };

  const handleInvoiceSaved = () => {
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
      <Paper elevation={2} sx={{ p: 3, mb: 3, bgcolor: 'warning.main', color: 'white' }}>
        <Box display="flex" alignItems="center" gap={2}>
          <ReceiptIcon sx={{ fontSize: 40 }} />
          <Box>
            <Typography variant="h4" component="h1" fontWeight="bold">
              Gestión de Facturas
            </Typography>
            <Typography variant="subtitle1" sx={{ opacity: 0.9 }}>
              Administra tu facturación, ventas y cartera de clientes
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

      {/* Message if backend not ready */}
      {!stats?.total_facturas_emitidas && !loading && !error && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="body1" sx={{ fontWeight: 'bold', mb: 1 }}>
            ⚠️ Módulo de Facturas - Estado de Desarrollo
          </Typography>
          <Typography variant="body2">
            El frontend está completamente implementado y listo para usar. Sin embargo, los endpoints del backend de facturas 
            aún están pendientes de implementación. Una vez que el backend esté disponible, todas las funcionalidades 
            (crear, editar, listar, reportes) funcionarán automáticamente.
          </Typography>
        </Alert>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Facturas Emitidas */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'primary.main', color: 'white', height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h6" fontWeight="bold">
                    {stats?.total_facturas_emitidas.toLocaleString() || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Total Emitidas
                  </Typography>
                </Box>
                <ReceiptIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Facturas Pagadas */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'success.main', color: 'white', height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h6" fontWeight="bold">
                    {stats?.total_facturas_pagadas.toLocaleString() || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Pagadas
                  </Typography>
                </Box>
                <CheckCircleIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Total Ventas */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'info.main', color: 'white', height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h6" fontWeight="bold">
                    {InvoicesService.formatCurrency(stats?.valor_total_ventas || 0)}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Total Ventas
                  </Typography>
                </Box>
                <MoneyIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Cartera Pendiente */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'warning.main', color: 'white', height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h6" fontWeight="bold">
                    {InvoicesService.formatCurrency(stats?.valor_pendiente_cobro || 0)}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Pendiente Cobro
                  </Typography>
                </Box>
                <AccountBalanceIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Facturas Anuladas */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'error.main', color: 'white', height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h6" fontWeight="bold">
                    {stats?.total_facturas_anuladas.toLocaleString() || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Anuladas
                  </Typography>
                </Box>
                <CancelIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Promedio Días Pago */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'secondary.main', color: 'white', height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h6" fontWeight="bold">
                    {Math.round(stats?.promedio_dias_pago || 0)}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Días Promedio Pago
                  </Typography>
                </Box>
                <TrendingUpIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Cartera Panel */}
      {portfolioValue && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AccountBalanceIcon /> Estado de Cartera
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <Box textAlign="center">
                    <Typography variant="h5" fontWeight="bold" color="primary">
                      {InvoicesService.formatCurrency(portfolioValue.total_cartera)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Cartera
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Box textAlign="center">
                    <Typography variant="h5" fontWeight="bold" color="success.main">
                      {InvoicesService.formatCurrency(portfolioValue.cartera_vigente)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Vigente
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Box textAlign="center">
                    <Typography variant="h5" fontWeight="bold" color="error.main">
                      {InvoicesService.formatCurrency(portfolioValue.cartera_vencida)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Vencida
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <WarningIcon /> Facturas Vencidas
              </Typography>
              <Box textAlign="center">
                <Typography variant="h4" fontWeight="bold" color="error.main">
                  {overdueInvoices.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Facturas por cobrar
                </Typography>
                {overdueInvoices.length > 0 && (
                  <Chip 
                    label="Requiere Atención" 
                    color="error" 
                    size="small"
                    sx={{ mt: 1 }}
                  />
                )}
              </Box>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Top Clientes */}
      {stats?.clientes_top && stats.clientes_top.length > 0 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AssessmentIcon /> Mejores Clientes
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {stats.clientes_top.slice(0, 5).map((client) => (
              <Chip
                key={client.cliente_id}
                label={`${client.nombre_completo} (${InvoicesService.formatCurrency(client.valor_total_compras)})`}
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
          <Tab label="Lista de Facturas" />
          <Tab label="Facturas Vencidas" />
        </Tabs>

        {/* Tab Panels */}
        <TabPanel value={tabValue} index={0}>
          <InvoicesList 
            onEditInvoice={handleOpenForm}
            onRefresh={loadDashboardData}
          />
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          <InvoicesList 
            onEditInvoice={handleOpenForm}
            onRefresh={loadDashboardData}
            filterOverdue={true}
          />
        </TabPanel>
      </Paper>

      {/* Floating Action Button */}
      <Fab
        color="primary"
        aria-label="add invoice"
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

      {/* Invoice Form Dialog */}
      <InvoiceForm
        open={isFormOpen}
        onClose={handleCloseForm}
        onSave={handleInvoiceSaved}
        invoice={selectedInvoice}
      />
    </Box>
  );
};

export default InvoicesPage;