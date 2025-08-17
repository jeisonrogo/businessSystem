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

// Tema de Material-UI
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ErrorBoundary>
        <AuthProvider>
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
      </AuthProvider>
      </ErrorBoundary>
    </ThemeProvider>
  );
}

export default App;
