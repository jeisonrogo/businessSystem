/**
 * Modern Data Grid Component - Professional Business Interface
 * Sistema de Gestión Empresarial
 */

import React from 'react';
import {
  Box,
  alpha,
  useTheme,
  Typography,
  Skeleton,
  Alert,
} from '@mui/material';
import {
  DataGrid,
  GridColDef,
  GridPaginationModel,
  DataGridProps,
  GridRowParams,
  gridClasses,
} from '@mui/x-data-grid';
import { SvgIconComponent } from '@mui/icons-material';
import { Search as SearchIcon } from '@mui/icons-material';
import ModernCard from './ModernCard';

interface ModernDataGridProps extends Omit<DataGridProps, 'rows' | 'columns'> {
  rows: any[];
  columns: GridColDef[];
  loading?: boolean;
  error?: string;
  totalCount?: number;
  paginationModel?: GridPaginationModel;
  onPaginationModelChange?: (model: GridPaginationModel) => void;
  title?: string;
  description?: string;
  emptyStateIcon?: SvgIconComponent;
  emptyStateTitle?: string;
  emptyStateDescription?: string;
  variant?: 'default' | 'gradient' | 'glass' | 'bordered';
}

const ModernDataGrid: React.FC<ModernDataGridProps> = ({
  rows,
  columns,
  loading = false,
  error,
  totalCount,
  paginationModel,
  onPaginationModelChange,
  title,
  description,
  emptyStateIcon: EmptyIcon = SearchIcon,
  emptyStateTitle = 'No hay datos',
  emptyStateDescription = 'No se encontraron elementos para mostrar',
  variant = 'glass',
  ...props
}) => {
  const theme = useTheme();

  const customLoadingOverlay = () => (
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
  );

  const customNoRowsOverlay = () => (
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
        <EmptyIcon sx={{ fontSize: 36 }} />
      </Box>
      <Typography
        variant="h6"
        sx={{
          color: 'text.secondary',
          fontWeight: 600,
        }}
      >
        {emptyStateTitle}
      </Typography>
      <Typography
        variant="body2"
        sx={{
          color: 'text.secondary',
          textAlign: 'center',
          maxWidth: 300,
        }}
      >
        {emptyStateDescription}
      </Typography>
    </Box>
  );

  if (error) {
    return (
      <ModernCard variant={variant}>
        <Box sx={{ p: 3 }}>
          {(title || description) && (
            <Box sx={{ mb: 3 }}>
              {title && (
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  {title}
                </Typography>
              )}
              {description && (
                <Typography variant="body2" color="text.secondary">
                  {description}
                </Typography>
              )}
            </Box>
          )}
          <Alert severity="error" sx={{ borderRadius: 2 }}>
            {error}
          </Alert>
        </Box>
      </ModernCard>
    );
  }

  return (
    <ModernCard variant={variant}>
      <Box>
        {/* Header */}
        {(title || description) && (
          <Box sx={{ p: 3, pb: 0 }}>
            {title && (
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 600,
                  mb: description ? 0.5 : 0,
                  color: 'text.primary',
                }}
              >
                {title}
              </Typography>
            )}
            {description && (
              <Typography variant="body2" color="text.secondary">
                {description}
              </Typography>
            )}
          </Box>
        )}

        {/* Data Grid */}
        <Box sx={{ height: 'auto', width: '100%' }}>
          <DataGrid
            rows={rows}
            columns={columns}
            loading={loading}
            paginationMode={totalCount ? "server" : "client"}
            rowCount={totalCount}
            paginationModel={paginationModel}
            onPaginationModelChange={onPaginationModelChange}
            pageSizeOptions={[10, 25, 50, 100]}
            disableRowSelectionOnClick
            autoHeight
            sx={{
              border: 'none',
              '& .MuiDataGrid-main': {
                borderRadius: 0,
              },
              '& .MuiDataGrid-columnHeaders': {
                backgroundColor: alpha(theme.palette.primary.main, 0.04),
                borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
                borderRadius: 0,
                '& .MuiDataGrid-columnHeader': {
                  '&:focus': {
                    outline: 'none',
                  },
                  '&:focus-within': {
                    outline: 'none',
                  },
                },
                '& .MuiDataGrid-columnHeaderTitle': {
                  fontWeight: 600,
                  fontSize: '0.875rem',
                  color: theme.palette.text.primary,
                },
              },
              '& .MuiDataGrid-cell': {
                borderBottom: `1px solid ${alpha(theme.palette.divider, 0.05)}`,
                '&:focus': {
                  outline: 'none',
                },
                '&:focus-within': {
                  outline: 'none',
                },
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
                borderRadius: 0,
              },
              '& .MuiDataGrid-virtualScroller': {
                '&::-webkit-scrollbar': {
                  width: 8,
                  height: 8,
                },
                '&::-webkit-scrollbar-track': {
                  background: alpha(theme.palette.grey[300], 0.3),
                  borderRadius: 4,
                },
                '&::-webkit-scrollbar-thumb': {
                  background: alpha(theme.palette.grey[500], 0.5),
                  borderRadius: 4,
                  '&:hover': {
                    background: alpha(theme.palette.grey[500], 0.7),
                  },
                },
              },
            }}
            slots={{
              loadingOverlay: customLoadingOverlay,
              noRowsOverlay: customNoRowsOverlay,
            }}
            {...props}
          />
        </Box>
      </Box>
    </ModernCard>
  );
};

export default ModernDataGrid;