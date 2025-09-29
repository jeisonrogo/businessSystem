/**
 * Modern Dashboard Page - Professional Business Management Interface
 * Sistema de Gestión Empresarial
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Chip,
  Alert,
  Tabs,
  Tab,
  Skeleton,
  Button,
  IconButton,
  Tooltip,
  LinearProgress,
  alpha,
  useTheme,
  Fade,
  Stack,
  Container,
} from '@mui/material';
import Grid2 from '@mui/material/Unstable_Grid2';
import {
  TrendingUp,
  Inventory,
  People,
  Receipt,
  AttachMoney,
  Warning,
  ShowChart,
  Refresh,
  BarChart,
  PieChart,
  Timeline,
  TrendingDown,
  Analytics,
  Group,
} from '@mui/icons-material';
// Importar types
import {
  MetricasRapidas,
  KPIDashboard,
  VentasPorPeriodo,
  ProductoTopVentas,
  ClienteTopVentas,
  AlertaDashboard,
  PeriodoReporte,
} from '../types';
import dashboardService from '../services/dashboardService';

const DashboardPage: React.FC = () => {
  const theme = useTheme();

  // Estados principales
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  
  // Estados de datos
  const [metricasRapidas, setMetricasRapidas] = useState<MetricasRapidas | null>(null);
  const [kpis, setKpis] = useState<KPIDashboard[]>([]);
  const [ventasPorPeriodo, setVentasPorPeriodo] = useState<VentasPorPeriodo[]>([]);
  const [productosTop, setProductosTop] = useState<ProductoTopVentas[]>([]);
  const [clientesTop, setClientesTop] = useState<ClienteTopVentas[]>([]);
  const [alertas, setAlertas] = useState<AlertaDashboard[]>([]);
  
  // Estados de filtros
  const [periodo] = useState<PeriodoReporte>(PeriodoReporte.MES);
  const [refreshing, setRefreshing] = useState(false);

  // Cargar datos del dashboard
  const cargarDatos = async (mostrarLoading = true) => {
    try {
      if (mostrarLoading) {
        setLoading(true);
      } else {
        setRefreshing(true);
      }
      setError(null);

      // Cargar métricas rápidas
      const metricas = await dashboardService.getMetricasRapidas();
      setMetricasRapidas(metricas);

      // Cargar KPIs principales
      const kpisData = await dashboardService.getKPIsPrincipales(periodo);
      setKpis(kpisData);

      // Cargar ventas del período actual
      const { fechaInicio, fechaFin } = periodo === PeriodoReporte.MES 
        ? dashboardService.getMesActual() 
        : dashboardService.getPeriodoDefault();
        
      const ventasData = await dashboardService.getVentasPorPeriodo(
        fechaInicio,
        fechaFin,
        'mes'
      );
      setVentasPorPeriodo(ventasData);

      // Cargar tops
      const [productosData, clientesData] = await Promise.all([
        dashboardService.getProductosTopVentas(fechaInicio, fechaFin, 5),
        dashboardService.getClientesTopVentas(fechaInicio, fechaFin, 5),
      ]);
      setProductosTop(productosData);
      setClientesTop(clientesData);

      // Cargar alertas
      const alertasData = await dashboardService.getAlertasDashboard();
      setAlertas(alertasData);

    } catch (err: any) {
      console.error('Error cargando dashboard:', err);
      setError(err.message || 'Error al cargar los datos del dashboard');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Efecto para cargar datos iniciales
  useEffect(() => {
    cargarDatos();
  }, [periodo]); // eslint-disable-line react-hooks/exhaustive-deps

  // Función para refrescar
  const handleRefresh = () => {
    cargarDatos(false);
  };

  // Función para cambiar de tab
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // Función para obtener color de criticidad
  const getCriticidadColor = (criticidad: 'baja' | 'media' | 'alta') => {
    switch (criticidad) {
      case 'alta': return 'error';
      case 'media': return 'warning';
      case 'baja': return 'info';
      default: return 'default';
    }
  };

  // Función para obtener icono de tendencia
  const getTendenciaIcon = (tendencia: 'positiva' | 'negativa' | 'estable') => {
    switch (tendencia) {
      case 'positiva': return <TrendingUp color="success" />;
      case 'negativa': return <TrendingDown color="error" />;
      case 'estable': return <Timeline color="info" />;
    }
  };

  // Modern sales chart rendering with professional design
  const renderVentasChart = () => {
    if (ventasPorPeriodo.length === 0) {
      return (
        <Box sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: 300,
          color: 'text.secondary',
          background: alpha(theme.palette.grey[50], 0.5),
          borderRadius: 2,
          border: '2px dashed',
          borderColor: 'divider',
        }}>
          <ShowChart sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
          <Typography variant="h6" gutterBottom>
            No hay datos de ventas
          </Typography>
          <Typography variant="body2">
            Los datos de ventas se mostrarán aquí cuando estén disponibles
          </Typography>
        </Box>
      );
    }

    const maxVenta = Math.max(...ventasPorPeriodo.map(v => v.total_ventas));
    const maxFacturas = Math.max(...ventasPorPeriodo.map(v => v.cantidad_facturas));

    return (
      <Box>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
            Tendencia de Ventas - Últimos Meses
          </Typography>
          <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
            <Chip
              label="Ingresos por Ventas"
              color="primary"
              variant="filled"
              sx={{ borderRadius: 2, fontWeight: 500 }}
            />
            <Chip
              label="Cantidad de Facturas"
              color="secondary"
              variant="filled"
              sx={{ borderRadius: 2, fontWeight: 500 }}
            />
          </Stack>
        </Box>

        <Grid2 container spacing={2}>
          {ventasPorPeriodo.slice(-12).map((venta, index) => {
            const ventaPercentage = (venta.total_ventas / maxVenta) * 100;
            const facturaPercentage = (venta.cantidad_facturas / maxFacturas) * 100;

            return (
              <Grid2 key={index} xs={12} sm={6} md={4} lg={3}>
                <Card
                  sx={{
                    p: 2.5,
                    borderRadius: 2,
                    background: alpha(theme.palette.background.paper, 0.8),
                    border: '1px solid',
                    borderColor: alpha(theme.palette.divider, 0.5),
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: `0 8px 25px ${alpha(theme.palette.primary.main, 0.15)}`,
                      borderColor: alpha(theme.palette.primary.main, 0.3),
                    },
                  }}
                >
                  <Typography
                    variant="subtitle2"
                    color="text.secondary"
                    sx={{ fontWeight: 600, mb: 2 }}
                  >
                    {venta.fecha.includes('2025') ? venta.fecha : new Date(venta.fecha).toLocaleDateString('es-ES', { month: 'short', year: 'numeric' })}
                  </Typography>

                  <Box sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                        Ventas
                      </Typography>
                      <Typography variant="caption" sx={{ fontWeight: 600, color: 'primary.main' }}>
                        {dashboardService.formatCurrency(venta.total_ventas)}
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={ventaPercentage}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        background: alpha(theme.palette.primary.main, 0.1),
                        '& .MuiLinearProgress-bar': {
                          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                          borderRadius: 4,
                        }
                      }}
                    />
                  </Box>

                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                        Facturas
                      </Typography>
                      <Typography variant="caption" sx={{ fontWeight: 600, color: 'secondary.main' }}>
                        {venta.cantidad_facturas}
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={facturaPercentage}
                      color="secondary"
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        background: alpha(theme.palette.secondary.main, 0.1),
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 3,
                        }
                      }}
                    />
                  </Box>
                </Card>
              </Grid2>
            );
          })}
        </Grid2>
      </Box>
    );
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ mb: 4 }}>
          <Skeleton variant="text" width={300} height={60} />
          <Skeleton variant="text" width={500} height={30} sx={{ mt: 1 }} />
        </Box>

        <Grid2 container spacing={3}>
          {[...Array(4)].map((_, index) => (
            <Grid2 key={index} xs={12} sm={6} lg={3}>
              <Card
                sx={{
                  borderRadius: 3,
                  background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
                  border: '1px solid',
                  borderColor: alpha(theme.palette.primary.main, 0.1),
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Skeleton variant="circular" width={48} height={48} sx={{ mr: 2 }} />
                    <Box sx={{ flex: 1 }}>
                      <Skeleton variant="text" width="60%" height={20} />
                      <Skeleton variant="text" width="40%" height={32} sx={{ mt: 1 }} />
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid2>
          ))}

          <Grid2 xs={12}>
            <Paper
              sx={{
                p: 4,
                borderRadius: 3,
                background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.95) 100%)',
                backdropFilter: 'blur(10px)',
                border: '1px solid',
                borderColor: alpha(theme.palette.primary.main, 0.1),
              }}
            >
              <Skeleton variant="rectangular" height={400} sx={{ borderRadius: 2 }} />
            </Paper>
          </Grid2>
        </Grid2>
      </Container>
    );
  }

  if (error) {
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
            Dashboard Empresarial
          </Typography>
          <Typography variant="h6" color="text.secondary">
            Sistema de Gestión Empresarial
          </Typography>
        </Box>

        <Fade in>
          <Alert
            severity="error"
            sx={{
              mb: 3,
              borderRadius: 3,
              border: '1px solid',
              borderColor: alpha(theme.palette.error.main, 0.2),
              background: alpha(theme.palette.error.main, 0.05),
            }}
            action={
              <Button
                color="inherit"
                size="small"
                onClick={() => cargarDatos()}
                sx={{ fontWeight: 600 }}
              >
                Reintentar
              </Button>
            }
          >
            {error}
          </Alert>
        </Fade>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Fade in timeout={600}>
        <Box>
          {/* Modern Header Section */}
          <Box sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            mb: 4,
            flexDirection: { xs: 'column', md: 'row' },
            gap: { xs: 2, md: 0 }
          }}>
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
                Dashboard Empresarial
              </Typography>
              <Typography
                variant="h6"
                color="text.secondary"
                sx={{
                  fontWeight: 500,
                  mb: 1,
                }}
              >
                Sistema de Gestión Empresarial
              </Typography>
              <Typography
                variant="body1"
                color="text.secondary"
                sx={{ opacity: 0.8 }}
              >
                Vista general del rendimiento de su negocio
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <Tooltip title="Actualizar datos" arrow>
                <IconButton
                  onClick={handleRefresh}
                  disabled={refreshing}
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
          </Box>

          {refreshing && (
            <LinearProgress
              sx={{
                mb: 3,
                borderRadius: 2,
                height: 6,
                background: alpha(theme.palette.primary.main, 0.1),
                '& .MuiLinearProgress-bar': {
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  borderRadius: 2,
                }
              }}
            />
          )}

          {/* Modern Alerts Section */}
          {alertas.length > 0 && (
            <Fade in timeout={800}>
              <Paper
                sx={{
                  mb: 4,
                  p: 3,
                  borderRadius: 3,
                  background: alpha(theme.palette.warning.main, 0.05),
                  border: '1px solid',
                  borderColor: alpha(theme.palette.warning.main, 0.2),
                }}
              >
                <Typography
                  variant="h6"
                  gutterBottom
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    fontWeight: 600,
                    color: 'warning.main',
                  }}
                >
                  <Warning sx={{ mr: 1 }} />
                  Alertas del Sistema
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
                  {alertas.slice(0, 6).map((alerta, index) => (
                    <Chip
                      key={index}
                      label={`${alerta.titulo}: ${alerta.cantidad}`}
                      color={getCriticidadColor(alerta.criticidad) as any}
                      variant="filled"
                      size="medium"
                      sx={{
                        borderRadius: 2,
                        fontWeight: 500,
                        boxShadow: `0 2px 8px ${alpha(theme.palette.grey[500], 0.3)}`,
                      }}
                    />
                  ))}
                </Stack>
              </Paper>
            </Fade>
          )}

          {/* Modern KPI Cards */}
          <Grid2 container spacing={3} sx={{ mb: 4 }}>
            <Grid2 xs={12} sm={6} lg={3}>
              <Fade in timeout={800}>
                <Card
                  sx={{
                    borderRadius: 3,
                    background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
                    border: '1px solid',
                    borderColor: alpha(theme.palette.primary.main, 0.15),
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: `0 12px 40px ${alpha(theme.palette.primary.main, 0.2)}`,
                      borderColor: alpha(theme.palette.primary.main, 0.3),
                    },
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                      <Box sx={{ flex: 1 }}>
                        <Typography color="text.secondary" variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
                          Total Productos
                        </Typography>
                        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, color: 'primary.main' }}>
                          {metricasRapidas?.total_productos?.toLocaleString() || '0'}
                        </Typography>
                        {(metricasRapidas?.productos_sin_stock || 0) > 0 && (
                          <Chip
                            label={`${metricasRapidas?.productos_sin_stock} sin stock`}
                            color="error"
                            size="small"
                            variant="filled"
                            sx={{ borderRadius: 1.5, fontWeight: 500 }}
                          />
                        )}
                      </Box>
                      <Box
                        sx={{
                          p: 2,
                          borderRadius: 2,
                          background: alpha(theme.palette.primary.main, 0.15),
                        }}
                      >
                        <Inventory sx={{ fontSize: 32, color: 'primary.main' }} />
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Fade>
            </Grid2>

            <Grid2 xs={12} sm={6} lg={3}>
              <Fade in timeout={900}>
                <Card
                  sx={{
                    borderRadius: 3,
                    background: 'linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(67, 160, 71, 0.1) 100%)',
                    border: '1px solid',
                    borderColor: alpha(theme.palette.success.main, 0.15),
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: `0 12px 40px ${alpha(theme.palette.success.main, 0.2)}`,
                      borderColor: alpha(theme.palette.success.main, 0.3),
                    },
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                      <Box sx={{ flex: 1 }}>
                        <Typography color="text.secondary" variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
                          Total Clientes
                        </Typography>
                        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, color: 'success.main' }}>
                          {metricasRapidas?.total_clientes?.toLocaleString() || '0'}
                        </Typography>
                        {(metricasRapidas?.clientes_nuevos_mes || 0) > 0 && (
                          <Chip
                            label={`+${metricasRapidas?.clientes_nuevos_mes} este mes`}
                            color="success"
                            size="small"
                            variant="filled"
                            sx={{ borderRadius: 1.5, fontWeight: 500 }}
                          />
                        )}
                      </Box>
                      <Box
                        sx={{
                          p: 2,
                          borderRadius: 2,
                          background: alpha(theme.palette.success.main, 0.15),
                        }}
                      >
                        <People sx={{ fontSize: 32, color: 'success.main' }} />
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Fade>
            </Grid2>

            <Grid2 xs={12} sm={6} lg={3}>
              <Fade in timeout={1000}>
                <Card
                  sx={{
                    borderRadius: 3,
                    background: 'linear-gradient(135deg, rgba(255, 152, 0, 0.1) 0%, rgba(251, 140, 0, 0.1) 100%)',
                    border: '1px solid',
                    borderColor: alpha(theme.palette.warning.main, 0.15),
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: `0 12px 40px ${alpha(theme.palette.warning.main, 0.2)}`,
                      borderColor: alpha(theme.palette.warning.main, 0.3),
                    },
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                      <Box sx={{ flex: 1 }}>
                        <Typography color="text.secondary" variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
                          Facturas Este Mes
                        </Typography>
                        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, color: 'warning.main' }}>
                          {metricasRapidas?.facturas_mes?.toLocaleString() || '0'}
                        </Typography>
                        {(metricasRapidas?.facturas_vencidas || 0) > 0 && (
                          <Chip
                            label={`${metricasRapidas?.facturas_vencidas} vencidas`}
                            color="error"
                            size="small"
                            variant="filled"
                            sx={{ borderRadius: 1.5, fontWeight: 500 }}
                          />
                        )}
                      </Box>
                      <Box
                        sx={{
                          p: 2,
                          borderRadius: 2,
                          background: alpha(theme.palette.warning.main, 0.15),
                        }}
                      >
                        <Receipt sx={{ fontSize: 32, color: 'warning.main' }} />
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Fade>
            </Grid2>

            <Grid2 xs={12} sm={6} lg={3}>
              <Fade in timeout={1100}>
                <Card
                  sx={{
                    borderRadius: 3,
                    background: 'linear-gradient(135deg, rgba(33, 150, 243, 0.1) 0%, rgba(30, 136, 229, 0.1) 100%)',
                    border: '1px solid',
                    borderColor: alpha(theme.palette.info.main, 0.15),
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: `0 12px 40px ${alpha(theme.palette.info.main, 0.2)}`,
                      borderColor: alpha(theme.palette.info.main, 0.3),
                    },
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                      <Box sx={{ flex: 1 }}>
                        <Typography color="text.secondary" variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
                          Valor Inventario
                        </Typography>
                        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, color: 'info.main' }}>
                          {dashboardService.formatCurrency(metricasRapidas?.valor_inventario || 0)}
                        </Typography>
                        <Chip
                          label={`Ventas hoy: ${dashboardService.formatCurrency(metricasRapidas?.ventas_hoy || 0)}`}
                          color="success"
                          size="small"
                          variant="filled"
                          sx={{ borderRadius: 1.5, fontWeight: 500 }}
                        />
                      </Box>
                      <Box
                        sx={{
                          p: 2,
                          borderRadius: 2,
                          background: alpha(theme.palette.info.main, 0.15),
                        }}
                      >
                        <AttachMoney sx={{ fontSize: 32, color: 'info.main' }} />
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Fade>
            </Grid2>
          </Grid2>

          {/* Modern KPIs Section */}
          {kpis.length > 0 && (
            <Fade in timeout={1200}>
              <Paper
                sx={{
                  mb: 4,
                  p: 4,
                  borderRadius: 3,
                  background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.95) 100%)',
                  backdropFilter: 'blur(10px)',
                  border: '1px solid',
                  borderColor: alpha(theme.palette.primary.main, 0.1),
                  boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.08)}`,
                }}
              >
                <Box sx={{ mb: 3 }}>
                  <Typography
                    variant="h5"
                    gutterBottom
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      fontWeight: 700,
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      backgroundClip: 'text',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                    }}
                  >
                    <Analytics sx={{ mr: 2, color: 'primary.main' }} />
                    Indicadores Clave de Rendimiento
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Métricas esenciales para el monitoreo del desempeño empresarial
                  </Typography>
                </Box>

                <Grid2 container spacing={3}>
                  {kpis.slice(0, 6).map((kpi, index) => (
                    <Grid2 key={index} xs={12} sm={6} lg={4}>
                      <Card
                        sx={{
                          p: 3,
                          borderRadius: 2,
                          background: alpha(theme.palette.background.paper, 0.8),
                          border: '1px solid',
                          borderColor: alpha(theme.palette.divider, 0.8),
                          transition: 'all 0.3s ease',
                          '&:hover': {
                            transform: 'translateY(-2px)',
                            boxShadow: `0 8px 25px ${alpha(theme.palette.primary.main, 0.15)}`,
                            borderColor: alpha(theme.palette.primary.main, 0.3),
                          },
                        }}
                      >
                        <Box sx={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          justifyContent: 'space-between'
                        }}>
                          <Box sx={{ flex: 1 }}>
                            <Typography
                              variant="body2"
                              color="text.secondary"
                              sx={{ fontWeight: 500, mb: 1 }}
                            >
                              {kpi.nombre}
                            </Typography>
                            <Typography
                              variant="h5"
                              sx={{
                                fontWeight: 700,
                                mb: kpi.porcentaje_cambio !== undefined ? 1 : 0,
                                color: kpi.tendencia === 'positiva' ? 'success.main' :
                                       kpi.tendencia === 'negativa' ? 'error.main' : 'primary.main'
                              }}
                            >
                              {kpi.tipo === 'monetario'
                                ? dashboardService.formatCurrency(kpi.valor_actual)
                                : kpi.tipo === 'porcentaje'
                                ? dashboardService.formatPercentage(kpi.valor_actual)
                                : kpi.valor_actual.toLocaleString()
                              }
                            </Typography>
                            {kpi.porcentaje_cambio !== undefined && (
                              <Chip
                                label={`${kpi.porcentaje_cambio > 0 ? '+' : ''}${kpi.porcentaje_cambio.toFixed(1)}%`}
                                color={kpi.tendencia === 'positiva' ? 'success' :
                                       kpi.tendencia === 'negativa' ? 'error' : 'default'}
                                size="small"
                                variant="filled"
                                sx={{ borderRadius: 1, fontWeight: 500 }}
                              />
                            )}
                          </Box>
                          <Box
                            sx={{
                              p: 1.5,
                              borderRadius: 2,
                              background: alpha(
                                kpi.tendencia === 'positiva' ? theme.palette.success.main :
                                kpi.tendencia === 'negativa' ? theme.palette.error.main :
                                theme.palette.primary.main, 0.1
                              ),
                            }}
                          >
                            {getTendenciaIcon(kpi.tendencia)}
                          </Box>
                        </Box>
                      </Card>
                    </Grid2>
                  ))}
                </Grid2>
              </Paper>
            </Fade>
          )}

          {/* Modern Analytics Tabs */}
          <Fade in timeout={1400}>
            <Paper
              sx={{
                mb: 3,
                borderRadius: 3,
                background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.95) 100%)',
                backdropFilter: 'blur(10px)',
                border: '1px solid',
                borderColor: alpha(theme.palette.primary.main, 0.1),
                boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.08)}`,
                overflow: 'hidden',
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
                  Análisis de Rendimiento
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Visualizaciones detalladas del desempeño empresarial
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
                  label="Tendencias de Ventas"
                  icon={<ShowChart />}
                  iconPosition="start"
                  sx={{ mr: 1 }}
                />
                <Tab
                  label="Top Productos"
                  icon={<PieChart />}
                  iconPosition="start"
                  sx={{ mr: 1 }}
                />
                <Tab
                  label="Top Clientes"
                  icon={<BarChart />}
                  iconPosition="start"
                />
              </Tabs>

              <Box sx={{ p: 4 }}>
                {tabValue === 0 && (
                  <Box sx={{ minHeight: 400 }}>
                    <Fade in timeout={300}>
                      <Box>
                        {renderVentasChart()}
                      </Box>
                    </Fade>
                  </Box>
                )}
          
                {tabValue === 1 && (
                  <Box sx={{ minHeight: 400 }}>
                    <Fade in timeout={300}>
                      <Box>
                        {productosTop.length > 0 ? (
                          <Box>
                            <Box sx={{ mb: 3 }}>
                              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                                Top 5 Productos por Ingresos
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                Productos con mejor rendimiento en el período seleccionado
                              </Typography>
                            </Box>

                            <Grid2 container spacing={3}>
                              {productosTop.map((producto, index) => {
                                const maxIngresos = Math.max(...productosTop.map(p => p.ingresos_generados));
                                const porcentaje = (producto.ingresos_generados / maxIngresos) * 100;
                                const gradients = [
                                  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                                  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                                  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
                                  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
                                ];
                                const colors = ['#667eea', '#f5576c', '#4facfe', '#43e97b', '#fa709a'];

                                return (
                                  <Grid2 key={index} xs={12} lg={6}>
                                    <Card
                                      sx={{
                                        p: 3,
                                        borderRadius: 2,
                                        background: alpha(theme.palette.background.paper, 0.8),
                                        border: '1px solid',
                                        borderColor: alpha(colors[index % colors.length], 0.2),
                                        transition: 'all 0.3s ease',
                                        '&:hover': {
                                          transform: 'translateY(-2px)',
                                          boxShadow: `0 8px 25px ${alpha(colors[index % colors.length], 0.25)}`,
                                          borderColor: alpha(colors[index % colors.length], 0.4),
                                        },
                                      }}
                                    >
                                      <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                                        <Box
                                          sx={{
                                            width: 32,
                                            height: 32,
                                            background: gradients[index % gradients.length],
                                            borderRadius: 2,
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            mr: 2,
                                            flexShrink: 0,
                                          }}
                                        >
                                          <Typography
                                            variant="h6"
                                            sx={{ color: 'white', fontWeight: 700 }}
                                          >
                                            {index + 1}
                                          </Typography>
                                        </Box>
                                        <Box sx={{ flex: 1, minWidth: 0 }}>
                                          <Typography
                                            variant="subtitle1"
                                            sx={{
                                              fontWeight: 600,
                                              mb: 0.5,
                                              overflow: 'hidden',
                                              textOverflow: 'ellipsis',
                                              whiteSpace: 'nowrap',
                                            }}
                                          >
                                            {producto.nombre_producto}
                                          </Typography>
                                          <Typography variant="body2" color="text.secondary">
                                            SKU: {producto.sku}
                                          </Typography>
                                        </Box>
                                      </Box>

                                      <Stack spacing={2}>
                                        <Box>
                                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                            <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                                              Ingresos Generados
                                            </Typography>
                                            <Typography variant="h6" sx={{ fontWeight: 700, color: colors[index % colors.length] }}>
                                              {dashboardService.formatCurrency(producto.ingresos_generados)}
                                            </Typography>
                                          </Box>
                                          <LinearProgress
                                            variant="determinate"
                                            value={porcentaje}
                                            sx={{
                                              height: 8,
                                              borderRadius: 4,
                                              background: alpha(colors[index % colors.length], 0.1),
                                              '& .MuiLinearProgress-bar': {
                                                background: gradients[index % gradients.length],
                                                borderRadius: 4,
                                              }
                                            }}
                                          />
                                        </Box>

                                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                          <Box sx={{ textAlign: 'center' }}>
                                            <Typography variant="h6" sx={{ fontWeight: 700, color: 'text.primary' }}>
                                              {producto.cantidad_vendida}
                                            </Typography>
                                            <Typography variant="caption" color="text.secondary">
                                              Unidades Vendidas
                                            </Typography>
                                          </Box>
                                          <Box sx={{ textAlign: 'center' }}>
                                            <Typography variant="h6" sx={{ fontWeight: 700, color: 'success.main' }}>
                                              {dashboardService.formatPercentage(producto.margen_ganancia)}
                                            </Typography>
                                            <Typography variant="caption" color="text.secondary">
                                              Margen de Ganancia
                                            </Typography>
                                          </Box>
                                        </Box>
                                      </Stack>
                                    </Card>
                                  </Grid2>
                                );
                              })}
                            </Grid2>
                          </Box>
                        ) : (
                          <Box sx={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            height: '100%',
                            color: 'text.secondary'
                          }}>
                            <Typography>No hay datos de productos para mostrar</Typography>
                          </Box>
                        )}
                      </Box>
                    </Fade>
                  </Box>
                )}
          
                {tabValue === 2 && (
                  <Box sx={{ minHeight: 400 }}>
                    <Fade in timeout={300}>
                      <Box>
                        {clientesTop.length > 0 ? (
                          <Box>
                            <Box sx={{ mb: 3 }}>
                              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                                Top 5 Clientes por Compras
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                Clientes con mayor volumen de compras en el período
                              </Typography>
                            </Box>

                            <Grid2 container spacing={3}>
                              {clientesTop.map((cliente, index) => {
                                const maxCompras = Math.max(...clientesTop.map(c => c.total_compras));
                                const porcentaje = (cliente.total_compras / maxCompras) * 100;
                                const avatarColors = ['#667eea', '#f5576c', '#4facfe', '#43e97b', '#fa709a'];

                                return (
                                  <Grid2 key={index} xs={12} md={6}>
                                    <Card
                                      sx={{
                                        p: 3,
                                        borderRadius: 2,
                                        background: alpha(theme.palette.background.paper, 0.8),
                                        border: '1px solid',
                                        borderColor: alpha(theme.palette.divider, 0.5),
                                        transition: 'all 0.3s ease',
                                        '&:hover': {
                                          transform: 'translateY(-2px)',
                                          boxShadow: `0 8px 25px ${alpha(theme.palette.primary.main, 0.15)}`,
                                          borderColor: alpha(theme.palette.primary.main, 0.3),
                                        },
                                      }}
                                    >
                                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                        <Box
                                          sx={{
                                            width: 48,
                                            height: 48,
                                            borderRadius: '50%',
                                            background: avatarColors[index % avatarColors.length],
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            mr: 2,
                                          }}
                                        >
                                          <Group sx={{ color: 'white', fontSize: 24 }} />
                                        </Box>
                                        <Box sx={{ flex: 1, minWidth: 0 }}>
                                          <Typography
                                            variant="h6"
                                            sx={{
                                              fontWeight: 600,
                                              mb: 0.5,
                                              overflow: 'hidden',
                                              textOverflow: 'ellipsis',
                                              whiteSpace: 'nowrap',
                                            }}
                                          >
                                            #{index + 1} {cliente.nombre_cliente}
                                          </Typography>
                                          <Typography variant="body2" color="text.secondary">
                                            {cliente.numero_documento}
                                          </Typography>
                                        </Box>
                                      </Box>

                                      <Box sx={{ mb: 2 }}>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                          <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                                            Total Compras
                                          </Typography>
                                          <Typography variant="h6" sx={{ fontWeight: 700, color: 'primary.main' }}>
                                            {dashboardService.formatCurrency(cliente.total_compras)}
                                          </Typography>
                                        </Box>
                                        <LinearProgress
                                          variant="determinate"
                                          value={porcentaje}
                                          sx={{
                                            height: 6,
                                            borderRadius: 3,
                                            background: alpha(theme.palette.primary.main, 0.1),
                                            '& .MuiLinearProgress-bar': {
                                              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                              borderRadius: 3,
                                            }
                                          }}
                                        />
                                      </Box>

                                      <Stack direction="row" spacing={2}>
                                        <Box sx={{ textAlign: 'center', flex: 1 }}>
                                          <Typography variant="h6" sx={{ fontWeight: 700, color: 'text.primary' }}>
                                            {cliente.cantidad_facturas}
                                          </Typography>
                                          <Typography variant="caption" color="text.secondary">
                                            Facturas
                                          </Typography>
                                        </Box>
                                        <Box sx={{ textAlign: 'center', flex: 1 }}>
                                          <Typography variant="h6" sx={{ fontWeight: 700, color: 'success.main' }}>
                                            {dashboardService.formatCurrency(cliente.promedio_compra)}
                                          </Typography>
                                          <Typography variant="caption" color="text.secondary">
                                            Promedio por Compra
                                          </Typography>
                                        </Box>
                                      </Stack>
                                    </Card>
                                  </Grid2>
                                );
                              })}
                            </Grid2>
                          </Box>
                        ) : (
                          <Box sx={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            height: '100%',
                            color: 'text.secondary'
                          }}>
                            <Typography>No hay datos de clientes para mostrar</Typography>
                          </Box>
                        )}
                      </Box>
                    </Fade>
                  </Box>
                )}
              </Box>
            </Paper>
          </Fade>
        </Box>
      </Fade>
    </Container>
  );
};

export default DashboardPage;