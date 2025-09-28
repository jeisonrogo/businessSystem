/**
 * Utilidades para exportación de datos
 * Funciones para exportar a CSV, Excel y generar reportes
 */

import { KardexResponse, Product, MovementType } from '../types';
import { InventoryService } from '../services/inventoryService';

/**
 * Obtener headers con autenticación y contexto tenant
 */
const getHeaders = (): HeadersInit => {
  const token = localStorage.getItem('access_token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Agregar contexto tenant si está disponible
  try {
    const tenantContext = localStorage.getItem('tenant_context');
    if (tenantContext) {
      const context = JSON.parse(tenantContext);
      if (context.local_id) {
        headers['X-Local-ID'] = context.local_id;
      }
    }
  } catch (error) {
    console.warn('Error al obtener contexto tenant para exportación:', error);
  }

  return headers;
};


/**
 * Descargar archivo Excel desde blob
 */
export const downloadExcel = (blob: Blob, filename: string): void => {
  const link = document.createElement('a');

  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }
};

/**
 * Exportar kardex a Excel
 */
export const exportKardexToExcel = async (product: Product): Promise<void> => {
  try {
    const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

    // Llamar al endpoint de exportación Excel
    const response = await fetch(
      `${API_BASE_URL}/api/v1/inventario/kardex/${product.id}/export/excel`,
      {
        method: 'GET',
        headers: getHeaders(),
      }
    );

    if (!response.ok) {
      throw new Error(`Error al exportar kardex: ${response.statusText}`);
    }

    // Obtener el blob del archivo Excel
    const blob = await response.blob();

    // Crear nombre de archivo
    const now = new Date();
    const dateStr = now.toISOString().split('T')[0];
    const filename = `kardex_${product.sku}_${dateStr}.xlsx`;

    // Descargar archivo
    downloadExcel(blob, filename);
  } catch (error) {
    console.error('Error exportando kardex:', error);
    throw new Error('Error al exportar kardex a Excel');
  }
};


/**
 * Exportar movimientos a Excel
 */
