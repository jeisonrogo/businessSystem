#!/usr/bin/env python3
"""
Script to create initial inventory entry for testing
"""

import asyncio
from sqlmodel import Session
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.inventario_repository import SQLInventarioRepository
from app.infrastructure.repositories.product_repository import SQLProductRepository
from app.domain.models.movimiento_inventario import MovimientoInventarioCreate, TipoMovimiento
from decimal import Decimal
from uuid import UUID

async def create_initial_inventory():
    """Create initial inventory entry."""
    session_gen = get_session()
    session = next(session_gen)

    try:
        # Setup repositories
        product_repo = SQLProductRepository(session)
        inventario_repo = SQLInventarioRepository(session, product_repo)
        
        # Create inventory entry for first product
        product_id = UUID('50bfec78-3382-4a2f-ac28-a5746d77e464')  # PROD-001
        local_id = UUID('95a4fc43-46ef-4512-8547-9215d61631fb')   # Sucursal Centro
        
        movimiento_data = MovimientoInventarioCreate(
            producto_id=product_id,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            cantidad=100,  # 100 units
            precio_unitario=Decimal('50.00'),
            costo_unitario=Decimal('40.00'),
            referencia='Compra inicial para inventario',
            observaciones='Entrada inicial de inventario para pruebas',
            local_id=local_id
        )
        
        # Create the movement
        admin_id = UUID('6d3992f0-ff7b-49bc-86be-a1984919d4d5')  # admin@demoprincipal.com
        movimiento = await inventario_repo.create_movimiento(movimiento_data, admin_id)
        
        print(f'✅ Movimiento de entrada creado exitosamente!')
        print(f'   ID: {movimiento.id}')
        print(f'   Producto: {product_id}')
        print(f'   Cantidad: {movimiento.cantidad}')
        print(f'   Stock anterior: {movimiento.stock_anterior}')
        print(f'   Stock posterior: {movimiento.stock_posterior}')
        
        session.commit()
        
    except Exception as e:
        session.rollback()
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(create_initial_inventory())