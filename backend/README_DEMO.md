# 🎯 Datos de Demostración - Sistema de Gestión Empresarial

Este documento describe los datos de demostración que se han poblado en el sistema para facilitar las pruebas y validación de funcionalidades.

## 📊 Resumen de Datos Demo

### 👥 Usuarios Creados (4)

| Email | Nombre | Rol | Password |
|-------|--------|-----|----------|
| `admin.demo@empresa.com` | María García (Demo) | Administrador | `admin123` |
| `gerente.demo@empresa.com` | Carlos Rodríguez (Demo) | Gerente de Ventas | `gerente123` |
| `contador.demo@empresa.com` | Ana López (Demo) | Contador | `contador123` |
| `vendedor.demo@empresa.com` | Luis Martínez (Demo) | Vendedor | `vendedor123` |

### 📦 Productos en Catálogo (6)

| SKU | Nombre | Stock | Precio Base | Precio Público |
|-----|--------|-------|-------------|----------------|
| `DEMO-LAPTOP-001` | Laptop HP Pavilion 15 (Demo) | 24 | $2,500,000 | $3,200,000 |
| `DEMO-MOUSE-001` | Mouse Logitech MX Master 3 (Demo) | 74 | $180,000 | $250,000 |
| `DEMO-TECLADO-001` | Teclado Mecánico RGB (Demo) | 14 | $320,000 | $450,000 |
| `DEMO-MONITOR-001` | Monitor Dell 24 pulgadas (Demo) | 8 | $850,000 | $1,100,000 |
| `DEMO-CABLE-001` | Cable USB-C 2 metros (Demo) | 400 | $25,000 | $35,000 |
| `DEMO-AUDIFONOS-001` | Audífonos Sony WH-1000XM4 (Demo) | 12 | $950,000 | $1,200,000 |

### 📋 Movimientos de Inventario (~30)

**Entradas (18 movimientos):**
- Compras iniciales de todos los productos
- Reabastecimientos con precios diferentes (para probar costo promedio)
- Referencias: `DEMO-FC-001` a `DEMO-FC-009`

**Salidas (12 movimientos):**
- Ventas de diferentes productos
- Simulación de ventas combo y mayoristas
- Referencias: `DEMO-FV-001` a `DEMO-FV-006`

**Estadísticas:**
- **Valor total del inventario:** $102,881,111.44
- **Total entradas este mes:** 18
- **Total salidas este mes:** 12
- **Valor entradas:** $145,250,000.00
- **Valor salidas:** $57,100,000.00

## 🚀 Cómo Poblar los Datos Demo

### Opción 1: Script Interactivo
```bash
cd backend
python populate_demo_data.py
```

### Opción 2: Comando Pytest
```bash
cd backend
python -m pytest tests/test_demo_data.py::test_populate_demo_data -v -s
```

## 🧪 Casos de Uso para Probar

### 1. Autenticación y Autorización
- Probar login con cada tipo de usuario
- Verificar que cada rol tiene acceso solo a sus funciones permitidas
- Endpoint: `POST /api/v1/auth/login`

### 2. Gestión de Productos
- Listar productos: `GET /api/v1/products/`
- Buscar por SKU: `GET /api/v1/products/sku/DEMO-LAPTOP-001`
- Productos con stock bajo: `GET /api/v1/products/low-stock/?threshold=10`

### 3. Inventario y Kardex
- Ver resumen de inventario: `GET /api/v1/inventario/resumen/`
- Consultar estadísticas: `GET /api/v1/inventario/estadisticas/`
- Kardex de un producto: `GET /api/v1/inventario/kardex/{producto_id}`
- Validar stock: `POST /api/v1/inventario/validar-stock/`

### 4. Movimientos de Inventario
- Listar movimientos: `GET /api/v1/inventario/movimientos/`
- Registrar nueva entrada: `POST /api/v1/inventario/movimientos/`
- Registrar nueva salida: `POST /api/v1/inventario/movimientos/`

## 🔍 Funcionalidades Demostradas

### ✅ Reglas de Negocio Implementadas
- **BR-01:** Stock no puede ser negativo
- **BR-02:** SKU único e inmutable
- **BR-06:** Control de acceso por roles
- **BR-11:** Costo promedio ponderado

### ✅ Características del Sistema
- **Clean Architecture:** Separación clara de capas
- **Validación de datos:** Pydantic para entrada y salida
- **Soft delete:** Los productos se marcan como inactivos
- **Auditoría:** Timestamps automáticos en todas las operaciones
- **Cálculo automático:** Costos promedio y stocks actualizados

## 🌐 Interfaces de Prueba

Una vez que el servidor esté ejecutándose (`uvicorn main:app --reload`):

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## 📝 Notas Importantes

1. **Datos Persistentes:** Los datos se guardan en PostgreSQL y persisten entre reinicios
2. **Reutilización:** El script maneja datos existentes (no duplica usuarios/productos)
3. **Limpieza:** Todos los datos demo tienen el sufijo "(Demo)" para fácil identificación
4. **Passwords:** Todas las contraseñas están hasheadas con bcrypt
5. **Tokens JWT:** Los tokens tienen expiración de 15 minutos por seguridad

## 🔧 Troubleshooting

### Error de Base de Datos
```bash
# Verificar conexión a PostgreSQL
psql -h localhost -p 5432 -U admin -d inventario
```

### Error de Migraciones
```bash
# Aplicar migraciones pendientes
alembic upgrade head
```

### Error de Dependencias
```bash
# Reinstalar dependencias
pip install -r requirements.txt
``` 