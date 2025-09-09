#!/usr/bin/env python3
"""
Script para corregir inconsistencias de datos multi-tenant.

Este script resuelve el problema donde productos y usuarios están asignados
a tiendas diferentes, causando errores de "Producto no encontrado en su tienda".

Problemas identificados:
1. admin@empresa.com está en tienda: 24674128-7622-4d47-88db-f3284997da31
2. Producto 9ff11ab8-dc6d-428a-83c4-c59994427fca está en tienda: aaaaaaaa-bbbb-cccc-dddd-000000000001
3. Local solicitado 95a4fc43-46ef-4512-8547-9215d61631fb está en tienda: 24674128-7622-4d47-88db-f3284997da31

Ejecutar desde backend/:
    python fix_multi_tenant_data.py
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
    """Ejecutar corrección de datos multi-tenant."""
    print("🔧 === CORRIGIENDO INCONSISTENCIAS MULTI-TENANT ===")
    
    # Ejecución automática (sin confirmación)
    print("\n⚠️ Este script modificará datos en la base de datos:")
    print("   • Asignará productos huérfanos a la tienda correcta")
    print("   • Corregirá usuarios sin tienda asignada")
    print("   • Unificará datos hacia una tienda principal")
    print("\n✅ Ejecutando corrección automáticamente...")
    
    engine = get_engine()
    
    with Session(engine) as session:
        # ========== ANÁLISIS INICIAL ==========
        print("\n📊 Analizando estado actual...")
        
        # Contar usuarios por tienda
        users = session.exec(select(User)).all()
        tiendas = session.exec(select(Tienda)).all()
        products = session.exec(select(Product)).all()
        locales = session.exec(select(Local)).all()
        
        print(f"\n📈 Estado actual:")
        print(f"   • {len(users)} usuarios total")
        print(f"   • {len(tiendas)} tiendas total")
        print(f"   • {len(products)} productos total")
        print(f"   • {len(locales)} locales total")
        
        # Análisis por tienda
        for tienda in tiendas:
            users_tienda = [u for u in users if u.tienda_id == tienda.id]
            products_tienda = [p for p in products if p.tienda_id == tienda.id]
            locales_tienda = [l for l in locales if l.tienda_id == tienda.id]
            
            print(f"\n🏪 {tienda.nombre} ({tienda.codigo}):")
            print(f"   • {len(users_tienda)} usuarios")
            print(f"   • {len(products_tienda)} productos")
            print(f"   • {len(locales_tienda)} locales")
        
        # Usuarios sin tienda
        users_sin_tienda = [u for u in users if u.tienda_id is None]
        if users_sin_tienda:
            print(f"\n⚠️ {len(users_sin_tienda)} usuarios sin tienda:")
            for user in users_sin_tienda:
                print(f"   • {user.email}")
        
        # ========== ESTRATEGIA DE CORRECCIÓN ==========
        print("\n🎯 Estrategia de corrección:")
        
        # Identificar tienda principal (la que tiene más datos)
        tienda_principal = None
        max_datos = 0
        
        for tienda in tiendas:
            users_count = len([u for u in users if u.tienda_id == tienda.id])
            products_count = len([p for p in products if p.tienda_id == tienda.id])
            locales_count = len([l for l in locales if l.tienda_id == tienda.id])
            total_datos = users_count + products_count + locales_count
            
            print(f"   • {tienda.nombre}: {total_datos} elementos totales")
            
            if total_datos > max_datos:
                max_datos = total_datos
                tienda_principal = tienda
        
        if not tienda_principal:
            print("❌ No se pudo identificar tienda principal")
            return
        
        print(f"\n✅ Tienda principal identificada: {tienda_principal.nombre}")
        print(f"   ID: {tienda_principal.id}")
        print(f"   Código: {tienda_principal.codigo}")
        
        # ========== CORRECCIÓN 1: USUARIOS SIN TIENDA ==========
        if users_sin_tienda:
            print(f"\n🔧 Asignando {len(users_sin_tienda)} usuarios sin tienda a tienda principal...")
            
            for user in users_sin_tienda:
                user.tienda_id = tienda_principal.id
                # Si no tiene local principal, asignar el primer local de la tienda
                if not user.local_principal_id:
                    primer_local = next(
                        (l for l in locales if l.tienda_id == tienda_principal.id), 
                        None
                    )
                    if primer_local:
                        user.local_principal_id = primer_local.id
                
                session.add(user)
                print(f"   ✅ {user.email} → {tienda_principal.nombre}")
        
        # ========== CORRECCIÓN 2: PRODUCTOS EN TIENDAS INCORRECTAS ==========
        print(f"\n🔧 Verificando asignación de productos...")
        
        # Para simplificar, mover todos los productos a la tienda principal
        # Esto asegura que todos los usuarios puedan acceder a todos los productos
        productos_movidos = 0
        
        for product in products:
            if product.tienda_id != tienda_principal.id:
                old_tienda = next((t for t in tiendas if t.id == product.tienda_id), None)
                old_tienda_name = old_tienda.nombre if old_tienda else "Desconocida"
                
                product.tienda_id = tienda_principal.id
                session.add(product)
                productos_movidos += 1
                print(f"   📦 {product.sku}: {old_tienda_name} → {tienda_principal.nombre}")
        
        if productos_movidos == 0:
            print("   ✅ Todos los productos ya están en la tienda principal")
        else:
            print(f"   ✅ {productos_movidos} productos movidos a tienda principal")
        
        # ========== CORRECCIÓN 3: VALIDAR LOCALES ==========
        print(f"\n🔧 Verificando asignación de locales...")
        
        locales_tienda_principal = [l for l in locales if l.tienda_id == tienda_principal.id]
        print(f"   📍 {len(locales_tienda_principal)} locales en tienda principal:")
        
        for local in locales_tienda_principal:
            print(f"      • {local.codigo}: {local.nombre}")
        
        # ========== GUARDAR CAMBIOS ==========
        print(f"\n💾 Guardando cambios...")
        session.commit()
        
        # ========== VERIFICACIÓN FINAL ==========
        print(f"\n🔍 Verificación final...")
        
        # Verificar el caso específico reportado
        problema_user = session.exec(
            select(User).where(User.email == "admin@empresa.com")
        ).first()
        
        problema_product = session.exec(
            select(Product).where(Product.id == "9ff11ab8-dc6d-428a-83c4-c59994427fca")
        ).first()
        
        problema_local = session.exec(
            select(Local).where(Local.id == "95a4fc43-46ef-4512-8547-9215d61631fb")
        ).first()
        
        if problema_user and problema_product and problema_local:
            print(f"\n✅ Verificación del caso específico:")
            print(f"   👤 Usuario admin@empresa.com en tienda: {problema_user.tienda_id}")
            print(f"   📦 Producto {problema_product.sku} en tienda: {problema_product.tienda_id}")
            print(f"   📍 Local {problema_local.codigo} en tienda: {problema_local.tienda_id}")
            
            if (problema_user.tienda_id == problema_product.tienda_id == problema_local.tienda_id):
                print(f"   🎉 PROBLEMA RESUELTO: Todos en la misma tienda")
            else:
                print(f"   ⚠️ Aún hay inconsistencias")
        
        # ========== ESTADO FINAL ==========
        print(f"\n📊 Estado final:")
        
        # Recargar datos
        users_final = session.exec(select(User)).all()
        products_final = session.exec(select(Product)).all()
        
        for tienda in tiendas:
            users_count = len([u for u in users_final if u.tienda_id == tienda.id])
            products_count = len([p for p in products_final if p.tienda_id == tienda.id])
            locales_count = len([l for l in locales if l.tienda_id == tienda.id])
            
            if users_count > 0 or products_count > 0 or locales_count > 0:
                print(f"   🏪 {tienda.nombre}:")
                print(f"      • {users_count} usuarios")
                print(f"      • {products_count} productos")
                print(f"      • {locales_count} locales")
        
        users_sin_tienda_final = [u for u in users_final if u.tienda_id is None]
        if users_sin_tienda_final:
            print(f"\n⚠️ Aún quedan {len(users_sin_tienda_final)} usuarios sin tienda")
        else:
            print(f"\n✅ Todos los usuarios tienen tienda asignada")
    
    print(f"\n🎉 === CORRECCIÓN COMPLETADA ===")
    print(f"📋 Resumen de cambios:")
    print(f"   • Usuarios sin tienda: {len(users_sin_tienda)} → 0")
    print(f"   • Productos movidos: {productos_movidos}")
    print(f"   • Tienda principal: {tienda_principal.nombre}")
    print(f"   • El problema reportado debería estar resuelto")
    
    print(f"\n🔗 Para probar:")
    print(f"   1. Reinicia el backend")
    print(f"   2. Login como admin@empresa.com")
    print(f"   3. Intenta acceder al producto {problema_product.sku if problema_product else 'PROD001'}")
    print(f"   4. Cambia a local {problema_local.codigo if problema_local else 'SUC001'}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error durante la corrección: {e}")
        sys.exit(1)