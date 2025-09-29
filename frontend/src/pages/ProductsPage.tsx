/**
 * Página de Gestión de Productos
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  Alert,
  Snackbar,
  Grid,
  Container,
  alpha,
  useTheme,
  Fab,
} from '@mui/material';
import {
  Add,
  Inventory,
  TrendingDown,
  AttachMoney,
  Warning,
  Refresh,
} from '@mui/icons-material';
import { GridPaginationModel } from '@mui/x-data-grid';

import { Product, ProductCreate, ProductUpdate } from '../types';
import { ProductService } from '../services/productService';
import ProductList from '../components/products/ProductList';
import ProductForm from '../components/products/ProductForm';
import ProductDetailDialog from '../components/products/ProductDetailDialog';
import ProductStockDialog from '../components/products/ProductStockDialog';
import { useTenant } from '../context/TenantContext';
import ModernCard from '../components/common/ModernCard';
import ModernStatsCard from '../components/common/ModernStatsCard';
import ModernSearchBar from '../components/common/ModernSearchBar';

const ProductsPage: React.FC = () => {
  // Contexto de tenant
  const { selectedLocal, selectedStore, isStoreManager } = useTenant();
  
  // Estados principales
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [totalCount, setTotalCount] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Estados de paginación
  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 25,
  });

  // Estados de diálogos
  const [formOpen, setFormOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [stockOpen, setStockOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState('');

  // Estados de notificaciones
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info' | 'warning';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  // Cargar productos con filtrado por contexto local
  const loadProducts = useCallback(async () => {
    setLoading(true);
    setError('');
    
    try {
      // Determinar parámetros basados en el contexto de tenant
      const params: any = {
        page: paginationModel.page + 1, // Backend usa páginas 1-based
        limit: paginationModel.pageSize,
        search: searchTerm || undefined,
        only_active: true,
      };

      // Implementar la lógica propuesta:
      // - Si hay local seleccionado, mostrar solo productos de ese local
      // - Si es administrador/gerente y no hay local específico, puede ver todos
      // - Si no hay contexto local válido, no mostrar productos
      if (selectedLocal) {
        params.local_id = selectedLocal.id;
      } else if (isStoreManager() && selectedStore) {
        // Permitir ver todos los locales si es administrador/gerente
        params.todos_los_locales = true;
      } else {
        // Sin contexto local válido, no cargar productos
        setProducts([]);
        setTotalCount(0);
        setError('Seleccione un local para ver los productos disponibles');
        return;
      }

      const response = await ProductService.getProducts(params);
      
      setProducts(response.items);
      setTotalCount(response.total);
      setError(''); // Limpiar cualquier error previo
    } catch (err: any) {
      console.error('Error al cargar productos:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Error al cargar productos';
      setError(errorMessage);
      setProducts([]);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  }, [paginationModel, searchTerm, selectedLocal, selectedStore, isStoreManager]);

  // Efectos
  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  // Debounce para búsqueda
  useEffect(() => {
    const timer = setTimeout(() => {
      if (paginationModel.page === 0) {
        loadProducts();
      } else {
        setPaginationModel(prev => ({ ...prev, page: 0 }));
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [searchTerm]); // eslint-disable-line react-hooks/exhaustive-deps

  // Handlers de eventos
  const handlePaginationChange = (model: GridPaginationModel) => {
    setPaginationModel(model);
  };

  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
  };

  const handleNewProduct = () => {
    setSelectedProduct(null);
    setFormError('');
    setFormOpen(true);
  };

  const handleEditProduct = (product: Product) => {
    setSelectedProduct(product);
    setFormError('');
    setFormOpen(true);
  };

  const handleViewDetails = (product: Product) => {
    setSelectedProduct(product);
    setDetailOpen(true);
  };

  const handleUpdateStock = (product: Product) => {
    setSelectedProduct(product);
    setStockOpen(true);
  };

  const handleDeleteProduct = async (product: Product) => {
    if (!window.confirm(`¿Estás seguro de eliminar el producto "${product.nombre}"?`)) {
      return;
    }

    try {
      await ProductService.deleteProduct(product.id);
      showSnackbar('Producto eliminado exitosamente', 'success');
      loadProducts();
    } catch (err: any) {
      console.error('Error al eliminar producto:', err);
      showSnackbar(
        err.response?.data?.detail || 'Error al eliminar producto',
        'error'
      );
    }
  };

  const handleSaveProduct = async (productData: ProductCreate | ProductUpdate) => {
    setFormLoading(true);
    setFormError('');

    try {
      if (selectedProduct) {
        // Editar producto existente
        await ProductService.updateProduct(selectedProduct.id, productData as ProductUpdate);
        showSnackbar('Producto actualizado exitosamente', 'success');
      } else {
        // Crear nuevo producto
        await ProductService.createProduct(productData as ProductCreate);
        showSnackbar('Producto creado exitosamente', 'success');
      }
      
      setFormOpen(false);
      loadProducts();
    } catch (err: any) {
      console.error('Error al guardar producto:', err);
      
      // El error ya viene procesado por handleApiError en ProductService
      const errorMessage = err.message || 'Error al guardar producto';
      setFormError(errorMessage);
      
      // También mostramos el error en un snackbar para mayor visibilidad
      showSnackbar(errorMessage, 'error');
    } finally {
      setFormLoading(false);
    }
  };

  const handleSaveStock = async (newStock: number) => {
    if (!selectedProduct) return;

    // Verificar que hay un local seleccionado
    if (!selectedLocal) {
      showSnackbar('Se requiere seleccionar un local para actualizar stock', 'error');
      return;
    }

    try {
      await ProductService.updateStock(selectedProduct.id, newStock, selectedLocal.id);
      showSnackbar('Stock actualizado exitosamente', 'success');
      setStockOpen(false);
      loadProducts();
    } catch (err: any) {
      console.error('Error al actualizar stock:', err);
      
      // El error ya viene procesado por handleApiError
      const errorMessage = err.message || 'Error al actualizar stock';
      showSnackbar(errorMessage, 'error');
      
      // Re-lanzamos el error para que el diálogo de stock lo pueda manejar
      throw new Error(errorMessage);
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info' | 'warning') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  // Calcular estadísticas
  const lowStockCount = products.filter(p => (p.stock_local_actual ?? 0) <= 10).length;
  const totalValue = products.reduce((sum, p) => sum + (p.precio_publico * (p.stock_local_actual ?? 0)), 0);
  const outOfStockCount = products.filter(p => (p.stock_local_actual ?? 0) === 0).length;

  const theme = useTheme();

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
      {/* Encabezado moderno */}
      <ModernCard variant="glass" sx={{ mb: 4, p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box sx={{ flex: 1 }}>
            <Typography
              variant="h3"
              component="h1"
              sx={{
                fontWeight: 700,
                background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                mb: 1,
              }}
            >
              Gestión de Productos
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ mb: 2, fontWeight: 400 }}>
              Administra tu catálogo de productos de manera profesional
            </Typography>

            {/* Indicador de contexto local moderno */}
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
                  `📍 Local: ${selectedLocal.nombre} (${selectedLocal.codigo})`
                ) : isStoreManager() && selectedStore ? (
                  `🏢 Todos los locales de ${selectedStore.nombre}`
                ) : (
                  '⚠️ Sin contexto local seleccionado'
                )}
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
            <Button
              variant="contained"
              startIcon={<Add />}
              size="large"
              onClick={handleNewProduct}
              disabled={!selectedLocal && !(isStoreManager() && selectedStore)}
              sx={{
                borderRadius: 2,
                px: 3,
                py: 1.5,
                background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
                boxShadow: `0 4px 16px ${alpha(theme.palette.primary.main, 0.3)}`,
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: `0 6px 20px ${alpha(theme.palette.primary.main, 0.4)}`,
                },
                '&:disabled': {
                  background: alpha(theme.palette.action.disabled, 0.3),
                  boxShadow: 'none',
                },
              }}
            >
              Nuevo Producto
            </Button>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={loadProducts}
              disabled={loading}
              sx={{
                borderRadius: 2,
                borderColor: alpha(theme.palette.primary.main, 0.3),
                color: 'primary.main',
                '&:hover': {
                  backgroundColor: alpha(theme.palette.primary.main, 0.1),
                  borderColor: theme.palette.primary.main,
                  transform: 'translateY(-1px)',
                },
              }}
            >
              Actualizar
            </Button>
          </Box>
        </Box>
      </ModernCard>

      {/* Estadísticas modernas */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <ModernStatsCard
            title="Total Productos"
            value={totalCount}
            icon={Inventory}
            color="primary"
            variant="gradient"
            loading={loading}
            trend={{
              value: 5.2,
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
            title="Stock Bajo"
            value={lowStockCount}
            subtitle="≤ 10 unidades"
            icon={Warning}
            color="warning"
            variant="gradient"
            loading={loading}
            status={lowStockCount > 0 ? {
              label: 'Atención Requerida',
              color: 'warning'
            } : {
              label: 'Normal',
              color: 'success'
            }}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <ModernStatsCard
            title="Sin Stock"
            value={outOfStockCount}
            subtitle="0 unidades"
            icon={TrendingDown}
            color="error"
            variant="gradient"
            loading={loading}
            status={outOfStockCount > 0 ? {
              label: 'Crítico',
              color: 'error'
            } : {
              label: 'Normal',
              color: 'success'
            }}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <ModernStatsCard
            title="Valor Inventario"
            value={new Intl.NumberFormat('es-CO', {
              style: 'currency',
              currency: 'COP',
              minimumFractionDigits: 0,
              maximumFractionDigits: 0,
            }).format(totalValue)}
            icon={AttachMoney}
            color="success"
            variant="gradient"
            loading={loading}
            trend={{
              value: 12.5,
              label: 'vs mes anterior',
              direction: 'up'
            }}
            status={{
              label: 'Saludable',
              color: 'success'
            }}
          />
        </Grid>
      </Grid>

      {/* Barra de búsqueda moderna */}
      <Box sx={{ mb: 4 }}>
        <ModernSearchBar
          value={searchTerm}
          onChange={handleSearchChange}
          placeholder="Buscar productos por nombre, SKU o descripción..."
          debounceMs={500}
          sortOptions={[
            { value: 'nombre_asc', label: 'Nombre A-Z' },
            { value: 'nombre_desc', label: 'Nombre Z-A' },
            { value: 'precio_asc', label: 'Precio menor' },
            { value: 'precio_desc', label: 'Precio mayor' },
            { value: 'stock_asc', label: 'Stock menor' },
            { value: 'stock_desc', label: 'Stock mayor' },
          ]}
          filters={[
            { key: 'low_stock', label: 'Stock Bajo', value: true },
            { key: 'no_stock', label: 'Sin Stock', value: true },
            { key: 'active_only', label: 'Solo Activos', value: true },
          ]}
          disabled={loading}
        />
      </Box>

      {/* Lista de productos moderna */}
      <ModernCard variant="glass" sx={{ mb: 4 }}>
        <ProductList
          products={products}
          loading={loading}
          error={error}
          totalCount={totalCount}
          paginationModel={paginationModel}
          onPaginationModelChange={handlePaginationChange}
          onEdit={handleEditProduct}
          onDelete={handleDeleteProduct}
          onViewDetails={handleViewDetails}
          onUpdateStock={handleUpdateStock}
        />
      </ModernCard>

      {/* Diálogos */}
      <ProductForm
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSave={handleSaveProduct}
        product={selectedProduct}
        loading={formLoading}
        error={formError}
      />

      <ProductDetailDialog
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        onEdit={handleEditProduct}
        product={selectedProduct}
      />

      <ProductStockDialog
        open={stockOpen}
        onClose={() => setStockOpen(false)}
        onUpdateStock={handleSaveStock}
        product={selectedProduct}
      />

      {/* Floating Action Button moderno */}
      <Fab
        color="primary"
        aria-label="Nuevo producto"
        onClick={handleNewProduct}
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

      {/* Notificaciones modernas */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          sx={{
            width: '100%',
            borderRadius: 2,
            backdropFilter: 'blur(10px)',
            boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.15)}`,
          }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
      </Container>
    </Box>
  );
};

export default ProductsPage;