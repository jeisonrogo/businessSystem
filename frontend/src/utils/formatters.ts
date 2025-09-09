/**
 * Utilidades de formateo
 * 
 * Funciones helper para formatear números, fechas, monedas y otros datos
 * de forma consistente en toda la aplicación.
 */

// ============================================================================
// FORMATEO DE NÚMEROS Y MONEDAS
// ============================================================================

/**
 * Formatea un número como moneda en pesos colombianos
 */
export const formatCurrency = (
  amount: number | string,
  options?: {
    showCurrency?: boolean;
    minimumFractionDigits?: number;
    maximumFractionDigits?: number;
  }
): string => {
  const numericAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
  
  if (isNaN(numericAmount)) return '$0';
  
  const { 
    showCurrency = true, 
    minimumFractionDigits = 0, 
    maximumFractionDigits = 2 
  } = options || {};

  const formatted = numericAmount.toLocaleString('es-CO', {
    minimumFractionDigits,
    maximumFractionDigits
  });

  return showCurrency ? `$${formatted}` : formatted;
};

/**
 * Formatea un número simple con separadores de miles
 */
export const formatNumber = (
  value: number | string,
  decimals: number = 0
): string => {
  const numericValue = typeof value === 'string' ? parseFloat(value) : value;
  
  if (isNaN(numericValue)) return '0';
  
  return numericValue.toLocaleString('es-CO', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
};

/**
 * Formatea un porcentaje
 */
export const formatPercentage = (
  value: number | string,
  decimals: number = 1
): string => {
  const numericValue = typeof value === 'string' ? parseFloat(value) : value;
  
  if (isNaN(numericValue)) return '0%';
  
  return `${numericValue.toFixed(decimals)}%`;
};

// ============================================================================
// FORMATEO DE FECHAS
// ============================================================================

/**
 * Formatea una fecha a formato legible en español
 */
export const formatDate = (
  date: string | Date,
  options?: {
    includeTime?: boolean;
    format?: 'short' | 'medium' | 'long';
  }
): string => {
  if (!date) return '';
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  if (isNaN(dateObj.getTime())) return '';
  
  const { includeTime = false, format = 'medium' } = options || {};
  
  const formatOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: format === 'short' ? '2-digit' : 'short',
    day: '2-digit'
  };
  
  if (includeTime) {
    formatOptions.hour = '2-digit';
    formatOptions.minute = '2-digit';
    formatOptions.hour12 = true;
  }
  
  return dateObj.toLocaleDateString('es-CO', formatOptions);
};

/**
 * Formatea solo la hora de una fecha
 */
export const formatTime = (date: string | Date): string => {
  if (!date) return '';
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  if (isNaN(dateObj.getTime())) return '';
  
  return dateObj.toLocaleTimeString('es-CO', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  });
};

/**
 * Formatea una fecha como tiempo relativo (ej: "hace 2 horas")
 */
export const formatRelativeTime = (date: string | Date): string => {
  if (!date) return '';
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  if (isNaN(dateObj.getTime())) return '';
  
  const now = new Date();
  const diffMs = now.getTime() - dateObj.getTime();
  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffMinutes < 1) return 'Ahora mismo';
  if (diffMinutes < 60) return `Hace ${diffMinutes} min`;
  if (diffHours < 24) return `Hace ${diffHours}h`;
  if (diffDays < 7) return `Hace ${diffDays} días`;
  
  return formatDate(dateObj, { format: 'short' });
};

// ============================================================================
// FORMATEO DE TEXTO
// ============================================================================

/**
 * Trunca un texto a una longitud específica
 */
export const truncateText = (
  text: string,
  maxLength: number,
  suffix: string = '...'
): string => {
  if (!text || text.length <= maxLength) return text;
  
  return text.substring(0, maxLength - suffix.length) + suffix;
};

/**
 * Convierte texto a título (primera letra de cada palabra en mayúscula)
 */
export const toTitleCase = (text: string): string => {
  if (!text) return '';
  
  return text.toLowerCase().replace(/\b\w/g, letter => letter.toUpperCase());
};

/**
 * Formatea un nombre de usuario o cliente
 */
export const formatPersonName = (firstName?: string, lastName?: string): string => {
  const parts = [firstName, lastName].filter(Boolean);
  return parts.join(' ').trim();
};

// ============================================================================
// FORMATEO DE IDENTIFICADORES
// ============================================================================

/**
 * Formatea un número de documento según el tipo
 */
