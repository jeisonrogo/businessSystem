/**
 * Página de Gestión de Inventario
 * Dashboard principal para movimientos de inventario, kardex y estadísticas
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  Alert,
  Tabs,
  Tab,
  Chip,
  Fab,
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
} from '@mui/icons-material';

import { InventoryService } from '../services/inventoryService';
import { ProductService } from '../services/productService';
import { InventorySummary, InventoryStats, MovementType } from '../types';
import InventoryMovementsList from '../components/inventory/InventoryMovementsList';
import KardexView from '../components/inventory/KardexView';
import MovementForm from '../components/inventory/MovementForm';

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

  const loadInventoryData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Cargar resumen, estadísticas y productos en paralelo
      const [summaryResponse, statsResponse, productsResponse, movementsResponse] = await Promise.all([
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

      // Calcular total de stock de todos los productos
      const totalStockCalculated = productsResponse.items.reduce((sum, product) => sum + product.stock, 0);
      setTotalStock(totalStockCalculated);

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
    setRefreshTrigger(prev => prev + 1);
  };

  const typeLabels = InventoryService.getMovementTypeLabels();
  const typeColors = InventoryService.getMovementTypeColors();

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
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Gestión de Inventario
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Control de movimientos, kardex y estadísticas de inventario
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Refrescar datos">
            <span>
              <IconButton onClick={handleRefresh} disabled={loading}>
                <Refresh />
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </Box>

      {/* Alertas */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Resumen de inventario */}
      {summary && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" component="div" color="primary">
                      {summary.total_productos}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Productos Totales
                    </Typography>
                  </Box>
                  <Inventory2 sx={{ fontSize: 40, color: 'primary.main', opacity: 0.7 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" component="div" color="success.main">
                      {totalStock}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Stock Total
                    </Typography>
                  </Box>
                  <Assessment sx={{ fontSize: 40, color: 'success.main', opacity: 0.7 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" component="div" color="info.main">
                      {InventoryService.formatCurrency(parseFloat(summary.valor_total_inventario))}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Valor Inventario
                    </Typography>
                  </Box>
                  <Receipt sx={{ fontSize: 40, color: 'info.main', opacity: 0.7 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" component="div" color="warning.main">
                      {movimientosHoy}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Movimientos Hoy
                    </Typography>
                  </Box>
                  <TrendingUp sx={{ fontSize: 40, color: 'warning.main', opacity: 0.7 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Estadísticas por tipo de movimiento */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {Object.entries(typeLabels).map(([type, label]) => (
          <Grid item xs={12} sm={6} md={3} key={type}>
            <Card>
              <CardContent sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h6" component="div">
                      {movementStats[type as MovementType]}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {label}s
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5 }}>
                    {getMovementIcon(type as MovementType)}
                    <Chip
                      size="small"
                      label={type.toUpperCase()}
                      sx={{
                        backgroundColor: typeColors[type as MovementType] + '20',
                        color: typeColors[type as MovementType],
                        fontWeight: 'bold',
                        fontSize: '0.7rem',
                      }}
                    />
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Contenido principal */}
      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={currentTab} onChange={handleTabChange}>
            <Tab 
              icon={<Assessment />} 
              iconPosition="start" 
              label="Movimientos" 
            />
            <Tab 
              icon={<Receipt />} 
              iconPosition="start" 
              label="Kardex por Producto" 
            />
          </Tabs>
        </Box>

        <TabPanel value={currentTab} index={0}>
          <InventoryMovementsList
            onRefresh={handleRefresh}
            loading={loading}
          />
        </TabPanel>

        <TabPanel value={currentTab} index={1}>
          <KardexView
            loading={loading}
            onRefresh={handleRefresh}
          />
        </TabPanel>
      </Paper>

      {/* FAB para crear movimiento */}
      <Fab
        color="primary"
        aria-label="Crear movimiento"
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
        }}
        onClick={handleCreateMovement}
      >
        <Add />
      </Fab>

      {/* Formulario de movimiento */}
      {showMovementForm && (
        <MovementForm
          open={showMovementForm}
          onClose={handleFormClose}
          onSave={handleMovementSaved}
        />
      )}
    </Box>
  );
};

export default InventoryPage;