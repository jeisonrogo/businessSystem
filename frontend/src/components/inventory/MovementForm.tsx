/**
 * Formulario de Creación de Movimientos de Inventario
 * Modal para registrar nuevos movimientos de entrada, salida, merma y ajuste
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  TextField,
  Button,
  MenuItem,
  Alert,
  CircularProgress,
  Typography,
  Grid,
  Autocomplete,
  InputAdornment,
} from '@mui/material';
import {
  Save,
  Cancel,
  TrendingUp,
  TrendingDown,
  ReportProblem,
  Tune,
} from '@mui/icons-material';

import { ProductService } from '../../services/productService';
import { InventoryService } from '../../services/inventoryService';
import {
  InventoryMovementCreate,
  MovementType,
  Product,
} from '../../types';

interface MovementFormProps {
  open: boolean;
  onClose: () => void;
  onSave: (movement: any) => void;
}

const MovementForm: React.FC<MovementFormProps> = ({
  open,
  onClose,
  onSave,
}) => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  
  const [formData, setFormData] = useState<InventoryMovementCreate>({
    producto_id: '',
    tipo_movimiento: MovementType.ENTRADA,
    cantidad: 0,
    precio_unitario: 0,
    referencia: '',
    observaciones: '',
  });

  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  // Cargar productos al abrir el modal
  useEffect(() => {
    if (open) {
      loadProducts();
      resetForm();
    }
  }, [open]);

  const loadProducts = async () => {
    setLoading(true);
    try {
      const response = await ProductService.getProducts({ 
        limit: 100, 
        only_active: true 
      });
      setProducts(response.items);
    } catch (err: any) {
      setError('Error al cargar productos: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      producto_id: '',
      tipo_movimiento: MovementType.ENTRADA,
      cantidad: 0,
      precio_unitario: 0,
      referencia: '',
      observaciones: '',
    });
    setSelectedProduct(null);
    setFormErrors({});
    setError(null);
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.producto_id) {
      errors.producto_id = 'El producto es requerido';
    }

    if (!formData.cantidad || formData.cantidad <= 0) {
      errors.cantidad = 'La cantidad debe ser mayor a cero';
    }

    if (!formData.precio_unitario || formData.precio_unitario <= 0) {
      errors.precio_unitario = 'El precio unitario debe ser mayor a cero';
    }

    // Validación especial para salidas - verificar stock disponible
    if (
      formData.tipo_movimiento === MovementType.SALIDA &&
      selectedProduct &&
      formData.cantidad > selectedProduct.stock
    ) {
      errors.cantidad = `Stock insuficiente. Disponible: ${selectedProduct.stock}`;
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleInputChange = (field: keyof InventoryMovementCreate, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Limpiar error del campo modificado
    if (formErrors[field]) {
      setFormErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleProductChange = (product: Product | null) => {
    setSelectedProduct(product);
    if (product) {
      handleInputChange('producto_id', product.id);
      
      // Si es entrada, usar el precio base del producto como sugerencia
      if (formData.tipo_movimiento === MovementType.ENTRADA && formData.precio_unitario === 0) {
        handleInputChange('precio_unitario', product.precio_base);
      }
      // Si es salida, usar el precio público
      else if (formData.tipo_movimiento === MovementType.SALIDA && formData.precio_unitario === 0) {
        handleInputChange('precio_unitario', product.precio_publico);
      }
    } else {
      handleInputChange('producto_id', '');
      handleInputChange('precio_unitario', 0);
    }
  };

  const handleTypeChange = (tipo: MovementType) => {
    handleInputChange('tipo_movimiento', tipo);
    
    // Ajustar precio sugerido según el tipo
    if (selectedProduct) {
      if (tipo === MovementType.ENTRADA) {
        handleInputChange('precio_unitario', selectedProduct.precio_base);
      } else if (tipo === MovementType.SALIDA) {
        handleInputChange('precio_unitario', selectedProduct.precio_publico);
      }
    }
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const movement = await InventoryService.createMovement(formData);
      onSave(movement);
      onClose();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleClose = () => {
    if (!saving) {
      onClose();
    }
  };

  const typeLabels = InventoryService.getMovementTypeLabels();
  const typeColors = InventoryService.getMovementTypeColors();

  const getTypeIcon = (type: MovementType) => {
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
        return null;
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
    }).format(value);
  };

  const totalValue = formData.cantidad * (formData.precio_unitario || 0);

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      disableEscapeKeyDown={saving}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {getTypeIcon(formData.tipo_movimiento)}
          <Typography variant="h6">
            Registrar Movimiento de Inventario
          </Typography>
        </Box>
      </DialogTitle>

      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Box sx={{ mt: 2 }}>
          <Grid container spacing={3}>
            {/* Tipo de movimiento */}
            <Grid item xs={12} sm={6}>
              <TextField
                select
                fullWidth
                label="Tipo de Movimiento"
                value={formData.tipo_movimiento}
                onChange={(e) => handleTypeChange(e.target.value as MovementType)}
                error={!!formErrors.tipo_movimiento}
                helperText={formErrors.tipo_movimiento}
                required
              >
                {Object.entries(typeLabels).map(([key, label]) => (
                  <MenuItem key={key} value={key}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getTypeIcon(key as MovementType)}
                      <span style={{ color: typeColors[key as MovementType] }}>
                        {label}
                      </span>
                    </Box>
                  </MenuItem>
                ))}
              </TextField>
            </Grid>

            {/* Producto */}
            <Grid item xs={12} sm={6}>
              <Autocomplete
                options={products}
                getOptionLabel={(option) => `${option.sku} - ${option.nombre}`}
                value={selectedProduct}
                onChange={(_, value) => handleProductChange(value)}
                loading={loading}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Producto"
                    required
                    error={!!formErrors.producto_id}
                    helperText={formErrors.producto_id}
                    InputProps={{
                      ...params.InputProps,
                      endAdornment: (
                        <>
                          {loading ? <CircularProgress size={20} /> : null}
                          {params.InputProps.endAdornment}
                        </>
                      ),
                    }}
                  />
                )}
                renderOption={(props, option) => (
                  <li {...props}>
                    <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                      <Typography variant="body2">
                        <strong>{option.sku}</strong> - {option.nombre}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Stock actual: {option.stock} | Precio: {formatCurrency(option.precio_publico)}
                      </Typography>
                    </Box>
                  </li>
                )}
              />
            </Grid>

            {/* Stock actual del producto seleccionado */}
            {selectedProduct && (
              <Grid item xs={12}>
                <Box 
                  sx={{ 
                    p: 2, 
                    backgroundColor: 'background.paper', 
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                  }}
                >
                  <Typography variant="body2" color="text.secondary">
                    <strong>Stock Actual:</strong> {selectedProduct.stock} unidades |
                    <strong> Precio Base:</strong> {formatCurrency(selectedProduct.precio_base)} |
                    <strong> Precio Público:</strong> {formatCurrency(selectedProduct.precio_publico)}
                  </Typography>
                </Box>
              </Grid>
            )}

            {/* Cantidad */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Cantidad"
                type="number"
                value={formData.cantidad || ''}
                onChange={(e) => handleInputChange('cantidad', parseInt(e.target.value) || 0)}
                error={!!formErrors.cantidad}
                helperText={formErrors.cantidad}
                inputProps={{ min: 1 }}
                required
              />
            </Grid>

            {/* Precio unitario */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Precio Unitario"
                type="number"
                value={formData.precio_unitario || ''}
                onChange={(e) => handleInputChange('precio_unitario', parseFloat(e.target.value) || 0)}
                error={!!formErrors.precio_unitario}
                helperText={formErrors.precio_unitario}
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                }}
                inputProps={{ min: 0, step: 0.01 }}
                required
              />
            </Grid>

            {/* Valor total calculado */}
            {totalValue > 0 && (
              <Grid item xs={12}>
                <Box sx={{ textAlign: 'right', p: 2, backgroundColor: 'action.hover', borderRadius: 1 }}>
                  <Typography variant="h6" color="primary">
                    Valor Total: {formatCurrency(totalValue)}
                  </Typography>
                </Box>
              </Grid>
            )}

            {/* Referencia */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Referencia"
                value={formData.referencia || ''}
                onChange={(e) => handleInputChange('referencia', e.target.value)}
                placeholder="Ej: FC-001, OC-123, etc."
                helperText="Número de factura, orden de compra, etc."
              />
            </Grid>

            {/* Observaciones */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Observaciones"
                value={formData.observaciones || ''}
                onChange={(e) => handleInputChange('observaciones', e.target.value)}
                multiline
                rows={2}
                placeholder="Observaciones adicionales..."
              />
            </Grid>
          </Grid>
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button
          onClick={handleClose}
          disabled={saving}
          startIcon={<Cancel />}
        >
          Cancelar
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={saving}
          startIcon={saving ? <CircularProgress size={20} /> : <Save />}
        >
          {saving ? 'Guardando...' : 'Guardar Movimiento'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default MovementForm;