"""
Script para poblar la base de datos con datos demo multi-tenant.
Crea tiendas, locales, stock por local, transferencias y permisos.
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Cliente de prueba que usa la base de datos real PostgreSQL."""
    with TestClient(app) as test_client:
        yield test_client


def test_populate_multi_tenant_demo(client: TestClient):
    """Poblar la base de datos con datos demo multi-tenant."""
    print("\n🏢 === POBLANDO BASE DE DATOS CON DATOS DEMO MULTI-TENANT ===")
    
    # ========== EJECUTAR DATOS DEMO BÁSICOS PRIMERO ==========
    print("\n📋 Ejecutando datos demo básicos...")
    
    # Importar y ejecutar el test de datos básicos
    try:
        from test_demo_data import test_populate_demo_data
        test_populate_demo_data(client)
        print("✅ Datos demo básicos creados exitosamente")
    except Exception as e:
        print(f"⚠️ Error con datos básicos: {e}")
        print("Continuando con estructura multi-tenant...")
    
    # Login con admin para estructura multi-tenant
    print("\n🔐 Autenticando como administrador...")
    login_response = client.post("/api/v1/auth/login", json={
        "email": "admin.demo@empresa.com", 
        "password": "admin123"  # Password from basic demo
    })
    
    if login_response.status_code != 200:
        print("❌ No se pudo autenticar. Asegúrate de ejecutar populate_demo_data.py primero")
        print("Intentando crear estructura mínima...")
        # Try with empty auth for testing endpoints
        headers = {}
    else:
        admin_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}
        print("✅ Autenticado exitosamente")
    
    # ========== PRODUCTOS BASE ==========
    print("\n📦 Verificando productos base...")
    
    productos_response = client.get("/api/v1/products/")
    assert productos_response.status_code == 200
    productos_existentes = productos_response.json()["products"]
    
    if len(productos_existentes) < 3:
        print("⚠️ Pocos productos encontrados, ejecuta populate_demo_data.py primero")
        # Crear algunos productos básicos
        productos_basicos = [
            {
                "sku": "MT-LAPTOP-001",
                "nombre": "Laptop Demo Multi-Tenant",
                "descripcion": "Laptop para demo multi-tenant",
                "precio_base": "2000000.00",
                "precio_publico": "2500000.00",
                "stock": 0
            },
            {
                "sku": "MT-MOUSE-001", 
                "nombre": "Mouse Demo Multi-Tenant",
                "descripcion": "Mouse para demo multi-tenant",
                "precio_base": "80000.00",
                "precio_publico": "120000.00",
                "stock": 0
            },
            {
                "sku": "MT-CABLE-001",
                "nombre": "Cable Demo Multi-Tenant", 
                "descripcion": "Cable para demo multi-tenant",
                "precio_base": "15000.00",
                "precio_publico": "25000.00",
                "stock": 0
            }
        ]
        
        for producto in productos_basicos:
            response = client.post("/api/v1/products/", json=producto)
            if response.status_code == 201:
                print(f"✅ Producto creado: {producto['nombre']}")
            else:
                print(f"⚠️ Producto ya existe: {producto['sku']}")
        
        # Recargar productos
        productos_response = client.get("/api/v1/products/")
        productos_existentes = productos_response.json()["products"]
    
    productos_demo = productos_existentes[:6]  # Usar primeros 6 productos
    print(f"✅ Usando {len(productos_demo)} productos para demo multi-tenant")
    
    # ========== TIENDAS ==========
    print("\n🏪 Creando tiendas demo...")
    
    tiendas_data = [
        {
            "codigo": "TC-001",
            "nombre": "Tienda Centro",
            "descripcion": "Tienda principal en el centro de la ciudad",
            "direccion": "Calle 100 #15-20, Centro, Bogotá",
            "telefono": "+57 1 234-5678",
            "email": "centro@empresa.com",
            "gerente_nombre": "Carlos Rodríguez",
            "is_active": True
        },
        {
            "codigo": "TN-001", 
            "nombre": "Tienda Norte",
            "descripcion": "Tienda en zona norte de la ciudad",
            "direccion": "Carrera 15 #85-30, Zona Norte, Bogotá", 
            "telefono": "+57 1 345-6789",
            "email": "norte@empresa.com",
            "gerente_nombre": "Patricia Morales",
            "is_active": True
        }
    ]
    
    tiendas_creadas = []
    for tienda_data in tiendas_data:
        response = client.post("/api/v1/tiendas/", json=tienda_data, headers=headers)
        
        if response.status_code == 400 and "ya existe" in response.text:
            print(f"⚠️ Tienda ya existe: {tienda_data['codigo']}, buscando...")
            # Buscar tienda existente
            tiendas_response = client.get("/api/v1/tiendas/", headers=headers)
            if tiendas_response.status_code == 200:
                tiendas_existentes = tiendas_response.json()["tiendas"]
                tienda_existente = next((t for t in tiendas_existentes if t["codigo"] == tienda_data["codigo"]), None)
                if tienda_existente:
                    tiendas_creadas.append(tienda_existente)
                    print(f"✅ Tienda encontrada: {tienda_existente['nombre']}")
                    continue
        
        assert response.status_code == 201, f"Error creando tienda: {response.text}"
        tienda = response.json()
        tiendas_creadas.append(tienda)
        print(f"✅ Tienda creada: {tienda['nombre']} ({tienda['codigo']})")
    
    # ========== LOCALES ==========
    print("\n🏢 Creando locales por tienda...")
    
    locales_tienda_centro = [
        {
            "tienda_id": tiendas_creadas[0]["id"],
            "codigo": "TC-SUC-001",
            "nombre": "Sucursal Principal Centro",
            "descripcion": "Sucursal principal de atención al público",
            "tipo_local": "SUCURSAL",
            "direccion": {
                "direccion_principal": "Calle 100 #15-20, Local 101",
                "ciudad": "Bogotá",
                "departamento": "Cundinamarca",
                "pais": "Colombia"
            },
            "telefono": "+57 1 234-5678 Ext 101",
            "email": "sucursal.centro@empresa.com",
            "responsable_nombre": "Ana López",
            "capacidad_productos": 1000,
            "is_active": True
        },
        {
            "tienda_id": tiendas_creadas[0]["id"],
            "codigo": "TC-ALM-001", 
            "nombre": "Almacén Central",
            "descripcion": "Almacén central de distribución",
            "tipo_local": "ALMACEN",
            "direccion": {
                "direccion_principal": "Calle 100 #15-20, Bodega B1",
                "ciudad": "Bogotá", 
                "departamento": "Cundinamarca",
                "pais": "Colombia"
            },
            "telefono": "+57 1 234-5678 Ext 200",
            "email": "almacen.central@empresa.com",
            "responsable_nombre": "Luis Martínez",
            "capacidad_productos": 5000,
            "is_active": True
        },
        {
            "tienda_id": tiendas_creadas[0]["id"],
            "codigo": "TC-SHW-001",
            "nombre": "Showroom Centro",
            "descripcion": "Showroom para exhibición de productos",
            "tipo_local": "SHOWROOM", 
            "direccion": {
                "direccion_principal": "Calle 100 #15-20, Piso 2",
                "ciudad": "Bogotá",
                "departamento": "Cundinamarca", 
                "pais": "Colombia"
            },
            "telefono": "+57 1 234-5678 Ext 300",
            "email": "showroom.centro@empresa.com",
            "responsable_nombre": "Carolina Silva",
            "capacidad_productos": 200,
            "is_active": True
        },
        {
            "tienda_id": tiendas_creadas[0]["id"],
            "codigo": "TC-VIR-001",
            "nombre": "Tienda Virtual Centro",
            "descripcion": "Tienda virtual para ventas en línea",
            "tipo_local": "VIRTUAL",
            "direccion": {
                "direccion_principal": "Plataforma Digital",
                "ciudad": "Bogotá",
                "departamento": "Cundinamarca",
                "pais": "Colombia"
            },
            "telefono": "+57 1 234-5678 Ext 400",
            "email": "virtual.centro@empresa.com", 
            "responsable_nombre": "Diego Ramírez",
            "capacidad_productos": 0,
            "is_active": True
        }
    ]
    
    locales_tienda_norte = [
        {
            "tienda_id": tiendas_creadas[1]["id"],
            "codigo": "TN-SUC-001",
            "nombre": "Sucursal Norte",
            "descripcion": "Sucursal en zona norte",
            "tipo_local": "SUCURSAL",
            "direccion": {
                "direccion_principal": "Carrera 15 #85-30, Local 1-2",
                "ciudad": "Bogotá",
                "departamento": "Cundinamarca",
                "pais": "Colombia"
            },
            "telefono": "+57 1 345-6789 Ext 101",
            "email": "sucursal.norte@empresa.com",
            "responsable_nombre": "Patricia Morales",
            "capacidad_productos": 800,
            "is_active": True
        },
        {
            "tienda_id": tiendas_creadas[1]["id"],
            "codigo": "TN-ALM-001",
            "nombre": "Almacén Norte", 
            "descripcion": "Almacén de apoyo zona norte",
            "tipo_local": "ALMACEN",
            "direccion": {
                "direccion_principal": "Carrera 15 #85-30, Bodega A1",
                "ciudad": "Bogotá",
                "departamento": "Cundinamarca",
                "pais": "Colombia"
            },
            "telefono": "+57 1 345-6789 Ext 200",
            "email": "almacen.norte@empresa.com",
            "responsable_nombre": "Roberto Castillo",
            "capacidad_productos": 2000,
            "is_active": True
        }
    ]
    
    todos_los_locales = locales_tienda_centro + locales_tienda_norte
    locales_creados = []
    
    for local_data in todos_los_locales:
        response = client.post("/api/v1/locales/", json=local_data, headers=headers)
        
        if response.status_code == 400 and "ya existe" in response.text:
            print(f"⚠️ Local ya existe: {local_data['codigo']}")
            # Buscar local existente por código
            tienda_id = local_data["tienda_id"]
            locales_response = client.get(f"/api/v1/locales/tienda/{tienda_id}", headers=headers)
            if locales_response.status_code == 200:
                locales_existentes = locales_response.json()["locales"]
                local_existente = next((l for l in locales_existentes if l["codigo"] == local_data["codigo"]), None)
                if local_existente:
                    locales_creados.append(local_existente)
                    print(f"✅ Local encontrado: {local_existente['nombre']}")
                    continue
        
        assert response.status_code == 201, f"Error creando local: {response.text}"
        local = response.json()
        locales_creados.append(local)
        print(f"✅ Local creado: {local['nombre']} ({local['codigo']}) - {local['tipo_local']}")
    
    # ========== STOCK POR LOCAL ==========
    print("\n📦 Distribuyendo stock inicial por local...")
    
    # Distribución de stock por tipo de local
    stock_distributions = [
        # Almacén Central - Stock principal
        {
            "local": next(l for l in locales_creados if l["codigo"] == "TC-ALM-001"),
            "stock_data": [
                {"producto": productos_demo[0], "cantidad": 50, "costo": "2400000.00"},  # Laptop
                {"producto": productos_demo[1], "cantidad": 200, "costo": "170000.00"},  # Mouse
                {"producto": productos_demo[2], "cantidad": 100, "costo": "300000.00"},  # Teclado
                {"producto": productos_demo[3], "cantidad": 80, "costo": "800000.00"},   # Monitor
                {"producto": productos_demo[4], "cantidad": 500, "costo": "20000.00"},   # Cable
                {"producto": productos_demo[5], "cantidad": 60, "costo": "900000.00"}    # Audífonos
            ]
        },
        # Sucursal Principal - Stock de venta
        {
            "local": next(l for l in locales_creados if l["codigo"] == "TC-SUC-001"),
            "stock_data": [
                {"producto": productos_demo[0], "cantidad": 15, "costo": "2450000.00"},
                {"producto": productos_demo[1], "cantidad": 80, "costo": "175000.00"},
                {"producto": productos_demo[2], "cantidad": 30, "costo": "310000.00"},
                {"producto": productos_demo[3], "cantidad": 20, "costo": "820000.00"},
                {"producto": productos_demo[4], "cantidad": 150, "costo": "22000.00"},
                {"producto": productos_demo[5], "cantidad": 25, "costo": "920000.00"}
            ]
        },
        # Showroom Centro - Stock limitado de exhibición
        {
            "local": next(l for l in locales_creados if l["codigo"] == "TC-SHW-001"),
            "stock_data": [
                {"producto": productos_demo[0], "cantidad": 3, "costo": "2450000.00"},
                {"producto": productos_demo[1], "cantidad": 10, "costo": "175000.00"},
                {"producto": productos_demo[2], "cantidad": 5, "costo": "310000.00"},
                {"producto": productos_demo[3], "cantidad": 8, "costo": "820000.00"},
                {"producto": productos_demo[4], "cantidad": 20, "costo": "22000.00"},
                {"producto": productos_demo[5], "cantidad": 4, "costo": "920000.00"}
            ]
        },
        # Sucursal Norte - Stock operativo
        {
            "local": next(l for l in locales_creados if l["codigo"] == "TN-SUC-001"),
            "stock_data": [
                {"producto": productos_demo[0], "cantidad": 10, "costo": "2500000.00"},
                {"producto": productos_demo[1], "cantidad": 40, "costo": "180000.00"},
                {"producto": productos_demo[2], "cantidad": 20, "costo": "315000.00"},
                {"producto": productos_demo[3], "cantidad": 12, "costo": "850000.00"},
                {"producto": productos_demo[4], "cantidad": 100, "costo": "25000.00"},
                {"producto": productos_demo[5], "cantidad": 15, "costo": "950000.00"}
            ]
        },
        # Almacén Norte - Stock de respaldo
        {
            "local": next(l for l in locales_creados if l["codigo"] == "TN-ALM-001"),
            "stock_data": [
                {"producto": productos_demo[0], "cantidad": 20, "costo": "2480000.00"},
                {"producto": productos_demo[1], "cantidad": 60, "costo": "178000.00"},
                {"producto": productos_demo[2], "cantidad": 40, "costo": "312000.00"},
                {"producto": productos_demo[3], "cantidad": 25, "costo": "830000.00"},
                {"producto": productos_demo[4], "cantidad": 200, "costo": "23000.00"},
                {"producto": productos_demo[5], "cantidad": 30, "costo": "930000.00"}
            ]
        }
    ]
    
    stock_creado = 0
    for distribution in stock_distributions:
        local = distribution["local"]
        print(f"\n📍 Distribuyendo stock en {local['nombre']}:")
        
        for stock_item in distribution["stock_data"]:
            # Crear movimiento de entrada inicial
            movimiento_data = {
                "local_id": local["id"],
                "producto_id": stock_item["producto"]["id"],
                "tipo_movimiento": "ENTRADA",
                "cantidad": stock_item["cantidad"],
                "costo_unitario": stock_item["costo"],
                "referencia": f"STOCK-INICIAL-{local['codigo']}-{stock_item['producto']['sku']}",
                "observaciones": f"Stock inicial para {local['nombre']}"
            }
            
            response = client.post("/api/v1/stock-local/movimiento", json=movimiento_data, headers=headers)
            
            if response.status_code == 201:
                stock_creado += 1
                print(f"  ✅ {stock_item['producto']['nombre']}: {stock_item['cantidad']} unidades")
            elif response.status_code == 400 and "ya existe" in response.text:
                print(f"  ⚠️ Stock ya existe: {stock_item['producto']['sku']}")
            else:
                print(f"  ❌ Error: {response.text}")
    
    print(f"\n📦 Stock distribuido: {stock_creado} movimientos iniciales")
    
    # ========== TRANSFERENCIAS ==========
    print("\n🚚 Creando transferencias demo...")
    
    # Obtener IDs de locales para transferencias
    almacen_central = next(l for l in locales_creados if l["codigo"] == "TC-ALM-001")
    sucursal_principal = next(l for l in locales_creados if l["codigo"] == "TC-SUC-001")
    showroom_centro = next(l for l in locales_creados if l["codigo"] == "TC-SHW-001")
    sucursal_norte = next(l for l in locales_creados if l["codigo"] == "TN-SUC-001")
    almacen_norte = next(l for l in locales_creados if l["codigo"] == "TN-ALM-001")
    
    transferencias_data = [
        {
            "local_origen_id": almacen_central["id"],
            "local_destino_id": sucursal_principal["id"],
            "producto_id": productos_demo[0]["id"],  # Laptop
            "cantidad": 5,
            "observaciones_origen": "Transferencia para restock sucursal principal",
            "prioridad": "ALTA"
        },
        {
            "local_origen_id": almacen_central["id"],
            "local_destino_id": showroom_centro["id"],
            "producto_id": productos_demo[1]["id"],  # Mouse
            "cantidad": 15,
            "observaciones_origen": "Productos para exhibición en showroom",
            "prioridad": "MEDIA"
        },
        {
            "local_origen_id": sucursal_principal["id"],
            "local_destino_id": sucursal_norte["id"],
            "producto_id": productos_demo[2]["id"],  # Teclado
            "cantidad": 8,
            "observaciones_origen": "Apoyo entre sucursales",
            "prioridad": "MEDIA"
        },
        {
            "local_origen_id": almacen_central["id"],
            "local_destino_id": almacen_norte["id"],
            "producto_id": productos_demo[3]["id"],  # Monitor
            "cantidad": 10,
            "observaciones_origen": "Distribución inter-almacenes",
            "prioridad": "BAJA"
        },
        {
            "local_origen_id": almacen_norte["id"],
            "local_destino_id": sucursal_norte["id"],
            "producto_id": productos_demo[4]["id"],  # Cable
            "cantidad": 50,
            "observaciones_origen": "Reabastecimiento cables USB",
            "prioridad": "ALTA"
        }
    ]
    
    transferencias_creadas = []
    for i, transfer_data in enumerate(transferencias_data):
        response = client.post("/api/v1/transferencias/", json=transfer_data, headers=headers)
        
        if response.status_code == 201:
            transferencia = response.json()
            transferencias_creadas.append(transferencia)
            origen = next(l for l in locales_creados if l["id"] == transfer_data["local_origen_id"])
            destino = next(l for l in locales_creados if l["id"] == transfer_data["local_destino_id"])
            producto = next(p for p in productos_demo if p["id"] == transfer_data["producto_id"])
            print(f"✅ Transferencia: {origen['nombre']} → {destino['nombre']}")
            print(f"   Producto: {producto['nombre']} ({transfer_data['cantidad']} unidades)")
            
            # Confirmar algunas transferencias
            if i % 2 == 0:  # Confirmar envío de transferencias pares
                confirm_response = client.post(
                    f"/api/v1/transferencias/{transferencia['id']}/confirmar-envio",
                    json={"observaciones_origen": "Enviado desde almacén"},
                    headers=headers
                )
                if confirm_response.status_code == 200:
                    print(f"   📤 Envío confirmado")
                    
                    # Confirmar recepción de algunas
                    if i == 0:  # Solo la primera
                        receive_response = client.post(
                            f"/api/v1/transferencias/{transferencia['id']}/confirmar-recepcion",
                            json={"observaciones_destino": "Recibido en perfecto estado"},
                            headers=headers
                        )
                        if receive_response.status_code == 200:
                            print(f"   📥 Recepción confirmada")
                            
        elif response.status_code == 400 and "no tiene suficiente stock" in response.text:
            print(f"⚠️ Transferencia sin stock suficiente")
        else:
            print(f"❌ Error creando transferencia: {response.text}")
    
    # ========== PERMISOS USUARIO-LOCAL ==========
    print("\n🔐 Configurando permisos usuario-local...")
    
    # Obtener IDs de usuarios
    gerente_id = next(u["id"] for u in usuarios_creados if "Gerente Centro" in u["nombre"])
    vendedor_id = next(u["id"] for u in usuarios_creados if "Vendedor Principal" in u["nombre"])
    almacenista_id = next(u["id"] for u in usuarios_creados if "Almacenista" in u["nombre"])
    
    permisos_data = [
        # Gerente - Acceso a todos los locales de Tienda Centro
        {
            "usuario_id": gerente_id,
            "local_id": sucursal_principal["id"],
            "perfil_permisos": "GERENTE_LOCAL",
            "permisos_personalizados": ["venta", "consulta_stock", "transferencia", "ver_reportes", "gestion_usuarios"],
            "observaciones": "Gerente con acceso completo",
            "is_active": True
        },
        {
            "usuario_id": gerente_id,
            "local_id": almacen_central["id"],
            "perfil_permisos": "SUPERVISOR",
            "permisos_personalizados": ["consulta_stock", "transferencia", "ver_reportes"],
            "observaciones": "Supervisión del almacén central",
            "is_active": True
        },
        {
            "usuario_id": gerente_id,
            "local_id": showroom_centro["id"],
            "perfil_permisos": "SUPERVISOR",
            "permisos_personalizados": ["consulta_stock", "ver_reportes"],
            "observaciones": "Supervisión del showroom",
            "is_active": True
        },
        # Vendedor - Acceso a sucursal principal
        {
            "usuario_id": vendedor_id,
            "local_id": sucursal_principal["id"],
            "perfil_permisos": "VENDEDOR",
            "permisos_personalizados": ["venta", "consulta_stock"],
            "observaciones": "Vendedor de sucursal principal",
            "is_active": True
        },
        # Almacenista - Acceso a almacenes
        {
            "usuario_id": almacenista_id,
            "local_id": almacen_central["id"],
            "perfil_permisos": "ALMACENISTA",
            "permisos_personalizados": ["consulta_stock", "transferencia", "modificar_stock"],
            "observaciones": "Responsable del almacén central",
            "is_active": True
        },
        {
            "usuario_id": almacenista_id,
            "local_id": almacen_norte["id"],
            "perfil_permisos": "ALMACENISTA",
            "permisos_personalizados": ["consulta_stock", "transferencia"],
            "observaciones": "Apoyo en almacén norte",
            "is_active": True
        }
    ]
    
    permisos_creados = 0
    for permiso_data in permisos_data:
        response = client.post("/api/v1/usuario-locales/", json=permiso_data, headers=headers)
        
        if response.status_code == 201:
            permisos_creados += 1
            usuario = next(u for u in usuarios_creados if u["id"] == permiso_data["usuario_id"])
            local = next(l for l in locales_creados if l["id"] == permiso_data["local_id"])
            print(f"✅ Permiso: {usuario['nombre']} → {local['nombre']} ({permiso_data['perfil_permisos']})")
        elif response.status_code == 400 and "ya existe" in response.text:
            print(f"⚠️ Permiso ya existe")
        else:
            print(f"❌ Error creando permiso: {response.text}")
    
    # ========== CONSULTAS FINALES ==========
    print("\n📊 Consultando estado final multi-tenant...")
    
    # Estadísticas por tienda
    for tienda in tiendas_creadas:
        response = client.get(f"/api/v1/tiendas/{tienda['id']}/estadisticas", headers=headers)
        if response.status_code == 200:
            stats = response.json()
            print(f"\n🏪 {tienda['nombre']}:")
            print(f"   • Locales: {stats.get('total_locales', 0)}")
            print(f"   • Productos únicos: {stats.get('productos_unicos', 0)}")
            print(f"   • Valor total inventario: ${stats.get('valor_total_inventario', 0):,.0f}")
            print(f"   • Transferencias activas: {stats.get('transferencias_pendientes', 0)}")
    
    # Stock por algunos locales
    print(f"\n📦 Resumen de stock por local:")
    for local in locales_creados[:3]:  # Primeros 3 locales
        response = client.get(f"/api/v1/stock-local/?local_id={local['id']}", headers=headers)
        if response.status_code == 200:
            stock_items = response.json()["stock_items"]
            total_valor = sum(float(item.get("valor_total_stock", 0)) for item in stock_items)
            total_productos = len(stock_items)
            print(f"   • {local['nombre']}: {total_productos} productos, ${total_valor:,.0f}")
    
    # Transferencias resumen
    response = client.get("/api/v1/transferencias/resumen", headers=headers)
    if response.status_code == 200:
        resumen_transfers = response.json()
        print(f"\n🚚 Resumen de transferencias:")
        print(f"   • Total transferencias: {resumen_transfers.get('total_transferencias', 0)}")
        print(f"   • Pendientes: {resumen_transfers.get('pendientes', 0)}")
        print(f"   • En tránsito: {resumen_transfers.get('enviadas', 0)}")
        print(f"   • Completadas: {resumen_transfers.get('recibidas', 0)}")
    
    print(f"\n🎉 === DATOS DEMO MULTI-TENANT CREADOS EXITOSAMENTE ===")
    print(f"📊 Resumen de la estructura multi-tenant:")
    print(f"   • {len(usuarios_creados)} usuarios con roles específicos")
    print(f"   • {len(tiendas_creadas)} tiendas operativas")
    print(f"   • {len(locales_creados)} locales de diferentes tipos")
    print(f"   • {stock_creado} distribuciones de stock inicial")
    print(f"   • {len(transferencias_creadas)} transferencias entre locales")
    print(f"   • {permisos_creados} asignaciones de permisos usuario-local")
    print(f"   • Sistema multi-tenant funcionando con PostgreSQL")
    
    print(f"\n🔧 Para probar el sistema multi-tenant:")
    print(f"   1. Login como cualquier usuario demo")
    print(f"   2. Usar endpoints /tenant-context/ para cambiar contexto")
    print(f"   3. Probar endpoints /tiendas/, /locales/, /stock-local/, /transferencias/")
    print(f"   4. Verificar permisos granulares por local")


if __name__ == "__main__":
    # Ejecutar directamente
    pytest.main([__file__ + "::test_populate_multi_tenant_demo", "-v", "-s"])