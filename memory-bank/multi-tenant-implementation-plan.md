# Plan de Implementación Multi-Tenant: Tiendas y Locales

## 🎯 Resumen Ejecutivo

### Necesidad del Cliente
El cliente requiere transformar el sistema actual (mono-tenant) a una arquitectura **multi-tenant** de dos niveles:
- **Nivel 1 - Tiendas**: Diferentes líneas de negocio (zapatos, vidrios, etc.)
- **Nivel 2 - Locales**: Múltiples puntos de venta dentro de cada tienda

### Objetivo
Permitir gestión independiente de inventario, ventas, facturas y contabilidad por local, con capacidad de administración consolidada por tienda.

---

## 📊 Análisis Costo-Beneficio

### 🏆 Beneficios

#### **Beneficios de Negocio**
- **Escalabilidad**: Crecimiento orgánico agregando tiendas/locales
- **Segregación de Datos**: Claridad contable y operacional por local
- **Gestión Centralizada**: Control desde un solo sistema
- **Análisis Granular**: KPIs por local, consolidados por tienda
- **Flexibilidad Operativa**: Diferentes estrategias por tipo de tienda

#### **Beneficios Técnicos**
- **Reutilización**: Una sola aplicación para múltiples negocios
- **Mantenimiento Centralizado**: Updates únicos para todos los tenants
- **Consistencia**: UX/UI uniforme across todas las tiendas
- **Seguridad**: Aislamiento de datos garantizado por diseño

### 💰 Costos Estimados

#### **Desarrollo (220-280 horas)**
- **Backend Modifications**: 120-150 horas
- **Frontend Modifications**: 80-100 horas  
- **Testing & QA**: 20-30 horas

#### **Esfuerzo por Componente Actualizado**

| Componente | Horas | Complejidad | Descripción |
|------------|-------|-------------|-------------|
| **Modelo de Datos Multi-Tenant** | 24-30 | Alta | Migraciones, stock por local, transferencias |
| **Capa de Contexto y Permisos** | 32-40 | Alta | Context + sistema de permisos granular |
| **APIs Backend Existentes** | 40-50 | Media | Actualizar 76 endpoints + filtros tenant |
| **APIs Nuevas (Transferencias)** | 16-20 | Media | Sistema completo de transferencias |
| **APIs Nuevas (Multi-Stock)** | 12-16 | Media | Gestión de stock multi-local |
| **Autenticación y Permisos** | 12-16 | Media | JWT + validación permisos por local |
| **Frontend Context Avanzado** | 24-30 | Media | React Context + permisos + navegación |
| **UI/UX Multi-Level** | 32-40 | Media | Dashboards, transferencias, selectors |
| **Sistema de Transferencias UI** | 16-20 | Media | Interfaz completa de transferencias |
| **Data Migration Compleja** | 12-16 | Alta | Migración stock + permisos + datos existentes |
| **Testing Integral** | 24-30 | Media | Unit + Integration + E2E + Security tests |
| **Documentation Completa** | 12-16 | Baja | Guías técnicas y de usuario |

#### **ROI Estimado Actualizado**
- **Costo Total**: $11,000 - $14,000 USD (280 horas @ $40-50/hora)
- **Beneficio Anual**: $20,000 - $35,000 USD (mayor por funcionalidades adicionales)
- **Break-even**: 6-10 meses
- **ROI a 2 años**: 200-400%

#### **Justificación del Costo Adicional**
El incremento de 80 horas (+40%) se justifica por:
- **Sistema de Transferencias**: Funcionalidad crítica para múltiples locales
- **Gestión de Permisos Granular**: Seguridad por local esencial para el negocio
- **Stock Multi-Local**: Complejidad adicional vs stock simple por tienda
- **UI/UX Avanzada**: Dashboards multi-nivel y navegación contextual

---

## 🏗️ Diseño de Arquitectura Multi-Tenant

### **Estrategia Elegida: Row-Level Security (RLS)**

**Justificación:**
- Mantiene rendimiento óptimo (single database)
- Aislamiento garantizado por diseño
- Menor complejidad operacional
- Compatible con arquitectura existente

### **Modelo de Datos Multi-Tenant**

#### **Entidades Principales**

