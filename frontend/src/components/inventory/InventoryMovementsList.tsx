/**
 * Lista de Movimientos de Inventario
 * Componente con DataGrid para mostrar y filtrar movimientos de inventario
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  TextField,
  MenuItem,
  Button,
  IconButton,
  Tooltip,
  Alert,
  Chip,
  Typography,
} from '@mui/material';
import {
  DataGrid,
  GridColDef,
  GridPaginationModel,
  GridSortModel,
  GridToolbar,
} from '@mui/x-data-grid';
import {
  Refresh,
  FilterList,
  Clear,
  Visibility,
  TrendingUp,
  TrendingDown,
  ReportProblem,
  Tune,
  GetApp,
} from '@mui/icons-material';

import { InventoryService } from '../../services/inventoryService';
import { ProductService } from '../../services/productService';
import {
  InventoryMovement,
  MovementType,
  InventoryMovementListResponse,
} from '../../types';
import MovementDetailsModal from './MovementDetailsModal';
import { exportMovementsToCSV } from '../../utils/exportUtils';

interface InventoryMovementsListProps {
  onRefresh?: () => void;
  loading?: boolean;
}

const InventoryMovementsList: React.FC<InventoryMovementsListProps> = ({
  onRefresh,
  loading: externalLoading = false,
}) => {
  const [movements, setMovements] = useState<InventoryMovement[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 25,
  });
  const [sortModel, setSortModel] = useState<GridSortModel>([
    { field: 'created_at', sort: 'desc' },
  ]);
  
  // Filtros
  const [filters, setFilters] = useState({
    search: '',
    tipo_movimiento: '',
    producto_id: '',
    fecha_desde: '',
    fecha_hasta: '',
    referencia: '',
  });
  const [showFilters, setShowFilters] = useState(false);
  const [total, setTotal] = useState(0);
  const [selectedMovement, setSelectedMovement] = useState<InventoryMovement | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  // Cargar movimientos
  const loadMovements = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params: any = {
        page: paginationModel.page + 1,
        limit: paginationModel.pageSize,
      };

      // Agregar filtros activos
      if (filters.search.trim()) params.search = filters.search;
      if (filters.tipo_movimiento) params.tipo_movimiento = filters.tipo_movimiento;
      if (filters.producto_id) params.producto_id = filters.producto_id;
      if (filters.fecha_desde) params.fecha_desde = filters.fecha_desde;
      if (filters.fecha_hasta) params.fecha_hasta = filters.fecha_hasta;
      if (filters.referencia.trim()) params.referencia = filters.referencia;

      // Agregar ordenamiento
      if (sortModel.length > 0) {
        const sort = sortModel[0];
        params.order_by = sort.field;
        params.order_dir = sort.sort;
      }

      const response: InventoryMovementListResponse = await InventoryService.getMovements(params);
      setMovements(response.movimientos);
      setTotal(response.total);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [paginationModel, sortModel, filters]);

  useEffect(() => {
    loadMovements();
  }, [loadMovements]);

  const handleRefresh = () => {
    loadMovements();
    onRefresh?.();
  };

  const handleFilterChange = (field: string, value: string) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setPaginationModel({ page: 0, pageSize: paginationModel.pageSize });
  };

  const handleClearFilters = () => {
    setFilters({
      search: '',
      tipo_movimiento: '',
      producto_id: '',
      fecha_desde: '',
      fecha_hasta: '',
      referencia: '',
    });
    setPaginationModel({ page: 0, pageSize: paginationModel.pageSize });
  };

  const getMovementIcon = (type: MovementType) => {
    switch (type) {
      case MovementType.ENTRADA:
        return <TrendingUp fontSize="small" />;
      case MovementType.SALIDA:
        return <TrendingDown fontSize="small" />;
      case MovementType.MERMA:
        return <ReportProblem fontSize="small" />;
      case MovementType.AJUSTE:
        return <Tune fontSize="small" />;
      default:
        return <Visibility fontSize="small" />;
    }
  };

  const typeLabels = InventoryService.getMovementTypeLabels();
  const typeColors = InventoryService.getMovementTypeColors();

  const columns: GridColDef[] = [
    {
      field: 'created_at',
      headerName: 'Fecha',
      width: 120,
      type: 'dateTime',
      valueGetter: (params) => new Date(params.row.created_at),
      renderCell: (params) => {
        const date = new Date(params.row.created_at);
        return date.toLocaleDateString('es-CO', {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric',
        });
      },
    },
    {
      field: 'tipo_movimiento',
      headerName: 'Tipo',
      width: 120,
      renderCell: (params) => {
        const type = params.value as MovementType;
        return (
          <Chip
            icon={getMovementIcon(type)}
            label={typeLabels[type]}
            size="small"
            sx={{
              backgroundColor: typeColors[type] + '20',
              color: typeColors[type],
              fontWeight: 'bold',
              '& .MuiChip-icon': {
                color: typeColors[type],
              },
            }}
          />
        );
      },
    },
    {
      field: 'producto',
      headerName: 'Producto',
      width: 200,
      flex: 1,
      renderCell: (params) => (
        <Box>
          <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
            {params.row.producto?.nombre || 'N/A'}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            SKU: {params.row.producto?.sku || 'N/A'}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'cantidad',
      headerName: 'Cantidad',
      width: 100,
      type: 'number',
      align: 'right',
      headerAlign: 'right',
      renderCell: (params) => {
        const type = params.row.tipo_movimiento as MovementType;
        const cantidad = params.value;
        const formatted = InventoryService.formatQuantityWithSign(type, cantidad);
        
        return (
          <Typography
            variant="body2"
            sx={{
              fontWeight: 'bold',
              color: type === MovementType.ENTRADA || type === MovementType.AJUSTE 
                ? 'success.main' 
                : 'error.main',
            }}
          >
            {formatted}
          </Typography>
        );
      },
    },
    {
      field: 'precio_unitario',
      headerName: 'Precio Unit.',
      width: 120,
      type: 'number',
      align: 'right',
      headerAlign: 'right',
      renderCell: (params) => InventoryService.formatCurrency(params.value),
    },
    {
      field: 'valor_total',
      headerName: 'Valor Total',
      width: 130,
      type: 'number',
      align: 'right',
      headerAlign: 'right',
      valueGetter: (params) => InventoryService.calculateMovementValue(params.row),
      renderCell: (params) => (
        <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
          {InventoryService.formatCurrency(params.value)}
        </Typography>
      ),
    },
    {
      field: 'stock_anterior',
      headerName: 'Stock Ant.',
      width: 100,
      type: 'number',
      align: 'right',
      headerAlign: 'right',
    },
    {
      field: 'stock_posterior',
      headerName: 'Stock Post.',
      width: 100,
      type: 'number',
      align: 'right',
      headerAlign: 'right',
    },
    {
      field: 'referencia',
      headerName: 'Referencia',
      width: 120,
      renderCell: (params) => params.value || '-',
    },
    {
      field: 'observaciones',
      headerName: 'Observaciones',
      width: 150,
      renderCell: (params) => (
        <Tooltip title={params.value || ''} arrow>
          <Typography
            variant="body2"
            sx={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {params.value || '-'}
          </Typography>
        </Tooltip>
      ),
    },
    {
      field: 'actions',
      headerName: 'Acciones',
      width: 80,
      sortable: false,
      filterable: false,
      renderCell: (params) => (
        <Tooltip title="Ver detalles">
          <IconButton
            size="small"
            onClick={async () => {
              try {
                // Cargar detalles del producto si no están disponibles
                let movementWithProduct = params.row;
                if (!movementWithProduct.producto && movementWithProduct.producto_id) {
                  const productDetails = await ProductService.getProductById(movementWithProduct.producto_id);
                  movementWithProduct = {
                    ...movementWithProduct,
                    producto: productDetails
                  };
                }
                setSelectedMovement(movementWithProduct);
                setShowDetailsModal(true);
              } catch (error) {
                console.error('Error loading product details:', error);
                setSelectedMovement(params.row);
                setShowDetailsModal(true);
              }
            }}
          >
            <Visibility fontSize="small" />
          </IconButton>
        </Tooltip>
      ),
    },
  ];

  return (
    <Box>
      {/* Controles superiores */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" component="h2">
          Movimientos de Inventario
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Exportar a CSV">
            <span>
              <IconButton
                onClick={() => exportMovementsToCSV(movements)}
                disabled={loading || externalLoading || movements.length === 0}
              >
                <GetApp />
              </IconButton>
            </span>
          </Tooltip>
          <Tooltip title="Mostrar/ocultar filtros">
            <IconButton
              onClick={() => setShowFilters(!showFilters)}
              color={showFilters ? 'primary' : 'default'}
            >
              <FilterList />
            </IconButton>
          </Tooltip>
          <Tooltip title="Refrescar">
            <span>
              <IconButton 
                onClick={handleRefresh} 
                disabled={loading || externalLoading}
              >
                <Refresh />
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </Box>

      {/* Filtros */}
      {showFilters && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
            <TextField
              label="Buscar"
              size="small"
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              sx={{ minWidth: 200 }}
            />
            
            <TextField
              select
              label="Tipo de Movimiento"
              size="small"
              value={filters.tipo_movimiento}
              onChange={(e) => handleFilterChange('tipo_movimiento', e.target.value)}
              sx={{ minWidth: 150 }}
            >
              <MenuItem value="">Todos</MenuItem>
              {Object.entries(typeLabels).map(([key, label]) => (
                <MenuItem key={key} value={key}>
                  {label}
                </MenuItem>
              ))}
            </TextField>

            <TextField
              label="Fecha Desde"
              type="date"
              size="small"
              value={filters.fecha_desde}
              onChange={(e) => handleFilterChange('fecha_desde', e.target.value)}
              InputLabelProps={{ shrink: true }}
              sx={{ minWidth: 150 }}
            />

            <TextField
              label="Fecha Hasta"
              type="date"
              size="small"
              value={filters.fecha_hasta}
              onChange={(e) => handleFilterChange('fecha_hasta', e.target.value)}
              InputLabelProps={{ shrink: true }}
              sx={{ minWidth: 150 }}
            />

            <TextField
              label="Referencia"
              size="small"
              value={filters.referencia}
              onChange={(e) => handleFilterChange('referencia', e.target.value)}
              sx={{ minWidth: 150 }}
            />

            <Button
              variant="outlined"
              startIcon={<Clear />}
              onClick={handleClearFilters}
              size="small"
            >
              Limpiar
            </Button>
          </Box>
        </Paper>
      )}

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* DataGrid */}
      <Paper sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={movements}
          columns={columns}
          loading={loading || externalLoading}
          paginationMode="server"
          sortingMode="server"
          paginationModel={paginationModel}
          onPaginationModelChange={setPaginationModel}
          sortModel={sortModel}
          onSortModelChange={setSortModel}
          rowCount={total}
          pageSizeOptions={[10, 25, 50, 100]}
          disableRowSelectionOnClick
          slots={{
            toolbar: GridToolbar,
          }}
          slotProps={{
            toolbar: {
              showQuickFilter: false,
              quickFilterProps: { debounceMs: 500 },
            },
          }}
          sx={{
            '& .MuiDataGrid-cell': {
              border: 'none',
            },
            '& .MuiDataGrid-row:hover': {
              backgroundColor: 'action.hover',
            },
          }}
        />
      </Paper>

      {/* Modal de detalles */}
      <MovementDetailsModal
        open={showDetailsModal}
        movement={selectedMovement}
        onClose={() => {
          setShowDetailsModal(false);
          setSelectedMovement(null);
        }}
      />
    </Box>
  );
};

export default InventoryMovementsList;