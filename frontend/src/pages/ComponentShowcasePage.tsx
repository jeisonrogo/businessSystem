/**
 * Component Showcase Page - Demonstrates Modern UI Components
 * Sistema de Gestión Empresarial
 */

import React, { useState } from 'react';
import {
  Container,
  Fade,
  Box,
  Typography,
  Tooltip,
} from '@mui/material';
import Grid2 from '@mui/material/Unstable_Grid2';
import {
  Inventory,
  People,
  Receipt,
  AttachMoney,
  TrendingUp,
  Refresh,
  Add,
  Download,
  Visibility,
} from '@mui/icons-material';

// Import new modern components
import {
  PageHeader,
  ModernCard,
  StatCard,
  ModernButton,
  LoadingSpinner,
  ModernBarChart,
  MetricCard,
  SimpleGridChart,
} from '../components/common';

const ComponentShowcasePage: React.FC = () => {
  const [loading, setLoading] = useState(false);

  const handleRefresh = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 2000);
  };

  // Sample data for visualizations
  const sampleBarData = [
    { label: 'Productos Vendidos', value: 1250, subtitle: 'Este mes' },
    { label: 'Nuevos Clientes', value: 85, subtitle: 'Últimos 30 días' },
    { label: 'Facturas Generadas', value: 320, subtitle: 'Este mes' },
    { label: 'Valor Inventario', value: 850000, subtitle: 'Total actual' },
  ];

  const sampleGridData = [
    {
      period: 'Enero 2025',
      value1: 12500000,
      value2: 45,
      label1: 'Ventas',
      label2: 'Facturas',
    },
    {
      period: 'Febrero 2025',
      value1: 15200000,
      value2: 52,
      label1: 'Ventas',
      label2: 'Facturas',
    },
    {
      period: 'Marzo 2025',
      value1: 18750000,
      value2: 64,
      label1: 'Ventas',
      label2: 'Facturas',
    },
    {
      period: 'Abril 2025',
      value1: 16800000,
      value2: 58,
      label1: 'Ventas',
      label2: 'Facturas',
    },
  ];

  if (loading) {
    return <LoadingSpinner fullScreen message="Cargando componentes modernos..." variant="pulse" />;
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Fade in timeout={600}>
        <Box>
          {/* Modern Page Header */}
          <PageHeader
            title="Componentes Modernos"
            subtitle="Demostración de la nueva librería de componentes profesionales"
            breadcrumbs={[
              { label: 'Dashboard', href: '/dashboard' },
              { label: 'Sistema', href: '/system' },
              { label: 'Componentes' },
            ]}
            tags={['UI/UX', 'Componentes', 'Diseño Moderno']}
            actions={
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Tooltip title="Actualizar datos">
                  <ModernButton
                    variant="outlined"
                    icon={<Refresh />}
                    onClick={handleRefresh}
                  >
                    Actualizar
                  </ModernButton>
                </Tooltip>
                <ModernButton
                  variant="gradient"
                  icon={<Add />}
                  onClick={() => alert('Nuevo elemento')}
                >
                  Crear Nuevo
                </ModernButton>
              </Box>
            }
          />

          {/* Modern Stat Cards Section */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
              Tarjetas de Estadísticas Modernas
            </Typography>
            <Grid2 container spacing={3}>
              <Grid2 xs={12} sm={6} lg={3}>
                <StatCard
                  title="Total Productos"
                  value="1,247"
                  subtitle="Inventario actual"
                  icon={<Inventory />}
                  trend="up"
                  trendValue="+12.5%"
                  color="primary"
                />
              </Grid2>
              <Grid2 xs={12} sm={6} lg={3}>
                <StatCard
                  title="Clientes Activos"
                  value="892"
                  subtitle="Este mes"
                  icon={<People />}
                  trend="up"
                  trendValue="+8.2%"
                  color="success"
                />
              </Grid2>
              <Grid2 xs={12} sm={6} lg={3}>
                <StatCard
                  title="Facturas Pendientes"
                  value="23"
                  subtitle="Por revisar"
                  icon={<Receipt />}
                  trend="down"
                  trendValue="-15.3%"
                  color="warning"
                />
              </Grid2>
              <Grid2 xs={12} sm={6} lg={3}>
                <StatCard
                  title="Ingresos del Mes"
                  value="$45.2M"
                  subtitle="COP"
                  icon={<AttachMoney />}
                  trend="up"
                  trendValue="+23.1%"
                  color="info"
                />
              </Grid2>
            </Grid2>
          </Box>

          {/* Metric Cards Section */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
              Tarjetas de Métricas
            </Typography>
            <Grid2 container spacing={3}>
              <Grid2 xs={12} sm={6} md={4}>
                <MetricCard
                  title="Crecimiento Mensual"
                  value="24.5%"
                  trend={{
                    value: 5.2,
                    label: '+5.2% vs mes anterior',
                    direction: 'up',
                  }}
                  color="#4facfe"
                  icon={<TrendingUp />}
                />
              </Grid2>
              <Grid2 xs={12} sm={6} md={4}>
                <MetricCard
                  title="Conversión de Ventas"
                  value="18.7%"
                  trend={{
                    value: -2.1,
                    label: '-2.1% vs promedio',
                    direction: 'down',
                  }}
                  color="#43e97b"
                  icon={<Visibility />}
                />
              </Grid2>
              <Grid2 xs={12} sm={6} md={4}>
                <MetricCard
                  title="ROI del Período"
                  value="142%"
                  trend={{
                    value: 0,
                    label: 'Estable este mes',
                    direction: 'neutral',
                  }}
                  color="#fa709a"
                  icon={<AttachMoney />}
                />
              </Grid2>
            </Grid2>
          </Box>

          {/* Data Visualization Section */}
          <Grid2 container spacing={4}>
            <Grid2 xs={12} lg={6}>
              <ModernBarChart
                title="Resumen de Actividad"
                data={sampleBarData}
                format="number"
              />
            </Grid2>
            <Grid2 xs={12} lg={6}>
              <ModernCard variant="glass">
                <Box sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                    Acciones Rápidas
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    Herramientas de gestión empresarial
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <ModernButton
                      variant="contained"
                      icon={<Add />}
                      fullWidth
                    >
                      Crear Nueva Factura
                    </ModernButton>
                    <ModernButton
                      variant="outlined"
                      icon={<Download />}
                      fullWidth
                    >
                      Exportar Reportes
                    </ModernButton>
                    <ModernButton
                      variant="text"
                      icon={<Visibility />}
                      fullWidth
                    >
                      Ver Estadísticas Completas
                    </ModernButton>
                  </Box>
                </Box>
              </ModernCard>
            </Grid2>
            <Grid2 xs={12}>
              <SimpleGridChart
                data={sampleGridData}
                title="Tendencias Trimestrales"
                colors={['#667eea', '#764ba2']}
              />
            </Grid2>
          </Grid2>

          {/* Loading States Showcase */}
          <Box sx={{ mt: 4 }}>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
              Estados de Carga
            </Typography>
            <Grid2 container spacing={3}>
              <Grid2 xs={12} sm={4}>
                <ModernCard>
                  <Box sx={{ p: 3, textAlign: 'center' }}>
                    <Typography variant="h6" gutterBottom>
                      Spinner Clásico
                    </Typography>
                    <LoadingSpinner message="Cargando datos..." />
                  </Box>
                </ModernCard>
              </Grid2>
              <Grid2 xs={12} sm={4}>
                <ModernCard>
                  <Box sx={{ p: 3, textAlign: 'center' }}>
                    <Typography variant="h6" gutterBottom>
                      Dots Animados
                    </Typography>
                    <LoadingSpinner variant="dots" message="Procesando..." />
                  </Box>
                </ModernCard>
              </Grid2>
              <Grid2 xs={12} sm={4}>
                <ModernCard>
                  <Box sx={{ p: 3, textAlign: 'center' }}>
                    <Typography variant="h6" gutterBottom>
                      Pulse Effect
                    </Typography>
                    <LoadingSpinner variant="pulse" message="Sincronizando..." />
                  </Box>
                </ModernCard>
              </Grid2>
            </Grid2>
          </Box>
        </Box>
      </Fade>
    </Container>
  );
};

export default ComponentShowcasePage;