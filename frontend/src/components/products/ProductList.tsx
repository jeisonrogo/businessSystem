/**
 * Lista de productos con funcionalidades CRUD
 */

import React, { useState, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Avatar,
  Menu,
  MenuItem,
  Tooltip,
  Alert,
  Skeleton,
} from '@mui/material';
import {
  DataGrid,
  GridColDef,
  GridActionsCellItem,
  GridRowParams,
  GridPaginationModel,
} from '@mui/x-data-grid';
import {
  Edit,
  Delete,
  MoreVert,
  Inventory,
  Visibility,
  Warning,
} from '@mui/icons-material';
import { Product } from '../../types';

interface ProductListProps {
  products: Product[];
  loading?: boolean;
  error?: string;
  totalCount: number;
  paginationModel: GridPaginationModel;
  onPaginationModelChange: (model: GridPaginationModel) => void;
  onEdit: (product: Product) => void;
  onDelete: (product: Product) => void;
  onViewDetails: (product: Product) => void;
  onUpdateStock: (product: Product) => void;
}

const ProductList: React.FC<ProductListProps> = ({
  products,
  loading = false,
  error,
  totalCount,
  paginationModel,
  onPaginationModelChange,
  onEdit,
  onDelete,
  onViewDetails,
  onUpdateStock,
}) => {
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  const handleMenuOpen = useCallback((event: React.MouseEvent<HTMLElement>, product: Product) => {
    event.stopPropagation();
    setMenuAnchorEl(event.currentTarget);
    setSelectedProduct(product);
  }, []);

  const handleMenuClose = useCallback(() => {
    setMenuAnchorEl(null);
    setSelectedProduct(null);
  }, []);

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getStockColor = (stock: number): 'error' | 'warning' | 'success' => {
    if (stock === 0) return 'error';
    if (stock <= 10) return 'warning';
    return 'success';
  };

  const columns: GridColDef[] = [
    {
      field: 'url_foto',
      headerName: '',
      width: 60,
      sortable: false,
      filterable: false,
      renderCell: (params) => (
        <Avatar
          src={params.value || undefined}
          alt={params.row.nombre}
          variant="rounded"
          sx={{ width: 40, height: 40 }}
        >
          <Inventory />
        </Avatar>
      ),
    },
    {
      field: 'sku',
      headerName: 'SKU',
      width: 120,
      renderCell: (params) => (
        <Typography variant="body2" fontWeight="bold">
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'nombre',
      headerName: 'Nombre',
      flex: 1,
      minWidth: 200,
      renderCell: (params) => (
        <Box>
          <Typography variant="body2" fontWeight="medium">
            {params.value}
          </Typography>
          {params.row.descripcion && (
            <Typography variant="caption" color="text.secondary" noWrap>
              {params.row.descripcion}
            </Typography>
          )}
        </Box>
      ),
    },
    {
      field: 'precio_base',
      headerName: 'Precio Base',
      width: 120,
      type: 'number',
      renderCell: (params) => (
        <Typography variant="body2">
          {formatCurrency(params.value)}
        </Typography>
      ),
    },
    {
      field: 'precio_publico',
      headerName: 'Precio Público',
      width: 130,
      type: 'number',
      renderCell: (params) => (
        <Typography variant="body2" fontWeight="medium">
          {formatCurrency(params.value)}
        </Typography>
      ),
    },
    {
      field: 'stock',
      headerName: 'Stock',
      width: 100,
      type: 'number',
      renderCell: (params) => (
        <Chip
          label={params.value}
          color={getStockColor(params.value)}
          size="small"
          icon={params.value === 0 ? <Warning /> : undefined}
        />
      ),
    },
    {
      field: 'is_active',
      headerName: 'Estado',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Activo' : 'Inactivo'}
          color={params.value ? 'success' : 'default'}
          size="small"
        />
      ),
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Acciones',
      width: 120,
      getActions: (params: GridRowParams<Product>) => [
        <GridActionsCellItem
          key="view"
          icon={
            <Tooltip title="Ver detalles">
              <Visibility />
            </Tooltip>
          }
          label="Ver detalles"
          onClick={() => onViewDetails(params.row)}
        />,
        <GridActionsCellItem
          key="edit"
          icon={
            <Tooltip title="Editar">
              <Edit />
            </Tooltip>
          }
          label="Editar"
          onClick={() => onEdit(params.row)}
        />,
        <GridActionsCellItem
          key="more"
          icon={
            <Tooltip title="Más opciones">
              <MoreVert />
            </Tooltip>
          }
          label="Más opciones"
          onClick={(event) => handleMenuOpen(event, params.row)}
        />,
      ],
    },
  ];

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Error al cargar productos: {error}
      </Alert>
    );
  }

  return (
    <Box>
      <Card>
        <CardContent sx={{ p: 0 }}>
          <DataGrid
            rows={products}
            columns={columns}
            loading={loading}
            paginationMode="server"
            rowCount={totalCount}
            paginationModel={paginationModel}
            onPaginationModelChange={onPaginationModelChange}
            pageSizeOptions={[10, 25, 50, 100]}
            disableRowSelectionOnClick
            autoHeight
            sx={{
              border: 'none',
              '& .MuiDataGrid-cell:focus': {
                outline: 'none',
              },
              '& .MuiDataGrid-row:hover': {
                backgroundColor: 'action.hover',
              },
            }}
            slots={{
              loadingOverlay: () => (
                <Box sx={{ p: 2 }}>
                  {Array.from({ length: 10 }).map((_, index) => (
                    <Skeleton
                      key={index}
                      variant="rectangular"
                      height={52}
                      sx={{ mb: 1 }}
                    />
                  ))}
                </Box>
              ),
              noRowsOverlay: () => (
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: 400,
                  }}
                >
                  <Inventory sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">
                    No hay productos
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Crea tu primer producto para comenzar
                  </Typography>
                </Box>
              ),
            }}
          />
        </CardContent>
      </Card>

      {/* Menú contextual */}
      <Menu
        anchorEl={menuAnchorEl}
        open={Boolean(menuAnchorEl)}
        onClose={handleMenuClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem
          onClick={() => {
            if (selectedProduct) onUpdateStock(selectedProduct);
            handleMenuClose();
          }}
        >
          <Inventory sx={{ mr: 1 }} />
          Actualizar Stock
        </MenuItem>
        <MenuItem
          onClick={() => {
            if (selectedProduct) onDelete(selectedProduct);
            handleMenuClose();
          }}
          sx={{ color: 'error.main' }}
        >
          <Delete sx={{ mr: 1 }} />
          Eliminar
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default ProductList;