/**
 * Modern Layout Component - Professional Business Management Interface
 * Sistema de Gestión Empresarial
 */

import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Box,
  CssBaseline,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Menu,
  MenuItem,
  Avatar,
  alpha,
  useTheme,
  Chip,
  Stack,
  Badge,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard,
  Inventory,
  Receipt,
  People,
  AccountBalance,
  Assessment,
  Settings,
  Logout,
  AccountCircle,
  SupervisorAccount,
  Business as BusinessIcon,
  NotificationsNone,
} from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';
import { TenantIndicator } from '../tenant/TenantIndicator';
import { TenantSwitcher } from '../tenant/TenantSwitcher';
import { useTenant } from '../../context/TenantContext';

const drawerWidth = 300;

interface NavigationItem {
  text: string;
  icon: React.ReactElement;
  path: string;
  roles?: string[];
}

const navigationItems: NavigationItem[] = [
  {
    text: 'Dashboard',
    icon: <Dashboard />,
    path: '/dashboard',
  },
  {
    text: 'Productos',
    icon: <Inventory />,
    path: '/products',
  },
  {
    text: 'Inventario',
    icon: <Assessment />,
    path: '/inventory',
  },
  {
    text: 'Clientes',
    icon: <People />,
    path: '/clients',
    roles: ['administrador', 'gerente_ventas', 'vendedor'],
  },
  {
    text: 'Facturas',
    icon: <Receipt />,
    path: '/invoices',
    roles: ['administrador', 'gerente_ventas', 'vendedor'],
  },
  {
    text: 'Contabilidad',
    icon: <AccountBalance />,
    path: '/accounting',
    roles: ['administrador', 'contador'],
  },
  {
    text: 'Usuarios',
    icon: <SupervisorAccount />,
    path: '/users',
    roles: ['administrador'],
  },
];

