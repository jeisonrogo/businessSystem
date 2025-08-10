/**
 * Utilidades para imprimir facturas
 * Genera HTML optimizado para impresión con estilos CSS específicos
 */

import { Invoice } from '../types';
import { InvoicesService } from '../services/invoicesService';

export interface PrintOptions {
  showHeader?: boolean;
  showFooter?: boolean;
  showTotals?: boolean;
  showDetails?: boolean;
  companyName?: string;
  companyAddress?: string;
  companyPhone?: string;
  companyEmail?: string;
}

const defaultOptions: PrintOptions = {
  showHeader: true,
  showFooter: true,
  showTotals: true,
  showDetails: true,
  companyName: 'Mi Empresa',
  companyAddress: 'Dirección de la empresa',
  companyPhone: 'Teléfono de contacto',
  companyEmail: 'contacto@empresa.com'
};

export class InvoicePrintUtils {
  /**
   * Imprime una factura abriendo una nueva ventana con el formato de impresión
   */
  static async printInvoice(invoice: Invoice, options: PrintOptions = {}): Promise<void> {
    const printOptions = { ...defaultOptions, ...options };
    const htmlContent = this.generateInvoiceHTML(invoice, printOptions);
    
    const printWindow = window.open('', '_blank', 'width=800,height=600');
    if (!printWindow) {
      throw new Error('No se pudo abrir la ventana de impresión. Verifique que los pop-ups estén habilitados.');
    }

    printWindow.document.write(htmlContent);
    printWindow.document.close();

    // Esperar a que se cargue el contenido y luego imprimir
    printWindow.onload = () => {
      setTimeout(() => {
        printWindow.print();
        printWindow.close();
      }, 250);
    };
  }

  /**
   * Genera el HTML completo para la impresión de la factura
   */
  static generateInvoiceHTML(invoice: Invoice, options: PrintOptions): string {
    const styles = this.getInvoiceStyles();
    const header = options.showHeader ? this.generateHeader(options) : '';
    const invoiceInfo = this.generateInvoiceInfo(invoice);
    const clientInfo = this.generateClientInfo(invoice);
    const details = options.showDetails ? this.generateInvoiceDetails(invoice) : '';
    const totals = options.showTotals ? this.generateTotals(invoice) : '';
    const footer = options.showFooter ? this.generateFooter(options) : '';

    return `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Factura ${InvoicesService.formatInvoiceNumber(invoice.numero_factura)}</title>
    <style>${styles}</style>
</head>
<body>
    <div class="invoice-container">
        ${header}
        
        <div class="invoice-header-section">
            ${invoiceInfo}
            ${clientInfo}
        </div>
        
        ${details}
        ${totals}
        ${footer}
    </div>
</body>
</html>`;
  }

  /**
   * Genera los estilos CSS para la impresión
   */
  private static getInvoiceStyles(): string {
    return `
      @media print {
        @page {
          margin: 0.5in;
          size: A4;
        }
      }
      
      * {
        box-sizing: border-box;
      }
      
      body {
        font-family: 'Arial', sans-serif;
        font-size: 12px;
        line-height: 1.4;
        color: #333;
        margin: 0;
        padding: 0;
      }
      
      .invoice-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
      }
      
      .company-header {
        text-align: center;
        border-bottom: 2px solid #333;
        padding-bottom: 20px;
        margin-bottom: 30px;
      }
      
      .company-name {
        font-size: 24px;
        font-weight: bold;
        color: #333;
        margin-bottom: 10px;
      }
      
      .company-info {
        font-size: 11px;
        color: #666;
        line-height: 1.3;
      }
      
      .invoice-header-section {
        display: flex;
        justify-content: space-between;
        margin-bottom: 30px;
        gap: 40px;
      }
      
      .invoice-info, .client-info {
        flex: 1;
      }
      
      .section-title {
        font-size: 14px;
        font-weight: bold;
        color: #333;
        border-bottom: 1px solid #ddd;
        padding-bottom: 5px;
        margin-bottom: 15px;
      }
      
      .info-row {
        margin-bottom: 8px;
      }
      
      .info-label {
        font-weight: bold;
        color: #555;
        display: inline-block;
        width: 120px;
      }
      
      .info-value {
        color: #333;
      }
      
      .invoice-number {
        font-size: 18px;
        font-weight: bold;
        color: #e74c3c;
      }
      
      .status-chip {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 10px;
        font-weight: bold;
        text-transform: uppercase;
      }
      
      .status-emitida {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
      }
      
      .status-pagada {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
      }
      
      .status-anulada {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
      }
      
      .details-table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-size: 11px;
      }
      
      .details-table th {
        background-color: #f8f9fa;
        border: 1px solid #ddd;
        padding: 10px 8px;
        text-align: left;
        font-weight: bold;
        color: #333;
      }
      
      .details-table td {
        border: 1px solid #ddd;
        padding: 8px;
        vertical-align: top;
      }
      
      .details-table tr:nth-child(even) {
        background-color: #f9f9f9;
      }
      
      .text-right {
        text-align: right;
      }
      
      .text-center {
        text-align: center;
      }
      
      .product-name {
        font-weight: bold;
        color: #333;
      }
      
      .product-sku {
        font-size: 10px;
        color: #666;
        font-style: italic;
      }
      
      .totals-section {
        float: right;
        width: 300px;
        margin-top: 20px;
      }
      
      .totals-table {
        width: 100%;
        border-collapse: collapse;
      }
      
      .totals-table td {
        padding: 8px 12px;
        border-bottom: 1px solid #eee;
      }
      
      .totals-table .total-label {
        font-weight: bold;
        text-align: right;
      }
      
      .totals-table .total-value {
        text-align: right;
        font-family: 'Courier New', monospace;
      }
      
      .grand-total {
        border-top: 2px solid #333 !important;
        font-size: 14px;
        font-weight: bold;
        background-color: #f8f9fa;
      }
      
      .footer {
        clear: both;
        margin-top: 50px;
        padding-top: 20px;
        border-top: 1px solid #ddd;
        text-align: center;
        font-size: 11px;
        color: #666;
      }
      
      .overdue-notice {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 10px;
        margin-bottom: 20px;
        border-radius: 4px;
        text-align: center;
        font-weight: bold;
      }
      
      @media print {
        .invoice-container {
          padding: 0;
        }
        
        body {
          font-size: 11px;
        }
        
        .company-name {
          font-size: 22px;
        }
        
        .invoice-number {
          font-size: 16px;
        }
        
        .totals-section {
          page-break-inside: avoid;
        }
      }
    `;
  }

