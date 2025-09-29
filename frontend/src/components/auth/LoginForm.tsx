/**
 * Modern Login Form Component
 * Sistema de Gestión Empresarial - Professional Business Management
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
  InputAdornment,
  IconButton,
  Divider,
  Fade,
  alpha,
} from '@mui/material';
import {
  Email as EmailIcon,
  Lock as LockIcon,
  Visibility,
  VisibilityOff,
  Business as BusinessIcon,
} from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';
import { LoginRequest } from '../../types';

interface FormErrors {
  email?: string;
  password?: string;
}

const LoginForm: React.FC = () => {
  const [formData, setFormData] = useState<LoginRequest>({
    email: '',
    password: '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Obtener la ruta a la que debe redirigir después del login
  const from = (location.state as any)?.from?.pathname || '/dashboard';

  const validateEmail = (email: string): string | undefined => {
    if (!email) return 'El email es requerido';
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) return 'Ingrese un email válido';
    return undefined;
  };

  const validatePassword = (password: string): string | undefined => {
    if (!password) return 'La contraseña es requerida';
    if (password.length < 6) return 'La contraseña debe tener al menos 6 caracteres';
    return undefined;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));

    // Real-time validation
    const newErrors = { ...errors };
    if (name === 'email') {
      const emailError = validateEmail(value);
      if (emailError) {
        newErrors.email = emailError;
      } else {
        delete newErrors.email;
      }
    } else if (name === 'password') {
      const passwordError = validatePassword(value);
      if (passwordError) {
        newErrors.password = passwordError;
      } else {
        delete newErrors.password;
      }
    }
    setErrors(newErrors);

    // Clear general error when user starts typing
    if (error) setError('');
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate all fields
    const emailError = validateEmail(formData.email);
    const passwordError = validatePassword(formData.password);

    const newErrors: FormErrors = {};
    if (emailError) newErrors.email = emailError;
    if (passwordError) newErrors.password = passwordError;

    setErrors(newErrors);

    if (Object.keys(newErrors).length > 0) {
      return;
    }

    setLoading(true);
    setError('');

    try {
      await login(formData);
      navigate(from, { replace: true });
    } catch (err: any) {
      console.error('Error en login:', err);

      // Enhanced error messages
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.response?.status === 401) {
        setError('Credenciales incorrectas. Verifique su email y contraseña.');
      } else if (err.response?.status === 403) {
        setError('Acceso denegado. Su cuenta puede estar inactiva.');
      } else if (err.response?.status >= 500) {
        setError('Error del servidor. Por favor, intente más tarde.');
      } else if (err.code === 'NETWORK_ERROR') {
        setError('Error de conexión. Verifique su conexión a internet.');
      } else {
        setError('Error al iniciar sesión. Intente nuevamente.');
      }
    } finally {
      setLoading(false);
    }
  };

  const isFormValid = () => {
    return formData.email &&
           formData.password &&
           Object.keys(errors).length === 0 &&
           !loading;
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 2,
      }}
    >
      <Container component="main" maxWidth="sm">
        <Fade in timeout={800}>
          <Paper
            elevation={24}
            sx={{
              p: { xs: 3, sm: 4, md: 5 },
              width: '100%',
              maxWidth: 450,
              borderRadius: 3,
              background: 'rgba(255, 255, 255, 0.98)',
              backdropFilter: 'blur(10px)',
              boxShadow: `0 20px 60px rgba(0, 0, 0, 0.1),
                         0 8px 25px rgba(0, 0, 0, 0.08)`,
              mx: 'auto',
            }}
          >
            {/* Header Section */}
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              {/* Company Icon */}
              <Box
                sx={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: 80,
                  height: 80,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  mb: 3,
                  boxShadow: '0 8px 32px rgba(102, 126, 234, 0.3)',
                }}
              >
                <BusinessIcon sx={{ fontSize: 40, color: 'white' }} />
              </Box>

              <Typography
                variant="h4"
                component="h1"
                sx={{
                  fontWeight: 700,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  mb: 1,
                  fontSize: { xs: '1.8rem', sm: '2.125rem' },
                }}
              >
                Sistema de Gestión
              </Typography>

              <Typography
                variant="h6"
                sx={{
                  color: 'text.secondary',
                  fontWeight: 500,
                  mb: 1,
                }}
              >
                Empresarial
              </Typography>

              <Typography
                variant="body2"
                sx={{
                  color: 'text.secondary',
                  lineHeight: 1.6,
                }}
              >
                Acceda a su cuenta para gestionar su negocio
              </Typography>
            </Box>

            <Divider sx={{ mb: 3, opacity: 0.6 }} />

            {/* Error Alert */}
            {error && (
              <Fade in>
                <Alert
                  severity="error"
                  sx={{
                    mb: 3,
                    borderRadius: 2,
                    '& .MuiAlert-icon': {
                      fontSize: '1.5rem',
                    },
                  }}
                >
                  {error}
                </Alert>
              </Fade>
            )}

            {/* Login Form */}
            <Box component="form" onSubmit={handleSubmit} noValidate>
              {/* Email Field */}
              <TextField
                margin="normal"
                required
                fullWidth
                id="email"
                label="Correo Electrónico"
                name="email"
                type="email"
                autoComplete="email"
                autoFocus
                value={formData.email}
                onChange={handleChange}
                disabled={loading}
                error={!!errors.email}
                helperText={errors.email}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <EmailIcon sx={{ color: 'action.active' }} />
                    </InputAdornment>
                  ),
                }}
                sx={{
                  mb: 2,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      boxShadow: `0 4px 12px ${alpha('#667eea', 0.15)}`,
                    },
                    '&.Mui-focused': {
                      boxShadow: `0 4px 12px ${alpha('#667eea', 0.25)}`,
                    },
                  },
                }}
              />

              {/* Password Field */}
              <TextField
                margin="normal"
                required
                fullWidth
                name="password"
                label="Contraseña"
                type={showPassword ? 'text' : 'password'}
                id="password"
                autoComplete="current-password"
                value={formData.password}
                onChange={handleChange}
                disabled={loading}
                error={!!errors.password}
                helperText={errors.password}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <LockIcon sx={{ color: 'action.active' }} />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle password visibility"
                        onClick={togglePasswordVisibility}
                        onMouseDown={(e) => e.preventDefault()}
                        edge="end"
                        disabled={loading}
                        size="small"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                sx={{
                  mb: 3,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      boxShadow: `0 4px 12px ${alpha('#667eea', 0.15)}`,
                    },
                    '&.Mui-focused': {
                      boxShadow: `0 4px 12px ${alpha('#667eea', 0.25)}`,
                    },
                  },
                }}
              />

              {/* Submit Button */}
              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={!isFormValid()}
                sx={{
                  py: 1.8,
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  boxShadow: '0 8px 32px rgba(102, 126, 234, 0.4)',
                  textTransform: 'none',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                    boxShadow: '0 12px 40px rgba(102, 126, 234, 0.5)',
                    transform: 'translateY(-2px)',
                  },
                  '&:active': {
                    transform: 'translateY(-1px)',
                  },
                  '&:disabled': {
                    background: alpha('#667eea', 0.6),
                    boxShadow: 'none',
                    transform: 'none',
                  },
                }}
              >
                {loading ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <CircularProgress size={24} color="inherit" thickness={4} />
                    <Typography variant="inherit" sx={{ fontWeight: 600 }}>
                      Iniciando sesión...
                    </Typography>
                  </Box>
                ) : (
                  'Iniciar Sesión'
                )}
              </Button>
            </Box>

            {/* Footer */}
            <Box sx={{ mt: 4, textAlign: 'center' }}>
              <Typography
                variant="body2"
                sx={{
                  color: 'text.secondary',
                  fontSize: '0.875rem',
                }}
              >
                © {new Date().getFullYear()} Sistema de Gestión Empresarial
              </Typography>
            </Box>
          </Paper>
        </Fade>
      </Container>
    </Box>
  );
};

export default LoginForm;