const Layout: React.FC = () => {
  const theme = useTheme();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [showTenantSwitcher, setShowTenantSwitcher] = useState(false);

  const { user, logout } = useAuth();
  const { showStoreSwitcher, setShowStoreSwitcher } = useTenant();
  const navigate = useNavigate();
  const location = useLocation();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    handleMenuClose();
    logout();
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    if (mobileOpen) {
      setMobileOpen(false);
    }
  };

  // Filtrar elementos de navegación según el rol del usuario
  const filteredNavigationItems = navigationItems.filter(item => {
    if (!item.roles) return true; // Sin restricción de rol
    return user && item.roles.includes(user.rol);
  });

  const drawer = (
    <Box
      sx={{
        height: '100%',
        background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)',
        backdropFilter: 'blur(10px)',
      }}
    >
      {/* Modern Sidebar Header */}
      <Box
        sx={{
          p: 3,
          display: 'flex',
          alignItems: 'center',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)',
            backdropFilter: 'blur(10px)',
          },
        }}
      >
        <Box sx={{ position: 'relative', zIndex: 1, display: 'flex', alignItems: 'center', width: '100%' }}>
          <Box
            sx={
              {
                p: 1.5,
                borderRadius: 2,
                background: 'rgba(255, 255, 255, 0.15)',
                backdropFilter: 'blur(10px)',
                mr: 2,
              }
            }
          >
            <BusinessIcon sx={{ fontSize: 28 }} />
          </Box>
          <Box>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                fontSize: '1.1rem',
                lineHeight: 1.2,
              }}
            >
              Sistema de Gestión
            </Typography>
            <Typography
              variant="body2"
              sx={
                {
                  opacity: 0.9,
                  fontSize: '0.85rem',
                }
              }
            >
              Empresarial
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Navigation Items */}
      <Box sx={{ p: 2 }}>
        <List sx={{ py: 0 }}>
          {filteredNavigationItems.map((item, index) => {
            const isSelected = location.pathname === item.path;
            return (
              <ListItem key={item.text} disablePadding sx={{ mb: 1 }}>
                <ListItemButton
                  selected={isSelected}
                  onClick={() => handleNavigation(item.path)}
                  sx={{
                    borderRadius: 2,
                    py: 1.5,
                    px: 2,
                    transition: 'all 0.3s ease',
                    position: 'relative',
                    overflow: 'hidden',
                    '&.Mui-selected': {
                      background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%)',
                      color: 'primary.main',
                      '&::before': {
                        content: '""',
                        position: 'absolute',
                        left: 0,
                        top: 0,
                        bottom: 0,
                        width: 4,
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        borderRadius: '0 2px 2px 0',
                      },
                      '&:hover': {
                        background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%)',
                      },
                    },
                    '&:hover': {
                      background: alpha(theme.palette.primary.main, 0.08),
                      transform: 'translateX(4px)',
                    },
                  }}
                >
                  <ListItemIcon
                    sx={{
                      color: isSelected ? 'primary.main' : 'text.secondary',
                      minWidth: 40,
                      transition: 'color 0.3s ease',
                    }}
                  >
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={item.text}
                    primaryTypographyProps={{
                      fontWeight: isSelected ? 600 : 500,
                      fontSize: '0.95rem',
                      color: isSelected ? 'primary.main' : 'text.primary',
                    }}
                  />
                </ListItemButton>
              </ListItem>
            );
          })}
        </List>
      </Box>

      {/* User Role Indicator at Bottom */}
      <Box
        sx={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          p: 2,
          background: alpha(theme.palette.background.paper, 0.8),
          backdropFilter: 'blur(10px)',
          borderTop: '1px solid',
          borderColor: alpha(theme.palette.divider, 0.1),
        }}
      >
        <Chip
          label={user?.rol || 'Usuario'}
          size="small"
          sx={{
            width: '100%',
            background: alpha(theme.palette.primary.main, 0.1),
            color: 'primary.main',
            fontWeight: 600,
            borderRadius: 2,
          }}
        />
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid',
          borderColor: alpha(theme.palette.divider, 0.1),
          color: 'text.primary',
        }}
      >
        <Toolbar sx={{ py: 1 }}>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{
              mr: 2,
              display: { sm: 'none' },
              background: alpha(theme.palette.primary.main, 0.1),
              '&:hover': {
                background: alpha(theme.palette.primary.main, 0.2),
              },
            }}
          >
            <MenuIcon />
          </IconButton>

          {/* Page Title */}
          <Box sx={{ flexGrow: 1 }}>
            <Typography
              variant="h5"
              component="h1"
              sx={{
                fontWeight: 700,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontSize: { xs: '1.25rem', sm: '1.5rem' },
              }}
            >
              Sistema de Gestión Empresarial
            </Typography>
          </Box>

          {/* Header Actions */}
          <Stack direction="row" spacing={2} alignItems="center">
            {/* Tenant Context */}
            <TenantIndicator
              variant="compact"
              onSwitchClick={() => setShowTenantSwitcher(true)}
            />

            {/* Notifications */}
            <IconButton
              sx={{
                background: alpha(theme.palette.primary.main, 0.1),
                borderRadius: 2,
                '&:hover': {
                  background: alpha(theme.palette.primary.main, 0.15),
                },
              }}
            >
              <Badge badgeContent={3} color="error">
                <NotificationsNone sx={{ color: 'primary.main' }} />
              </Badge>
            </IconButton>

            {/* User Profile */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Box sx={{ textAlign: 'right', display: { xs: 'none', sm: 'block' } }}>
                <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.primary' }}>
                  {user?.nombre}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {user?.rol}
                </Typography>
              </Box>
              <IconButton
                onClick={handleMenuOpen}
                sx={{
                  p: 0.5,
                  border: '2px solid',
                  borderColor: alpha(theme.palette.primary.main, 0.2),
                  '&:hover': {
                    borderColor: alpha(theme.palette.primary.main, 0.4),
                  },
                }}
              >
                <Avatar
                  sx={{
                    width: 40,
                    height: 40,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    fontWeight: 700,
                    fontSize: '1.1rem',
                  }}
                >
                  {user?.nombre?.charAt(0)?.toUpperCase() || <AccountCircle />}
                </Avatar>
              </IconButton>
            </Box>
          </Stack>

          {/* Modern User Menu */}
          <Menu
            id="user-menu"
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            PaperProps={{
              sx: {
                borderRadius: 3,
                mt: 1,
                minWidth: 200,
                background: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(20px)',
                border: '1px solid',
                borderColor: alpha(theme.palette.divider, 0.1),
                boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.15)}`,
              }
            }}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            {/* User Info in Menu */}
            <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                {user?.nombre}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {user?.email}
              </Typography>
              <Chip
                label={user?.rol}
                size="small"
                sx={{
                  mt: 1,
                  background: alpha(theme.palette.primary.main, 0.1),
                  color: 'primary.main',
                  fontWeight: 500,
                }}
              />
            </Box>

            <MenuItem
              onClick={() => { handleMenuClose(); handleNavigation('/settings'); }}
              sx={{
                borderRadius: 2,
                mx: 1,
                my: 0.5,
                '&:hover': {
                  background: alpha(theme.palette.primary.main, 0.08),
                },
              }}
            >
              <ListItemIcon>
                <Settings fontSize="small" sx={{ color: 'primary.main' }} />
              </ListItemIcon>
              <ListItemText
                primary="Configuración"
                primaryTypographyProps={{ fontWeight: 500 }}
              />
            </MenuItem>
            <MenuItem
              onClick={handleLogout}
              sx={{
                borderRadius: 2,
                mx: 1,
                mb: 1,
                color: 'error.main',
                '&:hover': {
                  background: alpha(theme.palette.error.main, 0.08),
                },
              }}
            >
              <ListItemIcon>
                <Logout fontSize="small" sx={{ color: 'error.main' }} />
              </ListItemIcon>
              <ListItemText
                primary="Cerrar Sesión"
                primaryTypographyProps={{ fontWeight: 500 }}
              />
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>
      
      {/* Selector de contexto multi-tenant */}
      <TenantSwitcher 
        open={showTenantSwitcher || showStoreSwitcher}
        onClose={() => {
          setShowTenantSwitcher(false);
          setShowStoreSwitcher(false);
        }}
      />

      {/* Modern Drawer */}
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              borderRadius: '0 16px 16px 0',
              border: 'none',
              boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.15)}`,
            },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              borderRadius: '0 16px 16px 0',
              border: 'none',
              boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.08)}`,
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(20px)',
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Modern Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh',
          background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.02) 0%, rgba(118, 75, 162, 0.02) 100%)',
          position: 'relative',
          '&::before': {
            content: '""',
            position: 'fixed',
            top: 0,
            left: { xs: 0, sm: drawerWidth },
            right: 0,
            bottom: 0,
            background: 'radial-gradient(circle at 20% 50%, rgba(102, 126, 234, 0.05) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(118, 75, 162, 0.05) 0%, transparent 50%)',
            pointerEvents: 'none',
            zIndex: -1,
          },
        }}
      >
        <Toolbar sx={{ minHeight: '80px !important' }} />
        <Box sx={{ position: 'relative', zIndex: 1 }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;