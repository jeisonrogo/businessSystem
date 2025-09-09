#!/usr/bin/env python3
"""
Script to create initial stock local entry for testing
"""

from sqlmodel import Session
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
from app.domain.models.stock_local import StockLocalCreate
from decimal import Decimal
from uuid import UUID

def create_initial_stock_local():
    """Create initial stock local entry."""
    session_gen = get_session()
    session = next(session_gen)

    try:
        # Setup repositories
        stock_local_repo = StockLocalRepository(session)
        
        # Create stock local entry for first product
        product_id = UUID('50bfec78-3382-4a2f-ac28-a5746d77e464')  # PROD-001
        local_id = UUID('95a4fc43-46ef-4512-8547-9215d61631fb')   # Sucursal Centro
        
        stock_data = StockLocalCreate(
            producto_id=product_id,
            local_id=local_id,
            cantidad=100,  # 100 units
            costo_promedio=Decimal('40.00'),
            stock_minimo=10,
            stock_maximo=200
        )
        
        # Create the stock local
        stock = stock_local_repo.create(stock_data)
        
        print(f'✅ Stock local creado exitosamente!')
        print(f'   ID: {stock.id}')
        print(f'   Producto: {product_id}')
        print(f'   Local: {local_id}')
        print(f'   Cantidad: {stock.cantidad}')
        print(f'   Costo promedio: {stock.costo_promedio}')
        print(f'   Valor total: {stock.valor_total_inventario}')
        
    except Exception as e:
        session.rollback()
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    create_initial_stock_local()