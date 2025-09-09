/**
 * Tipos para el sistema Multi-Tenant
 * 
 * Define interfaces para tiendas, locales, stock por local,
 * transferencias y permisos granulares.
 */

// Importar tipos existentes del sistema para compatibilidad
import type { Product, User } from './index';

// ============================================================================
// TIPOS BASE MULTI-TENANT
// ============================================================================

export interface BaseMultiTenantEntity {
  id: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

// ============================================================================
// TIENDA (STORE)
// ============================================================================

export interface Tienda extends BaseMultiTenantEntity {
  codigo: string;
  nombre: string;
  descripcion?: string;
  dominio?: string;
  configuracion_fiscal: ConfiguracionFiscal;
  configuracion_facturacion: ConfiguracionFacturacion;
  direccion?: string;
  telefono?: string;
  email?: string;
  logo_url?: string;
  total_locales?: number;
}

export interface TiendaCreate {
  codigo: string;
  nombre: string;
  descripcion?: string;
  dominio?: string;
  direccion?: string;
  telefono?: string;
  email?: string;
  logo_url?: string;
  configuracion_fiscal?: Partial<ConfiguracionFiscal>;
  configuracion_facturacion?: Partial<ConfiguracionFacturacion>;
}

export interface TiendaUpdate {
  nombre?: string;
  descripcion?: string;
  dominio?: string;
  direccion?: string;
  telefono?: string;
  email?: string;
  logo_url?: string;
  is_active?: boolean;
  configuracion_fiscal?: Partial<ConfiguracionFiscal>;
  configuracion_facturacion?: Partial<ConfiguracionFacturacion>;
}

export interface ConfiguracionFiscal {
  regimen_tributario: string;
  responsabilidades_fiscales: string[];
  resolucion_facturacion?: string;
  fecha_resolucion?: string;
  numeracion_desde?: number;
  numeracion_hasta?: number;
}

export interface ConfiguracionFacturacion {
  consecutivo_facturas: number;
  prefijo_facturas: string;
  auto_numeracion: boolean;
  incluir_impuestos: boolean;
  porcentaje_iva_defecto: number;
  terminos_condiciones?: string;
  politica_descuentos?: string;
  metodos_pago_aceptados: string[];
}

// ============================================================================
// LOCAL (LOCATION)
// ============================================================================

export interface Local extends BaseMultiTenantEntity {
  tienda_id: string;
  codigo: string;
  nombre: string;
  descripcion?: string;
  tipo_local?: TipoLocal;
  direccion?: string;  // Dirección como string simple
  ciudad?: string;     // Ciudad como campo separado
  departamento?: string; // Departamento como campo separado
  codigo_postal?: string;
  telefono?: string;
  email?: string;
  configuracion?: ConfiguracionLocal;
  responsable_principal?: string;
  horario_operacion?: HorarioOperacion;
  total_productos?: number;
  valor_inventario?: number;
}

export interface LocalCreate {
  tienda_id: string;
  codigo: string;
  nombre: string;
  descripcion?: string;
  tipo_local: TipoLocal;
  direccion: DireccionCompleta;
  configuracion?: Partial<ConfiguracionLocal>;
  responsable_principal?: string;
  horario_operacion?: HorarioOperacion;
}

export interface LocalUpdate {
  nombre?: string;
  descripcion?: string;
  tipo_local?: TipoLocal;
  direccion?: Partial<DireccionCompleta>;
  configuracion?: Partial<ConfiguracionLocal>;
  responsable_principal?: string;
  horario_operacion?: Partial<HorarioOperacion>;
  is_active?: boolean;
}

export enum TipoLocal {
  SUCURSAL = 'SUCURSAL',
  ALMACEN = 'ALMACEN',
  SHOWROOM = 'SHOWROOM',
  VIRTUAL = 'VIRTUAL'
}

export interface DireccionCompleta {
  direccion_principal: string;
  ciudad: string;
  departamento: string;
  codigo_postal?: string;
  pais: string;
  coordenadas_gps?: string;
  referencias?: string;
}

export interface ConfiguracionLocal {
  permite_ventas: boolean;
  permite_transferencias: boolean;
  maneja_inventario: boolean;
  requiere_autorizacion_descuentos: boolean;
  limite_descuento_maximo: number;
  acepta_devoluciones: boolean;
  genera_reportes_automaticos: boolean;
  notificaciones_stock_bajo: boolean;
  stock_minimo_default: number;
}

export interface HorarioOperacion {
  lunes: HorarioDia;
  martes: HorarioDia;
  miercoles: HorarioDia;
  jueves: HorarioDia;
  viernes: HorarioDia;
  sabado: HorarioDia;
  domingo: HorarioDia;
  dias_festivos?: string[];
  horario_especial?: HorarioEspecial[];
}

export interface HorarioDia {
  abierto: boolean;
  hora_apertura?: string;
  hora_cierre?: string;
  descanso_inicio?: string;
  descanso_fin?: string;
}

export interface HorarioEspecial {
  fecha: string;
  abierto: boolean;
  hora_apertura?: string;
  hora_cierre?: string;
  descripcion?: string;
}

// ============================================================================
// STOCK POR LOCAL
// ============================================================================

export interface StockLocal extends BaseMultiTenantEntity {
  local_id: string;
  producto_id: string;
  cantidad: number;
  stock_minimo: number;
  stock_maximo?: number;
  costo_promedio: number;
  ultima_entrada?: string;
  ultima_salida?: string;
  ubicacion_fisica?: string;
  lote?: string;
  fecha_vencimiento?: string;
  producto?: Product;
  local?: Local;
}

export interface StockLocalUpdate {
  cantidad?: number;
  stock_minimo?: number;
  stock_maximo?: number;
  costo_promedio?: number;
  ubicacion_fisica?: string;
  lote?: string;
  fecha_vencimiento?: string;
}

export interface StockLocalMovimiento {
  local_id: string;
  producto_id: string;
  tipo_movimiento: TipoMovimientoStock;
  cantidad: number;
  costo_unitario?: number;
  referencia?: string;
  observaciones?: string;
}

export enum TipoMovimientoStock {
  ENTRADA = 'ENTRADA',
  SALIDA = 'SALIDA',
  AJUSTE_POSITIVO = 'AJUSTE_POSITIVO',
  AJUSTE_NEGATIVO = 'AJUSTE_NEGATIVO',
  TRANSFERENCIA_ENTRADA = 'TRANSFERENCIA_ENTRADA',
  TRANSFERENCIA_SALIDA = 'TRANSFERENCIA_SALIDA'
}

// ============================================================================
// TRANSFERENCIAS ENTRE LOCALES
// ============================================================================

export interface TransferenciaInventario extends BaseMultiTenantEntity {
  codigo_transferencia: string;
  local_origen_id: string;
  local_destino_id: string;
  producto_id: string;
  cantidad: number;
  costo_unitario: number;
  estado: EstadoTransferencia;
  fecha_solicitud: string;
  fecha_envio?: string;
  fecha_recepcion?: string;
  observaciones_origen?: string;
  observaciones_destino?: string;
  solicitado_por?: string;
  enviado_por?: string;
  recibido_por?: string;
  producto?: Product;
  local_origen?: Local;
  local_destino?: Local;
}

export interface TransferenciaCreate {
  local_origen_id: string;
  local_destino_id: string;
  producto_id: string;
  cantidad: number;
  costo_unitario?: number;
  observaciones_origen?: string;
}

export interface TransferenciaUpdate {
  estado?: EstadoTransferencia;
  observaciones_origen?: string;
  observaciones_destino?: string;
}

export enum EstadoTransferencia {
  PENDIENTE = 'PENDIENTE',
  ENVIADA = 'ENVIADA',
  RECIBIDA = 'RECIBIDA',
  CANCELADA = 'CANCELADA'
}

// ============================================================================
// PERMISOS GRANULARES USUARIO-LOCAL
// ============================================================================

export interface UsuarioLocal extends BaseMultiTenantEntity {
  user_id: string;
  local_id: string;
  puede_vender: boolean;
  puede_ver_stock: boolean;
  puede_transferir: boolean;
  es_responsable: boolean;
  puede_modificar_precios: boolean;
  puede_aplicar_descuentos: boolean;
  puede_ver_reportes: boolean;
  puede_gestionar_usuarios: boolean;
  limite_descuento_porcentaje?: number;
  limite_credito_monto?: number;
  asignado_por?: string;
  fecha_asignacion: string;
  user?: User;
  local?: Local;
}

export interface UsuarioLocalCreate {
  user_id: string;
  local_id: string;
  puede_vender?: boolean;
  puede_ver_stock?: boolean;
  puede_transferir?: boolean;
  es_responsable?: boolean;
  puede_modificar_precios?: boolean;
  puede_aplicar_descuentos?: boolean;
  puede_ver_reportes?: boolean;
  puede_gestionar_usuarios?: boolean;
  limite_descuento_porcentaje?: number;
  limite_credito_monto?: number;
}

export interface UsuarioLocalUpdate {
  puede_vender?: boolean;
  puede_ver_stock?: boolean;
  puede_transferir?: boolean;
  es_responsable?: boolean;
  puede_modificar_precios?: boolean;
  puede_aplicar_descuentos?: boolean;
  puede_ver_reportes?: boolean;
  puede_gestionar_usuarios?: boolean;
  limite_descuento_porcentaje?: number;
  limite_credito_monto?: number;
  is_active?: boolean;
}

export enum PerfilPermiso {
  VENDEDOR = 'VENDEDOR',
  RESPONSABLE_LOCAL = 'RESPONSABLE_LOCAL',
  GERENTE_VENTAS = 'GERENTE_VENTAS',
  CONTADOR = 'CONTADOR',
  ADMINISTRADOR = 'ADMINISTRADOR'
}

// ============================================================================
// CONTEXTO DE TENANT
// ============================================================================

export interface TenantContext {
  tienda_id: string;
  tienda_codigo: string;
  tienda_nombre: string;
  local_id?: string;
  local_codigo?: string;
  local_nombre?: string;
  tiene_contexto_local: boolean;
  permisos_disponibles: string[];
}

export enum TipoContextoTenant {
  SOLO_TIENDA = 'SOLO_TIENDA',
  CON_LOCAL = 'CON_LOCAL'
}

// ============================================================================
// RESPUESTAS DE API MULTI-TENANT
// ============================================================================

export interface TiendaListResponse {
  tiendas: Tienda[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface LocalListResponse {
  locales: Local[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface StockLocalListResponse {
  stock_items: StockLocal[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface TransferenciaListResponse {
  transferencias: TransferenciaInventario[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface UsuarioLocalListResponse {
  asignaciones: UsuarioLocal[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

// ============================================================================
// ESTADÍSTICAS Y REPORTES MULTI-TENANT
// ============================================================================

export interface EstadisticasTienda {
  tienda_id: string;
  total_locales: number;
  locales_activos: number;
  total_productos_sistema: number;
  valor_inventario_total: number;
  transferencias_pendientes: number;
  usuarios_con_acceso: number;
  ventas_mes_actual: number;
  locales_por_tipo: { [key in TipoLocal]: number };
}

export interface EstadisticasLocal {
  local_id: string;
  total_productos: number;
  productos_con_stock: number;
  productos_sin_stock: number;
  valor_inventario: number;
  transferencias_enviadas: number;
  transferencias_recibidas: number;
  usuarios_asignados: number;
  ventas_mes: number;
  rotacion_inventario: number;
}

export interface ResumenTransferencias {
  transferencias_pendientes: number;
  transferencias_en_transito: number;
  transferencias_completadas_mes: number;
  valor_transferido_mes: number;
  locales_mas_solicitan: Array<{
    local_id: string;
    local_nombre: string;
    total_solicitudes: number;
  }>;
  productos_mas_transferidos: Array<{
    producto_id: string;
    producto_nombre: string;
    cantidad_transferida: number;
  }>;
}

// ============================================================================
// FILTROS Y CONSULTAS
// ============================================================================

export interface FiltroMultiTenant {
  tienda_id?: string;
  local_id?: string;
  incluir_inactivos?: boolean;
  fecha_desde?: string;
  fecha_hasta?: string;
}

export interface FiltroTransferencias extends FiltroMultiTenant {
  estado?: EstadoTransferencia;
  producto_id?: string;
  local_origen_id?: string;
  local_destino_id?: string;
}

export interface FiltroStockLocal extends FiltroMultiTenant {
  producto_id?: string;
  solo_con_stock?: boolean;
  solo_stock_bajo?: boolean;
  buscar_producto?: string;
}

export interface FiltroPermisos extends FiltroMultiTenant {
  user_id?: string;
  es_responsable?: boolean;
  puede_vender?: boolean;
}

// ============================================================================
// TIPOS DE UTILIDAD
// ============================================================================

export interface CambiarContextoRequest {
  local_id?: string;
}

export interface ValidacionStock {
  producto_id: string;
  local_id: string;
  cantidad_solicitada: number;
  stock_disponible: boolean;
  stock_actual: number;
  puede_realizar_venta: boolean;
  requiere_transferencia: boolean;
  locales_con_stock?: Array<{
    local_id: string;
    local_nombre: string;
    stock_disponible: number;
  }>;
}

export interface SugerenciaTransferencia {
  producto_id: string;
  local_destino_id: string;
  cantidad_sugerida: number;
  locales_origen_disponibles: Array<{
    local_id: string;
    local_nombre: string;
    stock_disponible: number;
    costo_transferencia_estimado: number;
  }>;
}

export type { Product, User } from './index';