#!/usr/bin/env python3
"""
Test script para probar el endpoint del kardex
con la nueva funcionalidad de información del producto.
"""

import asyncio
import json
from uuid import UUID
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.inventario_repository import SQLInventarioRepository
from app.infrastructure.repositories.product_repository import SQLProductRepository
from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
from app.application.use_cases.inventario_use_cases import ConsultarKardexUseCase

async def test_kardex_endpoint():
    """Test para verificar que el kardex incluye información del producto."""
    
    print("🧪 Testing kardex endpoint with product info...")
    
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        # Setup repositories
        product_repo = SQLProductRepository(session)
        stock_local_repo = StockLocalRepository(session)
        inventario_repo = SQLInventarioRepository(session, product_repo, stock_local_repo)
        
        # Create use case
        use_case = ConsultarKardexUseCase(inventario_repo, product_repo)
        
        # Test with PROD001
        producto_id = UUID("9ff11ab8-dc6d-428a-83c4-c59994427fca")
        
        # Execute use case to get kardex
        result = await use_case.execute(producto_id=producto_id, skip=0, limit=10)
        
        print(f"📊 Kardex for producto: {result.producto_id}")
        print(f"📈 Stock actual: {result.stock_actual}")
        print(f"💰 Costo promedio actual: ${result.costo_promedio_actual}")
        print(f"💵 Valor inventario: ${result.valor_inventario}")
        print(f"📄 Total movimientos: {result.total_movimientos}")
        
        print(f"\n📋 Recent movements ({len(result.movimientos)}):")
        for i, movimiento in enumerate(result.movimientos[:5], 1):
            print(f"\n{i}. Movement ID: {movimiento.id}")
            print(f"   Tipo: {movimiento.tipo_movimiento}")
            print(f"   Cantidad: {movimiento.cantidad}")
            print(f"   Stock: {movimiento.stock_anterior} → {movimiento.stock_posterior}")
            print(f"   Fecha: {movimiento.created_at}")
            
            if movimiento.producto:
                print(f"   ✅ Producto: {movimiento.producto.nombre} ({movimiento.producto.sku})")
                print(f"   💰 Precio público: ${movimiento.producto.precio_publico}")
            else:
                print(f"   ❌ Producto: No info available (producto_id: {movimiento.producto_id})")
        
        print(f"\n✅ Kardex successfully loaded with product info!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(test_kardex_endpoint())