export const formatDocumentNumber = (
  number: string,
  type?: string
): string => {
  if (!number) return '';
  
  const cleaned = number.replace(/\D/g, '');
  
  switch (type?.toUpperCase()) {
    case 'NIT':
      // Formato NIT: 123.456.789-0
      if (cleaned.length >= 9) {
        const digits = cleaned.slice(0, -1);
        const checkDigit = cleaned.slice(-1);
        return digits.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + '-' + checkDigit;
      }
      break;
    case 'CC':
    case 'CEDULA':
      // Formato cédula: 12.345.678
      return cleaned.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    default:
      return number;
  }
  
  return number;
};

/**
 * Formatea un código de producto (SKU)
 */
export const formatSKU = (sku: string): string => {
  if (!sku) return '';
  return sku.toUpperCase();
};

/**
 * Formatea un código de transferencia
 */
export const formatTransferCode = (code: string): string => {
  if (!code) return '';
  
  // Formato: TRF-YYYYMM-NNNN
  const match = code.match(/^(TRF)-(\d{6})-(\d{4})$/);
  if (match) {
    const [, prefix, date, number] = match;
    return `${prefix}-${date}-${number}`;
  }
  
  return code.toUpperCase();
};

// ============================================================================
// FORMATEO DE DIRECCIONES
// ============================================================================

/**
 * Formatea una dirección completa
 */
export const formatAddress = (address: {
  direccion_principal?: string;
  ciudad?: string;
  departamento?: string;
  pais?: string;
}): string => {
  const parts = [
    address.direccion_principal,
    address.ciudad,
    address.departamento,
    address.pais
  ].filter(Boolean);
  
  return parts.join(', ');
};

// ============================================================================
// FORMATEO DE ESTADOS Y ENUMS
// ============================================================================

/**
 * Formatea el estado de una transferencia
 */
export const formatTransferStatus = (status: string): string => {
  const statusMap: { [key: string]: string } = {
    'PENDIENTE': 'Pendiente',
    'ENVIADA': 'Enviada',
    'RECIBIDA': 'Recibida',
    'CANCELADA': 'Cancelada'
  };
  
  return statusMap[status] || status;
};

/**
 * Formatea el tipo de local
 */
export const formatLocalType = (type: string): string => {
  const typeMap: { [key: string]: string } = {
    'SUCURSAL': 'Sucursal',
    'ALMACEN': 'Almacén',
    'SHOWROOM': 'Showroom',
    'VIRTUAL': 'Virtual'
  };
  
  return typeMap[type] || type;
};

/**
 * Formatea el rol de un usuario
 */
export const formatUserRole = (role: string): string => {
  const roleMap: { [key: string]: string } = {
    'ADMINISTRADOR': 'Administrador',
    'GERENTE_VENTAS': 'Gerente de Ventas',
    'CONTADOR': 'Contador',
    'VENDEDOR': 'Vendedor'
  };
  
  return roleMap[role] || role;
};

// ============================================================================
// FORMATEO DE COLORES Y ESTILOS
// ============================================================================

/**
 * Obtiene el color para un estado específico
 */
export const getStatusColor = (status: string): string => {
  const colorMap: { [key: string]: string } = {
    'ACTIVO': '#4caf50',
    'INACTIVO': '#f44336',
    'PENDIENTE': '#ff9800',
    'ENVIADA': '#2196f3',
    'RECIBIDA': '#4caf50',
    'CANCELADA': '#f44336',
    'PAGADA': '#4caf50',
    'EMITIDA': '#ff9800',
    'ANULADA': '#f44336'
  };
  
  return colorMap[status] || '#757575';
};

// ============================================================================
// VALIDACIONES DE FORMATO
// ============================================================================

/**
 * Valida si un texto es un email válido
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Valida si un texto es un número de teléfono válido (Colombia)
 */
export const isValidPhone = (phone: string): boolean => {
  const phoneRegex = /^[\+]?[(]?[\d\s\-\(\)]{10,}$/;
  return phoneRegex.test(phone);
};

/**
 * Valida si un código es válido (solo letras, números y guiones)
 */
export const isValidCode = (code: string): boolean => {
  const codeRegex = /^[A-Za-z0-9\-_]+$/;
  return codeRegex.test(code);
};

// ============================================================================
// EXPORTACIONES POR DEFECTO
// ============================================================================

export default {
  formatCurrency,
  formatNumber,
  formatPercentage,
  formatDate,
  formatTime,
  formatRelativeTime,
  truncateText,
  toTitleCase,
  formatPersonName,
  formatDocumentNumber,
  formatSKU,
  formatTransferCode,
  formatAddress,
  formatTransferStatus,
  formatLocalType,
  formatUserRole,
  getStatusColor,
  isValidEmail,
  isValidPhone,
  isValidCode
};