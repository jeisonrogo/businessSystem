/**
 * Modern Card Component - Professional Business Interface
 * Sistema de Gestión Empresarial
 */

import React from 'react';
import {
  Card,
  CardProps,
  alpha,
  useTheme,
} from '@mui/material';

interface ModernCardProps extends Omit<CardProps, 'variant'> {
  variant?: 'default' | 'gradient' | 'glass' | 'bordered';
  hoverable?: boolean;
  children: React.ReactNode;
}

const ModernCard: React.FC<ModernCardProps> = ({
  variant = 'default',
  hoverable = true,
  children,
  sx,
  ...props
}) => {
  const theme = useTheme();

  const getVariantStyles = () => {
    switch (variant) {
      case 'gradient':
        return {
          background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
          border: '1px solid',
          borderColor: alpha(theme.palette.primary.main, 0.15),
        };
      case 'glass':
        return {
          background: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(20px)',
          border: '1px solid',
          borderColor: alpha(theme.palette.divider, 0.1),
        };
      case 'bordered':
        return {
          background: theme.palette.background.paper,
          border: '1px solid',
          borderColor: alpha(theme.palette.divider, 0.2),
        };
      default:
        return {
          background: alpha(theme.palette.background.paper, 0.8),
          border: '1px solid',
          borderColor: alpha(theme.palette.divider, 0.1),
        };
    }
  };

  const hoverStyles = hoverable ? {
    transition: 'all 0.3s ease',
    cursor: 'pointer',
    '&:hover': {
      transform: 'translateY(-4px)',
      boxShadow: `0 12px 40px ${alpha(theme.palette.primary.main, 0.15)}`,
      borderColor: alpha(theme.palette.primary.main, 0.3),
    },
  } : {};

  return (
    <Card
      {...props}
      sx={{
        borderRadius: 3,
        boxShadow: `0 4px 16px ${alpha(theme.palette.primary.main, 0.08)}`,
        ...getVariantStyles(),
        ...hoverStyles,
        ...sx,
      }}
    >
      {children}
    </Card>
  );
};

export default ModernCard;