```sql
-- 1. TIENDAS (Nivel Superior - Independientes)
CREATE TABLE tiendas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo VARCHAR(20) UNIQUE NOT NULL,        -- "ZAPATOS", "VIDRIOS"
    nombre VARCHAR(255) NOT NULL,              -- "Calzado Premium", "Vidrios San José"
    descripcion TEXT,
    dominio VARCHAR(100) UNIQUE,               -- "zapatos.miempresa.com"
    configuracion JSONB,                       -- Settings específicos
    -- Numeración consecutiva por tienda
    consecutivo_facturas INTEGER DEFAULT 1,   -- Facturación consecutiva por tienda
    prefijo_facturas VARCHAR(10) DEFAULT 'F', -- Prefijo para facturas
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 2. LOCALES (Puntos de Venta por Tienda)
CREATE TABLE locales (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tienda_id UUID NOT NULL REFERENCES tiendas(id),
    codigo VARCHAR(20) NOT NULL,               -- "LOCAL001", "CENTRO", "NORTE"
    nombre VARCHAR(255) NOT NULL,              -- "Local Centro", "Local Norte"
    direccion TEXT,
    telefono VARCHAR(20),
    configuracion JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(tienda_id, codigo)
);

-- 3. STOCK POR LOCAL (Inventario Independiente)
CREATE TABLE stock_por_local (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id UUID NOT NULL REFERENCES products(id),
    local_id UUID NOT NULL REFERENCES locales(id),
    cantidad INTEGER NOT NULL DEFAULT 0,
    stock_minimo INTEGER DEFAULT 0,
    stock_maximo INTEGER,
    costo_promedio DECIMAL(10,2) DEFAULT 0,   -- Costo promedio ponderado por local
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(producto_id, local_id)
);

-- 4. TRANSFERENCIAS ENTRE LOCALES
CREATE TABLE transferencias_inventario (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    numero_transferencia VARCHAR(50) NOT NULL, -- TRF-001, TRF-002
    producto_id UUID NOT NULL REFERENCES products(id),
    local_origen_id UUID NOT NULL REFERENCES locales(id),
    local_destino_id UUID NOT NULL REFERENCES locales(id),
    cantidad_solicitada INTEGER NOT NULL,
    cantidad_enviada INTEGER DEFAULT 0,
    cantidad_recibida INTEGER DEFAULT 0,
    estado VARCHAR(20) DEFAULT 'PENDIENTE',    -- PENDIENTE, ENVIADO, RECIBIDO, CANCELADO
    observaciones TEXT,
    usuario_solicita_id UUID REFERENCES users(id),
    usuario_envia_id UUID REFERENCES users(id),
    usuario_recibe_id UUID REFERENCES users(id),
    fecha_solicitud TIMESTAMP WITH TIME ZONE DEFAULT now(),
    fecha_envio TIMESTAMP WITH TIME ZONE,
    fecha_recepcion TIMESTAMP WITH TIME ZONE,
    CONSTRAINT transferencia_misma_tienda CHECK (
        (SELECT tienda_id FROM locales WHERE id = local_origen_id) = 
        (SELECT tienda_id FROM locales WHERE id = local_destino_id)
    )
);

-- 5. PERMISOS USUARIO-LOCAL
CREATE TABLE usuario_locales (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    local_id UUID NOT NULL REFERENCES locales(id),
    puede_vender BOOLEAN DEFAULT TRUE,         -- Puede crear facturas en este local
    puede_ver_stock BOOLEAN DEFAULT TRUE,     -- Puede ver inventario del local
    puede_transferir BOOLEAN DEFAULT FALSE,   -- Puede crear transferencias
    es_responsable BOOLEAN DEFAULT FALSE,     -- Es responsable del local
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(user_id, local_id)
);
```

#### **Actualización Tablas Existentes**

```sql
-- USUARIOS (Pertenecen a una tienda)
ALTER TABLE users ADD COLUMN tienda_id UUID REFERENCES tiendas(id);
ALTER TABLE users ADD COLUMN local_principal_id UUID REFERENCES locales(id); -- Local por defecto

-- PRODUCTOS (Catálogo por tienda, stock por local)
ALTER TABLE products ADD COLUMN tienda_id UUID REFERENCES tiendas(id);
-- Eliminar campo stock de products (ahora en stock_por_local)
ALTER TABLE products DROP COLUMN IF EXISTS stock;

-- CLIENTES (Globales por tienda, con local de origen)
ALTER TABLE clientes ADD COLUMN tienda_id UUID REFERENCES tiendas(id);
ALTER TABLE clientes ADD COLUMN local_origen_id UUID REFERENCES locales(id); -- Donde fue creado

-- FACTURAS (Por local, numeración por tienda)
ALTER TABLE facturas ADD COLUMN tienda_id UUID REFERENCES tiendas(id);
ALTER TABLE facturas ADD COLUMN local_id UUID REFERENCES locales(id);
ALTER TABLE facturas ADD COLUMN numero_tienda INTEGER; -- Numeración consecutiva por tienda

-- MOVIMIENTOS INVENTARIO (Por local específico)
ALTER TABLE movimientos_inventario ADD COLUMN local_id UUID REFERENCES locales(id);
ALTER TABLE movimientos_inventario ADD COLUMN transferencia_id UUID REFERENCES transferencias_inventario(id);

-- CONTABILIDAD (Por local, consolidación por tienda)
ALTER TABLE asientos_contables ADD COLUMN tienda_id UUID REFERENCES tiendas(id);
ALTER TABLE asientos_contables ADD COLUMN local_id UUID REFERENCES locales(id);
ALTER TABLE cuentas_contables ADD COLUMN tienda_id UUID REFERENCES tiendas(id);
```

