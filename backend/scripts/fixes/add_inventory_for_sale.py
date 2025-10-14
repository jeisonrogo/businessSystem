#!/usr/bin/env python3
"""
Add inventory to allow the user's sale of 8 cables de red units
"""

import asyncio
from uuid import UUID
from decimal import Decimal
from datetime import datetime, timezone

from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.inventario_repository import SQLInventarioRepository
from app.infrastructure.repositories.product_repository import SQLProductRepository
from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
from app.domain.models.movimiento_inventario import MovimientoInventarioCreate, TipoMovimiento

async def add_inventory_for_sale():
    """Add inventory entry to allow sale of 8 units."""
    session_gen = get_session()
    session = next(session_gen)

    try:
        print("📦 Adding inventory to allow sale of 8 cables de red units...")
        
        # Setup repositories
        product_repo = SQLProductRepository(session)
        stock_local_repo = StockLocalRepository(session)
        inventario_repo = SQLInventarioRepository(session, product_repo, stock_local_repo)
        
        # Product and user info
        product_id = UUID("b825b9cc-f009-46e9-8e57-54c89ba5826e")
        admin_user_id = UUID("c03958af-e2f3-4bbd-a2c6-abf9ee7dab20")
        local_id = UUID("aaaaaaaa-bbbb-cccc-dddd-000000000002")
        
        # Current stock: 1 unit. Need 8 total, so add 7 more units
        cantidad_entrada = 7
        
        # Create inventory entry
        movimiento_data = MovimientoInventarioCreate(
            producto_id=product_id,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            cantidad=cantidad_entrada,
            precio_unitario=Decimal("50000.00"),
            referencia="Entrada - Reabastecimiento para venta",
            observaciones=f"Entrada de {cantidad_entrada} unidades para permitir venta de 8 unidades total",
            local_id=local_id
        )
        
        print(f"   Creating ENTRADA movement: {cantidad_entrada} units at $50,000 each")
        movimiento = await inventario_repo.create_movimiento(movimiento_data, admin_user_id)
        
        print(f"   ✅ Movement created: {movimiento.id}")
        print(f"   Stock: {movimiento.stock_anterior} → {movimiento.stock_posterior}")
        print(f"   Cost: ${movimiento.costo_unitario}")
        
        session.commit()
        
        # Verify final stock
        from sqlmodel import select, func
        from app.domain.models.movimiento_inventario import MovimientoInventario
        
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
        
        stock_total = max(0, entradas - salidas)
        print(f"\n📊 Final stock calculation:")
        print(f"   Total entries: {entradas}")
        print(f"   Total exits: {salidas}")
        print(f"   Final stock: {stock_total}")
        
        if stock_total >= 8:
            print(f"   ✅ Stock sufficient for sale of 8 units!")
        else:
            print(f"   ⚠️ Stock still insufficient: {stock_total} < 8")
        
        print(f"\n🎉 Inventory added successfully! You can now sell up to {stock_total} units.")

    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(add_inventory_for_sale())