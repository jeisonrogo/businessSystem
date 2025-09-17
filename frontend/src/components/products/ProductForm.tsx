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
  Card,
  CardMedia,
  IconButton,
  Typography,
} from '@mui/material';
import { CloudUpload, Delete, Image } from '@mui/icons-material';
import { Product, ProductCreate, ProductUpdate } from '../../types';
import { useTenant } from '../../context/TenantContext';
import { ProductService } from '../../services/productService';

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
  const { currentContext } = useTenant();
  
  const [formData, setFormData] = useState({
    sku: '',
    nombre: '',
    descripcion: '',
    imagen_path: '',
    precio_base: 0,
    precio_publico: 0,
    stock_inicial: 0,
    tienda_id: '',
  });

  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string>('');
  const [uploadingImage, setUploadingImage] = useState(false);

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
        imagen_path: product.imagen_path || '',
        precio_base: product.precio_base,
        precio_publico: product.precio_publico,
        stock_inicial: product.stock_local_actual ?? 0,
        tienda_id: product.tienda_id,
      });
      
      // Cargar imagen existente si hay una
      if (product.imagen_url) {
        setImagePreview(product.imagen_url);
      } else {
        setImagePreview('');
      }
      setImageFile(null);
    } else if (open && !product) {
      // Modo creación - resetear formulario
      setFormData({
        sku: '',
        nombre: '',
        descripcion: '',
        imagen_path: '',
        precio_base: 0,
        precio_publico: 0,
        stock_inicial: 0,
        tienda_id: currentContext?.tienda_id || '',
      });
      setImagePreview('');
      setImageFile(null);
    }
    setValidationErrors({});
    setUploadingImage(false);
  }, [open, product, currentContext?.tienda_id]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    
    // Convertir valores numéricos
    let processedValue: string | number = value;
    if (['precio_base', 'precio_publico', 'stock_inicial'].includes(name)) {
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

    if (typeof formData.stock_inicial === 'number' && formData.stock_inicial < 0) {
      errors.stock_inicial = 'El stock no puede ser negativo';
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
      // Primero guardamos los datos del producto
      if (isEditing) {
        const { sku, stock_inicial, tienda_id, ...updateData } = formData;
        await onSave(updateData as ProductUpdate);
      } else {
        await onSave(formData as ProductCreate);
      }

      // Si hay una imagen nueva que subir y tenemos un productId
      // En modo edición usamos el ID del producto existente
      // En modo creación, necesitaríamos obtener el ID del producto recién creado
      // Por ahora, solo manejamos la edición donde ya tenemos el ID
      if (imageFile && isEditing && product?.id) {
        const imagePath = await uploadImage(product.id);
        
        if (imagePath) {
          console.log('Imagen subida exitosamente:', imagePath);
        }
      } else if (imageFile && !isEditing) {
        // Para modo creación, necesitaríamos que onSave retorne el producto creado
        // o implementar una lógica diferente para obtener el ID
        console.log('Imagen seleccionada para nuevo producto - se subirá después de obtener el ID');
      }
    } catch (error: any) {
      // Los errores ya se manejan en el componente padre
      // Solo logueamos aquí para debugging
      console.error('Error en ProductForm:', error);
    }
  };

  const handleImageChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validar tipo de archivo
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      alert('Tipo de archivo no soportado. Use JPG, PNG, GIF o WEBP.');
      return;
    }

    // Validar tamaño (5MB máximo)
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
      alert('El archivo es demasiado grande. Tamaño máximo: 5MB');
      return;
    }

    setImageFile(file);

    // Crear preview
    const reader = new FileReader();
    reader.onload = (event) => {
      setImagePreview(event.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleRemoveImage = () => {
    setImageFile(null);
    setImagePreview('');
    setFormData(prev => ({
      ...prev,
      imagen_path: ''
    }));
  };

  const uploadImage = async (productId: string): Promise<string | null> => {
    if (!imageFile) return null;

    setUploadingImage(true);
    
    try {
      const imagePath = await ProductService.uploadProductImage(productId, imageFile);
      return imagePath;
    } catch (error: any) {
      console.error('Error uploading image:', error);
      alert(error.message || 'Error al subir la imagen. Inténtelo de nuevo.');
      return null;
    } finally {
      setUploadingImage(false);
    }
  };

  const handleClose = () => {
    setValidationErrors({});
    setImageFile(null);
    setImagePreview('');
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

          {/* Sección de imagen del producto */}
          <Grid item xs={12}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Imagen del Producto
            </Typography>
            
            {/* Área de carga de imagen */}
            <Box
              sx={{
                border: '2px dashed #ccc',
                borderRadius: 2,
                p: 3,
                textAlign: 'center',
                backgroundColor: imageFile || imagePreview ? '#f9f9f9' : 'transparent',
                transition: 'all 0.3s ease',
                '&:hover': {
                  borderColor: '#1976d2',
                  backgroundColor: '#f5f5f5',
                },
              }}
            >
              {imagePreview ? (
                <Box>
                  <Card sx={{ maxWidth: 200, margin: '0 auto', mb: 2 }}>
                    <CardMedia
                      component="img"
                      height="140"
                      image={imagePreview}
                      alt="Vista previa"
                      sx={{ objectFit: 'cover' }}
                    />
                  </Card>
                  
                  <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
                    <Button
                      variant="outlined"
                      component="label"
                      startIcon={<CloudUpload />}
                      disabled={loading || uploadingImage}
                    >
                      Cambiar Imagen
                      <input
                        type="file"
                        hidden
                        accept="image/*"
                        onChange={handleImageChange}
                      />
                    </Button>
                    
                    <IconButton
                      color="error"
                      onClick={handleRemoveImage}
                      disabled={loading || uploadingImage}
                    >
                      <Delete />
                    </IconButton>
                  </Box>
                </Box>
              ) : (
                <Box>
                  <Image sx={{ fontSize: 48, color: '#ccc', mb: 2 }} />
                  <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                    Arrastra una imagen aquí o haz clic para seleccionar
                  </Typography>
                  <Button
                    variant="outlined"
                    component="label"
                    startIcon={<CloudUpload />}
                    disabled={loading || uploadingImage}
                  >
                    Seleccionar Imagen
                    <input
                      type="file"
                      hidden
                      accept="image/*"
                      onChange={handleImageChange}
                    />
                  </Button>
                </Box>
              )}
              
              {uploadingImage && (
                <Box sx={{ mt: 2 }}>
                  <CircularProgress size={24} />
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Subiendo imagen...
                  </Typography>
                </Box>
              )}
            </Box>
            
            <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
              Formatos soportados: JPG, PNG, GIF, WEBP. Tamaño máximo: 5MB
            </Typography>
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
              name="stock_inicial"
              label="Stock Inicial"
              type="number"
              fullWidth
              value={formData.stock_inicial}
              onChange={handleChange}
              error={!!validationErrors.stock_inicial}
              helperText={validationErrors.stock_inicial || (isEditing ? 'Use la gestión de inventario para modificar stock' : '')}
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