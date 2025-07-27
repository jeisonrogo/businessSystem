"""
Casos de uso para la gestión de inventario.

Implementa la lógica de negocio para el registro de movimientos de inventario,
consulta de kardex, cálculo de estadísticas y aplicación de reglas de negocio
como el costo promedio ponderado (BR-11) y validación de stock (BR-01).
"""

from datetime import datetime, UTC
from typing import Optional, List
from uuid import UUID

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
        fecha_hasta: Optional[datetime] = None
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
            movimientos = await self.inventario_repository.get_movimientos_by_producto(
                producto_id, skip, limit, tipo_movimiento, fecha_desde, fecha_hasta
            )

            # Obtener información agregada
            stock_actual = await self.inventario_repository.get_stock_actual(producto_id)
            
            try:
                costo_promedio_actual = await self.inventario_repository.get_costo_promedio_actual(producto_id)
                valor_inventario = await self.inventario_repository.get_valor_inventario_producto(producto_id)
            except ValueError:
                # Si no hay movimientos de entrada, usar valores por defecto
                costo_promedio_actual = producto.precio_base
                valor_inventario = costo_promedio_actual * stock_actual

            # Contar total de movimientos para paginación
            total_movimientos = await self.inventario_repository.count_movimientos(
                MovimientoInventarioFilter(producto_id=producto_id)
            )

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

    def __init__(self, inventario_repository: IInventarioRepository):
        self.inventario_repository = inventario_repository

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

            # Calcular metadatos de paginación
            total_pages = (total + limit - 1) // limit  # Ceiling division
            has_next = page < total_pages
            has_prev = page > 1

            return MovimientoInventarioListResponse(
                movimientos=movimientos,
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

    async def execute(self) -> InventarioResumenResponse:
        """
        Obtener resumen general del inventario.

        Returns:
            InventarioResumenResponse: Resumen con estadísticas generales
        """
        try:
            # Obtener todos los productos activos
            productos = await self.product_repository.get_all(only_active=True)
            total_productos = len(productos)

            # Calcular valor total del inventario
            valor_total_inventario = 0
            productos_sin_stock = 0
            productos_stock_bajo = 0

            for producto in productos:
                try:
                    valor_producto = await self.inventario_repository.get_valor_inventario_producto(
                        producto.id
                    )
                    valor_total_inventario += valor_producto
                    
                    if producto.stock == 0:
                        productos_sin_stock += 1
                    elif producto.stock <= 10:  # Umbral de stock bajo
                        productos_stock_bajo += 1
                        
                except ValueError:
                    # Producto sin movimientos, no contribuye al valor
                    if producto.stock == 0:
                        productos_sin_stock += 1
                    elif producto.stock <= 10:
                        productos_stock_bajo += 1

            # Obtener último movimiento general
            ultimo_movimiento = None
            try:
                movimientos_recientes = await self.inventario_repository.get_all_movimientos(
                    skip=0, limit=1
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
                ultimo_movimiento=ultimo_movimiento
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
        fecha_hasta: Optional[datetime] = None
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
                fecha_desde, fecha_hasta
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