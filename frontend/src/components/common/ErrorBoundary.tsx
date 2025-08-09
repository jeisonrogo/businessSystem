/**
 * Error Boundary para capturar errores de React
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import {
  Box,
  Typography,
  Button,
  Alert,
  Paper,
  Container,
} from '@mui/material';
import { Refresh, BugReport } from '@mui/icons-material';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error Boundary capturó un error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  private handleReload = () => {
    window.location.reload();
  };

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  public render() {
    if (this.state.hasError) {
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
            <Paper
              elevation={4}
              sx={{
                p: 4,
                width: '100%',
                maxWidth: 600,
              }}
            >
              <BugReport
                sx={{
                  fontSize: 80,
                  color: 'error.main',
                  mb: 2,
                }}
              />
              
              <Typography variant="h4" component="h1" gutterBottom>
                ¡Ups! Algo salió mal
              </Typography>
              
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                Ha ocurrido un error inesperado. Por favor, intenta recargar la página
                o contacta al administrador si el problema persiste.
              </Typography>

              <Alert severity="error" sx={{ mb: 3, textAlign: 'left' }}>
                <Typography variant="body2" fontWeight="bold">
                  Error: {this.state.error?.message}
                </Typography>
              </Alert>

              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
                <Button
                  variant="contained"
                  startIcon={<Refresh />}
                  onClick={this.handleReload}
                >
                  Recargar Página
                </Button>
                <Button
                  variant="outlined"
                  onClick={this.handleReset}
                >
                  Intentar de Nuevo
                </Button>
              </Box>

              {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
                <Box sx={{ mt: 4, textAlign: 'left' }}>
                  <Typography variant="h6" gutterBottom>
                    Detalles del Error (Desarrollo):
                  </Typography>
                  <Alert severity="info">
                    <pre style={{ 
                      fontSize: '0.75rem', 
                      overflow: 'auto', 
                      maxHeight: '200px',
                      margin: 0,
                    }}>
                      {this.state.error?.stack}
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </Alert>
                </Box>
              )}
            </Paper>
          </Box>
        </Container>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;