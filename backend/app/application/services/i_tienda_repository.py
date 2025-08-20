"""
Interface del repositorio para la entidad Tienda en el sistema multi-tenant.

Define las operaciones de persistencia para gestionar tiendas con sus 
configuraciones y numeración de facturas.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.models.tienda import Tienda, TiendaCreate, TiendaUpdate


class ITiendaRepository(ABC):
    """
    Interface del repositorio para gestión de tiendas.
    
    Define las operaciones CRUD básicas y consultas específicas 
    para el manejo de tiendas en el sistema multi-tenant.
    """

    @abstractmethod
    async def create(self, tienda_data: TiendaCreate) -> Tienda:
        """
        Crea una nueva tienda en el sistema.

        Args:
            tienda_data: Datos para crear la tienda

        Returns:
            Tienda: La tienda creada con ID asignado

        Raises:
            ValueError: Si el código de tienda ya existe
            ValidationError: Si los datos no son válidos
        """
        pass

    @abstractmethod
    async def get_by_id(self, tienda_id: UUID) -> Optional[Tienda]:
        """
        Obtiene una tienda por su ID.

        Args:
            tienda_id: ID único de la tienda

        Returns:
            Tienda o None si no existe
        """
        pass

    @abstractmethod
    async def get_by_codigo(self, codigo: str) -> Optional[Tienda]:
        """
        Obtiene una tienda por su código único.

        Args:
            codigo: Código único de la tienda

        Returns:
            Tienda o None si no existe
        """
        pass

    @abstractmethod
    async def get_by_dominio(self, dominio: str) -> Optional[Tienda]:
        """
        Obtiene una tienda por su dominio (para multi-tenancy por subdomain).

        Args:
            dominio: Dominio de la tienda

        Returns:
            Tienda o None si no existe
        """
        pass

    @abstractmethod
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[Tienda]:
        """
        Obtiene todas las tiendas con paginación.

        Args:
            skip: Número de registros a omitir
            limit: Número máximo de registros a retornar
            include_inactive: Si incluir tiendas inactivas

        Returns:
            Lista de tiendas
        """
        pass

    @abstractmethod
    async def update(self, tienda_id: UUID, tienda_data: TiendaUpdate) -> Optional[Tienda]:
        """
        Actualiza una tienda existente.

        Args:
            tienda_id: ID de la tienda a actualizar
            tienda_data: Datos a actualizar

        Returns:
            Tienda actualizada o None si no existe

        Raises:
            ValueError: Si el nuevo código ya existe en otra tienda
        """
        pass

    @abstractmethod
    async def delete(self, tienda_id: UUID) -> bool:
        """
        Elimina (desactiva) una tienda.

        Args:
            tienda_id: ID de la tienda a eliminar

        Returns:
            True si se eliminó correctamente, False si no existe
        """
        pass

    @abstractmethod
    async def get_tiendas_activas(self) -> List[Tienda]:
        """
        Obtiene todas las tiendas activas.

        Returns:
            Lista de tiendas activas
        """
        pass

    @abstractmethod
    async def incrementar_consecutivo_factura(self, tienda_id: UUID) -> Optional[str]:
        """
        Incrementa el consecutivo de facturación y retorna el número generado.

        Args:
            tienda_id: ID de la tienda

        Returns:
            Número de factura generado (ej: "F-001") o None si no existe la tienda

        Raises:
            ConcurrencyError: Si hay conflicto en la numeración concurrente
        """
        pass

    @abstractmethod
    async def verificar_codigo_disponible(self, codigo: str, tienda_id: Optional[UUID] = None) -> bool:
        """
        Verifica si un código de tienda está disponible.

        Args:
            codigo: Código a verificar
            tienda_id: ID de tienda a excluir (para updates)

        Returns:
            True si está disponible, False si ya existe
        """
        pass

    @abstractmethod
    async def get_with_locales(self, tienda_id: UUID) -> Optional[Tienda]:
        """
        Obtiene una tienda con sus locales asociados.

        Args:
            tienda_id: ID de la tienda

        Returns:
            Tienda con locales cargados o None si no existe
        """
        pass

    @abstractmethod
    async def get_estadisticas_tienda(self, tienda_id: UUID) -> dict:
        """
        Obtiene estadísticas básicas de una tienda.

        Args:
            tienda_id: ID de la tienda

        Returns:
            Diccionario con estadísticas:
            - total_locales: Número de locales
            - locales_activos: Locales activos
            - total_productos: Productos en la tienda
            - total_usuarios: Usuarios asignados
        """
        pass