#!/usr/bin/env python3
"""
Script para arreglar el problema de usuario sin tienda asignada.
"""

import asyncio
from uuid import uuid4
from sqlmodel import Session, select
from app.infrastructure.database.session import get_session
from app.domain.models.user import User
from app.domain.models.tienda import Tienda
from app.domain.models.local import Local
from app.domain.models.usuario_local import UsuarioLocal

def fix_user_tenant_assignment():
    """Arregla la asignación de tienda y local para el usuario admin."""

    print("🔧 Arreglando asignación de tienda para usuario admin...")

    for session in get_session():
        # Buscar usuario admin
        admin_user = session.exec(
            select(User).where(User.email == "admin@test.com")
        ).first()

        if not admin_user:
            print("❌ Usuario admin@test.com no encontrado")
            return

        print(f"👤 Usuario encontrado: {admin_user.nombre} ({admin_user.email})")

        # Buscar o crear tienda
        tienda = session.exec(select(Tienda)).first()

        if not tienda:
            print("🏢 Creando tienda demo...")
            tienda = Tienda(
                id=uuid4(),
                codigo="DEMO",
                nombre="Tienda Demo",
                descripcion="Tienda de demostración para testing",
                dominio="demo.local",
                configuracion={}
            )
            session.add(tienda)
            session.commit()
            session.refresh(tienda)
            print(f"✅ Tienda creada: {tienda.nombre}")
        else:
            print(f"🏢 Tienda existente encontrada: {tienda.nombre}")

        # Buscar o crear local
        local = session.exec(
            select(Local).where(Local.tienda_id == tienda.id)
        ).first()

        if not local:
            print("📍 Creando local demo...")
            local = Local(
                id=uuid4(),
                tienda_id=tienda.id,
                codigo="LOCAL01",
                nombre="Local Principal",
                direccion="Calle Demo 123",
                ciudad="Bogotá",
                departamento="Cundinamarca",
                configuracion={}
            )
            session.add(local)
            session.commit()
            session.refresh(local)
            print(f"✅ Local creado: {local.nombre}")
        else:
            print(f"📍 Local existente encontrado: {local.nombre}")

        # Asignar tienda al usuario
        if not admin_user.tienda_id:
            admin_user.tienda_id = tienda.id
            admin_user.local_principal_id = local.id
            session.add(admin_user)
            print("🔗 Asignando tienda y local principal al usuario...")
        else:
            print("✅ Usuario ya tiene tienda asignada")

        # Crear o verificar asignación usuario-local
        usuario_local = session.exec(
            select(UsuarioLocal).where(
                UsuarioLocal.user_id == admin_user.id,
                UsuarioLocal.local_id == local.id
            )
        ).first()

        if not usuario_local:
            print("🔗 Creando asignación usuario-local...")
            usuario_local = UsuarioLocal(
                id=uuid4(),
                user_id=admin_user.id,
                local_id=local.id,
                puede_vender=True,
                puede_ver_stock=True,
                puede_transferir=True,
                es_responsable=True,
                puede_modificar_precios=True,
                puede_aplicar_descuentos=True,
                puede_ver_reportes=True,
                puede_gestionar_usuarios=True,
                limite_descuento_porcentaje=100.0,
                created_by=admin_user.id
            )
            session.add(usuario_local)
            print("✅ Asignación usuario-local creada")
        else:
            print("✅ Asignación usuario-local ya existe")

        # Guardar cambios
        session.commit()

        print("\n🎉 ¡Configuración completada exitosamente!")
        print(f"   Usuario: {admin_user.email}")
        print(f"   Tienda: {tienda.nombre} ({tienda.codigo})")
        print(f"   Local: {local.nombre} ({local.codigo})")
        print(f"   ID Tienda: {tienda.id}")
        print(f"   ID Local: {local.id}")

        break

if __name__ == "__main__":
    fix_user_tenant_assignment()