#### **Índices para Performance**

```sql
-- Índices críticos para queries multi-tenant
CREATE INDEX idx_stock_local_producto ON stock_por_local(local_id, producto_id);
CREATE INDEX idx_facturas_tienda_local ON facturas(tienda_id, local_id);
CREATE INDEX idx_movimientos_local ON movimientos_inventario(local_id);
CREATE INDEX idx_transferencias_estados ON transferencias_inventario(estado, local_origen_id);
CREATE INDEX idx_usuarios_tienda ON users(tienda_id);
CREATE INDEX idx_productos_tienda ON products(tienda_id);
CREATE INDEX idx_clientes_tienda ON clientes(tienda_id);
CREATE INDEX idx_asientos_tienda_local ON asientos_contables(tienda_id, local_id);
```

### **Context Propagation Pattern**

#### **Backend: Tenant Context Extendido**

```python
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID

class PermisoLocal(str, Enum):
    VER_STOCK = "ver_stock"
    VENDER = "vender" 
    TRANSFERIR = "transferir"
    RESPONSABLE = "responsable"

class TenantContext:
    def __init__(
        self, 
        tienda_id: UUID, 
        local_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        permisos_locales: Optional[Dict[UUID, List[PermisoLocal]]] = None
    ):
        self.tienda_id = tienda_id
        self.local_id = local_id
        self.user_id = user_id
        self.permisos_locales = permisos_locales or {}
    
    def get_filters(self) -> Dict[str, Any]:
        """Filtros base para queries multi-tenant"""
        filters = {"tienda_id": self.tienda_id}
        if self.local_id:
            filters["local_id"] = self.local_id
        return filters
    
    def puede_vender_en_local(self, local_id: UUID) -> bool:
        """Verifica si el usuario puede vender en el local específico"""
        return PermisoLocal.VENDER in self.permisos_locales.get(local_id, [])
    
    def puede_ver_stock_local(self, local_id: UUID) -> bool:
        """Verifica si puede ver stock del local"""
        return PermisoLocal.VER_STOCK in self.permisos_locales.get(local_id, [])
    
    def puede_transferir_desde_local(self, local_id: UUID) -> bool:
        """Verifica si puede crear transferencias desde el local"""
        return PermisoLocal.TRANSFERIR in self.permisos_locales.get(local_id, [])
    
    def get_locales_venta_permitidos(self) -> List[UUID]:
        """Retorna locales donde el usuario puede vender"""
        return [
            local_id for local_id, permisos in self.permisos_locales.items()
            if PermisoLocal.VENDER in permisos
        ]

# Dependency Injection Mejorado
async def get_tenant_context(
    tienda_codigo: str = Header(alias="X-Tenant-Store"),
    local_codigo: Optional[str] = Header(alias="X-Tenant-Location", default=None),
    current_user: User = Depends(get_current_user),
    tenant_service: ITenantService = Depends(get_tenant_service)
) -> TenantContext:
    """
    Resuelve el contexto del tenant y valida permisos
    """
    # 1. Resolver tienda
    tienda = await tenant_service.get_tienda_by_codigo(tienda_codigo)
    if not tienda or not await tenant_service.user_belongs_to_tienda(current_user.id, tienda.id):
        raise HTTPException(status_code=403, detail="Acceso denegado a la tienda")
    
    # 2. Resolver local (opcional)
    local_id = None
    if local_codigo:
        local = await tenant_service.get_local_by_codigo(tienda.id, local_codigo)
        if not local:
            raise HTTPException(status_code=404, detail="Local no encontrado")
        local_id = local.id
    
    # 3. Obtener permisos del usuario en todos los locales de la tienda
    permisos_locales = await tenant_service.get_user_permissions_by_tienda(
        current_user.id, tienda.id
    )
    
    return TenantContext(
        tienda_id=tienda.id,
        local_id=local_id,
        user_id=current_user.id,
        permisos_locales=permisos_locales
    )

# Decorador para validar permisos específicos
def require_local_permission(permission: PermisoLocal):
    def decorator(func):
        async def wrapper(*args, tenant_ctx: TenantContext = Depends(get_tenant_context), **kwargs):
            if not tenant_ctx.local_id:
                raise HTTPException(status_code=400, detail="Se requiere contexto de local")
            
            has_permission = False
            if permission == PermisoLocal.VENDER:
                has_permission = tenant_ctx.puede_vender_en_local(tenant_ctx.local_id)
            elif permission == PermisoLocal.VER_STOCK:
                has_permission = tenant_ctx.puede_ver_stock_local(tenant_ctx.local_id)
            elif permission == PermisoLocal.TRANSFERIR:
                has_permission = tenant_ctx.puede_transferir_desde_local(tenant_ctx.local_id)
                
            if not has_permission:
                raise HTTPException(status_code=403, detail=f"Sin permisos: {permission}")
            
            return await func(*args, tenant_ctx=tenant_ctx, **kwargs)
        return wrapper
    return decorator
```

