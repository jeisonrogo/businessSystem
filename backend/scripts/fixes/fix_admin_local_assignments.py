#!/usr/bin/env python3
"""
Script para asignar automáticamente todos los locales a usuarios con rol ADMINISTRADOR
que no tienen asignaciones locales configuradas.

Este script corrige casos donde administradores fueron creados antes de implementar
la asignación automática de locales.
"""

import asyncio
import sys
import os

# Agregar el directorio backend al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.user_repository import SQLUserRepository
from app.infrastructure.repositories.local_repository import LocalRepository
from app.infrastructure.repositories.usuario_local_repository import UsuarioLocalRepository
from app.domain.models.user import UserRole
from app.domain.models.usuario_local import UsuarioLocalCreate


async def fix_admin_local_assignments():
    """
    Buscar usuarios administradores sin asignaciones locales y asignarles
    automáticamente todos los locales de su tienda con permisos completos.
    """
    print("🔧 Iniciando corrección de asignaciones locales para administradores...")
    
    # Obtener sesión de base de datos
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        # Inicializar repositorios
        user_repo = SQLUserRepository(session)
        local_repo = LocalRepository(session)
        usuario_local_repo = UsuarioLocalRepository(session)
        
        print("📋 Buscando usuarios administradores...")
        
        # Buscar todos los usuarios y filtrar administradores
        all_users = await user_repo.get_all(limit=1000)
        admin_users = [user for user in all_users if user.rol == UserRole.ADMINISTRADOR]
        print(f"   Encontrados {len(admin_users)} usuarios administradores")
        
        fixed_count = 0
        
        for admin_user in admin_users:
            print(f"\n👤 Procesando administrador: {admin_user.nombre} ({admin_user.email})")
            
            # Verificar si ya tiene asignaciones locales
            existing_assignments = usuario_local_repo.get_by_usuario(admin_user.id)
            
            if len(existing_assignments) > 0:
                print(f"   ✅ Ya tiene {len(existing_assignments)} locales asignados")
                continue
            
            # Obtener todos los locales de la tienda del administrador
            locales_tienda = local_repo.get_by_tienda(admin_user.tienda_id, limit=1000)
            
            if len(locales_tienda) == 0:
                print(f"   ⚠️  No hay locales en la tienda {admin_user.tienda_id}")
                continue
            
            print(f"   🏪 Asignando {len(locales_tienda)} locales...")
            
            # Asignar todos los locales con permisos completos
            for local in locales_tienda:
                assignment_data = UsuarioLocalCreate(
                    user_id=admin_user.id,
                    local_id=local.id,
                    puede_vender=True,
                    puede_ver_stock=True,
                    puede_transferir=True,
                    es_responsable=True,
                    puede_modificar_precios=True,
                    puede_aplicar_descuentos=True,
                    puede_ver_reportes=True,
                    puede_gestionar_usuarios=True
                )
                
                usuario_local_repo.create(assignment_data)
                print(f"      ✅ Asignado al local: {local.nombre} ({local.codigo})")
            
            fixed_count += 1
        
        session.commit()
        
        print(f"\n🎉 Corrección completada!")
        print(f"   - Administradores procesados: {len(admin_users)}")
        print(f"   - Administradores corregidos: {fixed_count}")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error durante la corrección: {e}")
        raise
    
    finally:
        session.close()


async def verify_admin_assignments():
    """
    Verificar que todos los administradores tienen asignaciones locales correctas.
    """
    print("\n🔍 Verificando asignaciones de administradores...")
    
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        user_repo = SQLUserRepository(session)
        usuario_local_repo = UsuarioLocalRepository(session)
        
        all_users = await user_repo.get_all(limit=1000)
        admin_users = [user for user in all_users if user.rol == UserRole.ADMINISTRADOR]
        
        print(f"📊 Resumen de asignaciones para {len(admin_users)} administradores:")
        
        for admin_user in admin_users:
            assignments = usuario_local_repo.get_by_usuario(admin_user.id)
            print(f"   👤 {admin_user.nombre}: {len(assignments)} locales asignados")
            
            if len(assignments) == 0:
                print(f"      ⚠️  ¡Sin asignaciones!")
    
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🏢 CORRECCIÓN DE ASIGNACIONES LOCALES PARA ADMINISTRADORES")
    print("=" * 60)
    
    asyncio.run(fix_admin_local_assignments())
    asyncio.run(verify_admin_assignments())
    
    print("\n✅ Script completado exitosamente!")