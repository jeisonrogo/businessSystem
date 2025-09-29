/**
 * Lista de productos con funcionalidades CRUD
 */

import React, { useState, useCallback } from 'react';
import {
  Box,
  Typography,
  Chip,
  Avatar,
  Menu,
  MenuItem,
  Tooltip,
  Alert,
  Skeleton,
  alpha,
  useTheme,
  Badge,
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
  ErrorOutline,
  CheckCircle,
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

  const theme = useTheme();

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

  const getStockIcon = (stock: number) => {
    if (stock === 0) return <ErrorOutline />;
    if (stock <= 10) return <Warning />;
    return <CheckCircle />;
  };

  const columns: GridColDef[] = [
    {
      field: 'imagen_url',
      headerName: '',
      width: 70,
      sortable: false,
      filterable: false,
      renderCell: (params) => (
        <Badge
          overlap="circular"
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          badgeContent={
            params.row.is_active ? (
              <CheckCircle
                sx={{
                  color: 'success.main',
                  fontSize: 14,
                  backgroundColor: 'white',
                  borderRadius: '50%',
                }}
              />
            ) : (
              <ErrorOutline
                sx={{
                  color: 'error.main',
                  fontSize: 14,
                  backgroundColor: 'white',
                  borderRadius: '50%',
                }}
              />
            )
          }
        >
          <Avatar
            src={params.value || undefined}
            alt={params.row.nombre}
            variant="rounded"
            sx={{
              width: 48,
              height: 48,
              border: `2px solid ${alpha(theme.palette.primary.main, 0.2)}`,
              backgroundColor: alpha(theme.palette.primary.main, 0.1),
            }}
          >
            <Inventory sx={{ color: 'primary.main' }} />
          </Avatar>
        </Badge>
      ),
    },
    {
      field: 'sku',
      headerName: 'SKU',
      width: 130,
      renderCell: (params) => (
        <Chip
          label={params.value}
          size="small"
          variant="outlined"
          sx={{
            fontWeight: 600,
            borderColor: alpha(theme.palette.primary.main, 0.3),
            color: 'primary.main',
            backgroundColor: alpha(theme.palette.primary.main, 0.05),
          }}
        />
      ),
    },
    {
      field: 'nombre',
      headerName: 'Producto',
      flex: 1,
      minWidth: 220,
      renderCell: (params) => (
        <Box sx={{ py: 1 }}>
          <Typography
            variant="body2"
            sx={{
              fontWeight: 600,
              color: 'text.primary',
              mb: 0.5,
              lineHeight: 1.3,
            }}
          >
            {params.value}
          </Typography>
          {params.row.descripcion && (
            <Typography
              variant="caption"
              sx={{
                color: 'text.secondary',
                fontSize: '0.75rem',
                lineHeight: 1.2,
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
              }}
            >
              {params.row.descripcion}
            </Typography>
          )}
        </Box>
      ),
    },
    {
      field: 'precio_base',
      headerName: 'Precio Base',
      width: 130,
      type: 'number',
      renderCell: (params) => (
        <Typography
          variant="body2"
          sx={{
            fontWeight: 500,
            color: 'text.secondary',
            fontSize: '0.875rem',
          }}
        >
          {formatCurrency(params.value)}
        </Typography>
      ),
    },
    {
      field: 'precio_publico',
      headerName: 'Precio Público',
      width: 140,
      type: 'number',
      renderCell: (params) => (
        <Chip
          label={formatCurrency(params.value)}
          size="small"
          sx={{
            fontWeight: 600,
            backgroundColor: alpha(theme.palette.success.main, 0.1),
            color: 'success.main',
            border: `1px solid ${alpha(theme.palette.success.main, 0.3)}`,
            fontSize: '0.8rem',
          }}
        />
      ),
    },
    {
      field: 'stock_local_actual',
      headerName: 'Stock',
      width: 110,
      type: 'number',
      renderCell: (params) => {
        const stockValue = params.value ?? 0;
        const stockColor = getStockColor(stockValue);
        return (
          <Chip
            label={stockValue.toLocaleString()}
            color={stockColor}
            size="small"
            icon={getStockIcon(stockValue)}
            sx={{
              fontWeight: 600,
              minWidth: 80,
              '& .MuiChip-icon': {
                fontSize: 16,
              },
            }}
          />
        );
      },
    },
    {
      field: 'is_active',
      headerName: 'Estado',
      width: 110,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Activo' : 'Inactivo'}
          color={params.value ? 'success' : 'error'}
          size="small"
          variant={params.value ? 'filled' : 'outlined'}
          icon={params.value ? <CheckCircle /> : <ErrorOutline />}
          sx={{
            fontWeight: 600,
            '& .MuiChip-icon': {
              fontSize: 16,
            },
          }}
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
              borderRadius: 0,
              '& .MuiDataGrid-main': {
                borderRadius: 0,
              },
              '& .MuiDataGrid-columnHeaders': {
                backgroundColor: alpha(theme.palette.primary.main, 0.04),
                borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
                borderRadius: 0,
                '& .MuiDataGrid-columnHeader': {
                  '&:focus': { outline: 'none' },
                  '&:focus-within': { outline: 'none' },
                },
                '& .MuiDataGrid-columnHeaderTitle': {
                  fontWeight: 600,
                  fontSize: '0.875rem',
                  color: theme.palette.text.primary,
                },
              },
              '& .MuiDataGrid-cell': {
                borderBottom: `1px solid ${alpha(theme.palette.divider, 0.05)}`,
                '&:focus': { outline: 'none' },
                '&:focus-within': { outline: 'none' },
              },
              '& .MuiDataGrid-row': {
                '&:hover': {
                  backgroundColor: alpha(theme.palette.primary.main, 0.04),
                },
                '&.Mui-selected': {
                  backgroundColor: alpha(theme.palette.primary.main, 0.08),
                  '&:hover': {
                    backgroundColor: alpha(theme.palette.primary.main, 0.12),
                  },
                },
              },
              '& .MuiDataGrid-footerContainer': {
                backgroundColor: alpha(theme.palette.background.default, 0.5),
                borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
              },
            }}
            slots={{
              loadingOverlay: () => (
                <Box sx={{ p: 3, width: '100%' }}>
                  {Array.from({ length: 8 }).map((_, index) => (
                    <Skeleton
                      key={index}
                      variant="rectangular"
                      height={52}
                      sx={{
                        mb: 1,
                        borderRadius: 1,
                        opacity: 1 - (index * 0.1),
                      }}
                      animation="wave"
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
                    gap: 2,
                  }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: 80,
                      height: 80,
                      borderRadius: '50%',
                      backgroundColor: alpha(theme.palette.primary.main, 0.1),
                      color: alpha(theme.palette.primary.main, 0.6),
                      mb: 1,
                    }}
                  >
                    <Inventory sx={{ fontSize: 36 }} />
                  </Box>
                  <Typography
                    variant="h6"
                    sx={{
                      color: 'text.secondary',
                      fontWeight: 600,
                    }}
                  >
                    No hay productos
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{
                      color: 'text.secondary',
                      textAlign: 'center',
                      maxWidth: 300,
                    }}
                  >
                    Crea tu primer producto para comenzar a gestionar tu inventario
                  </Typography>
                </Box>
              ),
            }}
          />

      {/* Menú contextual moderno */}
      <Menu
        anchorEl={menuAnchorEl}
        open={Boolean(menuAnchorEl)}
        onClose={handleMenuClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        PaperProps={{
          sx: {
            borderRadius: 2,
            mt: 1,
            minWidth: 180,
            boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.15)}`,
            border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
          },
        }}
      >
        <MenuItem
          onClick={() => {
            if (selectedProduct) onUpdateStock(selectedProduct);
            handleMenuClose();
          }}
          sx={{
            py: 1.5,
            px: 2,
            '&:hover': {
              backgroundColor: alpha(theme.palette.primary.main, 0.1),
              color: 'primary.main',
            },
          }}
        >
          <Inventory sx={{ mr: 1.5, fontSize: 20 }} />
          Actualizar Stock
        </MenuItem>
        <MenuItem
          onClick={() => {
            if (selectedProduct) onDelete(selectedProduct);
            handleMenuClose();
          }}
          sx={{
            py: 1.5,
            px: 2,
            color: 'error.main',
            '&:hover': {
              backgroundColor: alpha(theme.palette.error.main, 0.1),
              color: 'error.dark',
            },
          }}
        >
          <Delete sx={{ mr: 1.5, fontSize: 20 }} />
          Eliminar
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default ProductList;