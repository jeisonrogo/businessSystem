/**
 * Página de Gestión de Productos
 */

import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Chip,
} from '@mui/material';
import { Add, Inventory } from '@mui/icons-material';

const ProductsPage: React.FC = () => {
  return (
    <Box>
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
        >
          Nuevo Producto
        </Button>
      </Box>

      <Paper sx={{ p: 4 }}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: 400,
            textAlign: 'center',
          }}
        >
          <Inventory sx={{ fontSize: 80, color: 'primary.main', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Módulo de Productos
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            La gestión completa de productos está en desarrollo.
          </Typography>
          <Chip 
            label="Próximamente" 
            color="primary" 
            variant="outlined" 
          />
        </Box>
      </Paper>
    </Box>
  );
};

export default ProductsPage;