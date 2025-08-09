/**
 * Diálogo de vista detallada de cliente
 * Muestra información completa y estadísticas del cliente
 */

import React, { useState, useEffect } from 'react';
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
  CircularProgress,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Close as CloseIcon,
  Edit as EditIcon,
  Person as PersonIcon,
  Business as BusinessIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  LocationOn as LocationIcon,
  CalendarToday as CalendarIcon,
  Assessment as AssessmentIcon,
  Receipt as ReceiptIcon,
  AttachMoney as MoneyIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import { ClientsService, ClientStats } from '../../services/clientsService';
import { Client, ClientType } from '../../types';

interface ClientDetailDialogProps {
  client: Client | null;
  open: boolean;
  onClose: () => void;
  onEdit?: (client: Client) => void;
}

const ClientDetailDialog: React.FC<ClientDetailDialogProps> = ({
  client,
  open,
  onClose,
  onEdit
}) => {
  const [stats, setStats] = useState<ClientStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (client && open) {
      loadClientStats();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [client, open]);

  const loadClientStats = async () => {
    if (!client) return;

    try {
      setLoading(true);
      setError(null);
      
      const clientStats = await ClientsService.getClientStats(client.id);
      setStats(clientStats);
    } catch (error: any) {
      console.error('Error al cargar estadísticas del cliente:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    if (client && onEdit) {
      onEdit(client);
    }
  };

  const getEstadoCarteraColor = (estado: string) => {
    switch (estado) {
      case 'AL_DIA':
        return 'success';
      case 'VENCIDA':
        return 'error';
      case 'PARCIAL':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getEstadoCarteraLabel = (estado: string) => {
    switch (estado) {
      case 'AL_DIA':
        return 'Al Día';
      case 'VENCIDA':
        return 'Vencida';
      case 'PARCIAL':
        return 'Parcial';
      default:
        return estado;
    }
  };

  if (!client) return null;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: '600px' }
      }}
    >
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box display="flex" alignItems="center" gap={2}>
            {client.tipo_cliente === ClientType.EMPRESA ? (
              <BusinessIcon color="primary" sx={{ fontSize: 32 }} />
            ) : (
              <PersonIcon color="primary" sx={{ fontSize: 32 }} />
            )}
            <Box>
              <Typography variant="h6">
                {client.nombre_completo}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {ClientsService.getDocumentTypeLabel(client.tipo_documento)}: {client.numero_documento}
              </Typography>
            </Box>
          </Box>
          <Box>
            {onEdit && (
              <Tooltip title="Editar cliente">
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
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3}>
          {/* Información Básica */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <PersonIcon /> Información Básica
            </Typography>
            <Card variant="outlined">
              <CardContent>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Box display="flex" alignItems="center" gap={1} mb={1}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Tipo de Cliente:
                      </Typography>
                      <Chip
                        label={ClientsService.getClientTypeLabel(client.tipo_cliente)}
                        size="small"
                        color={client.tipo_cliente === ClientType.EMPRESA ? 'primary' : 'success'}
                        variant="outlined"
                      />
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <Box display="flex" alignItems="center" gap={1} mb={1}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Estado:
                      </Typography>
                      <Chip
                        label={client.is_active ? 'Activo' : 'Inactivo'}
                        size="small"
                        color={client.is_active ? 'success' : 'error'}
                        variant="filled"
                      />
                    </Box>
                  </Grid>

                  {client.nombre_comercial && (
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Nombre Comercial:
                      </Typography>
                      <Typography variant="body1">
                        {client.nombre_comercial}
                      </Typography>
                    </Grid>
                  )}

                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <CalendarIcon fontSize="small" /> Fecha de Registro:
                    </Typography>
                    <Typography variant="body1">
                      {new Date(client.created_at).toLocaleDateString('es-CO', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })}
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Información de Contacto */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Información de Contacto
            </Typography>
            <Card variant="outlined">
              <CardContent>
                <Grid container spacing={2}>
                  {client.email && (
                    <Grid item xs={12} sm={6}>
                      <Box display="flex" alignItems="center" gap={1}>
                        <EmailIcon color="action" />
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">
                            Email:
                          </Typography>
                          <Typography variant="body1">
                            {client.email}
                          </Typography>
                        </Box>
                      </Box>
                    </Grid>
                  )}

                  {client.telefono && (
                    <Grid item xs={12} sm={6}>
                      <Box display="flex" alignItems="center" gap={1}>
                        <PhoneIcon color="action" />
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">
                            Teléfono:
                          </Typography>
                          <Typography variant="body1">
                            {client.telefono}
                          </Typography>
                        </Box>
                      </Box>
                    </Grid>
                  )}

                  {client.direccion && (
                    <Grid item xs={12}>
                      <Box display="flex" alignItems="flex-start" gap={1}>
                        <LocationIcon color="action" />
                        <Box>
                          <Typography variant="subtitle2" color="text.secondary">
                            Dirección:
                          </Typography>
                          <Typography variant="body1">
                            {client.direccion}
                          </Typography>
                        </Box>
                      </Box>
                    </Grid>
                  )}

                  {!client.email && !client.telefono && !client.direccion && (
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary" textAlign="center">
                        No hay información de contacto adicional registrada
                      </Typography>
                    </Grid>
                  )}
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Estadísticas */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AssessmentIcon /> Estadísticas de Compras
            </Typography>
            
            {loading ? (
              <Box display="flex" justifyContent="center" p={4}>
                <CircularProgress />
              </Box>
            ) : stats ? (
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ bgcolor: 'primary.main', color: 'white' }}>
                    <CardContent>
                      <Box display="flex" alignItems="center" justifyContent="space-between">
                        <Box>
                          <Typography variant="h6" fontWeight="bold">
                            {stats.total_facturas}
                          </Typography>
                          <Typography variant="body2" sx={{ opacity: 0.9 }}>
                            Total Facturas
                          </Typography>
                        </Box>
                        <ReceiptIcon sx={{ fontSize: 32, opacity: 0.8 }} />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ bgcolor: 'success.main', color: 'white' }}>
                    <CardContent>
                      <Box display="flex" alignItems="center" justifyContent="space-between">
                        <Box>
                          <Typography variant="h6" fontWeight="bold">
                            {ClientsService.formatCurrency(stats.total_compras)}
                          </Typography>
                          <Typography variant="body2" sx={{ opacity: 0.9 }}>
                            Total Compras
                          </Typography>
                        </Box>
                        <MoneyIcon sx={{ fontSize: 32, opacity: 0.8 }} />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ bgcolor: 'info.main', color: 'white' }}>
                    <CardContent>
                      <Box display="flex" alignItems="center" justifyContent="space-between">
                        <Box>
                          <Typography variant="h6" fontWeight="bold">
                            {ClientsService.formatCurrency(stats.promedio_compra)}
                          </Typography>
                          <Typography variant="body2" sx={{ opacity: 0.9 }}>
                            Promedio Compra
                          </Typography>
                        </Box>
                        <AssessmentIcon sx={{ fontSize: 32, opacity: 0.8 }} />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                  <Card sx={{ bgcolor: getEstadoCarteraColor(stats.estado_cartera) === 'error' ? 'error.main' : 
                                  getEstadoCarteraColor(stats.estado_cartera) === 'warning' ? 'warning.main' : 'success.main', 
                              color: 'white' }}>
                    <CardContent>
                      <Box display="flex" alignItems="center" justifyContent="space-between">
                        <Box>
                          <Typography variant="h6" fontWeight="bold">
                            {getEstadoCarteraLabel(stats.estado_cartera)}
                          </Typography>
                          <Typography variant="body2" sx={{ opacity: 0.9 }}>
                            Estado Cartera
                          </Typography>
                        </Box>
                        <ScheduleIcon sx={{ fontSize: 32, opacity: 0.8 }} />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                {stats.ultima_compra && (
                  <Grid item xs={12}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" color="text.secondary">
                          Última Compra:
                        </Typography>
                        <Typography variant="body1">
                          {new Date(stats.ultima_compra).toLocaleDateString('es-CO', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric'
                          })}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                )}

                {stats.saldo_pendiente > 0 && (
                  <Grid item xs={12}>
                    <Alert severity="warning">
                      <Typography variant="subtitle2">
                        Saldo Pendiente: {ClientsService.formatCurrency(stats.saldo_pendiente)}
                      </Typography>
                    </Alert>
                  </Grid>
                )}
              </Grid>
            ) : (
              <Alert severity="info">
                No se pudieron cargar las estadísticas del cliente
              </Alert>
            )}
          </Grid>
        </Grid>
      </DialogContent>

      <DialogActions sx={{ p: 3 }}>
        {onEdit && (
          <Button
            onClick={handleEdit}
            variant="contained"
            startIcon={<EditIcon />}
            sx={{ mr: 'auto' }}
          >
            Editar Cliente
          </Button>
        )}
        <Button onClick={onClose}>
          Cerrar
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ClientDetailDialog;