#!/usr/bin/env python3
"""
Script para probar el funcionamiento de la exportación a Excel.
"""

import requests
import json

def test_excel_export():
    """Prueba la funcionalidad de exportación a Excel."""

    base_url = "http://localhost:8000"

    print("🧪 Probando exportación a Excel...")

    # 1. Login
    print("\n1️⃣ Autenticando usuario...")
    login_response = requests.post(f"{base_url}/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "admin123"
    })

    if login_response.status_code != 200:
        print(f"❌ Error en login: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return

    token = login_response.json()["access_token"]
    print("✅ Login exitoso")

    # 2. Headers con token y tenant context
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Local-ID": "aaaaaaaa-bbbb-cccc-dddd-000000000002"  # ID del local creado
    }

    print("\n2️⃣ Configurando headers:")
    print(f"   Authorization: Bearer {token[:20]}...")
    print(f"   X-Local-ID: {headers['X-Local-ID']}")

    # 3. Probar endpoint de user info
    print("\n3️⃣ Verificando información de usuario...")
    me_response = requests.get(f"{base_url}/api/v1/auth/me", headers=headers)
    if me_response.status_code == 200:
        user_info = me_response.json()
        print(f"✅ Usuario: {user_info['nombre']} ({user_info['email']})")
        print(f"   Tienda ID: {user_info.get('tienda_id', 'No asignada')}")
        print(f"   Local Principal ID: {user_info.get('local_principal_id', 'No asignado')}")
    else:
        print(f"❌ Error al obtener usuario: {me_response.status_code}")
        print(f"Response: {me_response.text}")
        return

    # 4. Probar exportación de movimientos
    print("\n4️⃣ Probando exportación de movimientos a Excel...")

    export_url = f"{base_url}/api/v1/inventario/movimientos/export/excel?limit=10"
    export_response = requests.get(export_url, headers=headers)

    print(f"Status Code: {export_response.status_code}")
    print(f"Headers: {dict(export_response.headers)}")

    if export_response.status_code == 200:
        print("✅ ¡Exportación exitosa!")

        # Verificar tipo de contenido
        content_type = export_response.headers.get('content-type', '')
        print(f"Content-Type: {content_type}")

        if 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type:
            print("📊 Archivo Excel válido recibido")

            # Guardar archivo para verificación
            with open('test_export.xlsx', 'wb') as f:
                f.write(export_response.content)
            print(f"💾 Archivo guardado como 'test_export.xlsx' ({len(export_response.content)} bytes)")
        else:
            print("⚠️ Tipo de contenido inesperado")

    else:
        print(f"❌ Error en exportación: {export_response.status_code}")
        print(f"Response: {export_response.text}")

        # Intentar decodificar error JSON
        try:
            error_detail = export_response.json()
            print(f"Error detail: {json.dumps(error_detail, indent=2)}")
        except:
            pass

    # 5. Probar sin headers de tenant context
    print("\n5️⃣ Probando sin header X-Local-ID...")
    headers_no_local = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    export_response_no_local = requests.get(export_url, headers=headers_no_local)
    print(f"Status Code (sin X-Local-ID): {export_response_no_local.status_code}")

    if export_response_no_local.status_code != 200:
        print(f"Response: {export_response_no_local.text}")
    else:
        print("✅ También funciona sin X-Local-ID (vista unificada)")

if __name__ == "__main__":
    test_excel_export()