/**
 * Página de Gestión de Clientes
 */

import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Chip,
} from '@mui/material';
import { Add, People } from '@mui/icons-material';

const ClientsPage: React.FC = () => {
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Gestión de Clientes
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Administra la información de tus clientes
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Add />}
          size="large"
        >
          Nuevo Cliente
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
          <People sx={{ fontSize: 80, color: 'info.main', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Módulo de Clientes
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            La gestión completa de clientes está en desarrollo.
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

export default ClientsPage;