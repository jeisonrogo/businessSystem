/**
 * Professional Data Visualization Components
 * Sistema de Gestión Empresarial
 */

import React from 'react';
import {
  Box,
  Typography,
  LinearProgress,
  Card,
  CardContent,
  alpha,
  useTheme,
  Stack,
  Chip,
} from '@mui/material';
import Grid2 from '@mui/material/Unstable_Grid2';

interface ProgressBarProps {
  label: string;
  value: number;
  maxValue: number;
  color?: string;
  format?: 'currency' | 'number' | 'percentage';
  subtitle?: string;
}

export const ModernProgressBar: React.FC<ProgressBarProps> = ({
  label,
  value,
  maxValue,
  color = '#667eea',
  format = 'number',
  subtitle,
}) => {
  const theme = useTheme();
  const percentage = (value / maxValue) * 100;

  const formatValue = (val: number) => {
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('es-CO', {
          style: 'currency',
          currency: 'COP',
          minimumFractionDigits: 0,
        }).format(val);
      case 'percentage':
        return `${val.toFixed(1)}%`;
      default:
        return val.toLocaleString();
    }
  };

  return (
    <Box sx={{ mb: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
          {label}
        </Typography>
        <Typography variant="body2" sx={{ fontWeight: 600, color }}>
          {formatValue(value)}
        </Typography>
      </Box>
      <LinearProgress
        variant="determinate"
        value={Math.min(percentage, 100)}
        sx={{
          height: 8,
          borderRadius: 4,
          background: alpha(color, 0.1),
          '& .MuiLinearProgress-bar': {
            background: `linear-gradient(135deg, ${color} 0%, ${alpha(color, 0.8)} 100%)`,
            borderRadius: 4,
          },
        }}
      />
      {subtitle && (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
          {subtitle}
        </Typography>
      )}
    </Box>
  );
};

interface BarChartProps {
  data: Array<{
    label: string;
    value: number;
    color?: string;
    subtitle?: string;
  }>;
  title?: string;
  maxValue?: number;
  format?: 'currency' | 'number' | 'percentage';
}

export const ModernBarChart: React.FC<BarChartProps> = ({
  data,
  title,
  maxValue,
  format = 'number',
}) => {
  const theme = useTheme();
  const maxVal = maxValue || Math.max(...data.map(item => item.value));
  const colors = ['#667eea', '#f5576c', '#4facfe', '#43e97b', '#fa709a'];

  return (
    <Card
      sx={{
        borderRadius: 3,
        background: alpha(theme.palette.background.paper, 0.8),
        border: '1px solid',
        borderColor: alpha(theme.palette.divider, 0.1),
      }}
    >
      <CardContent sx={{ p: 3 }}>
        {title && (
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
            {title}
          </Typography>
        )}
        <Stack spacing={2}>
          {data.map((item, index) => (
            <ModernProgressBar
              key={index}
              label={item.label}
              value={item.value}
              maxValue={maxVal}
              color={item.color || colors[index % colors.length]}
              format={format}
              subtitle={item.subtitle}
            />
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
};

interface MetricCardProps {
  title: string;
  value: string | number;
  trend?: {
    value: number;
    label: string;
    direction: 'up' | 'down' | 'neutral';
  };
  color?: string;
  icon?: React.ReactElement;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  trend,
  color = '#667eea',
  icon,
}) => {
  const theme = useTheme();

  const getTrendColor = () => {
    switch (trend?.direction) {
      case 'up':
        return theme.palette.success.main;
      case 'down':
        return theme.palette.error.main;
      default:
        return theme.palette.grey[500];
    }
  };

  return (
    <Card
      sx={{
        borderRadius: 3,
        background: `linear-gradient(135deg, ${alpha(color, 0.1)} 0%, ${alpha(color, 0.05)} 100%)`,
        border: '1px solid',
        borderColor: alpha(color, 0.15),
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: `0 8px 25px ${alpha(color, 0.2)}`,
          borderColor: alpha(color, 0.3),
        },
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box sx={{ flex: 1 }}>
            <Typography
              color="text.secondary"
              variant="body2"
              sx={{ fontWeight: 500, mb: 1 }}
            >
              {title}
            </Typography>
            <Typography
              variant="h4"
              sx={{ fontWeight: 700, color, mb: trend ? 1 : 0 }}
            >
              {value}
            </Typography>
            {trend && (
              <Chip
                label={trend.label}
                size="small"
                sx={{
                  background: alpha(getTrendColor(), 0.1),
                  color: getTrendColor(),
                  fontWeight: 500,
                  borderRadius: 1.5,
                }}
              />
            )}
          </Box>
          {icon && (
            <Box
              sx={{
                p: 2,
                borderRadius: 2,
                background: alpha(color, 0.15),
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {React.cloneElement(icon, {
                style: { fontSize: 32, color },
              } as any)}
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

interface SimpleGridChartProps {
  data: Array<{
    period: string;
    value1: number;
    value2?: number;
    label1: string;
    label2?: string;
  }>;
  title: string;
  colors?: [string, string];
}

export const SimpleGridChart: React.FC<SimpleGridChartProps> = ({
  data,
  title,
  colors = ['#667eea', '#764ba2'],
}) => {
  const theme = useTheme();
  const maxValue1 = Math.max(...data.map(d => d.value1));
  const maxValue2 = data[0]?.value2 !== undefined ? Math.max(...data.map(d => d.value2 || 0)) : 0;

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
          {title}
        </Typography>
        <Stack direction="row" spacing={2}>
          <Chip
            label={data[0]?.label1}
            sx={{
              background: alpha(colors[0], 0.1),
              color: colors[0],
              fontWeight: 500,
            }}
          />
          {data[0]?.label2 && (
            <Chip
              label={data[0].label2}
              sx={{
                background: alpha(colors[1], 0.1),
                color: colors[1],
                fontWeight: 500,
              }}
            />
          )}
        </Stack>
      </Box>

      <Grid2 container spacing={2}>
        {data.map((item, index) => (
          <Grid2 key={index} xs={12} sm={6} md={4} lg={3}>
            <Card
              sx={{
                p: 2.5,
                borderRadius: 2,
                background: alpha(theme.palette.background.paper, 0.8),
                border: '1px solid',
                borderColor: alpha(theme.palette.divider, 0.1),
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: `0 8px 25px ${alpha(theme.palette.primary.main, 0.15)}`,
                  borderColor: alpha(theme.palette.primary.main, 0.3),
                },
              }}
            >
              <Typography
                variant="subtitle2"
                color="text.secondary"
                sx={{ fontWeight: 600, mb: 2 }}
              >
                {item.period}
              </Typography>

              <ModernProgressBar
                label={item.label1}
                value={item.value1}
                maxValue={maxValue1}
                color={colors[0]}
                format="currency"
              />

              {item.value2 !== undefined && item.label2 && (
                <ModernProgressBar
                  label={item.label2}
                  value={item.value2}
                  maxValue={maxValue2}
                  color={colors[1]}
                  format="number"
                />
              )}
            </Card>
          </Grid2>
        ))}
      </Grid2>
    </Box>
  );
};