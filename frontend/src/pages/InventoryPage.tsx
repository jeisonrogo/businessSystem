/**
 * Página de Gestión de Inventario - Modern Professional Interface
 * Dashboard principal para movimientos de inventario, kardex y estadísticas
 * Sistema de Gestión Empresarial
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  IconButton,
  Tooltip,
  Alert,
  Tabs,
  Tab,
  Chip,
  Fab,
  Container,
  alpha,
  useTheme,
  Fade,
  LinearProgress,
} from '@mui/material';
import {
  Add,
  TrendingUp,
  TrendingDown,
  ReportProblem,
  Tune,
  Refresh,
  Inventory2,
  Assessment,
  Receipt,
  Analytics,
  ShowChart,
  BarChart,
} from '@mui/icons-material';

import { InventoryService } from '../services/inventoryService';
import { ProductService } from '../services/productService';
import { InventorySummary, InventoryStats, MovementType } from '../types';
import InventoryMovementsList from '../components/inventory/InventoryMovementsList';
import KardexView from '../components/inventory/KardexView';
import MovementForm from '../components/inventory/MovementForm';
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
      id={`inventory-tabpanel-${index}`}
      aria-labelledby={`inventory-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ py: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const InventoryPage: React.FC = () => {
  const theme = useTheme();
  const { selectedLocal, selectedStore, isStoreManager } = useTenant();

  const [currentTab, setCurrentTab] = useState(0);
  const [summary, setSummary] = useState<InventorySummary | null>(null);
  const [, setStats] = useState<InventoryStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showMovementForm, setShowMovementForm] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [totalStock, setTotalStock] = useState(0);
  const [movimientosHoy, setMovimientosHoy] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  // Estadísticas por tipo de movimiento
  const [movementStats, setMovementStats] = useState<Record<MovementType, number>>({
    [MovementType.ENTRADA]: 0,
    [MovementType.SALIDA]: 0,
    [MovementType.MERMA]: 0,
    [MovementType.AJUSTE]: 0,
  });

  // Cargar datos iniciales
  useEffect(() => {
    loadInventoryData();
  }, [refreshTrigger]);

  const loadInventoryData = async (showRefreshing = false) => {
    if (showRefreshing) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);
    
    try {
      // Cargar resumen, estadísticas y productos en paralelo
      const [summaryResponse, statsResponse, , movementsResponse] = await Promise.all([
        InventoryService.getInventorySummary(),
        InventoryService.getInventoryStats(),
        ProductService.getProducts({ limit: 100 }),
        InventoryService.getMovements({ 
          limit: 100, 
          fecha_desde: new Date().toISOString().split('T')[0] // Solo hoy
        }),
      ]);

      setSummary(summaryResponse);
      setStats(statsResponse);

      // Usar el stock total del resumen que ya viene filtrado por local
      setTotalStock(summaryResponse.stock_total);

      // Contar movimientos de hoy
      setMovimientosHoy(movementsResponse.total);

      // Actualizar estadísticas por tipo de movimiento
      if (statsResponse) {
        setMovementStats({
          [MovementType.ENTRADA]: statsResponse.total_entradas_mes,
          [MovementType.SALIDA]: statsResponse.total_salidas_mes,
          [MovementType.MERMA]: statsResponse.total_mermas_mes,
          [MovementType.AJUSTE]: 0, // No disponible en estadísticas del mes
        });
      }
    } catch (err: any) {
      setError(err.message);
      console.error('Error loading inventory data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleCreateMovement = () => {
    setShowMovementForm(true);
  };

  const handleFormClose = () => {
    setShowMovementForm(false);
  };

  const handleMovementSaved = () => {
    setSuccess('Movimiento de inventario registrado exitosamente');
    setRefreshTrigger(prev => prev + 1);
    handleFormClose();
  };

  const handleRefresh = () => {
    loadInventoryData(true);
    setRefreshTrigger(prev => prev + 1);
  };

  const typeLabels = InventoryService.getMovementTypeLabels();

  const getMovementIcon = (type: MovementType) => {
    switch (type) {
      case MovementType.ENTRADA:
        return <TrendingUp />;
      case MovementType.SALIDA:
        return <TrendingDown />;
      case MovementType.MERMA:
        return <ReportProblem />;
      case MovementType.AJUSTE:
        return <Tune />;
      default:
        return <Assessment />;
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: `linear-gradient(135deg,
          ${alpha(theme.palette.primary.main, 0.05)} 0%,
          ${alpha(theme.palette.secondary.main, 0.05)} 50%,
          ${alpha(theme.palette.primary.main, 0.03)} 100%
        )`,
        py: 3,
      }}
    >
      <Container maxWidth="xl">
        <Fade in timeout={600}>
          <Box>
            {/* Modern Header Section */}
            <ModernCard variant="glass" sx={{ mb: 4, p: 4 }}>
              <Box sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                flexDirection: { xs: 'column', md: 'row' },
                gap: { xs: 2, md: 0 }
              }}>
                <Box sx={{ flex: 1 }}>
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
                    Gestión de Inventario
                  </Typography>
                  <Typography
                    variant="h6"
                    color="text.secondary"
                    sx={{
                      fontWeight: 500,
                      mb: 2,
                    }}
                  >
                    Control avanzado de movimientos, kardex y estadísticas de inventario
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
                        `📦 Local: ${selectedLocal.nombre} (${selectedLocal.codigo})`
                      ) : isStoreManager() && selectedStore ? (
                        `🏢 Todos los locales de ${selectedStore.nombre}`
                      ) : (
                        '⚠️ Sin contexto local seleccionado'
                      )}
                    </Typography>
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                  <Tooltip title="Actualizar datos" arrow>
                    <IconButton
                      onClick={handleRefresh}
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
              </Box>
            </ModernCard>

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

            {/* Modern Alerts */}
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

            {success && (
              <Fade in timeout={800}>
                <Alert
                  severity="success"
                  sx={{
                    mb: 3,
                    borderRadius: 3,
                    border: '1px solid',
                    borderColor: alpha(theme.palette.success.main, 0.2),
                    background: alpha(theme.palette.success.main, 0.05),
                    backdropFilter: 'blur(10px)',
                  }}
                  onClose={() => setSuccess(null)}
                >
                  {success}
                </Alert>
              </Fade>
            )}

            {/* Modern Statistics Cards */}
            {summary && (
              <Fade in timeout={1000}>
                <Grid container spacing={3} sx={{ mb: 4 }}>
                  <Grid item xs={12} sm={6} md={3}>
                    <ModernStatsCard
                      title="Total Productos"
                      value={summary.total_productos}
                      icon={Inventory2}
                      color="primary"
                      variant="gradient"
                      loading={loading}
                      trend={{
                        value: 3.2,
                        label: 'vs mes anterior',
                        direction: 'up'
                      }}
                      status={{
                        label: 'Activos',
                        color: 'success'
                      }}
                    />
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <ModernStatsCard
                      title="Stock Total"
                      value={totalStock}
                      subtitle="unidades"
                      icon={Assessment}
                      color="success"
                      variant="gradient"
                      loading={loading}
                      trend={{
                        value: 1.8,
                        label: 'vs semana anterior',
                        direction: 'up'
                      }}
                      status={{
                        label: 'Saludable',
                        color: 'success'
                      }}
                    />
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <ModernStatsCard
                      title="Valor Inventario"
                      value={InventoryService.formatCurrency(parseFloat(summary.valor_total_inventario))}
                      icon={Receipt}
                      color="info"
                      variant="gradient"
                      loading={loading}
                      trend={{
                        value: 5.7,
                        label: 'vs mes anterior',
                        direction: 'up'
                      }}
                      status={{
                        label: 'Óptimo',
                        color: 'success'
                      }}
                    />
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <ModernStatsCard
                      title="Movimientos Hoy"
                      value={movimientosHoy}
                      subtitle="operaciones"
                      icon={TrendingUp}
                      color="warning"
                      variant="gradient"
                      loading={loading}
                      status={movimientosHoy > 0 ? {
                        label: 'Activo',
                        color: 'success'
                      } : {
                        label: 'Sin actividad',
                        color: 'warning'
                      }}
                    />
                  </Grid>
                </Grid>
              </Fade>
            )}

            {/* Modern Movement Statistics */}
            <Fade in timeout={1200}>
              <ModernCard variant="glass" sx={{ mb: 4, p: 3 }}>
                <Box sx={{ mb: 3 }}>
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
                    <Analytics sx={{ color: 'primary.main' }} />
                    Estadísticas de Movimientos del Mes
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Resumen detallado de operaciones de inventario por categoría
                  </Typography>
                </Box>

                <Grid container spacing={3}>
                  {Object.entries(typeLabels).map(([type, label]) => {
                    const count = movementStats[type as MovementType];
                    const colors = {
                      [MovementType.ENTRADA]: theme.palette.success.main,
                      [MovementType.SALIDA]: theme.palette.error.main,
                      [MovementType.MERMA]: theme.palette.warning.main,
                      [MovementType.AJUSTE]: theme.palette.info.main,
                    };

                    return (
                      <Grid item xs={12} sm={6} md={3} key={type}>
                        <Card
                          sx={{
                            p: 2.5,
                            borderRadius: 2,
                            background: alpha(theme.palette.background.paper, 0.8),
                            border: '1px solid',
                            borderColor: alpha(colors[type as MovementType], 0.2),
                            borderLeft: `4px solid ${colors[type as MovementType]}`,
                            transition: 'all 0.3s ease',
                            '&:hover': {
                              transform: 'translateY(-2px)',
                              boxShadow: `0 8px 25px ${alpha(colors[type as MovementType], 0.2)}`,
                              borderColor: alpha(colors[type as MovementType], 0.4),
                            },
                          }}
                        >
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                            <Box>
                              <Typography
                                variant="h4"
                                sx={{
                                  fontWeight: 700,
                                  color: colors[type as MovementType],
                                  mb: 0.5,
                                }}
                              >
                                {count}
                              </Typography>
                              <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                                {label}s Este Mes
                              </Typography>
                            </Box>
                            <Box
                              sx={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                gap: 1,
                              }}
                            >
                              <Box
                                sx={{
                                  p: 1,
                                  borderRadius: '50%',
                                  background: alpha(colors[type as MovementType], 0.1),
                                  color: colors[type as MovementType],
                                }}
                              >
                                {getMovementIcon(type as MovementType)}
                              </Box>
                              <Chip
                                size="small"
                                label={type.toUpperCase()}
                                sx={{
                                  backgroundColor: alpha(colors[type as MovementType], 0.1),
                                  color: colors[type as MovementType],
                                  fontWeight: 700,
                                  fontSize: '0.7rem',
                                  border: `1px solid ${alpha(colors[type as MovementType], 0.3)}`,
                                }}
                              />
                            </Box>
                          </Box>
                        </Card>
                      </Grid>
                    );
                  })}
                </Grid>
              </ModernCard>
            </Fade>

            {/* Modern Content Tabs */}
            <Fade in timeout={1400}>
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
                    Análisis Detallado de Inventario
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Gestión completa de movimientos y trazabilidad por producto
                  </Typography>
                </Box>

                <Tabs
                  value={currentTab}
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
                    icon={<ShowChart />}
                    iconPosition="start"
                    label="Historial de Movimientos"
                    sx={{ mr: 1 }}
                  />
                  <Tab
                    icon={<BarChart />}
                    iconPosition="start"
                    label="Kardex por Producto"
                    sx={{ mr: 1 }}
                  />
                </Tabs>

                <Box sx={{ p: 4 }}>
                  <TabPanel value={currentTab} index={0}>
                    <Box sx={{ minHeight: 400 }}>
                      <Fade in timeout={300}>
                        <Box>
                          <InventoryMovementsList
                            onRefresh={handleRefresh}
                            loading={loading}
                          />
                        </Box>
                      </Fade>
                    </Box>
                  </TabPanel>

                  <TabPanel value={currentTab} index={1}>
                    <Box sx={{ minHeight: 400 }}>
                      <Fade in timeout={300}>
                        <Box>
                          <KardexView
                            loading={loading}
                            onRefresh={handleRefresh}
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
              aria-label="Crear movimiento de inventario"
              onClick={handleCreateMovement}
              disabled={!selectedLocal && !(isStoreManager() && selectedStore)}
              sx={{
                position: 'fixed',
                bottom: 24,
                right: 24,
                background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
                boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.3)}`,
                '&:hover': {
                  transform: 'scale(1.1)',
                  boxShadow: `0 12px 40px ${alpha(theme.palette.primary.main, 0.4)}`,
                },
                '&:disabled': {
                  background: alpha(theme.palette.action.disabled, 0.3),
                  boxShadow: 'none',
                },
                transition: 'all 0.3s ease',
              }}
            >
              <Add />
            </Fab>

            {/* Modern Movement Form Dialog */}
            {showMovementForm && (
              <MovementForm
                open={showMovementForm}
                onClose={handleFormClose}
                onSave={handleMovementSaved}
              />
            )}
          </Box>
        </Fade>
      </Container>
    </Box>
  );
};

export default InventoryPage;