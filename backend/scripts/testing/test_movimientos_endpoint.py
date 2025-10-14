#!/usr/bin/env python3
"""
Test script para probar el endpoint de movimientos de inventario
con la nueva funcionalidad de información del producto.
"""

import asyncio
import json
from uuid import UUID
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.inventario_repository import SQLInventarioRepository
from app.infrastructure.repositories.product_repository import SQLProductRepository
from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
from app.application.use_cases.inventario_use_cases import ListarMovimientosUseCase

async def test_movimientos_endpoint():
    """Test para verificar que los movimientos incluyen información del producto."""
    
    print("🧪 Testing movimientos endpoint with product info...")
    
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        # Setup repositories
        product_repo = SQLProductRepository(session)
        stock_local_repo = StockLocalRepository(session)
        inventario_repo = SQLInventarioRepository(session, product_repo, stock_local_repo)
        
        # Create use case
        use_case = ListarMovimientosUseCase(inventario_repo, product_repo)
        
        # Execute use case to get movements
        result = await use_case.execute(page=1, limit=10)
        
        print(f"📊 Total movements found: {result.total}")
        print(f"📄 Page: {result.page}, Limit: {result.limit}")
        print(f"🔗 Has next: {result.has_next}, Has prev: {result.has_prev}")
        
        print("\n📋 First few movements:")
        for i, movimiento in enumerate(result.movimientos[:5], 1):
            print(f"\n{i}. Movement ID: {movimiento.id}")
            print(f"   Tipo: {movimiento.tipo_movimiento}")
            print(f"   Cantidad: {movimiento.cantidad}")
            print(f"   Fecha: {movimiento.created_at}")
            
            if movimiento.producto:
                print(f"   ✅ Producto: {movimiento.producto.nombre} ({movimiento.producto.sku})")
                print(f"   💰 Precio público: ${movimiento.producto.precio_publico}")
            else:
                print(f"   ❌ Producto: No info available (producto_id: {movimiento.producto_id})")
        
        if result.total == 0:
            print("⚠️  No movements found in the database")
        else:
            print(f"\n✅ Successfully loaded {len(result.movimientos)} movements with product info!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(test_movimientos_endpoint())