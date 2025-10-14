#!/usr/bin/env python3
"""
Add inventory to Sucursal Centro for testing invoice creation
"""

import asyncio
from uuid import UUID
from decimal import Decimal

from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.inventario_repository import SQLInventarioRepository
from app.infrastructure.repositories.product_repository import SQLProductRepository
from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
from app.domain.models.movimiento_inventario import MovimientoInventarioCreate, TipoMovimiento

async def add_inventory_sucursal_centro():
    """Add inventory to Sucursal Centro for PROD001."""
    session_gen = get_session()
    session = next(session_gen)

    try:
        print("📦 Adding inventory to Sucursal Centro for PROD001...")
        
        # Setup repositories
        product_repo = SQLProductRepository(session)
        stock_local_repo = StockLocalRepository(session)
        inventario_repo = SQLInventarioRepository(session, product_repo, stock_local_repo)
        
        # Product and location info
        product_id = UUID("9ff11ab8-dc6d-428a-83c4-c59994427fca")  # PROD001
        sucursal_centro_id = UUID("95a4fc43-46ef-4512-8547-9215d61631fb")  # Sucursal Centro
        admin_user_id = UUID("c03958af-e2f3-4bbd-a2c6-abf9ee7dab20")
        
        # Add 10 units to have stock for testing
        movimiento_data = MovimientoInventarioCreate(
            producto_id=product_id,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            cantidad=10,
            precio_unitario=Decimal("60000.00"),
            referencia="Entrada - Stock para pruebas Sucursal Centro",
            observaciones="Entrada de stock en Sucursal Centro para permitir ventas de prueba",
            local_id=sucursal_centro_id
        )
        
        print(f"   Creating ENTRADA movement: 10 units at $60,000 each")
        movimiento = await inventario_repo.create_movimiento(movimiento_data, admin_user_id)
        
        print(f"   ✅ Movement created: {movimiento.id}")
        print(f"   Stock: {movimiento.stock_anterior} → {movimiento.stock_posterior}")
        print(f"   Cost: ${movimiento.costo_unitario}")
        
        session.commit()
        print(f"\n🎉 Inventory added successfully to Sucursal Centro!")

    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(add_inventory_sucursal_centro())