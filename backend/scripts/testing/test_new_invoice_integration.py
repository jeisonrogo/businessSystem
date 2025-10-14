#!/usr/bin/env python3
"""
Test script to create a new invoice and verify inventory integration works
"""

import requests
import json

def test_new_invoice_integration():
    """Test creating a new invoice and verifying inventory movements are created."""
    base_url = "http://localhost:8000/api/v1"
    
    # Use a fresh auth token
    auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2ZDM5OTJmMC1mZjdiLTQ5YmMtODZiZS1hMTk4NDkxOWQ0ZDUiLCJlbWFpbCI6ImFkbWluQGRlbW9wcmluY2lwYWwuY29tIiwibm9tYnJlIjoiYWRtaW4gZGVtbyBwcmluY2lwYWwiLCJyb2wiOiJhZG1pbmlzdHJhZG9yIiwiaXNfYWN0aXZlIjp0cnVlLCJleHAiOjE3NTYwNTY5NzB9.aVtj2RFiWmc0ceAReMxpdHe63ZcFbaIQx8DBwkZj8jM"
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    # First, check inventory movements count before
    print("🔍 Checking inventory movements before invoice creation...")
    response = requests.get(f"{base_url}/inventario/movimientos/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        movements_before = data['total']
        print(f"   Total movements before: {movements_before}")
    else:
        print(f"   ❌ Error getting movements: {response.status_code}")
        return
    
    # Create a new invoice
    print("\n📄 Creating new invoice...")
    
    invoice_data = {
        "cliente_id": "95c4b5e9-72c5-42a5-94a8-f4fad7116366",  # prueba@empresa.com client
        "tipo_factura": "VENTA",
        "fecha_emision": "2025-08-24",
        "observaciones": "Test invoice for inventory integration verification",
        "detalles": [
            {
                "producto_id": "b825b9cc-f009-46e9-8e57-54c89ba5826e",  # cables de red
                "cantidad": 2,
                "precio_unitario": "55000.00",
                "descripcion_producto": "cables de red ",
                "codigo_producto": "demo-prueba"
            }
        ]
    }
    
    response = requests.post(f"{base_url}/facturas/", headers=headers, json=invoice_data)
    
    if response.status_code == 201:
        invoice = response.json()
        print(f"   ✅ Invoice created successfully!")
        print(f"   Invoice number: {invoice['numero_factura']}")
        print(f"   Total: ${invoice['total_factura']}")
    else:
        print(f"   ❌ Error creating invoice: {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    # Check inventory movements count after
    print("\n🔍 Checking inventory movements after invoice creation...")
    response = requests.get(f"{base_url}/inventario/movimientos/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        movements_after = data['total']
        print(f"   Total movements after: {movements_after}")
        print(f"   New movements created: {movements_after - movements_before}")
        
        if movements_after > movements_before:
            print("   ✅ Inventory integration is working correctly!")
            
            # Show the latest movement
            latest_movement = data['movimientos'][0]
            print(f"   Latest movement:")
            print(f"   - Type: {latest_movement['tipo_movimiento']}")
            print(f"   - Product: {latest_movement['producto_id']}")
            print(f"   - Quantity: {latest_movement['cantidad']}")
            print(f"   - Reference: {latest_movement['referencia']}")
        else:
            print("   ❌ No new movements created - integration may not be working")
    else:
        print(f"   ❌ Error getting movements after: {response.status_code}")
    
    # Check product kardex
    print(f"\n📊 Checking product kardex...")
    product_id = "b825b9cc-f009-46e9-8e57-54c89ba5826e"
    response = requests.get(f"{base_url}/inventario/kardex/{product_id}", headers=headers)
    
    if response.status_code == 200:
        kardex = response.json()
        print(f"   ✅ Kardex is working!")
        print(f"   Current stock: {kardex['stock_actual']}")
        print(f"   Average cost: ${kardex['costo_promedio_actual']}")
        print(f"   Inventory value: ${kardex['valor_inventario']}")
        print(f"   Total movements: {kardex['total_movimientos']}")
    else:
        print(f"   ❌ Error getting kardex: {response.status_code}")
        print(f"   Response: {response.text}")

if __name__ == "__main__":
    test_new_invoice_integration()