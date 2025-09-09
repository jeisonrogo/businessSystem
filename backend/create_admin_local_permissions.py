#!/usr/bin/env python3
"""
Script para crear permisos de usuario-local para el admin.

Esto asegura que el admin@empresa.com tenga permisos completos
en todos los locales de su tienda.
"""

import sys
from pathlib import Path

# Agregar el directorio actual al path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlmodel import Session, select
from app.domain.models.user import User
from app.domain.models.local import Local
from app.domain.models.usuario_local import UsuarioLocal
from app.infrastructure.database.session import get_engine
from uuid import uuid4


def main():
    """Crear permisos de admin en locales."""
    print("🔐 === CREANDO PERMISOS ADMIN-LOCAL ===")
    
    engine = get_engine()
    
    with Session(engine) as session:
        # Obtener admin user
        admin_user = session.exec(
            select(User).where(User.email == "admin@empresa.com")
        ).first()
        
        if not admin_user:
            print("❌ Usuario admin@empresa.com no encontrado")
            return
        
        print(f"👤 Admin encontrado: {admin_user.nombre}")
        print(f"   Tienda: {admin_user.tienda_id}")
        
        # Obtener todos los locales de la tienda del admin
        locales_admin = session.exec(
            select(Local).where(Local.tienda_id == admin_user.tienda_id)
        ).all()
        
        print(f"\n📍 Locales en tienda del admin ({len(locales_admin)}):")
        for local in locales_admin:
            print(f"   • {local.codigo}: {local.nombre}")
        
        # Verificar permisos existentes
        permisos_existentes = session.exec(
            select(UsuarioLocal).where(UsuarioLocal.user_id == admin_user.id)
        ).all()
        
        print(f"\n🔍 Permisos existentes ({len(permisos_existentes)}):")
        for permiso in permisos_existentes:
            local = next((l for l in locales_admin if l.id == permiso.local_id), None)
            local_name = local.codigo if local else "Local no encontrado"
            print(f"   • {local_name}: {permiso.es_responsable}")
        
        # Crear permisos faltantes
        permisos_creados = 0
        
        for local in locales_admin:
            # Verificar si ya existe permiso para este local
            permiso_existente = next(
                (p for p in permisos_existentes if p.local_id == local.id), 
                None
            )
            
            if permiso_existente:
                print(f"   ✅ Permiso ya existe para {local.codigo}")
                
                # Verificar si el permiso tiene todos los privilegios de admin
                if not permiso_existente.es_responsable:
                    print(f"      🔧 Actualizando permisos a responsable...")
                    permiso_existente.es_responsable = True
                    permiso_existente.puede_vender = True
                    permiso_existente.puede_ver_stock = True
                    permiso_existente.puede_transferir = True
                    permiso_existente.puede_modificar_precios = True
                    permiso_existente.puede_aplicar_descuentos = True
                    permiso_existente.puede_ver_reportes = True
                    permiso_existente.puede_gestionar_usuarios = True
                    permiso_existente.is_active = True
                    session.add(permiso_existente)
                    print(f"      ✅ Permisos actualizados para {local.codigo}")
                
                continue
            
            # Crear nuevo permiso con privilegios completos de admin
            nuevo_permiso = UsuarioLocal(
                id=uuid4(),
                user_id=admin_user.id,
                local_id=local.id,
                puede_vender=True,
                puede_ver_stock=True,
                puede_transferir=True,
                es_responsable=True,  # Admin es responsable de todos los locales
                puede_modificar_precios=True,
                puede_aplicar_descuentos=True,
                puede_ver_reportes=True,
                puede_gestionar_usuarios=True,
                limite_descuento_porcentaje=100.0,  # Sin límite para admin
                limite_credito_monto=999999999.0,   # Sin límite para admin
                is_active=True,
                created_by=admin_user.id
            )
            
            session.add(nuevo_permiso)
            permisos_creados += 1
            print(f"   ✅ Permiso creado para {local.codigo}")
        
        # Guardar cambios
        if permisos_creados > 0:
            print(f"\n💾 Guardando {permisos_creados} nuevos permisos...")
            session.commit()
        else:
            print(f"\n✅ No se requieren nuevos permisos")
        
        # Verificación final
        print(f"\n🔍 Verificación final...")
        permisos_final = session.exec(
            select(UsuarioLocal).where(
                UsuarioLocal.user_id == admin_user.id,
                UsuarioLocal.is_active == True
            )
        ).all()
        
        print(f"📊 Resumen de permisos del admin:")
        print(f"   • Total locales en tienda: {len(locales_admin)}")
        print(f"   • Permisos activos: {len(permisos_final)}")
        
        if len(permisos_final) >= len(locales_admin):
            print(f"   🎉 Admin tiene acceso completo a todos los locales")
        else:
            print(f"   ⚠️ Admin no tiene acceso a algunos locales")
        
        # Mostrar permisos específicos
        for local in locales_admin:
            permiso = next((p for p in permisos_final if p.local_id == local.id), None)
            if permiso:
                status = "🔓 Responsable" if permiso.es_responsable else "🔒 Usuario"
                print(f"   {status} {local.codigo}: {local.nombre}")
            else:
                print(f"   ❌ SIN ACCESO {local.codigo}: {local.nombre}")
    
    print(f"\n🎉 === PERMISOS ADMIN CONFIGURADOS ===")
    print(f"📋 Para probar:")
    print(f"   1. Login como admin@empresa.com")
    print(f"   2. Cambiar a local SUC001 debería funcionar")
    print(f"   3. Acceder a productos debería funcionar")
    print(f"   4. El error 'Producto no encontrado en su tienda' debería estar resuelto")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error creando permisos: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)