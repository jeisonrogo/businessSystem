#!/usr/bin/env python3
"""
Check recent invoices for PROD001 to find the problematic one
"""

from app.infrastructure.database.session import get_session
from sqlmodel import Session, select
from app.domain.models.facturacion import Factura

session_gen = get_session()
session = next(session_gen)

try:
    # Find recent invoices
    recent_facturas = session.exec(
        select(Factura)
        .where(Factura.numero_factura.like("FV-%"))
        .order_by(Factura.created_at.desc())
        .limit(15)
    ).all()
    
    print("📋 Recent Invoices:")
    problem_product_id = "9ff11ab8-dc6d-428a-83c4-c59994427fca"
    
    for factura in recent_facturas:
        print(f"   {factura.numero_factura} | Created: {factura.created_at} | Local: {factura.local_id} | Total: ${factura.total_factura}")
        
        # Check if this invoice has our problem product
        for detalle in factura.detalles:
            if str(detalle.producto_id) == problem_product_id:
                print(f"     -> Contains PROD001: {detalle.cantidad} units")
                if detalle.cantidad >= 50:
                    print(f"     -> 🚨 FOUND PROBLEMATIC INVOICE: {factura.numero_factura}")
                    print(f"        Local ID: {factura.local_id}")
                    print(f"        Client ID: {factura.cliente_id}")
                    print(f"        Created by: {factura.created_by}")
                    print(f"        Invoice ID: {factura.id}")
                    
finally:
    session.close()