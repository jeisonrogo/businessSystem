#!/usr/bin/env python3
"""
Test script para probar la creación de productos con auto-creación de stock inicial
"""

import requests
import json
from uuid import UUID

def test_product_creation():
    """Test de creación de producto con contexto local."""
    
    print("🧪 Testing product creation with automatic initial stock...")
    
    # Configuración
    base_url = "http://localhost:8000"
    
    # Obtener token de autenticación (usuario admin)
    login_data = {
        "email": "admin@inventario.com",
        "password": "admin123"
    }
    
    print("🔐 Getting authentication token...")
    login_response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    print(f"✅ Token obtained successfully")
    
    # Headers con autenticación y contexto local
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Local-ID": "95a4fc43-46ef-4512-8547-9215d61631fb",  # Sucursal Centro
        "X-Tienda-ID": "24674128-7622-4d47-88db-f3284997da31"   # Tienda Demo Principal
    }
    
    # Datos del nuevo producto de prueba
    product_data = {
        "sku": "TEST-001",
        "nombre": "Producto de Prueba",
        "descripcion": "Producto creado para probar la auto-creación de stock",
        "precio_base": 5000.00,
        "precio_publico": 8000.00
    }
    
    print(f"📦 Creating product with SKU: {product_data['sku']}")
    print(f"   Context: Sucursal Centro")
    
    # Crear producto
    create_response = requests.post(
        f"{base_url}/api/v1/products/",
        headers=headers,
        json=product_data
    )
    
    if create_response.status_code == 201:
        created_product = create_response.json()
        product_id = created_product["id"]
        
        print(f"✅ Product created successfully!")
        print(f"   Product ID: {product_id}")
        print(f"   SKU: {created_product['sku']}")
        print(f"   Name: {created_product['nombre']}")
        
        # Verificar que el producto aparece en la lista de productos del local
        print(f"\n📋 Checking if product appears in local product list...")
        
        list_response = requests.get(
            f"{base_url}/api/v1/products/",
            headers=headers,
            params={"page": 1, "limit": 100}
        )
        
        if list_response.status_code == 200:
            products_data = list_response.json()
            test_product = None
            
            for product in products_data["products"]:
                if product["sku"] == "TEST-001":
                    test_product = product
                    break
            
            if test_product:
                print(f"✅ Product found in local product list!")
                print(f"   SKU: {test_product['sku']}")
                print(f"   Name: {test_product['nombre']}")
                print(f"   Stock local actual: {test_product.get('stock_local_actual', 'N/A')}")
                print(f"   Local: {test_product.get('local_nombre', 'N/A')}")
                
                # Verificar stock en base de datos
                print(f"\n📊 Verifying stock record in database...")
                
            else:
                print(f"❌ Product NOT found in local product list!")
                print(f"   Total products in list: {len(products_data['products'])}")
                print(f"   Available SKUs: {[p['sku'] for p in products_data['products'][:5]]}")
        else:
            print(f"❌ Failed to get product list: {list_response.status_code}")
            print(f"Response: {list_response.text}")
            
    else:
        print(f"❌ Product creation failed: {create_response.status_code}")
        print(f"Response: {create_response.text}")

if __name__ == "__main__":
    test_product_creation()