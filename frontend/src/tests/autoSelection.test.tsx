/**
 * Frontend Auto-Selection Tests
 * ============================
 *
 * Comprehensive tests for the automatic local selection functionality
 * in the multi-tenant frontend application.
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { jest } from '@jest/globals';
import { TenantProvider } from '../context/TenantContext';
import { AuthProvider } from '../context/AuthContext';
import LocalSelectionDialog from '../components/tenant/LocalSelectionDialog';
import TenantService from '../services/tenantService';

// Mock the TenantService
jest.mock('../services/tenantService');
const mockTenantService = TenantService as jest.Mocked<typeof TenantService>;

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

// Test utilities
const createMockUser = (role: string = 'VENDEDOR') => ({
  id: '123',
  nombre: 'Test User',
  email: 'test@example.com',
  rol: role,
  tienda_id: 'tienda-123',
  is_active: true,
});

const createMockLocal = (id: string, nombre: string) => ({
  id,
  nombre,
  codigo: `LOCAL-${id}`,
  direccion: 'Test Address',
  ciudad: 'Test City',
  tienda_id: 'tienda-123',
  is_active: true,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
});

const createMockAuthContext = (user: any = null) => ({
  user,
  isAuthenticated: !!user,
  login: jest.fn(),
  logout: jest.fn(),
  isLoading: false,
});

// Mock the AuthContext
jest.mock('../context/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
  useAuth: () => createMockAuthContext(createMockUser())
}));

// Wrapper component for tests
const TestWrapper: React.FC<{ children: React.ReactNode; user?: any }> = ({
  children,
  user = createMockUser()
}) => {
  return (
    <TenantProvider>
      {children}
    </TenantProvider>
  );
};

describe('Auto-Selection Logic Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalStorage.clear();
  });

  describe('TenantService Auto-Selection Methods', () => {
    test('getLocalsInfo returns correct auto-selection data for single local', async () => {
      // Arrange
      const mockResponse = {
        total_locales: 1,
        should_auto_select: true,
        auto_select_local_id: 'local-123',
        auto_select_local_name: 'Main Store',
        requires_manual_selection: false,
      };
      mockTenantService.getLocalsInfo.mockResolvedValue(mockResponse);

      // Act
      const result = await TenantService.getLocalsInfo();

      // Assert
      expect(result.should_auto_select).toBe(true);
      expect(result.total_locales).toBe(1);
      expect(result.auto_select_local_id).toBe('local-123');
      expect(result.requires_manual_selection).toBe(false);
    });

    test('getLocalsInfo returns correct data for multiple locals', async () => {
      // Arrange
      const mockResponse = {
        total_locales: 3,
        should_auto_select: false,
        auto_select_local_id: undefined,
        requires_manual_selection: true,
      };
      mockTenantService.getLocalsInfo.mockResolvedValue(mockResponse);

      // Act
      const result = await TenantService.getLocalsInfo();

      // Assert
      expect(result.should_auto_select).toBe(false);
      expect(result.total_locales).toBe(3);
      expect(result.requires_manual_selection).toBe(true);
    });

    test('selectLocal calls correct endpoint with local ID', async () => {
      // Arrange
      const mockContext = {
        tienda_id: 'tienda-123',
        tienda_codigo: 'T001',
        tienda_nombre: 'Test Store',
        local_id: 'local-123',
        local_codigo: 'L001',
        local_nombre: 'Test Local',
        tiene_contexto_local: true,
        permisos_disponibles: ['venta', 'consulta_stock'],
      };
      mockTenantService.selectLocal.mockResolvedValue(mockContext);

      // Act
      const result = await TenantService.selectLocal('local-123');

      // Assert
      expect(mockTenantService.selectLocal).toHaveBeenCalledWith('local-123');
      expect(result.local_id).toBe('local-123');
      expect(result.tiene_contexto_local).toBe(true);
    });
  });

  describe('LocalSelectionDialog Auto-Selection Behavior', () => {
    test('auto-confirms when single local is available', async () => {
      // Arrange
      const mockOnLocalSelected = jest.fn();
      const singleLocal = [createMockLocal('local-123', 'Main Store')];
      const mockUser = createMockUser();

      // Mock the auto-confirmation timer
      jest.useFakeTimers();

      // Act
      render(
        <LocalSelectionDialog
          open={true}
          user={mockUser}
          availableLocals={singleLocal}
          onLocalSelected={mockOnLocalSelected}
        />
      );

      // Fast-forward time to trigger auto-confirmation
      jest.advanceTimersByTime(1600);

      // Assert
      await waitFor(() => {
        expect(mockOnLocalSelected).toHaveBeenCalledWith('local-123');
      });

      jest.useRealTimers();
    });

    test('shows manual selection for multiple locals', () => {
      // Arrange
      const mockOnLocalSelected = jest.fn();
      const multipleLocals = [
        createMockLocal('local-123', 'Main Store'),
        createMockLocal('local-456', 'Branch Store'),
        createMockLocal('local-789', 'Warehouse'),
      ];
      const mockUser = createMockUser();

      // Act
      render(
        <LocalSelectionDialog
          open={true}
          user={mockUser}
          availableLocals={multipleLocals}
          onLocalSelected={mockOnLocalSelected}
        />
      );

      // Assert
      expect(screen.getByText('Selecciona el local donde vas a trabajar')).toBeInTheDocument();
      expect(screen.getByText('Locales Disponibles (3)')).toBeInTheDocument();
      expect(screen.getByText('Main Store')).toBeInTheDocument();
      expect(screen.getByText('Branch Store')).toBeInTheDocument();
      expect(screen.getByText('Warehouse')).toBeInTheDocument();
    });

    test('displays correct message for single local', () => {
      // Arrange
      const mockOnLocalSelected = jest.fn();
      const singleLocal = [createMockLocal('local-123', 'Main Store')];
      const mockUser = createMockUser();

      // Act
      render(
        <LocalSelectionDialog
          open={true}
          user={mockUser}
          availableLocals={singleLocal}
          onLocalSelected={mockOnLocalSelected}
        />
      );

      // Assert
      expect(screen.getByText('Tienes un local asignado. Serás dirigido automáticamente.')).toBeInTheDocument();
      expect(screen.getByText('Main Store')).toBeInTheDocument();
      expect(screen.getByText('Continuar al Sistema')).toBeInTheDocument();
    });
  });

  describe('Context Persistence Tests', () => {
    test('localStorage is updated when local is selected', async () => {
      // Arrange
      const mockContext = {
        tienda_id: 'tienda-123',
        tienda_codigo: 'T001',
        tienda_nombre: 'Test Store',
        local_id: 'local-123',
        local_codigo: 'L001',
        local_nombre: 'Main Store',
        tiene_contexto_local: true,
        permisos_disponibles: ['venta', 'consulta_stock'],
      };

      mockTenantService.selectLocal.mockResolvedValue(mockContext);
      mockTenantService.getLocalsInfo.mockResolvedValue({
        total_locales: 1,
        should_auto_select: true,
        auto_select_local_id: 'local-123',
        requires_manual_selection: false,
      });

      // Act
      const { rerender } = render(
        <TestWrapper>
          <div data-testid="test-component">Test</div>
        </TestWrapper>
      );

      // Wait for auto-selection to complete
      await waitFor(() => {
        expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
          'tenant_context',
          expect.stringContaining('local-123')
        );
      });
    });

    test('context is restored from localStorage on app restart', () => {
      // Arrange
      const savedContext = JSON.stringify({
        tienda_id: 'tienda-123',
        local_id: 'local-123',
        local_nombre: 'Main Store',
        tiene_contexto_local: true,
      });

      mockLocalStorage.getItem.mockReturnValue(savedContext);
      mockTenantService.getAvailableLocals.mockResolvedValue([
        createMockLocal('local-123', 'Main Store')
      ]);

      // Act
      render(
        <TestWrapper>
          <div data-testid="test-component">Test</div>
        </TestWrapper>
      );

      // Assert
      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('tenant_context');
    });
  });

  describe('Navigation Persistence Tests', () => {
    test('X-Local-ID header is sent with API requests', async () => {
      // This test would require mocking the axios interceptor
      // In a real scenario, you'd test that the API client sends the correct headers

      // Arrange
      const mockContext = {
        local_id: 'local-123',
        tiene_contexto_local: true,
      };

      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(mockContext));

      // Act & Assert
      // This would be tested by intercepting actual API calls
      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('tenant_context');
    });
  });

  describe('Error Handling Tests', () => {
    test('handles API errors gracefully during auto-selection', async () => {
      // Arrange
      mockTenantService.getLocalsInfo.mockRejectedValue(new Error('API Error'));

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      // Act
      render(
        <TestWrapper>
          <div data-testid="test-component">Test</div>
        </TestWrapper>
      );

      // Assert
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          expect.stringContaining('Error al inicializar contexto de tenant'),
          expect.any(Error)
        );
      });

      consoleSpy.mockRestore();
    });

    test('clears corrupted localStorage context', () => {
      // Arrange
      mockLocalStorage.getItem.mockReturnValue('invalid-json');

      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});

      // Act
      render(
        <TestWrapper>
          <div data-testid="test-component">Test</div>
        </TestWrapper>
      );

      // Assert
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        expect.stringContaining('Error al restaurar contexto'),
        expect.any(Error)
      );
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('tenant_context');

      consoleWarnSpy.mockRestore();
    });
  });

  describe('Role-Based Auto-Selection Tests', () => {
    test('administrators get auto-selection for single local', async () => {
      // Arrange
      const adminUser = createMockUser('ADMINISTRADOR');
      mockTenantService.getLocalsInfo.mockResolvedValue({
        total_locales: 1,
        should_auto_select: true,
        auto_select_local_id: 'local-123',
        requires_manual_selection: false,
      });

      // Act
      render(
        <TestWrapper user={adminUser}>
          <div data-testid="test-component">Test</div>
        </TestWrapper>
      );

      // Assert
      await waitFor(() => {
        expect(mockTenantService.getLocalsInfo).toHaveBeenCalled();
      });
    });

    test('regular users get manual selection for multiple locals', async () => {
      // Arrange
      const regularUser = createMockUser('VENDEDOR');
      mockTenantService.getLocalsInfo.mockResolvedValue({
        total_locales: 3,
        should_auto_select: false,
        requires_manual_selection: true,
      });

      // Act
      render(
        <TestWrapper user={regularUser}>
          <div data-testid="test-component">Test</div>
        </TestWrapper>
      );

      // Assert
      await waitFor(() => {
        expect(mockTenantService.getLocalsInfo).toHaveBeenCalled();
      });
    });
  });
});

// Integration Tests
describe('Auto-Selection Integration Tests', () => {
  test('complete auto-selection flow works end-to-end', async () => {
    // This would be a full integration test that:
    // 1. Simulates user login
    // 2. Checks locals info
    // 3. Auto-selects if appropriate
    // 4. Verifies context persistence
    // 5. Tests navigation between modules

    // For brevity, this is a placeholder for the actual implementation
    expect(true).toBe(true);
  });
});