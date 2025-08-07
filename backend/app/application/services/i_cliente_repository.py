"""
Interfaz del repositorio de clientes.

Define el contrato abstracto para el acceso a datos de clientes,
siguiendo el principio de inversión de dependencias de Clean Architecture.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.models.facturacion import (
    Cliente,
    ClienteCreate,
    ClienteUpdate,
    TipoCliente,
    TipoDocumento
)


class IClienteRepository(ABC):
    """
    Interfaz abstracta para el repositorio de clientes.
    
    Define todas las operaciones de acceso a datos para la entidad Cliente.
    Las implementaciones concretas manejarán la persistencia específica.
    """

    @abstractmethod
    async def create(self, cliente_data: ClienteCreate) -> Cliente:
        """
        Crear un nuevo cliente.
        
        Args:
            cliente_data: Datos del cliente a crear
            
        Returns:
            Cliente: El cliente creado con su ID generado
            
        Raises:
            ValueError: Si el número de documento ya existe
            IntegrityError: Si hay problemas de integridad en la BD
        """
        pass

    @abstractmethod
    async def get_by_id(self, cliente_id: UUID) -> Optional[Cliente]:
        """
        Obtener un cliente por su ID.
        
        Args:
            cliente_id: UUID del cliente
            
        Returns:
            Optional[Cliente]: El cliente si existe, None en caso contrario
        """
        pass

    @abstractmethod
    async def get_by_documento(self, numero_documento: str) -> Optional[Cliente]:
        """
        Obtener un cliente por su número de documento.
        
        Args:
            numero_documento: Número de documento del cliente
            
        Returns:
            Optional[Cliente]: El cliente si existe, None en caso contrario
        """
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Cliente]:
        """
        Obtener un cliente por su email.
        
        Args:
            email: Email del cliente
            
        Returns:
            Optional[Cliente]: El cliente si existe, None en caso contrario
        """
        pass

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        tipo_cliente: Optional[TipoCliente] = None,
        only_active: bool = True
    ) -> List[Cliente]:
        """
        Obtener lista paginada de clientes con filtros opcionales.
        
        Args:
            skip: Número de registros a saltar para paginación
            limit: Número máximo de registros a retornar
            search: Término de búsqueda para nombre, documento o email
            tipo_cliente: Filtrar por tipo de cliente
            only_active: Si solo incluir clientes activos
            
        Returns:
            List[Cliente]: Lista de clientes que cumplen los criterios
        """
        pass

    @abstractmethod
    async def update(self, cliente_id: UUID, cliente_data: ClienteUpdate) -> Optional[Cliente]:
        """
        Actualizar un cliente existente.
        
        Args:
            cliente_id: UUID del cliente a actualizar
            cliente_data: Nuevos datos del cliente
            
        Returns:
            Optional[Cliente]: El cliente actualizado si existe, None en caso contrario
            
        Raises:
            ValueError: Si hay problemas de validación
        """
        pass

    @abstractmethod
    async def delete(self, cliente_id: UUID) -> bool:
        """
        Eliminar (desactivar) un cliente.
        
        Realiza soft delete marcando is_active=False.
        
        Args:
            cliente_id: UUID del cliente a eliminar
            
        Returns:
            bool: True si se eliminó exitosamente, False si no existía
        """
        pass

    @abstractmethod
    async def exists_by_documento(
        self,
        numero_documento: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """
        Verificar si existe un cliente con el número de documento dado.
        
        Args:
            numero_documento: Número de documento a verificar
            exclude_id: ID del cliente a excluir de la búsqueda (útil para updates)
            
        Returns:
            bool: True si existe un cliente con ese documento, False en caso contrario
        """
        pass

    @abstractmethod
    async def count_total(
        self,
        search: Optional[str] = None,
        tipo_cliente: Optional[TipoCliente] = None,
        only_active: bool = True
    ) -> int:
        """
        Contar el número total de clientes que cumplen los criterios.
        
        Args:
            search: Término de búsqueda para nombre, documento o email
            tipo_cliente: Filtrar por tipo de cliente
            only_active: Si solo contar clientes activos
            
        Returns:
            int: Número total de clientes
        """
        pass

    @abstractmethod
    async def get_clientes_frecuentes(self, limit: int = 10) -> List[Cliente]:
        """
        Obtener los clientes más frecuentes basado en número de facturas.
        
        Args:
            limit: Número máximo de clientes a retornar
            
        Returns:
            List[Cliente]: Lista de clientes más frecuentes
        """
        pass

    @abstractmethod
    async def get_clientes_by_tipo(self, tipo_cliente: TipoCliente) -> List[Cliente]:
        """
        Obtener todos los clientes de un tipo específico.
        
        Args:
            tipo_cliente: Tipo de cliente a buscar
            
        Returns:
            List[Cliente]: Lista de clientes del tipo especificado
        """
        pass

    @abstractmethod
    async def search_clientes(
        self,
        term: str,
        limit: int = 20
    ) -> List[Cliente]:
        """
        Buscar clientes por término (nombre, documento, email).
        
        Búsqueda más flexible para autocompletado.
        
        Args:
            term: Término de búsqueda
            limit: Número máximo de resultados
            
        Returns:
            List[Cliente]: Lista de clientes que coinciden con el término
        """
        pass

    @abstractmethod
    async def get_estadisticas_cliente(self, cliente_id: UUID) -> dict:
        """
        Obtener estadísticas de un cliente específico.
        
        Args:
            cliente_id: UUID del cliente
            
        Returns:
            dict: Estadísticas del cliente (total facturas, monto total, etc.)
        """
        pass

    @abstractmethod
    async def activate_cliente(self, cliente_id: UUID) -> bool:
        """
        Reactivar un cliente desactivado.
        
        Args:
            cliente_id: UUID del cliente a reactivar
            
        Returns:
            bool: True si se reactivó exitosamente, False si no existía
        """
        pass