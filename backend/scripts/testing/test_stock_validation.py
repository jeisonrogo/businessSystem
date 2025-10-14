#!/usr/bin/env python3
"""
Test stock validation logic for PROD001 issue
"""

import asyncio
from uuid import UUID
from sqlmodel import Session

from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.factura_repository import SQLFacturaRepository
from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
from app.domain.models.facturacion import DetalleFacturaCreate
from decimal import Decimal

async def test_stock_validation():
    """Test the stock validation logic that should have prevented the overselling."""
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        print("🧪 Testing stock validation for PROD001 in Sucursal Centro...")
        
        product_id = UUID("9ff11ab8-dc6d-428a-83c4-c59994427fca")
        local_id = UUID("95a4fc43-46ef-4512-8547-9215d61631fb")
        
        # 1. Check current stock in Sucursal Centro
        stock_repo = StockLocalRepository(session)
        stock_local = stock_repo.get_by_producto_and_local(product_id, local_id)
        
        print(f"📍 Current Stock in Sucursal Centro:")
        if stock_local:
            print(f"   Available: {stock_local.cantidad} units")
        else:
            print("   No stock entry found!")
            return
        
        # 2. Test validation with different quantities
        factura_repo = SQLFacturaRepository(session)
        
        test_cases = [
            {"cantidad": 5, "should_pass": True, "description": "5 units (should pass)"},
            {"cantidad": 8, "should_pass": True, "description": "8 units (exactly available, should pass)"},
            {"cantidad": 10, "should_pass": False, "description": "10 units (should fail)"},
            {"cantidad": 50, "should_pass": False, "description": "50 units (should definitely fail)"}
        ]
        
        print(f"\n🧪 Testing validation scenarios:")
        
        for case in test_cases:
            # Create test detail
            detalle = DetalleFacturaCreate(
                producto_id=product_id,
                cantidad=case["cantidad"],
                precio_unitario=Decimal("55000.00"),
                descuento_porcentaje=0,
                porcentaje_iva=19
            )
            
            try:
                await factura_repo._validar_stock_productos([detalle], local_id)
                result = "✅ PASSED"
                print(f"   {result} - {case['description']}")
                
                if not case["should_pass"]:
                    print(f"   ❌ ERROR: This should have failed but didn't!")
                    
            except ValueError as e:
                result = "❌ FAILED"
                print(f"   {result} - {case['description']}: {str(e)}")
                
                if case["should_pass"]:
                    print(f"   ❌ ERROR: This should have passed but failed!")
        
        # 3. Test with no local_id (this is likely the bug)
        print(f"\n🔍 Testing validation with no local_id (likely bug source):")
        detalle_50 = DetalleFacturaCreate(
            producto_id=product_id,
            cantidad=50,  # Way over available stock
            precio_unitario=Decimal("55000.00"),
            descuento_porcentaje=0,
            porcentaje_iva=19
        )
        
        try:
            await factura_repo._validar_stock_productos([detalle_50], None)  # No local_id
            print("   ✅ PASSED - 50 units with no local_id")
            print("   🚨 BUG FOUND: Validation is skipped when local_id is None!")
            
        except ValueError as e:
            print(f"   ❌ FAILED - 50 units with no local_id: {str(e)}")
            print("   ✅ This is correct behavior")
        
        # 4. Test with wrong local_id
        print(f"\n🔍 Testing validation with Local Principal ID:")
        local_principal_id = UUID("aaaaaaaa-bbbb-cccc-dddd-000000000002")
        
        # Check stock in Local Principal for this product
        stock_principal = stock_repo.get_by_producto_and_local(product_id, local_principal_id)
        print(f"   Stock in Local Principal: {stock_principal.cantidad if stock_principal else 'N/A'}")
        
        try:
            await factura_repo._validar_stock_productos([detalle_50], local_principal_id)
            print("   ✅ PASSED - 50 units in Local Principal")
            print("   📝 This explains why validation passed - wrong local was used!")
            
        except ValueError as e:
            print(f"   ❌ FAILED - 50 units in Local Principal: {str(e)}")
        
        # 5. Summary
        print(f"\n🔍 DIAGNOSIS SUMMARY:")
        print(f"   Product: cables de red 2 (PROD001)")
        print(f"   Sucursal Centro stock: {stock_local.cantidad if stock_local else 'N/A'}")
        print(f"   Local Principal stock: {stock_principal.cantidad if stock_principal else 'N/A'}")
        print(f"   Issue: Validation likely used wrong local or was skipped entirely")
        
    except Exception as e:
        print(f"❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(test_stock_validation())