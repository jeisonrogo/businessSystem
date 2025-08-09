/**
 * Componente de Lista de Cuentas Contables
 * DataGrid avanzado con filtros, búsqueda y acciones
 */

import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Tooltip,
  Alert,
} from '@mui/material';
import { DataGrid, GridColDef, GridActionsCellItem, GridRowParams } from '@mui/x-data-grid';
import {
  Edit,
  Delete,
  Visibility,
  AccountBalance,
  FilterList,
} from '@mui/icons-material';

import { Account, AccountType } from '../../types';
import { AccountingService } from '../../services/accountingService';

interface ChartOfAccountsListProps {
  accounts: Account[];
  loading: boolean;
  onEdit: (account: Account) => void;
  onRefresh: () => void;
}

const ChartOfAccountsList: React.FC<ChartOfAccountsListProps> = ({
  accounts,
  loading,
  onEdit,
  onRefresh,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<AccountType | 'ALL'>('ALL');
  const [showInactive, setShowInactive] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const typeLabels = AccountingService.getAccountTypeLabels();
  const typeColors = AccountingService.getAccountTypeColors();

  // Filtrar y buscar cuentas
  const filteredAccounts = useMemo(() => {
    return accounts.filter(account => {
      // Filtro por término de búsqueda
      const matchesSearch = !searchTerm || 
        account.codigo.toLowerCase().includes(searchTerm.toLowerCase()) ||
        account.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (account.nombre_cuenta_padre && account.nombre_cuenta_padre.toLowerCase().includes(searchTerm.toLowerCase()));

      // Filtro por tipo de cuenta
      const matchesType = filterType === 'ALL' || account.tipo_cuenta === filterType;

      // Filtro por estado activo
      const matchesActive = showInactive || account.is_active;

      return matchesSearch && matchesType && matchesActive;
    });
  }, [accounts, searchTerm, filterType, showInactive]);

  const handleDelete = async (account: Account) => {
    if (!window.confirm(`¿Está seguro de que desea eliminar la cuenta "${account.nombre}"?`)) {
      return;
    }

    try {
      await AccountingService.deleteAccount(account.id);
      onRefresh();
    } catch (error: any) {
      setDeleteError(error.message);
    }
  };

  const columns: GridColDef[] = [
    {
      field: 'codigo',
      headerName: 'Código',
      width: 120,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AccountBalance sx={{ fontSize: 16, color: 'primary.main' }} />
          <Typography variant="body2" fontFamily="monospace" fontWeight="bold">
            {params.value}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'nombre',
      headerName: 'Nombre de la Cuenta',
      flex: 1,
      minWidth: 200,
      renderCell: (params) => (
        <Box>
          <Typography variant="body2" fontWeight={params.row.cuenta_padre_id ? 'normal' : 'bold'}>
            {params.value}
          </Typography>
          {params.row.nombre_cuenta_padre && (
            <Typography variant="caption" color="text.secondary">
              Padre: {params.row.nombre_cuenta_padre}
            </Typography>
          )}
        </Box>
      ),
    },
    {
      field: 'tipo_cuenta',
      headerName: 'Tipo',
      width: 140,
      renderCell: (params) => (
        <Chip
          size="small"
          label={typeLabels[params.value as AccountType]}
          sx={{
            backgroundColor: typeColors[params.value as AccountType] + '20',
            color: typeColors[params.value as AccountType],
            fontWeight: 'bold',
            fontSize: '0.75rem',
          }}
        />
      ),
    },
    {
      field: 'subcuentas',
      headerName: 'Subcuentas',
      width: 100,
      align: 'center',
      renderCell: (params) => (
        <Typography variant="body2" color="text.secondary">
          {params.row.tiene_subcuentas ? '✓' : '-'}
        </Typography>
      ),
    },
    {
      field: 'is_active',
      headerName: 'Estado',
      width: 90,
      renderCell: (params) => (
        <Chip
          size="small"
          label={params.value ? 'Activa' : 'Inactiva'}
          color={params.value ? 'success' : 'default'}
          variant={params.value ? 'filled' : 'outlined'}
        />
      ),
    },
    {
      field: 'created_at',
      headerName: 'Creada',
      width: 110,
      renderCell: (params) => (
        <Typography variant="caption" color="text.secondary">
          {new Date(params.value).toLocaleDateString('es-CO')}
        </Typography>
      ),
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Acciones',
      width: 120,
      getActions: (params: GridRowParams) => [
        <GridActionsCellItem
          icon={
            <Tooltip title="Ver detalles">
              <Visibility />
            </Tooltip>
          }
          label="Ver"
          onClick={() => {
            // TODO: Implementar vista de detalles
            console.log('Ver detalles de cuenta:', params.row);
          }}
        />,
        <GridActionsCellItem
          icon={
            <Tooltip title="Editar cuenta">
              <Edit />
            </Tooltip>
          }
          label="Editar"
          onClick={() => onEdit(params.row as Account)}
        />,
        <GridActionsCellItem
          icon={
            <Tooltip title="Eliminar cuenta">
              <Delete />
            </Tooltip>
          }
          label="Eliminar"
          onClick={() => handleDelete(params.row as Account)}
          disabled={params.row.tiene_subcuentas}
        />,
      ],
    },
  ];

  return (
    <Box>
      {/* Filtros y búsqueda */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <TextField
          label="Buscar cuentas"
          placeholder="Código, nombre o cuenta padre..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          sx={{ minWidth: 300 }}
          size="small"
        />
        
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Tipo de Cuenta</InputLabel>
          <Select
            value={filterType}
            label="Tipo de Cuenta"
            onChange={(e) => setFilterType(e.target.value as AccountType | 'ALL')}
          >
            <MenuItem value="ALL">Todos los tipos</MenuItem>
            {Object.entries(typeLabels).map(([type, label]) => (
              <MenuItem key={type} value={type}>
                {label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 130 }}>
          <InputLabel>Estado</InputLabel>
          <Select
            value={showInactive ? 'ALL' : 'ACTIVE'}
            label="Estado"
            onChange={(e) => setShowInactive(e.target.value === 'ALL')}
          >
            <MenuItem value="ACTIVE">Solo activas</MenuItem>
            <MenuItem value="ALL">Activas e inactivas</MenuItem>
          </Select>
        </FormControl>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 'auto' }}>
          <FilterList sx={{ color: 'text.secondary' }} />
          <Typography variant="body2" color="text.secondary">
            {filteredAccounts.length} de {accounts.length} cuentas
          </Typography>
        </Box>
      </Box>

      {/* Error de eliminación */}
      {deleteError && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setDeleteError(null)}>
          {deleteError}
        </Alert>
      )}

      {/* DataGrid */}
      <Box sx={{ height: 600 }}>
        <DataGrid
          rows={filteredAccounts}
          columns={columns}
          loading={loading}
          pageSizeOptions={[25, 50, 100]}
          initialState={{
            pagination: {
              paginationModel: { page: 0, pageSize: 25 },
            },
            sorting: {
              sortModel: [{ field: 'codigo', sort: 'asc' }],
            },
          }}
          disableRowSelectionOnClick
          sx={{
            '& .MuiDataGrid-row:hover': {
              backgroundColor: 'action.hover',
            },
            '& .MuiDataGrid-cell:focus': {
              outline: 'none',
            },
          }}
        />
      </Box>

      {/* Información adicional */}
      <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
        <Typography variant="body2" color="text.secondary">
          💡 <strong>Consejos:</strong> Use el buscador para encontrar cuentas por código o nombre. 
          Las cuentas padre se muestran en negrita. Las cuentas con subcuentas no se pueden eliminar.
        </Typography>
      </Box>
    </Box>
  );
};

export default ChartOfAccountsList;