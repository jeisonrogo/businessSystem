/**
 * Formulario para crear/editar productos
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Grid,
  Box,
  Alert,
  CircularProgress,
  InputAdornment,
} from '@mui/material';
import { Product, ProductCreate, ProductUpdate } from '../../types';

interface ProductFormProps {
  open: boolean;
  onClose: () => void;
  onSave: (product: ProductCreate | ProductUpdate) => Promise<void>;
  product?: Product | null;
  loading?: boolean;
  error?: string;
}

const ProductForm: React.FC<ProductFormProps> = ({
  open,
  onClose,
  onSave,
  product,
  loading = false,
  error,
}) => {
  const [formData, setFormData] = useState<ProductCreate>({
    sku: '',
    nombre: '',
    descripcion: '',
    url_foto: '',
    precio_base: 0,
    precio_publico: 0,
    stock: 0,
  });

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const isEditing = !!product;

  // Resetear formulario cuando se abre/cierra o cambia el producto
  useEffect(() => {
    if (open && product) {
      // Modo edición - cargar datos del producto
      setFormData({
        sku: product.sku,
        nombre: product.nombre,
        descripcion: product.descripcion || '',
        url_foto: product.url_foto || '',
        precio_base: product.precio_base,
        precio_publico: product.precio_publico,
        stock: product.stock,
      });
    } else if (open && !product) {
      // Modo creación - resetear formulario
      setFormData({
        sku: '',
        nombre: '',
        descripcion: '',
        url_foto: '',
        precio_base: 0,
        precio_publico: 0,
        stock: 0,
      });
    }
    setValidationErrors({});
  }, [open, product]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    
    // Convertir valores numéricos
    let processedValue: string | number = value;
    if (['precio_base', 'precio_publico', 'stock'].includes(name)) {
      processedValue = value === '' ? 0 : Number(value);
    }

    setFormData(prev => ({
      ...prev,
      [name]: processedValue,
    }));

    // Limpiar error de validación del campo cuando el usuario empiece a escribir
    if (validationErrors[name]) {
      setValidationErrors(prev => ({
        ...prev,
        [name]: '',
      }));
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.sku.trim()) {
      errors.sku = 'El SKU es requerido';
    }

    if (!formData.nombre.trim()) {
      errors.nombre = 'El nombre es requerido';
    }

    if (formData.precio_base <= 0) {
      errors.precio_base = 'El precio base debe ser mayor a 0';
    }

    if (formData.precio_publico <= 0) {
      errors.precio_publico = 'El precio público debe ser mayor a 0';
    }

    if (typeof formData.stock === 'number' && formData.stock < 0) {
      errors.stock = 'El stock no puede ser negativo';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      if (isEditing) {
        // En modo edición, no enviamos SKU ya que es inmutable
        const { sku, stock, ...updateData } = formData;
        await onSave(updateData as ProductUpdate);
      } else {
        // En modo creación, enviamos todo
        await onSave(formData);
      }
    } catch (error: any) {
      // Los errores ya se manejan en el componente padre
      // Solo logueamos aquí para debugging
      console.error('Error en ProductForm:', error);
    }
  };

  const handleClose = () => {
    setValidationErrors({});
    onClose();
  };

  return (
    <Dialog 
      open={open} 
      onClose={handleClose} 
      maxWidth="md" 
      fullWidth
      PaperProps={{
        component: 'form',
        onSubmit: handleSubmit,
      }}
    >
      <DialogTitle>
        {isEditing ? 'Editar Producto' : 'Nuevo Producto'}
      </DialogTitle>

      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} md={6}>
            <TextField
              name="sku"
              label="SKU"
              fullWidth
              required
              value={formData.sku}
              onChange={handleChange}
              error={!!validationErrors.sku}
              helperText={validationErrors.sku || (isEditing ? 'El SKU no puede ser modificado' : '')}
              disabled={isEditing || loading}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              name="nombre"
              label="Nombre"
              fullWidth
              required
              value={formData.nombre}
              onChange={handleChange}
              error={!!validationErrors.nombre}
              helperText={validationErrors.nombre}
              disabled={loading}
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              name="descripcion"
              label="Descripción"
              fullWidth
              multiline
              rows={3}
              value={formData.descripcion}
              onChange={handleChange}
              disabled={loading}
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              name="url_foto"
              label="URL de la Foto"
              fullWidth
              value={formData.url_foto}
              onChange={handleChange}
              disabled={loading}
              placeholder="https://ejemplo.com/imagen.jpg"
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              name="precio_base"
              label="Precio Base"
              type="number"
              fullWidth
              required
              value={formData.precio_base}
              onChange={handleChange}
              error={!!validationErrors.precio_base}
              helperText={validationErrors.precio_base}
              disabled={loading}
              InputProps={{
                startAdornment: <InputAdornment position="start">$</InputAdornment>,
              }}
              inputProps={{ min: 0, step: 0.01 }}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              name="precio_publico"
              label="Precio Público"
              type="number"
              fullWidth
              required
              value={formData.precio_publico}
              onChange={handleChange}
              error={!!validationErrors.precio_publico}
              helperText={validationErrors.precio_publico}
              disabled={loading}
              InputProps={{
                startAdornment: <InputAdornment position="start">$</InputAdornment>,
              }}
              inputProps={{ min: 0, step: 0.01 }}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              name="stock"
              label="Stock Inicial"
              type="number"
              fullWidth
              value={formData.stock}
              onChange={handleChange}
              error={!!validationErrors.stock}
              helperText={validationErrors.stock || (isEditing ? 'Use la gestión de inventario para modificar stock' : '')}
              disabled={isEditing || loading}
              inputProps={{ min: 0 }}
            />
          </Grid>
        </Grid>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancelar
        </Button>
        <Button 
          type="submit" 
          variant="contained" 
          disabled={loading}
        >
          {loading ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CircularProgress size={16} />
              Guardando...
            </Box>
          ) : (
            isEditing ? 'Actualizar' : 'Crear'
          )}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ProductForm;