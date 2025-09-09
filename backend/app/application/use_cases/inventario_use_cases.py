"""
Casos de uso para la gestión de inventario.

Implementa la lógica de negocio para el registro de movimientos de inventario,
consulta de kardex, cálculo de estadísticas y aplicación de reglas de negocio
como el costo promedio ponderado (BR-11) y validación de stock (BR-01).
"""

from datetime import datetime, UTC
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from app.application.services.i_inventario_repository import IInventarioRepository
from app.application.services.i_product_repository import IProductRepository
from app.domain.models.movimiento_inventario import (
    MovimientoInventario,
    MovimientoInventarioCreate,
    MovimientoInventarioFilter,
    MovimientoInventarioListResponse,
    KardexResponse,
    InventarioResumenResponse,
    EstadisticasInventario,
    TipoMovimiento
)


class InventarioError(Exception):
    """Excepción base para errores de inventario."""
    pass


class StockInsuficienteError(InventarioError):
    """Excepción lanzada cuando no hay stock suficiente para una salida."""
    pass


class ProductoNoEncontradoError(InventarioError):
    """Excepción lanzada cuando un producto no se encuentra."""
    pass


class MovimientoInvalidoError(InventarioError):
    """Excepción lanzada cuando un movimiento es inválido."""
    pass


class RegistrarMovimientoUseCase:
    """
    Caso de uso para registrar un nuevo movimiento de inventario.
    
    Implementa las reglas de negocio:
    - BR-01: Stock no puede ser negativo
    - BR-11: Cálculo de costo promedio ponderado
    """

    def __init__(
        self, 
        inventario_repository: IInventarioRepository,
        product_repository: IProductRepository
    ):
        self.inventario_repository = inventario_repository
        self.product_repository = product_repository

    async def execute(
        self, 
        movimiento_data: MovimientoInventarioCreate,
        created_by: Optional[UUID] = None
    ) -> MovimientoInventario:
        """
        Registrar un nuevo movimiento de inventario.

        Args:
            movimiento_data: Datos del movimiento a registrar
            created_by: UUID del usuario que registra el movimiento

        Returns:
            MovimientoInventario: El movimiento registrado con cálculos aplicados

        Raises:
            ProductoNoEncontradoError: Si el producto no existe
            StockInsuficienteError: Si no hay stock suficiente para salidas/mermas
            MovimientoInvalidoError: Si los datos del movimiento son inválidos
        """
        try:
            # Verificar que el producto existe
            producto = await self.product_repository.get_by_id(movimiento_data.producto_id)
            if not producto:
                raise ProductoNoEncontradoError(
                    f"Producto con ID {movimiento_data.producto_id} no encontrado"
                )

            # Validar stock suficiente para salidas y mermas
            if movimiento_data.tipo_movimiento in [TipoMovimiento.SALIDA, TipoMovimiento.MERMA]:
                stock_suficiente = await self.inventario_repository.validar_stock_suficiente(
                    movimiento_data.producto_id, 
                    movimiento_data.cantidad
                )
                if not stock_suficiente:
                    stock_actual = await self.inventario_repository.get_stock_actual(
                        movimiento_data.producto_id
                    )
                    raise StockInsuficienteError(
                        f"Stock insuficiente. Stock actual: {stock_actual}, "
                        f"cantidad solicitada: {movimiento_data.cantidad}"
                    )

            # Registrar el movimiento
            return await self.inventario_repository.create_movimiento(
                movimiento_data, created_by
            )

        except (ProductoNoEncontradoError, StockInsuficienteError, MovimientoInvalidoError):
            raise
        except ValueError as e:
            if "Stock insuficiente" in str(e):
                raise StockInsuficienteError(str(e))
            elif "no encontrado" in str(e):
                raise ProductoNoEncontradoError(str(e))
            else:
                raise MovimientoInvalidoError(str(e))
        except Exception as e:
            raise MovimientoInvalidoError(f"Error al registrar movimiento: {str(e)}")


