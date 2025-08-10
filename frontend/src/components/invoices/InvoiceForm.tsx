/**
 * Formulario para crear y editar facturas
 * Incluye búsqueda de clientes, productos y cálculos automáticos
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Divider,
  Autocomplete,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Card,
  CardContent
} from '@mui/material';
import {
  Save as SaveIcon,
  Cancel as CancelIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Receipt as ReceiptIcon,
  Calculate as CalculateIcon
} from '@mui/icons-material';
import { InvoicesService, InvoiceCreate, InvoiceUpdate, InvoiceDetailCreate } from '../../services/invoicesService';
import { ClientsService } from '../../services/clientsService';
import { ProductService } from '../../services/productService';
import { Invoice, InvoiceType, Client, Product } from '../../types';

interface InvoiceFormProps {
  open: boolean;
  onClose: () => void;
  onSave: () => void;
  invoice?: Invoice | null;
}

interface FormData {
  cliente_id: string;
  tipo_factura: InvoiceType | '';
  fecha_emision: string;
  fecha_vencimiento: string;
  observaciones: string;
  detalles: InvoiceDetailCreate[];
}

interface FormErrors {
  cliente_id?: string;
  tipo_factura?: string;
  fecha_emision?: string;
  detalles?: string;
}

const InvoiceForm: React.FC<InvoiceFormProps> = ({
  open,
  onClose,
  onSave,
  invoice
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);

  const [formData, setFormData] = useState<FormData>({
    cliente_id: '',
    tipo_factura: '',
    fecha_emision: new Date().toISOString().split('T')[0],
    fecha_vencimiento: '',
    observaciones: '',
    detalles: []
  });

  const [errors, setErrors] = useState<FormErrors>({});

  // Efecto para cargar datos del invoice en modo edición
  useEffect(() => {
    if (open) {
      if (invoice) {
        console.log('Cargando factura para edición:', invoice);
        setFormData({
          cliente_id: invoice.cliente_id || '',
          tipo_factura: invoice.tipo_factura,
          fecha_emision: invoice.fecha_emision.split('T')[0],
          fecha_vencimiento: invoice.fecha_vencimiento ? invoice.fecha_vencimiento.split('T')[0] : '',
          observaciones: invoice.observaciones || '',
          detalles: invoice.detalles?.map(d => ({
            producto_id: d.producto_id || '',
            descripcion_producto: d.descripcion_producto,
            cantidad: d.cantidad,
            precio_unitario: d.precio_unitario,
            descuento_porcentaje: d.descuento_porcentaje,
            impuesto_porcentaje: d.porcentaje_iva || 19
          })) || []
        });
        // Create a client object from the invoice data
        const clientFromInvoice = invoice.cliente_nombre ? {
          id: invoice.cliente_id,
          nombre_completo: invoice.cliente_nombre,
          numero_documento: invoice.cliente_documento || '',
          email: invoice.cliente_email || '',
          telefono: invoice.cliente_telefono || '',
          direccion: invoice.cliente_direccion || '',
          tipo_documento: 'CEDULA' as any,
          tipo_cliente: 'PERSONA_NATURAL' as any,
          is_active: true,
          created_at: new Date().toISOString()
        } : null;
        setSelectedClient(clientFromInvoice);
      } else {
        // Reset form for new invoice
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 30); // 30 días por defecto
        
        setFormData({
          cliente_id: '',
          tipo_factura: InvoiceType.VENTA,
          fecha_emision: new Date().toISOString().split('T')[0],
          fecha_vencimiento: tomorrow.toISOString().split('T')[0],
          observaciones: '',
          detalles: []
        });
        setSelectedClient(null);
      }
      setErrors({});
      setError(null);
    }
  }, [invoice, open]);

  // Cargar clientes y productos
  useEffect(() => {
    if (open) {
      loadInitialData();
    }
  }, [open]);

  const loadInitialData = async () => {
    try {
      const [clientsResponse, productsResponse] = await Promise.all([
        ClientsService.getClients({ limit: 100, only_active: true }),
        ProductService.getProducts({ limit: 100, only_active: true })
      ]);

      setClients(clientsResponse.items || []);
      setProducts(productsResponse.items || []);
    } catch (error) {
      console.error('Error al cargar datos iniciales:', error);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.cliente_id) {
      newErrors.cliente_id = 'Debe seleccionar un cliente';
    }

    if (!formData.tipo_factura) {
      newErrors.tipo_factura = 'Debe seleccionar el tipo de factura';
    }

    if (!formData.fecha_emision) {
      newErrors.fecha_emision = 'La fecha de emisión es requerida';
    }

    if (formData.detalles.length === 0) {
      newErrors.detalles = 'Debe agregar al menos un producto';
    }

    // Validar detalles
    const detailErrors = InvoicesService.validateInvoiceDetails(formData.detalles);
    if (detailErrors.length > 0) {
      newErrors.detalles = detailErrors.join(', ');
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: keyof FormData) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | { target: { value: unknown } }
  ) => {
    const value = event.target.value;
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  const handleClientChange = (client: Client | null) => {
    setSelectedClient(client);
    setFormData(prev => ({ 
      ...prev, 
      cliente_id: client?.id || '' 
    }));
    
    if (errors.cliente_id) {
      setErrors(prev => ({ ...prev, cliente_id: undefined }));
    }
  };

  const handleAddDetail = () => {
    setFormData(prev => ({
      ...prev,
      detalles: [
        ...prev.detalles,
        {
          producto_id: '',
          descripcion_producto: '',
          cantidad: 1,
          precio_unitario: 0,
          descuento_porcentaje: 0,
          impuesto_porcentaje: 19 // IVA por defecto en Colombia
        }
      ]
    }));
  };

  const handleRemoveDetail = (index: number) => {
    setFormData(prev => ({
      ...prev,
      detalles: prev.detalles.filter((_, i) => i !== index)
    }));
  };

  const handleDetailChange = (index: number, field: keyof InvoiceDetailCreate, value: any) => {
    setFormData(prev => ({
      ...prev,
      detalles: prev.detalles.map((detail, i) => 
        i === index ? { ...detail, [field]: value } : detail
      )
    }));
  };

  const handleProductSelect = (index: number, product: Product | null) => {
    if (product) {
      handleDetailChange(index, 'producto_id', product.id);
      handleDetailChange(index, 'descripcion_producto', product.nombre);
      handleDetailChange(index, 'precio_unitario', product.precio_publico);
    }
  };

  const calculateTotals = () => {
    return InvoicesService.calculateInvoiceTotal(formData.detalles);
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (invoice) {
        // Actualizar factura existente
        const updateData: InvoiceUpdate = {
          fecha_vencimiento: formData.fecha_vencimiento || undefined,
          observaciones: formData.observaciones || undefined,
          detalles: formData.detalles
        };
        await InvoicesService.updateInvoice(invoice.id, updateData);
      } else {
        // Crear nueva factura
        const createData: InvoiceCreate = {
          cliente_id: formData.cliente_id,
          tipo_factura: formData.tipo_factura as InvoiceType,
          fecha_emision: formData.fecha_emision,
          fecha_vencimiento: formData.fecha_vencimiento || undefined,
          observaciones: formData.observaciones || undefined,
          detalles: formData.detalles
        };
        await InvoicesService.createInvoice(createData);
      }

      onSave();
    } catch (error: any) {
      console.error('Error al guardar factura:', error);
      
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const totals = calculateTotals();

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { minHeight: '80vh' }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={2}>
          <ReceiptIcon color="primary" />
          <Typography variant="h6">
            {invoice ? 'Editar Factura' : 'Nueva Factura'}
          </Typography>
        </Box>
      </DialogTitle>

      <DialogContent dividers sx={{ p: 3 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3}>
          {/* Información General */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom color="primary">
              Información General
            </Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>

          <Grid item xs={12} md={6}>
            <Autocomplete
              options={clients}
              getOptionLabel={(client) => `${client.nombre_completo} - ${client.numero_documento}`}
              value={selectedClient}
              onChange={(_, newValue) => handleClientChange(newValue)}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Cliente *"
                  error={!!errors.cliente_id}
                  helperText={errors.cliente_id}
                  InputProps={{
                    ...params.InputProps,
                    startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                  }}
                />
              )}
              disabled={loading || !!invoice} // No permitir cambiar cliente en edición
              noOptionsText="No se encontraron clientes"
              loadingText="Cargando clientes..."
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth error={!!errors.tipo_factura}>
              <InputLabel>Tipo de Factura *</InputLabel>
              <Select
                value={formData.tipo_factura}
                label="Tipo de Factura *"
                onChange={handleInputChange('tipo_factura')}
                disabled={loading || !!invoice} // No permitir cambiar tipo en edición
              >
                <MenuItem value={InvoiceType.VENTA}>Venta</MenuItem>
                <MenuItem value={InvoiceType.SERVICIO}>Servicio</MenuItem>
              </Select>
              {errors.tipo_factura && (
                <FormHelperText>{errors.tipo_factura}</FormHelperText>
              )}
            </FormControl>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="date"
              label="Fecha de Emisión *"
              value={formData.fecha_emision}
              onChange={handleInputChange('fecha_emision')}
              error={!!errors.fecha_emision}
              helperText={errors.fecha_emision}
              InputLabelProps={{ shrink: true }}
              disabled={loading || !!invoice} // No permitir cambiar fecha emisión en edición
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="date"
              label="Fecha de Vencimiento"
              value={formData.fecha_vencimiento}
              onChange={handleInputChange('fecha_vencimiento')}
              InputLabelProps={{ shrink: true }}
              disabled={loading}
              helperText="Opcional - dejar vacío si no aplica"
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={2}
              label="Observaciones"
              value={formData.observaciones}
              onChange={handleInputChange('observaciones')}
              disabled={loading}
              placeholder="Observaciones adicionales..."
            />
          </Grid>

          {/* Detalles de la Factura */}
          <Grid item xs={12}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6" color="primary">
                Detalles de la Factura
              </Typography>
              <Button
                startIcon={<AddIcon />}
                onClick={handleAddDetail}
                variant="outlined"
                size="small"
                disabled={loading}
              >
                Agregar Producto
              </Button>
            </Box>
            <Divider sx={{ mb: 2 }} />
            
            {errors.detalles && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {errors.detalles}
              </Alert>
            )}
          </Grid>

          <Grid item xs={12}>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Producto *</TableCell>
                    <TableCell width="100px">Cantidad *</TableCell>
                    <TableCell width="120px">Precio Unit. *</TableCell>
                    <TableCell width="100px">Desc. %</TableCell>
                    <TableCell width="100px">IVA %</TableCell>
                    <TableCell width="120px" align="right">Total</TableCell>
                    <TableCell width="60px">Acciones</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {formData.detalles.map((detail, index) => {
                    const lineTotal = InvoicesService.calculateLineTotal(
                      detail.cantidad,
                      detail.precio_unitario,
                      detail.descuento_porcentaje,
                      detail.impuesto_porcentaje || 0
                    );

                    return (
                      <TableRow key={index}>
                        <TableCell>
                          <Autocomplete
                            size="small"
                            options={products}
                            getOptionLabel={(product) => `${product.nombre} (${product.sku})`}
                            value={products.find(p => p.id === detail.producto_id) || null}
                            onChange={(_, product) => handleProductSelect(index, product)}
                            renderInput={(params) => (
                              <TextField
                                {...params}
                                variant="outlined"
                                placeholder="Buscar producto..."
                                value={detail.descripcion_producto}
                                onChange={(e) => handleDetailChange(index, 'descripcion_producto', e.target.value)}
                              />
                            )}
                            disabled={loading}
                            noOptionsText="No se encontraron productos"
                            sx={{ minWidth: 200 }}
                          />
                        </TableCell>
                        <TableCell>
                          <TextField
                            size="small"
                            type="number"
                            value={detail.cantidad}
                            onChange={(e) => handleDetailChange(index, 'cantidad', Number(e.target.value))}
                            inputProps={{ min: 1, step: 1 }}
                            disabled={loading}
                            fullWidth
                          />
                        </TableCell>
                        <TableCell>
                          <TextField
                            size="small"
                            type="number"
                            value={detail.precio_unitario}
                            onChange={(e) => handleDetailChange(index, 'precio_unitario', Number(e.target.value))}
                            inputProps={{ min: 0, step: 0.01 }}
                            disabled={loading}
                            fullWidth
                          />
                        </TableCell>
                        <TableCell>
                          <TextField
                            size="small"
                            type="number"
                            value={detail.descuento_porcentaje}
                            onChange={(e) => handleDetailChange(index, 'descuento_porcentaje', Number(e.target.value))}
                            inputProps={{ min: 0, max: 100, step: 0.01 }}
                            disabled={loading}
                            fullWidth
                          />
                        </TableCell>
                        <TableCell>
                          <TextField
                            size="small"
                            type="number"
                            value={detail.impuesto_porcentaje}
                            onChange={(e) => handleDetailChange(index, 'impuesto_porcentaje', Number(e.target.value))}
                            inputProps={{ min: 0, max: 100, step: 0.01 }}
                            disabled={loading}
                            fullWidth
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" fontWeight="500">
                            {InvoicesService.formatCurrency(lineTotal.total)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Tooltip title="Eliminar">
                            <IconButton
                              size="small"
                              onClick={() => handleRemoveDetail(index)}
                              disabled={loading}
                              color="error"
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                  {formData.detalles.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>
                        No hay productos agregados. Haz clic en "Agregar Producto" para comenzar.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Grid>

          {/* Totales */}
          {formData.detalles.length > 0 && (
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                <Card sx={{ minWidth: 300 }}>
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={1} mb={2}>
                      <CalculateIcon color="primary" />
                      <Typography variant="h6" color="primary">Resumen</Typography>
                    </Box>
                    <Grid container spacing={1}>
                      <Grid item xs={8}>
                        <Typography variant="body2">Subtotal:</Typography>
                      </Grid>
                      <Grid item xs={4} sx={{ textAlign: 'right' }}>
                        <Typography variant="body2">
                          {InvoicesService.formatCurrency(totals.subtotal)}
                        </Typography>
                      </Grid>

                      <Grid item xs={8}>
                        <Typography variant="body2" color="success.main">Descuentos:</Typography>
                      </Grid>
                      <Grid item xs={4} sx={{ textAlign: 'right' }}>
                        <Typography variant="body2" color="success.main">
                          -{InvoicesService.formatCurrency(totals.totalDescuentos)}
                        </Typography>
                      </Grid>

                      <Grid item xs={8}>
                        <Typography variant="body2">Impuestos:</Typography>
                      </Grid>
                      <Grid item xs={4} sx={{ textAlign: 'right' }}>
                        <Typography variant="body2">
                          +{InvoicesService.formatCurrency(totals.totalImpuestos)}
                        </Typography>
                      </Grid>

                      <Grid item xs={12}>
                        <Divider sx={{ my: 1 }} />
                      </Grid>

                      <Grid item xs={8}>
                        <Typography variant="h6" fontWeight="bold">TOTAL:</Typography>
                      </Grid>
                      <Grid item xs={4} sx={{ textAlign: 'right' }}>
                        <Typography variant="h6" fontWeight="bold">
                          {InvoicesService.formatCurrency(totals.total)}
                        </Typography>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Box>
            </Grid>
          )}
        </Grid>
      </DialogContent>

      <DialogActions sx={{ p: 3 }}>
        <Button
          onClick={onClose}
          disabled={loading}
          startIcon={<CancelIcon />}
        >
          Cancelar
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading || formData.detalles.length === 0}
          startIcon={loading ? <CircularProgress size={16} /> : <SaveIcon />}
        >
          {loading ? 'Guardando...' : (invoice ? 'Actualizar' : 'Crear Factura')}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default InvoiceForm;