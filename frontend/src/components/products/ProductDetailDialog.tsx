/**
 * Diálogo de detalles del producto
 */

import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Grid,
  Chip,
  Divider,
  Avatar,
  Card,
  CardContent,
} from '@mui/material';
import {
  Inventory,
  AttachMoney,
  CalendarToday,
  QrCode2,
  Image,
  Description,
  Warning,
} from '@mui/icons-material';
import { Product } from '../../types';

interface ProductDetailDialogProps {
  open: boolean;
  onClose: () => void;
  onEdit?: (product: Product) => void;
  product: Product | null;
}

const ProductDetailDialog: React.FC<ProductDetailDialogProps> = ({
  open,
  onClose,
  onEdit,
  product,
}) => {
  if (!product) return null;

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('es-CO', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStockColor = (stock: number): 'error' | 'warning' | 'success' => {
    if (stock === 0) return 'error';
    if (stock <= 10) return 'warning';
    return 'success';
  };

  const getStockStatus = (stock: number): string => {
    if (stock === 0) return 'Sin stock';
    if (stock <= 10) return 'Stock bajo';
    return 'Stock disponible';
  };

  const marginPercent = product.precio_publico > 0 
    ? ((product.precio_publico - product.precio_base) / product.precio_base * 100).toFixed(1)
    : '0';

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="md" 
      fullWidth
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Inventory />
          Detalles del Producto
        </Box>
      </DialogTitle>

      <DialogContent>
        <Grid container spacing={3}>
          {/* Imagen y información básica */}
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center', mb: 2 }}>
              <Avatar
                src={product.url_foto || undefined}
                alt={product.nombre}
                variant="rounded"
                sx={{ 
                  width: 150, 
                  height: 150, 
                  mx: 'auto', 
                  mb: 2,
                  bgcolor: 'grey.100',
                }}
              >
                <Inventory sx={{ fontSize: 64 }} />
              </Avatar>
              
              <Chip
                label={product.is_active ? 'Activo' : 'Inactivo'}
                color={product.is_active ? 'success' : 'default'}
                sx={{ mb: 1 }}
              />
              
              <Chip
                label={getStockStatus(product.stock)}
                color={getStockColor(product.stock)}
                icon={product.stock === 0 ? <Warning /> : <Inventory />}
              />
            </Box>
          </Grid>

          {/* Información detallada */}
          <Grid item xs={12} md={8}>
            <Typography variant="h5" gutterBottom>
              {product.nombre}
            </Typography>

            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                <QrCode2 sx={{ fontSize: 16, mr: 1, verticalAlign: 'middle' }} />
                SKU: {product.sku}
              </Typography>
              
              <Typography variant="body2" color="text.secondary">
                <CalendarToday sx={{ fontSize: 16, mr: 1, verticalAlign: 'middle' }} />
                Creado: {formatDate(product.created_at)}
              </Typography>
            </Box>

            {product.descripcion && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  <Description sx={{ fontSize: 16, mr: 1, verticalAlign: 'middle' }} />
                  Descripción:
                </Typography>
                <Typography variant="body2">
                  {product.descripcion}
                </Typography>
              </Box>
            )}

            {product.url_foto && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  <Image sx={{ fontSize: 16, mr: 1, verticalAlign: 'middle' }} />
                  Imagen:
                </Typography>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    wordBreak: 'break-all',
                    fontSize: '0.875rem',
                  }}
                >
                  {product.url_foto}
                </Typography>
              </Box>
            )}
          </Grid>

          {/* Información de precios y stock */}
          <Grid item xs={12}>
            <Divider sx={{ my: 2 }} />
            
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Card variant="outlined">
                  <CardContent sx={{ textAlign: 'center' }}>
                    <AttachMoney color="primary" />
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Precio Base
                    </Typography>
                    <Typography variant="h6">
                      {formatCurrency(product.precio_base)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <Card variant="outlined">
                  <CardContent sx={{ textAlign: 'center' }}>
                    <AttachMoney color="success" />
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Precio Público
                    </Typography>
                    <Typography variant="h6">
                      {formatCurrency(product.precio_publico)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <Card variant="outlined">
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Inventory color="warning" />
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Stock Actual
                    </Typography>
                    <Typography variant="h6">
                      {product.stock} unidades
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <Card variant="outlined">
                  <CardContent sx={{ textAlign: 'center' }}>
                    <AttachMoney color="info" />
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Margen
                    </Typography>
                    <Typography variant="h6">
                      {marginPercent}%
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>
          Cerrar
        </Button>
        {onEdit && (
          <Button 
            variant="contained" 
            onClick={() => {
              onEdit(product);
              onClose();
            }}
          >
            Editar Producto
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default ProductDetailDialog;