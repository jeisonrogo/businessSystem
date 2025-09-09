#!/usr/bin/env python3
"""
Script to test inventory repository with stock local integration
"""

import asyncio
from sqlmodel import Session
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.inventario_repository import SQLInventarioRepository
from app.infrastructure.repositories.product_repository import SQLProductRepository
from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
from app.domain.models.movimiento_inventario import MovimientoInventarioCreate, TipoMovimiento
from decimal import Decimal
from uuid import UUID

async def test_inventory_with_stock_local():
    """Test inventory repository with stock local integration."""
    session_gen = get_session()
    session = next(session_gen)

    try:
        # Setup repositories
        product_repo = SQLProductRepository(session)
        stock_local_repo = StockLocalRepository(session)
        inventario_repo = SQLInventarioRepository(session, product_repo, stock_local_repo)
        
        # Create inventory SALIDA movement (like a sale)
        product_id = UUID('50bfec78-3382-4a2f-ac28-a5746d77e464')  # PROD-001
        local_id = UUID('95a4fc43-46ef-4512-8547-9215d61631fb')   # Sucursal Centro
        
        movimiento_data = MovimientoInventarioCreate(
            producto_id=product_id,
            tipo_movimiento=TipoMovimiento.SALIDA,
            cantidad=5,  # Sell 5 units
            precio_unitario=Decimal('60.00'),  # Sale price
            costo_unitario=Decimal('40.00'),   # Cost price
            referencia='Venta de prueba',
            observaciones='Venta de prueba para verificar integración',
            local_id=local_id
        )
        
        # Create the movement
        admin_id = UUID('6d3992f0-ff7b-49bc-86be-a1984919d4d5')  # admin@demoprincipal.com
        movimiento = await inventario_repo.create_movimiento(movimiento_data, admin_id)
        
        print(f'✅ Movimiento de salida creado exitosamente!')
        print(f'   ID: {movimiento.id}')
        print(f'   Tipo: {movimiento.tipo_movimiento}')
        print(f'   Producto: {movimiento.producto_id}')
        print(f'   Cantidad: {movimiento.cantidad}')
        print(f'   Stock anterior: {movimiento.stock_anterior}')
        print(f'   Stock posterior: {movimiento.stock_posterior}')
        print(f'   Local: {movimiento.local_id}')
        
        # Verify stock local was updated
        stock_local = stock_local_repo.get_by_producto_and_local(product_id, local_id)
        if stock_local:
            print(f'   Stock local actualizado: {stock_local.cantidad}')
        
        session.commit()
        
    except Exception as e:
        session.rollback()
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(test_inventory_with_stock_local())