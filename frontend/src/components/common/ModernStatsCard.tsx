/**
 * Modern Statistics Card Component - Professional Business Interface
 * Sistema de Gestión Empresarial
 */

import React from 'react';
import {
  CardContent,
  Typography,
  Box,
  alpha,
  useTheme,
  IconButton,
  Tooltip,
  Chip,
  CircularProgress,
} from '@mui/material';
import { SvgIconComponent } from '@mui/icons-material';
import ModernCard from './ModernCard';

interface ModernStatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: SvgIconComponent;
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
  trend?: {
    value: number;
    label: string;
    direction: 'up' | 'down' | 'neutral';
  };
  loading?: boolean;
  variant?: 'default' | 'gradient' | 'glass' | 'bordered';
  actionIcon?: SvgIconComponent;
  onActionClick?: () => void;
  actionTooltip?: string;
  status?: {
    label: string;
    color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning';
  };
}

const ModernStatsCard: React.FC<ModernStatsCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'primary',
  trend,
  loading = false,
  variant = 'glass',
  actionIcon: ActionIcon,
  onActionClick,
  actionTooltip,
  status,
}) => {
  const theme = useTheme();

  const getColorValue = () => {
    switch (color) {
      case 'primary':
        return theme.palette.primary.main;
      case 'secondary':
        return theme.palette.secondary.main;
      case 'success':
        return theme.palette.success.main;
      case 'error':
        return theme.palette.error.main;
      case 'warning':
        return theme.palette.warning.main;
      case 'info':
        return theme.palette.info.main;
      default:
        return theme.palette.primary.main;
    }
  };

  const getTrendColor = () => {
    if (!trend) return '';
    switch (trend.direction) {
      case 'up':
        return theme.palette.success.main;
      case 'down':
        return theme.palette.error.main;
      default:
        return theme.palette.text.secondary;
    }
  };

  const formatValue = (val: string | number): string => {
    if (typeof val === 'number') {
      if (val >= 1000000) {
        return `${(val / 1000000).toFixed(1)}M`;
      } else if (val >= 1000) {
        return `${(val / 1000).toFixed(1)}K`;
      }
      return val.toLocaleString();
    }
    return val;
  };

  return (
    <ModernCard
      variant={variant}
      hoverable={false}
      sx={{
        height: '100%',
        position: 'relative',
        background: variant === 'gradient' ?
          `linear-gradient(135deg, ${alpha(getColorValue(), 0.1)} 0%, ${alpha(getColorValue(), 0.05)} 100%)` :
          undefined,
        borderLeft: `4px solid ${getColorValue()}`,
      }}
    >
      <CardContent sx={{ p: 3, pb: '16px !important' }}>
        {/* Header with title and action */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography
              variant="subtitle2"
              sx={{
                color: 'text.secondary',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: 0.5,
                fontSize: '0.75rem',
                mb: 0.5,
              }}
            >
              {title}
            </Typography>
            {status && (
              <Chip
                label={status.label}
                color={status.color}
                size="small"
                sx={{
                  height: 20,
                  fontSize: '0.65rem',
                  fontWeight: 600,
                }}
              />
            )}
          </Box>
          {ActionIcon && onActionClick && (
            <Tooltip title={actionTooltip || 'Acción'}>
              <IconButton
                size="small"
                onClick={onActionClick}
                sx={{
                  color: alpha(getColorValue(), 0.7),
                  '&:hover': {
                    backgroundColor: alpha(getColorValue(), 0.1),
                    color: getColorValue(),
                  },
                }}
              >
                <ActionIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>

        {/* Value section */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Box sx={{ flex: 1 }}>
            {loading ? (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CircularProgress size={24} thickness={4} />
                <Typography variant="h4" sx={{ color: 'text.secondary' }}>
                  --
                </Typography>
              </Box>
            ) : (
              <Typography
                variant="h4"
                sx={{
                  fontWeight: 700,
                  color: getColorValue(),
                  lineHeight: 1.2,
                }}
              >
                {formatValue(value)}
              </Typography>
            )}

            {subtitle && (
              <Typography
                variant="body2"
                sx={{
                  color: 'text.secondary',
                  mt: 0.5,
                  fontSize: '0.875rem',
                }}
              >
                {subtitle}
              </Typography>
            )}
          </Box>

          {Icon && (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 60,
                height: 60,
                borderRadius: '50%',
                backgroundColor: alpha(getColorValue(), 0.1),
                color: getColorValue(),
              }}
            >
              <Icon sx={{ fontSize: 28 }} />
            </Box>
          )}
        </Box>

        {/* Trend indicator */}
        {trend && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
            <Typography
              variant="caption"
              sx={{
                color: getTrendColor(),
                fontWeight: 600,
                fontSize: '0.75rem',
              }}
            >
              {trend.direction === 'up' ? '↗' : trend.direction === 'down' ? '↘' : '→'}
              {Math.abs(trend.value)}%
            </Typography>
            <Typography
              variant="caption"
              sx={{
                color: 'text.secondary',
                fontSize: '0.75rem',
              }}
            >
              {trend.label}
            </Typography>
          </Box>
        )}
      </CardContent>
    </ModernCard>
  );
};

export default ModernStatsCard;