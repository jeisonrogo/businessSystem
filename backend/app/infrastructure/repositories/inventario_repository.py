"""
Implementación del repositorio de movimientos de inventario usando SQLModel y PostgreSQL.

Implementa todas las operaciones definidas en IInventarioRepository,
aplicando las reglas de negocio correspondientes, especialmente
la lógica de costo promedio ponderado (BR-11).
"""

from datetime import datetime, UTC
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlmodel import Session, select, and_, or_, func, desc
from sqlalchemy.exc import IntegrityError

from app.application.services.i_inventario_repository import IInventarioRepository
from app.application.services.i_product_repository import IProductRepository
from app.domain.models.movimiento_inventario import (
    MovimientoInventario,
    MovimientoInventarioCreate,
    MovimientoInventarioFilter,
    TipoMovimiento,
    CostoPromedioCalculation,
    EstadisticasInventario
)
from app.domain.models.product import Product


class SQLInventarioRepository(IInventarioRepository):
    """
    Implementación del repositorio de movimientos de inventario usando SQLModel y PostgreSQL.
    
    Implementa todas las operaciones CRUD y métodos especializados definidos
    en IInventarioRepository, aplicando las reglas de negocio correspondientes.
    """

    def __init__(self, session: Session, product_repository: IProductRepository):
        self.session = session
        self.product_repository = product_repository

    async def create_movimiento(
        self, 
        movimiento_data: MovimientoInventarioCreate,
        created_by: Optional[UUID] = None
    ) -> MovimientoInventario:
        """
        Crear un nuevo movimiento de inventario.
        
        Implementa la lógica de costo promedio ponderado (BR-11) y actualiza
        automáticamente el stock del producto.
        """
        try:
            # Verificar que el producto existe
            producto = await self.product_repository.get_by_id(movimiento_data.producto_id)
            if not producto:
                raise ValueError(f"Producto con ID {movimiento_data.producto_id} no encontrado")

            # Obtener stock actual
            stock_anterior = await self.get_stock_actual(movimiento_data.producto_id)
            
            # Calcular stock posterior según tipo de movimiento
            if movimiento_data.tipo_movimiento in [TipoMovimiento.ENTRADA, TipoMovimiento.AJUSTE]:
                stock_posterior = stock_anterior + movimiento_data.cantidad
            else:  # SALIDA, MERMA
                stock_posterior = stock_anterior - movimiento_data.cantidad
                
                # Validar BR-01: Stock no puede ser negativo
                if stock_posterior < 0:
                    raise ValueError(
                        f"Stock insuficiente. Stock actual: {stock_anterior}, "
                        f"cantidad solicitada: {movimiento_data.cantidad}"
                    )

            # Calcular costo unitario para el movimiento
            costo_unitario = None
            if movimiento_data.tipo_movimiento == TipoMovimiento.ENTRADA:
                # Para entradas, calcular nuevo costo promedio ponderado
                if stock_anterior > 0:
                    calculo = await self.calcular_costo_promedio(
                        movimiento_data.producto_id,
                        movimiento_data.cantidad,
                        movimiento_data.precio_unitario
                    )
                    costo_unitario = calculo.costo_promedio_nuevo
                else:
                    # Primer entrada, el costo es el precio de entrada
                    costo_unitario = movimiento_data.precio_unitario
            else:
                # Para salidas y mermas, usar el costo promedio actual
                try:
                    costo_unitario = await self.get_costo_promedio_actual(movimiento_data.producto_id)
                except ValueError:
                    # Si no hay costo promedio, usar precio_base del producto
                    costo_unitario = producto.precio_base

            # Crear el movimiento
            movimiento = MovimientoInventario(
                **movimiento_data.model_dump(),
                stock_anterior=stock_anterior,
                stock_posterior=stock_posterior,
                costo_unitario=costo_unitario,
                created_by=created_by
            )

            self.session.add(movimiento)
            self.session.commit()
            self.session.refresh(movimiento)

            # Actualizar stock del producto
            await self.product_repository.update_stock(
                movimiento_data.producto_id, 
                stock_posterior
            )

            return movimiento

        except ValueError as e:
            self.session.rollback()
            raise e
        except IntegrityError as e:
            self.session.rollback()
            if "foreign key" in str(e.orig).lower():
                raise ValueError(f"Producto con ID {movimiento_data.producto_id} no encontrado")
            raise Exception(f"Error de integridad al crear el movimiento: {str(e)}")
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Error al crear el movimiento: {str(e)}")

    async def get_by_id(self, movimiento_id: UUID) -> Optional[MovimientoInventario]:
        """Obtener un movimiento por su ID."""
        try:
            statement = select(MovimientoInventario).where(MovimientoInventario.id == movimiento_id)
            result = self.session.exec(statement)
            return result.first()
        except Exception as e:
            raise Exception(f"Error al obtener el movimiento por ID: {str(e)}")

    async def get_movimientos_by_producto(
        self,
        producto_id: UUID,
        skip: int = 0,
        limit: int = 100,
        tipo_movimiento: Optional[TipoMovimiento] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> List[MovimientoInventario]:
        """Obtener movimientos de un producto específico (Kardex)."""
        try:
            statement = select(MovimientoInventario).where(
                MovimientoInventario.producto_id == producto_id
            )

            # Aplicar filtros opcionales
            if tipo_movimiento:
                statement = statement.where(MovimientoInventario.tipo_movimiento == tipo_movimiento)
            
            if fecha_desde:
                statement = statement.where(MovimientoInventario.created_at >= fecha_desde)
            
            if fecha_hasta:
                statement = statement.where(MovimientoInventario.created_at <= fecha_hasta)

            # Ordenar por fecha descendente (más recientes primero)
            statement = statement.order_by(desc(MovimientoInventario.created_at))
            statement = statement.offset(skip).limit(limit)

            result = self.session.exec(statement)
            return result.all()
        except Exception as e:
            raise Exception(f"Error al obtener movimientos del producto: {str(e)}")

    async def get_all_movimientos(
        self,
        skip: int = 0,
        limit: int = 100,
        filtros: Optional[MovimientoInventarioFilter] = None
    ) -> List[MovimientoInventario]:
        """Obtener lista paginada de todos los movimientos."""
        try:
            statement = select(MovimientoInventario)

            # Aplicar filtros si se proporcionan
            if filtros:
                if filtros.producto_id:
                    statement = statement.where(MovimientoInventario.producto_id == filtros.producto_id)
                
                if filtros.tipo_movimiento:
                    statement = statement.where(MovimientoInventario.tipo_movimiento == filtros.tipo_movimiento)
                
                if filtros.fecha_desde:
                    statement = statement.where(MovimientoInventario.created_at >= filtros.fecha_desde)
                
                if filtros.fecha_hasta:
                    statement = statement.where(MovimientoInventario.created_at <= filtros.fecha_hasta)
                
                if filtros.referencia:
                    statement = statement.where(MovimientoInventario.referencia.ilike(f"%{filtros.referencia}%"))
                
                if filtros.created_by:
                    statement = statement.where(MovimientoInventario.created_by == filtros.created_by)

            # Ordenar por fecha descendente
            statement = statement.order_by(desc(MovimientoInventario.created_at))
            statement = statement.offset(skip).limit(limit)

            result = self.session.exec(statement)
            return result.all()
        except Exception as e:
            raise Exception(f"Error al obtener lista de movimientos: {str(e)}")

    async def count_movimientos(
        self, 
        filtros: Optional[MovimientoInventarioFilter] = None
    ) -> int:
        """Contar el total de movimientos que cumplen los criterios."""
        try:
            statement = select(func.count(MovimientoInventario.id))

            # Aplicar los mismos filtros que en get_all_movimientos
            if filtros:
                if filtros.producto_id:
                    statement = statement.where(MovimientoInventario.producto_id == filtros.producto_id)
                
                if filtros.tipo_movimiento:
                    statement = statement.where(MovimientoInventario.tipo_movimiento == filtros.tipo_movimiento)
                
                if filtros.fecha_desde:
                    statement = statement.where(MovimientoInventario.created_at >= filtros.fecha_desde)
                
                if filtros.fecha_hasta:
                    statement = statement.where(MovimientoInventario.created_at <= filtros.fecha_hasta)
                
                if filtros.referencia:
                    statement = statement.where(MovimientoInventario.referencia.ilike(f"%{filtros.referencia}%"))
                
                if filtros.created_by:
                    statement = statement.where(MovimientoInventario.created_by == filtros.created_by)

            result = self.session.exec(statement)
            return result.one()
        except Exception as e:
            raise Exception(f"Error al contar movimientos: {str(e)}")

    async def calcular_costo_promedio(
        self, 
        producto_id: UUID,
        cantidad_entrada: int,
        precio_entrada: Decimal
    ) -> CostoPromedioCalculation:
        """
        Calcular el nuevo costo promedio ponderado para una entrada.
        
        Implementa BR-11: Método de costo promedio ponderado.
        """
        try:
            # Obtener stock y costo actual
            stock_anterior = await self.get_stock_actual(producto_id)
            
            if stock_anterior == 0:
                # Primera entrada, el costo promedio es el precio de entrada
                return CostoPromedioCalculation(
                    stock_anterior=0,
                    costo_anterior=Decimal('0.00'),
                    cantidad_entrada=cantidad_entrada,
                    precio_entrada=precio_entrada,
                    stock_nuevo=cantidad_entrada,
                    costo_promedio_nuevo=precio_entrada
                )
            
            # Obtener costo promedio actual
            costo_anterior = await self.get_costo_promedio_actual(producto_id)
            
            # Calcular nuevo costo promedio ponderado
            # Fórmula: (Stock Anterior × Costo Anterior + Cantidad Nueva × Precio Nuevo) / (Stock Anterior + Cantidad Nueva)
            valor_anterior = Decimal(str(stock_anterior)) * costo_anterior
            valor_nuevo = Decimal(str(cantidad_entrada)) * precio_entrada
            stock_nuevo = stock_anterior + cantidad_entrada
            
            costo_promedio_nuevo = (valor_anterior + valor_nuevo) / Decimal(str(stock_nuevo))
            
            return CostoPromedioCalculation(
                stock_anterior=stock_anterior,
                costo_anterior=costo_anterior,
                cantidad_entrada=cantidad_entrada,
                precio_entrada=precio_entrada,
                stock_nuevo=stock_nuevo,
                costo_promedio_nuevo=costo_promedio_nuevo
            )
            
        except Exception as e:
            raise Exception(f"Error al calcular costo promedio: {str(e)}")

    async def get_stock_actual(self, producto_id: UUID) -> int:
        """Obtener el stock actual de un producto basado en movimientos."""
        try:
            # Sumar entradas y restar salidas
            statement_entradas = select(func.coalesce(func.sum(MovimientoInventario.cantidad), 0)).where(
                and_(
                    MovimientoInventario.producto_id == producto_id,
                    MovimientoInventario.tipo_movimiento.in_([TipoMovimiento.ENTRADA, TipoMovimiento.AJUSTE])
                )
            )
            
            statement_salidas = select(func.coalesce(func.sum(MovimientoInventario.cantidad), 0)).where(
                and_(
                    MovimientoInventario.producto_id == producto_id,
                    MovimientoInventario.tipo_movimiento.in_([TipoMovimiento.SALIDA, TipoMovimiento.MERMA])
                )
            )
            
            entradas = self.session.exec(statement_entradas).one()
            salidas = self.session.exec(statement_salidas).one()
            
            return max(0, entradas - salidas)  # Asegurar que no sea negativo
            
        except Exception as e:
            raise Exception(f"Error al calcular stock actual: {str(e)}")

    async def get_costo_promedio_actual(self, producto_id: UUID) -> Decimal:
        """Obtener el costo promedio actual de un producto."""
        try:
            # Obtener el último movimiento de entrada con costo calculado
            statement = select(MovimientoInventario).where(
                and_(
                    MovimientoInventario.producto_id == producto_id,
                    MovimientoInventario.tipo_movimiento == TipoMovimiento.ENTRADA,
                    MovimientoInventario.costo_unitario.is_not(None)
                )
            ).order_by(desc(MovimientoInventario.created_at))
            
            result = self.session.exec(statement)
            ultimo_movimiento = result.first()
            
            if not ultimo_movimiento:
                raise ValueError(f"No se encontraron movimientos de entrada para el producto {producto_id}")
            
            return ultimo_movimiento.costo_unitario
            
        except Exception as e:
            raise Exception(f"Error al obtener costo promedio actual: {str(e)}")

    async def get_valor_inventario_producto(self, producto_id: UUID) -> Decimal:
        """Calcular el valor total del inventario de un producto."""
        try:
            stock_actual = await self.get_stock_actual(producto_id)
            if stock_actual == 0:
                return Decimal('0.00')
            
            costo_promedio = await self.get_costo_promedio_actual(producto_id)
            return Decimal(str(stock_actual)) * costo_promedio
            
        except ValueError:
            # Si no hay costo promedio, el valor es 0
            return Decimal('0.00')
        except Exception as e:
            raise Exception(f"Error al calcular valor de inventario: {str(e)}")

    async def get_ultimo_movimiento_producto(
        self, 
        producto_id: UUID
    ) -> Optional[MovimientoInventario]:
        """Obtener el último movimiento de un producto."""
        try:
            statement = select(MovimientoInventario).where(
                MovimientoInventario.producto_id == producto_id
            ).order_by(desc(MovimientoInventario.created_at))
            
            result = self.session.exec(statement)
            return result.first()
            
        except Exception as e:
            raise Exception(f"Error al obtener último movimiento: {str(e)}")

    async def validar_stock_suficiente(
        self, 
        producto_id: UUID, 
        cantidad_salida: int
    ) -> bool:
        """
        Validar si hay stock suficiente para una salida.
        
        Implementa BR-01: Stock no puede ser negativo.
        """
        try:
            stock_actual = await self.get_stock_actual(producto_id)
            return stock_actual >= cantidad_salida
        except Exception as e:
            raise Exception(f"Error al validar stock suficiente: {str(e)}")

    async def get_estadisticas_inventario(
        self,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> EstadisticasInventario:
        """Obtener estadísticas generales de inventario."""
        try:
            # Si no se especifican fechas, usar el mes actual
            if not fecha_desde:
                now = datetime.now(UTC)
                fecha_desde = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            if not fecha_hasta:
                fecha_hasta = datetime.now(UTC)

            # Estadísticas de movimientos por tipo
            base_query = select(MovimientoInventario).where(
                and_(
                    MovimientoInventario.created_at >= fecha_desde,
                    MovimientoInventario.created_at <= fecha_hasta
                )
            )

            # Contar movimientos por tipo
            entradas = self.session.exec(
                select(func.count(MovimientoInventario.id)).where(
                    and_(
                        MovimientoInventario.created_at >= fecha_desde,
                        MovimientoInventario.created_at <= fecha_hasta,
                        MovimientoInventario.tipo_movimiento == TipoMovimiento.ENTRADA
                    )
                )
            ).one()

            salidas = self.session.exec(
                select(func.count(MovimientoInventario.id)).where(
                    and_(
                        MovimientoInventario.created_at >= fecha_desde,
                        MovimientoInventario.created_at <= fecha_hasta,
                        MovimientoInventario.tipo_movimiento == TipoMovimiento.SALIDA
                    )
                )
            ).one()

            mermas = self.session.exec(
                select(func.count(MovimientoInventario.id)).where(
                    and_(
                        MovimientoInventario.created_at >= fecha_desde,
                        MovimientoInventario.created_at <= fecha_hasta,
                        MovimientoInventario.tipo_movimiento == TipoMovimiento.MERMA
                    )
                )
            ).one()

            # Calcular valores por tipo
            valor_entradas = self.session.exec(
                select(func.coalesce(func.sum(MovimientoInventario.cantidad * MovimientoInventario.precio_unitario), 0)).where(
                    and_(
                        MovimientoInventario.created_at >= fecha_desde,
                        MovimientoInventario.created_at <= fecha_hasta,
                        MovimientoInventario.tipo_movimiento == TipoMovimiento.ENTRADA
                    )
                )
            ).one()

            valor_salidas = self.session.exec(
                select(func.coalesce(func.sum(MovimientoInventario.cantidad * MovimientoInventario.precio_unitario), 0)).where(
                    and_(
                        MovimientoInventario.created_at >= fecha_desde,
                        MovimientoInventario.created_at <= fecha_hasta,
                        MovimientoInventario.tipo_movimiento == TipoMovimiento.SALIDA
                    )
                )
            ).one()

            valor_mermas = self.session.exec(
                select(func.coalesce(func.sum(MovimientoInventario.cantidad * MovimientoInventario.costo_unitario), 0)).where(
                    and_(
                        MovimientoInventario.created_at >= fecha_desde,
                        MovimientoInventario.created_at <= fecha_hasta,
                        MovimientoInventario.tipo_movimiento == TipoMovimiento.MERMA,
                        MovimientoInventario.costo_unitario.is_not(None)
                    )
                )
            ).one()

            # Productos más movidos
            productos_mas_movidos = await self.get_productos_mas_movidos(
                limit=5, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta
            )

            return EstadisticasInventario(
                total_entradas_mes=entradas,
                total_salidas_mes=salidas,
                total_mermas_mes=mermas,
                valor_entradas_mes=Decimal(str(valor_entradas)),
                valor_salidas_mes=Decimal(str(valor_salidas)),
                valor_mermas_mes=Decimal(str(valor_mermas)),
                productos_mas_movidos=productos_mas_movidos
            )

        except Exception as e:
            raise Exception(f"Error al obtener estadísticas de inventario: {str(e)}")

    async def get_productos_mas_movidos(
        self,
        limit: int = 10,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> List[dict]:
        """Obtener los productos con más movimientos."""
        try:
            statement = select(
                MovimientoInventario.producto_id,
                func.count(MovimientoInventario.id).label('total_movimientos')
            )

            if fecha_desde:
                statement = statement.where(MovimientoInventario.created_at >= fecha_desde)
            
            if fecha_hasta:
                statement = statement.where(MovimientoInventario.created_at <= fecha_hasta)

            statement = statement.group_by(MovimientoInventario.producto_id)
            statement = statement.order_by(desc('total_movimientos'))
            statement = statement.limit(limit)

            result = self.session.exec(statement)
            productos_data = result.all()

            # Enriquecer con información del producto
            productos_mas_movidos = []
            for producto_id, total_movimientos in productos_data:
                producto = await self.product_repository.get_by_id(producto_id)
                productos_mas_movidos.append({
                    "producto_id": producto_id,
                    "nombre": producto.nombre if producto else "Producto no encontrado",
                    "total_movimientos": total_movimientos
                })

            return productos_mas_movidos

        except Exception as e:
            raise Exception(f"Error al obtener productos más movidos: {str(e)}")

    async def recalcular_costos_producto(self, producto_id: UUID) -> bool:
        """Recalcular todos los costos promedio de un producto."""
        try:
            # Obtener todos los movimientos del producto ordenados por fecha
            movimientos = await self.get_movimientos_by_producto(
                producto_id, skip=0, limit=10000  # Obtener todos
            )
            
            # Recalcular secuencialmente
            stock_acumulado = 0
            costo_promedio = Decimal('0.00')
            
            for movimiento in reversed(movimientos):  # Procesar del más antiguo al más reciente
                if movimiento.tipo_movimiento == TipoMovimiento.ENTRADA:
                    if stock_acumulado == 0:
                        costo_promedio = movimiento.precio_unitario
                    else:
                        # Calcular nuevo costo promedio ponderado
                        valor_anterior = Decimal(str(stock_acumulado)) * costo_promedio
                        valor_nuevo = Decimal(str(movimiento.cantidad)) * movimiento.precio_unitario
                        stock_nuevo = stock_acumulado + movimiento.cantidad
                        costo_promedio = (valor_anterior + valor_nuevo) / Decimal(str(stock_nuevo))
                    
                    stock_acumulado += movimiento.cantidad
                    
                    # Actualizar el costo en el movimiento
                    movimiento.costo_unitario = costo_promedio
                    self.session.add(movimiento)
                
                elif movimiento.tipo_movimiento in [TipoMovimiento.SALIDA, TipoMovimiento.MERMA]:
                    stock_acumulado -= movimiento.cantidad
                    movimiento.costo_unitario = costo_promedio
                    self.session.add(movimiento)

            self.session.commit()
            return True

        except Exception as e:
            self.session.rollback()
            raise Exception(f"Error al recalcular costos del producto: {str(e)}")

    async def get_movimientos_pendientes_costo(self) -> List[MovimientoInventario]:
        """Obtener movimientos que no tienen costo_unitario calculado."""
        try:
            statement = select(MovimientoInventario).where(
                MovimientoInventario.costo_unitario.is_(None)
            ).order_by(MovimientoInventario.created_at)
            
            result = self.session.exec(statement)
            return result.all()
            
        except Exception as e:
            raise Exception(f"Error al obtener movimientos pendientes de costo: {str(e)}") 