/**
 * Contexto de Autenticación
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User, LoginRequest } from '../types';
import { AuthService } from '../services/authService';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;

  // Cargar usuario al inicializar
  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      const token = AuthService.getAccessToken();
      if (token) {
        // Intentar cargar usuario del localStorage primero
        const cachedUser = AuthService.getCurrentUserFromStorage();
        if (cachedUser) {
          setUser(cachedUser);
        }
        
        // Luego intentar refrescar desde el servidor
        try {
          const currentUser = await AuthService.getCurrentUser();
          setUser(currentUser);
          localStorage.setItem('user', JSON.stringify(currentUser));
        } catch (error) {
          console.warn('No se pudo refrescar el usuario desde el servidor');
          // Si falla, mantener el usuario del cache si existe
          if (!cachedUser) {
            AuthService.logout();
          }
        }
      }
    } catch (error) {
      console.error('Error al inicializar autenticación:', error);
      AuthService.logout();
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (credentials: LoginRequest) => {
    setIsLoading(true);
    try {
      const { user: loggedInUser } = await AuthService.login(credentials);
      setUser(loggedInUser);
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    AuthService.logout();
  };

  const refreshUser = async () => {
    try {
      const currentUser = await AuthService.getCurrentUser();
      setUser(currentUser);
      localStorage.setItem('user', JSON.stringify(currentUser));
    } catch (error) {
      console.error('Error al refrescar usuario:', error);
      logout();
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth debe ser usado dentro de un AuthProvider');
  }
  return context;
};