export const exportMovementsToExcel = async (
  filters?: {
    producto_id?: string;
    tipo_movimiento?: string;
    fecha_inicio?: string;
    fecha_fin?: string;
    limit?: number;
  }
): Promise<void> => {
  try {
    const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

    // Construir parámetros de query
    const queryParams = new URLSearchParams();
    if (filters?.producto_id) queryParams.append('producto_id', filters.producto_id);
    if (filters?.tipo_movimiento) queryParams.append('tipo_movimiento', filters.tipo_movimiento);
    if (filters?.fecha_inicio) queryParams.append('fecha_inicio', filters.fecha_inicio);
    if (filters?.fecha_fin) queryParams.append('fecha_fin', filters.fecha_fin);
    if (filters?.limit) queryParams.append('limit', filters.limit.toString());

    const url = `${API_BASE_URL}/api/v1/inventario/movimientos/export/excel${
      queryParams.toString() ? `?${queryParams.toString()}` : ''
    }`;

    // Llamar al endpoint de exportación Excel
    const response = await fetch(url, {
      method: 'GET',
      headers: getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Error al exportar movimientos: ${response.statusText}`);
    }

    // Obtener el blob del archivo Excel
    const blob = await response.blob();

    // Crear nombre de archivo
    const now = new Date();
    const dateStr = now.toISOString().split('T')[0];
    const filename = `movimientos_inventario_${dateStr}.xlsx`;

    // Descargar archivo
    downloadExcel(blob, filename);
  } catch (error) {
    console.error('Error exportando movimientos:', error);
    throw new Error('Error al exportar movimientos a Excel');
  }
};


/**
 * Generar contenido HTML para impresión del kardex
 */
export const generateKardexPrintHTML = (kardex: KardexResponse, product: Product): string => {
  const typeLabels = InventoryService.getMovementTypeLabels();
  const formatCurrency = InventoryService.formatCurrency;
  
  const now = new Date();
  const dateStr = now.toLocaleDateString('es-CO');
  const timeStr = now.toLocaleTimeString('es-CO');

  const movementsHtml = kardex.movimientos.map(movement => `
    <tr>
      <td>${new Date(movement.created_at).toLocaleString('es-CO')}</td>
      <td>${typeLabels[movement.tipo_movimiento]}</td>
      <td style="text-align: right">${InventoryService.formatQuantityWithSign(movement.tipo_movimiento, movement.cantidad)}</td>
      <td style="text-align: right">${movement.precio_unitario ? formatCurrency(parseFloat(movement.precio_unitario.toString())) : '-'}</td>
      <td style="text-align: right">${movement.costo_unitario ? formatCurrency(parseFloat(movement.costo_unitario.toString())) : '-'}</td>
      <td style="text-align: right">${movement.stock_anterior}</td>
      <td style="text-align: right">${movement.stock_posterior}</td>
      <td>${movement.referencia || '-'}</td>
      <td>${movement.observaciones || '-'}</td>
    </tr>
  `).join('');

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>Kardex - ${product.sku}</title>
      <style>
        @media print {
          body { margin: 0; }
          .no-print { display: none; }
        }
        body {
          font-family: Arial, sans-serif;
          font-size: 12px;
          line-height: 1.4;
          margin: 20px;
        }
        .header {
          text-align: center;
          margin-bottom: 30px;
          border-bottom: 2px solid #333;
          padding-bottom: 20px;
        }
        .header h1 {
          margin: 0;
          color: #333;
          font-size: 24px;
        }
        .header h2 {
          margin: 5px 0;
          color: #666;
          font-size: 18px;
          font-weight: normal;
        }
        .info-section {
          display: flex;
          justify-content: space-between;
          margin-bottom: 20px;
          padding: 15px;
          background-color: #f5f5f5;
          border-radius: 5px;
        }
        .info-box {
          text-align: center;
        }
        .info-box .label {
          font-weight: bold;
          color: #666;
          font-size: 10px;
          text-transform: uppercase;
        }
        .info-box .value {
          font-size: 16px;
          font-weight: bold;
          color: #333;
          margin-top: 5px;
        }
        table {
          width: 100%;
          border-collapse: collapse;
          margin-top: 20px;
        }
        th, td {
          border: 1px solid #ddd;
          padding: 8px;
          text-align: left;
        }
        th {
          background-color: #f2f2f2;
          font-weight: bold;
          font-size: 11px;
        }
        td {
          font-size: 10px;
        }
        .footer {
          margin-top: 30px;
          text-align: center;
          font-size: 10px;
          color: #666;
          border-top: 1px solid #ddd;
          padding-top: 10px;
        }
        .summary {
          display: flex;
          justify-content: space-around;
          margin: 20px 0;
          padding: 15px;
          background-color: #f9f9f9;
          border-radius: 5px;
        }
        .summary-item {
          text-align: center;
        }
        .summary-item .count {
          font-size: 18px;
          font-weight: bold;
          color: #333;
        }
        .summary-item .label {
          font-size: 11px;
          color: #666;
          text-transform: uppercase;
        }
      </style>
    </head>
    <body>
      <div class="header">
        <h1>KARDEX DE PRODUCTO</h1>
        <h2>${product.nombre}</h2>
        <p>SKU: ${product.sku} | Generado: ${dateStr} ${timeStr}</p>
      </div>

      <div class="info-section">
        <div class="info-box">
          <div class="label">Stock Actual</div>
          <div class="value">${kardex.stock_actual}</div>
        </div>
        <div class="info-box">
          <div class="label">Costo Promedio</div>
          <div class="value">${formatCurrency(parseFloat(kardex.costo_promedio_actual))}</div>
        </div>
        <div class="info-box">
          <div class="label">Valor Total</div>
          <div class="value">${formatCurrency(parseFloat(kardex.valor_inventario))}</div>
        </div>
        <div class="info-box">
          <div class="label">Total Movimientos</div>
          <div class="value">${kardex.total_movimientos}</div>
        </div>
      </div>

      <div class="summary">
        <div class="summary-item">
          <div class="count">${kardex.movimientos.filter(m => m.tipo_movimiento === MovementType.ENTRADA).length}</div>
          <div class="label">Entradas</div>
        </div>
        <div class="summary-item">
          <div class="count">${kardex.movimientos.filter(m => m.tipo_movimiento === MovementType.SALIDA).length}</div>
          <div class="label">Salidas</div>
        </div>
        <div class="summary-item">
          <div class="count">${kardex.movimientos.filter(m => m.tipo_movimiento === MovementType.MERMA).length}</div>
          <div class="label">Mermas</div>
        </div>
        <div class="summary-item">
          <div class="count">${kardex.movimientos.filter(m => m.tipo_movimiento === MovementType.AJUSTE).length}</div>
          <div class="label">Ajustes</div>
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Tipo</th>
            <th>Cantidad</th>
            <th>Precio Unit.</th>
            <th>Costo Unit.</th>
            <th>Stock Ant.</th>
            <th>Stock Post.</th>
            <th>Referencia</th>
            <th>Observaciones</th>
          </tr>
        </thead>
        <tbody>
          ${movementsHtml}
        </tbody>
      </table>

      <div class="footer">
        <p>Sistema de Gestión Empresarial | Reporte generado automáticamente el ${dateStr} a las ${timeStr}</p>
      </div>
    </body>
    </html>
  `;
};

/**
 * Imprimir kardex
 */
export const printKardex = (kardex: KardexResponse, product: Product): void => {
  const printWindow = window.open('', '_blank');
  if (printWindow) {
    const htmlContent = generateKardexPrintHTML(kardex, product);
    printWindow.document.write(htmlContent);
    printWindow.document.close();
    
    // Esperar a que se cargue completamente antes de imprimir
    printWindow.addEventListener('load', () => {
      printWindow.focus();
      printWindow.print();
    });
  }
};