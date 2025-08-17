/**
 * Componente para mostrar lista de usuarios con funcionalidades de gestión
 */

import React, { useState } from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Avatar,
  Box,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Alert
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  PersonOff as PersonOffIcon,
  PersonAdd as PersonAddIcon,
  VpnKey as VpnKeyIcon,
  FilterList as FilterIcon
} from '@mui/icons-material';

import { User, usersService, USER_ROLES } from '../../services/usersService';
import ChangePasswordDialog from './ChangePasswordDialog';

interface UsersListProps {
  users: User[];
  onEditUser: (user: User) => void;
  onDeleteUser: () => void;
  onRefresh: () => void;
}

const UsersList: React.FC<UsersListProps> = ({
  users,
  onEditUser,
  onDeleteUser,
  onRefresh
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState<User | null>(null);
  const [changePasswordDialogOpen, setChangePasswordDialogOpen] = useState(false);
  const [userToChangePassword, setUserToChangePassword] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filtrar usuarios
  const filteredUsers = users.filter(user => {
    const matchesSearch = user.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = roleFilter === '' || user.rol === roleFilter;
    const matchesStatus = statusFilter === '' || 
                         (statusFilter === 'active' && user.is_active) ||
                         (statusFilter === 'inactive' && !user.is_active);
    
    return matchesSearch && matchesRole && matchesStatus;
  });

  const handleDeleteClick = (user: User) => {
    setUserToDelete(user);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!userToDelete) return;

    setLoading(true);
    setError(null);

    try {
      await usersService.deleteUser(userToDelete.id);
      onDeleteUser();
      setDeleteDialogOpen(false);
      setUserToDelete(null);
    } catch (error: any) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleActivateUser = async (user: User) => {
    setLoading(true);
    setError(null);

    try {
      await usersService.activateUser(user.id);
      onRefresh();
    } catch (error: any) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleChangePasswordClick = (user: User) => {
    setUserToChangePassword(user);
    setChangePasswordDialogOpen(true);
  };

  const handlePasswordChanged = () => {
    setChangePasswordDialogOpen(false);
    setUserToChangePassword(null);
    onRefresh();
  };

  const getInitials = (name: string): string => {
    return name
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <Box>
      {/* Filtros */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          <TextField
            placeholder="Buscar por nombre o email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            size="small"
            sx={{ minWidth: 250 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />

          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Rol</InputLabel>
            <Select
              value={roleFilter}
              label="Rol"
              onChange={(e) => setRoleFilter(e.target.value)}
            >
              <MenuItem value="">Todos</MenuItem>
              {Object.entries(USER_ROLES).map(([key, value]) => (
                <MenuItem key={value} value={value}>
                  {usersService.getRoleLabel(value)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Estado</InputLabel>
            <Select
              value={statusFilter}
              label="Estado"
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <MenuItem value="">Todos</MenuItem>
              <MenuItem value="active">Activos</MenuItem>
              <MenuItem value="inactive">Inactivos</MenuItem>
            </Select>
          </FormControl>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 'auto' }}>
            <FilterIcon />
            <Typography variant="body2" color="text.secondary">
              {filteredUsers.length} de {users.length} usuarios
            </Typography>
          </Box>
        </Box>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Tabla de usuarios */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Usuario</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Rol</TableCell>
              <TableCell>Estado</TableCell>
              <TableCell>Fecha Creación</TableCell>
              <TableCell align="center">Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredUsers.map((user) => (
              <TableRow key={user.id} hover>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Avatar
                      sx={{
                        bgcolor: usersService.getRoleColor(user.rol) + '.main',
                        width: 40,
                        height: 40
                      }}
                    >
                      {getInitials(user.nombre)}
                    </Avatar>
                    <Box>
                      <Typography variant="subtitle2" fontWeight="bold">
                        {user.nombre}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        ID: {user.id.slice(0, 8)}...
                      </Typography>
                    </Box>
                  </Box>
                </TableCell>

                <TableCell>
                  <Typography variant="body2">{user.email}</Typography>
                </TableCell>

                <TableCell>
                  <Chip
                    label={usersService.getRoleLabel(user.rol)}
                    color={usersService.getRoleColor(user.rol)}
                    size="small"
                    variant="outlined"
                  />
                </TableCell>

                <TableCell>
                  <Chip
                    label={user.is_active ? 'Activo' : 'Inactivo'}
                    color={user.is_active ? 'success' : 'error'}
                    size="small"
                    variant={user.is_active ? 'filled' : 'outlined'}
                  />
                </TableCell>

                <TableCell>
                  <Typography variant="body2">
                    {usersService.formatCreatedDate(user.created_at)}
                  </Typography>
                </TableCell>

                <TableCell align="center">
                  <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
                    <Tooltip title="Editar usuario">
                      <IconButton
                        size="small"
                        onClick={() => onEditUser(user)}
                        disabled={loading}
                      >
                        <EditIcon />
                      </IconButton>
                    </Tooltip>

                    <Tooltip title="Cambiar contraseña">
                      <IconButton
                        size="small"
                        onClick={() => handleChangePasswordClick(user)}
                        disabled={loading}
                      >
                        <VpnKeyIcon />
                      </IconButton>
                    </Tooltip>

                    {user.is_active ? (
                      <Tooltip title="Desactivar usuario">
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteClick(user)}
                          color="error"
                          disabled={loading}
                        >
                          <PersonOffIcon />
                        </IconButton>
                      </Tooltip>
                    ) : (
                      <Tooltip title="Activar usuario">
                        <IconButton
                          size="small"
                          onClick={() => handleActivateUser(user)}
                          color="success"
                          disabled={loading}
                        >
                          <PersonAddIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                </TableCell>
              </TableRow>
            ))}

            {filteredUsers.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body1" color="text.secondary">
                    No se encontraron usuarios que coincidan con los filtros aplicados
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Dialog de confirmación de eliminación */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Confirmar Desactivación</DialogTitle>
        <DialogContent>
          <Typography>
            ¿Estás seguro de que quieres desactivar al usuario{' '}
            <strong>{userToDelete?.nombre}</strong>?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            El usuario será desactivado pero no eliminado permanentemente.
            Podrás reactivarlo más tarde si es necesario.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={loading}>
            Cancelar
          </Button>
          <Button
            onClick={handleConfirmDelete}
            color="error"
            variant="contained"
            disabled={loading}
          >
            {loading ? 'Desactivando...' : 'Desactivar'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog de cambio de contraseña */}
      {userToChangePassword && (
        <ChangePasswordDialog
          open={changePasswordDialogOpen}
          onClose={() => setChangePasswordDialogOpen(false)}
          onPasswordChanged={handlePasswordChanged}
          user={userToChangePassword}
        />
      )}
    </Box>
  );
};

export default UsersList;