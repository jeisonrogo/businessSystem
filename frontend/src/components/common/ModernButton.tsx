/**
 * Modern Button Component - Professional Business Interface
 * Sistema de Gestión Empresarial
 */

import React from 'react';
import {
  Button,
  ButtonProps,
  alpha,
  useTheme,
  CircularProgress,
  Box,
} from '@mui/material';

interface ModernButtonProps extends Omit<ButtonProps, 'variant'> {
  variant?: 'contained' | 'outlined' | 'text' | 'gradient';
  loading?: boolean;
  icon?: React.ReactElement;
  iconPosition?: 'start' | 'end';
}

const ModernButton: React.FC<ModernButtonProps> = ({
  variant = 'contained',
  loading = false,
  icon,
  iconPosition = 'start',
  children,
  disabled,
  sx,
  ...props
}) => {
  const theme = useTheme();

  const getVariantStyles = () => {
    switch (variant) {
      case 'gradient':
        return {
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          border: 'none',
          '&:hover': {
            background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
            boxShadow: `0 8px 25px ${alpha(theme.palette.primary.main, 0.4)}`,
          },
          '&:disabled': {
            background: alpha(theme.palette.primary.main, 0.3),
            color: alpha(theme.palette.common.white, 0.7),
          },
        };
      case 'outlined':
        return {
          borderColor: alpha(theme.palette.primary.main, 0.3),
          color: 'primary.main',
          background: 'transparent',
          '&:hover': {
            background: alpha(theme.palette.primary.main, 0.08),
            borderColor: theme.palette.primary.main,
            boxShadow: `0 4px 16px ${alpha(theme.palette.primary.main, 0.2)}`,
          },
        };
      case 'text':
        return {
          color: 'primary.main',
          '&:hover': {
            background: alpha(theme.palette.primary.main, 0.08),
          },
        };
      default:
        return {
          background: theme.palette.primary.main,
          '&:hover': {
            background: theme.palette.primary.dark,
            boxShadow: `0 6px 20px ${alpha(theme.palette.primary.main, 0.3)}`,
          },
        };
    }
  };

  const renderIcon = () => {
    if (!icon) return null;
    return React.cloneElement(icon, {
      style: { fontSize: 20 },
    } as any);
  };

  const renderContent = () => {
    if (loading) {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CircularProgress size={20} color="inherit" />
          {children}
        </Box>
      );
    }

    if (icon) {
      return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {iconPosition === 'start' && renderIcon()}
          {children}
          {iconPosition === 'end' && renderIcon()}
        </Box>
      );
    }

    return children;
  };

  const buttonVariant = variant === 'gradient' ? 'contained' : variant;

  return (
    <Button
      {...props}
      variant={buttonVariant}
      disabled={disabled || loading}
      sx={{
        borderRadius: 2,
        py: 1.5,
        px: 3,
        fontSize: '0.95rem',
        fontWeight: 600,
        textTransform: 'none',
        transition: 'all 0.3s ease',
        minHeight: 48,
        '&:active': {
          transform: 'translateY(1px)',
        },
        ...getVariantStyles(),
        ...sx,
      }}
    >
      {renderContent()}
    </Button>
  );
};

export default ModernButton;