/**
 * Modern Loading Spinner Component
 * Sistema de Gestión Empresarial
 */

import React from 'react';
import {
  Box,
  CircularProgress,
  Typography,
  alpha,
  useTheme,
} from '@mui/material';

interface LoadingSpinnerProps {
  size?: number;
  message?: string;
  fullScreen?: boolean;
  variant?: 'default' | 'dots' | 'pulse';
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 40,
  message = 'Cargando...',
  fullScreen = false,
  variant = 'default',
}) => {
  const theme = useTheme();

  const DotsLoader = () => (
    <Box sx={{ display: 'flex', gap: 1 }}>
      {[0, 1, 2].map((index) => (
        <Box
          key={index}
          sx={{
            width: 12,
            height: 12,
            borderRadius: '50%',
            background: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`,
            animation: `dotPulse 1.4s ease-in-out ${index * 0.16}s infinite both`,
            '@keyframes dotPulse': {
              '0%, 80%, 100%': {
                transform: 'scale(0)',
                opacity: 0.5,
              },
              '40%': {
                transform: 'scale(1)',
                opacity: 1,
              },
            },
          }}
        />
      ))}
    </Box>
  );

  const PulseLoader = () => (
    <Box
      sx={{
        width: size,
        height: size,
        borderRadius: '50%',
        background: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`,
        animation: 'pulse 2s ease-in-out infinite',
        '@keyframes pulse': {
          '0%': {
            transform: 'scale(0.95)',
            boxShadow: `0 0 0 0 ${alpha(theme.palette.primary.main, 0.7)}`,
          },
          '70%': {
            transform: 'scale(1)',
            boxShadow: `0 0 0 10px ${alpha(theme.palette.primary.main, 0)}`,
          },
          '100%': {
            transform: 'scale(0.95)',
            boxShadow: `0 0 0 0 ${alpha(theme.palette.primary.main, 0)}`,
          },
        },
      }}
    />
  );

  const renderSpinner = () => {
    switch (variant) {
      case 'dots':
        return <DotsLoader />;
      case 'pulse':
        return <PulseLoader />;
      default:
        return (
          <CircularProgress
            size={size}
            thickness={4}
            sx={{
              color: 'primary.main',
              '& .MuiCircularProgress-circle': {
                strokeLinecap: 'round',
              },
            }}
          />
        );
    }
  };

  const content = (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 2,
        p: 3,
      }}
    >
      {renderSpinner()}
      {message && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            fontWeight: 500,
            textAlign: 'center',
          }}
        >
          {message}
        </Typography>
      )}
    </Box>
  );

  if (fullScreen) {
    return (
      <Box
        sx={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(10px)',
          zIndex: 9999,
        }}
      >
        <Box
          sx={{
            background: 'rgba(255, 255, 255, 0.95)',
            borderRadius: 3,
            border: '1px solid',
            borderColor: alpha(theme.palette.divider, 0.1),
            boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.15)}`,
          }}
        >
          {content}
        </Box>
      </Box>
    );
  }

  return content;
};

export default LoadingSpinner;