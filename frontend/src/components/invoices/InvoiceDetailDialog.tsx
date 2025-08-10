/**
 * Diálogo de vista detallada de factura
 * Muestra información completa, detalles de línea y opciones de pago
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Grid,
  Typography,
  Box,
  Chip,
  Card,
  CardContent,
  Alert,
  IconButton,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Divider,
  TextField,
  MenuItem
} from '@mui/material';
import {
  Close as CloseIcon,
  Edit as EditIcon,
  Receipt as ReceiptIcon,
  Person as PersonIcon,
  CalendarToday as CalendarIcon,
  AttachMoney as MoneyIcon,
  Payment as PaymentIcon,
  Print as PrintIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import { InvoicesService, PaymentData } from '../../services/invoicesService';
import { Invoice, InvoiceStatus, InvoiceType } from '../../types';

interface InvoiceDetailDialogProps {
  invoice: Invoice | null;
  open: boolean;
  onClose: () => void;
  onEdit?: (invoice: Invoice) => void;
  onMarkAsPaid?: (invoice: Invoice, paymentData: PaymentData) => Promise<void>;
}

const InvoiceDetailDialog: React.FC<InvoiceDetailDialogProps> = ({
  invoice,
  open,
  onClose,
  onEdit,
  onMarkAsPaid
}) => {
  const [showPaymentForm, setShowPaymentForm] = useState(false);
  const [paymentData, setPaymentData] = useState<PaymentData>({
    forma_pago: 'EFECTIVO',
    fecha_pago: new Date().toISOString().split('T')[0],
    observaciones: '',
    valor_recibido: undefined
  });

  const handleEdit = () => {
    if (invoice && onEdit) {
      onEdit(invoice);
    }
  };

  const handlePayment = async () => {
    if (invoice && onMarkAsPaid) {
      try {
        await onMarkAsPaid(invoice, paymentData);
        setShowPaymentForm(false);
      } catch (error) {
        // Error handling is done in parent component
      }
    }
  };

  const handlePrint = async () => {
    if (invoice) {
      try {
        const { InvoicePrintUtils } = await import('../../utils/invoicePrint');
        await InvoicePrintUtils.printInvoice(invoice, {
          companyName: 'Sistema de Gestión Empresarial',
          companyAddress: 'Dirección de su empresa',
          companyPhone: 'Teléfono de contacto',
          companyEmail: 'contacto@suempresa.com'
        });
      } catch (error) {
        console.error('Error al imprimir factura:', error);
      }
    }
  };

  const isOverdue = invoice && invoice.fecha_vencimiento && 
    new Date(invoice.fecha_vencimiento) < new Date() && 
    invoice.estado === InvoiceStatus.EMITIDA;

  if (!invoice) return null;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { minHeight: '700px' }
      }}
    >
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box display="flex" alignItems="center" gap={2}>
            <ReceiptIcon color="primary" sx={{ fontSize: 32 }} />
            <Box>
              <Typography variant="h6">
                Factura {InvoicesService.formatInvoiceNumber(invoice.numero_factura)}
              </Typography>
              <Box display="flex" alignItems="center" gap={1}>
                <Chip
                  label={InvoicesService.getInvoiceStatusLabel(invoice.estado)}
                  size="small"
                  color={InvoicesService.getInvoiceStatusColor(invoice.estado)}
                  variant="filled"
                />
                <Chip
                  label={InvoicesService.getInvoiceTypeLabel(invoice.tipo_factura)}
                  size="small"
                  variant="outlined"
                />
                {isOverdue && (
                  <Chip
                    label="VENCIDA"
                    size="small"
                    color="error"
                    variant="filled"
                    icon={<WarningIcon />}
                  />
                )}
              </Box>
            </Box>
          </Box>
          <Box>
            <Tooltip title="Imprimir">
              <IconButton onClick={handlePrint} color="primary">
                <PrintIcon />
              </IconButton>
            </Tooltip>
            {invoice.estado === InvoiceStatus.EMITIDA && onEdit && (
              <Tooltip title="Editar factura">
                <IconButton onClick={handleEdit} color="primary">
                  <EditIcon />
                </IconButton>
              </Tooltip>
            )}
            <IconButton onClick={onClose}>
              <CloseIcon />
            </IconButton>
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        <Grid container spacing={3}>
          {/* Información General */}
          <Grid item xs={12} md={8}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <ReceiptIcon /> Información General
            </Typography>
            <Card variant="outlined">
              <CardContent>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Número de Factura:
                    </Typography>
                    <Typography variant="body1" fontWeight="500">
                      {InvoicesService.formatInvoiceNumber(invoice.numero_factura)}
                    </Typography>
                  </Grid>

                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <CalendarIcon fontSize="small" /> Fecha de Emisión:
                    </Typography>
                    <Typography variant="body1">
                      {new Date(invoice.fecha_emision).toLocaleDateString('es-CO')}
                    </Typography>
                  </Grid>

                  {invoice.fecha_vencimiento && (
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Fecha de Vencimiento:
                      </Typography>
                      <Typography variant="body1" color={isOverdue ? 'error.main' : 'inherit'}>
                        {new Date(invoice.fecha_vencimiento).toLocaleDateString('es-CO')}
                      </Typography>
                    </Grid>
                  )}

                  {invoice.fecha_pago && (
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Fecha de Pago:
                      </Typography>
                      <Typography variant="body1" color="success.main">
                        {new Date(invoice.fecha_pago).toLocaleDateString('es-CO')}
                      </Typography>
                    </Grid>
                  )}

                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Estado:
                    </Typography>
                    <Chip
                      label={InvoicesService.getInvoiceStatusLabel(invoice.estado)}
                      color={InvoicesService.getInvoiceStatusColor(invoice.estado)}
                      variant="filled"
                      size="small"
                    />
                  </Grid>

                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Tipo:
                    </Typography>
                    <Typography variant="body1">
                      {InvoicesService.getInvoiceTypeLabel(invoice.tipo_factura)}
                    </Typography>
                  </Grid>

                  {invoice.observaciones && (
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Observaciones:
                      </Typography>
                      <Typography variant="body1">
                        {invoice.observaciones}
                      </Typography>
                    </Grid>
                  )}
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Información del Cliente */}
          <Grid item xs={12} md={4}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <PersonIcon /> Cliente
            </Typography>
            <Card variant="outlined" sx={{ height: 'fit-content' }}>
              <CardContent>
                <Typography variant="subtitle1" fontWeight="500">
                  {invoice.cliente?.nombre_completo || 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {invoice.cliente?.numero_documento || 'N/A'}
                </Typography>
                {invoice.cliente?.email && (
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    {invoice.cliente.email}
                  </Typography>
                )}
                {invoice.cliente?.telefono && (
                  <Typography variant="body2" color="text.secondary">
                    {invoice.cliente.telefono}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Detalles de la Factura */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Detalles de la Factura
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Producto</TableCell>
                    <TableCell align="center">Cantidad</TableCell>
                    <TableCell align="right">Precio Unit.</TableCell>
                    <TableCell align="right">Descuento</TableCell>
                    <TableCell align="right">Subtotal</TableCell>
                    <TableCell align="right">Impuesto</TableCell>
                    <TableCell align="right">Total</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {invoice.detalles?.map((detalle, index) => {
                    const lineTotal = InvoicesService.calculateLineTotal(
                      detalle.cantidad,
                      detalle.precio_unitario,
                      detalle.descuento_porcentaje,
                      detalle.impuesto_porcentaje
                    );

                    return (
                      <TableRow key={index}>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" fontWeight="500">
                              {detalle.descripcion_producto}
                            </Typography>
                            {detalle.producto?.sku && (
                              <Typography variant="caption" color="text.secondary">
                                SKU: {detalle.producto.sku}
                              </Typography>
                            )}
                          </Box>
                        </TableCell>
                        <TableCell align="center">
                          {detalle.cantidad.toLocaleString()}
                        </TableCell>
                        <TableCell align="right">
                          {InvoicesService.formatCurrency(detalle.precio_unitario)}
                        </TableCell>
                        <TableCell align="right">
                          {detalle.descuento_porcentaje}%
                          <br />
                          <Typography variant="caption" color="success.main">
                            -{InvoicesService.formatCurrency(lineTotal.descuento)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          {InvoicesService.formatCurrency(lineTotal.subtotal)}
                        </TableCell>
                        <TableCell align="right">
                          {detalle.impuesto_porcentaje}%
                          <br />
                          <Typography variant="caption" color="text.secondary">
                            +{InvoicesService.formatCurrency(lineTotal.impuesto)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body1" fontWeight="500">
                            {InvoicesService.formatCurrency(lineTotal.total)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </Grid>

          {/* Totales */}
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Card sx={{ minWidth: 300 }}>
                <CardContent>
                  <Grid container spacing={1}>
                    <Grid item xs={8}>
                      <Typography variant="body2">Subtotal:</Typography>
                    </Grid>
                    <Grid item xs={4} sx={{ textAlign: 'right' }}>
                      <Typography variant="body2">
                        {InvoicesService.formatCurrency(invoice.subtotal)}
                      </Typography>
                    </Grid>

                    <Grid item xs={8}>
                      <Typography variant="body2" color="success.main">Descuentos:</Typography>
                    </Grid>
                    <Grid item xs={4} sx={{ textAlign: 'right' }}>
                      <Typography variant="body2" color="success.main">
                        -{InvoicesService.formatCurrency(invoice.total_descuentos)}
                      </Typography>
                    </Grid>

                    <Grid item xs={8}>
                      <Typography variant="body2">Impuestos:</Typography>
                    </Grid>
                    <Grid item xs={4} sx={{ textAlign: 'right' }}>
                      <Typography variant="body2">
                        +{InvoicesService.formatCurrency(invoice.total_impuestos)}
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
                        {InvoicesService.formatCurrency(invoice.total)}
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Box>
          </Grid>

          {/* Formulario de Pago */}
          {showPaymentForm && invoice.estado === InvoiceStatus.EMITIDA && (
            <Grid item xs={12}>
              <Alert severity="info" sx={{ mb: 2 }}>
                Complete la información del pago para marcar la factura como pagada
              </Alert>
              <Card>
                <CardContent>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        select
                        fullWidth
                        label="Forma de Pago"
                        value={paymentData.forma_pago}
                        onChange={(e) => setPaymentData(prev => ({...prev, forma_pago: e.target.value}))}
                      >
                        <MenuItem value="EFECTIVO">Efectivo</MenuItem>
                        <MenuItem value="TRANSFERENCIA">Transferencia</MenuItem>
                        <MenuItem value="TARJETA_CREDITO">Tarjeta de Crédito</MenuItem>
                        <MenuItem value="TARJETA_DEBITO">Tarjeta de Débito</MenuItem>
                        <MenuItem value="CHEQUE">Cheque</MenuItem>
                      </TextField>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        type="date"
                        label="Fecha de Pago"
                        value={paymentData.fecha_pago}
                        onChange={(e) => setPaymentData(prev => ({...prev, fecha_pago: e.target.value}))}
                        InputLabelProps={{ shrink: true }}
                      />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        type="number"
                        label="Valor Recibido"
                        value={paymentData.valor_recibido || invoice.total}
                        onChange={(e) => setPaymentData(prev => ({...prev, valor_recibido: Number(e.target.value)}))}
                        InputProps={{
                          startAdornment: <Typography sx={{ mr: 1 }}>$</Typography>,
                        }}
                      />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Observaciones"
                        value={paymentData.observaciones}
                        onChange={(e) => setPaymentData(prev => ({...prev, observaciones: e.target.value}))}
                        placeholder="Observaciones del pago..."
                      />
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      </DialogContent>

      <DialogActions sx={{ p: 3 }}>
        {invoice.estado === InvoiceStatus.EMITIDA && (
          <>
            {!showPaymentForm && onMarkAsPaid && (
              <Button
                onClick={() => setShowPaymentForm(true)}
                variant="contained"
                startIcon={<PaymentIcon />}
                color="success"
              >
                Marcar como Pagada
              </Button>
            )}
            
            {showPaymentForm && (
              <>
                <Button
                  onClick={() => setShowPaymentForm(false)}
                  sx={{ mr: 1 }}
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handlePayment}
                  variant="contained"
                  startIcon={<PaymentIcon />}
                  color="success"
                >
                  Confirmar Pago
                </Button>
              </>
            )}

            {onEdit && !showPaymentForm && (
              <Button
                onClick={handleEdit}
                variant="outlined"
                startIcon={<EditIcon />}
                sx={{ ml: 1 }}
              >
                Editar
              </Button>
            )}
          </>
        )}
        
        <Button onClick={onClose} sx={{ ml: 'auto' }}>
          Cerrar
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default InvoiceDetailDialog;