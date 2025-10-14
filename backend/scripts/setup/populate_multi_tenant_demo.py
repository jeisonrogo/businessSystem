#!/usr/bin/env python3
"""
Script para poblar la base de datos con datos demo multi-tenant.
Crea tiendas, locales, stock por local, transferencias y permisos.
Ejecutar desde el directorio backend:
    python populate_multi_tenant_demo.py
"""

import sys
import os
from pathlib import Path

# Agregar el directorio actual al path para importar los módulos
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """Ejecutar el script de población de datos demo multi-tenant."""
    print("🏢 Iniciando población de datos demo MULTI-TENANT...")
    print("📋 Esto creará tiendas, locales, stock por local, transferencias y permisos")
    
    # Confirmar con el usuario
    confirm = input("\n¿Desea continuar? (y/N): ").lower().strip()
    if confirm not in ['y', 'yes', 'sí', 'si']:
        print("❌ Operación cancelada")
        return
    
    # Ejecutar la prueba que pobla los datos multi-tenant
    import subprocess
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_multi_tenant_demo.py::test_populate_multi_tenant_demo", 
            "-v", "-s"
        ], check=True, capture_output=False)
        
        print("\n✅ Datos demo multi-tenant poblados exitosamente!")
        print("\n🏢 Estructura multi-tenant creada:")
        print("   • 2 tiendas demo")
        print("   • 6 locales (sucursales, almacenes, showrooms)")
        print("   • Stock independiente por local")
        print("   • 8+ transferencias entre locales")
        print("   • Permisos granulares por usuario-local")
        
        print("\n🔐 Usuarios multi-tenant:")
        print("   • admin.demo@empresa.com - Acceso a todas las tiendas")
        print("   • gerente.tienda1@empresa.com - Gerente Tienda Centro")
        print("   • vendedor.sucursal1@empresa.com - Vendedor Sucursal Principal")
        print("   • almacenista.central@empresa.com - Almacenista Central")
        
        print("\n🏪 Tiendas creadas:")
        print("   • Tienda Centro (TC-001) - 4 locales")
        print("   • Tienda Norte (TN-001) - 2 locales")
        
        print("\n📦 Locales por tienda:")
        print("   Tienda Centro:")
        print("     - Sucursal Principal (stock completo)")
        print("     - Almacén Central (stock distribuido)")
        print("     - Showroom Centro (stock limitado)")
        print("     - Local Virtual (sin stock físico)")
        print("   Tienda Norte:")
        print("     - Sucursal Norte (stock operativo)")
        print("     - Almacén Norte (stock de respaldo)")
        
        print("\n🚚 Transferencias demo:")
        print("   • Almacén Central → Sucursal Principal")
        print("   • Almacén Central → Showroom Centro")
        print("   • Sucursal Principal → Sucursal Norte")
        print("   • Estados: Pendientes, Enviadas, Recibidas")
        
        print("\n🌐 Testing multi-tenant:")
        print("   • http://localhost:8000/docs (Swagger UI)")
        print("   • Usa endpoints /tiendas/, /locales/, /stock-local/")
        print("   • Cambia contexto con /tenant-context/cambiar-contexto")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error al poblar datos multi-tenant: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Operación interrumpida por el usuario")
        sys.exit(1)

if __name__ == "__main__":
    main()