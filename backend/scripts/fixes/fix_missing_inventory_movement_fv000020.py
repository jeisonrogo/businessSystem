#!/usr/bin/env python3
"""
Script para crear el movimiento de inventario faltante para la factura FV-000020.

Esta factura se creó pero no generó su movimiento de inventario correspondiente.
"""

import sys
from pathlib import Path

# Agregar el directorio actual al path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlmodel import Session, select
from app.domain.models.facturacion import Factura, DetalleFactura
from app.domain.models.movimiento_inventario import TipoMovimiento, MovimientoInventarioCreate
from app.domain.models.product import Product
from app.domain.models.stock_local import StockLocal
from app.infrastructure.database.session import get_engine
from app.infrastructure.repositories.inventario_repository import SQLInventarioRepository
from uuid import UUID


async def main():
    """Crear movimiento de inventario faltante para FV-000020."""
    print("🔧 === CREANDO MOVIMIENTO DE INVENTARIO FALTANTE ===")
    
    engine = get_engine()
    
    with Session(engine) as session:
        # Obtener la factura FV-000020
        factura = session.exec(
            select(Factura).where(Factura.numero_factura == "FV-000020")
        ).first()
        
        if not factura:
            print("❌ Factura FV-000020 no encontrada")
            return
        
        print(f"✅ Factura encontrada: {factura.numero_factura}")
        print(f"   Fecha: {factura.fecha_emision}")
        print(f"   Estado: {factura.estado}")
        print(f"   Local ID: {factura.local_id}")
        
        # Obtener los detalles de la factura
        detalles = session.exec(
            select(DetalleFactura).where(DetalleFactura.factura_id == factura.id)
        ).all()
        
        print(f"\\n📋 Detalles de la factura ({len(detalles)}):")
        
        inventario_repo = SQLInventarioRepository(session)
        
        for detalle in detalles:
            print(f"   • Producto: {detalle.descripcion_producto} ({detalle.codigo_producto})")
            print(f"     Cantidad: {detalle.cantidad}")
            print(f"     Precio unitario: ${detalle.precio_unitario}")
            
            # Verificar si ya existe el movimiento
            from app.domain.models.movimiento_inventario import MovimientoInventario
            movimiento_existente = session.exec(
                select(MovimientoInventario).where(
                    MovimientoInventario.producto_id == detalle.producto_id,
                    MovimientoInventario.referencia.like(f"%{factura.numero_factura}%")
                )
            ).first()
            
            if movimiento_existente:
                print(f"     ⚠️  Movimiento ya existe: {movimiento_existente.id}")
                continue
            
            # Obtener información del producto
            producto = session.exec(
                select(Product).where(Product.id == detalle.producto_id)
            ).first()
            
            if not producto:
                print(f"     ❌ Producto {detalle.producto_id} no encontrado")
                continue
            
            # Obtener stock local actual para calcular stock anterior
            stock_local = session.exec(
                select(StockLocal).where(
                    StockLocal.producto_id == detalle.producto_id,
                    StockLocal.local_id == factura.local_id
                )
            ).first()
            
            # El stock actual es el resultado después de la venta
            # Necesitamos calcular el stock anterior sumando lo que se vendió
            stock_posterior = stock_local.cantidad if stock_local else 0
            stock_anterior = stock_posterior + detalle.cantidad  # Lo que había antes de la venta
            
            print(f"     📊 Stock anterior: {stock_anterior} -> Stock posterior: {stock_posterior}")
            
            # Crear el movimiento de inventario
            movimiento_data = MovimientoInventarioCreate(
                producto_id=detalle.producto_id,
                local_id=factura.local_id,
                tipo_movimiento=TipoMovimiento.SALIDA,
                cantidad=detalle.cantidad,
                precio_unitario=detalle.precio_unitario,
                costo_unitario=producto.precio_base,
                stock_anterior=stock_anterior,
                stock_posterior=stock_posterior,
                referencia=f"Venta - Factura {factura.numero_factura}",
                observaciones=f"Movimiento creado para corregir factura {factura.numero_factura} - Venta de producto según factura",
                created_by=factura.created_by
            )
            
            try:
                # Crear el movimiento usando el repositorio
                movimiento = await inventario_repo.create_movimiento(movimiento_data)
                print(f"     ✅ Movimiento creado: {movimiento.id}")
                
            except Exception as e:
                print(f"     ❌ Error al crear movimiento: {str(e)}")
                session.rollback()
                return
        
        # Confirmar cambios
        session.commit()
        print(f"\\n🎉 === MOVIMIENTOS CREADOS EXITOSAMENTE ===")
        print(f"📋 Ahora puedes consultar el kardex del producto PROD001")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())