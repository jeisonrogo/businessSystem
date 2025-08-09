/**
 * Formulario para crear y editar clientes
 * Incluye validaciones de negocio y UX optimizada
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
  Divider
} from '@mui/material';
import {
  Save as SaveIcon,
  Cancel as CancelIcon,
  Person as PersonIcon,
  Business as BusinessIcon
} from '@mui/icons-material';
import { ClientsService, ClientCreate, ClientUpdate } from '../../services/clientsService';
import { Client, ClientType, DocumentType } from '../../types';

interface ClientFormProps {
  open: boolean;
  onClose: () => void;
  onSave: () => void;
  client?: Client | null;
}

interface FormData {
  tipo_documento: DocumentType | '';
  numero_documento: string;
  nombre_completo: string;
  nombre_comercial: string;
  email: string;
  telefono: string;
  direccion: string;
  tipo_cliente: ClientType | '';
}

interface FormErrors {
  tipo_documento?: string;
  numero_documento?: string;
  nombre_completo?: string;
  email?: string;
  tipo_cliente?: string;
}

const ClientForm: React.FC<ClientFormProps> = ({
  open,
  onClose,
  onSave,
  client
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<FormData>({
    tipo_documento: '',
    numero_documento: '',
    nombre_completo: '',
    nombre_comercial: '',
    email: '',
    telefono: '',
    direccion: '',
    tipo_cliente: '',
  });

  const [errors, setErrors] = useState<FormErrors>({});

  // Efecto para cargar datos del cliente en modo edición
  useEffect(() => {
    if (client) {
      setFormData({
        tipo_documento: client.tipo_documento,
        numero_documento: client.numero_documento,
        nombre_completo: client.nombre_completo,
        nombre_comercial: client.nombre_comercial || '',
        email: client.email || '',
        telefono: client.telefono || '',
        direccion: client.direccion || '',
        tipo_cliente: client.tipo_cliente,
      });
    } else {
      setFormData({
        tipo_documento: '',
        numero_documento: '',
        nombre_completo: '',
        nombre_comercial: '',
        email: '',
        telefono: '',
        direccion: '',
        tipo_cliente: '',
      });
    }
    setErrors({});
    setError(null);
  }, [client, open]);

  // Handlers
  const handleChange = (field: keyof FormData) => (event: any) => {
    const value = event.target.value;
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Limpiar errores del campo que se está editando
    if (errors[field as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }

    // Auto-formatear NIT si es necesario
    if (field === 'numero_documento' && formData.tipo_documento === DocumentType.NIT) {
      if (value.length === 9 && !value.includes('-')) {
        const formatted = ClientsService.formatDocumentNumber(DocumentType.NIT, value);
        setFormData(prev => ({ ...prev, numero_documento: formatted }));
      }
    }

    // Suggerir tipo de cliente basado en tipo de documento
    if (field === 'tipo_documento') {
      if (value === DocumentType.NIT && !formData.tipo_cliente) {
        setFormData(prev => ({ ...prev, tipo_cliente: ClientType.EMPRESA }));
      } else if (value === DocumentType.CC && !formData.tipo_cliente) {
        setFormData(prev => ({ ...prev, tipo_cliente: ClientType.PERSONA_NATURAL }));
      }
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Validaciones requeridas
    if (!formData.tipo_documento) {
      newErrors.tipo_documento = 'El tipo de documento es requerido';
    }

    if (!formData.numero_documento.trim()) {
      newErrors.numero_documento = 'El número de documento es requerido';
    } else if (formData.tipo_documento && !ClientsService.validateDocumentNumber(formData.tipo_documento, formData.numero_documento)) {
      newErrors.numero_documento = 'El formato del documento no es válido';
    }

    if (!formData.nombre_completo.trim()) {
      newErrors.nombre_completo = 'El nombre completo es requerido';
    }

    if (!formData.tipo_cliente) {
      newErrors.tipo_cliente = 'El tipo de cliente es requerido';
    }

    // Validación de email si se proporciona
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'El formato del email no es válido';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    try {
      setLoading(true);
      setError(null);

      if (client) {
        // Actualizar cliente existente
        const updateData: ClientUpdate = {};
        
        if (formData.nombre_completo !== client.nombre_completo) {
          updateData.nombre_completo = formData.nombre_completo;
        }
        if (formData.nombre_comercial !== (client.nombre_comercial || '')) {
          updateData.nombre_comercial = formData.nombre_comercial || undefined;
        }
        if (formData.email !== (client.email || '')) {
          updateData.email = formData.email || undefined;
        }
        if (formData.telefono !== (client.telefono || '')) {
          updateData.telefono = formData.telefono || undefined;
        }
        if (formData.direccion !== (client.direccion || '')) {
          updateData.direccion = formData.direccion || undefined;
        }
        if (formData.tipo_cliente !== client.tipo_cliente) {
          updateData.tipo_cliente = formData.tipo_cliente as ClientType;
        }

        await ClientsService.updateClient(client.id, updateData);
      } else {
        // Crear nuevo cliente
        const createData: ClientCreate = {
          tipo_documento: formData.tipo_documento as DocumentType,
          numero_documento: formData.numero_documento.trim(),
          nombre_completo: formData.nombre_completo.trim(),
          nombre_comercial: formData.nombre_comercial.trim() || undefined,
          email: formData.email.trim() || undefined,
          telefono: formData.telefono.trim() || undefined,
          direccion: formData.direccion.trim() || undefined,
          tipo_cliente: formData.tipo_cliente as ClientType,
        };

        await ClientsService.createClient(createData);
      }

      onSave();
    } catch (error: any) {
      console.error('Error al guardar cliente:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const isEditing = !!client;
  const title = isEditing ? 'Editar Cliente' : 'Nuevo Cliente';

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
        <Box display="flex" alignItems="center" gap={2}>
          {formData.tipo_cliente === ClientType.EMPRESA ? (
            <BusinessIcon color="primary" />
          ) : (
            <PersonIcon color="primary" />
          )}
          <Typography variant="h6">{title}</Typography>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3}>
          {/* Tipo de Cliente */}
          <Grid item xs={12}>
            <FormControl 
              fullWidth 
              error={!!errors.tipo_cliente}
              disabled={isEditing} // No permitir cambio en edición
            >
              <InputLabel>Tipo de Cliente *</InputLabel>
              <Select
                value={formData.tipo_cliente}
                label="Tipo de Cliente *"
                onChange={handleChange('tipo_cliente')}
              >
                <MenuItem value={ClientType.PERSONA_NATURAL}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <PersonIcon fontSize="small" />
                    Persona Natural
                  </Box>
                </MenuItem>
                <MenuItem value={ClientType.EMPRESA}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <BusinessIcon fontSize="small" />
                    Empresa
                  </Box>
                </MenuItem>
              </Select>
              {errors.tipo_cliente && <FormHelperText>{errors.tipo_cliente}</FormHelperText>}
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <Divider />
          </Grid>

          {/* Información del Documento */}
          <Grid item xs={12} md={4}>
            <FormControl 
              fullWidth 
              error={!!errors.tipo_documento}
              disabled={isEditing} // No permitir cambio en edición
            >
              <InputLabel>Tipo de Documento *</InputLabel>
              <Select
                value={formData.tipo_documento}
                label="Tipo de Documento *"
                onChange={handleChange('tipo_documento')}
              >
                {Object.entries(ClientsService.getDocumentTypeLabels()).map(([value, label]) => (
                  <MenuItem key={value} value={value}>
                    {label}
                  </MenuItem>
                ))}
              </Select>
              {errors.tipo_documento && <FormHelperText>{errors.tipo_documento}</FormHelperText>}
            </FormControl>
          </Grid>

          <Grid item xs={12} md={8}>
            <TextField
              fullWidth
              label="Número de Documento *"
              value={formData.numero_documento}
              onChange={handleChange('numero_documento')}
              error={!!errors.numero_documento}
              helperText={errors.numero_documento}
              disabled={isEditing} // No permitir cambio en edición
              placeholder="Ingrese el número de documento"
            />
          </Grid>

          {/* Información Básica */}
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Nombre Completo / Razón Social *"
              value={formData.nombre_completo}
              onChange={handleChange('nombre_completo')}
              error={!!errors.nombre_completo}
              helperText={errors.nombre_completo}
              placeholder={
                formData.tipo_cliente === ClientType.EMPRESA
                  ? "Razón social de la empresa"
                  : "Nombre completo de la persona"
              }
            />
          </Grid>

          {formData.tipo_cliente === ClientType.EMPRESA && (
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Nombre Comercial"
                value={formData.nombre_comercial}
                onChange={handleChange('nombre_comercial')}
                placeholder="Nombre comercial o marca (opcional)"
              />
            </Grid>
          )}

          <Grid item xs={12}>
            <Divider />
          </Grid>

          {/* Información de Contacto */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Email"
              type="email"
              value={formData.email}
              onChange={handleChange('email')}
              error={!!errors.email}
              helperText={errors.email}
              placeholder="correo@ejemplo.com"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Teléfono"
              value={formData.telefono}
              onChange={handleChange('telefono')}
              placeholder="310 123 4567"
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Dirección"
              value={formData.direccion}
              onChange={handleChange('direccion')}
              multiline
              rows={2}
              placeholder="Dirección completa (opcional)"
            />
          </Grid>
        </Grid>
      </DialogContent>

      <DialogActions sx={{ p: 3 }}>
        <Button
          onClick={onClose}
          startIcon={<CancelIcon />}
          disabled={loading}
        >
          Cancelar
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          startIcon={loading ? <CircularProgress size={16} /> : <SaveIcon />}
          disabled={loading}
        >
          {loading ? 'Guardando...' : (isEditing ? 'Actualizar' : 'Crear Cliente')}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ClientForm;