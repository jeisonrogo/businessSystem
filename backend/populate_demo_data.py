#!/usr/bin/env python3
"""
Script para poblar la base de datos con datos de demostración.
Ejecutar desde el directorio backend:
    python populate_demo_data.py
"""

import sys
import os
from pathlib import Path

# Agregar el directorio actual al path para importar los módulos
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """Ejecutar el script de población de datos demo."""
    print("🚀 Iniciando población de datos demo...")
    print("📋 Esto creará usuarios, productos y movimientos de inventario de ejemplo")
    
    # Confirmar con el usuario
    confirm = input("\n¿Desea continuar? (y/N): ").lower().strip()
    if confirm not in ['y', 'yes', 'sí', 'si']:
        print("❌ Operación cancelada")
        return
    
    # Ejecutar la prueba que pobla los datos
    import subprocess
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_demo_data.py::test_populate_demo_data", 
            "-v", "-s"
        ], check=True, capture_output=False)
        
        print("\n✅ Datos de demostración poblados exitosamente!")
        print("\n📊 Resumen de datos creados:")
        print("   • 4 usuarios con diferentes roles")
        print("   • 6 productos en el catálogo")
        print("   • ~30 movimientos de inventario")
        print("   • Valor total del inventario: >$100M")
        
        print("\n🔐 Usuarios creados:")
        print("   • admin.demo@empresa.com (admin123) - Administrador")
        print("   • gerente.demo@empresa.com (gerente123) - Gerente de Ventas")
        print("   • contador.demo@empresa.com (contador123) - Contador")
        print("   • vendedor.demo@empresa.com (vendedor123) - Vendedor")
        
        print("\n🌐 Puedes probar los endpoints en:")
        print("   • http://localhost:8000/docs (Swagger UI)")
        print("   • http://localhost:8000/redoc (ReDoc)")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error al poblar datos: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Operación interrumpida por el usuario")
        sys.exit(1)

if __name__ == "__main__":
    main() 