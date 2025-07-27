"""
Script para poblar la base de datos con datos de demostración.
Utiliza la base de datos real PostgreSQL.
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


def test_populate_demo_data(client: TestClient):
    """Poblar la base de datos con datos de demostración."""
    print("\n🚀 === POBLANDO BASE DE DATOS CON DATOS DEMO ===")
    
    # ========== USUARIOS ==========
    print("\n👥 Creando usuarios demo...")
    
    usuarios = [
        {
            "email": "admin.demo@empresa.com",
            "nombre": "María García (Demo)",
            "rol": "administrador",
            "password": "admin123"
        },
        {
            "email": "gerente.demo@empresa.com",
            "nombre": "Carlos Rodríguez (Demo)",
            "rol": "gerente_ventas",
            "password": "gerente123"
        },
        {
            "email": "contador.demo@empresa.com",
            "nombre": "Ana López (Demo)",
            "rol": "contador",
            "password": "contador123"
        },
        {
            "email": "vendedor.demo@empresa.com",
            "nombre": "Luis Martínez (Demo)",
            "rol": "vendedor",
            "password": "vendedor123"
        }
    ]
    
    usuarios_creados = []
    for usuario_data in usuarios:
        response = client.post("/api/v1/auth/register", json=usuario_data)
        
        if response.status_code == 409:  # Usuario ya existe
            print(f"⚠️ Usuario ya existe: {usuario_data['email']}, haciendo login...")
            login_data = {"email": usuario_data["email"], "password": usuario_data["password"]}
            response = client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 200
        else:
            assert response.status_code == 201
            
        result = response.json()
        usuarios_creados.append(result["user"])
        print(f"✅ Usuario: {result['user']['nombre']}")
    
    # ========== PRODUCTOS ==========
    print("\n📦 Creando productos demo...")
    
    productos = [
        {
            "sku": "DEMO-LAPTOP-001",
            "nombre": "Laptop HP Pavilion 15 (Demo)",
            "descripcion": "Laptop HP Pavilion 15 pulgadas, Intel Core i5, 8GB RAM, 256GB SSD - Producto Demo",
            "precio_base": "2500000.00",
            "precio_publico": "3200000.00",
            "stock": 0
        },
        {
            "sku": "DEMO-MOUSE-001",
            "nombre": "Mouse Logitech MX Master 3 (Demo)",
            "descripcion": "Mouse inalámbrico ergonómico para productividad - Producto Demo",
            "precio_base": "180000.00",
            "precio_publico": "250000.00",
            "stock": 0
        },
        {
            "sku": "DEMO-TECLADO-001",
            "nombre": "Teclado Mecánico RGB (Demo)",
            "descripcion": "Teclado mecánico gaming con iluminación RGB - Producto Demo",
            "precio_base": "320000.00",
            "precio_publico": "450000.00",
            "stock": 0
        },
        {
            "sku": "DEMO-MONITOR-001",
            "nombre": "Monitor Dell 24 pulgadas (Demo)",
            "descripcion": "Monitor Dell Full HD 24 pulgadas, IPS, 75Hz - Producto Demo",
            "precio_base": "850000.00",
            "precio_publico": "1100000.00",
            "stock": 0
        },
        {
            "sku": "DEMO-CABLE-001",
            "nombre": "Cable USB-C 2 metros (Demo)",
            "descripcion": "Cable USB-C de alta velocidad, 2 metros de longitud - Producto Demo",
            "precio_base": "25000.00",
            "precio_publico": "35000.00",
            "stock": 0
        },
        {
            "sku": "DEMO-AUDIFONOS-001",
            "nombre": "Audífonos Sony WH-1000XM4 (Demo)",
            "descripcion": "Audífonos inalámbricos con cancelación de ruido - Producto Demo",
            "precio_base": "950000.00",
            "precio_publico": "1200000.00",
            "stock": 0
        }
    ]
    
    productos_creados = []
    for producto_data in productos:
        response = client.post("/api/v1/products/", json=producto_data)
        
        if response.status_code == 400:  # Producto ya existe
            print(f"⚠️ Producto ya existe: {producto_data['sku']}, buscando...")
            response_get = client.get(f"/api/v1/products/sku/{producto_data['sku']}")
            if response_get.status_code == 200:
                producto = response_get.json()
                productos_creados.append(producto)
                print(f"✅ Producto encontrado: {producto['nombre']}")
            continue
        
        assert response.status_code == 201
        producto = response.json()
        productos_creados.append(producto)
        print(f"✅ Producto creado: {producto['nombre']}")
    
    # ========== MOVIMIENTOS DE INVENTARIO ==========
    print("\n📋 Creando movimientos de inventario demo...")
    
    # Entradas de inventario
    entradas = [
        {
            "producto_id": productos_creados[0]["id"],  # Laptop
            "tipo_movimiento": "entrada",
            "cantidad": 10,
            "precio_unitario": "2450000.00",
            "referencia": "DEMO-FC-001",
            "observaciones": "Compra inicial de laptops HP - Proveedor Demo"
        },
        {
            "producto_id": productos_creados[1]["id"],  # Mouse
            "tipo_movimiento": "entrada",
            "cantidad": 25,
            "precio_unitario": "175000.00",
            "referencia": "DEMO-FC-002",
            "observaciones": "Compra de mice Logitech - Proveedor Demo"
        },
        {
            "producto_id": productos_creados[2]["id"],  # Teclado
            "tipo_movimiento": "entrada",
            "cantidad": 15,
            "precio_unitario": "310000.00",
            "referencia": "DEMO-FC-003",
            "observaciones": "Compra de teclados mecánicos - Proveedor Demo"
        },
        {
            "producto_id": productos_creados[3]["id"],  # Monitor
            "tipo_movimiento": "entrada",
            "cantidad": 8,
            "precio_unitario": "820000.00",
            "referencia": "DEMO-FC-004",
            "observaciones": "Compra de monitores Dell - Proveedor Demo"
        },
        {
            "producto_id": productos_creados[4]["id"],  # Cable
            "tipo_movimiento": "entrada",
            "cantidad": 100,
            "precio_unitario": "22000.00",
            "referencia": "DEMO-FC-005",
            "observaciones": "Compra masiva de cables USB-C - Proveedor Demo"
        },
        {
            "producto_id": productos_creados[5]["id"],  # Audífonos
            "tipo_movimiento": "entrada",
            "cantidad": 12,
            "precio_unitario": "920000.00",
            "referencia": "DEMO-FC-006",
            "observaciones": "Compra de audífonos Sony - Proveedor Demo"
        }
    ]
    
    movimientos_creados = 0
    for entrada in entradas:
        response = client.post("/api/v1/inventario/movimientos/", json=entrada)
        
        if response.status_code == 201:
            movimiento = response.json()
            movimientos_creados += 1
            print(f"✅ Entrada: {entrada['cantidad']} unidades - Ref: {entrada['referencia']}")
            print(f"   Stock: {movimiento['stock_anterior']} → {movimiento['stock_posterior']}")
        else:
            print(f"⚠️ Movimiento ya existe: {entrada['referencia']}")
    
    # Reabastecimientos
    reabastecimientos = [
        {
            "producto_id": productos_creados[0]["id"],  # Laptop
            "tipo_movimiento": "entrada",
            "cantidad": 5,
            "precio_unitario": "2600000.00",
            "referencia": "DEMO-FC-007",
            "observaciones": "Reabastecimiento laptops HP - Demo"
        },
        {
            "producto_id": productos_creados[1]["id"],  # Mouse
            "tipo_movimiento": "entrada",
            "cantidad": 20,
            "precio_unitario": "165000.00",
            "referencia": "DEMO-FC-008",
            "observaciones": "Reabastecimiento mice - Demo"
        },
        {
            "producto_id": productos_creados[4]["id"],  # Cable
            "tipo_movimiento": "entrada",
            "cantidad": 150,
            "precio_unitario": "20000.00",
            "referencia": "DEMO-FC-009",
            "observaciones": "Reabastecimiento cables - Demo"
        }
    ]
    
    for reabastecimiento in reabastecimientos:
        response = client.post("/api/v1/inventario/movimientos/", json=reabastecimiento)
        if response.status_code == 201:
            movimiento = response.json()
            movimientos_creados += 1
            print(f"✅ Reabastecimiento: {reabastecimiento['cantidad']} unidades")
        else:
            print(f"⚠️ Reabastecimiento ya existe: {reabastecimiento['referencia']}")
    
    # Ventas
    ventas = [
        {
            "producto_id": productos_creados[0]["id"],  # Laptop
            "tipo_movimiento": "salida",
            "cantidad": 3,
            "precio_unitario": "3200000.00",
            "referencia": "DEMO-FV-001",
            "observaciones": "Venta laptops - Demo"
        },
        {
            "producto_id": productos_creados[1]["id"],  # Mouse
            "tipo_movimiento": "salida",
            "cantidad": 8,
            "precio_unitario": "250000.00",
            "referencia": "DEMO-FV-002",
            "observaciones": "Venta mice - Demo"
        },
        {
            "producto_id": productos_creados[2]["id"],  # Teclado
            "tipo_movimiento": "salida",
            "cantidad": 8,
            "precio_unitario": "450000.00",
            "referencia": "DEMO-FV-003",
            "observaciones": "Venta teclados - Demo"
        },
        {
            "producto_id": productos_creados[3]["id"],  # Monitor
            "tipo_movimiento": "salida",
            "cantidad": 4,
            "precio_unitario": "1100000.00",
            "referencia": "DEMO-FV-004",
            "observaciones": "Venta monitores - Demo"
        },
        {
            "producto_id": productos_creados[4]["id"],  # Cable
            "tipo_movimiento": "salida",
            "cantidad": 50,
            "precio_unitario": "35000.00",
            "referencia": "DEMO-FV-005",
            "observaciones": "Venta cables - Demo"
        },
        {
            "producto_id": productos_creados[5]["id"],  # Audífonos
            "tipo_movimiento": "salida",
            "cantidad": 6,
            "precio_unitario": "1200000.00",
            "referencia": "DEMO-FV-006",
            "observaciones": "Venta audífonos - Demo"
        }
    ]
    
    for venta in ventas:
        response = client.post("/api/v1/inventario/movimientos/", json=venta)
        if response.status_code == 201:
            movimiento = response.json()
            movimientos_creados += 1
            print(f"✅ Venta: {venta['cantidad']} unidades - Ref: {venta['referencia']}")
        else:
            print(f"⚠️ Venta ya existe: {venta['referencia']}")
    
    # ========== CONSULTAS FINALES ==========
    print("\n📊 Consultando estado final...")
    
    # Estado de productos
    response = client.get("/api/v1/products/")
    assert response.status_code == 200
    productos_actuales = response.json()
    
    productos_demo = [p for p in productos_actuales["products"] if "Demo" in p["nombre"]]
    print(f"\n📦 Productos demo en inventario:")
    for producto in productos_demo:
        print(f"• {producto['nombre']}: {producto['stock']} unidades")
    
    # Resumen de inventario
    response = client.get("/api/v1/inventario/resumen/")
    assert response.status_code == 200
    resumen = response.json()
    
    print(f"\n📋 Resumen del inventario:")
    print(f"• Total productos: {resumen['total_productos']}")
    print(f"• Valor total inventario: ${resumen['valor_total_inventario']}")
    print(f"• Productos sin stock: {resumen['productos_sin_stock']}")
    print(f"• Productos con stock bajo: {resumen['productos_stock_bajo']}")
    
    # Estadísticas
    response = client.get("/api/v1/inventario/estadisticas/")
    assert response.status_code == 200
    estadisticas = response.json()
    
    print(f"\n📈 Estadísticas:")
    print(f"• Total entradas este mes: {estadisticas['total_entradas_mes']}")
    print(f"• Total salidas este mes: {estadisticas['total_salidas_mes']}")
    print(f"• Valor entradas: ${estadisticas['valor_entradas_mes']}")
    print(f"• Valor salidas: ${estadisticas['valor_salidas_mes']}")
    
    # Kardex de un producto (laptop)
    if productos_creados:
        laptop_id = productos_creados[0]["id"]
        response = client.get(f"/api/v1/inventario/kardex/{laptop_id}")
        assert response.status_code == 200
        kardex = response.json()
        
        print(f"\n💻 Kardex - Laptop Demo:")
        print(f"• Stock actual: {kardex['stock_actual']} unidades")
        print(f"• Costo promedio actual: ${kardex['costo_promedio_actual']}")
        print(f"• Valor inventario: ${kardex['valor_inventario']}")
        print(f"• Total movimientos: {kardex['total_movimientos']}")
    
    print(f"\n🎉 === DATOS DEMO CREADOS EXITOSAMENTE ===")
    print(f"📊 Resumen:")
    print(f"   • {len(usuarios_creados)} usuarios registrados")
    print(f"   • {len(productos_creados)} productos en catálogo")
    print(f"   • {movimientos_creados} movimientos de inventario")
    print(f"   • ${resumen['valor_total_inventario']} en valor total")
    print(f"   • Sistema funcionando con PostgreSQL")


if __name__ == "__main__":
    # Ejecutar directamente
    pytest.main([__file__ + "::test_populate_demo_data", "-v", "-s"]) 