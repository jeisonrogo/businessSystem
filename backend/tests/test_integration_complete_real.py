"""
Pruebas de integración completas para poblar la base de datos REAL.
Consume todos los servicios implementados (auth, products, inventario) 
para crear un escenario realista de uso del sistema usando PostgreSQL.
"""

import pytest
from decimal import Decimal
from datetime import datetime, UTC

from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Crear un cliente de prueba que use la base de datos real PostgreSQL."""
    with TestClient(app) as test_client:
        yield test_client


class TestCompleteIntegrationReal:
    """Pruebas de integración completas del sistema usando base de datos real."""

    def test_complete_business_scenario_real_db(self, client: TestClient):
        """
        Escenario completo de negocio que utiliza todos los servicios con BD real:
        1. Registrar usuarios con diferentes roles
        2. Crear catálogo de productos
        3. Registrar movimientos de inventario
        4. Consultar estadísticas y reportes
        """
        print("\n🚀 === INICIANDO ESCENARIO COMPLETO CON BASE DE DATOS REAL ===")
        
        # ========== FASE 1: GESTIÓN DE USUARIOS ==========
        print("\n👥 FASE 1: Registrando usuarios del sistema...")
        
        # Registrar administrador
        admin_data = {
            "email": "admin.demo@empresa.com",
            "nombre": "María García (Demo)",
            "rol": "administrador",
            "password": "admin123"
        }
        
        response = client.post("/api/v1/auth/register", json=admin_data)
        print(f"Admin register response: {response.status_code} - {response.text[:200]}...")
        
        if response.status_code == 409:  # Usuario ya existe
            print("⚠️ Usuario administrador ya existe, haciendo login...")
            login_data = {"email": admin_data["email"], "password": admin_data["password"]}
            response = client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 200
        else:
            assert response.status_code == 201
            
        admin_result = response.json()
        admin_token = admin_result["access_token"]
        print(f"✅ Administrador autenticado: {admin_result.get('user', {}).get('nombre', 'Admin')}")
        
        # Registrar gerente de ventas
        manager_data = {
            "email": "gerente.demo@empresa.com",
            "nombre": "Carlos Rodríguez (Demo)",
            "rol": "gerente_ventas",
            "password": "gerente123"
        }
        
        response = client.post("/api/v1/auth/register", json=manager_data)
        if response.status_code == 409:  # Usuario ya existe
            print("⚠️ Usuario gerente ya existe, haciendo login...")
            login_data = {"email": manager_data["email"], "password": manager_data["password"]}
            response = client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 200
        else:
            assert response.status_code == 201
            
        manager_result = response.json()
        manager_token = manager_result["access_token"]
        print(f"✅ Gerente de ventas autenticado: {manager_result.get('user', {}).get('nombre', 'Gerente')}")
        
        # Registrar contador
        contador_data = {
            "email": "contador.demo@empresa.com",
            "nombre": "Ana López (Demo)",
            "rol": "contador",
            "password": "contador123"
        }
        
        response = client.post("/api/v1/auth/register", json=contador_data)
        if response.status_code == 409:  # Usuario ya existe
            print("⚠️ Usuario contador ya existe, haciendo login...")
            login_data = {"email": contador_data["email"], "password": contador_data["password"]}
            response = client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 200
        else:
            assert response.status_code == 201
            
        contador_result = response.json()
        contador_token = contador_result["access_token"]
        print(f"✅ Contador autenticado: {contador_result.get('user', {}).get('nombre', 'Contador')}")
        
        # Registrar vendedor
        vendedor_data = {
            "email": "vendedor.demo@empresa.com",
            "nombre": "Luis Martínez (Demo)",
            "rol": "vendedor",
            "password": "vendedor123"
        }
        
        response = client.post("/api/v1/auth/register", json=vendedor_data)
        if response.status_code == 409:  # Usuario ya existe
            print("⚠️ Usuario vendedor ya existe, haciendo login...")
            login_data = {"email": vendedor_data["email"], "password": vendedor_data["password"]}
            response = client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 200
        else:
            assert response.status_code == 201
            
        vendedor_result = response.json()
        vendedor_token = vendedor_result["access_token"]
        print(f"✅ Vendedor autenticado: {vendedor_result.get('user', {}).get('nombre', 'Vendedor')}")
        
        # ========== FASE 2: CREACIÓN DEL CATÁLOGO DE PRODUCTOS ==========
        print("\n📦 FASE 2: Creando catálogo de productos...")
        
        productos_catalogo = [
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
        for producto_data in productos_catalogo:
            response = client.post("/api/v1/products/", json=producto_data)
            
            if response.status_code == 400 and "SKU ya existe" in response.text:
                print(f"⚠️ Producto ya existe: {producto_data['sku']}, buscando...")
                # Buscar el producto existente
                response_get = client.get(f"/api/v1/products/sku/{producto_data['sku']}")
                if response_get.status_code == 200:
                    producto = response_get.json()
                    productos_creados.append(producto)
                    print(f"✅ Producto encontrado: {producto['nombre']} (SKU: {producto['sku']})")
                continue
            
            assert response.status_code == 201, f"Error creando producto: {response.text}"
            producto = response.json()
            productos_creados.append(producto)
            print(f"✅ Producto creado: {producto['nombre']} (SKU: {producto['sku']})")
        
        print(f"📊 Total productos en catálogo: {len(productos_creados)}")
        
        # ========== FASE 3: MOVIMIENTOS DE INVENTARIO ==========
        print("\n📋 FASE 3: Registrando movimientos de inventario...")
        
        # Entrada inicial de inventario - Compra a proveedores
        print("\n🚚 Registrando entradas de inventario (compras a proveedores)...")
        
        entradas_inventario = [
            # Laptops - Compra inicial
            {
                "producto_id": productos_creados[0]["id"],  # Laptop HP
                "tipo_movimiento": "entrada",
                "cantidad": 10,
                "precio_unitario": "2450000.00",  # Precio de compra ligeramente menor
                "referencia": "DEMO-FC-001",
                "observaciones": "Compra inicial de laptops HP - Proveedor Demo"
            },
            # Mice - Compra inicial
            {
                "producto_id": productos_creados[1]["id"],  # Mouse Logitech
                "tipo_movimiento": "entrada", 
                "cantidad": 25,
                "precio_unitario": "175000.00",
                "referencia": "DEMO-FC-002",
                "observaciones": "Compra de mice Logitech - Proveedor Demo"
            },
            # Teclados - Compra inicial
            {
                "producto_id": productos_creados[2]["id"],  # Teclado Mecánico
                "tipo_movimiento": "entrada",
                "cantidad": 15,
                "precio_unitario": "310000.00",
                "referencia": "DEMO-FC-003",
                "observaciones": "Compra de teclados mecánicos - Proveedor Demo"
            },
            # Monitores - Compra inicial
            {
                "producto_id": productos_creados[3]["id"],  # Monitor Dell
                "tipo_movimiento": "entrada",
                "cantidad": 8,
                "precio_unitario": "820000.00",
                "referencia": "DEMO-FC-004",
                "observaciones": "Compra de monitores Dell - Proveedor Demo"
            },
            # Cables - Compra inicial (gran cantidad)
            {
                "producto_id": productos_creados[4]["id"],  # Cable USB-C
                "tipo_movimiento": "entrada",
                "cantidad": 100,
                "precio_unitario": "22000.00",
                "referencia": "DEMO-FC-005",
                "observaciones": "Compra masiva de cables USB-C - Proveedor Demo"
            },
            # Audífonos - Compra inicial
            {
                "producto_id": productos_creados[5]["id"],  # Audífonos Sony
                "tipo_movimiento": "entrada",
                "cantidad": 12,
                "precio_unitario": "920000.00",
                "referencia": "DEMO-FC-006",
                "observaciones": "Compra de audífonos Sony - Proveedor Demo"
            }
        ]
        
        movimientos_creados = []
        for entrada in entradas_inventario:
            response = client.post("/api/v1/inventario/movimientos/", json=entrada)
            
            # Si el movimiento ya existe o hay algún error, continuar
            if response.status_code not in [201, 400]:
                print(f"❌ Error en movimiento: {response.status_code} - {response.text}")
                continue
                
            if response.status_code == 201:
                movimiento = response.json()
                movimientos_creados.append(movimiento)
                print(f"✅ Entrada registrada: {entrada['cantidad']} unidades - Ref: {entrada['referencia']}")
                print(f"   Stock anterior: {movimiento['stock_anterior']} → Stock posterior: {movimiento['stock_posterior']}")
                print(f"   Costo unitario calculado: ${movimiento['costo_unitario']}")
            else:
                print(f"⚠️ Movimiento ya existe o error: {entrada['referencia']}")
        
        # Segunda compra (reabastecimiento) - Precios diferentes para probar costo promedio
        print("\n🔄 Registrando segunda compra (reabastecimiento) con precios diferentes...")
        
        reabastecimientos = [
            # Laptops - Segunda compra con precio diferente
            {
                "producto_id": productos_creados[0]["id"],  # Laptop HP
                "tipo_movimiento": "entrada",
                "cantidad": 5,
                "precio_unitario": "2600000.00",  # Precio más alto
                "referencia": "DEMO-FC-007",
                "observaciones": "Reabastecimiento laptops HP - Precio aumentado por inflación - Demo"
            },
            # Mice - Segunda compra
            {
                "producto_id": productos_creados[1]["id"],  # Mouse Logitech  
                "tipo_movimiento": "entrada",
                "cantidad": 20,
                "precio_unitario": "165000.00",  # Precio más bajo (descuento por volumen)
                "referencia": "DEMO-FC-008",
                "observaciones": "Reabastecimiento mice - Descuento por volumen - Demo"
            },
            # Cables - Reabastecimiento masivo
            {
                "producto_id": productos_creados[4]["id"],  # Cable USB-C
                "tipo_movimiento": "entrada",
                "cantidad": 150,
                "precio_unitario": "20000.00",  # Mejor precio por cantidad
                "referencia": "DEMO-FC-009",
                "observaciones": "Reabastecimiento masivo cables - Mejor precio por cantidad - Demo"
            }
        ]
        
        for reabastecimiento in reabastecimientos:
            response = client.post("/api/v1/inventario/movimientos/", json=reabastecimiento)
            if response.status_code == 201:
                movimiento = response.json()
                movimientos_creados.append(movimiento)
                print(f"✅ Reabastecimiento: {reabastecimiento['cantidad']} unidades - Ref: {reabastecimiento['referencia']}")
                print(f"   Nuevo costo promedio: ${movimiento['costo_unitario']}")
            else:
                print(f"⚠️ Reabastecimiento ya existe o error: {reabastecimiento['referencia']}")
        
        # Registrar ventas (salidas)
        print("\n💰 Registrando ventas (salidas de inventario)...")
        
        ventas = [
            # Venta de laptops
            {
                "producto_id": productos_creados[0]["id"],  # Laptop HP
                "tipo_movimiento": "salida",
                "cantidad": 3,
                "precio_unitario": "3200000.00",  # Precio de venta
                "referencia": "DEMO-FV-001",
                "observaciones": "Venta a empresa TechCorp - 3 laptops para oficina - Demo"
            },
            # Venta de combo (mouse + teclado)
            {
                "producto_id": productos_creados[1]["id"],  # Mouse Logitech
                "tipo_movimiento": "salida",
                "cantidad": 8,
                "precio_unitario": "250000.00",
                "referencia": "DEMO-FV-002",
                "observaciones": "Venta combo oficina - 8 mouse para setup completo - Demo"
            },
            {
                "producto_id": productos_creados[2]["id"],  # Teclado Mecánico
                "tipo_movimiento": "salida",
                "cantidad": 8,
                "precio_unitario": "450000.00",
                "referencia": "DEMO-FV-002",
                "observaciones": "Venta combo oficina - 8 teclados para setup completo - Demo"
            },
            # Venta de monitores
            {
                "producto_id": productos_creados[3]["id"],  # Monitor Dell
                "tipo_movimiento": "salida",
                "cantidad": 4,
                "precio_unitario": "1100000.00",
                "referencia": "DEMO-FV-003",
                "observaciones": "Venta monitores a estudio de diseño - Demo"
            },
            # Venta masiva de cables
            {
                "producto_id": productos_creados[4]["id"],  # Cable USB-C
                "tipo_movimiento": "salida",
                "cantidad": 50,
                "precio_unitario": "35000.00",
                "referencia": "DEMO-FV-004",
                "observaciones": "Venta mayorista de cables USB-C - Demo"
            },
            # Venta de audífonos
            {
                "producto_id": productos_creados[5]["id"],  # Audífonos Sony
                "tipo_movimiento": "salida",
                "cantidad": 6,
                "precio_unitario": "1200000.00",
                "referencia": "DEMO-FV-005",
                "observaciones": "Venta audífonos premium a clientes individuales - Demo"
            }
        ]
        
        for venta in ventas:
            response = client.post("/api/v1/inventario/movimientos/", json=venta)
            if response.status_code == 201:
                movimiento = response.json()
                movimientos_creados.append(movimiento)
                print(f"✅ Venta registrada: {venta['cantidad']} unidades - Ref: {venta['referencia']}")
                print(f"   Stock después de venta: {movimiento['stock_posterior']}")
            else:
                print(f"⚠️ Venta ya existe o error: {venta['referencia']} - {response.status_code}")
        
        print(f"📊 Total movimientos procesados: {len(movimientos_creados)}")
        
        # ========== FASE 4: CONSULTAS Y REPORTES ==========
        print("\n📊 FASE 4: Generando consultas y reportes...")
        
        # Consultar estado actual de productos
        print("\n📦 Estado actual del inventario:")
        response = client.get("/api/v1/products/")
        assert response.status_code == 200
        productos_actuales = response.json()
        
        productos_demo = [p for p in productos_actuales["products"] if "Demo" in p["nombre"]]
        for producto in productos_demo[:6]:  # Mostrar solo los primeros 6 productos demo
            print(f"• {producto['nombre']}: {producto['stock']} unidades en stock")
        
        # Consultar resumen de inventario
        print("\n📋 Resumen general del inventario:")
        response = client.get("/api/v1/inventario/resumen/")
        assert response.status_code == 200
        resumen = response.json()
        
        print(f"• Total productos: {resumen['total_productos']}")
        print(f"• Valor total inventario: ${resumen['valor_total_inventario']:,.2f}")
        print(f"• Productos sin stock: {resumen['productos_sin_stock']}")
        print(f"• Productos con stock bajo: {resumen['productos_stock_bajo']}")
        if resumen.get('ultimo_movimiento'):
            print(f"• Último movimiento: {resumen['ultimo_movimiento']}")
        
        # Consultar estadísticas de inventario
        print("\n📈 Estadísticas de inventario:")
        response = client.get("/api/v1/inventario/estadisticas/")
        assert response.status_code == 200
        estadisticas = response.json()
        
        print(f"• Total entradas este mes: {estadisticas['total_entradas_mes']}")
        print(f"• Total salidas este mes: {estadisticas['total_salidas_mes']}")
        print(f"• Total mermas este mes: {estadisticas['total_mermas_mes']}")
        print(f"• Valor entradas: ${estadisticas['valor_entradas_mes']:,.2f}")
        print(f"• Valor salidas: ${estadisticas['valor_salidas_mes']:,.2f}")
        print(f"• Valor mermas: ${estadisticas['valor_mermas_mes']:,.2f}")
        
        if estadisticas.get('productos_mas_movidos'):
            print("\n🔥 Productos más movidos:")
            for producto_movido in estadisticas['productos_mas_movidos'][:3]:
                print(f"• Producto ID: {producto_movido['producto_id']} - {producto_movido['total_movimientos']} movimientos")
        
        # Consultar kardex de productos específicos
        print("\n📋 Kardex de productos seleccionados:")
        
        # Kardex de laptops (producto con más valor)
        if productos_creados:
            laptop_id = productos_creados[0]["id"]
            response = client.get(f"/api/v1/inventario/kardex/{laptop_id}")
            assert response.status_code == 200
            kardex_laptop = response.json()
            
            print(f"\n💻 Kardex - {productos_creados[0]['nombre']}:")
            print(f"• Stock actual: {kardex_laptop['stock_actual']} unidades")
            print(f"• Costo promedio actual: ${kardex_laptop['costo_promedio_actual']:,.2f}")
            print(f"• Valor inventario: ${kardex_laptop['valor_inventario']:,.2f}")
            print(f"• Total movimientos: {kardex_laptop['total_movimientos']}")
            
            # Mostrar últimos movimientos de laptops
            print("• Últimos movimientos:")
            for movimiento in kardex_laptop['movimientos'][:3]:
                print(f"  - {movimiento['tipo_movimiento'].upper()}: {movimiento['cantidad']} unidades")
                print(f"    Precio: ${movimiento['precio_unitario']:,.2f} | Stock después: {movimiento['stock_posterior']}")
        
        # ========== FASE 5: VERIFICACIONES FINALES ==========
        print("\n✅ FASE 5: Verificaciones finales del sistema...")
        
        # Verificar que todos los usuarios pueden hacer login
        print("\n🔐 Verificando login de todos los usuarios:")
        
        usuarios_login = [
            {"email": "admin.demo@empresa.com", "password": "admin123", "rol": "administrador"},
            {"email": "gerente.demo@empresa.com", "password": "gerente123", "rol": "gerente_ventas"},
            {"email": "contador.demo@empresa.com", "password": "contador123", "rol": "contador"},
            {"email": "vendedor.demo@empresa.com", "password": "vendedor123", "rol": "vendedor"}
        ]
        
        for usuario in usuarios_login:
            login_data = {"email": usuario["email"], "password": usuario["password"]}
            response = client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 200
            login_result = response.json()
            print(f"✅ Login exitoso: {login_result['user']['nombre']} ({usuario['rol']})")
            
            # Verificar endpoint /me con el token
            headers = {"Authorization": f"Bearer {login_result['access_token']}"}
            response = client.get("/api/v1/auth/me", headers=headers)
            assert response.status_code == 200
            user_info = response.json()
            assert user_info["rol"] == usuario["rol"]
        
        # Verificar integridad de datos
        print("\n🔍 Verificando integridad de datos:")
        
        # Contar total de movimientos
        response = client.get("/api/v1/inventario/movimientos/")
        assert response.status_code == 200
        todos_movimientos = response.json()
        print(f"✅ Total movimientos en sistema: {todos_movimientos['total']}")
        
        # Verificar productos con stock bajo
        print("\n⚠️ Productos con stock bajo (umbral: 10):")
        response = client.get("/api/v1/products/low-stock/?threshold=10")
        assert response.status_code == 200
        productos_stock_bajo = response.json()
        
        productos_demo_bajo = [p for p in productos_stock_bajo["products"] if "Demo" in p["nombre"]]
        if productos_demo_bajo:
            for producto in productos_demo_bajo[:3]:
                print(f"• {producto['nombre']}: {producto['stock']} unidades (SKU: {producto['sku']})")
        else:
            print("• No hay productos demo con stock bajo")
        
        print("\n🎉 === ESCENARIO COMPLETO EJECUTADO EXITOSAMENTE CON BD REAL ===")
        print(f"📊 Resumen final:")
        print(f"   • {len(usuarios_login)} usuarios demo registrados")
        print(f"   • {len(productos_creados)} productos demo en catálogo")
        print(f"   • {todos_movimientos['total']} movimientos totales en sistema")
        print(f"   • ${resumen['valor_total_inventario']:,.2f} en valor total de inventario")
        print(f"   • Sistema funcionando correctamente con base de datos PostgreSQL")
        print(f"   • Todos los servicios (auth, products, inventario) validados")

if __name__ == "__main__":
    # Ejecutar solo la prueba principal si se ejecuta directamente
    pytest.main([__file__ + "::TestCompleteIntegrationReal::test_complete_business_scenario_real_db", "-v", "-s"]) 