#### **Frontend: React Context Extendido**

```typescript
interface PermisoLocal {
  ver_stock: boolean;
  vender: boolean;
  transferir: boolean;
  responsable: boolean;
}

interface Local {
  id: string;
  codigo: string;
  nombre: string;
  direccion?: string;
  telefono?: string;
  permisos: PermisoLocal; // Permisos del usuario actual en este local
}

interface Tienda {
  id: string;
  codigo: string;
  nombre: string;
  descripcion?: string;
  consecutivo_facturas: number;
  prefijo_facturas: string;
}

interface TenantContextValue {
  // Estado actual
  currentTienda: Tienda | null;
  currentLocal: Local | null;
  
  // Datos disponibles
  availableLocales: Local[];
  localesVentaPermitidos: Local[]; // Solo locales donde puede vender
  
  // Acciones
  switchLocal: (localId: string) => Promise<void>;
  switchTienda: (tiendaId: string) => Promise<void>;
  
  // Validaciones de permisos
  puedeVenderEnLocal: (localId: string) => boolean;
  puedeVerStockLocal: (localId: string) => boolean;
  puedeTransferirDesdeLocal: (localId: string) => boolean;
  
  // Estado de carga
  isLoading: boolean;
  error: string | null;
}

const TenantContext = createContext<TenantContextValue | undefined>(undefined);

// Hook personalizado con validaciones
export const useTenant = () => {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error('useTenant debe usarse dentro de TenantProvider');
  }
  return context;
};

// Hook para requerir contexto específico
export const useRequireLocal = () => {
  const { currentLocal } = useTenant();
  if (!currentLocal) {
    throw new Error('Esta operación requiere seleccionar un local');
  }
  return currentLocal;
};
```

---

## 📋 Plan de Trabajo Detallado

### **FASE 1: Fundación Multi-Tenant (40-50 horas)**

#### **1.1. Diseño de Datos y Migraciones (16-20 horas)**

**Entregables:**
- ✅ **Nuevas entidades**: `Tienda`, `Local` en domain models
- ✅ **Migraciones Alembic**: Creación de tablas + actualización existentes
- ✅ **Data seeding**: Script para convertir datos actuales a estructura multi-tenant
- ✅ **Constraints**: Índices, foreign keys, unique constraints

**Archivos a crear/modificar:**
```
backend/app/domain/models/
├── tienda.py                    # NEW - Entidad Tienda
├── local.py                     # NEW - Entidad Local  
├── tenant_context.py            # NEW - Context de tenant
└── [existing models]            # MODIFY - Agregar campos tienda_id/local_id

backend/alembic/versions/
└── xxx_add_multi_tenant_support.py   # NEW - Migración principal

backend/scripts/
└── migrate_to_multi_tenant.py   # NEW - Script de migración de datos
```

**Tareas específicas:**
1. **Definir modelos**: Tienda, Local con validaciones
2. **Actualizar modelos existentes**: Agregar relaciones multi-tenant
3. **Crear migración**: Estructura completa de BD
4. **Script de migración**: Datos existentes → primera tienda/local
5. **Validar integridad**: Constraints y relaciones correctas

#### **1.2. Capa de Contexto Backend (24-30 horas)**

**Entregables:**
- ✅ **Context Manager**: Gestión de tenant context en aplicación
- ✅ **Repository Updates**: Todos los repositories con filtros tenant
- ✅ **Dependency Injection**: Inyección automática de tenant context
- ✅ **Middleware**: Header parsing y validación de tenant

