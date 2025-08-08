/**
 * Página de Gestión de Productos
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  TextField,
  InputAdornment,
  Alert,
  Snackbar,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import {
  Add,
  Search,
  Inventory,
  TrendingDown,
  AttachMoney,
} from '@mui/icons-material';
import { GridPaginationModel } from '@mui/x-data-grid';

import { Product, ProductCreate, ProductUpdate } from '../types';
import { ProductService } from '../services/productService';
import ProductList from '../components/products/ProductList';
import ProductForm from '../components/products/ProductForm';
import ProductDetailDialog from '../components/products/ProductDetailDialog';
import ProductStockDialog from '../components/products/ProductStockDialog';

const ProductsPage: React.FC = () => {
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

  // Cargar productos
  const loadProducts = useCallback(async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await ProductService.getProducts({
        page: paginationModel.page + 1, // Backend usa páginas 1-based
        limit: paginationModel.pageSize,
        search: searchTerm || undefined,
        only_active: true,
      });
      
      setProducts(response.items);
      setTotalCount(response.total);
    } catch (err: any) {
      console.error('Error al cargar productos:', err);
      setError(err.response?.data?.detail || 'Error al cargar productos');
    } finally {
      setLoading(false);
    }
  }, [paginationModel, searchTerm]);

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
  }, [searchTerm]);

  // Handlers de eventos
  const handlePaginationChange = (model: GridPaginationModel) => {
    setPaginationModel(model);
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
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
      const errorMessage = err.response?.data?.detail || 'Error al guardar producto';
      setFormError(errorMessage);
    } finally {
      setFormLoading(false);
    }
  };

  const handleSaveStock = async (newStock: number) => {
    if (!selectedProduct) return;

    try {
      await ProductService.updateStock(selectedProduct.id, newStock);
      showSnackbar('Stock actualizado exitosamente', 'success');
      setStockOpen(false);
      loadProducts();
    } catch (err: any) {
      console.error('Error al actualizar stock:', err);
      throw new Error(err.response?.data?.detail || 'Error al actualizar stock');
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info' | 'warning') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  // Calcular estadísticas
  const lowStockCount = products.filter(p => p.stock <= 10).length;
  const totalValue = products.reduce((sum, p) => sum + (p.precio_publico * p.stock), 0);
  const outOfStockCount = products.filter(p => p.stock === 0).length;

  return (
    <Box>
      {/* Encabezado */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Gestión de Productos
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Administra tu catálogo de productos
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Add />}
          size="large"
          onClick={handleNewProduct}
        >
          Nuevo Producto
        </Button>
      </Box>

      {/* Estadísticas */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Inventory color="primary" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h6">{totalCount}</Typography>
              <Typography variant="body2" color="text.secondary">
                Total Productos
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <TrendingDown color="warning" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h6">{lowStockCount}</Typography>
              <Typography variant="body2" color="text.secondary">
                Stock Bajo
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <TrendingDown color="error" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h6">{outOfStockCount}</Typography>
              <Typography variant="body2" color="text.secondary">
                Sin Stock
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <AttachMoney color="success" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h6">
                {new Intl.NumberFormat('es-CO', {
                  style: 'currency',
                  currency: 'COP',
                  minimumFractionDigits: 0,
                  maximumFractionDigits: 0,
                }).format(totalValue)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Valor Inventario
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Barra de búsqueda */}
      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Buscar productos por nombre o SKU..."
          value={searchTerm}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search />
              </InputAdornment>
            ),
          }}
        />
      </Box>

      {/* Lista de productos */}
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

      {/* Notificaciones */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ProductsPage;