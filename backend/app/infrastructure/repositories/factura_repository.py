"""
Implementación del repositorio de facturas usando SQLModel/PostgreSQL.
Maneja la persistencia de facturas con integración a inventario y contabilidad.
"""

from typing import List, Optional
from uuid import UUID
from datetime import date, datetime, UTC
from decimal import Decimal
from sqlmodel import Session, select, and_, func, or_, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.application.services.i_factura_repository import IFacturaRepository
from app.domain.models.facturacion import (
    Factura,
    FacturaCreate,
    FacturaUpdate,
    DetalleFactura,
    DetalleFacturaCreate,
    EstadoFactura,
    TipoFactura,
    generar_numero_factura,
    calcular_totales_factura
)
from app.domain.models.product import Product


class SQLFacturaRepository(IFacturaRepository):
    """
    Implementación del repositorio de facturas usando SQLModel/PostgreSQL.
    """
    
    def __init__(self, session: Session):
        self.session = session

    async def create(self, factura_data: FacturaCreate, created_by: Optional[UUID] = None) -> Factura:
        """Crear una nueva factura con sus detalles."""
        try:
            # Generar número consecutivo
            numero_factura = await self.generar_numero_consecutivo()
            
            # Validar stock disponible para todos los productos
            await self._validar_stock_productos(factura_data.detalles)
            
            # Calcular totales de la factura
            totales = calcular_totales_factura(factura_data.detalles)
            
            # Crear la factura principal
            factura_dict = factura_data.model_dump(exclude={'detalles'})
            factura_dict.update({
                'numero_factura': numero_factura,
                'prefijo': 'FV',
                'subtotal': totales['subtotal'],
                'total_descuento': totales['total_descuento'],
                'total_impuestos': totales['total_impuestos'],
                'total_factura': totales['total_factura'],
                'estado': EstadoFactura.EMITIDA,  # Las facturas se crean emitidas
                'created_by': created_by,
                'created_at': datetime.now(UTC)
            })
            
            factura = Factura(**factura_dict)
            self.session.add(factura)
            self.session.flush()  # Para obtener el ID
            
            # Crear los detalles de la factura
            detalles_creados = []
            for detalle_data in factura_data.detalles:
                # Obtener información del producto
                producto = await self._get_producto(detalle_data.producto_id)
                if not producto:
                    raise ValueError(f"Producto {detalle_data.producto_id} no encontrado")
                
                # Calcular totales del detalle
                totales_detalle = self._calcular_totales_detalle(detalle_data)
                
                # Crear el detalle
                detalle_dict = detalle_data.model_dump()
                detalle_dict.update({
                    'factura_id': factura.id,
                    'descripcion_producto': producto.nombre,
                    'codigo_producto': producto.sku,
                    **totales_detalle
                })
                
                detalle = DetalleFactura(**detalle_dict)
                self.session.add(detalle)
                detalles_creados.append(detalle)
                
                # Actualizar stock del producto
                await self._actualizar_stock_producto(producto.id, detalle_data.cantidad)
            
            self.session.commit()
            
            # Retornar la factura completa con detalles
            return await self.get_by_id(factura.id)
        
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error al crear la factura: {str(e)}")

    async def get_by_id(self, factura_id: UUID) -> Optional[Factura]:
        """Obtener una factura por su ID con detalles cargados."""
        statement = (
            select(Factura)
            .options(
                selectinload(Factura.detalles),
                selectinload(Factura.cliente)
            )
            .where(Factura.id == factura_id)
        )
        result = self.session.exec(statement)
        return result.first()

    async def get_by_numero(self, numero_factura: str) -> Optional[Factura]:
        """Obtener una factura por su número."""
        statement = (
            select(Factura)
            .options(
                selectinload(Factura.detalles),
                selectinload(Factura.cliente)
            )
            .where(Factura.numero_factura == numero_factura)
        )
        result = self.session.exec(statement)
        return result.first()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        cliente_id: Optional[UUID] = None,
        estado: Optional[EstadoFactura] = None,
        tipo_factura: Optional[TipoFactura] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        search: Optional[str] = None
    ) -> List[Factura]:
        """Obtener lista paginada de facturas con filtros opcionales."""
        statement = (
            select(Factura)
            .options(
                selectinload(Factura.cliente),
                selectinload(Factura.detalles)
            )
            .offset(skip)
            .limit(limit)
            .order_by(desc(Factura.fecha_emision), desc(Factura.created_at))
        )
        
        # Aplicar filtros
        conditions = []
        
        if cliente_id:
            conditions.append(Factura.cliente_id == cliente_id)
        
        if estado:
            conditions.append(Factura.estado == estado)
        
        if tipo_factura:
            conditions.append(Factura.tipo_factura == tipo_factura)
        
        if fecha_desde:
            conditions.append(Factura.fecha_emision >= fecha_desde)
        
        if fecha_hasta:
            conditions.append(Factura.fecha_emision <= fecha_hasta)
        
        if search:
            # Buscar en número de factura y datos del cliente
            from app.domain.models.facturacion import Cliente
            search_pattern = f"%{search}%"
            statement = statement.join(Cliente, Factura.cliente_id == Cliente.id)
            search_conditions = or_(
                Factura.numero_factura.ilike(search_pattern),
                Cliente.nombre_completo.ilike(search_pattern),
                Cliente.numero_documento.ilike(search_pattern)
            )
            conditions.append(search_conditions)
        
        if conditions:
            statement = statement.where(and_(*conditions))
        
        result = self.session.exec(statement)
        return list(result.all())

    async def update(self, factura_id: UUID, factura_data: FacturaUpdate) -> Optional[Factura]:
        """Actualizar una factura existente."""
        try:
            # Obtener factura sin detalles para evitar conflictos de sesión
            statement = select(Factura).where(Factura.id == factura_id)
            result = self.session.exec(statement)
            factura = result.first()
            
            if not factura:
                return None
            
            # Solo permitir actualizar ciertas facturas (no pagadas ni anuladas)
            if factura.estado in [EstadoFactura.PAGADA, EstadoFactura.ANULADA]:
                raise ValueError(f"No se puede modificar una factura en estado {factura.estado}")
            
            # Si se proporcionan nuevos detalles, procesarlos
            if factura_data.detalles is not None:
                # 1. Obtener detalles antiguos para revertir stock
                statement_detalles = select(DetalleFactura).where(DetalleFactura.factura_id == factura_id)
                detalles_antiguos = list(self.session.exec(statement_detalles))
                
                # 2. Revertir stock de los detalles antiguos
                for detalle_antiguo in detalles_antiguos:
                    await self._revertir_stock_producto(detalle_antiguo.producto_id, detalle_antiguo.cantidad)
                
                # 3. Validar stock disponible para todos los nuevos productos
                await self._validar_stock_productos(factura_data.detalles)
                
                # 4. Eliminar detalles antiguos
                from sqlmodel import delete
                statement_delete = delete(DetalleFactura).where(DetalleFactura.factura_id == factura_id)
                self.session.exec(statement_delete)
                
                # 5. Crear los nuevos detalles
                for detalle_data in factura_data.detalles:
                    # Obtener información del producto
                    producto = await self._get_producto(detalle_data.producto_id)
                    if not producto:
                        raise ValueError(f"Producto {detalle_data.producto_id} no encontrado")
                    
                    # Calcular totales del detalle
                    totales_detalle = self._calcular_totales_detalle(detalle_data)
                    
                    # Crear el detalle
                    detalle_dict = detalle_data.model_dump()
                    detalle_dict.update({
                        'factura_id': factura.id,
                        'descripcion_producto': producto.nombre,
                        'codigo_producto': producto.sku,
                        **totales_detalle
                    })
                    
                    detalle = DetalleFactura(**detalle_dict)
                    self.session.add(detalle)
                    
                    # Actualizar stock del producto
                    await self._actualizar_stock_producto(producto.id, detalle_data.cantidad)
                
                # 6. Recalcular totales de la factura
                totales = calcular_totales_factura(factura_data.detalles)
                factura.subtotal = totales['subtotal']
                factura.total_descuento = totales['total_descuento']
                factura.total_impuestos = totales['total_impuestos']
                factura.total_factura = totales['total_factura']
            
            # Actualizar campos básicos
            update_data = factura_data.model_dump(exclude_unset=True, exclude={'detalles'})
            update_data['updated_at'] = datetime.now(UTC)
            
            for field, value in update_data.items():
                if hasattr(factura, field):
                    setattr(factura, field, value)
            
            self.session.add(factura)
            self.session.commit()
            
            # Retornar la factura completa actualizada
            return await self.get_by_id(factura.id)
        
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error al actualizar la factura: {str(e)}")

    async def delete(self, factura_id: UUID) -> bool:
        """Anular una factura."""
        try:
            factura = await self.get_by_id(factura_id)
            if not factura:
                return False
            
            if factura.estado == EstadoFactura.ANULADA:
                raise ValueError("La factura ya está anulada")
            
            # Revertir stock de los productos
            for detalle in factura.detalles:
                await self._revertir_stock_producto(detalle.producto_id, detalle.cantidad)
            
            # Cambiar estado a anulada
            factura.estado = EstadoFactura.ANULADA
            factura.updated_at = datetime.now(UTC)
            
            self.session.add(factura)
            self.session.commit()
            
            return True
        
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error al anular la factura: {str(e)}")

    async def count_total(
        self,
        cliente_id: Optional[UUID] = None,
        estado: Optional[EstadoFactura] = None,
        tipo_factura: Optional[TipoFactura] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        search: Optional[str] = None
    ) -> int:
        """Contar el número total de facturas que cumplen los criterios."""
        statement = select(func.count(Factura.id))
        
        # Aplicar los mismos filtros que get_all
        conditions = []
        
        if cliente_id:
            conditions.append(Factura.cliente_id == cliente_id)
        
        if estado:
            conditions.append(Factura.estado == estado)
        
        if tipo_factura:
            conditions.append(Factura.tipo_factura == tipo_factura)
        
        if fecha_desde:
            conditions.append(Factura.fecha_emision >= fecha_desde)
        
        if fecha_hasta:
            conditions.append(Factura.fecha_emision <= fecha_hasta)
        
        if search:
            from app.domain.models.facturacion import Cliente
            search_pattern = f"%{search}%"
            statement = statement.join(Cliente, Factura.cliente_id == Cliente.id)
            search_conditions = or_(
                Factura.numero_factura.ilike(search_pattern),
                Cliente.nombre_completo.ilike(search_pattern),
                Cliente.numero_documento.ilike(search_pattern)
            )
            conditions.append(search_conditions)
        
        if conditions:
            statement = statement.where(and_(*conditions))
        
        result = self.session.exec(statement)
        return result.one()

    async def generar_numero_consecutivo(self, prefijo: str = "FV") -> str:
        """Generar el siguiente número consecutivo de factura."""
        consecutivo = await self.get_siguiente_consecutivo(prefijo)
        return generar_numero_factura(prefijo, consecutivo)

    async def get_siguiente_consecutivo(self, prefijo: str = "FV") -> int:
        """Obtener el siguiente número consecutivo disponible."""
        # Buscar el último número usado con este prefijo
        statement = (
            select(func.max(Factura.numero_factura))
            .where(Factura.prefijo == prefijo)
        )
        
        result = self.session.exec(statement).first()
        
        if not result:
            return 1
        
        # Extraer el número del formato "FV-000001"
        try:
            numero_str = result.split('-')[1] if '-' in result else result
            ultimo_numero = int(numero_str)
            return ultimo_numero + 1
        except (ValueError, IndexError):
            return 1

    async def get_facturas_vencidas(self, fecha_corte: Optional[date] = None) -> List[Factura]:
        """Obtener facturas vencidas que no han sido pagadas."""
        if fecha_corte is None:
            fecha_corte = date.today()
        
        statement = (
            select(Factura)
            .options(selectinload(Factura.cliente))
            .where(
                and_(
                    Factura.estado == EstadoFactura.EMITIDA,
                    Factura.fecha_vencimiento.is_not(None),
                    Factura.fecha_vencimiento < fecha_corte
                )
            )
            .order_by(Factura.fecha_vencimiento)
        )
        
        result = self.session.exec(statement)
        return list(result.all())

    async def get_facturas_por_cliente(
        self,
        cliente_id: UUID,
        skip: int = 0,
        limit: int = 50,
        estado: Optional[EstadoFactura] = None
    ) -> List[Factura]:
        """Obtener facturas de un cliente específico."""
        statement = (
            select(Factura)
            .where(Factura.cliente_id == cliente_id)
            .offset(skip)
            .limit(limit)
            .order_by(desc(Factura.fecha_emision))
        )
        
        if estado:
            statement = statement.where(Factura.estado == estado)
        
        result = self.session.exec(statement)
        return list(result.all())

    async def get_resumen_ventas(
        self,
        fecha_desde: date,
        fecha_hasta: date,
        cliente_id: Optional[UUID] = None
    ) -> dict:
        """Obtener resumen de ventas para un período."""
        conditions = [
            Factura.fecha_emision >= fecha_desde,
            Factura.fecha_emision <= fecha_hasta,
            Factura.estado.in_([EstadoFactura.EMITIDA, EstadoFactura.PAGADA])
        ]
        
        if cliente_id:
            conditions.append(Factura.cliente_id == cliente_id)
        
        statement = (
            select(
                func.count(Factura.id).label('total_facturas'),
                func.coalesce(func.sum(Factura.total_factura), 0).label('total_ventas'),
                func.coalesce(func.sum(Factura.total_impuestos), 0).label('total_impuestos'),
                func.coalesce(func.avg(Factura.total_factura), 0).label('promedio_venta')
            )
            .where(and_(*conditions))
        )
        
        result = self.session.exec(statement).first()
        
        # Facturas por estado (incluir TODAS las facturas, incluyendo ANULADA)
        conditions_estados = [
            Factura.fecha_emision >= fecha_desde,
            Factura.fecha_emision <= fecha_hasta
        ]
        
        if cliente_id:
            conditions_estados.append(Factura.cliente_id == cliente_id)
        
        statement_estados = (
            select(
                Factura.estado,
                func.count(Factura.id).label('cantidad')
            )
            .where(and_(*conditions_estados))
            .group_by(Factura.estado)
        )
        
        estados_result = self.session.exec(statement_estados).all()
        # Convertir estados a formato string limpio (e.g., "PAGADA" en lugar de "EstadoFactura.PAGADA")
        facturas_por_estado = {row.estado.value if hasattr(row.estado, 'value') else str(row.estado).split('.')[-1]: row.cantidad for row in estados_result}
        
        return {
            "total_facturas": int(result.total_facturas) if result else 0,
            "total_ventas": float(result.total_ventas) if result else 0.0,
            "total_impuestos": float(result.total_impuestos) if result else 0.0,
            "promedio_venta": float(result.promedio_venta) if result else 0.0,
            "facturas_por_estado": facturas_por_estado
        }

    async def get_productos_mas_vendidos(
        self,
        fecha_desde: date,
        fecha_hasta: date,
        limit: int = 10
    ) -> List[dict]:
        """Obtener los productos más vendidos en un período."""
        statement = (
            select(
                DetalleFactura.producto_id,
                DetalleFactura.descripcion_producto,
                DetalleFactura.codigo_producto,
                func.sum(DetalleFactura.cantidad).label('total_vendido'),
                func.sum(DetalleFactura.total_item).label('total_ingresos'),
                func.count(DetalleFactura.id).label('veces_vendido')
            )
            .join(Factura, DetalleFactura.factura_id == Factura.id)
            .where(
                and_(
                    Factura.fecha_emision >= fecha_desde,
                    Factura.fecha_emision <= fecha_hasta,
                    Factura.estado.in_([EstadoFactura.EMITIDA, EstadoFactura.PAGADA])
                )
            )
            .group_by(
                DetalleFactura.producto_id,
                DetalleFactura.descripcion_producto,
                DetalleFactura.codigo_producto
            )
            .order_by(desc(func.sum(DetalleFactura.cantidad)))
            .limit(limit)
        )
        
        result = self.session.exec(statement).all()
        
        return [
            {
                "producto_id": str(row.producto_id),
                "descripcion": row.descripcion_producto,
                "codigo": row.codigo_producto,
                "total_vendido": int(row.total_vendido),
                "total_ingresos": float(row.total_ingresos),
                "veces_vendido": int(row.veces_vendido)
            }
            for row in result
        ]

    async def get_clientes_top(
        self,
        fecha_desde: date,
        fecha_hasta: date,
        limit: int = 10
    ) -> List[dict]:
        """Obtener los clientes con más compras/facturación en un período."""
        from app.domain.models.facturacion import Cliente
        
        statement = (
            select(
                Cliente.id,
                Cliente.nombre_completo,
                Cliente.numero_documento,
                func.count(Factura.id).label('total_facturas'),
                func.sum(Factura.total_factura).label('total_compras')
            )
            .join(Factura, Cliente.id == Factura.cliente_id)
            .where(
                and_(
                    Factura.fecha_emision >= fecha_desde,
                    Factura.fecha_emision <= fecha_hasta,
                    Factura.estado.in_([EstadoFactura.EMITIDA, EstadoFactura.PAGADA])
                )
            )
            .group_by(Cliente.id, Cliente.nombre_completo, Cliente.numero_documento)
            .order_by(desc(func.sum(Factura.total_factura)))
            .limit(limit)
        )
        
        result = self.session.exec(statement).all()
        
        return [
            {
                "cliente_id": str(row.id),
                "nombre": row.nombre_completo,
                "documento": row.numero_documento,
                "total_facturas": int(row.total_facturas),
                "total_compras": float(row.total_compras)
            }
            for row in result
        ]

    async def cambiar_estado_factura(
        self,
        factura_id: UUID,
        nuevo_estado: EstadoFactura
    ) -> bool:
        """Cambiar el estado de una factura."""
        try:
            factura = await self.get_by_id(factura_id)
            if not factura:
                return False
            
            # Validar transiciones de estado
            if factura.estado == EstadoFactura.ANULADA:
                raise ValueError("No se puede cambiar el estado de una factura anulada")
            
            if factura.estado == EstadoFactura.PAGADA and nuevo_estado != EstadoFactura.ANULADA:
                raise ValueError("Solo se puede anular una factura pagada")
            
            factura.estado = nuevo_estado
            factura.updated_at = datetime.now(UTC)
            
            self.session.add(factura)
            self.session.commit()
            
            return True
        
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error al cambiar estado de factura: {str(e)}")

    async def marcar_como_pagada(
        self,
        factura_id: UUID,
        fecha_pago: Optional[datetime] = None
    ) -> bool:
        """Marcar una factura como pagada."""
        return await self.cambiar_estado_factura(factura_id, EstadoFactura.PAGADA)

    async def get_valor_cartera(
        self,
        cliente_id: Optional[UUID] = None,
        solo_vencida: bool = False
    ) -> dict:
        """Calcular el valor de la cartera (facturas pendientes de pago)."""
        conditions = [Factura.estado == EstadoFactura.EMITIDA]
        
        if cliente_id:
            conditions.append(Factura.cliente_id == cliente_id)
        
        if solo_vencida:
            conditions.append(
                and_(
                    Factura.fecha_vencimiento.is_not(None),
                    Factura.fecha_vencimiento < date.today()
                )
            )
        
        statement = (
            select(
                func.count(Factura.id).label('cantidad_facturas'),
                func.coalesce(func.sum(Factura.total_factura), 0).label('valor_total'),
                func.coalesce(func.avg(Factura.total_factura), 0).label('promedio')
            )
            .where(and_(*conditions))
        )
        
        result = self.session.exec(statement).first()
        
        return {
            "cantidad_facturas": int(result.cantidad_facturas) if result else 0,
            "valor_total": float(result.valor_total) if result else 0.0,
            "promedio": float(result.promedio) if result else 0.0
        }

    async def get_estadisticas_facturacion(
        self,
        fecha_desde: date,
        fecha_hasta: date
    ) -> dict:
        """Obtener estadísticas completas de facturación para un período."""
        resumen = await self.get_resumen_ventas(fecha_desde, fecha_hasta)
        productos_top = await self.get_productos_mas_vendidos(fecha_desde, fecha_hasta)
        clientes_top = await self.get_clientes_top(fecha_desde, fecha_hasta)
        cartera = await self.get_valor_cartera()
        cartera_vencida = await self.get_valor_cartera(solo_vencida=True)
        
        return {
            "resumen_ventas": resumen,
            "productos_mas_vendidos": productos_top,
            "clientes_top": clientes_top,
            "cartera_total": cartera,
            "cartera_vencida": cartera_vencida
        }

    async def existe_numero_factura(self, numero_factura: str) -> bool:
        """Verificar si existe una factura con el número dado."""
        statement = select(Factura.id).where(Factura.numero_factura == numero_factura)
        result = self.session.exec(statement)
        return result.first() is not None

    # Métodos auxiliares privados
    
    async def _validar_stock_productos(self, detalles: List[DetalleFacturaCreate]) -> None:
        """Validar que hay suficiente stock para todos los productos."""
        for detalle in detalles:
            producto = await self._get_producto(detalle.producto_id)
            if not producto:
                raise ValueError(f"Producto {detalle.producto_id} no encontrado")
            
            if producto.stock < detalle.cantidad:
                raise ValueError(
                    f"Stock insuficiente para {producto.nombre}. "
                    f"Disponible: {producto.stock}, Solicitado: {detalle.cantidad}"
                )

    async def _get_producto(self, producto_id: UUID) -> Optional[Product]:
        """Obtener un producto por ID."""
        statement = select(Product).where(Product.id == producto_id)
        result = self.session.exec(statement)
        return result.first()

    async def _actualizar_stock_producto(self, producto_id: UUID, cantidad_vendida: int) -> None:
        """Actualizar el stock de un producto después de una venta."""
        producto = await self._get_producto(producto_id)
        if producto:
            producto.stock -= cantidad_vendida
            self.session.add(producto)

    async def _revertir_stock_producto(self, producto_id: UUID, cantidad_devolver: int) -> None:
        """Revertir el stock de un producto (usado en anulaciones)."""
        producto = await self._get_producto(producto_id)
        if producto:
            producto.stock += cantidad_devolver
            self.session.add(producto)

    def _calcular_totales_detalle(self, detalle: DetalleFacturaCreate) -> dict:
        """Calcular los totales de un detalle de factura."""
        subtotal_item = Decimal(str(detalle.cantidad)) * detalle.precio_unitario
        
        # Calcular descuento
        if detalle.descuento_porcentaje > 0:
            valor_descuento = subtotal_item * (detalle.descuento_porcentaje / 100)
            descuento_valor = valor_descuento
        else:
            valor_descuento = Decimal("0.00")
            descuento_valor = Decimal("0.00")
        
        # Base gravable después del descuento
        base_gravable = subtotal_item - valor_descuento
        
        # Calcular IVA
        if detalle.porcentaje_iva > 0:
            valor_iva = base_gravable * (detalle.porcentaje_iva / 100)
        else:
            valor_iva = Decimal("0.00")
        
        # Total del item
        total_item = base_gravable + valor_iva
        
        return {
            "subtotal_item": subtotal_item,
            "descuento_valor": descuento_valor,
            "valor_descuento": valor_descuento,
            "base_gravable": base_gravable,
            "valor_iva": valor_iva,
            "total_item": total_item
        }