#!/usr/bin/env python3
"""
Debug stock inconsistency between different APIs
"""

import asyncio
from uuid import UUID
from sqlmodel import Session, select, func

from app.infrastructure.database.session import get_session
from app.domain.models.movimiento_inventario import MovimientoInventario, TipoMovimiento
from app.domain.models.stock_local import StockLocal
from app.domain.models.product import Product

async def debug_stock_inconsistency():
    """Debug the stock inconsistency issue."""
    session_gen = get_session()
    session = next(session_gen)

    try:
        print("🔍 Debugging stock inconsistency for cables de red...")
        
        product_id = UUID("b825b9cc-f009-46e9-8e57-54c89ba5826e")
        local_id = UUID("aaaaaaaa-bbbb-cccc-dddd-000000000002")
        
        # 1. Check product info
        product = session.exec(select(Product).where(Product.id == product_id)).first()
        if product:
            print(f"📦 Product: {product.nombre} ({product.sku})")
        else:
            print("❌ Product not found!")
            return
        
        # 2. Check global inventory movements
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
        
        stock_global = max(0, entradas - salidas)
        
        print(f"\n📊 Global Inventory Movements:")
        print(f"   Total ENTRADAS: {entradas}")
        print(f"   Total SALIDAS: {salidas}")
        print(f"   Stock Global Calculado: {stock_global}")
        
        # 3. Check local stock
        stock_local = session.exec(
            select(StockLocal)
            .where(StockLocal.producto_id == product_id)
            .where(StockLocal.local_id == local_id)
        ).first()
        
        print(f"\n📍 Local Stock (stock_por_local table):")
        if stock_local:
            print(f"   Local ID: {stock_local.local_id}")
            print(f"   Cantidad: {stock_local.cantidad}")
            print(f"   Costo Promedio: {stock_local.costo_promedio}")
            print(f"   Valor Total: {stock_local.valor_total_inventario}")
            print(f"   Updated At: {stock_local.updated_at}")
        else:
            print("   ❌ No local stock entry found!")
        
        # 4. Check recent movements
        recent_movements = session.exec(
            select(MovimientoInventario)
            .where(MovimientoInventario.producto_id == product_id)
            .order_by(MovimientoInventario.created_at.desc())
            .limit(5)
        ).all()
        
        print(f"\n📈 Recent 5 Movements:")
        for mov in recent_movements:
            print(f"   {mov.created_at.strftime('%Y-%m-%d %H:%M')} | {mov.tipo_movimiento} | Qty: {mov.cantidad} | Stock: {mov.stock_anterior} → {mov.stock_posterior} | Ref: {mov.referencia[:30]}...")
        
        # 5. Summary
        print(f"\n🔍 DIAGNOSIS:")
        print(f"   Global Stock (from movements): {stock_global}")
        print(f"   Local Stock (from stock_por_local): {stock_local.cantidad if stock_local else 'N/A'}")
        
        if stock_local and stock_global != stock_local.cantidad:
            print(f"   ⚠️  INCONSISTENCY DETECTED!")
            print(f"   Global: {stock_global}, Local: {stock_local.cantidad}")
            print(f"   Difference: {stock_global - stock_local.cantidad}")
            
            # Check if there are movements after the last local stock update
            if stock_local.updated_at:
                movements_after = session.exec(
                    select(MovimientoInventario)
                    .where(MovimientoInventario.producto_id == product_id)
                    .where(MovimientoInventario.created_at > stock_local.updated_at)
                ).all()
                
                if movements_after:
                    print(f"   Found {len(movements_after)} movements after last local stock update:")
                    for mov in movements_after:
                        print(f"     {mov.created_at} | {mov.tipo_movimiento} | Qty: {mov.cantidad}")
        elif stock_global == (stock_local.cantidad if stock_local else 0):
            print(f"   ✅ Stock is consistent!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(debug_stock_inconsistency())