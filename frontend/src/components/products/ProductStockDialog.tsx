/**
 * Diálogo para actualizar stock de productos
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  CircularProgress,
  InputAdornment,
  Chip,
} from '@mui/material';
import { Inventory, Store, LocationOn } from '@mui/icons-material';
import { Product } from '../../types';
import { useTenant } from '../../context/TenantContext';

interface ProductStockDialogProps {
  open: boolean;
  onClose: () => void;
  onUpdateStock: (newStock: number) => Promise<void>;
  product: Product | null;
  loading?: boolean;
  error?: string;
}

const ProductStockDialog: React.FC<ProductStockDialogProps> = ({
  open,
  onClose,
  onUpdateStock,
  product,
  loading = false,
  error,
}) => {
  const { currentContext, setShowStoreSwitcher } = useTenant();
  const [newStock, setNewStock] = useState<number | ''>('');
  const [validationError, setValidationError] = useState<string>('');
  const [internalLoading, setInternalLoading] = useState<boolean>(false);
  const [internalError, setInternalError] = useState<string>('');

  // Resetear el formulario cuando se abre el diálogo
  useEffect(() => {
    if (open && product) {
      const currentStock = product.stock_local_actual ?? 0;
      setNewStock(currentStock);
      setValidationError('');
      setInternalError('');
    }
  }, [open, product]);

  const handleStockChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    
    if (value === '') {
      setNewStock('');
      setValidationError('');
      return;
    }
    
    const numericValue = Number(value);
    
    if (isNaN(numericValue) || numericValue < 0) {
      setValidationError('El stock debe ser un número no negativo');
    } else {
      setValidationError('');
    }
    
    setNewStock(numericValue);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validar contexto de tenant
    if (!currentContext?.tiene_contexto_local) {
      setInternalError('Debe seleccionar una tienda y local para actualizar stock');
      return;
    }
    
    const stockValue = typeof newStock === 'string' ? Number(newStock) : newStock;
    
    if (isNaN(stockValue) || stockValue < 0) {
      setValidationError('El stock debe ser un número no negativo');
      return;
    }

    if (!product) return;

    setInternalLoading(true);
    setInternalError('');

    try {
      await onUpdateStock(stockValue);
    } catch (error: any) {
      console.error('Error al actualizar stock:', error);
      setInternalError(error.message || 'Error al actualizar stock');
    } finally {
      setInternalLoading(false);
    }
  };

  const handleClose = () => {
    setValidationError('');
    setInternalError('');
    onClose();
  };

  const stockDifference = product && typeof newStock === 'number' ? newStock - (product.stock_local_actual ?? 0) : 0;
  const isIncreasing = stockDifference > 0;

  if (!product) return null;

  return (
    <Dialog 
      open={open} 
      onClose={handleClose} 
      maxWidth="sm" 
      fullWidth
      PaperProps={{
        component: 'form',
        onSubmit: handleSubmit,
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Inventory />
          Actualizar Stock
        </Box>
      </DialogTitle>

      <DialogContent>
        {(error || internalError) && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error || internalError}
          </Alert>
        )}

        {/* Información del producto y contexto */}
        <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
            {product.nombre}
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            SKU: {product.sku}
          </Typography>
          
          {/* Información de contexto multi-tenant */}
          {currentContext?.tiene_contexto_local ? (
            <Box sx={{ mt: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Store fontSize="small" color="primary" />
                <Typography variant="body2">
                  <strong>{currentContext.tienda_nombre}</strong>
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <LocationOn fontSize="small" color="secondary" />
                <Typography variant="body2">
                  {currentContext.local_nombre}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Stock en este local: <strong>{product.stock_local_actual ?? 0} unidades</strong>
              </Typography>
              {(product.stock_total_tienda ?? 0) > 0 && (
                <Typography variant="caption" color="text.secondary">
                  Stock total en tienda: {product.stock_total_tienda} unidades
                </Typography>
              )}
            </Box>
          ) : (
            <Alert 
              severity="warning" 
              sx={{ mt: 2 }}
              action={
                <Button 
                  size="small" 
                  onClick={() => setShowStoreSwitcher(true)}
                >
                  Seleccionar
                </Button>
              }
            >
              <Typography variant="body2">
                Debe seleccionar una tienda y local para actualizar stock.
              </Typography>
            </Alert>
          )}
        </Box>

        {/* Campo de stock */}
        <TextField
          label="Nuevo Stock"
          type="number"
          fullWidth
          required
          value={newStock}
          onChange={handleStockChange}
          error={!!validationError}
          helperText={validationError}
          disabled={loading || internalLoading}
          inputProps={{ min: 0 }}
          InputProps={{
            endAdornment: <InputAdornment position="end">unidades</InputAdornment>,
          }}
          sx={{ mb: 2 }}
        />

        {/* Indicador de cambio */}
        {stockDifference !== 0 && (
          <Alert
            severity={isIncreasing ? 'info' : 'warning'}
            sx={{ mb: 2 }}
          >
            <Typography variant="body2">
              {isIncreasing ? 'Incremento' : 'Reducción'}: {Math.abs(stockDifference)} unidades
            </Typography>
            <Typography variant="caption" display="block">
              Stock resultante: {newStock} unidades
            </Typography>
          </Alert>
        )}

        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            <strong>Nota:</strong> Esta acción solo actualiza el stock del producto. 
            Para registrar movimientos de inventario con costos, utiliza el módulo de Inventario.
          </Typography>
        </Alert>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancelar
        </Button>
        <Button 
          type="submit" 
          variant="contained" 
          disabled={loading || stockDifference === 0 || !!validationError}
        >
          {loading ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CircularProgress size={16} />
              Actualizando...
            </Box>
          ) : (
            'Actualizar Stock'
          )}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ProductStockDialog;