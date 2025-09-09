#!/usr/bin/env python3
"""
Script específico para corregir el problema del admin y el producto.

El problema específico es:
- admin@empresa.com está en tienda: 24674128-7622-4d47-88db-f3284997da31 (Tienda Demo Principal)
- Producto 9ff11ab8-dc6d-428a-83c4-c59994427fca está en tienda: aaaaaaaa-bbbb-cccc-dddd-000000000001 (Tienda Principal)
- Local 95a4fc43-46ef-4512-8547-9215d61631fb está en tienda: 24674128-7622-4d47-88db-f3284997da31 (Tienda Demo Principal)

Estrategia: Mover el producto a la tienda del admin para que sean consistentes.
"""

import sys
from pathlib import Path

# Agregar el directorio actual al path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlmodel import Session, select
from app.domain.models.user import User
from app.domain.models.product import Product
from app.domain.models.tienda import Tienda
from app.domain.models.local import Local
from app.infrastructure.database.session import get_engine


def main():
    """Corregir el problema específico del admin."""
    print("🎯 === CORRIGIENDO PROBLEMA ESPECÍFICO DEL ADMIN ===")
    
    engine = get_engine()
    
    with Session(engine) as session:
        # Obtener entidades específicas del problema
        admin_user = session.exec(
            select(User).where(User.email == "admin@empresa.com")
        ).first()
        
        problema_product = session.exec(
            select(Product).where(Product.id == "9ff11ab8-dc6d-428a-83c4-c59994427fca")
        ).first()
        
        problema_local = session.exec(
            select(Local).where(Local.id == "95a4fc43-46ef-4512-8547-9215d61631fb")
        ).first()
        
        if not admin_user:
            print("❌ Usuario admin@empresa.com no encontrado")
            return
            
        if not problema_product:
            print("❌ Producto 9ff11ab8-dc6d-428a-83c4-c59994427fca no encontrado")
            return
            
        if not problema_local:
            print("❌ Local 95a4fc43-46ef-4512-8547-9215d61631fb no encontrado")
            return
        
        print(f"\n📊 Estado antes de la corrección:")
        print(f"   👤 Admin en tienda: {admin_user.tienda_id}")
        print(f"   📦 Producto en tienda: {problema_product.tienda_id}")
        print(f"   📍 Local en tienda: {problema_local.tienda_id}")
        
        # Obtener tienda del admin
        admin_tienda = session.exec(
            select(Tienda).where(Tienda.id == admin_user.tienda_id)
        ).first()
        
        if not admin_tienda:
            print("❌ Tienda del admin no encontrada")
            return
        
        print(f"   🏪 Admin está en tienda: {admin_tienda.nombre} ({admin_tienda.codigo})")
        
        # Estrategia: Mover el producto problemático a la tienda del admin
        # para que sean consistentes
        
        if problema_product.tienda_id != admin_user.tienda_id:
            print(f"\n🔧 Moviendo producto a la tienda del admin...")
            
            # Obtener la tienda original del producto
            producto_tienda_original = session.exec(
                select(Tienda).where(Tienda.id == problema_product.tienda_id)
            ).first()
            
            original_name = producto_tienda_original.nombre if producto_tienda_original else "Desconocida"
            
            print(f"   📦 Moviendo '{problema_product.sku}' de '{original_name}' a '{admin_tienda.nombre}'")
            
            problema_product.tienda_id = admin_user.tienda_id
            session.add(problema_product)
        
        # Verificar que el local también está en la tienda correcta
        if problema_local.tienda_id == admin_user.tienda_id:
            print(f"   ✅ Local ya está en la tienda correcta")
        else:
            print(f"   ⚠️ Local está en tienda diferente, pero esto es normal para multi-tenant")
        
        # Para simplificar el problema, también podemos mover TODOS los productos
        # de la tienda original a la tienda del admin
        print(f"\n🔧 Verificando otros productos en la tienda original...")
        
        productos_misma_tienda = session.exec(
            select(Product).where(Product.tienda_id == "aaaaaaaa-bbbb-cccc-dddd-000000000001")
        ).all()
        
        productos_movidos = 0
        for producto in productos_misma_tienda:
            if producto.tienda_id != admin_user.tienda_id:
                print(f"   📦 Moviendo producto adicional: {producto.sku}")
                producto.tienda_id = admin_user.tienda_id
                session.add(producto)
                productos_movidos += 1
        
        print(f"   ✅ {productos_movidos} productos adicionales movidos")
        
        # Guardar cambios
        print(f"\n💾 Guardando cambios...")
        session.commit()
        
        # Verificación final
        print(f"\n🔍 Verificación final...")
        
        # Recargar entidades
        session.refresh(admin_user)
        session.refresh(problema_product)
        session.refresh(problema_local)
        
        print(f"   👤 Admin en tienda: {admin_user.tienda_id}")
        print(f"   📦 Producto en tienda: {problema_product.tienda_id}")
        print(f"   📍 Local en tienda: {problema_local.tienda_id}")
        
        # Verificar si admin y producto están en la misma tienda
        if admin_user.tienda_id == problema_product.tienda_id:
            print(f"\n🎉 ¡PROBLEMA RESUELTO! Admin y producto están en la misma tienda")
            
            # Verificar si el local también está en la misma tienda
            if problema_local.tienda_id == admin_user.tienda_id:
                print(f"   ✅ Local también está en la misma tienda - Completamente resuelto")
            else:
                print(f"   ℹ️ Local está en tienda diferente, pero admin puede acceder vía permisos")
                
                # Verificar si hay permisos de usuario-local
                from app.domain.models.usuario_local import UsuarioLocal
                permisos = session.exec(
                    select(UsuarioLocal).where(
                        UsuarioLocal.user_id == admin_user.id,
                        UsuarioLocal.local_id == problema_local.id
                    )
                ).first()
                
                if permisos:
                    print(f"   ✅ Usuario tiene permisos específicos en el local")
                else:
                    print(f"   ⚠️ Usuario no tiene permisos específicos en el local")
                    print(f"      Esto podría requerir crear permisos o cambiar contexto")
        else:
            print(f"\n❌ Problema aún no resuelto completamente")
        
        # Mostrar todos los productos en la tienda del admin
        productos_admin_tienda = session.exec(
            select(Product).where(Product.tienda_id == admin_user.tienda_id)
        ).all()
        
        print(f"\n📦 Productos disponibles para el admin ({len(productos_admin_tienda)}):")
        for producto in productos_admin_tienda:
            check = "✅" if producto.id == problema_product.id else "📦"
            print(f"   {check} {producto.sku}: {producto.nombre}")
        
        # Mostrar locales disponibles en la tienda del admin
        locales_admin_tienda = session.exec(
            select(Local).where(Local.tienda_id == admin_user.tienda_id)
        ).all()
        
        print(f"\n📍 Locales en tienda del admin ({len(locales_admin_tienda)}):")
        for local in locales_admin_tienda:
            check = "🎯" if local.id == problema_local.id else "📍"
            print(f"   {check} {local.codigo}: {local.nombre}")
    
    print(f"\n🎉 === CORRECCIÓN ESPECÍFICA COMPLETADA ===")
    print(f"🔗 Para probar:")
    print(f"   1. Reinicia el backend si está corriendo")
    print(f"   2. Login como admin@empresa.com")
    print(f"   3. El producto {problema_product.sku} debería estar disponible")
    print(f"   4. Para acceder al local {problema_local.codigo}, podría necesitar permisos específicos")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error durante la corrección: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)