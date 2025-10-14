#!/usr/bin/env python3
"""
Sync global stock with local stock for proper multi-tenant inventory management
"""

from app.infrastructure.database.session import get_session
from sqlmodel import Session, select, func
from app.domain.models.movimiento_inventario import MovimientoInventario, TipoMovimiento
from app.domain.models.stock_local import StockLocal, StockLocalCreate
from app.domain.models.product import Product
from app.domain.models.local import Local
from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
from uuid import UUID
from decimal import Decimal

def sync_local_stock():
    """Sync global inventory movements with local stock."""
    session_gen = get_session()
    session = next(session_gen)

    try:
        print("🔄 Synchronizing local stock with global inventory movements...")
        
        # Get the specific product and local
        product_id = UUID("b825b9cc-f009-46e9-8e57-54c89ba5826e")  # cables de red
        local_id = UUID("aaaaaaaa-bbbb-cccc-dddd-000000000002")    # Local Principal
        
        # Get product info
        product = session.exec(select(Product).where(Product.id == product_id)).first()
        local = session.exec(select(Local).where(Local.id == local_id)).first()
        
        print(f"📦 Product: {product.nombre} ({product.sku})")
        print(f"🏢 Local: {local.nombre}")
        
        # Calculate current stock from global inventory movements
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
        print(f"📊 Global stock: {entradas} entradas - {salidas} salidas = {stock_global}")
        
        # Get current local stock
        stock_local_repo = StockLocalRepository(session)
        stock_local_actual = stock_local_repo.get_by_producto_and_local(product_id, local_id)
        
        if stock_local_actual:
            print(f"📍 Current local stock: {stock_local_actual.cantidad}")
            
            # Update local stock to match global stock
            stock_local_actual.cantidad = stock_global
            stock_local_actual.costo_promedio = Decimal("50000.00")  # From previous data
            stock_local_actual.valor_total_inventario = Decimal(str(stock_global)) * Decimal("50000.00")
            
            session.add(stock_local_actual)
            print(f"   ✅ Updated local stock to {stock_global}")
        else:
            print(f"📍 No local stock found, creating new entry...")
            
            # Create new local stock entry
            stock_data = StockLocalCreate(
                producto_id=product_id,
                local_id=local_id,
                cantidad=stock_global,
                costo_promedio=Decimal("50000.00"),
                stock_minimo=5,
                stock_maximo=100
            )
            
            stock_local = stock_local_repo.create(stock_data)
            print(f"   ✅ Created local stock: {stock_local.cantidad} units")
            print(f"   ✅ Cost: ${stock_local.costo_promedio}")
            print(f"   ✅ Value: ${stock_local.valor_total_inventario}")
        
        session.commit()
        print(f"\n🎉 Stock synchronization completed!")
        
        # Verify the sync
        stock_local_final = stock_local_repo.get_by_producto_and_local(product_id, local_id)
        if stock_local_final:
            print(f"✅ Final verification:")
            print(f"   Global stock: {stock_global}")
            print(f"   Local stock: {stock_local_final.cantidad}")
            print(f"   Match: {'✅' if stock_global == stock_local_final.cantidad else '❌'}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    sync_local_stock()