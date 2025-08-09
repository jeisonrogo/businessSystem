/**
 * Modal de Detalles de Movimiento de Inventario
 * Muestra información detallada de un movimiento específico
 */

import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Button,
  Typography,
  Grid,
  Chip,
  Divider,
  Paper,
} from '@mui/material';
import {
  Close,
  TrendingUp,
  TrendingDown,
  ReportProblem,
  Tune,
  Receipt,
  Person,
  CalendarToday,
} from '@mui/icons-material';

import { InventoryService } from '../../services/inventoryService';
import { InventoryMovement, MovementType } from '../../types';

interface MovementDetailsModalProps {
  open: boolean;
  movement: InventoryMovement | null;
  onClose: () => void;
}

const MovementDetailsModal: React.FC<MovementDetailsModalProps> = ({
  open,
  movement,
  onClose,
}) => {
  if (!movement) return null;

  const typeLabels = InventoryService.getMovementTypeLabels();
  const typeColors = InventoryService.getMovementTypeColors();

  const getMovementIcon = (type: MovementType) => {
    switch (type) {
      case MovementType.ENTRADA:
        return <TrendingUp />;
      case MovementType.SALIDA:
        return <TrendingDown />;
      case MovementType.MERMA:
        return <ReportProblem />;
      case MovementType.AJUSTE:
        return <Tune />;
      default:
        return <Receipt />;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('es-CO', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatCurrency = (value: number | string) => {
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    return InventoryService.formatCurrency(numValue);
  };

  const stockChange = movement.stock_posterior - movement.stock_anterior;
  const totalValue = InventoryService.calculateMovementValue(movement);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {getMovementIcon(movement.tipo_movimiento)}
          <Box>
            <Typography variant="h6">
              Detalles del Movimiento
            </Typography>
            <Chip
              icon={getMovementIcon(movement.tipo_movimiento)}
              label={typeLabels[movement.tipo_movimiento]}
              size="small"
              sx={{
                backgroundColor: typeColors[movement.tipo_movimiento] + '20',
                color: typeColors[movement.tipo_movimiento],
                fontWeight: 'bold',
                mt: 1,
                '& .MuiChip-icon': {
                  color: typeColors[movement.tipo_movimiento],
                },
              }}
            />
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Grid container spacing={3}>
          {/* Información del Producto */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2, backgroundColor: 'action.hover' }}>
              <Typography variant="h6" gutterBottom>
                Información del Producto
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Nombre
                  </Typography>
                  <Typography variant="body1" fontWeight="bold">
                    {movement.producto?.nombre || 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    SKU
                  </Typography>
                  <Typography variant="body1" fontWeight="bold">
                    {movement.producto?.sku || 'N/A'}
                  </Typography>
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          {/* Detalles del Movimiento */}
          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
              Detalles del Movimiento
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <CalendarToday sx={{ mr: 1, color: 'text.secondary' }} />
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Fecha y Hora
                </Typography>
                <Typography variant="body1">
                  {formatDate(movement.created_at)}
                </Typography>
              </Box>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Receipt sx={{ mr: 1, color: 'text.secondary' }} />
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Referencia
                </Typography>
                <Typography variant="body1">
                  {movement.referencia || 'Sin referencia'}
                </Typography>
              </Box>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Person sx={{ mr: 1, color: 'text.secondary' }} />
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Registrado por
                </Typography>
                <Typography variant="body1">
                  {movement.created_by || 'Sistema'}
                </Typography>
              </Box>
            </Box>
          </Grid>

          {/* Información Financiera */}
          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
              Información Financiera
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Cantidad
              </Typography>
              <Typography 
                variant="h6" 
                sx={{
                  color: movement.tipo_movimiento === MovementType.ENTRADA || movement.tipo_movimiento === MovementType.AJUSTE
                    ? 'success.main'
                    : 'error.main',
                  fontWeight: 'bold',
                }}
              >
                {InventoryService.formatQuantityWithSign(movement.tipo_movimiento, movement.cantidad)}
              </Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Precio Unitario
              </Typography>
              <Typography variant="body1" fontWeight="bold">
                {formatCurrency(movement.precio_unitario || 0)}
              </Typography>
            </Box>

            {movement.costo_unitario && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Costo Unitario
                </Typography>
                <Typography variant="body1" fontWeight="bold">
                  {formatCurrency(movement.costo_unitario)}
                </Typography>
              </Box>
            )}

            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Valor Total
              </Typography>
              <Typography variant="h6" color="primary" sx={{ fontWeight: 'bold' }}>
                {formatCurrency(totalValue)}
              </Typography>
            </Box>
          </Grid>

          {/* Cambios en Stock */}
          <Grid item xs={12}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
              Impacto en Stock
            </Typography>
            
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={4}>
                <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: 'info.light' }}>
                  <Typography variant="body2" color="text.secondary">
                    Stock Anterior
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    {movement.stock_anterior}
                  </Typography>
                </Paper>
              </Grid>
              
              <Grid item xs={12} sm={4} sx={{ textAlign: 'center' }}>
                <Typography 
                  variant="h4"
                  sx={{
                    color: stockChange >= 0 ? 'success.main' : 'error.main',
                    fontWeight: 'bold',
                  }}
                >
                  {stockChange >= 0 ? '+' : ''}{stockChange}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Cambio
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={4}>
                <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: 'success.light' }}>
                  <Typography variant="body2" color="text.secondary">
                    Stock Posterior
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    {movement.stock_posterior}
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </Grid>

          {/* Observaciones */}
          {movement.observaciones && (
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                Observaciones
              </Typography>
              <Paper sx={{ p: 2, backgroundColor: 'background.default' }}>
                <Typography variant="body1">
                  {movement.observaciones}
                </Typography>
              </Paper>
            </Grid>
          )}
        </Grid>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button
          onClick={onClose}
          startIcon={<Close />}
          variant="outlined"
        >
          Cerrar
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default MovementDetailsModal;