**Archivos a crear/modificar:**
```
backend/app/application/services/
├── tenant_context_service.py     # NEW - Gestión de contexto
├── i_tienda_repository.py        # NEW - Repositorio tiendas
├── i_local_repository.py         # NEW - Repositorio locales
└── [all existing repositories]   # MODIFY - Agregar filtros tenant

backend/app/infrastructure/
├── middleware/
│   └── tenant_middleware.py      # NEW - Middleware multi-tenant
└── repositories/
    ├── tienda_repository.py      # NEW
    ├── local_repository.py       # NEW
    └── [existing repositories]   # MODIFY - Implementar filtros
```

**Tareas específicas:**
1. **Context Service**: Gestión de tienda/local activo
2. **Repository Pattern**: Filtros automáticos en queries
3. **Middleware HTTP**: Headers X-Tenant-Store, X-Tenant-Location
4. **Validation**: Permisos de usuario por tienda/local
5. **Error Handling**: Errores específicos de tenant

### **FASE 2: APIs Multi-Tenant (32-40 horas)**

#### **2.1. Endpoints Tiendas y Locales (8-12 horas)**

**Entregables:**
- ✅ **CRUD Tiendas**: Gestión completa de tiendas
- ✅ **CRUD Locales**: Gestión de locales por tienda  
- ✅ **Endpoints de contexto**: Switching y validación

**Archivos a crear:**
```
backend/app/api/v1/endpoints/
├── tiendas.py                    # NEW - Endpoints tiendas
├── locales.py                    # NEW - Endpoints locales
└── tenant_context.py             # NEW - Context switching

backend/app/application/use_cases/
├── tienda_use_cases.py           # NEW - Lógica de negocio tiendas
└── local_use_cases.py            # NEW - Lógica de negocio locales
```

**APIs a implementar:**

#### **Gestión de Tiendas y Locales**
- `GET /api/v1/tiendas/` - Listar tiendas del usuario
- `POST /api/v1/tiendas/` - Crear nueva tienda
- `GET /api/v1/tiendas/{id}` - Obtener detalles de tienda
- `PUT /api/v1/tiendas/{id}` - Actualizar tienda
- `GET /api/v1/tiendas/{id}/locales/` - Locales de una tienda
- `POST /api/v1/locales/` - Crear nuevo local
- `PUT /api/v1/locales/{id}` - Actualizar local
- `GET /api/v1/locales/{id}/permisos/` - Permisos de usuarios en el local
- `PUT /api/v1/locales/{id}/permisos/` - Actualizar permisos de usuario

#### **Gestión de Stock Multi-Local**
- `GET /api/v1/stock/local/{local_id}` - Stock de productos por local
- `GET /api/v1/stock/producto/{producto_id}` - Stock de un producto en todos los locales
- `PUT /api/v1/stock/local/{local_id}/producto/{producto_id}` - Actualizar stock específico
- `GET /api/v1/stock/consolidado/tienda/` - Stock consolidado por tienda

#### **Sistema de Transferencias**
- `GET /api/v1/transferencias/` - Listar transferencias (filtros por estado, local)
- `POST /api/v1/transferencias/` - Crear nueva transferencia
- `GET /api/v1/transferencias/{id}` - Detalles de transferencia específica
- `PUT /api/v1/transferencias/{id}/enviar` - Marcar transferencia como enviada
- `PUT /api/v1/transferencias/{id}/recibir` - Confirmar recepción de transferencia
- `PUT /api/v1/transferencias/{id}/cancelar` - Cancelar transferencia
- `GET /api/v1/transferencias/pendientes/local/{local_id}` - Transferencias pendientes por local

#### **Contexto y Navegación**
- `PUT /api/v1/context/` - Cambiar contexto activo (tienda/local)
- `GET /api/v1/context/permisos/` - Obtener permisos del usuario en contexto actual
- `GET /api/v1/context/locales-disponibles/` - Locales disponibles para el usuario

#### **2.2. Actualización APIs Existentes (24-28 horas)**

**Entregables:**
- ✅ **76 endpoints existentes** actualizados con filtros tenant
- ✅ **Backward compatibility** mantenida
- ✅ **Testing** de todos los endpoints modificados

**Endpoints por módulo a actualizar:**

#### **Productos (13 endpoints + nuevos)**
- **Cambio principal**: Stock separado por local, catálogo por tienda
- `GET /api/v1/products/` - Filtrar por tienda, mostrar stock por local actual
- `POST /api/v1/products/` - Crear producto para tienda, inicializar stock en locales
- `GET /api/v1/products/{id}/stock-locales/` - **NUEVO** - Ver stock en todos los locales
- `PUT /api/v1/products/{id}/distribuir-stock/` - **NUEVO** - Distribuir stock inicial