class ConsultarKardexUseCase:
    """Caso de uso para consultar el kardex de un producto."""

    def __init__(
        self, 
        inventario_repository: IInventarioRepository,
        product_repository: IProductRepository
    ):
        self.inventario_repository = inventario_repository
        self.product_repository = product_repository

    async def execute(
        self,
        producto_id: UUID,
        skip: int = 0,
        limit: int = 100,
        tipo_movimiento: Optional[TipoMovimiento] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        local_id: Optional[UUID] = None
    ) -> KardexResponse:
        """
        Consultar el kardex (historial de movimientos) de un producto.

        Args:
            producto_id: UUID del producto
            skip: Número de movimientos a omitir
            limit: Número máximo de movimientos a retornar
            tipo_movimiento: Filtrar por tipo de movimiento
            fecha_desde: Filtrar desde esta fecha
            fecha_hasta: Filtrar hasta esta fecha

        Returns:
            KardexResponse: Kardex del producto con información agregada

        Raises:
            ProductoNoEncontradoError: Si el producto no existe
        """
        try:
            # Verificar que el producto existe
            producto = await self.product_repository.get_by_id(producto_id)
            if not producto:
                raise ProductoNoEncontradoError(f"Producto con ID {producto_id} no encontrado")

            # Obtener movimientos del producto
            movimientos_raw = await self.inventario_repository.get_movimientos_by_producto(
                producto_id, skip, limit, tipo_movimiento, fecha_desde, fecha_hasta, local_id
            )
            
            # Enriquecer movimientos con información del producto
            from app.domain.models.movimiento_inventario import MovimientoInventarioResponse, ProductoInfo
            
            movimientos = []
            for movimiento in movimientos_raw:
                movimiento_dict = {
                    "id": movimiento.id,
                    "producto_id": movimiento.producto_id,
                    "tipo_movimiento": movimiento.tipo_movimiento,
                    "cantidad": movimiento.cantidad,
                    "precio_unitario": movimiento.precio_unitario,
                    "costo_unitario": movimiento.costo_unitario,
                    "stock_anterior": movimiento.stock_anterior,
                    "stock_posterior": movimiento.stock_posterior,
                    "referencia": movimiento.referencia,
                    "observaciones": movimiento.observaciones,
                    "created_at": movimiento.created_at,
                    "created_by": movimiento.created_by,
                    "local_id": movimiento.local_id
                }
                
                # Agregar información del producto
                movimiento_dict["producto"] = ProductoInfo(
                    id=producto.id,
                    sku=producto.sku,
                    nombre=producto.nombre,
                    precio_publico=producto.precio_publico
                )
                
                movimientos.append(MovimientoInventarioResponse(**movimiento_dict))

            # Obtener información agregada
            stock_actual = await self.inventario_repository.get_stock_actual(producto_id)
            
            try:
                costo_promedio_actual = await self.inventario_repository.get_costo_promedio_actual(producto_id)
                valor_inventario = await self.inventario_repository.get_valor_inventario_producto(producto_id)
            except ValueError:
                # Si no hay movimientos de entrada, usar precio base del producto
                costo_promedio_actual = producto.precio_base if producto.precio_base else Decimal('0')
                valor_inventario = costo_promedio_actual * Decimal(str(stock_actual))

            # Contar total de movimientos para paginación
            filtros_count = MovimientoInventarioFilter(
                producto_id=producto_id,
                local_id=local_id
            )
            total_movimientos = await self.inventario_repository.count_movimientos(filtros_count)

            return KardexResponse(
                producto_id=producto_id,
                movimientos=movimientos,
                stock_actual=stock_actual,
                costo_promedio_actual=costo_promedio_actual,
                valor_inventario=valor_inventario,
                total_movimientos=total_movimientos
            )

        except ProductoNoEncontradoError:
            raise
        except Exception as e:
            raise InventarioError(f"Error al consultar kardex: {str(e)}")


