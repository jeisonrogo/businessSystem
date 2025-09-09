#!/usr/bin/env python3
"""
Script de prueba para debuggear el endpoint /locales/disponibles
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.user_repository import SQLUserRepository
from app.infrastructure.repositories.local_repository import LocalRepository
from app.infrastructure.repositories.usuario_local_repository import UsuarioLocalRepository


def debug_locales_disponibles():
    """
    Debuggear el endpoint de locales disponibles
    """
    print("🔍 Debuggeando endpoint /locales/disponibles...")
    
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        user_repo = SQLUserRepository(session)
        local_repo = LocalRepository(session)
        usuario_local_repo = UsuarioLocalRepository(session)
        
        # Buscar usuarios desde la base de datos directamente
        from sqlmodel import select
        from app.domain.models.user import User, UserRole
        
        result = session.exec(select(User).where(User.rol == UserRole.ADMINISTRADOR))
        admin_users = list(result.all())
        
        print(f"Encontrados {len(admin_users)} administradores:")
        
        for admin in admin_users:
            print(f"\n👤 Admin: {admin.nombre} ({admin.email})")
            print(f"   Tienda ID: {admin.tienda_id}")
            
            if not admin.tienda_id:
                print("   ⚠️  Sin tienda asignada")
                continue
            
            try:
                # Probar obtener locales de la tienda
                locales_tienda = local_repo.get_by_tienda(admin.tienda_id, limit=1000)
                print(f"   🏪 Locales en tienda: {len(locales_tienda)}")
                
                for local in locales_tienda:
                    print(f"      - {local.nombre} ({local.codigo})")
                    print(f"        Dirección: {local.direccion}")
                    print(f"        Tipo dirección: {type(local.direccion)}")
                    
                    # Probar acceso a dirección
                    try:
                        if local.direccion:
                            if isinstance(local.direccion, dict):
                                dir_principal = local.direccion.get('direccion_principal', 'N/A')
                                ciudad = local.direccion.get('ciudad', 'N/A')
                            elif hasattr(local.direccion, 'direccion_principal'):
                                dir_principal = local.direccion.direccion_principal
                                ciudad = local.direccion.ciudad
                            else:
                                dir_principal = str(local.direccion)
                                ciudad = 'N/A'
                            print(f"        ✅ Dirección procesada: {dir_principal}, {ciudad}")
                        else:
                            print(f"        ⚠️  Sin dirección")
                    except Exception as addr_err:
                        print(f"        ❌ Error accediendo dirección: {addr_err}")
                
                # Obtener asignaciones actuales
                asignaciones = usuario_local_repo.get_by_usuario(admin.id)
                print(f"   📋 Asignaciones actuales: {len(asignaciones)}")
                
            except Exception as e:
                print(f"   ❌ Error procesando admin: {e}")
    
    finally:
        session.close()


if __name__ == "__main__":
    debug_locales_disponibles()