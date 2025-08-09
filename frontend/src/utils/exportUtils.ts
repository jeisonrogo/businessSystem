/**
 * Utilidades para exportación de datos
 * Funciones para exportar a CSV, Excel y generar reportes
 */

import { KardexResponse, InventoryMovement, Product, MovementType } from '../types';
import { InventoryService } from '../services/inventoryService';

/**
 * Convertir datos a formato CSV
 */
export const convertToCSV = (data: any[], headers: string[]): string => {
  const csvHeaders = headers.join(',');
  const csvRows = data.map(row => 
    headers.map(header => {
      const value = row[header];
      // Escapar comillas y envolver en comillas si contiene comas o saltos de línea
      if (typeof value === 'string' && (value.includes(',') || value.includes('\n') || value.includes('"'))) {
        return `"${value.replace(/"/g, '""')}"`;
      }
      return value || '';
    }).join(',')
  );
  
  return [csvHeaders, ...csvRows].join('\n');
};

/**
 * Descargar archivo CSV
 */
export const downloadCSV = (csvContent: string, filename: string): void => {
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  
  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
};

/**
 * Exportar kardex a CSV
 */
export const exportKardexToCSV = (kardex: KardexResponse, product: Product): void => {
  const typeLabels = InventoryService.getMovementTypeLabels();
  
  // Preparar datos del kardex
  const kardexData = kardex.movimientos.map(movement => ({
    'Fecha': new Date(movement.created_at).toLocaleString('es-CO'),
    'Tipo de Movimiento': typeLabels[movement.tipo_movimiento],
    'Cantidad': InventoryService.formatQuantityWithSign(movement.tipo_movimiento, movement.cantidad),
    'Precio Unitario': movement.precio_unitario ? parseFloat(movement.precio_unitario.toString()) : 0,
    'Costo Unitario': movement.costo_unitario ? parseFloat(movement.costo_unitario.toString()) : 0,
    'Stock Anterior': movement.stock_anterior,
    'Stock Posterior': movement.stock_posterior,
    'Referencia': movement.referencia || '',
    'Observaciones': movement.observaciones || '',
  }));

  // Headers para CSV
  const headers = [
    'Fecha',
    'Tipo de Movimiento', 
    'Cantidad',
    'Precio Unitario',
    'Costo Unitario',
    'Stock Anterior',
    'Stock Posterior',
    'Referencia',
    'Observaciones'
  ];

  // Generar CSV
  const csvContent = convertToCSV(kardexData, headers);
  
  // Crear nombre de archivo
  const now = new Date();
  const dateStr = now.toISOString().split('T')[0];
  const filename = `kardex_${product.sku}_${dateStr}.csv`;
  
  downloadCSV(csvContent, filename);
};

/**
 * Exportar movimientos a CSV
 */
export const exportMovementsToCSV = (movements: InventoryMovement[]): void => {
  const typeLabels = InventoryService.getMovementTypeLabels();
  
  // Preparar datos de movimientos
  const movementsData = movements.map(movement => ({
    'ID': movement.id,
    'Fecha': new Date(movement.created_at).toLocaleString('es-CO'),
    'Producto': movement.producto?.nombre || 'N/A',
    'SKU': movement.producto?.sku || 'N/A',
    'Tipo de Movimiento': typeLabels[movement.tipo_movimiento],
    'Cantidad': InventoryService.formatQuantityWithSign(movement.tipo_movimiento, movement.cantidad),
    'Precio Unitario': movement.precio_unitario ? parseFloat(movement.precio_unitario.toString()) : 0,
    'Costo Unitario': movement.costo_unitario ? parseFloat(movement.costo_unitario.toString()) : 0,
    'Valor Total': InventoryService.calculateMovementValue(movement),
    'Stock Anterior': movement.stock_anterior,
    'Stock Posterior': movement.stock_posterior,
    'Referencia': movement.referencia || '',
    'Observaciones': movement.observaciones || '',
  }));

  // Headers para CSV
  const headers = [
    'ID',
    'Fecha',
    'Producto',
    'SKU',
    'Tipo de Movimiento',
    'Cantidad',
    'Precio Unitario',
    'Costo Unitario',
    'Valor Total',
    'Stock Anterior',
    'Stock Posterior',
    'Referencia',
    'Observaciones'
  ];

  // Generar CSV
  const csvContent = convertToCSV(movementsData, headers);
  
  // Crear nombre de archivo
  const now = new Date();
  const dateStr = now.toISOString().split('T')[0];
  const filename = `movimientos_inventario_${dateStr}.csv`;
  
  downloadCSV(csvContent, filename);
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