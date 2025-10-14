#!/usr/bin/env python3
"""
Script to investigate the kardex issue for cables de red product
"""

from app.infrastructure.database.session import get_session
from sqlmodel import Session, select
from app.domain.models.facturacion import Factura, DetalleFactura
from app.domain.models.movimiento_inventario import MovimientoInventario
from app.domain.models.product import Product
from uuid import UUID

def investigate_kardex_issue():
    """Investigate kardex issue for cables de red product."""
    session_gen = get_session()
    session = next(session_gen)

    try:
        # Check the specific product kardex issue
        product_id = UUID('b825b9cc-f009-46e9-8e57-54c89ba5826e')  # From user's error

        # Get product info
        product = session.exec(select(Product).where(Product.id == product_id)).first()
        print(f'🔍 Product info:')
        if product:
            print(f'   ID: {product.id}')
            print(f'   Name: {product.nombre}')
            print(f'   SKU: {product.sku}')
            print(f'   Base Price: {product.precio_base}')
            print(f'   Public Price: {product.precio_publico}')
        else:
            print(f'   Product not found with ID: {product_id}')
            return

        # Check invoice details for this product
        invoice_details = session.exec(
            select(DetalleFactura)
            .where(DetalleFactura.producto_id == product_id)
        ).all()

        print(f'\n📋 Invoice details for this product: {len(invoice_details)}')
        total_sold = 0
        for detail in invoice_details:
            factura = session.exec(select(Factura).where(Factura.id == detail.factura_id)).first()
            print(f'   Invoice: {factura.numero_factura if factura else "Unknown"} - Qty: {detail.cantidad} - Price: {detail.precio_unitario} - Local: {factura.local_id if factura else "None"}')
            total_sold += detail.cantidad

        print(f'   Total sold quantity: {total_sold}')

        # Check inventory movements for this product
        movements = session.exec(
            select(MovimientoInventario)
            .where(MovimientoInventario.producto_id == product_id)
        ).all()

        print(f'\n📦 Inventory movements for this product: {len(movements)}')
        for mov in movements:
            print(f'   Type: {mov.tipo_movimiento} - Qty: {mov.cantidad} - Price: {mov.precio_unitario} - Date: {mov.created_at}')

        # Check all products with invoices but no inventory movements
        print(f'\n🔎 Checking all products with sales but no inventory movements:')
        
        # Get all products that have been sold
        sold_products = session.exec(
            select(DetalleFactura.producto_id, Product.nombre, Product.sku)
            .join(Product, DetalleFactura.producto_id == Product.id)
            .distinct()
        ).all()

        print(f'   Products with sales: {len(sold_products)}')
        
        no_movement_count = 0
        for producto_id, nombre, sku in sold_products:
            movements = session.exec(
                select(MovimientoInventario)
                .where(MovimientoInventario.producto_id == producto_id)
            ).all()
            
            if not movements:
                no_movement_count += 1
                print(f'   - {nombre} ({sku}): Has sales but NO inventory movements')
        
        print(f'\nTotal products with sales but no movements: {no_movement_count}')

        session.close()

    except Exception as e:
        session.rollback()
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    investigate_kardex_issue()