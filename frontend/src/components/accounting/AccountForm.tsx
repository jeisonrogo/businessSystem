/**
 * Formulario de Cuenta Contable
 * Para crear y editar cuentas del plan contable
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Alert,
  Chip,
  Autocomplete,
  FormHelperText,
  Divider,
} from '@mui/material';
import {
  AccountBalance,
  Save,
  Cancel,
  Warning,
} from '@mui/icons-material';

import { Account, AccountCreate, AccountUpdate, AccountType } from '../../types';
import { AccountingService } from '../../services/accountingService';

interface AccountFormProps {
  open: boolean;
  account?: Account | null;
  onClose: () => void;
  onSave: () => void;
}

interface FormErrors {
  codigo?: string;
  nombre?: string;
  tipo_cuenta?: string;
  cuenta_padre_id?: string;
}

const AccountForm: React.FC<AccountFormProps> = ({
  open,
  account,
  onClose,
  onSave,
}) => {
  const [formData, setFormData] = useState<AccountCreate>({
    codigo: '',
    nombre: '',
    tipo_cuenta: AccountType.ACTIVO,
    cuenta_padre_id: undefined,
  });
  
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [availableParents, setAvailableParents] = useState<Account[]>([]);
  const [loadingParents, setLoadingParents] = useState(false);

  const isEditing = Boolean(account);
  const typeLabels = AccountingService.getAccountTypeLabels();
  const typeColors = AccountingService.getAccountTypeColors();

  // Resetear formulario cuando se abre/cierra
  useEffect(() => {
    if (open) {
      if (account) {
        setFormData({
          codigo: account.codigo,
          nombre: account.nombre,
          tipo_cuenta: account.tipo_cuenta,
          cuenta_padre_id: account.cuenta_padre_id,
        });
      } else {
        setFormData({
          codigo: '',
          nombre: '',
          tipo_cuenta: AccountType.ACTIVO,
          cuenta_padre_id: undefined,
        });
      }
      setErrors({});
      setSubmitError(null);
      loadParentAccounts();
    }
  }, [open, account]);

  // Cargar cuentas padre disponibles
  const loadParentAccounts = async () => {
    setLoadingParents(true);
    try {
      const response = await AccountingService.getAccounts({ limit: 500 });
      const accounts = response.cuentas || [];
      
      // Filtrar para excluir la cuenta actual (si estamos editando) y sus descendientes
      let filtered = accounts.filter(acc => acc.id !== account?.id);
      
      // TODO: También excluir descendientes de la cuenta actual para evitar referencias circulares
      setAvailableParents(filtered);
    } catch (error) {
      console.error('Error cargando cuentas padre:', error);
    } finally {
      setLoadingParents(false);
    }
  };

  // Cuentas padre filtradas por tipo compatible
  const compatibleParents = useMemo(() => {
    return availableParents.filter(parent => {
      // Las subcuentas deben ser del mismo tipo que la cuenta padre
      return parent.tipo_cuenta === formData.tipo_cuenta;
    });
  }, [availableParents, formData.tipo_cuenta]);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Validar código
    const codeValidation = AccountingService.validateAccountCode(formData.codigo);
    if (!codeValidation.isValid) {
      newErrors.codigo = codeValidation.error;
    }

    // Validar nombre
    if (!formData.nombre.trim()) {
      newErrors.nombre = 'El nombre es requerido';
    } else if (formData.nombre.length < 3) {
      newErrors.nombre = 'El nombre debe tener al menos 3 caracteres';
    }

    // Validar tipo de cuenta
    if (!formData.tipo_cuenta) {
      newErrors.tipo_cuenta = 'Debe seleccionar un tipo de cuenta';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleFieldChange = (field: keyof AccountCreate, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Limpiar error del campo al cambiar
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }

    // Si cambia el tipo de cuenta, limpiar la cuenta padre si no es compatible
    if (field === 'tipo_cuenta' && formData.cuenta_padre_id) {
      const selectedParent = availableParents.find(p => p.id === formData.cuenta_padre_id);
      if (selectedParent && selectedParent.tipo_cuenta !== value) {
        setFormData(prev => ({ ...prev, cuenta_padre_id: undefined }));
      }
    }
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setSubmitError(null);

    try {
      if (isEditing && account) {
        // Actualizar cuenta existente
        const updateData: AccountUpdate = {};
        if (formData.nombre !== account.nombre) updateData.nombre = formData.nombre;
        if (formData.tipo_cuenta !== account.tipo_cuenta) updateData.tipo_cuenta = formData.tipo_cuenta;
        if (formData.cuenta_padre_id !== account.cuenta_padre_id) updateData.cuenta_padre_id = formData.cuenta_padre_id;

        if (Object.keys(updateData).length > 0) {
          await AccountingService.updateAccount(account.id, updateData);
        }
      } else {
        // Crear nueva cuenta
        await AccountingService.createAccount(formData);
      }

      onSave();
    } catch (error: any) {
      setSubmitError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const selectedParent = formData.cuenta_padre_id ? 
    availableParents.find(p => p.id === formData.cuenta_padre_id) : null;

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="md" 
      fullWidth
      PaperProps={{
        sx: { minHeight: '500px' }
      }}
    >
      <DialogTitle sx={{ pb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AccountBalance color="primary" />
          <Typography variant="h6" component="span">
            {isEditing ? 'Editar Cuenta Contable' : 'Nueva Cuenta Contable'}
          </Typography>
        </Box>
        {isEditing && account && (
          <Typography variant="body2" color="text.secondary">
            Modificando: {account.codigo} - {account.nombre}
          </Typography>
        )}
      </DialogTitle>

      <DialogContent>
        {submitError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {submitError}
          </Alert>
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 1 }}>
          {/* Código de cuenta */}
          <TextField
            label="Código de Cuenta"
            value={formData.codigo}
            onChange={(e) => handleFieldChange('codigo', e.target.value)}
            error={Boolean(errors.codigo)}
            helperText={errors.codigo || '1-8 dígitos numéricos (ej: 1105, 11050105)'}
            disabled={isEditing} // No permitir cambiar código en edición
            required
            inputProps={{
              maxLength: 8,
              pattern: '[0-9]*',
            }}
            sx={{
              '& input': {
                fontFamily: 'monospace',
                fontSize: '1.1rem',
                fontWeight: 'bold',
              }
            }}
          />

          {/* Nombre de cuenta */}
          <TextField
            label="Nombre de la Cuenta"
            value={formData.nombre}
            onChange={(e) => handleFieldChange('nombre', e.target.value)}
            error={Boolean(errors.nombre)}
            helperText={errors.nombre || 'Nombre descriptivo de la cuenta contable'}
            required
            multiline
            rows={2}
          />

          {/* Tipo de cuenta */}
          <FormControl error={Boolean(errors.tipo_cuenta)} required>
            <InputLabel>Tipo de Cuenta</InputLabel>
            <Select
              value={formData.tipo_cuenta}
              label="Tipo de Cuenta"
              onChange={(e) => handleFieldChange('tipo_cuenta', e.target.value)}
            >
              {Object.entries(typeLabels).map(([type, label]) => (
                <MenuItem key={type} value={type}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip
                      size="small"
                      label={type}
                      sx={{
                        backgroundColor: typeColors[type as AccountType] + '20',
                        color: typeColors[type as AccountType],
                        fontWeight: 'bold',
                        minWidth: '80px',
                      }}
                    />
                    {label}
                  </Box>
                </MenuItem>
              ))}
            </Select>
            {errors.tipo_cuenta && (
              <FormHelperText>{errors.tipo_cuenta}</FormHelperText>
            )}
          </FormControl>

          <Divider />

          {/* Cuenta padre (opcional) */}
          <Box>
            <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              Jerarquía de Cuentas
              <Typography variant="caption" color="text.secondary">(Opcional)</Typography>
            </Typography>
            
            <Autocomplete
              options={compatibleParents}
              getOptionLabel={(option) => `${option.codigo} - ${option.nombre}`}
              value={selectedParent}
              onChange={(_, value) => handleFieldChange('cuenta_padre_id', value?.id)}
              loading={loadingParents}
              renderOption={(props, option) => (
                <Box component="li" {...props}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                    <Typography variant="body2" fontFamily="monospace" fontWeight="bold">
                      {option.codigo}
                    </Typography>
                    <Typography variant="body2" sx={{ flex: 1 }}>
                      {option.nombre}
                    </Typography>
                    {option.tiene_subcuentas && (
                      <Chip size="small" label="Tiene subcuentas" variant="outlined" />
                    )}
                  </Box>
                </Box>
              )}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Cuenta Padre"
                  placeholder="Buscar cuenta padre..."
                  helperText="Seleccione una cuenta padre para crear una subcuenta. Debe ser del mismo tipo."
                />
              )}
              noOptionsText={
                formData.tipo_cuenta 
                  ? `No hay cuentas de tipo ${typeLabels[formData.tipo_cuenta]} disponibles`
                  : 'Seleccione primero un tipo de cuenta'
              }
            />
          </Box>

          {/* Información de validación */}
          <Box sx={{ p: 2, bgcolor: 'info.50', borderRadius: 1 }}>
            <Typography variant="subtitle2" color="info.main" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <Warning fontSize="small" />
              Reglas de Validación
            </Typography>
            <Typography variant="caption" color="text.secondary" component="div">
              • El código debe ser único y numérico (1-8 dígitos)<br />
              • Las subcuentas deben ser del mismo tipo que la cuenta padre<br />
              • No se pueden crear referencias circulares en la jerarquía<br />
              • Una vez creada, el código de la cuenta no se puede modificar
            </Typography>
          </Box>
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 2, gap: 1 }}>
        <Button onClick={onClose} disabled={loading} startIcon={<Cancel />}>
          Cancelar
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading}
          startIcon={<Save />}
        >
          {loading ? 'Guardando...' : (isEditing ? 'Actualizar' : 'Crear Cuenta')}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AccountForm;