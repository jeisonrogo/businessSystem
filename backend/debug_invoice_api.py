#!/usr/bin/env python3
"""
Debug the invoice API creation issue by testing directly with the endpoint logic
"""

import asyncio
import json
from uuid import UUID
from decimal import Decimal
from datetime import date
from fastapi import HTTPException

from app.infrastructure.database.session import get_session
# from app.infrastructure.auth.auth_dependency import get_current_user_from_token
from app.infrastructure.repositories.factura_repository import SQLFacturaRepository
from app.infrastructure.repositories.cliente_repository import SQLClienteRepository
from app.infrastructure.repositories.product_repository import SQLProductRepository
from app.infrastructure.repositories.inventario_repository import SQLInventarioRepository
from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
from app.infrastructure.repositories.cuenta_contable_repository import SQLCuentaContableRepository
from app.infrastructure.repositories.asiento_contable_repository import SQLAsientoContableRepository
from app.application.use_cases.factura_use_cases import CreateFacturaUseCase
from app.domain.models.facturacion import FacturaCreate, DetalleFacturaCreate

async def debug_invoice_creation():
    """Debug the exact same flow as the API endpoint."""
    session_gen = get_session()
    session = next(session_gen)

    try:
        print("🐛 Debugging invoice API creation...")
        
        # Simulate the exact same request data
        request_data = {
            "cliente_id": "69020189-0a58-4a8c-ba06-f2c840732756",
            "tipo_factura": "VENTA",
            "fecha_emision": "2025-08-24",
            "fecha_vencimiento": "2025-09-23",
            "observaciones": "fsgrtsdfsfas",
            "detalles": [{
                "producto_id": "b825b9cc-f009-46e9-8e57-54c89ba5826e",
                "descripcion_producto": "cables de red",
                "cantidad": 8,
                "precio_unitario": 55000,
                "descuento_porcentaje": 0,
                "porcentaje_iva": 19
            }]
        }
        
        print(f"   Request data: {json.dumps(request_data, indent=2)}")
        
        # Convert to FacturaCreate model
        detalles = []
        for detalle_data in request_data["detalles"]:
            detalle = DetalleFacturaCreate(
                producto_id=UUID(detalle_data["producto_id"]),
                descripcion_producto=detalle_data["descripcion_producto"],
                cantidad=detalle_data["cantidad"],
                precio_unitario=Decimal(str(detalle_data["precio_unitario"])),
                descuento_porcentaje=Decimal(str(detalle_data["descuento_porcentaje"])),
                porcentaje_iva=Decimal(str(detalle_data["porcentaje_iva"]))
            )
            detalles.append(detalle)
        
        factura_data = FacturaCreate(
            cliente_id=UUID(request_data["cliente_id"]),
            tipo_factura=request_data["tipo_factura"],
            fecha_emision=date.fromisoformat(request_data["fecha_emision"]),
            fecha_vencimiento=date.fromisoformat(request_data["fecha_vencimiento"]) if request_data.get("fecha_vencimiento") else None,
            observaciones=request_data.get("observaciones"),
            detalles=detalles
        )
        
        print(f"   ✅ FacturaCreate model created successfully")
        
        # Setup repositories (same as API endpoint)
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
        
        print(f"   ✅ Use case created successfully")
        
        # Simulate current user (admin)
        current_user_id = UUID("c03958af-e2f3-4bbd-a2c6-abf9ee7dab20")
        
        # Simulate local_id fallback logic from endpoint
        local_id = None
        if not local_id:
            local_id = UUID("aaaaaaaa-bbbb-cccc-dddd-000000000002")  # Local Principal fallback
        
        print(f"   Using user_id: {current_user_id}")
        print(f"   Using local_id: {local_id}")
        
        # Execute the same logic as the API endpoint
        try:
            factura = await use_case.execute(factura_data, current_user_id, local_id)
            
            print(f"   ✅ Invoice created successfully!")
            print(f"   Invoice ID: {factura.id}")
            print(f"   Invoice number: {factura.numero_factura}")
            print(f"   Total: ${factura.total_factura}")
            print(f"   Details count: {len(factura.detalles)}")
            
            # Check inventory movement creation
            from app.domain.models.movimiento_inventario import MovimientoInventario
            from sqlmodel import select
            
            movements = session.exec(
                select(MovimientoInventario)
                .where(MovimientoInventario.referencia.like(f"%{factura.numero_factura}%"))
            ).all()
            
            print(f"   Inventory movements created: {len(movements)}")
            for mov in movements:
                print(f"   - {mov.tipo_movimiento}: {mov.cantidad} units, Stock: {mov.stock_anterior} → {mov.stock_posterior}")
            
            session.commit()
            
        except Exception as use_case_error:
            print(f"   ❌ Use case error: {use_case_error}")
            print(f"   Error type: {type(use_case_error)}")
            import traceback
            traceback.print_exc()
            session.rollback()
            return
        
        print(f"\n🎉 Debug completed successfully! The API should work now.")

    except Exception as e:
        session.rollback()
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(debug_invoice_creation())