  /**
   * Genera el encabezado de la empresa
   */
  private static generateHeader(options: PrintOptions): string {
    return `
      <div class="company-header">
        <div class="company-name">${options.companyName}</div>
        <div class="company-info">
          ${options.companyAddress}<br>
          Tel: ${options.companyPhone} | Email: ${options.companyEmail}
        </div>
      </div>
    `;
  }

  /**
   * Genera la información de la factura
   */
  private static generateInvoiceInfo(invoice: Invoice): string {
    const isOverdue = invoice.fecha_vencimiento && 
      new Date(invoice.fecha_vencimiento) < new Date() && 
      invoice.estado === 'EMITIDA';

    let statusClass = 'status-emitida';
    if (invoice.estado === 'PAGADA') statusClass = 'status-pagada';
    if (invoice.estado === 'ANULADA') statusClass = 'status-anulada';

    return `
      <div class="invoice-info">
        <div class="section-title">Información de la Factura</div>
        
        ${isOverdue ? '<div class="overdue-notice">⚠️ FACTURA VENCIDA</div>' : ''}
        
        <div class="info-row">
          <span class="info-label">Número:</span>
          <span class="info-value invoice-number">
            ${InvoicesService.formatInvoiceNumber(invoice.numero_factura)}
          </span>
        </div>
        
        <div class="info-row">
          <span class="info-label">Estado:</span>
          <span class="status-chip ${statusClass}">
            ${InvoicesService.getInvoiceStatusLabel(invoice.estado)}
          </span>
        </div>
        
        <div class="info-row">
          <span class="info-label">Tipo:</span>
          <span class="info-value">
            ${InvoicesService.getInvoiceTypeLabel(invoice.tipo_factura)}
          </span>
        </div>
        
        <div class="info-row">
          <span class="info-label">F. Emisión:</span>
          <span class="info-value">
            ${new Date(invoice.fecha_emision).toLocaleDateString('es-CO')}
          </span>
        </div>
        
        ${invoice.fecha_vencimiento ? `
          <div class="info-row">
            <span class="info-label">F. Vencimiento:</span>
            <span class="info-value" ${isOverdue ? 'style="color: #e74c3c; font-weight: bold;"' : ''}>
              ${new Date(invoice.fecha_vencimiento).toLocaleDateString('es-CO')}
            </span>
          </div>
        ` : ''}
        
        ${invoice.fecha_pago ? `
          <div class="info-row">
            <span class="info-label">F. Pago:</span>
            <span class="info-value" style="color: #27ae60; font-weight: bold;">
              ${new Date(invoice.fecha_pago).toLocaleDateString('es-CO')}
            </span>
          </div>
        ` : ''}
      </div>
    `;
  }