class ListarMovimientosUseCase:
    """Caso de uso para listar movimientos con filtros y paginación."""

    def __init__(
        self, 
        inventario_repository: IInventarioRepository,
        product_repository: IProductRepository
    ):
        self.inventario_repository = inventario_repository
        self.product_repository = product_repository

    async def execute(
        self,
        page: int = 1,
        limit: int = 50,
        filtros: Optional[MovimientoInventarioFilter] = None
    ) -> MovimientoInventarioListResponse:
        """
        Listar movimientos de inventario con filtros y paginación.

        Args:
            page: Número de página (empezando en 1)
            limit: Movimientos por página (máximo 100)
            filtros: Filtros opcionales para la consulta

        Returns:
            MovimientoInventarioListResponse: Lista paginada con metadatos
        """
        try:
            # Validar parámetros de paginación
            if page < 1:
                page = 1
            if limit > 100:
                limit = 100
            if limit < 1:
                limit = 10

            skip = (page - 1) * limit

            # Obtener movimientos y conteo total
            movimientos = await self.inventario_repository.get_all_movimientos(
                skip=skip, limit=limit, filtros=filtros
            )
            total = await self.inventario_repository.count_movimientos(filtros)

            # Enriquecer movimientos con información del producto
            movimientos_enriquecidos = []
            for movimiento in movimientos:
                # Obtener información del producto
                producto = await self.product_repository.get_by_id(movimiento.producto_id)
                
                # Convertir a MovimientoInventarioResponse con información del producto
                from app.domain.models.movimiento_inventario import MovimientoInventarioResponse, ProductoInfo
                
                movimiento_dict = {
                    "id": movimiento.id,
                    "producto_id": movimiento.producto_id,
                    "tipo_movimiento": movimiento.tipo_movimiento,
                    "cantidad": movimiento.cantidad,
                    "precio_unitario": movimiento.precio_unitario,
                    "costo_unitario": movimiento.costo_unitario,
                    "stock_anterior": movimiento.stock_anterior,
                    "stock_posterior": movimiento.stock_posterior,
                    "referencia": movimiento.referencia,
                    "observaciones": movimiento.observaciones,
                    "created_at": movimiento.created_at,
                    "created_by": movimiento.created_by,
                    "local_id": movimiento.local_id
                }
                
                # Agregar información del producto si existe
                if producto:
                    movimiento_dict["producto"] = ProductoInfo(
                        id=producto.id,
                        sku=producto.sku,
                        nombre=producto.nombre,
                        precio_publico=producto.precio_publico
                    )
                
                movimientos_enriquecidos.append(MovimientoInventarioResponse(**movimiento_dict))

            # Calcular metadatos de paginación
            total_pages = (total + limit - 1) // limit  # Ceiling division
            has_next = page < total_pages
            has_prev = page > 1

            return MovimientoInventarioListResponse(
                movimientos=movimientos_enriquecidos,
                total=total,
                page=page,
                limit=limit,
                has_next=has_next,
                has_prev=has_prev
            )

        except Exception as e:
            raise InventarioError(f"Error al listar movimientos: {str(e)}")


class ObtenerResumenInventarioUseCase:
    """Caso de uso para obtener un resumen general del inventario."""

    def __init__(
        self, 
        inventario_repository: IInventarioRepository,
        product_repository: IProductRepository
    ):
        self.inventario_repository = inventario_repository
        self.product_repository = product_repository

    async def execute(self, tenant_context=None) -> InventarioResumenResponse:
        """
        Obtener resumen general del inventario (multi-tenant compatible).

        Returns:
            InventarioResumenResponse: Resumen con estadísticas generales
        """
        try:
            # Determinar local_id basado en el contexto
            filter_local_id = tenant_context.local_id if tenant_context and tenant_context.tiene_contexto_local else None
            
            stock_total = 0
            if filter_local_id:
                # Contexto local específico - calcular estadísticas para ese local
                if hasattr(self.inventario_repository, 'stock_local_repository') and self.inventario_repository.stock_local_repository:
                    stock_repo = self.inventario_repository.stock_local_repository
                    
                    # Obtener estadísticas del local
                    stats = stock_repo.get_statistics_by_local(filter_local_id)
                    total_productos = stats['total_productos']
                    valor_total_inventario = float(stats['valor_inventario'])
                    productos_sin_stock = stats['productos_sin_stock']
                    productos_stock_bajo = 0  # TODO: implementar lógica de stock bajo
                    stock_total = stats.get('stock_total', 0)
                else:
                    # Fallback si no hay acceso al repositorio de stock local
                    productos = await self.product_repository.get_all(only_active=True)
                    total_productos = len(productos)
                    valor_total_inventario = 0
                    productos_sin_stock = 0
                    productos_stock_bajo = 0
                    stock_total = 0
            else:
                # Contexto tienda completa - calcular estadísticas generales
                productos = await self.product_repository.get_all(only_active=True)
                total_productos = len(productos)
                
                valor_total_inventario = 0
                productos_sin_stock = 0
                productos_stock_bajo = 0
                
                # Si tenemos acceso al repositorio de stock local, sumar todos los locales
                if hasattr(self.inventario_repository, 'stock_local_repository') and self.inventario_repository.stock_local_repository:
                    stock_repo = self.inventario_repository.stock_local_repository
                    
                    # Obtener estadísticas de todos los locales disponibles para el usuario
                    if tenant_context and hasattr(tenant_context, 'tienda_id'):
                        # Aquí podríamos obtener estadísticas por tienda completa
                        # Por ahora, usamos el método básico
                        pass
                
                # Método fallback usando movimientos de inventario
                for producto in productos:
                    try:
                        valor_producto = await self.inventario_repository.get_valor_inventario_producto(
                            producto.id
                        )
                        valor_total_inventario += float(valor_producto)
                        
                        # Calcular stock total
                        stock_producto = await self.inventario_repository.get_stock_actual(producto.id)
                        stock_total += stock_producto
                    except (ValueError, AttributeError, Exception):
                        pass

            # Obtener último movimiento (filtrado por local si aplica)
            ultimo_movimiento = None
            try:
                filtros = MovimientoInventarioFilter(local_id=filter_local_id) if filter_local_id else None
                movimientos_recientes = await self.inventario_repository.get_all_movimientos(
                    skip=0, limit=1, filtros=filtros
                )
                if movimientos_recientes:
                    ultimo_movimiento = movimientos_recientes[0].created_at
            except Exception:
                pass

            return InventarioResumenResponse(
                total_productos=total_productos,
                valor_total_inventario=valor_total_inventario,
                productos_sin_stock=productos_sin_stock,
                productos_stock_bajo=productos_stock_bajo,
                ultimo_movimiento=ultimo_movimiento,
                stock_total=stock_total
            )

        except Exception as e:
            raise InventarioError(f"Error al obtener resumen de inventario: {str(e)}")


