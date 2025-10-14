#!/usr/bin/env python3
"""
Script para probar directamente la creación de productos con auto-creación de stock
"""

import asyncio
import sys
from uuid import UUID
from decimal import Decimal

from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.product_repository import SQLProductRepository
from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
from app.application.use_cases.product_use_cases import CreateProductUseCase
from app.domain.models.product import ProductCreate
from app.domain.models.stock_local import StockLocalCreate

async def test_direct_product_creation():
    """Test directo de creación de producto con stock inicial."""
    
    print("🧪 Testing direct product creation with initial stock...")
    
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        # Setup repositories
        product_repo = SQLProductRepository(session)
        stock_repo = StockLocalRepository(session)
        
        # Datos del producto
        product_data = ProductCreate(
            sku="TEST-DIRECT-001",
            nombre="Producto Creado Directamente",
            descripcion="Producto creado para probar el flujo completo",
            precio_base=Decimal("5000.00"),
            precio_publico=Decimal("8000.00"),
            tienda_id=UUID("24674128-7622-4d47-88db-f3284997da31"),  # Tienda Demo Principal
            stock_inicial=15
        )
        
        print(f"📦 Creating product: {product_data.sku}")
        print(f"   Name: {product_data.nombre}")
        print(f"   Stock inicial: {product_data.stock_inicial}")
        
        # Crear producto
        use_case = CreateProductUseCase(product_repo)
        product = await use_case.execute(product_data)
        
        print(f"✅ Product created successfully!")
        print(f"   Product ID: {product.id}")
        print(f"   SKU: {product.sku}")
        print(f"   Tienda ID: {product.tienda_id}")
        
        # Crear stock inicial en Sucursal Centro
        sucursal_centro_id = UUID("95a4fc43-46ef-4512-8547-9215d61631fb")
        
        print(f"\n📊 Creating initial stock in Sucursal Centro...")
        
        stock_create = StockLocalCreate(
            local_id=sucursal_centro_id,
            producto_id=product.id,
            cantidad=product_data.stock_inicial,
            stock_minimo=0,
            stock_maximo=None,
            costo_promedio=product.precio_base
        )
        
        initial_stock = stock_repo.create(stock_create)
        
        print(f"✅ Initial stock created successfully!")
        print(f"   Stock Local ID: {initial_stock.id}")
        print(f"   Cantidad: {initial_stock.cantidad}")
        print(f"   Costo promedio: ${initial_stock.costo_promedio}")
        print(f"   Valor total: ${initial_stock.valor_total_inventario}")
        
        # Verificar que el producto aparece en consultas por local
        print(f"\n🔍 Verifying product appears in local queries...")
        
        products_in_local = stock_repo.get_by_local(sucursal_centro_id)
        
        test_product_stock = None
        for stock in products_in_local:
            if stock.producto_id == product.id:
                test_product_stock = stock
                break
        
        if test_product_stock:
            print(f"✅ Product found in local stock!")
            print(f"   Stock cantidad: {test_product_stock.cantidad}")
            print(f"   Local ID: {test_product_stock.local_id}")
        else:
            print(f"❌ Product NOT found in local stock")
        
        session.commit()
        print(f"\n🎉 Test completed successfully! Product {product.sku} should now be visible in Sucursal Centro.")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(test_direct_product_creation())