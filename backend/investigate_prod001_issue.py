#!/usr/bin/env python3
"""
Investigate PROD001 stock issues in Sucursal Centro
"""

import asyncio
from uuid import UUID
from sqlmodel import Session, select, func

from app.infrastructure.database.session import get_session
from app.domain.models.product import Product
from app.domain.models.stock_local import StockLocal
from app.domain.models.local import Local
from app.domain.models.movimiento_inventario import MovimientoInventario, TipoMovimiento

async def investigate_product_issue():
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        print("🔍 Investigating PROD001 issue in Sucursal Centro...")
        
        product_id = UUID("9ff11ab8-dc6d-428a-83c4-c59994427fca")
        local_id = UUID("95a4fc43-46ef-4512-8547-9215d61631fb")
        
        # 1. Check product info
        product = session.exec(select(Product).where(Product.id == product_id)).first()
        if product:
            print(f"📦 Product: {product.nombre} (SKU: {product.sku})")
            print(f"   ID: {product.id}")
            print(f"   Active: {product.is_active}")
        else:
            print("❌ Product not found!")
            return
        
        # 2. Check local info
        local = session.exec(select(Local).where(Local.id == local_id)).first()
        if local:
            print(f"🏪 Local: {local.nombre}")
            print(f"   ID: {local.id}")
            print(f"   Tienda ID: {local.tienda_id}")
        else:
            print("❌ Local not found!")
            return
        
        # 3. Check local stock
        stock_local = session.exec(
            select(StockLocal)
            .where(StockLocal.producto_id == product_id)
            .where(StockLocal.local_id == local_id)
        ).first()
        
        print(f"\n📍 Local Stock in {local.nombre}:")
        if stock_local:
            print(f"   Cantidad: {stock_local.cantidad}")
            print(f"   Costo Promedio: {stock_local.costo_promedio}")
            print(f"   Valor Total: {stock_local.valor_total_inventario}")
            print(f"   Updated At: {stock_local.updated_at}")
        else:
            print("   ❌ No local stock entry found!")
        
        # 4. Check global inventory movements for this product
        entradas = session.exec(
            select(func.coalesce(func.sum(MovimientoInventario.cantidad), 0))
            .where(MovimientoInventario.producto_id == product_id)
            .where(MovimientoInventario.tipo_movimiento == TipoMovimiento.ENTRADA)
        ).one()
        
        salidas = session.exec(
            select(func.coalesce(func.sum(MovimientoInventario.cantidad), 0))
            .where(MovimientoInventario.producto_id == product_id)
            .where(MovimientoInventario.tipo_movimiento == TipoMovimiento.SALIDA)
        ).one()
        
        global_stock = max(0, entradas - salidas)
        
        print(f"\n📊 Global Inventory Movements:")
        print(f"   Total ENTRADAS: {entradas}")
        print(f"   Total SALIDAS: {salidas}")
        print(f"   Global Stock: {global_stock}")
        
        # 5. Check movements filtered by local
        entradas_local = session.exec(
            select(func.coalesce(func.sum(MovimientoInventario.cantidad), 0))
            .where(MovimientoInventario.producto_id == product_id)
            .where(MovimientoInventario.local_id == local_id)
            .where(MovimientoInventario.tipo_movimiento == TipoMovimiento.ENTRADA)
        ).one()
        
        salidas_local = session.exec(
            select(func.coalesce(func.sum(MovimientoInventario.cantidad), 0))
            .where(MovimientoInventario.producto_id == product_id)
            .where(MovimientoInventario.local_id == local_id)
            .where(MovimientoInventario.tipo_movimiento == TipoMovimiento.SALIDA)
        ).one()
        
        local_stock_calc = max(0, entradas_local - salidas_local)
        
        print(f"\n📍 Local-filtered Movements:")
        print(f"   Local ENTRADAS: {entradas_local}")
        print(f"   Local SALIDAS: {salidas_local}")
        print(f"   Local Stock (calculated): {local_stock_calc}")
        
        # 6. Recent movements
        recent_movements = session.exec(
            select(MovimientoInventario)
            .where(MovimientoInventario.producto_id == product_id)
            .order_by(MovimientoInventario.created_at.desc())
            .limit(10)
        ).all()
        
        print(f"\n📈 Recent 10 Movements:")
        for mov in recent_movements:
            local_name = "N/A"
            if mov.local_id:
                try:
                    mov_local = session.exec(select(Local).where(Local.id == mov.local_id)).first()
                    local_name = mov_local.nombre if mov_local else str(mov.local_id)[:8]
                except:
                    local_name = str(mov.local_id)[:8] if mov.local_id else "N/A"
            
            print(f"   {mov.created_at.strftime('%Y-%m-%d %H:%M')} | {mov.tipo_movimiento} | {mov.cantidad} units | Local: {local_name} | Ref: {mov.referencia[:40]}...")
        
        # 7. Check all stock entries for this product across all locals
        all_stock_entries = session.exec(
            select(StockLocal)
            .where(StockLocal.producto_id == product_id)
        ).all()
        
        print(f"\n📋 All Stock Entries for this Product:")
        total_stock_in_table = 0
        for stock in all_stock_entries:
            try:
                stock_local_obj = session.exec(select(Local).where(Local.id == stock.local_id)).first()
                local_name = stock_local_obj.nombre if stock_local_obj else str(stock.local_id)[:8]
            except:
                local_name = str(stock.local_id)[:8]
            
            print(f"   {local_name}: {stock.cantidad} units")
            total_stock_in_table += stock.cantidad
        
        print(f"   Total in stock table: {total_stock_in_table}")
        
        # 8. Summary
        print(f"\n🔍 SUMMARY:")
        print(f"   Product: {product.nombre} ({product.sku})")
        print(f"   Specific Local: {local.nombre}")
        print(f"   Global Stock (movements): {global_stock}")
        print(f"   Total Stock (table): {total_stock_in_table}")
        print(f"   Specific Local Stock (table): {stock_local.cantidad if stock_local else 'N/A'}")
        print(f"   Specific Local Stock (calculated): {local_stock_calc}")
        
        if stock_local:
            if stock_local.cantidad != local_stock_calc:
                print(f"   ⚠️  INCONSISTENCY: Table shows {stock_local.cantidad}, movements calculate {local_stock_calc}")
            else:
                print(f"   ✅ Local stock is consistent")
        
        # Check if the issue is in the validation logic
        if stock_local and stock_local.cantidad < 50:
            print(f"\n⚠️  VALIDATION ISSUE DETECTED:")
            print(f"   Product has {stock_local.cantidad} units available")
            print(f"   But system allowed creating invoice with 50 units")
            print(f"   This suggests stock validation is not working properly")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(investigate_product_issue())