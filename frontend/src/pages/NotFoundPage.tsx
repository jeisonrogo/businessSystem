/**
 * Página 404 - No encontrada
 */

import React from 'react';
import { Box, Typography, Button, Container } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { Home } from '@mui/icons-material';

const NotFoundPage: React.FC = () => {
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
        <Typography
          variant="h1"
          component="h1"
          sx={{
            fontSize: '8rem',
            fontWeight: 'bold',
            color: 'primary.main',
            mb: 2,
          }}
        >
          404
        </Typography>
        <Typography variant="h4" component="h2" gutterBottom>
          Página No Encontrada
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          Lo sentimos, la página que buscas no existe o ha sido movida.
        </Typography>
        <Button
          variant="contained"
          size="large"
          startIcon={<Home />}
          onClick={() => navigate('/dashboard')}
        >
          Volver al Dashboard
        </Button>
      </Box>
    </Container>
  );
};

export default NotFoundPage;