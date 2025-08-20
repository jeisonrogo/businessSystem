"""
Interface del repositorio para la entidad StockLocal en el sistema multi-tenant.

Define las operaciones de persistencia para gestionar inventario independiente
por local con cálculos de costo promedio ponderado.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal

from app.domain.models.stock_local import (
    StockLocal, 
    StockLocalCreate, 
    StockLocalUpdate,
    StockLocalAjuste
)


class IStockLocalRepository(ABC):
    """
    Interface del repositorio para gestión de stock por local.
    
    Define las operaciones para manejo de inventario independiente
    en cada local con control de costos promedio ponderado.
    """

    @abstractmethod
    def create(self, stock_data: StockLocalCreate) -> StockLocal:
        """
        Crea un registro de stock inicial para un producto en un local.

        Args:
            stock_data: Datos para crear el stock

        Returns:
            StockLocal: El registro de stock creado

        Raises:
            ValueError: Si ya existe stock para el producto en el local
            ForeignKeyError: Si el producto o local no existen
        """
        pass

    @abstractmethod
    def get_by_id(self, stock_id: UUID) -> Optional[StockLocal]:
        """
        Obtiene un registro de stock por su ID.

        Args:
            stock_id: ID único del registro de stock

        Returns:
            StockLocal o None si no existe
        """
        pass

    @abstractmethod
    def get_by_producto_and_local(
        self, 
        producto_id: UUID, 
        local_id: UUID
    ) -> Optional[StockLocal]:
        """
        Obtiene el stock de un producto específico en un local.

        Args:
            producto_id: ID del producto
            local_id: ID del local

        Returns:
            StockLocal o None si no existe
        """
        pass

    @abstractmethod
    def get_by_local(
        self, 
        local_id: UUID,
        skip: int = 0,
        limit: int = 100,
        incluir_sin_stock: bool = True
    ) -> List[StockLocal]:
        """
        Obtiene todo el stock de un local con paginación.

        Args:
            local_id: ID del local
            skip: Número de registros a omitir
            limit: Número máximo de registros a retornar
            incluir_sin_stock: Si incluir productos con cantidad 0

        Returns:
            Lista de registros de stock del local
        """
        pass

    @abstractmethod
    def get_by_producto(self, producto_id: UUID) -> List[StockLocal]:
        """
        Obtiene el stock de un producto en todos los locales.

        Args:
            producto_id: ID del producto

        Returns:
            Lista de registros de stock del producto por local
        """
        pass

    @abstractmethod
    def get_by_tienda(
        self, 
        tienda_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StockLocal]:
        """
        Obtiene todo el stock de una tienda (todos sus locales).

        Args:
            tienda_id: ID de la tienda
            skip: Número de registros a omitir
            limit: Número máximo de registros a retornar

        Returns:
            Lista de registros de stock de la tienda
        """
        pass

    @abstractmethod
    def actualizar_stock(
        self,
        producto_id: UUID,
        local_id: UUID,
        nueva_cantidad: int,
        nuevo_costo: Optional[Decimal] = None,
        usuario_id: Optional[UUID] = None
    ) -> Optional[StockLocal]:
        """
        Actualiza el stock de un producto en un local.

        Args:
            producto_id: ID del producto
            local_id: ID del local
            nueva_cantidad: Nueva cantidad de stock
            nuevo_costo: Nuevo costo unitario (opcional)
            usuario_id: ID del usuario que realiza la actualización

        Returns:
            StockLocal actualizado o None si no existe

        Raises:
            ValueError: Si la cantidad es negativa
        """
        pass

    @abstractmethod
    def incrementar_stock(
        self,
        producto_id: UUID,
        local_id: UUID,
        cantidad_incremento: int,
        costo_unitario: Optional[Decimal] = None,
        usuario_id: Optional[UUID] = None
    ) -> Optional[StockLocal]:
        """
        Incrementa el stock con cálculo de costo promedio ponderado.

        Args:
            producto_id: ID del producto
            local_id: ID del local
            cantidad_incremento: Cantidad a agregar
            costo_unitario: Costo del stock agregado
            usuario_id: ID del usuario que realiza la operación

        Returns:
            StockLocal actualizado o None si no existe

        Raises:
            ValueError: Si el incremento es negativo o zero
        """
        pass

    @abstractmethod
    def decrementar_stock(
        self,
        producto_id: UUID,
        local_id: UUID,
        cantidad_decremento: int,
        usuario_id: Optional[UUID] = None
    ) -> Optional[StockLocal]:
        """
        Decrementa el stock manteniendo el costo promedio.

        Args:
            producto_id: ID del producto
            local_id: ID del local
            cantidad_decremento: Cantidad a restar
            usuario_id: ID del usuario que realiza la operación

        Returns:
            StockLocal actualizado o None si no existe

        Raises:
            ValueError: Si no hay stock suficiente o el decremento es inválido
        """
        pass

    @abstractmethod
    def update_configuracion(
        self,
        stock_id: UUID,
        stock_data: StockLocalUpdate
    ) -> Optional[StockLocal]:
        """
        Actualiza la configuración de stock (mínimos, máximos, etc.).

        Args:
            stock_id: ID del registro de stock
            stock_data: Datos de configuración a actualizar

        Returns:
            StockLocal actualizado o None si no existe
        """
        pass

    @abstractmethod
    def delete(self, stock_id: UUID) -> bool:
        """
        Elimina un registro de stock (solo si cantidad es 0).

        Args:
            stock_id: ID del registro de stock

        Returns:
            True si se eliminó, False si no existe o tiene stock

        Raises:
            ValueError: Si intenta eliminar stock con cantidad > 0
        """
        pass

    @abstractmethod
    def get_productos_bajo_minimo(self, local_id: UUID) -> List[StockLocal]:
        """
        Obtiene productos con stock por debajo del mínimo en un local.

        Args:
            local_id: ID del local

        Returns:
            Lista de productos con stock bajo mínimo
        """
        pass

    @abstractmethod
    def get_productos_agotados(self, local_id: UUID) -> List[StockLocal]:
        """
        Obtiene productos agotados (cantidad = 0) en un local.

        Args:
            local_id: ID del local

        Returns:
            Lista de productos agotados
        """
        pass

    @abstractmethod
    def get_resumen_por_local(self, local_id: UUID) -> Dict[str, Any]:
        """
        Obtiene resumen de inventario de un local.

        Args:
            local_id: ID del local

        Returns:
            Diccionario con resumen:
            - total_productos: Total de productos con registro
            - productos_con_stock: Productos con cantidad > 0
            - productos_bajo_minimo: Productos bajo mínimo
            - productos_agotados: Productos sin stock
            - valor_total_inventario: Valor total del inventario
        """
        pass

    @abstractmethod
    def get_stock_global_producto(self, producto_id: UUID) -> Dict[str, Any]:
        """
        Obtiene el stock global de un producto en todos los locales.

        Args:
            producto_id: ID del producto

        Returns:
            Diccionario con información global:
            - stock_total: Stock total en todos los locales
            - stock_por_local: Lista de stock por local
            - costo_promedio_global: Costo promedio ponderado global
            - valor_total_global: Valor total del producto
        """
        pass

    @abstractmethod
    def buscar_productos_con_stock(
        self,
        tienda_id: UUID,
        texto_busqueda: str,
        local_id: Optional[UUID] = None
    ) -> List[StockLocal]:
        """
        Busca productos con stock por nombre o SKU.

        Args:
            tienda_id: ID de la tienda
            texto_busqueda: Texto a buscar en nombre o SKU
            local_id: Local específico (opcional)

        Returns:
            Lista de productos que coinciden con la búsqueda
        """
        pass

    @abstractmethod
    def validar_stock_disponible(
        self,
        producto_id: UUID,
        local_id: UUID,
        cantidad_requerida: int
    ) -> bool:
        """
        Valida si hay stock suficiente para una operación.

        Args:
            producto_id: ID del producto
            local_id: ID del local
            cantidad_requerida: Cantidad necesaria

        Returns:
            True si hay stock suficiente, False si no
        """
        pass