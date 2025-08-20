"""
Interface del repositorio para la entidad Local en el sistema multi-tenant.

Define las operaciones de persistencia para gestionar locales (ubicaciones físicas)
dentro de cada tienda.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.domain.models.local import Local, LocalCreate, LocalUpdate


class ILocalRepository(ABC):
    """
    Interface del repositorio para gestión de locales.
    
    Define las operaciones CRUD y consultas específicas para el manejo
    de locales dentro del contexto de cada tienda.
    """

    @abstractmethod
    async def create(self, local_data: LocalCreate) -> Local:
        """
        Crea un nuevo local en una tienda.

        Args:
            local_data: Datos para crear el local

        Returns:
            Local: El local creado con ID asignado

        Raises:
            ValueError: Si el código ya existe en la tienda
            ValidationError: Si los datos no son válidos
            ForeignKeyError: Si la tienda no existe
        """
        pass

    @abstractmethod
    async def get_by_id(self, local_id: UUID) -> Optional[Local]:
        """
        Obtiene un local por su ID.

        Args:
            local_id: ID único del local

        Returns:
            Local o None si no existe
        """
        pass

    @abstractmethod
    async def get_by_codigo_and_tienda(self, codigo: str, tienda_id: UUID) -> Optional[Local]:
        """
        Obtiene un local por su código dentro de una tienda específica.

        Args:
            codigo: Código del local
            tienda_id: ID de la tienda

        Returns:
            Local o None si no existe
        """
        pass

    @abstractmethod
    async def get_by_tienda(
        self, 
        tienda_id: UUID, 
        skip: int = 0, 
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[Local]:
        """
        Obtiene todos los locales de una tienda con paginación.

        Args:
            tienda_id: ID de la tienda
            skip: Número de registros a omitir
            limit: Número máximo de registros a retornar
            include_inactive: Si incluir locales inactivos

        Returns:
            Lista de locales de la tienda
        """
        pass

    @abstractmethod
    async def get_locales_activos_by_tienda(self, tienda_id: UUID) -> List[Local]:
        """
        Obtiene todos los locales activos de una tienda.

        Args:
            tienda_id: ID de la tienda

        Returns:
            Lista de locales activos
        """
        pass

    @abstractmethod
    async def update(self, local_id: UUID, local_data: LocalUpdate) -> Optional[Local]:
        """
        Actualiza un local existente.

        Args:
            local_id: ID del local a actualizar
            local_data: Datos a actualizar

        Returns:
            Local actualizado o None si no existe

        Raises:
            ValueError: Si el nuevo código ya existe en la tienda
        """
        pass

    @abstractmethod
    async def delete(self, local_id: UUID) -> bool:
        """
        Elimina (desactiva) un local.

        Args:
            local_id: ID del local a eliminar

        Returns:
            True si se eliminó correctamente, False si no existe
        """
        pass

    @abstractmethod
    async def verificar_codigo_disponible(
        self, 
        codigo: str, 
        tienda_id: UUID, 
        local_id: Optional[UUID] = None
    ) -> bool:
        """
        Verifica si un código de local está disponible dentro de una tienda.

        Args:
            codigo: Código a verificar
            tienda_id: ID de la tienda
            local_id: ID de local a excluir (para updates)

        Returns:
            True si está disponible, False si ya existe
        """
        pass

    @abstractmethod
    async def get_with_stock(self, local_id: UUID) -> Optional[Local]:
        """
        Obtiene un local con su información de stock asociado.

        Args:
            local_id: ID del local

        Returns:
            Local con stock cargado o None si no existe
        """
        pass

    @abstractmethod
    async def get_with_usuarios(self, local_id: UUID) -> Optional[Local]:
        """
        Obtiene un local con los usuarios que tienen permisos en él.

        Args:
            local_id: ID del local

        Returns:
            Local con usuarios cargados o None si no existe
        """
        pass

    @abstractmethod
    async def get_locales_usuario(self, user_id: UUID) -> List[Local]:
        """
        Obtiene todos los locales donde un usuario tiene permisos.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de locales donde el usuario tiene acceso
        """
        pass

    @abstractmethod
    async def get_locales_para_transferencia(
        self, 
        local_origen_id: UUID
    ) -> List[Local]:
        """
        Obtiene locales disponibles para transferencia desde un local origen.
        (Todos los locales de la misma tienda excepto el origen)

        Args:
            local_origen_id: ID del local origen

        Returns:
            Lista de locales destino disponibles
        """
        pass

    @abstractmethod
    async def get_estadisticas_local(self, local_id: UUID) -> Dict[str, Any]:
        """
        Obtiene estadísticas básicas de un local.

        Args:
            local_id: ID del local

        Returns:
            Diccionario con estadísticas:
            - total_productos: Productos con stock en el local
            - total_stock: Stock total en el local
            - valor_inventario: Valor total del inventario
            - productos_bajo_minimo: Productos con stock bajo mínimo
            - total_usuarios: Usuarios con permisos en el local
            - transferencias_pendientes: Transferencias sin completar
        """
        pass

    @abstractmethod
    async def buscar_locales(
        self, 
        tienda_id: UUID,
        texto_busqueda: str,
        ciudad: Optional[str] = None,
        departamento: Optional[str] = None
    ) -> List[Local]:
        """
        Busca locales por texto en nombre, código o dirección.

        Args:
            tienda_id: ID de la tienda
            texto_busqueda: Texto a buscar
            ciudad: Filtro opcional por ciudad
            departamento: Filtro opcional por departamento

        Returns:
            Lista de locales que coinciden con la búsqueda
        """
        pass