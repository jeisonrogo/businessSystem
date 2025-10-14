#!/usr/bin/env python3
"""
Fix stock synchronization between global movements and local stock
"""

import asyncio
from uuid import UUID
from sqlmodel import Session, select, func
from decimal import Decimal
from datetime import datetime, timezone

from app.infrastructure.database.session import get_session
from app.domain.models.movimiento_inventario import MovimientoInventario, TipoMovimiento
from app.domain.models.stock_local import StockLocal
from app.domain.models.product import Product

async def fix_stock_synchronization():
    """Fix stock synchronization for cables de red product."""
    session_gen = get_session()
    session = next(session_gen)

    try:
        print("🔧 Fixing stock synchronization for cables de red...")
        
        product_id = UUID("b825b9cc-f009-46e9-8e57-54c89ba5826e")
        local_id = UUID("aaaaaaaa-bbbb-cccc-dddd-000000000002")
        
        # 1. Calculate correct global stock
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
        
        correct_stock = max(0, entradas - salidas)
        
        print(f"📊 Correct Stock Calculation:")
        print(f"   Total ENTRADAS: {entradas}")
        print(f"   Total SALIDAS: {salidas}")
        print(f"   Correct Stock: {correct_stock}")
        
        # 2. Get current local stock
        stock_local = session.exec(
            select(StockLocal)
            .where(StockLocal.producto_id == product_id)
            .where(StockLocal.local_id == local_id)
        ).first()
        
        if stock_local:
            print(f"📍 Current Local Stock: {stock_local.cantidad}")
            
            if stock_local.cantidad != correct_stock:
                print(f"   ⚠️  Fixing inconsistency: {stock_local.cantidad} → {correct_stock}")
                
                # Update local stock
                stock_local.cantidad = correct_stock
                stock_local.valor_total_inventario = Decimal(str(correct_stock)) * stock_local.costo_promedio
                stock_local.updated_at = datetime.now(timezone.utc)
                
                session.add(stock_local)
                session.commit()
                
                print(f"   ✅ Local stock updated to {correct_stock}")
                print(f"   ✅ Value updated to ${stock_local.valor_total_inventario}")
            else:
                print(f"   ✅ Local stock is already correct!")
        else:
            print(f"   ❌ No local stock entry found! Creating one...")
            
            # Create new local stock entry
            new_stock = StockLocal(
                producto_id=product_id,
                local_id=local_id,
                cantidad=correct_stock,
                stock_minimo=5,
                stock_maximo=100,
                costo_promedio=Decimal("50000.00"),
                valor_total_inventario=Decimal(str(correct_stock)) * Decimal("50000.00"),
                updated_at=datetime.now(timezone.utc)
            )
            
            session.add(new_stock)
            session.commit()
            
            print(f"   ✅ Created new local stock entry with {correct_stock} units")
        
        print(f"\n🎉 Stock synchronization completed!")
        print(f"   Final unified stock: {correct_stock} units")
        
        # 3. Verify the fix
        print(f"\n🔍 Verification:")
        updated_stock = session.exec(
            select(StockLocal)
            .where(StockLocal.producto_id == product_id)
            .where(StockLocal.local_id == local_id)
        ).first()
        
        if updated_stock:
            print(f"   Local stock now: {updated_stock.cantidad}")
            print(f"   Global stock: {correct_stock}")
            print(f"   Match: {'✅' if updated_stock.cantidad == correct_stock else '❌'}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(fix_stock_synchronization())