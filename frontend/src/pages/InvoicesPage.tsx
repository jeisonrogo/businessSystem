/**
 * Página principal del módulo de facturación - Modern Professional Interface
 * Incluye dashboard con estadísticas, cartera y navegación por tabs
 * Sistema de Gestión Empresarial
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Tabs,
  Tab,
  Fab,
  Alert,
  Chip,
  Container,
  alpha,
  useTheme,
  Fade,
  LinearProgress,
  IconButton,
  Tooltip,
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
  Refresh,
  ShowChart,
  Group,
} from '@mui/icons-material';
import { InvoicesService, InvoiceStatistics, PortfolioValue } from '../services/invoicesService';
import { Invoice } from '../types';
import InvoicesList from '../components/invoices/InvoicesList';
import InvoiceForm from '../components/invoices/InvoiceForm';
import ModernCard from '../components/common/ModernCard';
import ModernStatsCard from '../components/common/ModernStatsCard';
import { useTenant } from '../context/TenantContext';

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
  const theme = useTheme();
  const { selectedLocal, selectedStore, isStoreManager } = useTenant();

  const [tabValue, setTabValue] = useState(0);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);

  // Estados para estadísticas
  const [stats, setStats] = useState<InvoiceStatistics | null>(null);
  const [portfolioValue, setPortfolioValue] = useState<PortfolioValue | null>(null);
  const [overdueInvoices, setOverdueInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [, setDataLoaded] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const hasFetchedRef = useRef(false);

  useEffect(() => {
    // Solo cargar datos una vez al montar el componente
    loadDashboardData();
  }, []); // Dependencias vacías para cargar solo una vez

  const loadDashboardData = async (forceRefresh: boolean = false, showRefreshing: boolean = false) => {
    // Evitar múltiples llamadas en React.StrictMode (desarrollo), excepto si es forzado
    if (hasFetchedRef.current && !forceRefresh) return;
    if (!forceRefresh) hasFetchedRef.current = true;

    try {
      if (showRefreshing) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);

      // Cargar datos en paralelo con manejo de errores individual
      const [statsData, portfolioData, overdueData] = await Promise.all([
        InvoicesService.getCompleteStatistics().catch((error) => {
          console.error('Error al cargar estadísticas:', error.message);
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
          console.error('Error al cargar cartera:', error.message);
          return {
            total_cartera: 0,
            cartera_vigente: 0,
            cartera_vencida: 0,
            numero_facturas_pendientes: 0
          };
        }), 
        InvoicesService.getOverdueInvoices().catch((error) => {
          console.error('Error al cargar facturas vencidas:', error.message);
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
      setRefreshing(false);
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
    setRefreshKey(prev => prev + 1); // Forzar refresh de listas
    // Delay para permitir que el backend procese el cambio
    setTimeout(() => {
      loadDashboardData(true); // Recargar estadísticas forzadamente
    }, 500);
  };

  const refreshDashboardData = () => {
    setTimeout(() => {
      loadDashboardData(true, true);
    }, 500);
  };

  const handleManualRefresh = () => {
    loadDashboardData(true, true);
  };

  if (loading && !refreshing) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ mb: 4 }}>
          <Typography
            variant="h3"
            component="h1"
            sx={{
              fontWeight: 700,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              mb: 1,
            }}
          >
            Gestión de Facturas
          </Typography>
          <Typography variant="h6" color="text.secondary">
            Cargando dashboard de facturación...
          </Typography>
        </Box>

        <Grid container spacing={3}>
          {[...Array(6)].map((_, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <ModernCard variant="glass">
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Box sx={{ width: 48, height: 48, borderRadius: 2, bgcolor: 'action.hover', mr: 2 }} />
                    <Box sx={{ flex: 1 }}>
                      <Box sx={{ height: 20, bgcolor: 'action.hover', borderRadius: 1, mb: 1 }} />
                      <Box sx={{ height: 32, bgcolor: 'action.selected', borderRadius: 1 }} />
                    </Box>
                  </Box>
                </CardContent>
              </ModernCard>
            </Grid>
          ))}
        </Grid>
      </Container>
    );
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: `linear-gradient(135deg,
          ${alpha(theme.palette.warning.main, 0.05)} 0%,
          ${alpha(theme.palette.primary.main, 0.05)} 50%,
          ${alpha(theme.palette.secondary.main, 0.03)} 100%
        )`,
        py: 3,
      }}
    >
      <Container maxWidth="xl">
        <Fade in timeout={600}>
          <Box>
            {/* Modern Header Section */}
            <ModernCard variant="gradient" sx={{ mb: 4, p: 4 }}>
              <Box sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                flexDirection: { xs: 'column', md: 'row' },
                gap: { xs: 2, md: 0 }
              }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                  <Box
                    sx={{
                      p: 2,
                      borderRadius: 3,
                      background: `linear-gradient(135deg, ${theme.palette.warning.main}, ${theme.palette.warning.dark})`,
                      color: 'white',
                      boxShadow: `0 8px 32px ${alpha(theme.palette.warning.main, 0.3)}`,
                    }}
                  >
                    <ReceiptIcon sx={{ fontSize: 40 }} />
                  </Box>
                  <Box>
                    <Typography
                      variant="h3"
                      component="h1"
                      sx={{
                        fontWeight: 700,
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        backgroundClip: 'text',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        mb: 1,
                        fontSize: { xs: '2rem', md: '3rem' }
                      }}
                    >
                      Gestión de Facturas
                    </Typography>
                    <Typography
                      variant="h6"
                      color="text.secondary"
                      sx={{
                        fontWeight: 500,
                        mb: 1,
                      }}
                    >
                      Administración integral de facturación y cartera
                    </Typography>

                    {/* Modern Local Context Indicator */}
                    <Box
                      sx={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        px: 2,
                        py: 1,
                        backgroundColor: selectedLocal
                          ? alpha(theme.palette.success.main, 0.1)
                          : isStoreManager() && selectedStore
                          ? alpha(theme.palette.info.main, 0.1)
                          : alpha(theme.palette.warning.main, 0.1),
                        border: `1px solid ${
                          selectedLocal
                            ? alpha(theme.palette.success.main, 0.3)
                            : isStoreManager() && selectedStore
                            ? alpha(theme.palette.info.main, 0.3)
                            : alpha(theme.palette.warning.main, 0.3)
                        }`,
                        borderRadius: 2,
                        backdropFilter: 'blur(10px)',
                      }}
                    >
                      <Typography
                        variant="body2"
                        sx={{
                          fontWeight: 600,
                          color: selectedLocal
                            ? 'success.dark'
                            : isStoreManager() && selectedStore
                            ? 'info.dark'
                            : 'warning.dark',
                        }}
                      >
                        {selectedLocal ? (
                          `📄 Local: ${selectedLocal.nombre} (${selectedLocal.codigo})`
                        ) : isStoreManager() && selectedStore ? (
                          `🏢 Todos los locales de ${selectedStore.nombre}`
                        ) : (
                          '⚠️ Sin contexto local seleccionado'
                        )}
                      </Typography>
                    </Box>
                  </Box>
                </Box>

                <Tooltip title="Actualizar datos" arrow>
                  <IconButton
                    onClick={handleManualRefresh}
                    disabled={loading || refreshing}
                    sx={{
                      background: alpha(theme.palette.primary.main, 0.1),
                      backdropFilter: 'blur(10px)',
                      border: '1px solid',
                      borderColor: alpha(theme.palette.primary.main, 0.2),
                      borderRadius: 2,
                      p: 1.5,
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        background: alpha(theme.palette.primary.main, 0.15),
                        transform: 'translateY(-2px)',
                        boxShadow: `0 8px 25px ${alpha(theme.palette.primary.main, 0.3)}`,
                      },
                    }}
                  >
                    <Refresh sx={{ color: 'primary.main' }} />
                  </IconButton>
                </Tooltip>
              </Box>
            </ModernCard>

            {refreshing && (
              <LinearProgress
                sx={{
                  mb: 3,
                  borderRadius: 2,
                  height: 6,
                  background: alpha(theme.palette.warning.main, 0.1),
                  '& .MuiLinearProgress-bar': {
                    background: `linear-gradient(135deg, ${theme.palette.warning.main}, ${theme.palette.warning.dark})`,
                    borderRadius: 2,
                  }
                }}
              />
            )}

            {/* Modern Error Alert */}
            {error && (
              <Fade in timeout={800}>
                <Alert
                  severity="error"
                  sx={{
                    mb: 3,
                    borderRadius: 3,
                    border: '1px solid',
                    borderColor: alpha(theme.palette.error.main, 0.2),
                    background: alpha(theme.palette.error.main, 0.05),
                    backdropFilter: 'blur(10px)',
                  }}
                  onClose={() => setError(null)}
                >
                  {error}
                </Alert>
              </Fade>
            )}


            {/* Modern Statistics Cards */}
            <Fade in timeout={1000}>
              <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={4}>
                  <ModernStatsCard
                    title="Facturas Emitidas"
                    value={stats?.total_facturas_emitidas || 0}
                    subtitle="total general"
                    icon={ReceiptIcon}
                    color="primary"
                    variant="gradient"
                    loading={loading}
                    trend={{
                      value: 8.3,
                      label: 'vs mes anterior',
                      direction: 'up'
                    }}
                    status={{
                      label: 'Activas',
                      color: 'primary'
                    }}
                  />
                </Grid>

                <Grid item xs={12} sm={6} md={4}>
                  <ModernStatsCard
                    title="Facturas Pagadas"
                    value={stats?.total_facturas_pagadas || 0}
                    subtitle="cobradas"
                    icon={CheckCircleIcon}
                    color="success"
                    variant="gradient"
                    loading={loading}
                    trend={{
                      value: 12.1,
                      label: 'vs mes anterior',
                      direction: 'up'
                    }}
                    status={{
                      label: 'Saludable',
                      color: 'success'
                    }}
                  />
                </Grid>

                <Grid item xs={12} sm={6} md={4}>
                  <ModernStatsCard
                    title="Total Ventas"
                    value={InvoicesService.formatCurrency(stats?.valor_total_ventas || 0)}
                    icon={MoneyIcon}
                    color="info"
                    variant="gradient"
                    loading={loading}
                    trend={{
                      value: 15.7,
                      label: 'vs mes anterior',
                      direction: 'up'
                    }}
                    status={{
                      label: 'Excelente',
                      color: 'success'
                    }}
                  />
                </Grid>

                <Grid item xs={12} sm={6} md={4}>
                  <ModernStatsCard
                    title="Cartera Pendiente"
                    value={InvoicesService.formatCurrency(stats?.valor_pendiente_cobro || 0)}
                    subtitle="por cobrar"
                    icon={AccountBalanceIcon}
                    color="warning"
                    variant="gradient"
                    loading={loading}
                    status={{
                      label: 'Gestionar',
                      color: 'warning'
                    }}
                  />
                </Grid>

                <Grid item xs={12} sm={6} md={4}>
                  <ModernStatsCard
                    title="Facturas Anuladas"
                    value={stats?.total_facturas_anuladas || 0}
                    subtitle="canceladas"
                    icon={CancelIcon}
                    color="error"
                    variant="gradient"
                    loading={loading}
                    status={(stats?.total_facturas_anuladas || 0) > 0 ? {
                      label: 'Revisar',
                      color: 'error'
                    } : {
                      label: 'Normal',
                      color: 'success'
                    }}
                  />
                </Grid>

                <Grid item xs={12} sm={6} md={4}>
                  <ModernStatsCard
                    title="Días Promedio Pago"
                    value={Math.round(stats?.promedio_dias_pago || 0)}
                    subtitle="días"
                    icon={TrendingUpIcon}
                    color="secondary"
                    variant="gradient"
                    loading={loading}
                    status={{
                      label: (stats?.promedio_dias_pago || 0) <= 30 ? 'Excelente' : 'Mejorar',
                      color: (stats?.promedio_dias_pago || 0) <= 30 ? 'success' : 'warning'
                    }}
                  />
                </Grid>
              </Grid>
            </Fade>

            {/* Modern Portfolio Panel */}
            {portfolioValue && (
              <Fade in timeout={1200}>
                <Grid container spacing={3} sx={{ mb: 4 }}>
                  <Grid item xs={12} md={8}>
                    <ModernCard variant="glass" sx={{ p: 4, height: '100%' }}>
                      <Typography
                        variant="h5"
                        sx={{
                          fontWeight: 700,
                          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                          backgroundClip: 'text',
                          WebkitBackgroundClip: 'text',
                          WebkitTextFillColor: 'transparent',
                          mb: 2,
                          display: 'flex',
                          alignItems: 'center',
                          gap: 1,
                        }}
                      >
                        <AccountBalanceIcon sx={{ color: 'primary.main' }} />
                        Estado de Cartera
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        Análisis detallado de cuentas por cobrar y flujo de caja
                      </Typography>

                      <Grid container spacing={3}>
                        <Grid item xs={12} sm={4}>
                          <Box textAlign="center" sx={{ p: 2 }}>
                            <Typography
                              variant="h4"
                              sx={{
                                fontWeight: 700,
                                color: 'primary.main',
                                mb: 1,
                              }}
                            >
                              {InvoicesService.formatCurrency(portfolioValue.total_cartera)}
                            </Typography>
                            <Typography variant="body1" color="text.secondary" sx={{ fontWeight: 600 }}>
                              Total Cartera
                            </Typography>
                            <Box sx={{ mt: 1, height: 4, bgcolor: alpha(theme.palette.primary.main, 0.1), borderRadius: 2 }}>
                              <Box sx={{ width: '100%', height: '100%', bgcolor: 'primary.main', borderRadius: 2 }} />
                            </Box>
                          </Box>
                        </Grid>
                        <Grid item xs={12} sm={4}>
                          <Box textAlign="center" sx={{ p: 2 }}>
                            <Typography
                              variant="h4"
                              sx={{
                                fontWeight: 700,
                                color: 'success.main',
                                mb: 1,
                              }}
                            >
                              {InvoicesService.formatCurrency(portfolioValue.cartera_vigente)}
                            </Typography>
                            <Typography variant="body1" color="text.secondary" sx={{ fontWeight: 600 }}>
                              Cartera Vigente
                            </Typography>
                            <Box sx={{ mt: 1, height: 4, bgcolor: alpha(theme.palette.success.main, 0.1), borderRadius: 2 }}>
                              <Box
                                sx={{
                                  width: `${portfolioValue.total_cartera > 0 ? (portfolioValue.cartera_vigente / portfolioValue.total_cartera) * 100 : 0}%`,
                                  height: '100%',
                                  bgcolor: 'success.main',
                                  borderRadius: 2,
                                  transition: 'width 1s ease'
                                }}
                              />
                            </Box>
                          </Box>
                        </Grid>
                        <Grid item xs={12} sm={4}>
                          <Box textAlign="center" sx={{ p: 2 }}>
                            <Typography
                              variant="h4"
                              sx={{
                                fontWeight: 700,
                                color: 'error.main',
                                mb: 1,
                              }}
                            >
                              {InvoicesService.formatCurrency(portfolioValue.cartera_vencida)}
                            </Typography>
                            <Typography variant="body1" color="text.secondary" sx={{ fontWeight: 600 }}>
                              Cartera Vencida
                            </Typography>
                            <Box sx={{ mt: 1, height: 4, bgcolor: alpha(theme.palette.error.main, 0.1), borderRadius: 2 }}>
                              <Box
                                sx={{
                                  width: `${portfolioValue.total_cartera > 0 ? (portfolioValue.cartera_vencida / portfolioValue.total_cartera) * 100 : 0}%`,
                                  height: '100%',
                                  bgcolor: 'error.main',
                                  borderRadius: 2,
                                  transition: 'width 1s ease'
                                }}
                              />
                            </Box>
                          </Box>
                        </Grid>
                      </Grid>
                    </ModernCard>
                  </Grid>

                  <Grid item xs={12} md={4}>
                    <ModernCard variant="gradient" sx={{ p: 4, height: '100%', border: `2px solid ${alpha(theme.palette.error.main, 0.2)}` }}>
                      <Typography
                        variant="h6"
                        sx={{
                          fontWeight: 700,
                          mb: 2,
                          display: 'flex',
                          alignItems: 'center',
                          gap: 1,
                          color: 'error.main',
                        }}
                      >
                        <WarningIcon />
                        Atención Requerida
                      </Typography>
                      <Box textAlign="center">
                        <Typography
                          variant="h2"
                          sx={{
                            fontWeight: 700,
                            color: 'error.main',
                            mb: 1,
                          }}
                        >
                          {overdueInvoices.length}
                        </Typography>
                        <Typography variant="body1" color="text.secondary" sx={{ fontWeight: 600, mb: 2 }}>
                          Facturas Vencidas
                        </Typography>
                        {overdueInvoices.length > 0 && (
                          <Chip
                            label="Gestión Inmediata"
                            color="error"
                            variant="filled"
                            sx={{
                              fontWeight: 700,
                              borderRadius: 2,
                              boxShadow: `0 4px 16px ${alpha(theme.palette.error.main, 0.3)}`,
                            }}
                          />
                        )}
                      </Box>
                    </ModernCard>
                  </Grid>
                </Grid>
              </Fade>
            )}

            {/* Modern Top Clients Section */}
            {stats?.clientes_top && stats.clientes_top.length > 0 && stats.clientes_top.some(client => client.nombre_completo && client.valor_total_compras > 0) && (
              <Fade in timeout={1400}>
                <ModernCard variant="glass" sx={{ p: 4, mb: 4 }}>
                  <Typography
                    variant="h5"
                    sx={{
                      fontWeight: 700,
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      backgroundClip: 'text',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      mb: 1,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                    }}
                  >
                    <Group sx={{ color: 'primary.main' }} />
                    Top 5 Clientes Destacados
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    Clientes con mayor volumen de compras y mejor relación comercial
                  </Typography>

                  <Grid container spacing={2}>
                    {stats.clientes_top
                      .filter(client => client.nombre_completo && client.valor_total_compras > 0)
                      .slice(0, 5)
                      .map((client, index) => {
                        const colors = ['#667eea', '#f5576c', '#4facfe', '#43e97b', '#fa709a'];
                        return (
                          <Grid item xs={12} sm={6} md={4} key={client.cliente_id || index}>
                            <Card
                              sx={{
                                p: 2.5,
                                borderRadius: 2,
                                background: alpha(theme.palette.background.paper, 0.8),
                                border: '1px solid',
                                borderColor: alpha(colors[index], 0.2),
                                borderLeft: `4px solid ${colors[index]}`,
                                transition: 'all 0.3s ease',
                                '&:hover': {
                                  transform: 'translateY(-2px)',
                                  boxShadow: `0 8px 25px ${alpha(colors[index], 0.2)}`,
                                  borderColor: alpha(colors[index], 0.4),
                                },
                              }}
                            >
                              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                <Box
                                  sx={{
                                    width: 40,
                                    height: 40,
                                    borderRadius: '50%',
                                    background: colors[index],
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    color: 'white',
                                    fontWeight: 700,
                                    mr: 2,
                                  }}
                                >
                                  #{index + 1}
                                </Box>
                                <Box sx={{ flex: 1, minWidth: 0 }}>
                                  <Typography
                                    variant="subtitle1"
                                    sx={{
                                      fontWeight: 600,
                                      overflow: 'hidden',
                                      textOverflow: 'ellipsis',
                                      whiteSpace: 'nowrap',
                                    }}
                                  >
                                    {client.nombre_completo}
                                  </Typography>
                                  <Typography
                                    variant="h6"
                                    sx={{
                                      fontWeight: 700,
                                      color: colors[index],
                                    }}
                                  >
                                    {InvoicesService.formatCurrency(client.valor_total_compras || 0)}
                                  </Typography>
                                </Box>
                              </Box>
                            </Card>
                          </Grid>
                        );
                      })}
                  </Grid>
                </ModernCard>
              </Fade>
            )}

            {/* Modern Content Tabs */}
            <Fade in timeout={1600}>
              <ModernCard
                variant="glass"
                sx={{
                  mb: 3,
                  overflow: 'hidden',
                  background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.95) 100%)',
                  backdropFilter: 'blur(20px)',
                }}
              >
                <Box sx={{ px: 3, pt: 3, pb: 1 }}>
                  <Typography
                    variant="h5"
                    sx={{
                      fontWeight: 700,
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      backgroundClip: 'text',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      mb: 1,
                    }}
                  >
                    Gestión Detallada de Facturas
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Administración completa del ciclo de facturación y cobros
                  </Typography>
                </Box>

                <Tabs
                  value={tabValue}
                  onChange={handleTabChange}
                  sx={{
                    px: 3,
                    '& .MuiTabs-indicator': {
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      height: 3,
                      borderRadius: 2,
                    },
                    '& .MuiTab-root': {
                      textTransform: 'none',
                      fontWeight: 600,
                      fontSize: '1rem',
                      minHeight: 48,
                      minWidth: 160,
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        background: alpha(theme.palette.primary.main, 0.05),
                        borderRadius: 2,
                      },
                      '&.Mui-selected': {
                        background: alpha(theme.palette.primary.main, 0.08),
                        borderRadius: 2,
                        color: 'primary.main',
                      },
                    },
                  }}
                >
                  <Tab
                    icon={<ShowChart />}
                    iconPosition="start"
                    label="Todas las Facturas"
                    sx={{ mr: 1 }}
                  />
                  <Tab
                    icon={<WarningIcon />}
                    iconPosition="start"
                    label="Facturas Vencidas"
                    sx={{ color: overdueInvoices.length > 0 ? 'error.main' : undefined }}
                  />
                </Tabs>

                <Box sx={{ p: 4 }}>
                  <TabPanel value={tabValue} index={0}>
                    <Box sx={{ minHeight: 400 }}>
                      <Fade in timeout={300}>
                        <Box>
                          <InvoicesList
                            key={`invoices-list-${refreshKey}`}
                            onEditInvoice={handleOpenForm}
                            onRefresh={refreshDashboardData}
                          />
                        </Box>
                      </Fade>
                    </Box>
                  </TabPanel>

                  <TabPanel value={tabValue} index={1}>
                    <Box sx={{ minHeight: 400 }}>
                      <Fade in timeout={300}>
                        <Box>
                          <InvoicesList
                            key={`overdue-list-${refreshKey}`}
                            onEditInvoice={handleOpenForm}
                            onRefresh={refreshDashboardData}
                            filterOverdue={true}
                          />
                        </Box>
                      </Fade>
                    </Box>
                  </TabPanel>
                </Box>
              </ModernCard>
            </Fade>

            {/* Modern Floating Action Button */}
            <Fab
              color="primary"
              aria-label="Crear nueva factura"
              onClick={() => handleOpenForm()}
              disabled={!selectedLocal && !(isStoreManager() && selectedStore)}
              sx={{
                position: 'fixed',
                bottom: 24,
                right: 24,
                zIndex: 1000,
                background: `linear-gradient(135deg, ${theme.palette.warning.main}, ${theme.palette.warning.dark})`,
                boxShadow: `0 8px 32px ${alpha(theme.palette.warning.main, 0.3)}`,
                '&:hover': {
                  transform: 'scale(1.1)',
                  boxShadow: `0 12px 40px ${alpha(theme.palette.warning.main, 0.4)}`,
                },
                '&:disabled': {
                  background: alpha(theme.palette.action.disabled, 0.3),
                  boxShadow: 'none',
                },
                transition: 'all 0.3s ease',
              }}
            >
              <AddIcon />
            </Fab>

            {/* Modern Invoice Form Dialog */}
            <InvoiceForm
              open={isFormOpen}
              onClose={handleCloseForm}
              onSave={handleInvoiceSaved}
              invoice={selectedInvoice}
            />
          </Box>
        </Fade>
      </Container>
    </Box>
  );
};

export default InvoicesPage;