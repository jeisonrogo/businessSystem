/**
 * Modern Stat Card Component - Professional KPI Display
 * Sistema de Gestión Empresarial
 */

import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  alpha,
  useTheme,
  Chip,
  IconButton,
} from '@mui/material';
import { TrendingUp, TrendingDown, Remove } from '@mui/icons-material';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactElement;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
  variant?: 'default' | 'minimal' | 'detailed';
  onClick?: () => void;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendValue,
  color = 'primary',
  variant = 'default',
  onClick,
}) => {
  const theme = useTheme();

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp sx={{ fontSize: 16 }} />;
      case 'down':
        return <TrendingDown sx={{ fontSize: 16 }} />;
      default:
        return <Remove sx={{ fontSize: 16 }} />;
    }
  };

  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'success';
      case 'down':
        return 'error';
      default:
        return 'default';
    }
  };

  const getColorStyles = () => {
    const themeColor = theme.palette[color];
    return {
      background: `linear-gradient(135deg, ${alpha(themeColor.main, 0.1)} 0%, ${alpha(themeColor.main, 0.05)} 100%)`,
      borderColor: alpha(themeColor.main, 0.15),
      iconBackground: alpha(themeColor.main, 0.15),
      valueColor: themeColor.main,
    };
  };

  const colorStyles = getColorStyles();

  return (
    <Card
      onClick={onClick}
      sx={{
        borderRadius: 3,
        background: colorStyles.background,
        border: '1px solid',
        borderColor: colorStyles.borderColor,
        transition: 'all 0.3s ease',
        cursor: onClick ? 'pointer' : 'default',
        '&:hover': onClick ? {
          transform: 'translateY(-4px)',
          boxShadow: `0 12px 40px ${alpha(theme.palette[color].main, 0.2)}`,
          borderColor: alpha(theme.palette[color].main, 0.3),
        } : {},
      }}
    >
      <CardContent sx={{ p: 3 }}>
        {variant === 'minimal' ? (
          <Box>
            <Typography color="text.secondary" variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
              {title}
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 700, color: colorStyles.valueColor }}>
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                {subtitle}
              </Typography>
            )}
          </Box>
        ) : (
          <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <Box sx={{ flex: 1 }}>
              <Typography color="text.secondary" variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
                {title}
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, color: colorStyles.valueColor }}>
                {value}
              </Typography>

              {/* Trend and Subtitle */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                {trendValue && trend && (
                  <Chip
                    icon={getTrendIcon()}
                    label={trendValue}
                    color={getTrendColor() as any}
                    size="small"
                    variant="filled"
                    sx={{ borderRadius: 1.5, fontWeight: 500 }}
                  />
                )}
                {subtitle && (
                  <Typography variant="caption" color="text.secondary">
                    {subtitle}
                  </Typography>
                )}
              </Box>
            </Box>

            {/* Icon */}
            {icon && (
              <Box
                sx={{
                  p: 2,
                  borderRadius: 2,
                  background: colorStyles.iconBackground,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {React.cloneElement(icon, {
                  style: { fontSize: 32, color: colorStyles.valueColor },
                } as any)}
              </Box>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default StatCard;