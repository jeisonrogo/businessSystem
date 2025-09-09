#!/usr/bin/env python3
"""
Test the actual invoice creation flow to reproduce the bug
"""

import asyncio
from uuid import UUID
from decimal import Decimal

from app.infrastructure.database.session import get_session
from app.application.use_cases.factura_use_cases import CreateFacturaUseCase
from app.infrastructure.repositories.factura_repository import SQLFacturaRepository
from app.infrastructure.repositories.cliente_repository import SQLClienteRepository
from app.infrastructure.repositories.product_repository import SQLProductRepository
from app.infrastructure.repositories.inventario_repository import SQLInventarioRepository
from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
from app.domain.models.facturacion import FacturaCreate, DetalleFacturaCreate, TipoFactura

async def test_invoice_creation():
    """Test invoice creation with the problematic scenario."""
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        print("🧪 Testing invoice creation flow...")
        
        # Test data from user's issue
        product_id = UUID("9ff11ab8-dc6d-428a-83c4-c59994427fca")  # PROD001
        local_sucursal_centro = UUID("95a4fc43-46ef-4512-8547-9215d61631fb")
        local_principal = UUID("aaaaaaaa-bbbb-cccc-dddd-000000000002")
        cliente_id = UUID("69020189-0a58-4a8c-ba06-f2c840732756")
        
        # Check stock in both locals
        stock_repo = StockLocalRepository(session)
        
        stock_sucursal = stock_repo.get_by_producto_and_local(product_id, local_sucursal_centro)
        stock_principal = stock_repo.get_by_producto_and_local(product_id, local_principal)
        
        print(f"📍 Stock Status:")
        print(f"   Sucursal Centro: {stock_sucursal.cantidad if stock_sucursal else 'N/A'}")
        print(f"   Local Principal: {stock_principal.cantidad if stock_principal else 'N/A'}")
        
        # Create repositories
        factura_repo = SQLFacturaRepository(session)
        cliente_repo = SQLClienteRepository(session)
        product_repo = SQLProductRepository(session)
        inventario_repo = SQLInventarioRepository(session, product_repo, stock_repo)
        
        # Create invoice data (the same as user's request)
        invoice_data = FacturaCreate(
            cliente_id=cliente_id,
            tipo_factura=TipoFactura.VENTA,
            detalles=[
                DetalleFacturaCreate(
                    producto_id=product_id,
                    cantidad=50,  # This should fail!
                    precio_unitario=Decimal("55000.00"),
                    descuento_porcentaje=0,
                    porcentaje_iva=19
                )
            ]
        )
        
        use_case = CreateFacturaUseCase(
            factura_repo, cliente_repo, product_repo, inventario_repo
        )
        
        # Test 1: Try creating with Sucursal Centro context (should fail)
        print(f"\n🧪 Test 1: Creating invoice with Sucursal Centro local_id")
        try:
            factura = await use_case.execute(
                invoice_data, 
                created_by=UUID("12345678-1234-1234-1234-123456789abc"),  # dummy user
                local_id=local_sucursal_centro
            )
            print(f"   ❌ ERROR: Invoice creation should have failed but succeeded!")
            print(f"   Invoice number: {factura.numero_factura}")
            
        except ValueError as e:
            print(f"   ✅ SUCCESS: Invoice creation failed as expected")
            print(f"   Error: {str(e)}")
        except Exception as e:
            print(f"   ❓ UNEXPECTED ERROR: {str(e)}")
        
        # Test 2: Try creating with Local Principal context (might pass due to higher stock)
        print(f"\n🧪 Test 2: Creating invoice with Local Principal local_id")
        try:
            factura = await use_case.execute(
                invoice_data, 
                created_by=UUID("12345678-1234-1234-1234-123456789abc"),  # dummy user
                local_id=local_principal
            )
            print(f"   ✅ SUCCESS: Invoice created (expected due to higher stock)")
            print(f"   Invoice number: {factura.numero_factura}")
            
            # Clean up - delete this test invoice
            session.delete(factura)
            session.commit()
            
        except ValueError as e:
            print(f"   ❌ FAILED: {str(e)}")
        except Exception as e:
            print(f"   ❓ UNEXPECTED ERROR: {str(e)}")
        
        # Test 3: Try creating with None local_id (this is the likely bug source)
        print(f"\n🧪 Test 3: Creating invoice with None local_id (bug source)")
        try:
            factura = await use_case.execute(
                invoice_data, 
                created_by=UUID("12345678-1234-1234-1234-123456789abc"),  # dummy user
                local_id=None
            )
            print(f"   ❌ ERROR: Invoice creation should have failed but succeeded!")
            print(f"   Invoice number: {factura.numero_factura}")
            print(f"   🚨 BUG CONFIRMED: None local_id bypasses stock validation!")
            
            # Clean up
            session.delete(factura)
            session.commit()
            
        except ValueError as e:
            print(f"   ✅ SUCCESS: Invoice creation failed as expected")
            print(f"   Error: {str(e)}")
        except Exception as e:
            print(f"   ❓ UNEXPECTED ERROR: {str(e)}")
        
        print(f"\n🔍 CONCLUSION:")
        print(f"   The user's invoice was likely created with wrong local_id context")
        print(f"   or the fallback logic didn't work as expected.")
        
    except Exception as e:
        print(f"❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(test_invoice_creation())