#### **Inventario (6 endpoints + transferencias)**
- **Cambio principal**: Movimientos por local específico + transferencias entre locales
- `GET /api/v1/inventario/movimientos/` - Filtrar por local o consolidado por tienda
- `POST /api/v1/inventario/movimientos/` - Requerir local_id obligatorio
- `GET /api/v1/inventario/kardex/{producto_id}` - Kardex por local o consolidado
- **NUEVOS**: Toda la gestión de transferencias (7 endpoints)

#### **Facturas (15 endpoints)**
- **Cambio principal**: Ventas por local, numeración consecutiva por tienda
- `GET /api/v1/facturas/` - Filtrar por local, mostrar consolidado por tienda
- `POST /api/v1/facturas/` - Validar stock en local específico, numeración por tienda
- `GET /api/v1/facturas/consecutivo/siguiente/` - **NUEVO** - Siguiente número por tienda
- **Regla**: Solo puede vender productos del local actual o con stock disponible

#### **Clientes (11 endpoints)**
- **Cambio principal**: Clientes globales por tienda, con local de origen
- `GET /api/v1/clientes/` - Clientes de toda la tienda, indicar local de origen
- `POST /api/v1/clientes/` - Asignar local de origen automáticamente
- `GET /api/v1/clientes/{id}/compras-por-local/` - **NUEVO** - Historial por local

#### **Contabilidad (18 endpoints)**
- **Cambio principal**: Asientos por local, consolidación por tienda
- `GET /api/v1/contabilidad/asientos/` - Filtrar por local o consolidado
- `POST /api/v1/contabilidad/asientos/` - Incluir contexto de local
- `GET /api/v1/contabilidad/balances/` - Balance por local o consolidado por tienda
- `GET /api/v1/contabilidad/estados-financieros/` - **MEJORADO** - Multi-nivel

#### **Dashboard (15 endpoints + analytics multi-nivel)**
- **Cambio principal**: Métricas por local + consolidadas por tienda
- `GET /api/v1/dashboard/resumen/` - Cambiar según contexto (local vs tienda)
- `GET /api/v1/dashboard/ventas-por-local/` - **NUEVO** - Comparativa entre locales
- `GET /api/v1/dashboard/productos-mas-vendidos/` - Por local o consolidado
- `GET /api/v1/dashboard/transferencias-pendientes/` - **NUEVO** - Estado transferencias
- `GET /api/v1/dashboard/alertas-stock/` - **MEJORADO** - Alertas por local

**Patrón de modificación estándar:**
```python
# Antes
@router.get("/products/")
async def list_products(
    page: int = 1,
    limit: int = 20,
    repo: IProductRepository = Depends(get_product_repository)
):
    return repo.get_all(skip=(page-1)*limit, limit=limit)

# Después  
@router.get("/products/")
async def list_products(
    page: int = 1, 
    limit: int = 20,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    repo: IProductRepository = Depends(get_product_repository)
):
    return repo.get_all_by_tenant(
        skip=(page-1)*limit, 
        limit=limit,
        tenant_ctx=tenant_ctx
    )
```

### **FASE 3: Frontend Multi-Tenant (60-80 horas)**

#### **3.1. Contexto y Navegación (20-25 horas)**

**Entregables:**
- ✅ **Tenant Context Provider**: Gestión de estado tienda/local
- ✅ **URL Strategy**: Rutas que incluyen tenant context  
- ✅ **Tenant Selector**: UI para cambio de tienda/local
- ✅ **Breadcrumbs**: Navegación contextual

**Archivos a crear/modificar:**
```
frontend/src/
├── context/
│   ├── TenantContext.tsx         # NEW - Context multi-tenant
│   └── TenantProvider.tsx        # NEW - Provider con estado
├── hooks/
│   ├── useTenant.ts              # NEW - Hook para contexto
│   └── useTenantNavigation.ts    # NEW - Navegación tenant-aware
├── components/
│   ├── tenant/
│   │   ├── TenantSelector.tsx    # NEW - Selector tienda/local
│   │   ├── TenantBreadcrumb.tsx  # NEW - Breadcrumb contextual  
│   │   └── TenantGuard.tsx       # NEW - Route guard
│   └── layout/
│       └── Layout.tsx            # MODIFY - Integrar tenant selector
```

**Funcionalidades clave:**
1. **Context Provider**: Estado global de tienda/local actual
2. **URL Integration**: `/tienda/{codigo}/local/{codigo}/productos`
3. **Selector Component**: Dropdown para cambio rápido de contexto
4. **Route Guards**: Validación de permisos por tenant
5. **Breadcrumbs**: Navegación con contexto visual

#### **3.2. Servicios API Multi-Tenant (16-20 horas)**

**Entregables:**
- ✅ **API Client**: Headers automáticos con tenant context
- ✅ **Service Updates**: Todos los servicios actualizados
- ✅ **Error Handling**: Manejo de errores multi-tenant específicos

