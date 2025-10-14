#!/usr/bin/env python3
"""
Fix missing inventory movement for invoice FV-000005
"""

from app.infrastructure.database.session import get_session
from sqlmodel import Session, select
from app.domain.models.facturacion import Factura, DetalleFactura
from app.domain.models.movimiento_inventario import MovimientoInventario, TipoMovimiento
from app.domain.models.local import Local
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import timedelta

def fix_fv_000005_inventory():
    """Fix missing inventory movement for FV-000005."""
    session_gen = get_session()
    session = next(session_gen)

    try:
        print("🔧 Fixing inventory for FV-000005...")
        
        # Get the invoice FV-000005
        factura = session.exec(
            select(Factura).where(Factura.numero_factura == "FV-000005")
        ).first()
        
        if not factura:
            print("❌ Invoice FV-000005 not found")
            return
        
        print(f"📄 Found invoice FV-000005:")
        print(f"   ID: {factura.id}")
        print(f"   Created: {factura.created_at}")
        print(f"   Current local_id: {factura.local_id}")
        print(f"   Total: ${factura.total_factura}")
        
        # Get invoice details
        details = session.exec(
            select(DetalleFactura).where(DetalleFactura.factura_id == factura.id)
        ).all()
        
        print(f"   Details: {len(details)} items")
        for detail in details:
            print(f"   - Product: {detail.producto_id}, Qty: {detail.cantidad}, Price: ${detail.precio_unitario}")
        
        # Get default local (Local Principal)
        local = session.exec(
            select(Local).order_by(Local.created_at)
        ).first()
        
        if not local:
            print("❌ No local found")
            return
            
        print(f"🏢 Default local: {local.nombre} ({local.id})")
        
        # Update invoice with local_id
        if not factura.local_id:
            factura.local_id = local.id
            session.add(factura)
            print(f"   ✅ Updated invoice with local_id")
        
        # Check if inventory movement already exists
        existing_movement = session.exec(
            select(MovimientoInventario)
            .where(MovimientoInventario.referencia.like(f"%FV-000005%"))
        ).first()
        
        if existing_movement:
            print("   ⚠️ Inventory movement already exists for this invoice")
            session.close()
            return
        
        # Create inventory movements for each detail
        print(f"📦 Creating inventory movements...")
        
        for detail in details:
            # Get current stock for proper stock_anterior calculation
            entradas = session.exec(
                select(MovimientoInventario)
                .where(MovimientoInventario.producto_id == detail.producto_id)
                .where(MovimientoInventario.tipo_movimiento == TipoMovimiento.ENTRADA)
            ).all()
            
            salidas = session.exec(
                select(MovimientoInventario)
                .where(MovimientoInventario.producto_id == detail.producto_id)
                .where(MovimientoInventario.tipo_movimiento == TipoMovimiento.SALIDA)
            ).all()
            
            total_entradas = sum(mov.cantidad for mov in entradas)
            total_salidas = sum(mov.cantidad for mov in salidas)
            stock_anterior = max(0, total_entradas - total_salidas)
            stock_posterior = stock_anterior - detail.cantidad
            
            # Get cost from latest ENTRADA movement
            latest_entrada = session.exec(
                select(MovimientoInventario)
                .where(MovimientoInventario.producto_id == detail.producto_id)
                .where(MovimientoInventario.tipo_movimiento == TipoMovimiento.ENTRADA)
                .order_by(MovimientoInventario.created_at.desc())
            ).first()
            
            costo_unitario = latest_entrada.costo_unitario if latest_entrada else detail.precio_unitario
            
            # Create SALIDA movement
            movement_date = factura.created_at + timedelta(seconds=1)
            
            movimiento = MovimientoInventario(
                id=uuid4(),
                producto_id=detail.producto_id,
                tipo_movimiento=TipoMovimiento.SALIDA,
                cantidad=detail.cantidad,
                precio_unitario=detail.precio_unitario,
                costo_unitario=costo_unitario,
                stock_anterior=stock_anterior,
                stock_posterior=stock_posterior,
                referencia=f"Venta - Factura {factura.numero_factura}",
                observaciones=f"Movimiento de salida creado para migración. Venta según factura {factura.numero_factura}",
                created_at=movement_date,
                created_by=factura.created_by,
                local_id=local.id
            )
            
            session.add(movimiento)
            
            print(f"   ✅ SALIDA: Product {str(detail.producto_id)[:8]}... - Qty: {detail.cantidad}")
            print(f"      Stock: {stock_anterior} → {stock_posterior}")
            print(f"      Cost: ${costo_unitario}")
        
        # Commit changes
        session.commit()
        
        print(f"\n🎉 Successfully fixed inventory for FV-000005!")
        print(f"   - Updated invoice with local_id: {local.id}")
        print(f"   - Created {len(details)} inventory movements")
        
        # Verify the fix
        print(f"\n✅ Verification:")
        movements = session.exec(
            select(MovimientoInventario)
            .where(MovimientoInventario.referencia.like(f"%FV-000005%"))
        ).all()
        
        print(f"   Inventory movements for FV-000005: {len(movements)}")
        for mov in movements:
            print(f"   - {mov.tipo_movimiento}: Qty {mov.cantidad}, Stock: {mov.stock_anterior} → {mov.stock_posterior}")

    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    fix_fv_000005_inventory()