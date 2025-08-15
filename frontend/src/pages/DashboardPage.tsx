/**
 * Página del Dashboard Principal
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Chip,
  Alert,
  Tabs,
  Tab,
  Skeleton,
  Divider,
  Button,
  IconButton,
  Tooltip,
  LinearProgress,
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
  Assessment,
  Refresh,
  BarChart,
  PieChart,
  Timeline,
  TrendingDown,
} from '@mui/icons-material';
// Importar types
import {
  MetricasRapidas,
  KPIDashboard,
  VentasPorPeriodo,
  ProductoTopVentas,
  ClienteTopVentas,
  AlertaDashboard,
  FiltrosDashboard,
  PeriodoReporte,
} from '../types';
import dashboardService from '../services/dashboardService';

const DashboardPage: React.FC = () => {
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
  const [periodo, setPeriodo] = useState<PeriodoReporte>(PeriodoReporte.MES);
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
  }, [periodo]);

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

  // Función para renderizar gráfico simple de barras con Material-UI
  const renderVentasChart = () => {
    if (ventasPorPeriodo.length === 0) {
      return (
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          height: '100%',
          color: 'text.secondary'
        }}>
          <Typography>No hay datos de ventas para mostrar</Typography>
        </Box>
      );
    }

    const maxVenta = Math.max(...ventasPorPeriodo.map(v => v.total_ventas));
    const maxFacturas = Math.max(...ventasPorPeriodo.map(v => v.cantidad_facturas));

    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          Tendencia de Ventas - Por Mes
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
          <Chip label="Ventas ($)" color="primary" size="small" />
          <Chip label="Cantidad Facturas" color="secondary" size="small" />
        </Box>
        <Grid2 container spacing={1}>
          {ventasPorPeriodo.slice(-10).map((venta, index) => (
            <Grid2 key={index} xs={12} md={6} lg={4}>
              <Card variant="outlined" sx={{ p: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  {venta.fecha.includes('2025') ? venta.fecha : new Date(venta.fecha).toLocaleDateString()}
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Box sx={{ width: '100%', mr: 1 }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={(venta.total_ventas / maxVenta) * 100}
                        color="primary"
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                    </Box>
                    <Typography variant="caption" sx={{ minWidth: 35 }}>
                      {dashboardService.formatCurrency(venta.total_ventas)}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Box sx={{ width: '100%', mr: 1 }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={(venta.cantidad_facturas / maxFacturas) * 100}
                        color="secondary"
                        sx={{ height: 6, borderRadius: 3 }}
                      />
                    </Box>
                    <Typography variant="caption" sx={{ minWidth: 35 }}>
                      {venta.cantidad_facturas} fact.
                    </Typography>
                  </Box>
                </Box>
              </Card>
            </Grid2>
          ))}
        </Grid2>
      </Box>
    );
  };

  if (loading) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 4 }}>
          Cargando datos del sistema...
        </Typography>
        
        <Grid2 container spacing={3}>
          {[...Array(4)].map((_, index) => (
            <Grid2 key={index} xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Skeleton variant="rectangular" height={60} />
                </CardContent>
              </Card>
            </Grid2>
          ))}
          
          <Grid2 xs={12}>
            <Paper sx={{ p: 3 }}>
              <Skeleton variant="rectangular" height={400} />
            </Paper>
          </Grid2>
        </Grid2>
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>
        
        <Alert 
          severity="error" 
          sx={{ mb: 3 }}
          action={
            <Button color="inherit" size="small" onClick={() => cargarDatos()}>
              Reintentar
            </Button>
          }
        >
          {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Dashboard Gerencial
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Sistema de Gestión Empresarial - Vista General
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Actualizar datos">
            <IconButton 
              onClick={handleRefresh} 
              disabled={refreshing}
              color="primary"
            >
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {refreshing && <LinearProgress sx={{ mb: 2 }} />}

      {/* Alertas */}
      {alertas.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
            <Warning sx={{ mr: 1, color: 'warning.main' }} />
            Alertas del Sistema
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {alertas.slice(0, 6).map((alerta, index) => (
              <Chip
                key={index}
                label={`${alerta.titulo}: ${alerta.cantidad}`}
                color={getCriticidadColor(alerta.criticidad) as any}
                variant="outlined"
                size="small"
              />
            ))}
          </Box>
        </Box>
      )}

      {/* Métricas Rápidas */}
      <Grid2 container spacing={3} sx={{ mb: 3 }}>
        <Grid2 xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Inventory sx={{ mr: 2, color: 'primary.main' }} />
                <Box>
                  <Typography color="text.secondary" variant="body2">
                    Total Productos
                  </Typography>
                  <Typography variant="h6">
                    {metricasRapidas?.total_productos?.toLocaleString() || '0'}
                  </Typography>
                  {(metricasRapidas?.productos_sin_stock || 0) > 0 && (
                    <Typography variant="caption" color="error.main">
                      {metricasRapidas?.productos_sin_stock} sin stock
                    </Typography>
                  )}
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid2>

        <Grid2 xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <People sx={{ mr: 2, color: 'success.main' }} />
                <Box>
                  <Typography color="text.secondary" variant="body2">
                    Total Clientes
                  </Typography>
                  <Typography variant="h6">
                    {metricasRapidas?.total_clientes?.toLocaleString() || '0'}
                  </Typography>
                  {(metricasRapidas?.clientes_nuevos_mes || 0) > 0 && (
                    <Typography variant="caption" color="success.main">
                      +{metricasRapidas?.clientes_nuevos_mes} este mes
                    </Typography>
                  )}
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid2>

        <Grid2 xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Receipt sx={{ mr: 2, color: 'warning.main' }} />
                <Box>
                  <Typography color="text.secondary" variant="body2">
                    Facturas Este Mes
                  </Typography>
                  <Typography variant="h6">
                    {metricasRapidas?.facturas_mes?.toLocaleString() || '0'}
                  </Typography>
                  {(metricasRapidas?.facturas_vencidas || 0) > 0 && (
                    <Typography variant="caption" color="error.main">
                      {metricasRapidas?.facturas_vencidas} vencidas
                    </Typography>
                  )}
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid2>

        <Grid2 xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <AttachMoney sx={{ mr: 2, color: 'info.main' }} />
                <Box>
                  <Typography color="text.secondary" variant="body2">
                    Valor Inventario
                  </Typography>
                  <Typography variant="h6">
                    {dashboardService.formatCurrency(metricasRapidas?.valor_inventario || 0)}
                  </Typography>
                  <Typography variant="caption" color="success.main">
                    Ventas hoy: {dashboardService.formatCurrency(metricasRapidas?.ventas_hoy || 0)}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid2>
      </Grid2>

      {/* KPIs */}
      {kpis.length > 0 && (
        <Paper sx={{ mb: 3, p: 2 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
            <Assessment sx={{ mr: 1, color: 'primary.main' }} />
            Indicadores Clave de Rendimiento (KPIs)
          </Typography>
          <Grid2 container spacing={2}>
            {kpis.slice(0, 6).map((kpi, index) => (
              <Grid2 key={index} xs={12} sm={6} md={4}>
                <Box sx={{ 
                  p: 2, 
                  border: 1, 
                  borderColor: 'divider', 
                  borderRadius: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      {kpi.nombre}
                    </Typography>
                    <Typography variant="h6">
                      {kpi.tipo === 'monetario' 
                        ? dashboardService.formatCurrency(kpi.valor_actual)
                        : kpi.tipo === 'porcentaje'
                        ? dashboardService.formatPercentage(kpi.valor_actual)
                        : kpi.valor_actual.toLocaleString()
                      }
                    </Typography>
                    {kpi.porcentaje_cambio !== undefined && (
                      <Typography 
                        variant="caption" 
                        color={kpi.tendencia === 'positiva' ? 'success.main' : 
                               kpi.tendencia === 'negativa' ? 'error.main' : 'text.secondary'}
                      >
                        {kpi.porcentaje_cambio > 0 ? '+' : ''}{kpi.porcentaje_cambio.toFixed(1)}%
                      </Typography>
                    )}
                  </Box>
                  {getTendenciaIcon(kpi.tendencia)}
                </Box>
              </Grid2>
            ))}
          </Grid2>
        </Paper>
      )}

      {/* Tabs para gráficos */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab label="Tendencias de Ventas" icon={<ShowChart />} />
          <Tab label="Top Productos" icon={<PieChart />} />
          <Tab label="Top Clientes" icon={<BarChart />} />
        </Tabs>
        
        <Box sx={{ p: 3 }}>
          {tabValue === 0 && (
            <Box sx={{ height: 400, overflowY: 'auto' }}>
              {renderVentasChart()}
            </Box>
          )}
          
          {tabValue === 1 && (
            <Box sx={{ height: 400, overflowY: 'auto' }}>
              {productosTop.length > 0 ? (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Top 5 Productos por Ingresos
                  </Typography>
                  <Grid2 container spacing={2}>
                    {productosTop.map((producto, index) => {
                      const maxIngresos = Math.max(...productosTop.map(p => p.ingresos_generados));
                      const porcentaje = (producto.ingresos_generados / maxIngresos) * 100;
                      const colors = ['#f44336', '#2196f3', '#ff9800', '#4caf50', '#9c27b0'];
                      
                      return (
                        <Grid2 key={index} xs={12} md={6}>
                          <Card variant="outlined" sx={{ p: 2 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                              <Box sx={{ 
                                width: 24, 
                                height: 24, 
                                backgroundColor: colors[index % colors.length],
                                borderRadius: '50%',
                                mr: 2
                              }} />
                              <Typography variant="subtitle1" sx={{ flex: 1 }}>
                                #{index + 1} {producto.nombre_producto.length > 30 
                                  ? producto.nombre_producto.substring(0, 30) + '...' 
                                  : producto.nombre_producto}
                              </Typography>
                            </Box>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              SKU: {producto.sku}
                            </Typography>
                            <Box sx={{ mt: 2 }}>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                <Typography variant="body2">Ingresos:</Typography>
                                <Typography variant="body2" fontWeight="bold">
                                  {dashboardService.formatCurrency(producto.ingresos_generados)}
                                </Typography>
                              </Box>
                              <LinearProgress 
                                variant="determinate" 
                                value={porcentaje}
                                sx={{ 
                                  height: 8, 
                                  borderRadius: 4,
                                  backgroundColor: 'grey.200',
                                  '& .MuiLinearProgress-bar': {
                                    backgroundColor: colors[index % colors.length]
                                  }
                                }}
                              />
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                                <Typography variant="caption">
                                  Cantidad: {producto.cantidad_vendida}
                                </Typography>
                                <Typography variant="caption">
                                  Margen: {dashboardService.formatPercentage(producto.margen_ganancia)}
                                </Typography>
                              </Box>
                            </Box>
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
          )}
          
          {tabValue === 2 && (
            <Box sx={{ height: 400 }}>
              {clientesTop.length > 0 ? (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Top 5 Clientes por Compras
                  </Typography>
                  <Grid2 container spacing={2}>
                    {clientesTop.map((cliente, index) => (
                      <Grid2 key={index} xs={12} md={6}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography variant="subtitle1" gutterBottom>
                              #{index + 1} {cliente.nombre_cliente}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Doc: {cliente.numero_documento}
                            </Typography>
                            <Divider sx={{ my: 1 }} />
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="body2">
                                Total Compras:
                              </Typography>
                              <Typography variant="body2" fontWeight="bold">
                                {dashboardService.formatCurrency(cliente.total_compras)}
                              </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="body2">
                                Facturas:
                              </Typography>
                              <Typography variant="body2">
                                {cliente.cantidad_facturas}
                              </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="body2">
                                Promedio:
                              </Typography>
                              <Typography variant="body2">
                                {dashboardService.formatCurrency(cliente.promedio_compra)}
                              </Typography>
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid2>
                    ))}
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
          )}
        </Box>
      </Paper>
    </Box>
  );
};

export default DashboardPage;