**Archivos a crear/modificar:**
```
frontend/src/
├── services/
│   ├── tenantService.ts          # NEW - Servicios tienda/local
│   ├── api.ts                    # MODIFY - Headers automáticos
│   └── [all existing services]   # MODIFY - Tenant-aware calls
├── utils/
│   ├── tenantUtils.ts            # NEW - Utilidades tenant
│   └── apiUtils.ts               # MODIFY - Header injection
```

**Modificación patrón servicios:**
```typescript
// Antes
const getProducts = async (): Promise<Product[]> => {
  const response = await api.get('/products/');
  return response.data;
};

// Después
const getProducts = async (tenantContext?: TenantContext): Promise<Product[]> => {
  const headers = tenantContext ? {
    'X-Tenant-Store': tenantContext.tienda.codigo,
    'X-Tenant-Location': tenantContext.local?.codigo,
  } : {};
  
  const response = await api.get('/products/', { headers });
  return response.data;
};
```

#### **3.3. UI/UX Multi-Tenant (24-35 horas)**

**Entregables:**
- ✅ **Dashboard Updates**: Métricas por local + consolidadas
- ✅ **Component Updates**: Todos los componentes tenant-aware  
- ✅ **New Components**: Gestión de tiendas/locales
- ✅ **Multi-level Analytics**: Vistas granulares y consolidadas

**Archivos principales:**
```
frontend/src/
├── pages/
│   ├── TenantManagementPage.tsx  # NEW - Gestión tiendas/locales
│   ├── DashboardPage.tsx         # MODIFY - Métricas multi-level
│   └── [all existing pages]      # MODIFY - Tenant context integration
├── components/
│   ├── tenant/
│   │   ├── TiendaManagement.tsx  # NEW - CRUD tiendas
│   │   ├── LocalManagement.tsx   # NEW - CRUD locales  
│   │   ├── TenantDashboard.tsx   # NEW - Dashboard consolidado
│   │   └── TenantAnalytics.tsx   # NEW - Analytics multi-nivel
│   └── [existing components]     # MODIFY - Props tenant context
```

**Funcionalidades UI clave:**
1. **Tenant Management**: Páginas para administrar tiendas/locales
2. **Contextual Dashboard**: Métricas que cambian según contexto activo
3. **Multi-level Reports**: Reportes por local, consolidados por tienda
4. **Visual Indicators**: Claridad sobre contexto actual (breadcrumbs, badges)
5. **Quick Switcher**: Cambio rápido entre locales desde cualquier página

### **FASE 4: Testing y Finalización (20-30 horas)**

#### **4.1. Testing Integral (16-20 horas)**

**Entregables:**
- ✅ **Unit Tests**: Tests para nuevos componentes/servicios
- ✅ **Integration Tests**: APIs con tenant context
- ✅ **E2E Tests**: Flujos completos multi-tenant
- ✅ **Data Integrity**: Validación de segregación

**Testing Strategy:**
```
backend/tests/
├── test_multi_tenant/
│   ├── test_tenant_context.py
│   ├── test_tienda_repository.py
│   ├── test_local_repository.py
│   ├── test_tenant_middleware.py
│   └── test_api_segregation.py      # Validar que los datos no se filtren

frontend/src/
├── __tests__/
│   ├── tenant/
│   │   ├── TenantContext.test.tsx
│   │   ├── TenantSelector.test.tsx
│   │   └── tenantService.test.ts
│   └── integration/
│       └── multiTenant.test.tsx
```

**Tests críticos:**
1. **Data Segregation**: Verificar que Local A no ve datos de Local B
2. **Context Propagation**: Headers se envían correctamente
3. **Permission Validation**: Usuarios solo acceden a sus tiendas/locales
4. **Migration Integrity**: Datos migrados correctamente
5. **Performance**: Queries eficientes con filtros tenant

#### **4.2. Documentación y Deploy (4-10 horas)**

**Entregables:**
- ✅ **Documentación Técnica**: Architecture overview multi-tenant
- ✅ **Guía de Usuario**: Como usar el sistema multi-tenant
- ✅ **Migration Guide**: Pasos para activar modo multi-tenant
- ✅ **Performance Guide**: Optimizaciones y monitoring

**Documentos a crear:**
```
memory-bank/
├── multi-tenant-architecture.md     # Arquitectura técnica
├── multi-tenant-user-guide.md       # Guía de usuario
├── migration-production-guide.md    # Migración a producción
└── multi-tenant-troubleshooting.md  # Resolución de problemas
```

---

## 🚀 Estrategia de Implementación

