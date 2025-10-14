#!/usr/bin/env python3
"""
Script para crear stock inicial para el producto JR-005 en Sucursal Centro
"""

import asyncio
from uuid import UUID
from decimal import Decimal
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
from app.domain.models.stock_local import StockLocalCreate

async def fix_jr005_stock():
    """Crear stock inicial para el producto JR-005 en Sucursal Centro."""
    
    print("🔧 Creating initial stock for product JR-005 in Sucursal Centro...")
    
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        # Product and local info
        jr005_product_id = UUID("4788677e-3ca6-4a33-ab93-51f98cc92382")  # JR-005
        sucursal_centro_id = UUID("95a4fc43-46ef-4512-8547-9215d61631fb")  # Sucursal Centro
        
        # Setup repository
        stock_repo = StockLocalRepository(session)
        
        # Check if stock already exists
        existing_stock = stock_repo.get_by_producto_and_local(jr005_product_id, sucursal_centro_id)
        
        if existing_stock:
            print(f"   ⚠️  Stock already exists for JR-005 in Sucursal Centro: {existing_stock.cantidad} units")
        else:
            print(f"   📦 Creating initial stock record for JR-005 in Sucursal Centro...")
            
            # Create initial stock with 0 units (user can update later)
            stock_create = StockLocalCreate(
                local_id=sucursal_centro_id,
                producto_id=jr005_product_id,
                cantidad=0,  # Start with 0, user can update via UI
                stock_minimo=0,
                stock_maximo=None,
                costo_promedio=Decimal("5000.00")  # Use product's precio_base
            )
            
            new_stock = stock_repo.create(stock_create)
            
            print(f"   ✅ Stock record created successfully!")
            print(f"      Stock Local ID: {new_stock.id}")
            print(f"      Product ID: {new_stock.producto_id}")
            print(f"      Local ID: {new_stock.local_id}")
            print(f"      Initial cantidad: {new_stock.cantidad}")
            print(f"      Cost promedio: ${new_stock.costo_promedio}")
            
        # Now check all products in Sucursal Centro
        print(f"\n📋 All products now available in Sucursal Centro:")
        all_stock = stock_repo.get_by_local(sucursal_centro_id)
        
        for i, stock in enumerate(all_stock, 1):
            from sqlmodel import select
            from app.domain.models.product import Product
            
            # Get product info
            product_statement = select(Product).where(Product.id == stock.producto_id)
            product_result = session.exec(product_statement)
            product = product_result.first()
            
            if product:
                print(f"   {i}. SKU: {product.sku}, Name: {product.nombre}")
                print(f"      Stock: {stock.cantidad} units")
                print(f"      Value: ${stock.valor_total_inventario}")
                
                if product.sku == "JR-005":
                    print(f"      🎉 JR-005 is now visible in Sucursal Centro!")
            print()
        
        print(f"✅ Fix completed! The product JR-005 should now be visible in the Sucursal Centro product list.")
        print(f"💡 You can now update its stock through the UI to set the desired quantity.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(fix_jr005_stock())