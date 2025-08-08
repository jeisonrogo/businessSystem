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
} from '@mui/material';
import { Inventory } from '@mui/icons-material';
import { Product } from '../../types';

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
  const [newStock, setNewStock] = useState<number>(0);
  const [validationError, setValidationError] = useState<string>('');

  // Resetear el formulario cuando se abre el diálogo
  useEffect(() => {
    if (open && product) {
      setNewStock(product.stock);
      setValidationError('');
    }
  }, [open, product]);

  const handleStockChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    const numericValue = value === '' ? 0 : Number(value);
    
    if (numericValue < 0) {
      setValidationError('El stock no puede ser negativo');
    } else {
      setValidationError('');
    }
    
    setNewStock(numericValue);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (newStock < 0) {
      setValidationError('El stock no puede ser negativo');
      return;
    }

    if (!product) return;

    try {
      await onUpdateStock(newStock);
    } catch (error) {
      // El error se maneja en el componente padre
      console.error('Error al actualizar stock:', error);
    }
  };

  const handleClose = () => {
    setValidationError('');
    onClose();
  };

  const stockDifference = product ? newStock - product.stock : 0;
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
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Información del producto */}
        <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
            {product.nombre}
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            SKU: {product.sku}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Stock actual: <strong>{product.stock} unidades</strong>
          </Typography>
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
          disabled={loading}
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