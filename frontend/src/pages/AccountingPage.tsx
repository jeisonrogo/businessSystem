/**
 * Página de Gestión Contable
 */

import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Chip,
} from '@mui/material';
import { Add, AccountBalance } from '@mui/icons-material';

const AccountingPage: React.FC = () => {
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Gestión Contable
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Plan de cuentas y asientos contables
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Add />}
          size="large"
        >
          Nuevo Asiento
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
          <AccountBalance sx={{ fontSize: 80, color: 'secondary.main', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Módulo de Contabilidad
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            La gestión completa de contabilidad está en desarrollo.
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

export default AccountingPage;