class ObtenerEstadisticasInventarioUseCase:
    """Caso de uso para obtener estadísticas detalladas del inventario."""

    def __init__(self, inventario_repository: IInventarioRepository):
        self.inventario_repository = inventario_repository

    async def execute(
        self,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        local_id: Optional[UUID] = None
    ) -> EstadisticasInventario:
        """
        Obtener estadísticas detalladas del inventario.

        Args:
            fecha_desde: Fecha desde para el cálculo (default: inicio del mes actual)
            fecha_hasta: Fecha hasta para el cálculo (default: ahora)

        Returns:
            EstadisticasInventario: Estadísticas del período especificado
        """
        try:
            return await self.inventario_repository.get_estadisticas_inventario(
                fecha_desde, fecha_hasta, local_id
            )
        except Exception as e:
            raise InventarioError(f"Error al obtener estadísticas: {str(e)}")


class ValidarStockUseCase:
    """Caso de uso para validar disponibilidad de stock."""

    def __init__(self, inventario_repository: IInventarioRepository):
        self.inventario_repository = inventario_repository

    async def execute(self, producto_id: UUID, cantidad_requerida: int) -> dict:
        """
        Validar si hay stock suficiente para una operación.

        Args:
            producto_id: UUID del producto
            cantidad_requerida: Cantidad que se necesita

        Returns:
            dict: Información sobre disponibilidad de stock
        """
        try:
            stock_actual = await self.inventario_repository.get_stock_actual(producto_id)
            stock_suficiente = await self.inventario_repository.validar_stock_suficiente(
                producto_id, cantidad_requerida
            )

            return {
                "producto_id": producto_id,
                "stock_actual": stock_actual,
                "cantidad_requerida": cantidad_requerida,
                "stock_suficiente": stock_suficiente,
                "cantidad_disponible": max(0, stock_actual - cantidad_requerida) if stock_suficiente else 0
            }

        except Exception as e:
            raise InventarioError(f"Error al validar stock: {str(e)}")


class RecalcularCostosUseCase:
    """Caso de uso para recalcular costos promedio de un producto."""

    def __init__(self, inventario_repository: IInventarioRepository):
        self.inventario_repository = inventario_repository

    async def execute(self, producto_id: UUID) -> bool:
        """
        Recalcular todos los costos promedio de un producto.

        Args:
            producto_id: UUID del producto

        Returns:
            bool: True si se recalculó exitosamente

        Note:
            Útil para correcciones o migraciones de datos
        """
        try:
            return await self.inventario_repository.recalcular_costos_producto(producto_id)
        except Exception as e:
            raise InventarioError(f"Error al recalcular costos: {str(e)}")


class ObtenerMovimientoPorIdUseCase:
    """Caso de uso para obtener un movimiento específico por ID."""

    def __init__(self, inventario_repository: IInventarioRepository):
        self.inventario_repository = inventario_repository

    async def execute(self, movimiento_id: UUID) -> MovimientoInventario:
        """
        Obtener un movimiento por su ID.

        Args:
            movimiento_id: UUID del movimiento

        Returns:
            MovimientoInventario: El movimiento encontrado

        Raises:
            InventarioError: Si el movimiento no existe
        """
        try:
            movimiento = await self.inventario_repository.get_by_id(movimiento_id)
            if not movimiento:
                raise InventarioError(f"Movimiento con ID {movimiento_id} no encontrado")
            return movimiento
        except Exception as e:
            raise InventarioError(f"Error al obtener movimiento: {str(e)}") 