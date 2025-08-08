/**
 * Formulario de Login
 */

import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Container,
  Paper,
} from '@mui/material';
import { useAuth } from '../../context/AuthContext';
import { LoginRequest } from '../../types';

const LoginForm: React.FC = () => {
  const [formData, setFormData] = useState<LoginRequest>({
    username: '',
    password: '',
  });
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Obtener la ruta a la que debe redirigir después del login
  const from = (location.state as any)?.from?.pathname || '/dashboard';

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    // Limpiar error cuando el usuario comience a escribir
    if (error) setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.username || !formData.password) {
      setError('Por favor ingrese email y contraseña');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await login(formData);
      navigate(from, { replace: true });
    } catch (err: any) {
      console.error('Error en login:', err);
      
      // Extraer mensaje de error de la respuesta
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.response?.status === 401) {
        setError('Credenciales incorrectas');
      } else if (err.response?.status >= 500) {
        setError('Error del servidor. Intente más tarde.');
      } else {
        setError('Error al iniciar sesión. Verifique su conexión.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container component="main" maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <Paper
          elevation={8}
          sx={{
            padding: 4,
            width: '100%',
            maxWidth: 400,
            borderRadius: 2,
          }}
        >
          <Box sx={{ textAlign: 'center', mb: 3 }}>
            <Typography variant="h4" component="h1" gutterBottom color="primary">
              Sistema de Gestión
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Inicie sesión en su cuenta
            </Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="Email"
              name="username"
              type="email"
              autoComplete="email"
              autoFocus
              value={formData.username}
              onChange={handleChange}
              disabled={loading}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Contraseña"
              type="password"
              id="password"
              autoComplete="current-password"
              value={formData.password}
              onChange={handleChange}
              disabled={loading}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2, py: 1.5 }}
              disabled={loading || !formData.username || !formData.password}
            >
              {loading ? (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={20} color="inherit" />
                  Iniciando sesión...
                </Box>
              ) : (
                'Iniciar Sesión'
              )}
            </Button>
          </Box>

          <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              <strong>Usuarios de demostración:</strong>
            </Typography>
            <Typography variant="caption" display="block">
              • admin.demo@empresa.com (Administrador)
            </Typography>
            <Typography variant="caption" display="block">
              • gerente.demo@empresa.com (Gerente de Ventas)
            </Typography>
            <Typography variant="caption" display="block">
              • contador.demo@empresa.com (Contador)
            </Typography>
            <Typography variant="caption" display="block">
              • vendedor.demo@empresa.com (Vendedor)
            </Typography>
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              Contraseña para todos: <strong>password123</strong>
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default LoginForm;