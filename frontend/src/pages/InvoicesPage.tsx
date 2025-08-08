/**
 * Página de Gestión de Facturas
 */

import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Chip,
} from '@mui/material';
import { Add, Receipt } from '@mui/icons-material';

const InvoicesPage: React.FC = () => {
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Gestión de Facturas
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Crea y administra tus facturas de venta
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Add />}
          size="large"
        >
          Nueva Factura
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
          <Receipt sx={{ fontSize: 80, color: 'warning.main', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Módulo de Facturación
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            La gestión completa de facturación está en desarrollo.
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

export default InvoicesPage;