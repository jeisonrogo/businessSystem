/**
 * Página de No Autorizado
 */

import React from 'react';
import { Box, Typography, Button, Container, Alert } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { ArrowBack, Security } from '@mui/icons-material';

const UnauthorizedPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Container maxWidth="md">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          textAlign: 'center',
        }}
      >
        <Security
          sx={{
            fontSize: '6rem',
            color: 'warning.main',
            mb: 2,
          }}
        />
        <Typography variant="h4" component="h1" gutterBottom>
          Acceso No Autorizado
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          No tienes permisos para acceder a esta sección del sistema.
        </Typography>
        
        <Alert severity="warning" sx={{ mb: 4, maxWidth: 500 }}>
          Tu rol actual no tiene los permisos necesarios para ver este contenido.
          Contacta al administrador si crees que esto es un error.
        </Alert>

        <Button
          variant="contained"
          size="large"
          startIcon={<ArrowBack />}
          onClick={() => navigate(-1)}
          sx={{ mr: 2 }}
        >
          Volver
        </Button>
        <Button
          variant="outlined"
          size="large"
          onClick={() => navigate('/dashboard')}
        >
          Ir al Dashboard
        </Button>
      </Box>
    </Container>
  );
};

export default UnauthorizedPage;