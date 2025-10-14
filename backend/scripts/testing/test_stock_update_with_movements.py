#!/usr/bin/env python3
"""
Test script para probar la actualización de stock
y verificar que ahora genera movimientos de inventario.
"""

import asyncio
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.inventario_repository import SQLInventarioRepository
from app.infrastructure.repositories.product_repository import SQLProductRepository
from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
from app.domain.models.movimiento_inventario import MovimientoInventarioCreate, TipoMovimiento

async def test_stock_update_with_movements():
    """Test para simular actualización de stock via endpoint y verificar movimientos."""
    
    print("🧪 Testing stock update with inventory movements generation...")
    
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        # Setup repositories
        product_repo = SQLProductRepository(session)
        stock_local_repo = StockLocalRepository(session)
        inventario_repo = SQLInventarioRepository(session, product_repo, stock_local_repo)
        
        # PROD001 info
        product_id = UUID("9ff11ab8-dc6d-428a-83c4-c59994427fca")
        sucursal_centro_id = UUID("95a4fc43-46ef-4512-8547-9215d61631fb")
        admin_user_id = UUID("c03958af-e2f3-4bbd-a2c6-abf9ee7dab20")
        
        # Get current stock
        current_stock_local = stock_local_repo.get_by_producto_and_local(product_id, sucursal_centro_id)
        current_stock = current_stock_local.cantidad if current_stock_local else 0
        
        print(f"📊 Current stock in Sucursal Centro: {current_stock}")
        
        # Simulate manual stock adjustment: let's add 15 units
        new_stock_amount = current_stock + 15
        diferencia = new_stock_amount - current_stock
        
        print(f"🔧 Simulating stock update: {current_stock} → {new_stock_amount} (diferencia: {diferencia:+})")
        
        if diferencia != 0:
            # Get product info for movement
            product = await product_repo.get_by_id(product_id)
            
            # Create inventory movement (like the endpoint does)
            tipo_movimiento = TipoMovimiento.AJUSTE
            cantidad_movimiento = abs(diferencia)
            
            if diferencia < 0:
                tipo_movimiento = TipoMovimiento.SALIDA
            
            movimiento_data = MovimientoInventarioCreate(
                producto_id=product_id,
                local_id=sucursal_centro_id,
                tipo_movimiento=tipo_movimiento,
                cantidad=cantidad_movimiento,
                precio_unitario=product.precio_publico,
                costo_unitario=product.precio_base,
                referencia="Ajuste manual de stock",
                observaciones=f"Ajuste de stock: {current_stock} → {new_stock_amount} (diferencia: {diferencia:+})"
            )
            
            print(f"📝 Creating inventory movement...")
            print(f"   Tipo: {tipo_movimiento}")
            print(f"   Cantidad: {cantidad_movimiento}")
            print(f"   Referencia: {movimiento_data.referencia}")
            
            # Create the movement
            movimiento = await inventario_repo.create_movimiento(movimiento_data, admin_user_id)
            
            print(f"   ✅ Movement created: {movimiento.id}")
            print(f"   Stock: {movimiento.stock_anterior} → {movimiento.stock_posterior}")
            
            # Verify final stock
            updated_stock_local = stock_local_repo.get_by_producto_and_local(product_id, sucursal_centro_id)
            final_stock = updated_stock_local.cantidad if updated_stock_local else 0
            
            print(f"\n📈 Final results:")
            print(f"   Stock anterior: {current_stock}")
            print(f"   Stock esperado: {new_stock_amount}")
            print(f"   Stock actual: {final_stock}")
            
            if final_stock == new_stock_amount:
                print(f"   ✅ Stock update successful!")
            else:
                print(f"   ❌ Stock mismatch!")
            
            # Check recent movements for this product
            print(f"\n📋 Recent movements for PROD001:")
            from app.application.use_cases.inventario_use_cases import ConsultarKardexUseCase
            
            kardex_use_case = ConsultarKardexUseCase(inventario_repo, product_repo)
            kardex = await kardex_use_case.execute(product_id, skip=0, limit=3)
            
            for i, mov in enumerate(kardex.movimientos[:3], 1):
                print(f"   {i}. {mov.tipo_movimiento} - {mov.cantidad} units")
                print(f"      Stock: {mov.stock_anterior} → {mov.stock_posterior}")
                print(f"      Ref: {mov.referencia}")
                print(f"      Date: {mov.created_at}")
                if mov.producto:
                    print(f"      Producto: {mov.producto.nombre} ({mov.producto.sku})")
            
            print(f"\n🎉 Test completed successfully!")
        else:
            print(f"⚠️  No stock change needed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(test_stock_update_with_movements())