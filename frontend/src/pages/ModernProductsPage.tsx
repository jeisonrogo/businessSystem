/**
 * Modern Products Page - Professional Business Management Interface
 * Sistema de Gestión Empresarial
 */

import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  TextField,
  InputAdornment,
  Fade,
  Alert,
  Chip,
  Stack,
  Typography,
} from '@mui/material';
import Grid2 from '@mui/material/Unstable_Grid2';
import {
  Search,
  Add,
  FilterList,
  Inventory,
  AttachMoney,
  TrendingDown,
  LocalOffer,
  Download,
  Analytics,
} from '@mui/icons-material';

// Import modern components
import {
  PageHeader,
  ModernCard,
  StatCard,
  ModernButton,
  LoadingSpinner,
  MetricCard,
} from '../components/common';

interface ProductStats {
  totalProducts: number;
  lowStockProducts: number;
  totalValue: number;
  averagePrice: number;
  topCategory: string;
  monthlyGrowth: number;
}

interface ProductData {
  id: string;
  name: string;
  sku: string;
  price: number;
  stock: number;
  category: string;
  status: 'active' | 'inactive' | 'low_stock';
  lastSale?: string;
}

const ModernProductsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [products, setProducts] = useState<ProductData[]>([]);
  const [stats, setStats] = useState<ProductStats>({
    totalProducts: 0,
    lowStockProducts: 0,
    totalValue: 0,
    averagePrice: 0,
    topCategory: '',
    monthlyGrowth: 0,
  });

  const categories = ['Todos', 'Electrónicos', 'Ropa', 'Hogar', 'Libros', 'Deportes'];

  // Sample data - In real app, this would come from API
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Sample stats data
      setStats({
        totalProducts: 1247,
        lowStockProducts: 23,
        totalValue: 8750000,
        averagePrice: 125000,
        topCategory: 'Electrónicos',
        monthlyGrowth: 12.5,
      });

      // Sample products data
      const sampleProducts: ProductData[] = [
        {
          id: '1',
          name: 'Smartphone Samsung Galaxy S24',
          sku: 'SAM-S24-128',
          price: 2800000,
          stock: 15,
          category: 'Electrónicos',
          status: 'active',
          lastSale: '2025-01-15',
        },
        {
          id: '2',
          name: 'Laptop HP Pavilion 15"',
          sku: 'HP-PAV-15',
          price: 3200000,
          stock: 3,
          category: 'Electrónicos',
          status: 'low_stock',
          lastSale: '2025-01-14',
        },
        {
          id: '3',
          name: 'Camiseta Nike Dri-Fit',
          sku: 'NK-DF-001',
          price: 89000,
          stock: 45,
          category: 'Ropa',
          status: 'active',
          lastSale: '2025-01-16',
        },
        {
          id: '4',
          name: 'Mesa de Centro Madera',
          sku: 'MC-MAD-001',
          price: 450000,
          stock: 8,
          category: 'Hogar',
          status: 'active',
          lastSale: '2025-01-12',
        },
      ];

      setProducts(sampleProducts);
      setLoading(false);
    };

    loadData();
  }, []);

  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'low_stock':
        return 'warning';
      case 'inactive':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'active':
        return 'Activo';
      case 'low_stock':
        return 'Stock Bajo';
      case 'inactive':
        return 'Inactivo';
      default:
        return 'Desconocido';
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
    }).format(value);
  };

  if (loading) {
    return (
      <LoadingSpinner
        fullScreen
        message="Cargando gestión de productos..."
        variant="pulse"
      />
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Fade in timeout={600}>
        <Box>
          {/* Modern Page Header */}
          <PageHeader
            title="Gestión de Productos"
            subtitle="Administre su inventario y catálogo de productos de manera eficiente"
            breadcrumbs={[
              { label: 'Dashboard', href: '/dashboard' },
              { label: 'Inventario', href: '/inventory' },
              { label: 'Productos' },
            ]}
            tags={['Inventario', 'Catálogo', 'Stock']}
            actions={
              <Stack direction="row" spacing={2}>
                <ModernButton
                  variant="outlined"
                  icon={<Download />}
                  onClick={() => alert('Exportar productos')}
                >
                  Exportar
                </ModernButton>
                <ModernButton
                  variant="gradient"
                  icon={<Add />}
                  onClick={() => alert('Crear producto')}
                >
                  Nuevo Producto
                </ModernButton>
              </Stack>
            }
          />

          {/* Stats Overview */}
          <Grid2 container spacing={3} sx={{ mb: 4 }}>
            <Grid2 xs={12} sm={6} lg={3}>
              <StatCard
                title="Total Productos"
                value={stats.totalProducts.toLocaleString()}
                subtitle="En inventario"
                icon={<Inventory />}
                trend="up"
                trendValue={`+${stats.monthlyGrowth}%`}
                color="primary"
              />
            </Grid2>
            <Grid2 xs={12} sm={6} lg={3}>
              <StatCard
                title="Stock Bajo"
                value={stats.lowStockProducts}
                subtitle="Requieren atención"
                icon={<TrendingDown />}
                trend="down"
                trendValue="-8.2%"
                color="warning"
              />
            </Grid2>
            <Grid2 xs={12} sm={6} lg={3}>
              <StatCard
                title="Valor Total"
                value={formatCurrency(stats.totalValue)}
                subtitle="Inventario"
                icon={<AttachMoney />}
                trend="up"
                trendValue="+15.3%"
                color="success"
              />
            </Grid2>
            <Grid2 xs={12} sm={6} lg={3}>
              <StatCard
                title="Precio Promedio"
                value={formatCurrency(stats.averagePrice)}
                subtitle="Por producto"
                icon={<LocalOffer />}
                trend="up"
                trendValue="+5.7%"
                color="info"
              />
            </Grid2>
          </Grid2>

          {/* Search and Filters */}
          <ModernCard variant="glass" sx={{ mb: 4 }}>
            <Box sx={{ p: 3 }}>
              <Grid2 container spacing={3} alignItems="center">
                <Grid2 xs={12} md={6}>
                  <TextField
                    fullWidth
                    placeholder="Buscar productos por nombre o SKU..."
                    value={searchTerm}
                    onChange={handleSearch}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Search color="action" />
                        </InputAdornment>
                      ),
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                        background: 'rgba(255, 255, 255, 0.8)',
                      },
                    }}
                  />
                </Grid2>
                <Grid2 xs={12} md={6}>
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    <Typography variant="body2" color="text.secondary" sx={{ mr: 1, alignSelf: 'center' }}>
                      Categorías:
                    </Typography>
                    {categories.map((category) => (
                      <Chip
                        key={category}
                        label={category}
                        onClick={() => setSelectedCategory(category.toLowerCase())}
                        color={selectedCategory === category.toLowerCase() ? 'primary' : 'default'}
                        variant={selectedCategory === category.toLowerCase() ? 'filled' : 'outlined'}
                        sx={{ borderRadius: 2 }}
                      />
                    ))}
                  </Stack>
                </Grid2>
              </Grid2>
            </Box>
          </ModernCard>

          {/* Products Grid */}
          <Grid2 container spacing={3}>
            {products
              .filter((product) =>
                product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                product.sku.toLowerCase().includes(searchTerm.toLowerCase())
              )
              .map((product) => (
                <Grid2 key={product.id} xs={12} sm={6} lg={4}>
                  <ModernCard hoverable>
                    <Box sx={{ p: 3 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                        <Box sx={{ flex: 1 }}>
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
                            {product.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            SKU: {product.sku}
                          </Typography>
                        </Box>
                        <Chip
                          label={getStatusLabel(product.status)}
                          color={getStatusColor(product.status) as any}
                          size="small"
                          sx={{ borderRadius: 1.5 }}
                        />
                      </Box>

                      <Box sx={{ mb: 2 }}>
                        <Typography variant="h5" sx={{ fontWeight: 700, color: 'primary.main', mb: 1 }}>
                          {formatCurrency(product.price)}
                        </Typography>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Typography variant="body2" color="text.secondary">
                            Stock: <strong>{product.stock} unidades</strong>
                          </Typography>
                          <Chip
                            label={product.category}
                            size="small"
                            variant="outlined"
                            sx={{ borderRadius: 1.5 }}
                          />
                        </Box>
                      </Box>

                      {product.lastSale && (
                        <Typography variant="caption" color="text.secondary">
                          Última venta: {new Date(product.lastSale).toLocaleDateString('es-ES')}
                        </Typography>
                      )}

                      <Box sx={{ mt: 3, display: 'flex', gap: 1 }}>
                        <ModernButton
                          size="small"
                          variant="outlined"
                          fullWidth
                          onClick={() => alert(`Editar ${product.name}`)}
                        >
                          Editar
                        </ModernButton>
                        <ModernButton
                          size="small"
                          variant="contained"
                          fullWidth
                          onClick={() => alert(`Ver detalles de ${product.name}`)}
                        >
                          Ver Detalles
                        </ModernButton>
                      </Box>
                    </Box>
                  </ModernCard>
                </Grid2>
              ))}
          </Grid2>

          {/* Quick Actions Section */}
          <Grid2 container spacing={3} sx={{ mt: 4 }}>
            <Grid2 xs={12} md={6}>
              <MetricCard
                title="Productos con Stock Crítico"
                value={`${stats.lowStockProducts} productos`}
                trend={{
                  value: -15.2,
                  label: 'Mejora del 15.2% vs mes anterior',
                  direction: 'up',
                }}
                color="#f5576c"
                icon={<TrendingDown />}
              />
            </Grid2>
            <Grid2 xs={12} md={6}>
              <MetricCard
                title="Categoría Más Vendida"
                value={stats.topCategory}
                trend={{
                  value: 8.5,
                  label: '+8.5% de crecimiento',
                  direction: 'up',
                }}
                color="#43e97b"
                icon={<Analytics />}
              />
            </Grid2>
          </Grid2>

          {/* Low Stock Alert */}
          {stats.lowStockProducts > 0 && (
            <Fade in timeout={1000}>
              <Alert
                severity="warning"
                sx={{
                  mt: 4,
                  borderRadius: 3,
                  background: 'rgba(255, 152, 0, 0.1)',
                  border: '1px solid rgba(255, 152, 0, 0.2)',
                }}
                action={
                  <ModernButton
                    color="warning"
                    size="small"
                    onClick={() => alert('Ver productos con stock bajo')}
                  >
                    Ver Productos
                  </ModernButton>
                }
              >
                <Typography variant="body2">
                  <strong>Atención:</strong> Hay {stats.lowStockProducts} productos con stock bajo que requieren reposición.
                </Typography>
              </Alert>
            </Fade>
          )}
        </Box>
      </Fade>
    </Container>
  );
};

export default ModernProductsPage;