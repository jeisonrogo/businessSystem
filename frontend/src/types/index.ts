/**
 * Tipos y interfaces del Sistema de Gestión Empresarial
 */

// Tipos base
export interface BaseEntity {
  id: string;
  created_at: string;
}

// Usuario y Autenticación
export interface User extends BaseEntity {
  email: string;
  nombre: string;
  rol: UserRole;
  is_active: boolean;
}

export enum UserRole {
  ADMINISTRADOR = 'administrador',
  GERENTE_VENTAS = 'gerente_ventas',
  CONTADOR = 'contador',
  VENDEDOR = 'vendedor'
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Producto
export interface Product extends BaseEntity {
  sku: string;
  nombre: string;
  descripcion?: string;
  url_foto?: string;
  precio_base: number;
  precio_publico: number;
  stock: number;
  is_active: boolean;
}

export interface ProductCreate {
  sku: string;
  nombre: string;
  descripcion?: string;
  url_foto?: string;
  precio_base: number;
  precio_publico: number;
  stock?: number;
}

export interface ProductUpdate {
  nombre?: string;
  descripcion?: string;
  url_foto?: string;
  precio_base?: number;
  precio_publico?: number;
}

export interface ProductListResponse {
  items: Product[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}



// Cliente
export interface Client extends BaseEntity {
  tipo_documento: DocumentType;
  numero_documento: string;
  nombre_completo: string;
  nombre_comercial?: string;
  email?: string;
  telefono?: string;
  direccion?: string;
  tipo_cliente: ClientType;
  is_active: boolean;
}

export enum DocumentType {
  CC = 'CEDULA',
  NIT = 'NIT',
  CEDULA_EXTRANJERIA = 'CEDULA_EXTRANJERIA',
  PASAPORTE = 'PASAPORTE'
}

export enum ClientType {
  PERSONA_NATURAL = 'PERSONA_NATURAL',
  EMPRESA = 'EMPRESA'
}

// Factura
export interface Invoice extends BaseEntity {
  numero_factura: string;
  prefijo: string;
  cliente_id: string;
  tipo_factura: InvoiceType;
  estado: InvoiceStatus;
  fecha_emision: string;
  fecha_vencimiento?: string;
  subtotal: number;
  total_descuento: number;
  total_impuestos: number;
  total_factura: number;
  observaciones?: string;
  cliente?: Client;
  detalles?: InvoiceDetail[];
}

export interface InvoiceDetail extends BaseEntity {
  factura_id: string;
  producto_id: string;
  descripcion_producto: string;
  cantidad: number;
  precio_unitario: number;
  descuento_porcentaje: number;
  descuento_valor: number;
  impuesto_porcentaje: number;
  impuesto_valor: number;
  subtotal_linea: number;
  total_linea: number;
  producto?: Product;
}

export enum InvoiceType {
  VENTA = 'VENTA',
  SERVICIO = 'SERVICIO'
}

export enum InvoiceStatus {
  EMITIDA = 'EMITIDA',
  PAGADA = 'PAGADA',
  ANULADA = 'ANULADA'
}

// Contabilidad
export interface Account extends BaseEntity {
  codigo: string;
  nombre: string;
  tipo_cuenta: AccountType;
  cuenta_padre_id?: string;
  is_active: boolean;
  nombre_cuenta_padre?: string;
  tiene_subcuentas?: boolean;
}

export interface AccountCreate {
  codigo: string;
  nombre: string;
  tipo_cuenta: AccountType;
  cuenta_padre_id?: string;
}

export interface AccountUpdate {
  nombre?: string;
  tipo_cuenta?: AccountType;
  cuenta_padre_id?: string;
  is_active?: boolean;
}

export interface AccountListResponse {
  cuentas: Account[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface AccountHierarchy {
  plan_cuentas: Account[];
}

export interface MainAccountsResponse {
  cuentas: Account[];
  tipo_cuenta?: AccountType;
}

export interface SubAccountsResponse {
  subcuentas: Account[];
  cuenta_padre_id: string;
  total_subcuentas: number;
}

export interface SeedAccountsResponse {
  message: string;
  cuentas_creadas: number;
  cuentas_actualizadas: number;
}

export enum AccountType {
  ACTIVO = 'ACTIVO',
  PASIVO = 'PASIVO',
  PATRIMONIO = 'PATRIMONIO',
  INGRESO = 'INGRESO',
  EGRESO = 'EGRESO'
}

export interface AccountingEntry extends BaseEntity {
  numero_comprobante: string;
  fecha: string;
  descripcion: string;
  referencia?: string;
  total_debitos: number;
  total_creditos: number;
  is_balanced: boolean;
  created_by?: string;
  detalles: AccountingEntryDetail[];
}

export interface AccountingEntryDetail extends BaseEntity {
  asiento_id: string;
  cuenta_id: string;
  descripcion?: string;
  debito: number;
  credito: number;
  cuenta?: Account;
}

// ============================================================================
// INVENTORY TYPES - Tipos para el módulo de inventario
// ============================================================================

export enum MovementType {
  ENTRADA = 'entrada',
  SALIDA = 'salida',
  MERMA = 'merma',
  AJUSTE = 'ajuste'
}

export interface InventoryMovement extends BaseEntity {
  producto_id: string;
  tipo_movimiento: MovementType;
  cantidad: number;
  precio_unitario?: number;
  costo_unitario?: number;
  stock_anterior: number;
  stock_posterior: number;
  referencia?: string;
  observaciones?: string;
  created_by?: string;
  producto?: Product;
}

export interface InventoryMovementCreate {
  producto_id: string;
  tipo_movimiento: MovementType;
  cantidad: number;
  precio_unitario?: number;
  costo_unitario?: number;
  referencia?: string;
  observaciones?: string;
}

export interface InventoryMovementListResponse {
  movimientos: InventoryMovement[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface KardexEntry {
  fecha: string;
  tipo_movimiento: MovementType;
  cantidad: number;
  precio_unitario?: number;
  costo_unitario?: number;
  stock_anterior: number;
  stock_posterior: number;
  referencia?: string;
  observaciones?: string;
}

export interface KardexResponse {
  producto_id: string;
  movimientos: InventoryMovement[];
  stock_actual: number;
  costo_promedio_actual: string;
  valor_inventario: string;
  total_movimientos: number;
}

export interface InventorySummary {
  total_productos: number;
  valor_total_inventario: string;
  productos_sin_stock: number;
  productos_stock_bajo: number;
  ultimo_movimiento: string | null;
}

export interface InventoryStats {
  total_entradas_mes: number;
  total_salidas_mes: number;
  total_mermas_mes: number;
  valor_entradas_mes: string;
  valor_salidas_mes: string;
  valor_mermas_mes: string;
  productos_mas_movidos: Array<{
    producto_id: string;
    nombre: string;
    total_movimientos: number;
  }>;
}

export interface StockValidation {
  producto_id: string;
  cantidad_solicitada: number;
  stock_disponible: boolean;
  stock_actual: number;
  mensaje: string;
}

export interface InventoryMovementFilter {
  producto_id?: string;
  tipo_movimiento?: MovementType;
  fecha_desde?: string;
  fecha_hasta?: string;
  referencia?: string;
}

// Dashboard y Reportes
export interface DashboardOverview {
  total_productos: number;
  total_clientes: number;
  total_facturas: number;
  valor_inventario: number;
  ventas_mes_actual: number;
  facturas_pendientes: number;
  productos_bajo_stock: number;
  ingresos_mes_actual: number;
}

export interface SalesChartData {
  mes: string;
  ventas: number;
  cantidad_facturas: number;
}

// Respuestas de API comunes
export interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

// Parámetros de consulta comunes
export interface QueryParams {
  page?: number;
  limit?: number;
  search?: string;
  only_active?: boolean;
}

export interface DateRangeParams {
  fecha_inicio?: string;
  fecha_fin?: string;
}