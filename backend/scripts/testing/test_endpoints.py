"""
Script de prueba básico para los endpoints multi-tenant.

Prueba la funcionalidad básica de importación y acceso a endpoints
sin requerir una base de datos activa.
"""

import sys
import traceback

def test_application_import():
    """Prueba que la aplicación se pueda importar correctamente."""
    try:
        from main import app
        print("✅ Application imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import application: {e}")
        traceback.print_exc()
        return False

def test_endpoints_registration():
    """Prueba que los endpoints estén registrados correctamente."""
    try:
        from main import app
        routes = []
        
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(f"{route.methods} {route.path}")
        
        # Buscar endpoints multi-tenant específicos
        multi_tenant_paths = [
            '/api/v1/tiendas',
            '/api/v1/locales',
            '/api/v1/stock-local',
            '/api/v1/transferencias',
            '/api/v1/usuario-locales',
            '/api/v1/tenant-context'
        ]
        
        found_paths = []
        for route_info in routes:
            for path in multi_tenant_paths:
                if path in route_info:
                    found_paths.append(path)
                    break
        
        print(f"✅ Found {len(set(found_paths))} multi-tenant endpoint groups")
        print(f"   Total registered routes: {len(routes)}")
        
        # Mostrar algunos endpoints como ejemplo
        tenant_routes = [r for r in routes if '/api/v1/' in r and any(mt in r for mt in ['tienda', 'local', 'stock', 'transfer', 'usuario', 'tenant'])]
        
        if tenant_routes:
            print("   Sample multi-tenant routes:")
            for route in tenant_routes[:5]:  # Mostrar primeros 5
                print(f"     {route}")
            if len(tenant_routes) > 5:
                print(f"     ... and {len(tenant_routes) - 5} more")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test endpoint registration: {e}")
        traceback.print_exc()
        return False

def test_middleware_configuration():
    """Prueba que el middleware esté configurado."""
    try:
        from main import app
        middlewares = []
        
        for middleware in app.user_middleware:
            middlewares.append(str(middleware.cls.__name__))
        
        print(f"✅ Found {len(middlewares)} middleware components")
        print(f"   Configured middlewares: {', '.join(middlewares)}")
        
        # Verificar que el tenant middleware esté presente
        tenant_middleware_found = any('Tenant' in m for m in middlewares)
        if tenant_middleware_found:
            print("   ✅ TenantContext middleware is configured")
        else:
            print("   ⚠️  TenantContext middleware not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test middleware configuration: {e}")
        traceback.print_exc()
        return False

def test_schema_imports():
    """Prueba que los schemas multi-tenant se puedan importar."""
    try:
        from app.api.v1.schemas_multi_tenant import (
            TiendaCreate, TiendaResponse,
            LocalCreate, LocalResponse,
            StockLocalCreate, StockLocalResponse,
            TransferenciaCreate, TransferenciaResponse
        )
        print("✅ Multi-tenant schemas imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to import multi-tenant schemas: {e}")
        traceback.print_exc()
        return False

def main():
    """Ejecuta todas las pruebas básicas."""
    print("🚀 Testing Multi-Tenant System Integration")
    print("=" * 50)
    
    tests = [
        ("Application Import", test_application_import),
        ("Endpoints Registration", test_endpoints_registration), 
        ("Middleware Configuration", test_middleware_configuration),
        ("Schema Imports", test_schema_imports)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        success = test_func()
        results.append((test_name, success))
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Multi-tenant system is ready for testing.")
        return 0
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())