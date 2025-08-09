/**
 * Lista de clientes con DataGrid avanzado
 * Incluye paginación del servidor, filtros, búsqueda y operaciones CRUD
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  TextField,
  InputAdornment,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Chip,
  IconButton,
  Tooltip,
  Alert
} from '@mui/material';
import {
  Search as SearchIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  RestoreFromTrash as RestoreIcon,
  Visibility as ViewIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { DataGrid, GridColDef, GridPaginationModel, GridActionsCellItem } from '@mui/x-data-grid';
import { ClientsService, ClientListParams } from '../../services/clientsService';
import { Client, ClientType, DocumentType } from '../../types';
import ClientDetailDialog from './ClientDetailDialog';

interface ClientsListProps {
  onEditClient?: (client: Client) => void;
  onRefresh?: () => void;
}

const ClientsList: React.FC<ClientsListProps> = ({
  onEditClient,
  onRefresh
}) => {
  // Estados principales
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);

  // Estados para filtros y paginación
  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 25,
  });
  const [totalRows, setTotalRows] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [tipoClienteFilter, setTipoClienteFilter] = useState<ClientType | ''>('');
  const [tipoDocumentoFilter, setTipoDocumentoFilter] = useState<DocumentType | ''>('');
  const [onlyActiveFilter, setOnlyActiveFilter] = useState(true);

  // Debounce para búsqueda
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 500);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Cargar clientes
  const loadClients = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params: ClientListParams = {
        page: paginationModel.page + 1, // API usa 1-based indexing
        limit: Math.min(paginationModel.pageSize, 100),
        only_active: onlyActiveFilter,
      };

      if (debouncedSearchTerm) {
        params.search = debouncedSearchTerm;
      }

      if (tipoClienteFilter) {
        params.tipo_cliente = tipoClienteFilter;
      }

      if (tipoDocumentoFilter) {
        params.tipo_documento = tipoDocumentoFilter;
      }

      const response = await ClientsService.getClients(params);
      
      setClients(response.items);
      setTotalRows(response.total);
    } catch (error: any) {
      console.error('Error al cargar clientes:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [paginationModel, debouncedSearchTerm, tipoClienteFilter, tipoDocumentoFilter, onlyActiveFilter]);

  useEffect(() => {
    loadClients();
  }, [loadClients]);

  // Handlers
  const handlePaginationModelChange = (newModel: GridPaginationModel) => {
    setPaginationModel(newModel);
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  const handleEditClient = (client: Client) => {
    if (onEditClient) {
      onEditClient(client);
    }
  };

  const handleViewClient = (client: Client) => {
    setSelectedClient(client);
    setDetailDialogOpen(true);
  };

  const handleDeleteClient = async (client: Client) => {
    if (window.confirm(`¿Está seguro que desea ${client.is_active ? 'desactivar' : 'reactivar'} el cliente "${client.nombre_completo}"?`)) {
      try {
        setLoading(true);
        
        if (client.is_active) {
          await ClientsService.deleteClient(client.id);
        } else {
          await ClientsService.activateClient(client.id);
        }
        
        await loadClients();
        if (onRefresh) onRefresh();
      } catch (error: any) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleRefresh = () => {
    loadClients();
    if (onRefresh) onRefresh();
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setTipoClienteFilter('');
    setTipoDocumentoFilter('');
    setOnlyActiveFilter(true);
    setPaginationModel({ page: 0, pageSize: 25 });
  };

  // Definición de columnas
  const columns: GridColDef[] = [
    {
      field: 'numero_documento',
      headerName: 'Documento',
      width: 130,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontWeight: 500 }}>{params.value}</span>
          <span style={{ fontSize: '0.75rem', color: 'text.secondary' }}>
            {ClientsService.getDocumentTypeLabel(params.row.tipo_documento)}
          </span>
        </Box>
      ),
    },
    {
      field: 'nombre_completo',
      headerName: 'Nombre/Razón Social',
      flex: 1,
      minWidth: 200,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontWeight: 500 }}>{params.value}</span>
          {params.row.nombre_comercial && (
            <span style={{ fontSize: '0.75rem', color: 'text.secondary' }}>
              {params.row.nombre_comercial}
            </span>
          )}
        </Box>
      ),
    },
    {
      field: 'tipo_cliente',
      headerName: 'Tipo',
      width: 130,
      renderCell: (params) => (
        <Chip
          label={ClientsService.getClientTypeLabel(params.value)}
          size="small"
          color={params.value === ClientType.EMPRESA ? 'primary' : 'success'}
          variant="outlined"
        />
      ),
    },
    {
      field: 'email',
      headerName: 'Email',
      width: 200,
      renderCell: (params) => params.value || '-',
    },
    {
      field: 'telefono',
      headerName: 'Teléfono',
      width: 130,
      renderCell: (params) => params.value || '-',
    },
    {
      field: 'is_active',
      headerName: 'Estado',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Activo' : 'Inactivo'}
          size="small"
          color={params.value ? 'success' : 'error'}
          variant="filled"
        />
      ),
    },
    {
      field: 'created_at',
      headerName: 'Creado',
      width: 120,
      renderCell: (params) => new Date(params.value).toLocaleDateString('es-CO'),
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Acciones',
      width: 120,
      getActions: (params) => [
        <GridActionsCellItem
          key="view"
          icon={
            <Tooltip title="Ver detalles">
              <ViewIcon />
            </Tooltip>
          }
          label="Ver"
          onClick={() => handleViewClient(params.row)}
        />,
        <GridActionsCellItem
          key="edit"
          icon={
            <Tooltip title="Editar">
              <EditIcon />
            </Tooltip>
          }
          label="Editar"
          onClick={() => handleEditClient(params.row)}
        />,
        <GridActionsCellItem
          key="delete"
          icon={
            <Tooltip title={params.row.is_active ? 'Desactivar' : 'Reactivar'}>
              {params.row.is_active ? <DeleteIcon /> : <RestoreIcon />}
            </Tooltip>
          }
          label={params.row.is_active ? 'Desactivar' : 'Reactivar'}
          onClick={() => handleDeleteClient(params.row)}
        />,
      ],
    },
  ];

  return (
    <Box>
      {/* Filtros */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField
          size="small"
          placeholder="Buscar por nombre o documento..."
          value={searchTerm}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ minWidth: 250 }}
        />

        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Tipo Cliente</InputLabel>
          <Select
            value={tipoClienteFilter}
            label="Tipo Cliente"
            onChange={(e) => setTipoClienteFilter(e.target.value as ClientType | '')}
          >
            <MenuItem value="">Todos</MenuItem>
            <MenuItem value={ClientType.PERSONA_NATURAL}>Persona Natural</MenuItem>
            <MenuItem value={ClientType.EMPRESA}>Empresa</MenuItem>
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Tipo Documento</InputLabel>
          <Select
            value={tipoDocumentoFilter}
            label="Tipo Documento"
            onChange={(e) => setTipoDocumentoFilter(e.target.value as DocumentType | '')}
          >
            <MenuItem value="">Todos</MenuItem>
            <MenuItem value={DocumentType.CC}>Cédula</MenuItem>
            <MenuItem value={DocumentType.NIT}>NIT</MenuItem>
            <MenuItem value={DocumentType.CEDULA_EXTRANJERIA}>Cédula Extranjería</MenuItem>
            <MenuItem value={DocumentType.PASAPORTE}>Pasaporte</MenuItem>
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Estado</InputLabel>
          <Select
            value={onlyActiveFilter ? 'active' : 'all'}
            label="Estado"
            onChange={(e) => setOnlyActiveFilter(e.target.value === 'active')}
          >
            <MenuItem value="all">Todos</MenuItem>
            <MenuItem value="active">Solo Activos</MenuItem>
          </Select>
        </FormControl>

        <Tooltip title="Actualizar">
          <IconButton onClick={handleRefresh}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>

        <Chip
          label="Limpiar filtros"
          onClick={handleClearFilters}
          onDelete={handleClearFilters}
          variant="outlined"
          size="small"
        />
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* DataGrid */}
      <Box sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={clients}
          columns={columns}
          paginationModel={paginationModel}
          onPaginationModelChange={handlePaginationModelChange}
          pageSizeOptions={[10, 25, 50, 100]}
          rowCount={totalRows}
          paginationMode="server"
          loading={loading}
          disableRowSelectionOnClick
          sx={{
            '& .MuiDataGrid-row:hover': {
              backgroundColor: 'action.hover',
            },
            '& .MuiDataGrid-cell:focus': {
              outline: 'none',
            },
          }}
          localeText={{
            noRowsLabel: 'No se encontraron clientes',
            MuiTablePagination: {
              labelRowsPerPage: 'Filas por página:',
              labelDisplayedRows: ({ from, to, count }) =>
                `${from}–${to} de ${count !== -1 ? count : `más de ${to}`}`,
            },
          }}
        />
      </Box>

      {/* Client Detail Dialog */}
      <ClientDetailDialog
        client={selectedClient}
        open={detailDialogOpen}
        onClose={() => {
          setDetailDialogOpen(false);
          setSelectedClient(null);
        }}
        onEdit={(client) => {
          setDetailDialogOpen(false);
          setSelectedClient(null);
          handleEditClient(client);
        }}
      />
    </Box>
  );
};

export default ClientsList;