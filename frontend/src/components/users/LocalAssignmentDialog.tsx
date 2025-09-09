/**
 * Componente para gestionar asignaciones de locales a usuarios
 * Permite asignar, editar y remover locales con permisos granulares
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  TextField,
  Alert,
  CircularProgress,
  Divider
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Close as CloseIcon,
  Store as StoreIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon
} from '@mui/icons-material';

import {
  User,
  LocalAssignment,
  AvailableLocal,
  CreateLocalAssignmentRequest,
  PERMISSION_PROFILES,
  PERMISSION_PROFILE_LABELS,
  usersService
} from '../../services/usersService';

interface LocalAssignmentDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: () => void;
  user: User | null;
}

interface NewAssignmentState {
  localId: string;
  assignmentMode: 'profile' | 'custom';
  profile: keyof typeof PERMISSION_PROFILES | '';
  permissions: {
    puede_vender: boolean;
    puede_ver_stock: boolean;
    puede_transferir: boolean;
    es_responsable: boolean;
    puede_modificar_precios: boolean;
    puede_aplicar_descuentos: boolean;
    puede_ver_reportes: boolean;
    puede_gestionar_usuarios: boolean;
    limite_descuento_porcentaje: number | '';
    limite_credito_monto: number | '';
  };
}

const LocalAssignmentDialog: React.FC<LocalAssignmentDialogProps> = ({
  open,
  onClose,
  onSave,
  user
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [assignments, setAssignments] = useState<LocalAssignment[]>([]);
  const [availableLocals, setAvailableLocals] = useState<AvailableLocal[]>([]);
  const [showNewAssignment, setShowNewAssignment] = useState(false);
  
  const [newAssignment, setNewAssignment] = useState<NewAssignmentState>({
    localId: '',
    assignmentMode: 'profile',
    profile: '',
    permissions: {
      puede_vender: true,
      puede_ver_stock: true,
      puede_transferir: false,
      es_responsable: false,
      puede_modificar_precios: false,
      puede_aplicar_descuentos: false,
      puede_ver_reportes: false,
      puede_gestionar_usuarios: false,
      limite_descuento_porcentaje: '',
      limite_credito_monto: ''
    }
  });

  useEffect(() => {
    if (open && user) {
      loadData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, user]);

  const loadData = async () => {
    if (!user) return;

    setLoading(true);
    setError(null);

    try {
      const [assignmentsData, availableData] = await Promise.all([
        usersService.getUserLocalAssignments(user.id),
        usersService.getAvailableLocalsForUser(user.id)
      ]);

      setAssignments(assignmentsData);
      setAvailableLocals(availableData);
    } catch (error: any) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddAssignment = async () => {
    if (!user || !newAssignment.localId) return;

    setLoading(true);
    setError(null);

    try {
      if (newAssignment.assignmentMode === 'profile' && newAssignment.profile) {
        await usersService.assignUserToLocalWithProfile(
          user.id,
          newAssignment.localId,
          newAssignment.profile
        );
      } else {
        const assignmentData: CreateLocalAssignmentRequest = {
          user_id: user.id,
          local_id: newAssignment.localId,
          ...newAssignment.permissions,
          limite_descuento_porcentaje: newAssignment.permissions.limite_descuento_porcentaje || undefined,
          limite_credito_monto: newAssignment.permissions.limite_credito_monto || undefined
        };

        await usersService.assignUserToLocal(assignmentData);
      }

      // Resetear formulario
      setNewAssignment({
        localId: '',
        assignmentMode: 'profile',
        profile: '',
        permissions: {
          puede_vender: true,
          puede_ver_stock: true,
          puede_transferir: false,
          es_responsable: false,
          puede_modificar_precios: false,
          puede_aplicar_descuentos: false,
          puede_ver_reportes: false,
          puede_gestionar_usuarios: false,
          limite_descuento_porcentaje: '',
          limite_credito_monto: ''
        }
      });
      setShowNewAssignment(false);
      await loadData();
    } catch (error: any) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };


  const handleRemoveAssignment = async (assignment: LocalAssignment) => {
    if (!user) return;

    // Verificar que no se quede sin locales (excepto para administradores)
    if (assignments.length === 1 && user?.rol !== 'administrador') {
      setError('El usuario debe tener al menos un local asignado. No se puede eliminar el último local.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await usersService.removeUserFromLocal(user.id, assignment.assignment_id);
      await loadData();
    } catch (error: any) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setNewAssignment({
      localId: '',
      assignmentMode: 'profile',
      profile: '',
      permissions: {
        puede_vender: true,
        puede_ver_stock: true,
        puede_transferir: false,
        es_responsable: false,
        puede_modificar_precios: false,
        puede_aplicar_descuentos: false,
        puede_ver_reportes: false,
        puede_gestionar_usuarios: false,
        limite_descuento_porcentaje: '',
        limite_credito_monto: ''
      }
    });
    setShowNewAssignment(false);
    setError(null);
    onClose();
  };

  const handleSave = () => {
    // Validar que el usuario tenga al menos un local asignado (excepto para administradores)
    if (assignments.length === 0 && user?.rol !== 'administrador') {
      setError('El usuario debe tener al menos un local asignado');
      return;
    }
    
    onSave();
    handleClose();
  };

  const getPermissionIcon = (hasPermission: boolean) => {
    return hasPermission ? (
      <CheckCircleIcon color="success" fontSize="small" />
    ) : (
      <WarningIcon color="disabled" fontSize="small" />
    );
  };

  if (!user) return null;

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { height: '90vh' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <StoreIcon color="primary" />
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6">
              Gestión de Locales - {user.nombre}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Administrar accesos y permisos por local
            </Typography>
          </Box>
          <IconButton onClick={handleClose}>
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Box>
            {/* Locales Asignados */}
            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Locales Asignados ({assignments.length})
                </Typography>
                {availableLocals.length > 0 && (
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setShowNewAssignment(true)}
                    disabled={loading}
                  >
                    Asignar Local
                  </Button>
                )}
              </Box>

              {assignments.length === 0 ? (
                <Alert severity="info">
                  Este usuario no tiene locales asignados aún.
                </Alert>
              ) : (
                <Grid container spacing={2}>
                  {assignments.map((assignment) => (
                    <Grid item xs={12} md={6} key={assignment.assignment_id}>
                      <Card variant="outlined">
                        <CardContent>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                            <Box>
                              <Typography variant="subtitle1" fontWeight="bold">
                                {assignment.local_nombre}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                Código: {assignment.local_codigo}
                              </Typography>
                            </Box>
                            <Chip
                              label={assignment.es_responsable ? 'Responsable' : 'Colaborador'}
                              color={assignment.es_responsable ? 'error' : 'default'}
                              size="small"
                            />
                          </Box>

                          {/* Permisos Grid */}
                          <Grid container spacing={1} sx={{ mb: 2 }}>
                            <Grid item xs={6}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {getPermissionIcon(assignment.puede_vender)}
                                <Typography variant="caption">Vender</Typography>
                              </Box>
                            </Grid>
                            <Grid item xs={6}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {getPermissionIcon(assignment.puede_ver_stock)}
                                <Typography variant="caption">Ver Stock</Typography>
                              </Box>
                            </Grid>
                            <Grid item xs={6}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {getPermissionIcon(assignment.puede_transferir)}
                                <Typography variant="caption">Transferir</Typography>
                              </Box>
                            </Grid>
                            <Grid item xs={6}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {getPermissionIcon(assignment.puede_modificar_precios)}
                                <Typography variant="caption">Mod. Precios</Typography>
                              </Box>
                            </Grid>
                            <Grid item xs={6}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {getPermissionIcon(assignment.puede_aplicar_descuentos)}
                                <Typography variant="caption">Descuentos</Typography>
                              </Box>
                            </Grid>
                            <Grid item xs={6}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {getPermissionIcon(assignment.puede_ver_reportes)}
                                <Typography variant="caption">Reportes</Typography>
                              </Box>
                            </Grid>
                          </Grid>

                          {/* Límites */}
                          {(assignment.limite_descuento_porcentaje || assignment.limite_credito_monto) && (
                            <Box sx={{ mt: 1 }}>
                              <Typography variant="caption" color="text.secondary">
                                Límites:{' '}
                                {assignment.limite_descuento_porcentaje && 
                                  `Desc. ${assignment.limite_descuento_porcentaje}%`}
                                {assignment.limite_descuento_porcentaje && assignment.limite_credito_monto && ', '}
                                {assignment.limite_credito_monto && 
                                  `Crédito $${assignment.limite_credito_monto.toLocaleString()}`}
                              </Typography>
                            </Box>
                          )}
                        </CardContent>

                        <CardActions>
                          <Button
                            size="small"
                            color="error"
                            startIcon={<DeleteIcon />}
                            onClick={() => handleRemoveAssignment(assignment)}
                            disabled={loading}
                          >
                            Remover
                          </Button>
                        </CardActions>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              )}
            </Box>

            {/* Formulario Nueva Asignación */}
            {showNewAssignment && (
              <>
                <Divider sx={{ my: 3 }} />
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Asignar Nuevo Local
                  </Typography>

                  <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                      <FormControl fullWidth>
                        <InputLabel>Local</InputLabel>
                        <Select
                          value={newAssignment.localId}
                          label="Local"
                          onChange={(e) => setNewAssignment(prev => ({
                            ...prev,
                            localId: e.target.value
                          }))}
                        >
                          {availableLocals.map((local) => (
                            <MenuItem key={local.id} value={local.id}>
                              {local.nombre} ({local.codigo})
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <FormControl fullWidth>
                        <InputLabel>Modo de Asignación</InputLabel>
                        <Select
                          value={newAssignment.assignmentMode}
                          label="Modo de Asignación"
                          onChange={(e) => setNewAssignment(prev => ({
                            ...prev,
                            assignmentMode: e.target.value as 'profile' | 'custom'
                          }))}
                        >
                          <MenuItem value="profile">Perfil Predefinido</MenuItem>
                          <MenuItem value="custom">Permisos Personalizados</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>

                    {newAssignment.assignmentMode === 'profile' && (
                      <Grid item xs={12}>
                        <FormControl fullWidth>
                          <InputLabel>Perfil de Permisos</InputLabel>
                          <Select
                            value={newAssignment.profile}
                            label="Perfil de Permisos"
                            onChange={(e) => setNewAssignment(prev => ({
                              ...prev,
                              profile: e.target.value as keyof typeof PERMISSION_PROFILES
                            }))}
                          >
                            {Object.entries(PERMISSION_PROFILES).map(([key, value]) => (
                              <MenuItem key={value} value={value}>
                                {PERMISSION_PROFILE_LABELS[value as keyof typeof PERMISSION_PROFILE_LABELS]}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      </Grid>
                    )}

                    {newAssignment.assignmentMode === 'custom' && (
                      <>
                        <Grid item xs={12}>
                          <Typography variant="subtitle2" gutterBottom>
                            Permisos Básicos
                          </Typography>
                          <Grid container spacing={2}>
                            <Grid item xs={6} md={3}>
                              <FormControlLabel
                                control={
                                  <Switch
                                    checked={newAssignment.permissions.puede_vender}
                                    onChange={(e) => setNewAssignment(prev => ({
                                      ...prev,
                                      permissions: {
                                        ...prev.permissions,
                                        puede_vender: e.target.checked
                                      }
                                    }))}
                                  />
                                }
                                label="Vender"
                              />
                            </Grid>
                            <Grid item xs={6} md={3}>
                              <FormControlLabel
                                control={
                                  <Switch
                                    checked={newAssignment.permissions.puede_ver_stock}
                                    onChange={(e) => setNewAssignment(prev => ({
                                      ...prev,
                                      permissions: {
                                        ...prev.permissions,
                                        puede_ver_stock: e.target.checked
                                      }
                                    }))}
                                  />
                                }
                                label="Ver Stock"
                              />
                            </Grid>
                            <Grid item xs={6} md={3}>
                              <FormControlLabel
                                control={
                                  <Switch
                                    checked={newAssignment.permissions.puede_transferir}
                                    onChange={(e) => setNewAssignment(prev => ({
                                      ...prev,
                                      permissions: {
                                        ...prev.permissions,
                                        puede_transferir: e.target.checked
                                      }
                                    }))}
                                  />
                                }
                                label="Transferir"
                              />
                            </Grid>
                            <Grid item xs={6} md={3}>
                              <FormControlLabel
                                control={
                                  <Switch
                                    checked={newAssignment.permissions.es_responsable}
                                    onChange={(e) => setNewAssignment(prev => ({
                                      ...prev,
                                      permissions: {
                                        ...prev.permissions,
                                        es_responsable: e.target.checked
                                      }
                                    }))}
                                  />
                                }
                                label="Responsable"
                              />
                            </Grid>
                          </Grid>
                        </Grid>

                        <Grid item xs={12}>
                          <Typography variant="subtitle2" gutterBottom>
                            Permisos Avanzados
                          </Typography>
                          <Grid container spacing={2}>
                            <Grid item xs={6} md={3}>
                              <FormControlLabel
                                control={
                                  <Switch
                                    checked={newAssignment.permissions.puede_modificar_precios}
                                    onChange={(e) => setNewAssignment(prev => ({
                                      ...prev,
                                      permissions: {
                                        ...prev.permissions,
                                        puede_modificar_precios: e.target.checked
                                      }
                                    }))}
                                  />
                                }
                                label="Modificar Precios"
                              />
                            </Grid>
                            <Grid item xs={6} md={3}>
                              <FormControlLabel
                                control={
                                  <Switch
                                    checked={newAssignment.permissions.puede_aplicar_descuentos}
                                    onChange={(e) => setNewAssignment(prev => ({
                                      ...prev,
                                      permissions: {
                                        ...prev.permissions,
                                        puede_aplicar_descuentos: e.target.checked
                                      }
                                    }))}
                                  />
                                }
                                label="Aplicar Descuentos"
                              />
                            </Grid>
                            <Grid item xs={6} md={3}>
                              <FormControlLabel
                                control={
                                  <Switch
                                    checked={newAssignment.permissions.puede_ver_reportes}
                                    onChange={(e) => setNewAssignment(prev => ({
                                      ...prev,
                                      permissions: {
                                        ...prev.permissions,
                                        puede_ver_reportes: e.target.checked
                                      }
                                    }))}
                                  />
                                }
                                label="Ver Reportes"
                              />
                            </Grid>
                            <Grid item xs={6} md={3}>
                              <FormControlLabel
                                control={
                                  <Switch
                                    checked={newAssignment.permissions.puede_gestionar_usuarios}
                                    onChange={(e) => setNewAssignment(prev => ({
                                      ...prev,
                                      permissions: {
                                        ...prev.permissions,
                                        puede_gestionar_usuarios: e.target.checked
                                      }
                                    }))}
                                  />
                                }
                                label="Gestionar Usuarios"
                              />
                            </Grid>
                          </Grid>
                        </Grid>

                        <Grid item xs={12} md={6}>
                          <TextField
                            fullWidth
                            label="Límite Descuento (%)"
                            type="number"
                            value={newAssignment.permissions.limite_descuento_porcentaje}
                            onChange={(e) => setNewAssignment(prev => ({
                              ...prev,
                              permissions: {
                                ...prev.permissions,
                                limite_descuento_porcentaje: e.target.value === '' ? '' : Number(e.target.value)
                              }
                            }))}
                            InputProps={{
                              inputProps: { min: 0, max: 100 }
                            }}
                          />
                        </Grid>

                        <Grid item xs={12} md={6}>
                          <TextField
                            fullWidth
                            label="Límite Crédito ($)"
                            type="number"
                            value={newAssignment.permissions.limite_credito_monto}
                            onChange={(e) => setNewAssignment(prev => ({
                              ...prev,
                              permissions: {
                                ...prev.permissions,
                                limite_credito_monto: e.target.value === '' ? '' : Number(e.target.value)
                              }
                            }))}
                            InputProps={{
                              inputProps: { min: 0 }
                            }}
                          />
                        </Grid>
                      </>
                    )}
                  </Grid>

                  <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
                    <Button
                      variant="contained"
                      onClick={handleAddAssignment}
                      disabled={
                        loading || 
                        !newAssignment.localId || 
                        (newAssignment.assignmentMode === 'profile' && !newAssignment.profile)
                      }
                    >
                      {loading ? 'Asignando...' : 'Asignar Local'}
                    </Button>
                    <Button
                      variant="outlined"
                      onClick={() => setShowNewAssignment(false)}
                      disabled={loading}
                    >
                      Cancelar
                    </Button>
                  </Box>
                </Box>
              </>
            )}

            {/* Mostrar mensaje si no hay locales disponibles */}
            {!loading && availableLocals.length === 0 && assignments.length > 0 && !showNewAssignment && (
              <Alert severity="info" sx={{ mt: 2 }}>
                Todos los locales disponibles ya han sido asignados a este usuario.
              </Alert>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cerrar
        </Button>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={loading}
        >
          Guardar Cambios
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default LocalAssignmentDialog;