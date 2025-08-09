/**
 * Vista de Kardex por Producto
 * Componente para mostrar el kardex detallado de un producto específico
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  Card,
  CardContent,
  Grid,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Autocomplete,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Search,
  Refresh,
  Assessment,
  TrendingUp,
  TrendingDown,
  ReportProblem,
  Tune,
  Print,
  GetApp,
} from '@mui/icons-material';

import { ProductService } from '../../services/productService';
import { InventoryService } from '../../services/inventoryService';
import {
  Product,
  KardexResponse,
  MovementType,
} from '../../types';
import { exportKardexToCSV, printKardex } from '../../utils/exportUtils';

interface KardexViewProps {
  loading?: boolean;
  onRefresh?: () => void;
}

const KardexView: React.FC<KardexViewProps> = ({
  loading: externalLoading = false,
  onRefresh,
}) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [kardex, setKardex] = useState<KardexResponse | null>(null);
  const [kardexProduct, setKardexProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(false);
  const [productsLoading, setProductsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Cargar productos al montar el componente
  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    setProductsLoading(true);
    try {
      const response = await ProductService.getProducts({ 
        limit: 100, 
        only_active: true 
      });
      setProducts(response.items);
    } catch (err: any) {
      setError('Error al cargar productos: ' + err.message);
    } finally {
      setProductsLoading(false);
    }
  };

  const loadKardex = async (productId: string) => {
    setLoading(true);
    setError(null);
    
    try {
      // Cargar kardex y detalles del producto en paralelo
      const [kardexData, productData] = await Promise.all([
        InventoryService.getKardex(productId),
        ProductService.getProductById(productId),
      ]);
      
      setKardex(kardexData);
      setKardexProduct(productData);
    } catch (err: any) {
      setError(err.message);
      setKardex(null);
      setKardexProduct(null);
    } finally {
      setLoading(false);
    }
  };

  const handleProductSelect = (product: Product | null) => {
    setSelectedProduct(product);
    if (product) {
      loadKardex(product.id);
    } else {
      setKardex(null);
    }
  };

  const handleRefresh = () => {
    if (selectedProduct) {
      loadKardex(selectedProduct.id);
    }
    onRefresh?.();
  };

  const getMovementIcon = (type: MovementType) => {
    switch (type) {
      case MovementType.ENTRADA:
        return <TrendingUp fontSize="small" />;
      case MovementType.SALIDA:
        return <TrendingDown fontSize="small" />;
      case MovementType.MERMA:
        return <ReportProblem fontSize="small" />;
      case MovementType.AJUSTE:
        return <Tune fontSize="small" />;
      default:
        return <Assessment fontSize="small" />;
    }
  };

  const typeLabels = InventoryService.getMovementTypeLabels();
  const typeColors = InventoryService.getMovementTypeColors();

  const formatCurrency = (value: number) => {
    return InventoryService.formatCurrency(value);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-CO', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6" component="h2">
          Kardex por Producto
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Refrescar">
            <span>
              <IconButton 
                onClick={handleRefresh} 
                disabled={loading || externalLoading || !selectedProduct}
              >
                <Refresh />
              </IconButton>
            </span>
          </Tooltip>
          
          {kardex && kardexProduct && (
            <>
              <Tooltip title="Imprimir kardex">
                <span>
                  <IconButton 
                    onClick={() => printKardex(kardex, kardexProduct)}
                    disabled={loading}
                  >
                    <Print />
                  </IconButton>
                </span>
              </Tooltip>
              
              <Tooltip title="Exportar a CSV">
                <span>
                  <IconButton 
                    onClick={() => exportKardexToCSV(kardex, kardexProduct)}
                    disabled={loading}
                  >
                    <GetApp />
                  </IconButton>
                </span>
              </Tooltip>
            </>
          )}
        </Box>
      </Box>

      {/* Selector de producto */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={8}>
            <Autocomplete
              options={products}
              getOptionLabel={(option) => `${option.sku} - ${option.nombre}`}
              value={selectedProduct}
              onChange={(_, value) => handleProductSelect(value)}
              loading={productsLoading}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Seleccionar Producto"
                  variant="outlined"
                  InputProps={{
                    ...params.InputProps,
                    startAdornment: <Search sx={{ color: 'action.active', mr: 1 }} />,
                    endAdornment: (
                      <>
                        {productsLoading ? <CircularProgress size={20} /> : null}
                        {params.InputProps.endAdornment}
                      </>
                    ),
                  }}
                />
              )}
              renderOption={(props, option) => (
                <li {...props}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                    <Typography variant="body2">
                      <strong>{option.sku}</strong> - {option.nombre}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Stock: {option.stock} | Precio: {formatCurrency(option.precio_publico)}
                    </Typography>
                  </Box>
                </li>
              )}
            />
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Button
              variant="contained"
              startIcon={<Search />}
              onClick={() => selectedProduct && loadKardex(selectedProduct.id)}
              disabled={!selectedProduct || loading}
              fullWidth
            >
              {loading ? 'Cargando...' : 'Consultar Kardex'}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Información del producto y resumen */}
      {kardex && kardexProduct && (
        <>
          {/* Info del producto */}
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              {kardexProduct.nombre}
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  SKU
                </Typography>
                <Typography variant="body1" fontWeight="bold">
                  {kardexProduct.sku}
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Stock Actual
                </Typography>
                <Typography variant="h6" color="primary">
                  {kardex.stock_actual}
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Costo Promedio
                </Typography>
                <Typography variant="body1" fontWeight="bold">
                  {formatCurrency(parseFloat(kardex.costo_promedio_actual))}
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Valor Total
                </Typography>
                <Typography variant="h6" color="success.main">
                  {formatCurrency(parseFloat(kardex.valor_inventario))}
                </Typography>
              </Grid>
            </Grid>
          </Paper>

          {/* Estadísticas de movimientos calculadas */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center', p: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                    <TrendingUp sx={{ color: 'success.main', mr: 1 }} />
                    <Typography variant="h6" color="success.main">
                      {kardex.movimientos.filter(m => m.tipo_movimiento === MovementType.ENTRADA).length}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Entradas
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center', p: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                    <TrendingDown sx={{ color: 'error.main', mr: 1 }} />
                    <Typography variant="h6" color="error.main">
                      {kardex.movimientos.filter(m => m.tipo_movimiento === MovementType.SALIDA).length}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Salidas
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center', p: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                    <ReportProblem sx={{ color: 'warning.main', mr: 1 }} />
                    <Typography variant="h6" color="warning.main">
                      {kardex.movimientos.filter(m => m.tipo_movimiento === MovementType.MERMA).length}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Mermas
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center', p: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                    <Tune sx={{ color: 'info.main', mr: 1 }} />
                    <Typography variant="h6" color="info.main">
                      {kardex.movimientos.filter(m => m.tipo_movimiento === MovementType.AJUSTE).length}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Ajustes
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Tabla de movimientos */}
          <Paper>
            <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
              <Typography variant="h6">
                Movimientos del Producto ({kardex.total_movimientos})
              </Typography>
            </Box>
            
            <TableContainer sx={{ maxHeight: 600 }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Fecha</TableCell>
                    <TableCell>Tipo</TableCell>
                    <TableCell align="right">Cantidad</TableCell>
                    <TableCell align="right">Precio Unit.</TableCell>
                    <TableCell align="right">Costo Unit.</TableCell>
                    <TableCell align="right">Stock Ant.</TableCell>
                    <TableCell align="right">Stock Post.</TableCell>
                    <TableCell>Referencia</TableCell>
                    <TableCell>Observaciones</TableCell>
                  </TableRow>
                </TableHead>
                
                <TableBody>
                  {kardex.movimientos.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} align="center" sx={{ py: 4 }}>
                        <Typography variant="body2" color="text.secondary">
                          No hay movimientos registrados para este producto
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    kardex.movimientos.map((movement, index) => (
                      <TableRow key={movement.id || index} hover>
                        <TableCell>
                          <Typography variant="body2">
                            {formatDate(movement.created_at)}
                          </Typography>
                        </TableCell>
                        
                        <TableCell>
                          <Chip
                            icon={getMovementIcon(movement.tipo_movimiento)}
                            label={typeLabels[movement.tipo_movimiento]}
                            size="small"
                            sx={{
                              backgroundColor: typeColors[movement.tipo_movimiento] + '20',
                              color: typeColors[movement.tipo_movimiento],
                              fontWeight: 'bold',
                              '& .MuiChip-icon': {
                                color: typeColors[movement.tipo_movimiento],
                              },
                            }}
                          />
                        </TableCell>
                        
                        <TableCell align="right">
                          <Typography 
                            variant="body2" 
                            sx={{
                              fontWeight: 'bold',
                              color: movement.tipo_movimiento === MovementType.ENTRADA || movement.tipo_movimiento === MovementType.AJUSTE
                                ? 'success.main'
                                : 'error.main',
                            }}
                          >
                            {InventoryService.formatQuantityWithSign(
                              movement.tipo_movimiento,
                              movement.cantidad
                            )}
                          </Typography>
                        </TableCell>
                        
                        <TableCell align="right">
                          {movement.precio_unitario 
                            ? formatCurrency(parseFloat(movement.precio_unitario.toString()))
                            : '-'
                          }
                        </TableCell>
                        
                        <TableCell align="right">
                          {movement.costo_unitario 
                            ? formatCurrency(parseFloat(movement.costo_unitario.toString()))
                            : '-'
                          }
                        </TableCell>
                        
                        <TableCell align="right">
                          {movement.stock_anterior}
                        </TableCell>
                        
                        <TableCell align="right">
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                            {movement.stock_posterior}
                          </Typography>
                        </TableCell>
                        
                        <TableCell>
                          <Typography variant="body2">
                            {movement.referencia || '-'}
                          </Typography>
                        </TableCell>
                        
                        <TableCell>
                          <Tooltip title={movement.observaciones || ''} arrow>
                            <Typography
                              variant="body2"
                              sx={{
                                maxWidth: 150,
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                              }}
                            >
                              {movement.observaciones || '-'}
                            </Typography>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </>
      )}

      {/* Estado vacío */}
      {!selectedProduct && !loading && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Assessment sx={{ fontSize: 60, color: 'action.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Selecciona un producto
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Busca y selecciona un producto para ver su kardex detallado
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default KardexView;