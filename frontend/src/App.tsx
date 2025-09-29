/**
 * Componente principal de la aplicación
 * Sistema de Gestión Empresarial
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';

// Context
import { AuthProvider } from './context/AuthContext';
import { TenantProvider } from './context/TenantContext';

// Components
import ProtectedRoute from './components/common/ProtectedRoute';
import Layout from './components/layout/Layout';
import LoginForm from './components/auth/LoginForm';
import ErrorBoundary from './components/common/ErrorBoundary';

// Pages
import DashboardPage from './pages/DashboardPage';
import ProductsPage from './pages/ProductsPage';
import InventoryPage from './pages/InventoryPage';
import ClientsPage from './pages/ClientsPage';
import InvoicesPage from './pages/InvoicesPage';
import AccountingPage from './pages/AccountingPage';
import UsersPage from './pages/UsersPage';
import SettingsPage from './pages/SettingsPage';
import UnauthorizedPage from './pages/UnauthorizedPage';
import NotFoundPage from './pages/NotFoundPage';

// Enhanced Material-UI Theme for Business Management System
const theme = createTheme({
  palette: {
    primary: {
      main: '#667eea',
      light: '#8fa4f3',
      dark: '#4d63d2',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#764ba2',
      light: '#9575cd',
      dark: '#512da8',
      contrastText: '#ffffff',
    },
    background: {
      default: '#f8fafc',
      paper: '#ffffff',
    },
    text: {
      primary: '#1a202c',
      secondary: '#4a5568',
    },
    grey: {
      50: '#f7fafc',
      100: '#edf2f7',
      200: '#e2e8f0',
      300: '#cbd5e0',
      400: '#a0aec0',
      500: '#718096',
      600: '#4a5568',
      700: '#2d3748',
      800: '#1a202c',
      900: '#171923',
    },
    success: {
      main: '#48bb78',
      light: '#68d391',
      dark: '#38a169',
    },
    error: {
      main: '#f56565',
      light: '#fc8181',
      dark: '#e53e3e',
    },
    warning: {
      main: '#ed8936',
      light: '#fbb040',
      dark: '#dd6b20',
    },
    info: {
      main: '#4299e1',
      light: '#63b3ed',
      dark: '#3182ce',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 700,
      letterSpacing: '-0.025em',
    },
    h2: {
      fontWeight: 700,
      letterSpacing: '-0.025em',
    },
    h3: {
      fontWeight: 600,
      letterSpacing: '-0.025em',
    },
    h4: {
      fontWeight: 600,
      letterSpacing: '-0.025em',
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
    button: {
      fontWeight: 600,
      textTransform: 'none',
    },
  },
  shape: {
    borderRadius: 12,
  },
  shadows: [
    'none',
    '0px 1px 3px rgba(0, 0, 0, 0.05)',
    '0px 1px 6px rgba(0, 0, 0, 0.05)',
    '0px 3px 12px rgba(0, 0, 0, 0.1)',
    '0px 4px 16px rgba(0, 0, 0, 0.1)',
    '0px 6px 24px rgba(0, 0, 0, 0.1)',
    '0px 8px 32px rgba(0, 0, 0, 0.1)',
    '0px 12px 48px rgba(0, 0, 0, 0.15)',
    '0px 16px 64px rgba(0, 0, 0, 0.15)',
    '0px 20px 80px rgba(0, 0, 0, 0.2)',
    '0px 24px 96px rgba(0, 0, 0, 0.2)',
    '0px 28px 112px rgba(0, 0, 0, 0.25)',
    '0px 32px 128px rgba(0, 0, 0, 0.25)',
    '0px 36px 144px rgba(0, 0, 0, 0.3)',
    '0px 40px 160px rgba(0, 0, 0, 0.3)',
    '0px 44px 176px rgba(0, 0, 0, 0.35)',
    '0px 48px 192px rgba(0, 0, 0, 0.35)',
    '0px 52px 208px rgba(0, 0, 0, 0.4)',
    '0px 56px 224px rgba(0, 0, 0, 0.4)',
    '0px 60px 240px rgba(0, 0, 0, 0.45)',
    '0px 64px 256px rgba(0, 0, 0, 0.45)',
    '0px 68px 272px rgba(0, 0, 0, 0.5)',
    '0px 72px 288px rgba(0, 0, 0, 0.5)',
    '0px 76px 304px rgba(0, 0, 0, 0.55)',
    '0px 80px 320px rgba(0, 0, 0, 0.55)',
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          paddingTop: 12,
          paddingBottom: 12,
          paddingLeft: 24,
          paddingRight: 24,
          fontSize: '0.95rem',
          fontWeight: 600,
          textTransform: 'none',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.1)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12,
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.05)',
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ErrorBoundary>
        <AuthProvider>
          <TenantProvider>
            <Router>
            <Routes>
            {/* Ruta de login */}
            <Route path="/login" element={<LoginForm />} />
            
            {/* Rutas protegidas */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              {/* Redirigir raíz al dashboard */}
              <Route index element={<Navigate to="/dashboard" replace />} />
              
              {/* Dashboard - accesible para todos los usuarios autenticados */}
              <Route path="dashboard" element={<DashboardPage />} />
              
              {/* Productos - accesible para todos los usuarios */}
              <Route path="products" element={<ProductsPage />} />
              
              {/* Inventario - accesible para todos los usuarios */}
              <Route path="inventory" element={<InventoryPage />} />
              
              {/* Clientes - accesible para Admin, Gerente y Vendedor */}
              <Route
                path="clients"
                element={
                  <ProtectedRoute requiredRoles={['administrador', 'gerente_ventas', 'vendedor']}>
                    <ClientsPage />
                  </ProtectedRoute>
                }
              />
              
              {/* Facturas - accesible para Admin, Gerente y Vendedor */}
              <Route
                path="invoices"
                element={
                  <ProtectedRoute requiredRoles={['administrador', 'gerente_ventas', 'vendedor']}>
                    <InvoicesPage />
                  </ProtectedRoute>
                }
              />
              
              {/* Contabilidad - accesible para Admin y Contador */}
              <Route
                path="accounting"
                element={
                  <ProtectedRoute requiredRoles={['administrador', 'contador']}>
                    <AccountingPage />
                  </ProtectedRoute>
                }
              />
              
              {/* Usuarios - accesible solo para Administradores */}
              <Route
                path="users"
                element={
                  <ProtectedRoute requiredRoles={['administrador']}>
                    <UsersPage />
                  </ProtectedRoute>
                }
              />
              
              {/* Configuración - accesible para todos los usuarios autenticados */}
              <Route path="settings" element={<SettingsPage />} />
            </Route>

            {/* Rutas de error */}
            <Route path="/unauthorized" element={<UnauthorizedPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
            </Router>
          </TenantProvider>
        </AuthProvider>
      </ErrorBoundary>
    </ThemeProvider>
  );
}

export default App;
