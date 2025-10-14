#!/usr/bin/env python3
"""
Test completo de la funcionalidad de auto-selección de locales.
"""

import requests
import json

def test_auto_selection_flow():
    """Prueba completa del flujo de auto-selección."""

    base_url = "http://localhost:8000"

    print("🧪 PRUEBA COMPLETA: Auto-selección de locales")
    print("=" * 60)

    # 1. Login
    print("\n1️⃣ AUTENTICACIÓN")
    print("-" * 30)
    login_response = requests.post(f"{base_url}/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "admin123"
    })

    if login_response.status_code != 200:
        print(f"❌ Error en login: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False

    token = login_response.json()["access_token"]
    print("✅ Login exitoso")

    # Headers base
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 2. Verificar información del usuario
    print("\n2️⃣ INFORMACIÓN DEL USUARIO")
    print("-" * 35)
    me_response = requests.get(f"{base_url}/api/v1/auth/me", headers=headers)
    if me_response.status_code == 200:
        user_info = me_response.json()
        print(f"✅ Usuario: {user_info['nombre']}")
        print(f"   Email: {user_info['email']}")
        print(f"   Rol: {user_info['rol']}")
        print(f"   Tienda ID: {user_info.get('tienda_id', 'No asignada')}")
    else:
        print(f"❌ Error obteniendo usuario: {me_response.status_code}")
        return False

    # 3. Probar nuevo endpoint de información de locales
    print("\n3️⃣ INFORMACIÓN DE LOCALES (AUTO-SELECCIÓN)")
    print("-" * 50)
    locales_info_response = requests.get(f"{base_url}/api/v1/tenant-context/locales-info", headers=headers)

    if locales_info_response.status_code != 200:
        print(f"❌ Error obteniendo info de locales: {locales_info_response.status_code}")
        print(f"Response: {locales_info_response.text}")
        return False

    locales_info = locales_info_response.json()
    print(f"📊 Información de locales:")
    print(f"   Total locales: {locales_info.get('total_locales', 0)}")
    print(f"   Debe auto-seleccionar: {locales_info.get('should_auto_select', False)}")
    print(f"   Requiere selección manual: {locales_info.get('requires_manual_selection', False)}")

    if locales_info.get('auto_select_local_id'):
        print(f"   Local auto-seleccionado: {locales_info.get('auto_select_local_name')} ({locales_info.get('auto_select_local_id')})")

    # 4. Probar selección de local
    print("\n4️⃣ SELECCIÓN DE LOCAL")
    print("-" * 30)

    if locales_info.get('should_auto_select') and locales_info.get('auto_select_local_id'):
        # Auto-selección
        print("🎯 Probando auto-selección...")
        select_request = {
            "local_id": locales_info['auto_select_local_id']
        }

        select_response = requests.post(
            f"{base_url}/api/v1/tenant-context/select-local",
            json=select_request,
            headers=headers
        )

        if select_response.status_code == 200:
            context = select_response.json()
            print("✅ Auto-selección exitosa")
            print(f"   Tienda: {context.get('tienda_nombre')} ({context.get('tienda_codigo')})")
            print(f"   Local: {context.get('local_nombre')} ({context.get('local_codigo')})")

            # Headers con contexto local
            headers['X-Local-ID'] = locales_info['auto_select_local_id']

        else:
            print(f"❌ Error en auto-selección: {select_response.status_code}")
            print(f"Response: {select_response.text}")
            return False
    else:
        print("📋 Este usuario requiere selección manual de local")

    # 5. Probar contexto actual
    print("\n5️⃣ VERIFICACIÓN DE CONTEXTO ACTUAL")
    print("-" * 40)

    current_context_response = requests.get(f"{base_url}/api/v1/tenant-context/current", headers=headers)

    if current_context_response.status_code == 200:
        current_context = current_context_response.json()
        print("✅ Contexto actual obtenido:")
        print(f"   Tienda: {current_context.get('tienda_nombre')}")
        print(f"   Local: {current_context.get('local_nombre') or 'Vista completa'}")
        print(f"   Tiene contexto local: {current_context.get('tiene_contexto_local')}")
        print(f"   Permisos: {current_context.get('permisos_disponibles', [])}")
    else:
        print(f"❌ Error obteniendo contexto: {current_context_response.status_code}")

    # 6. Probar persistencia con llamadas a otros endpoints
    print("\n6️⃣ VERIFICACIÓN DE PERSISTENCIA")
    print("-" * 35)

    # Probar endpoint de productos (debe usar el contexto)
    products_response = requests.get(f"{base_url}/api/v1/products/?limit=5", headers=headers)
    print(f"   Productos API: {products_response.status_code} ({'✅' if products_response.status_code == 200 else '❌'})")

    # Probar endpoint de movimientos
    movements_response = requests.get(f"{base_url}/api/v1/inventario/movimientos/?limit=5", headers=headers)
    print(f"   Movimientos API: {movements_response.status_code} ({'✅' if movements_response.status_code == 200 else '❌'})")

    # Probar exportación Excel (el caso original reportado)
    excel_response = requests.get(f"{base_url}/api/v1/inventario/movimientos/export/excel?limit=5", headers=headers)
    print(f"   Excel Export API: {excel_response.status_code} ({'✅' if excel_response.status_code == 200 else '❌'})")

    if excel_response.status_code == 200:
        print(f"     Tamaño archivo: {len(excel_response.content)} bytes")

    # 7. Resumen final
    print("\n" + "=" * 60)
    print("🎉 RESUMEN DE LA PRUEBA")
    print("=" * 60)

    success_checks = [
        login_response.status_code == 200,
        locales_info_response.status_code == 200,
        current_context_response.status_code == 200,
        products_response.status_code == 200,
        movements_response.status_code == 200,
        excel_response.status_code == 200
    ]

    total_checks = len(success_checks)
    passed_checks = sum(success_checks)

    print(f"✅ Pruebas exitosas: {passed_checks}/{total_checks}")

    if passed_checks == total_checks:
        print("🎊 ¡TODAS LAS PRUEBAS PASARON!")
        print("   - Auto-selección funcionando correctamente")
        print("   - Contexto persistente en todas las APIs")
        print("   - Exportación Excel funcionando")
        return True
    else:
        print("⚠️  Algunas pruebas fallaron")
        return False

if __name__ == "__main__":
    try:
        result = test_auto_selection_flow()
        exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {str(e)}")
        exit(1)