  /**
   * Genera la información del cliente
   */
  private static generateClientInfo(invoice: Invoice): string {
    const client = invoice.cliente;
    
    return `
      <div class="client-info">
        <div class="section-title">Información del Cliente</div>
        
        <div class="info-row">
          <span class="info-label">Cliente:</span>
          <span class="info-value">${client?.nombre_completo || 'N/A'}</span>
        </div>
        
        <div class="info-row">
          <span class="info-label">Documento:</span>
          <span class="info-value">${client?.numero_documento || 'N/A'}</span>
        </div>
        
        ${client?.email ? `
          <div class="info-row">
            <span class="info-label">Email:</span>
            <span class="info-value">${client.email}</span>
          </div>
        ` : ''}
        
        ${client?.telefono ? `
          <div class="info-row">
            <span class="info-label">Teléfono:</span>
            <span class="info-value">${client.telefono}</span>
          </div>
        ` : ''}
        
        ${client?.direccion ? `
          <div class="info-row">
            <span class="info-label">Dirección:</span>
            <span class="info-value">${client.direccion}</span>
          </div>
        ` : ''}
      </div>
    `;
  }

  /**
   * Genera la tabla de detalles de la factura
   */
  private static generateInvoiceDetails(invoice: Invoice): string {
    if (!invoice.detalles || invoice.detalles.length === 0) {
      return '<p>No hay detalles disponibles para esta factura.</p>';
    }

    const rows = invoice.detalles.map(detalle => {
      const lineTotal = InvoicesService.calculateLineTotal(
        detalle.cantidad,
        detalle.precio_unitario,
        detalle.descuento_porcentaje,
        detalle.impuesto_porcentaje || detalle.porcentaje_iva || 0
      );

      return `
        <tr>
          <td>
            <div class="product-name">${detalle.descripcion_producto}</div>
            ${detalle.producto?.sku ? `<div class="product-sku">SKU: ${detalle.producto.sku}</div>` : ''}
          </td>
          <td class="text-center">${detalle.cantidad.toLocaleString()}</td>
          <td class="text-right">${InvoicesService.formatCurrency(detalle.precio_unitario)}</td>
          <td class="text-center">
            ${detalle.descuento_porcentaje}%
            ${lineTotal.descuento > 0 ? `<br><small>-${InvoicesService.formatCurrency(lineTotal.descuento)}</small>` : ''}
          </td>
          <td class="text-right">${InvoicesService.formatCurrency(lineTotal.subtotal - lineTotal.descuento)}</td>
          <td class="text-center">
            ${detalle.impuesto_porcentaje || detalle.porcentaje_iva || 0}%
            ${lineTotal.impuesto > 0 ? `<br><small>+${InvoicesService.formatCurrency(lineTotal.impuesto)}</small>` : ''}
          </td>
          <td class="text-right"><strong>${InvoicesService.formatCurrency(lineTotal.total)}</strong></td>
        </tr>
      `;
    }).join('');

    return `
      <table class="details-table">
        <thead>
          <tr>
            <th>Producto/Servicio</th>
            <th class="text-center">Cantidad</th>
            <th class="text-right">Precio Unit.</th>
            <th class="text-center">Descuento</th>
            <th class="text-right">Subtotal</th>
            <th class="text-center">Impuesto</th>
            <th class="text-right">Total</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>
    `;
  }

  /**
   * Genera la sección de totales
   */
  private static generateTotals(invoice: Invoice): string {
    return `
      <div class="totals-section">
        <table class="totals-table">
          <tr>
            <td class="total-label">Subtotal:</td>
            <td class="total-value">${InvoicesService.formatCurrency(invoice.subtotal)}</td>
          </tr>
          ${(invoice.total_descuentos || invoice.total_descuento || 0) > 0 ? `
            <tr>
              <td class="total-label" style="color: #27ae60;">Descuentos:</td>
              <td class="total-value" style="color: #27ae60;">
                -${InvoicesService.formatCurrency(invoice.total_descuentos || invoice.total_descuento || 0)}
              </td>
            </tr>
          ` : ''}
          ${invoice.total_impuestos > 0 ? `
            <tr>
              <td class="total-label">Impuestos:</td>
              <td class="total-value">+${InvoicesService.formatCurrency(invoice.total_impuestos)}</td>
            </tr>
          ` : ''}
          <tr class="grand-total">
            <td class="total-label">TOTAL A PAGAR:</td>
            <td class="total-value">${InvoicesService.formatCurrency(invoice.total || invoice.total_factura || 0)}</td>
          </tr>
        </table>
      </div>
    `;
  }

  /**
   * Genera el pie de página
   */
  private static generateFooter(options: PrintOptions): string {
    return `
      <div class="footer">
        <p>Gracias por su preferencia</p>
        <p>
          ${options.companyName} | ${options.companyPhone} | ${options.companyEmail}
        </p>
        <p style="font-size: 10px; margin-top: 10px;">
          Documento generado electrónicamente - ${new Date().toLocaleString('es-CO')}
        </p>
      </div>
    `;
  }

  /**
   * Genera un PDF de la factura (requiere biblioteca adicional)
   * Por ahora, simplemente usa la función de impresión del navegador
   */
  static async generatePDF(invoice: Invoice, options: PrintOptions = {}): Promise<void> {
    // Por ahora, usar la función de imprimir que permite "Guardar como PDF"
    await this.printInvoice(invoice, options);
  }
}

export default InvoicePrintUtils;