### **Enfoque Incremental**

**Opción A: Big Bang (Recomendado para desarrollo)**
- Implementación completa en branch feature/multi-tenant
- Testing integral antes de merge
- Deploy único con migración completa
- **Ventaja**: Menor complejidad, más predecible
- **Desventaja**: Mayor riesgo inicial

**Opción B: Incremental (Recomendado para producción)**
- Fase 1: Backend foundations
- Fase 2: APIs compatibles (feature flags)  
- Fase 3: Frontend gradual
- Fase 4: Activación completa
- **Ventaja**: Menor riesgo, validación continua
- **Desventaja**: Mayor complejidad temporal

### **Validación de Datos (Crítico)**

**Pre-migración:**
1. **Backup completo** de base de datos
2. **Validation scripts** para integridad
3. **Rollback plan** detallado

**Post-migración:**
1. **Smoke tests** de funcionalidades críticas
2. **Data integrity checks** automatizados
3. **Performance monitoring** activo

---

## 📈 Métricas de Éxito

### **KPIs Técnicos**
- **Performance**: < 10% degradación en tiempo de respuesta
- **Coverage**: > 90% test coverage en código nuevo  
- **Reliability**: 99.9% uptime durante migración
- **Data Integrity**: 0% pérdida/corrupción de datos

### **KPIs de Negocio**
- **Usabilidad**: < 30 segundos para cambiar contexto local
- **Adopción**: 100% de usuarios migrados en 2 semanas
- **Escalabilidad**: Soporte para 10+ tiendas, 50+ locales
- **ROI**: Tiempo de desarrollo recuperado en 6 meses

---

## ⚠️ Riesgos y Mitigaciones

### **Riesgos Técnicos**

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| **Performance degradación** | Media | Alto | Índices optimizados, query profiling |
| **Data migration issues** | Baja | Crítico | Scripts validados, rollback plan |
| **Complex testing** | Alta | Medio | Test strategy incremental, automation |
| **URL/routing complexity** | Media | Medio | Consistent patterns, documentation |

### **Riesgos de Negocio**

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| **User confusion** | Media | Medio | Training, intuitive UX design |
| **Data segregation issues** | Baja | Crítico | Extensive testing, security reviews |
| **Increased maintenance** | Alta | Medio | Clear architecture, documentation |
| **Feature development slowdown** | Media | Medio | Standard patterns, tooling |

---

## 🎯 Recomendación Final

### **Viabilidad: ✅ ALTA**
La implementación es técnicamente viable aprovechando la arquitectura Clean existente. El Row-Level Security approach es la estrategia más eficiente.

### **ROI: ✅ POSITIVO**  
Inversión inicial significativa pero con retorno garantizado si el cliente maneja múltiples locales/tiendas.

### **Estrategia Recomendada:**
1. **Implementación Incremental** en 4 fases
2. **Testing intensivo** en cada fase  
3. **Migration gradual** con rollback plan
4. **Monitoring activo** post-deployment

### **Próximos Pasos:**
1. ✅ **Aprobación del cliente** del plan y presupuesto
2. ✅ **Setup del entorno** de desarrollo multi-tenant
3. ✅ **Inicio Fase 1**: Fundación de datos y contexto
4. ✅ **Validación continua** con stakeholders

---

---

## 📊 Estimaciones Finales Actualizadas

### **Desarrollo Multi-Tenant Completo**
- **Horas Totales**: 220-280 horas de desarrollo
- **Costo Estimado**: $11,000 - $14,000 USD
- **Tiempo Estimado**: 8-10 semanas (con 1 desarrollador full-time)
- **ROI Esperado**: 200-400% a 24 meses

### **Desglose por Fases**
| Fase | Horas | Semanas | Funcionalidades Clave |
|------|-------|---------|------------------------|
| **Fase 1: Fundación** | 60-80 | 2-3 | Modelo datos + contexto + permisos |
| **Fase 2: APIs Backend** | 80-100 | 3-4 | Endpoints + transferencias + multi-stock |
| **Fase 3: Frontend** | 60-80 | 2-3 | UI multi-tenant + transferencias + dashboards |
| **Fase 4: Testing** | 20-30 | 1 | Testing integral + documentación |

### **Características del Sistema Resultante**
✅ **Multi-tenant completo** con aislamiento por tienda  
✅ **Stock independiente** por local con transferencias  
✅ **Permisos granulares** por usuario-local  
✅ **Facturación consecutiva** por tienda  
✅ **Contabilidad consolidada** por tienda y local  
✅ **Dashboard multi-nivel** con analytics avanzados  
✅ **Sistema de transferencias** automatizado  
✅ **Navegación contextual** intuitiva
