#!/usr/bin/env python3
"""
Data migration script to fix missing inventory movements from existing invoices.

This script will:
1. Find all invoices that don't have corresponding inventory movements
2. Create initial ENTRADA movements to establish cost basis for each product
3. Create SALIDA movements for each invoice detail that lacks inventory tracking
4. Assign appropriate local_id based on multi-tenant context
"""

from app.infrastructure.database.session import get_session
from sqlmodel import Session, select, func
from app.domain.models.facturacion import Factura, DetalleFactura
from app.domain.models.movimiento_inventario import MovimientoInventario, TipoMovimiento
from app.domain.models.product import Product
from app.domain.models.local import Local
from app.domain.models.user import User
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, UTC, timedelta
import asyncio

class InventoryMigrationService:
    def __init__(self, session: Session):
        self.session = session
        
    def find_invoices_without_movements(self):
        """Find all invoices that don't have corresponding inventory movements."""
        print("🔍 Finding invoices without inventory movements...")
        
        # Get all invoice details
        invoice_details = self.session.exec(
            select(DetalleFactura, Factura)
            .join(Factura, DetalleFactura.factura_id == Factura.id)
            .order_by(Factura.created_at)
        ).all()
        
        print(f"   Found {len(invoice_details)} invoice details total")
        
        missing_movements = []
        for detail, factura in invoice_details:
            # Check if there's a corresponding SALIDA movement for this invoice detail
            movement = self.session.exec(
                select(MovimientoInventario)
                .where(MovimientoInventario.producto_id == detail.producto_id)
                .where(MovimientoInventario.tipo_movimiento == TipoMovimiento.SALIDA)
                .where(MovimientoInventario.referencia.like(f"%{factura.numero_factura}%"))
            ).first()
            
            if not movement:
                missing_movements.append((detail, factura))
                print(f"   Missing movement for: {factura.numero_factura} - Product: {detail.codigo_producto} - Qty: {detail.cantidad}")
        
        print(f"   Total missing movements: {len(missing_movements)}")
        return missing_movements
    
    def get_products_needing_entrada(self, missing_movements):
        """Get unique products that need initial ENTRADA movements."""
        print("\n📦 Identifying products needing initial ENTRADA movements...")
        
        products_needing_entrada = {}
        
        for detail, factura in missing_movements:
            # Check if product already has any ENTRADA movement
            entrada_movement = self.session.exec(
                select(MovimientoInventario)
                .where(MovimientoInventario.producto_id == detail.producto_id)
                .where(MovimientoInventario.tipo_movimiento == TipoMovimiento.ENTRADA)
            ).first()
            
            if not entrada_movement:
                if detail.producto_id not in products_needing_entrada:
                    product = self.session.exec(
                        select(Product).where(Product.id == detail.producto_id)
                    ).first()
                    
                    # Calculate total quantity sold for this product
                    total_sold = self.session.exec(
                        select(func.sum(DetalleFactura.cantidad))
                        .where(DetalleFactura.producto_id == detail.producto_id)
                    ).one() or 0
                    
                    products_needing_entrada[detail.producto_id] = {
                        'product': product,
                        'total_sold': int(total_sold),
                        'base_cost': product.precio_base,
                        'earliest_sale_date': factura.created_at
                    }
                else:
                    # Update with earliest sale date
                    if factura.created_at < products_needing_entrada[detail.producto_id]['earliest_sale_date']:
                        products_needing_entrada[detail.producto_id]['earliest_sale_date'] = factura.created_at
        
        print(f"   Products needing ENTRADA: {len(products_needing_entrada)}")
        for product_id, info in products_needing_entrada.items():
            print(f"   - {info['product'].nombre} ({info['product'].sku}): Total sold: {info['total_sold']}, Base cost: {info['base_cost']}")
        
        return products_needing_entrada
    
    def get_default_local_and_admin(self):
        """Get default local and admin user for migration."""
        print("\n🏢 Getting default local and admin user...")
        
        # Get the first local (Centro)
        local = self.session.exec(
            select(Local).order_by(Local.created_at)
        ).first()
        
        # Get admin user
        admin = self.session.exec(
            select(User).where(User.email.like('%admin%'))
        ).first()
        
        print(f"   Default local: {local.nombre if local else 'None'} ({local.id if local else 'None'})")
        print(f"   Admin user: {admin.email if admin else 'None'} ({admin.id if admin else 'None'})")
        
        return local, admin
    
    def create_entrada_movements(self, products_needing_entrada, local, admin):
        """Create initial ENTRADA movements for products."""
        print("\n📥 Creating initial ENTRADA movements...")
        
        entrada_movements = []
        
        for product_id, info in products_needing_entrada.items():
            # Create ENTRADA movement with enough stock to cover all sales + buffer
            stock_needed = info['total_sold'] + 10  # Add 10 units buffer
            
            # Create movement datetime slightly before the earliest sale
            movement_date = info['earliest_sale_date'].replace(hour=0, minute=0, second=0, microsecond=0)
            
            movimento = MovimientoInventario(
                id=uuid4(),
                producto_id=product_id,
                tipo_movimiento=TipoMovimiento.ENTRADA,
                cantidad=stock_needed,
                precio_unitario=info['base_cost'],
                costo_unitario=info['base_cost'],
                stock_anterior=0,
                stock_posterior=stock_needed,
                referencia="Migración - Stock inicial",
                observaciones=f"Movimiento de entrada inicial creado para migración de datos. Stock para cubrir ventas existentes.",
                created_at=movement_date,
                created_by=admin.id if admin else None,
                local_id=local.id if local else None
            )
            
            entrada_movements.append(movimento)
            print(f"   ENTRADA: {info['product'].nombre} - Qty: {stock_needed} - Cost: {info['base_cost']}")
        
        # Save all ENTRADA movements
        for movement in entrada_movements:
            self.session.add(movement)
        
        self.session.commit()
        print(f"   ✅ Created {len(entrada_movements)} ENTRADA movements")
        
        return entrada_movements
    
    def create_salida_movements(self, missing_movements, local, admin):
        """Create SALIDA movements for missing invoice movements."""
        print("\n📤 Creating SALIDA movements for invoices...")
        
        salida_movements = []
        
        for detail, factura in missing_movements:
            # Get current stock after ENTRADA movements
            stock_actual = self.session.exec(
                select(func.coalesce(func.sum(MovimientoInventario.cantidad), 0))
                .where(MovimientoInventario.producto_id == detail.producto_id)
                .where(MovimientoInventario.tipo_movimiento == TipoMovimiento.ENTRADA)
            ).one() or 0
            
            stock_salidas = self.session.exec(
                select(func.coalesce(func.sum(MovimientoInventario.cantidad), 0))
                .where(MovimientoInventario.producto_id == detail.producto_id)
                .where(MovimientoInventario.tipo_movimiento == TipoMovimiento.SALIDA)
            ).one() or 0
            
            stock_anterior = max(0, stock_actual - stock_salidas)
            stock_posterior = stock_anterior - detail.cantidad
            
            # Get cost from latest ENTRADA movement
            costo_unitario = self.session.exec(
                select(MovimientoInventario.costo_unitario)
                .where(MovimientoInventario.producto_id == detail.producto_id)
                .where(MovimientoInventario.tipo_movimiento == TipoMovimiento.ENTRADA)
                .order_by(MovimientoInventario.created_at.desc())
            ).first()
            
            # Create SALIDA movement
            movement_date = factura.created_at + timedelta(seconds=1)  # Slightly after invoice
            
            movimento = MovimientoInventario(
                id=uuid4(),
                producto_id=detail.producto_id,
                tipo_movimiento=TipoMovimiento.SALIDA,
                cantidad=detail.cantidad,
                precio_unitario=detail.precio_unitario,
                costo_unitario=costo_unitario or detail.precio_unitario,
                stock_anterior=stock_anterior,
                stock_posterior=stock_posterior,
                referencia=f"Venta - Factura {factura.numero_factura}",
                observaciones=f"Movimiento de salida creado para migración. Venta según factura {factura.numero_factura}",
                created_at=movement_date,
                created_by=admin.id if admin else None,
                local_id=local.id if local else None
            )
            
            salida_movements.append(movimento)
            print(f"   SALIDA: {factura.numero_factura} - Product: {detail.codigo_producto} - Qty: {detail.cantidad} - Price: {detail.precio_unitario}")
        
        # Save all SALIDA movements
        for movement in salida_movements:
            self.session.add(movement)
        
        self.session.commit()
        print(f"   ✅ Created {len(salida_movements)} SALIDA movements")
        
        return salida_movements
    
    def update_invoice_local_ids(self, local):
        """Update existing invoices to have local_id assigned."""
        print(f"\n🔄 Updating invoices with local_id...")
        
        invoices_without_local = self.session.exec(
            select(Factura).where(Factura.local_id.is_(None))
        ).all()
        
        print(f"   Found {len(invoices_without_local)} invoices without local_id")
        
        for factura in invoices_without_local:
            factura.local_id = local.id if local else None
        
        self.session.commit()
        print(f"   ✅ Updated {len(invoices_without_local)} invoices with local_id")
    
    def verify_migration(self):
        """Verify that the migration was successful."""
        print(f"\n✅ Verifying migration results...")
        
        # Count invoices vs movements
        total_invoice_details = self.session.exec(
            select(func.count(DetalleFactura.id))
        ).one()
        
        total_salida_movements = self.session.exec(
            select(func.count(MovimientoInventario.id))
            .where(MovimientoInventario.tipo_movimiento == TipoMovimiento.SALIDA)
        ).one()
        
        total_entrada_movements = self.session.exec(
            select(func.count(MovimientoInventario.id))
            .where(MovimientoInventario.tipo_movimiento == TipoMovimiento.ENTRADA)
        ).one()
        
        print(f"   Total invoice details: {total_invoice_details}")
        print(f"   Total SALIDA movements: {total_salida_movements}")
        print(f"   Total ENTRADA movements: {total_entrada_movements}")
        
        # Test the problematic product
        product_id = UUID('b825b9cc-f009-46e9-8e57-54c89ba5826e')
        movements = self.session.exec(
            select(MovimientoInventario)
            .where(MovimientoInventario.producto_id == product_id)
            .order_by(MovimientoInventario.created_at)
        ).all()
        
        print(f"\n📦 Cables de red movements after migration: {len(movements)}")
        for mov in movements:
            print(f"   {mov.tipo_movimiento}: Qty {mov.cantidad} - Stock: {mov.stock_anterior} → {mov.stock_posterior}")

def main():
    """Main migration function."""
    print("🚀 Starting inventory movements migration...")
    
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        migration_service = InventoryMigrationService(session)
        
        # Step 1: Find invoices without movements
        missing_movements = migration_service.find_invoices_without_movements()
        
        if not missing_movements:
            print("✅ No missing movements found. Migration not needed.")
            return
        
        # Step 2: Get products needing ENTRADA movements
        products_needing_entrada = migration_service.get_products_needing_entrada(missing_movements)
        
        # Step 3: Get default local and admin
        local, admin = migration_service.get_default_local_and_admin()
        
        if not local or not admin:
            print("❌ Could not find default local or admin user. Migration aborted.")
            return
        
        # Step 4: Create ENTRADA movements
        if products_needing_entrada:
            migration_service.create_entrada_movements(products_needing_entrada, local, admin)
        
        # Step 5: Create SALIDA movements
        migration_service.create_salida_movements(missing_movements, local, admin)
        
        # Step 6: Update invoice local_ids
        migration_service.update_invoice_local_ids(local)
        
        # Step 7: Verify migration
        migration_service.verify_migration()
        
        print("\n🎉 Migration completed successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    main()