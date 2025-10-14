#!/usr/bin/env python3
"""
Test script to create a new invoice and verify inventory integration works with the fix
"""

import requests
import json

def test_new_invoice_with_fix():
    """Test creating a new invoice with the inventory integration fix."""
    base_url = "http://localhost:8000/api/v1"
    
    # Use fresh auth token
    auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2ZDM5OTJmMC1mZjdiLTQ5YmMtODZiZS1hMTk4NDkxOWQ0ZDUiLCJlbWFpbCI6ImFkbWluQGRlbW9wcmluY2lwYWwuY29tIiwibm9tYnJlIjoiYWRtaW4gZGVtbyBwcmluY2lwYWwiLCJyb2wiOiJhZG1pbmlzdHJhZG9yIiwiaXNfYWN0aXZlIjp0cnVlLCJleHAiOjE3NTYwNTc3NjJ9.TaJZMNCYicflPyKhVxtNxPv1Q5svk8K9Q4w8VJK1lbY"
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    # Check current stock before creating invoice
    print("🔍 Checking current stock before invoice creation...")
    product_id = "b825b9cc-f009-46e9-8e57-54c89ba5826e"
    response = requests.get(f"{base_url}/inventario/kardex/{product_id}", headers=headers)
    
    if response.status_code == 200:
        kardex_before = response.json()
        stock_before = kardex_before['stock_actual']
        movements_before = kardex_before['total_movimientos']
        print(f"   Stock before: {stock_before}")
        print(f"   Movements before: {movements_before}")
    else:
        print(f"   ❌ Error getting kardex: {response.status_code}")
        return
    
    # Create a new invoice
    print("\n📄 Creating new invoice (test for fix)...")
    
    invoice_data = {
        "cliente_id": "95c4b5e9-72c5-42a5-94a8-f4fad7116366",  # prueba@empresa.com client
        "tipo_factura": "VENTA",
        "fecha_emision": "2025-08-24",
        "observaciones": "Test invoice to verify inventory integration fix",
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
        
        # Check if invoice has local_id
        invoice_number = invoice['numero_factura']
        response = requests.get(f"{base_url}/facturas/numero/{invoice_number}", headers=headers)
        if response.status_code == 200:
            invoice_full = response.json()
            local_id = invoice_full.get('local_id')
            print(f"   Local ID: {local_id}")
    else:
        print(f"   ❌ Error creating invoice: {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    # Check if inventory movement was created
    print(f"\n📦 Checking for inventory movement...")
    invoice_number = invoice['numero_factura']
    response = requests.get(f"{base_url}/inventario/movimientos/?referencia={invoice_number}", headers=headers)
    
    if response.status_code == 200:
        movements = response.json()['movimientos']
        if movements:
            print(f"   ✅ Inventory movement created!")
            movement = movements[0]
            print(f"   - Type: {movement['tipo_movimiento']}")
            print(f"   - Quantity: {movement['cantidad']}")
            print(f"   - Stock: {movement['stock_anterior']} → {movement['stock_posterior']}")
            print(f"   - Reference: {movement['referencia']}")
        else:
            print(f"   ❌ No inventory movement found")
    else:
        print(f"   ❌ Error getting movements: {response.status_code}")
    
    # Check updated stock
    print(f"\n📊 Checking updated stock...")
    response = requests.get(f"{base_url}/inventario/kardex/{product_id}", headers=headers)
    
    if response.status_code == 200:
        kardex_after = response.json()
        stock_after = kardex_after['stock_actual']
        movements_after = kardex_after['total_movimientos']
        print(f"   Stock after: {stock_after} (changed: {stock_after - stock_before})")
        print(f"   Movements after: {movements_after} (added: {movements_after - movements_before})")
        
        if stock_after == stock_before - 2 and movements_after == movements_before + 1:
            print(f"   ✅ Inventory integration is working perfectly!")
        else:
            print(f"   ⚠️  Something might be wrong with the integration")
    else:
        print(f"   ❌ Error getting updated kardex: {response.status_code}")

if __name__ == "__main__":
    test_new_invoice_with_fix()