/**
 * Lista de facturas con DataGrid avanzado
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
  Alert,
  Typography,
  Button
} from '@mui/material';
import {
  Search as SearchIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Refresh as RefreshIcon,
  Payment as PaymentIcon,
  Print as PrintIcon
} from '@mui/icons-material';
import { DataGrid, GridColDef, GridPaginationModel, GridActionsCellItem } from '@mui/x-data-grid';
import { InvoicesService, InvoiceListParams } from '../../services/invoicesService';
import { Invoice, InvoiceStatus, InvoiceType } from '../../types';
import InvoiceDetailDialog from './InvoiceDetailDialog';

interface InvoicesListProps {
  onEditInvoice?: (invoice: Invoice) => void;
  onRefresh?: () => void;
  filterOverdue?: boolean;
}

const InvoicesList: React.FC<InvoicesListProps> = ({
  onEditInvoice,
  onRefresh,
  filterOverdue = false
}) => {
  // Estados principales
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);

  // Estados para filtros y paginación
  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 25,
  });
  const [totalRows, setTotalRows] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [estadoFilter, setEstadoFilter] = useState<InvoiceStatus | ''>('');
  const [tipoFacturaFilter, setTipoFacturaFilter] = useState<InvoiceType | ''>('');
  const [onlyActiveFilter, setOnlyActiveFilter] = useState(true);

  // Debounce para búsqueda
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 500);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Cargar facturas
  const loadInvoices = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      if (filterOverdue) {
        // Cargar facturas vencidas
        try {
          const overdueInvoices = await InvoicesService.getOverdueInvoices();
          setInvoices(overdueInvoices);
          setTotalRows(overdueInvoices.length);
        } catch (error: any) {
          console.error('Error al cargar facturas vencidas:', error.message);
          setInvoices([]);
          setTotalRows(0);
        }
      } else {
        // Cargar facturas con filtros normales
        const params: InvoiceListParams = {
          page: paginationModel.page + 1, // API usa 1-based indexing
          limit: Math.min(paginationModel.pageSize, 100),
          only_active: onlyActiveFilter,
        };

        if (debouncedSearchTerm) {
          params.search = debouncedSearchTerm;
        }

        if (estadoFilter) {
          params.estado = estadoFilter;
        }

        if (tipoFacturaFilter) {
          params.tipo_factura = tipoFacturaFilter;
        }

        try {
          const response = await InvoicesService.getInvoices(params);
          setInvoices(response.items || []);
          setTotalRows(response.total || 0);
        } catch (error: any) {
          console.error('Error al cargar facturas:', error.message);
          setInvoices([]);
          setTotalRows(0);
        }
      }
    } catch (error: any) {
      console.error('Error al cargar facturas:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [paginationModel, debouncedSearchTerm, estadoFilter, tipoFacturaFilter, onlyActiveFilter, filterOverdue]);

  useEffect(() => {
    loadInvoices();
  }, [loadInvoices]);

  // Handlers
  const handlePaginationModelChange = (newModel: GridPaginationModel) => {
    setPaginationModel(newModel);
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  const handleEditInvoice = (invoice: Invoice) => {
    if (onEditInvoice) {
      onEditInvoice(invoice);
    }
  };

  const handleViewInvoice = (invoice: Invoice) => {
    setSelectedInvoice(invoice);
    setDetailDialogOpen(true);
  };

  const handleMarkAsPaid = async (invoice: Invoice) => {
    if (window.confirm(`¿Está seguro que desea marcar como pagada la factura "${invoice.numero_factura}"?`)) {
      try {
        setLoading(true);
        
        await InvoicesService.markAsPaid(invoice.id, {
          forma_pago: 'EFECTIVO',
          fecha_pago: new Date().toISOString().split('T')[0],
          observaciones: 'Pago registrado desde el sistema',
        });
        
        await loadInvoices();
        if (onRefresh) onRefresh();
      } catch (error: any) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleDeleteInvoice = async (invoice: Invoice) => {
    if (window.confirm(`¿Está seguro que desea anular la factura "${invoice.numero_factura}"? Esta acción reversará los movimientos contables e inventario.`)) {
      try {
        setLoading(true);
        
        await InvoicesService.deleteInvoice(invoice.id);
        
        await loadInvoices();
        if (onRefresh) onRefresh();
      } catch (error: any) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleRefresh = () => {
    loadInvoices();
    if (onRefresh) onRefresh();
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setEstadoFilter('');
    setTipoFacturaFilter('');
    setOnlyActiveFilter(true);
    setPaginationModel({ page: 0, pageSize: 25 });
  };

  // Definición de columnas
  const columns: GridColDef[] = [
    {
      field: 'numero_factura',
      headerName: 'Número',
      width: 120,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontWeight: 500 }}>
            {InvoicesService.formatInvoiceNumber(params.value)}
          </span>
          <span style={{ fontSize: '0.75rem', color: 'text.secondary' }}>
            {new Date(params.row.fecha_emision).toLocaleDateString('es-CO')}
          </span>
        </Box>
      ),
    },
    {
      field: 'cliente',
      headerName: 'Cliente',
      flex: 1,
      minWidth: 200,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontWeight: 500 }}>{params.row.cliente_nombre || 'N/A'}</span>
          <span style={{ fontSize: '0.75rem', color: 'text.secondary' }}>
            {params.row.cliente_documento || ''}
          </span>
        </Box>
      ),
    },
    {
      field: 'tipo_factura',
      headerName: 'Tipo',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={InvoicesService.getInvoiceTypeLabel(params.value)}
          size="small"
          color={params.value === InvoiceType.VENTA ? 'primary' : 'success'}
          variant="outlined"
        />
      ),
    },
    {
      field: 'estado',
      headerName: 'Estado',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={InvoicesService.getInvoiceStatusLabel(params.value)}
          size="small"
          color={InvoicesService.getInvoiceStatusColor(params.value)}
          variant="filled"
        />
      ),
    },
    {
      field: 'total_factura',
      headerName: 'Total',
      width: 130,
      type: 'number',
      align: 'right',
      headerAlign: 'right',
      renderCell: (params) => (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
          <span style={{ fontWeight: 500 }}>
            {InvoicesService.formatCurrency(params.value)}
          </span>
          {params.row.total_descuento > 0 && (
            <span style={{ fontSize: '0.75rem', color: 'success.main' }}>
              Desc: {InvoicesService.formatCurrency(params.row.total_descuento)}
            </span>
          )}
        </Box>
      ),
    },
    {
      field: 'fecha_vencimiento',
      headerName: 'Vencimiento',
      width: 120,
      renderCell: (params) => {
        if (!params.value) return '-';
        
        const vencimiento = new Date(params.value);
        const hoy = new Date();
        const estaVencida = vencimiento < hoy && params.row.estado === InvoiceStatus.EMITIDA;
        
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span style={{ 
              color: estaVencida ? 'error.main' : 'inherit',
              fontWeight: estaVencida ? 500 : 'normal'
            }}>
              {vencimiento.toLocaleDateString('es-CO')}
            </span>
            {estaVencida && (
              <Chip
                label="VENCIDA"
                size="small"
                color="error"
                variant="filled"
                sx={{ fontSize: '0.6rem', height: '16px' }}
              />
            )}
          </Box>
        );
      },
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Acciones',
      width: 200,
      sortable: false,
      filterable: false,
      disableColumnMenu: true,
      getActions: (params) => {
        const actions = [
          <GridActionsCellItem
            key="view"
            icon={
              <Tooltip title="Ver detalles">
                <ViewIcon />
              </Tooltip>
            }
            label="Ver"
            onClick={() => handleViewInvoice(params.row)}
          />,
        ];

        // Solo agregar acciones de edición para facturas EMITIDA
        if (params.row.estado === InvoiceStatus.EMITIDA) {
          actions.push(
            <GridActionsCellItem
              key="edit"
              icon={
                <Tooltip title="Editar factura">
                  <EditIcon />
                </Tooltip>
              }
              label="Editar"
              onClick={() => handleEditInvoice(params.row)}
              disabled={false}
            />,
            <GridActionsCellItem
              key="pay"
              icon={
                <Tooltip title="Marcar como pagada">
                  <PaymentIcon />
                </Tooltip>
              }
              label="Pagar"
              onClick={() => handleMarkAsPaid(params.row)}
            />,
            <GridActionsCellItem
              key="delete"
              icon={
                <Tooltip title="Anular factura">
                  <DeleteIcon />
                </Tooltip>
              }
              label="Anular"
              onClick={() => handleDeleteInvoice(params.row)}
            />
          );
        }

        // Acción de impresión siempre disponible
        actions.push(
          <GridActionsCellItem
            key="print"
            icon={
              <Tooltip title="Imprimir">
                <PrintIcon />
              </Tooltip>
            }
            label="Imprimir"
            onClick={async () => {
              try {
                const { InvoicePrintUtils } = await import('../../utils/invoicePrint');
                await InvoicePrintUtils.printInvoice(params.row, {
                  companyName: 'Sistema de Gestión Empresarial',
                  companyAddress: 'Dirección de su empresa',
                  companyPhone: 'Teléfono de contacto',
                  companyEmail: 'contacto@suempresa.com'
                });
              } catch (error) {
                console.error('Error al imprimir factura:', error);
              }
            }}
          />
        );

        return actions;
      },
    },
  ];

  return (
    <Box>
      {/* Filtros - Solo mostrar si no es vista de vencidas */}
      {!filterOverdue && (
        <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          <TextField
            size="small"
            placeholder="Buscar por número, cliente..."
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

          <FormControl size="small" sx={{ minWidth: 140 }}>
            <InputLabel>Estado</InputLabel>
            <Select
              value={estadoFilter}
              label="Estado"
              onChange={(e) => setEstadoFilter(e.target.value as InvoiceStatus | '')}
            >
              <MenuItem value="">Todos</MenuItem>
              <MenuItem value={InvoiceStatus.EMITIDA}>Emitida</MenuItem>
              <MenuItem value={InvoiceStatus.PAGADA}>Pagada</MenuItem>
              <MenuItem value={InvoiceStatus.ANULADA}>Anulada</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 130 }}>
            <InputLabel>Tipo</InputLabel>
            <Select
              value={tipoFacturaFilter}
              label="Tipo"
              onChange={(e) => setTipoFacturaFilter(e.target.value as InvoiceType | '')}
            >
              <MenuItem value="">Todos</MenuItem>
              <MenuItem value={InvoiceType.VENTA}>Venta</MenuItem>
              <MenuItem value={InvoiceType.SERVICIO}>Servicio</MenuItem>
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
              <MenuItem value="active">Solo Activas</MenuItem>
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
      )}

      {/* Título para vista de vencidas */}
      {filterOverdue && (
        <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" color="error.main">
            Facturas Vencidas ({invoices.length})
          </Typography>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            size="small"
          >
            Actualizar
          </Button>
        </Box>
      )}

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* DataGrid */}
      <Box sx={{ height: filterOverdue ? 500 : 600, width: '100%' }}>
        {invoices.length === 0 && !loading && !error && (
          <Box 
            sx={{ 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center', 
              justifyContent: 'center', 
              height: '100%',
              color: 'text.secondary',
              gap: 2,
              p: 4
            }}
          >
            <Typography variant="h6">
              {filterOverdue ? 'No hay facturas vencidas' : 'No hay facturas registradas'}
            </Typography>
            <Typography variant="body2" textAlign="center">
              {filterOverdue 
                ? 'Todas las facturas están al día' 
                : 'Comienza creando tu primera factura usando el botón "+" en la esquina inferior derecha.'
              }
            </Typography>
          </Box>
        )}
        <DataGrid
          rows={invoices}
          columns={columns}
          paginationModel={paginationModel}
          onPaginationModelChange={handlePaginationModelChange}
          pageSizeOptions={[10, 25, 50, 100]}
          rowCount={totalRows}
          paginationMode={filterOverdue ? "client" : "server"}
          loading={loading}
          disableRowSelectionOnClick
          sx={{
            '& .MuiDataGrid-row:hover': {
              backgroundColor: 'action.hover',
            },
            '& .MuiDataGrid-cell:focus': {
              outline: 'none',
            },
            '& .MuiDataGrid-actionsCell': {
              gap: 0.5,
            },
            '& .MuiDataGrid-actionsCellButton': {
              padding: '2px',
            },
          }}
          localeText={{
            noRowsLabel: filterOverdue ? 'No hay facturas vencidas' : 'No se encontraron facturas',
            MuiTablePagination: {
              labelRowsPerPage: 'Filas por página:',
              labelDisplayedRows: ({ from, to, count }) =>
                `${from}–${to} de ${count !== -1 ? count : `más de ${to}`}`,
            },
          }}
        />
      </Box>

      {/* Invoice Detail Dialog */}
      <InvoiceDetailDialog
        invoice={selectedInvoice}
        open={detailDialogOpen}
        onClose={() => {
          setDetailDialogOpen(false);
          setSelectedInvoice(null);
        }}
        onEdit={(invoice) => {
          setDetailDialogOpen(false);
          setSelectedInvoice(null);
          handleEditInvoice(invoice);
        }}
        onMarkAsPaid={async (invoice, paymentData) => {
          try {
            await InvoicesService.markAsPaid(invoice.id, paymentData);
            setDetailDialogOpen(false);
            setSelectedInvoice(null);
            await loadInvoices();
            if (onRefresh) onRefresh();
          } catch (error: any) {
            setError(error.message);
          }
        }}
      />
    </Box>
  );
};

export default InvoicesList;