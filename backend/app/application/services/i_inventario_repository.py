"""
Interfaz del repositorio para la gestión de movimientos de inventario.

Define los métodos que debe implementar cualquier repositorio concreto
que maneje la persistencia de movimientos de inventario, siguiendo el
patrón Repository y el principio de Inversión de Dependencias.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID

from app.domain.models.movimiento_inventario import (
    MovimientoInventario,
    MovimientoInventarioCreate,
    MovimientoInventarioFilter,
    TipoMovimiento,
    CostoPromedioCalculation,
    EstadisticasInventario
)


class IInventarioRepository(ABC):
    """
    Interfaz del repositorio para la gestión de movimientos de inventario.
    
    Define los métodos que debe implementar cualquier repositorio concreto
    que maneje la persistencia de movimientos de inventario, implementando
    la lógica de costo promedio ponderado (BR-11).
    """

    @abstractmethod
    async def create_movimiento(
        self, 
        movimiento_data: MovimientoInventarioCreate,
        created_by: Optional[UUID] = None
    ) -> MovimientoInventario:
        """
        Crear un nuevo movimiento de inventario.
        
        Implementa la lógica de costo promedio ponderado (BR-11) y actualiza
        automáticamente el stock del producto.

        Args:
            movimiento_data: Datos del movimiento a crear
            created_by: UUID del usuario que registra el movimiento

        Returns:
            MovimientoInventario: El movimiento creado con cálculos aplicados

        Raises:
            ValueError: Si el movimiento causaría stock negativo (BR-01)
            ValueError: Si el producto no existe
            Exception: En caso de error en la base de datos
        """
        pass

    @abstractmethod
    async def get_by_id(self, movimiento_id: UUID) -> Optional[MovimientoInventario]:
        """
        Obtener un movimiento por su ID.

        Args:
            movimiento_id: UUID del movimiento a buscar

        Returns:
            MovimientoInventario si existe, None en caso contrario
        """
        pass

    @abstractmethod
    async def get_movimientos_by_producto(
        self,
        producto_id: UUID,
        skip: int = 0,
        limit: int = 100,
        tipo_movimiento: Optional[TipoMovimiento] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> List[MovimientoInventario]:
        """
        Obtener movimientos de un producto específico (Kardex).

        Args:
            producto_id: UUID del producto
            skip: Número de movimientos a omitir (offset)
            limit: Número máximo de movimientos a retornar
            tipo_movimiento: Filtrar por tipo de movimiento
            fecha_desde: Filtrar desde esta fecha
            fecha_hasta: Filtrar hasta esta fecha

        Returns:
            Lista de movimientos ordenados por fecha (más recientes primero)
        """
        pass

    @abstractmethod
    async def get_all_movimientos(
        self,
        skip: int = 0,
        limit: int = 100,
        filtros: Optional[MovimientoInventarioFilter] = None
    ) -> List[MovimientoInventario]:
        """
        Obtener lista paginada de todos los movimientos.

        Args:
            skip: Número de movimientos a omitir (offset)
            limit: Número máximo de movimientos a retornar
            filtros: Filtros opcionales para la consulta

        Returns:
            Lista de movimientos que cumplen los criterios
        """
        pass

    @abstractmethod
    async def count_movimientos(
        self, 
        filtros: Optional[MovimientoInventarioFilter] = None
    ) -> int:
        """
        Contar el total de movimientos que cumplen los criterios.

        Args:
            filtros: Filtros opcionales para el conteo

        Returns:
            Número total de movimientos
        """
        pass

    @abstractmethod
    async def calcular_costo_promedio(
        self, 
        producto_id: UUID,
        cantidad_entrada: int,
        precio_entrada: Decimal
    ) -> CostoPromedioCalculation:
        """
        Calcular el nuevo costo promedio ponderado para una entrada.

        Implementa BR-11: Método de costo promedio ponderado.
        
        Fórmula: 
        Nuevo Costo = (Stock Anterior × Costo Anterior + Cantidad Nueva × Precio Nuevo) 
                     / (Stock Anterior + Cantidad Nueva)

        Args:
            producto_id: UUID del producto
            cantidad_entrada: Cantidad de la nueva entrada
            precio_entrada: Precio unitario de la nueva entrada

        Returns:
            CostoPromedioCalculation: Cálculo detallado del nuevo costo promedio

        Raises:
            ValueError: Si el producto no existe
        """
        pass

    @abstractmethod
    async def get_stock_actual(self, producto_id: UUID) -> int:
        """
        Obtener el stock actual de un producto basado en movimientos.

        Args:
            producto_id: UUID del producto

        Returns:
            Stock actual calculado desde movimientos

        Note:
            Debe coincidir con el campo stock en la tabla products
        """
        pass

    @abstractmethod
    async def get_costo_promedio_actual(self, producto_id: UUID) -> Decimal:
        """
        Obtener el costo promedio actual de un producto.

        Args:
            producto_id: UUID del producto

        Returns:
            Costo promedio actual basado en movimientos

        Raises:
            ValueError: Si el producto no tiene movimientos de entrada
        """
        pass

    @abstractmethod
    async def get_valor_inventario_producto(self, producto_id: UUID) -> Decimal:
        """
        Calcular el valor total del inventario de un producto.

        Args:
            producto_id: UUID del producto

        Returns:
            Valor total (Stock × Costo Promedio)
        """
        pass

    @abstractmethod
    async def get_ultimo_movimiento_producto(
        self, 
        producto_id: UUID
    ) -> Optional[MovimientoInventario]:
        """
        Obtener el último movimiento de un producto.

        Args:
            producto_id: UUID del producto

        Returns:
            Último movimiento si existe, None si no hay movimientos
        """
        pass

    @abstractmethod
    async def validar_stock_suficiente(
        self, 
        producto_id: UUID, 
        cantidad_salida: int
    ) -> bool:
        """
        Validar si hay stock suficiente para una salida.

        Implementa BR-01: Stock no puede ser negativo.

        Args:
            producto_id: UUID del producto
            cantidad_salida: Cantidad que se quiere sacar

        Returns:
            True si hay stock suficiente, False en caso contrario
        """
        pass

    @abstractmethod
    async def get_estadisticas_inventario(
        self,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> EstadisticasInventario:
        """
        Obtener estadísticas generales de inventario.

        Args:
            fecha_desde: Fecha desde para el cálculo
            fecha_hasta: Fecha hasta para el cálculo

        Returns:
            EstadisticasInventario: Estadísticas del período
        """
        pass

    @abstractmethod
    async def get_productos_mas_movidos(
        self,
        limit: int = 10,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> List[dict]:
        """
        Obtener los productos con más movimientos.

        Args:
            limit: Número de productos a retornar
            fecha_desde: Fecha desde para el cálculo
            fecha_hasta: Fecha hasta para el cálculo

        Returns:
            Lista de diccionarios con producto_id, nombre y total_movimientos
        """
        pass

    @abstractmethod
    async def recalcular_costos_producto(self, producto_id: UUID) -> bool:
        """
        Recalcular todos los costos promedio de un producto.

        Útil para correcciones o migraciones de datos.

        Args:
            producto_id: UUID del producto

        Returns:
            True si se recalculó exitosamente

        Note:
            Recalcula secuencialmente todos los movimientos del producto
        """
        pass

    @abstractmethod
    async def get_movimientos_pendientes_costo(self) -> List[MovimientoInventario]:
        """
        Obtener movimientos que no tienen costo_unitario calculado.

        Returns:
            Lista de movimientos sin costo calculado

        Note:
            Útil para procesos de migración o corrección de datos
        """
        pass 