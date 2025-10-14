#!/usr/bin/env python3
"""
Test direct invoice creation through use case to understand the error
"""

import asyncio
from uuid import UUID
from decimal import Decimal
from datetime import date

from app.infrastructure.database.session import get_session
from app.application.use_cases.factura_use_cases import CreateFacturaUseCase
from app.infrastructure.repositories.factura_repository import SQLFacturaRepository
from app.infrastructure.repositories.cliente_repository import SQLClienteRepository
from app.infrastructure.repositories.product_repository import SQLProductRepository
from app.infrastructure.repositories.inventario_repository import SQLInventarioRepository
from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
from app.infrastructure.repositories.cuenta_contable_repository import SQLCuentaContableRepository
from app.infrastructure.repositories.asiento_contable_repository import SQLAsientoContableRepository
from app.domain.models.facturacion import FacturaCreate, DetalleFacturaCreate

async def test_direct_invoice_creation():
    """Test creating invoice directly through use case."""
    session_gen = get_session()
    session = next(session_gen)

    try:
        print("🧪 Testing direct invoice creation...")
        
        # Setup repositories
        factura_repo = SQLFacturaRepository(session)
        cliente_repo = SQLClienteRepository(session)
        product_repo = SQLProductRepository(session)
        stock_local_repo = StockLocalRepository(session)
        inventario_repo = SQLInventarioRepository(session, product_repo, stock_local_repo)
        cuenta_repo = SQLCuentaContableRepository(session)
        asiento_repo = SQLAsientoContableRepository(session)
        
        # Create use case
        use_case = CreateFacturaUseCase(
            factura_repo, cliente_repo, product_repo,
            inventario_repo, cuenta_repo, asiento_repo
        )
        
        # Create invoice data
        factura_data = FacturaCreate(
            cliente_id=UUID("95c4b5e9-72c5-42a5-94a8-f4fad7116366"),
            tipo_factura="VENTA",
            fecha_emision=date(2025, 8, 24),
            observaciones="Test direct creation",
            detalles=[
                DetalleFacturaCreate(
                    producto_id=UUID("b825b9cc-f009-46e9-8e57-54c89ba5826e"),
                    cantidad=1,
                    precio_unitario=Decimal("55000.00"),
                    descripcion_producto="cables de red",
                    codigo_producto="demo-prueba"
                )
            ]
        )
        
        # Test with local_id
        admin_user_id = UUID("6d3992f0-ff7b-49bc-86be-a1984919d4d5")
        local_id = UUID("aaaaaaaa-bbbb-cccc-dddd-000000000002")
        
        print(f"   Creating invoice with local_id: {local_id}")
        factura = await use_case.execute(factura_data, admin_user_id, local_id)
        
        print(f"   ✅ Invoice created successfully!")
        print(f"   Invoice number: {factura.numero_factura}")
        print(f"   Total: ${factura.total_factura}")
        
        # Check if inventory movement was created
        from app.domain.models.movimiento_inventario import MovimientoInventario
        from sqlmodel import select
        
        movements = session.exec(
            select(MovimientoInventario)
            .where(MovimientoInventario.referencia.like(f"%{factura.numero_factura}%"))
        ).all()
        
        print(f"   Inventory movements: {len(movements)}")
        for mov in movements:
            print(f"   - {mov.tipo_movimiento}: Qty {mov.cantidad}, Stock: {mov.stock_anterior} → {mov.stock_posterior}")
        
        session.commit()
        print(f"   ✅ Test completed successfully!")

    except Exception as e:
        session.rollback()
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(test_direct_invoice_creation())