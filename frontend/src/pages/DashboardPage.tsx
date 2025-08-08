/**
 * Página del Dashboard Principal
 */

import React from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  CircularProgress,
} from '@mui/material';
import {
  TrendingUp,
  Inventory,
  People,
  Receipt,
  AttachMoney,
} from '@mui/icons-material';

const DashboardPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 4 }}>
        Bienvenido al Sistema de Gestión Empresarial
      </Typography>

      <Grid container spacing={3}>
        {/* Tarjetas de estadísticas */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Inventory sx={{ mr: 2, color: 'primary.main' }} />
                <Box>
                  <Typography color="text.secondary" variant="body2">
                    Total Productos
                  </Typography>
                  <Typography variant="h6">
                    <CircularProgress size={16} sx={{ mr: 1 }} />
                    Cargando...
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <People sx={{ mr: 2, color: 'success.main' }} />
                <Box>
                  <Typography color="text.secondary" variant="body2">
                    Total Clientes
                  </Typography>
                  <Typography variant="h6">
                    <CircularProgress size={16} sx={{ mr: 1 }} />
                    Cargando...
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Receipt sx={{ mr: 2, color: 'warning.main' }} />
                <Box>
                  <Typography color="text.secondary" variant="body2">
                    Facturas Este Mes
                  </Typography>
                  <Typography variant="h6">
                    <CircularProgress size={16} sx={{ mr: 1 }} />
                    Cargando...
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <AttachMoney sx={{ mr: 2, color: 'error.main' }} />
                <Box>
                  <Typography color="text.secondary" variant="body2">
                    Valor Inventario
                  </Typography>
                  <Typography variant="h6">
                    <CircularProgress size={16} sx={{ mr: 1 }} />
                    Cargando...
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Panel principal */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Gráfico de Ventas
            </Typography>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '80%',
                color: 'text.secondary',
              }}
            >
              <Box sx={{ textAlign: 'center' }}>
                <TrendingUp sx={{ fontSize: 64, mb: 2 }} />
                <Typography variant="body1">
                  Gráfico de ventas en desarrollo...
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* Panel lateral */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Actividad Reciente
            </Typography>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '80%',
                color: 'text.secondary',
              }}
            >
              <Typography variant="body1">
                Actividad reciente en desarrollo...
              </Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardPage;