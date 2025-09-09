#!/usr/bin/env python3
"""
Script para investigar el problema con productos que comienzan con "JR"
"""

import asyncio
from uuid import UUID
from sqlmodel import Session, select
from app.infrastructure.database.session import get_session
from app.domain.models.product import Product
from app.domain.models.stock_local import StockLocal
from app.domain.models.local import Local

async def investigate_jr_product():
    """Investigar productos con SKU que comience con JR."""
    
    print("🔍 Investigating products with SKU starting with 'JR'...")
    
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        # Buscar productos que comiencen con JR
        print("\n📋 Searching for products with SKU starting with 'JR':")
        
        statement = select(Product).where(Product.sku.startswith("JR"))
        result = session.exec(statement)
        jr_products = result.all()
        
        if not jr_products:
            print("   ❌ No products found with SKU starting with 'JR'")
            
            # Buscar todos los productos recientes
            print("\n📋 Looking for recent products (last 10):")
            recent_statement = select(Product).order_by(Product.created_at.desc()).limit(10)
            recent_result = session.exec(recent_statement)
            recent_products = recent_result.all()
            
            for i, product in enumerate(recent_products, 1):
                print(f"   {i}. SKU: {product.sku}, Name: {product.nombre}")
                print(f"      ID: {product.id}")
                print(f"      Created: {product.created_at}")
                print(f"      Tienda ID: {product.tienda_id}")
                print(f"      Active: {product.is_active}")
                print()
        else:
            print(f"   ✅ Found {len(jr_products)} products with SKU starting with 'JR':")
            
            for i, product in enumerate(jr_products, 1):
                print(f"\n   {i}. Product found:")
                print(f"      SKU: {product.sku}")
                print(f"      Name: {product.nombre}")
                print(f"      ID: {product.id}")
                print(f"      Created: {product.created_at}")
                print(f"      Tienda ID: {product.tienda_id}")
                print(f"      Active: {product.is_active}")
                print(f"      Price Base: ${product.precio_base}")
                print(f"      Price Public: ${product.precio_publico}")
                
                # Check stock in different locals
                print(f"      📦 Stock por local:")
                stock_statement = select(StockLocal).where(StockLocal.producto_id == product.id)
                stock_result = session.exec(stock_statement)
                stock_records = stock_result.all()
                
                if stock_records:
                    for stock in stock_records:
                        # Get local name
                        local_statement = select(Local).where(Local.id == stock.local_id)
                        local_result = session.exec(local_statement)
                        local = local_result.first()
                        local_name = local.nombre if local else "Unknown Local"
                        
                        print(f"         - {local_name}: {stock.cantidad} units")
                        print(f"           Local ID: {stock.local_id}")
                else:
                    print(f"         - No stock records found")
        
        # Also search for case variations
        print(f"\n📋 Searching case-insensitive for 'jr' products:")
        case_statement = select(Product).where(Product.sku.ilike("jr%"))
        case_result = session.exec(case_statement)
        case_products = case_result.all()
        
        if case_products:
            print(f"   ✅ Found {len(case_products)} products with case-insensitive 'jr':")
            for product in case_products:
                print(f"      - SKU: {product.sku}, Name: {product.nombre}")
        else:
            print(f"   ❌ No products found with case-insensitive 'jr'")
        
        # Get Sucursal Centro ID
        print(f"\n🏪 Getting Sucursal Centro information:")
        sucursal_statement = select(Local).where(Local.nombre.ilike("%centro%"))
        sucursal_result = session.exec(sucursal_statement)
        sucursal_centro = sucursal_result.first()
        
        if sucursal_centro:
            print(f"   ✅ Sucursal Centro found:")
            print(f"      Name: {sucursal_centro.nombre}")
            print(f"      ID: {sucursal_centro.id}")
            print(f"      Tienda ID: {sucursal_centro.tienda_id}")
            
            # Check products with stock in Sucursal Centro
            print(f"\n📦 Products with stock in Sucursal Centro:")
            products_in_centro_statement = select(StockLocal).where(StockLocal.local_id == sucursal_centro.id)
            products_result = session.exec(products_in_centro_statement)
            products_in_centro = products_result.all()
            
            print(f"   Found {len(products_in_centro)} products with stock in Sucursal Centro:")
            for i, stock in enumerate(products_in_centro[-5:], 1):  # Show last 5
                # Get product info
                product_statement = select(Product).where(Product.id == stock.producto_id)
                product_result = session.exec(product_statement)
                product = product_result.first()
                
                if product:
                    print(f"   {i}. SKU: {product.sku}, Name: {product.nombre}")
                    print(f"      Stock: {stock.cantidad} units")
                    print(f"      Product ID: {product.id}")
                    print()
        else:
            print(f"   ❌ Sucursal Centro not found")
            
            # Show all locals
            print(f"\n🏪 All locals in system:")
            all_locals_statement = select(Local)
            all_locals_result = session.exec(all_locals_statement)
            all_locals = all_locals_result.all()
            
            for local in all_locals:
                print(f"   - {local.nombre} (ID: {local.id})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(investigate_jr_product())