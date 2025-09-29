/**
 * Modern Search Bar Component - Professional Business Interface
 * Sistema de Gestión Empresarial
 */

import React, { useState, useEffect } from 'react';
import {
  TextField,
  InputAdornment,
  IconButton,
  Box,
  alpha,
  useTheme,
  Chip,
  Menu,
  MenuItem,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  SelectChangeEvent,
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear as ClearIcon,
  FilterList as FilterIcon,
  Tune as TuneIcon,
} from '@mui/icons-material';

interface FilterOption {
  key: string;
  label: string;
  value: any;
}

interface ModernSearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  debounceMs?: number;
  filters?: FilterOption[];
  selectedFilters?: string[];
  onFiltersChange?: (filters: string[]) => void;
  sortOptions?: Array<{ value: string; label: string }>;
  sortValue?: string;
  onSortChange?: (value: string) => void;
  disabled?: boolean;
  fullWidth?: boolean;
  size?: 'small' | 'medium';
}

const ModernSearchBar: React.FC<ModernSearchBarProps> = ({
  value,
  onChange,
  placeholder = 'Buscar...',
  debounceMs = 500,
  filters = [],
  selectedFilters = [],
  onFiltersChange,
  sortOptions = [],
  sortValue = '',
  onSortChange,
  disabled = false,
  fullWidth = true,
  size = 'medium',
}) => {
  const theme = useTheme();
  const [internalValue, setInternalValue] = useState(value);
  const [filterMenuAnchor, setFilterMenuAnchor] = useState<null | HTMLElement>(null);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      onChange(internalValue);
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [internalValue, debounceMs, onChange]);

  // Sync with external value changes
  useEffect(() => {
    setInternalValue(value);
  }, [value]);

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setInternalValue(event.target.value);
  };

  const handleClear = () => {
    setInternalValue('');
    onChange('');
  };

  const handleFilterMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setFilterMenuAnchor(event.currentTarget);
  };

  const handleFilterMenuClose = () => {
    setFilterMenuAnchor(null);
  };

  const handleFilterToggle = (filterKey: string) => {
    if (!onFiltersChange) return;

    const newFilters = selectedFilters.includes(filterKey)
      ? selectedFilters.filter(f => f !== filterKey)
      : [...selectedFilters, filterKey];

    onFiltersChange(newFilters);
  };

  const handleSortChange = (event: SelectChangeEvent) => {
    if (onSortChange) {
      onSortChange(event.target.value);
    }
  };

  const getFilterLabel = (key: string) => {
    const filter = filters.find(f => f.key === key);
    return filter?.label || key;
  };

  return (
    <Box sx={{ width: fullWidth ? '100%' : 'auto' }}>
      {/* Main search bar */}
      <Box sx={{ display: 'flex', gap: 1, mb: selectedFilters.length > 0 ? 1 : 0 }}>
        <TextField
          fullWidth={fullWidth}
          size={size}
          value={internalValue}
          onChange={handleInputChange}
          placeholder={placeholder}
          disabled={disabled}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon sx={{ color: 'text.secondary' }} />
              </InputAdornment>
            ),
            endAdornment: (
              <InputAdornment position="end">
                <Box sx={{ display: 'flex', gap: 0.5 }}>
                  {internalValue && (
                    <Tooltip title="Limpiar búsqueda">
                      <IconButton
                        size="small"
                        onClick={handleClear}
                        disabled={disabled}
                        sx={{
                          color: 'text.secondary',
                          '&:hover': {
                            backgroundColor: alpha(theme.palette.error.main, 0.1),
                            color: 'error.main',
                          },
                        }}
                      >
                        <ClearIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                  {filters.length > 0 && (
                    <Tooltip title="Filtros">
                      <IconButton
                        size="small"
                        onClick={handleFilterMenuOpen}
                        disabled={disabled}
                        sx={{
                          color: selectedFilters.length > 0 ? 'primary.main' : 'text.secondary',
                          backgroundColor: selectedFilters.length > 0
                            ? alpha(theme.palette.primary.main, 0.1)
                            : 'transparent',
                          '&:hover': {
                            backgroundColor: alpha(theme.palette.primary.main, 0.1),
                            color: 'primary.main',
                          },
                        }}
                      >
                        <FilterIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                </Box>
              </InputAdornment>
            ),
            sx: {
              backgroundColor: alpha(theme.palette.background.paper, 0.8),
              borderRadius: 2,
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: alpha(theme.palette.divider, 0.3),
              },
              '&:hover .MuiOutlinedInput-notchedOutline': {
                borderColor: alpha(theme.palette.primary.main, 0.3),
              },
              '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                borderColor: theme.palette.primary.main,
                borderWidth: 2,
              },
            },
          }}
        />

        {/* Sort dropdown */}
        {sortOptions.length > 0 && onSortChange && (
          <FormControl sx={{ minWidth: 140 }} size={size}>
            <InputLabel
              sx={{
                fontSize: size === 'small' ? '0.875rem' : '1rem',
              }}
            >
              Ordenar
            </InputLabel>
            <Select
              value={sortValue}
              label="Ordenar"
              onChange={handleSortChange}
              disabled={disabled}
              startAdornment={
                <InputAdornment position="start">
                  <TuneIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                </InputAdornment>
              }
              sx={{
                backgroundColor: alpha(theme.palette.background.paper, 0.8),
                borderRadius: 2,
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: alpha(theme.palette.divider, 0.3),
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: alpha(theme.palette.primary.main, 0.3),
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  borderColor: theme.palette.primary.main,
                  borderWidth: 2,
                },
              }}
            >
              {sortOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
      </Box>

      {/* Active filters */}
      {selectedFilters.length > 0 && (
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {selectedFilters.map((filterKey) => (
            <Chip
              key={filterKey}
              label={getFilterLabel(filterKey)}
              onDelete={() => handleFilterToggle(filterKey)}
              size="small"
              color="primary"
              variant="outlined"
              sx={{
                backgroundColor: alpha(theme.palette.primary.main, 0.1),
                borderColor: alpha(theme.palette.primary.main, 0.3),
                '& .MuiChip-deleteIcon': {
                  color: 'primary.main',
                  '&:hover': {
                    color: 'primary.dark',
                  },
                },
              }}
            />
          ))}
        </Box>
      )}

      {/* Filter menu */}
      <Menu
        anchorEl={filterMenuAnchor}
        open={Boolean(filterMenuAnchor)}
        onClose={handleFilterMenuClose}
        PaperProps={{
          sx: {
            borderRadius: 2,
            mt: 1,
            minWidth: 200,
            boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.15)}`,
          },
        }}
      >
        {filters.map((filter) => (
          <MenuItem
            key={filter.key}
            onClick={() => handleFilterToggle(filter.key)}
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              py: 1,
            }}
          >
            {filter.label}
            {selectedFilters.includes(filter.key) && (
              <Chip
                size="small"
                label="✓"
                color="primary"
                sx={{ ml: 1, minWidth: 24, height: 20 }}
              />
            )}
          </MenuItem>
        ))}
      </Menu>
    </Box>
  );
};

export default ModernSearchBar;