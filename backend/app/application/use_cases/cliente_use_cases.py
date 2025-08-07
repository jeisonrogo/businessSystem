"""
Casos de uso para la gestión de clientes.

Implementa la lógica de negocio para operaciones relacionadas con clientes,
incluyendo validaciones específicas y manejo de excepciones.
"""

from typing import List, Optional
from uuid import UUID

from app.application.services.i_cliente_repository import IClienteRepository
from app.domain.models.facturacion import (
    Cliente,
    ClienteCreate,
    ClienteUpdate,
    ClienteResponse,
    TipoCliente,
    TipoDocumento
)


# Excepciones personalizadas

class ClienteError(Exception):
    """Excepción base para errores de cliente."""
    pass


class ClienteNotFoundError(ClienteError):
    """Error cuando no se encuentra un cliente."""
    pass


class DuplicateDocumentError(ClienteError):
    """Error cuando se intenta crear un cliente con documento duplicado."""
    pass


class ClienteInUseError(ClienteError):
    """Error cuando se intenta eliminar un cliente que tiene facturas asociadas."""
    pass


# Casos de uso

class CreateClienteUseCase:
    """Caso de uso para crear un nuevo cliente."""
    
    def __init__(self, cliente_repository: IClienteRepository):
        self.cliente_repository = cliente_repository
    
    async def execute(self, cliente_data: ClienteCreate) -> Cliente:
        """
        Crear un nuevo cliente.
        
        Args:
            cliente_data: Datos del cliente a crear
            
        Returns:
            Cliente: El cliente creado
            
        Raises:
            DuplicateDocumentError: Si el documento ya existe
            ClienteError: Si hay otros errores de validación
        """
        try:
            # Verificar que no existe el documento
            existing_cliente = await self.cliente_repository.get_by_documento(
                cliente_data.numero_documento
            )
            if existing_cliente:
                raise DuplicateDocumentError(
                    f"Ya existe un cliente con el documento {cliente_data.numero_documento}"
                )
            
            # Verificar email si se proporciona
            if cliente_data.email:
                existing_email = await self.cliente_repository.get_by_email(cliente_data.email)
                if existing_email:
                    raise DuplicateDocumentError(
                        f"Ya existe un cliente con el email {cliente_data.email}"
                    )
            
            # Crear el cliente
            return await self.cliente_repository.create(cliente_data)
        
        except DuplicateDocumentError:
            raise
        except Exception as e:
            raise ClienteError(f"Error al crear el cliente: {str(e)}")


class GetClienteUseCase:
    """Caso de uso para obtener un cliente por ID."""
    
    def __init__(self, cliente_repository: IClienteRepository):
        self.cliente_repository = cliente_repository
    
    async def execute(self, cliente_id: UUID) -> Cliente:
        """
        Obtener un cliente por ID.
        
        Args:
            cliente_id: UUID del cliente
            
        Returns:
            Cliente: El cliente encontrado
            
        Raises:
            ClienteNotFoundError: Si no se encuentra el cliente
        """
        cliente = await self.cliente_repository.get_by_id(cliente_id)
        if not cliente:
            raise ClienteNotFoundError(f"Cliente con ID {cliente_id} no encontrado")
        
        return cliente


class GetClienteByDocumentoUseCase:
    """Caso de uso para obtener un cliente por documento."""
    
    def __init__(self, cliente_repository: IClienteRepository):
        self.cliente_repository = cliente_repository
    
    async def execute(self, numero_documento: str) -> Cliente:
        """
        Obtener un cliente por documento.
        
        Args:
            numero_documento: Número de documento del cliente
            
        Returns:
            Cliente: El cliente encontrado
            
        Raises:
            ClienteNotFoundError: Si no se encuentra el cliente
        """
        cliente = await self.cliente_repository.get_by_documento(numero_documento)
        if not cliente:
            raise ClienteNotFoundError(f"Cliente con documento {numero_documento} no encontrado")
        
        return cliente


class ListClientesUseCase:
    """Caso de uso para listar clientes con paginación y filtros."""
    
    def __init__(self, cliente_repository: IClienteRepository):
        self.cliente_repository = cliente_repository
    
    async def execute(
        self,
        page: int = 1,
        limit: int = 50,
        search: Optional[str] = None,
        tipo_cliente: Optional[TipoCliente] = None,
        only_active: bool = True
    ) -> dict:
        """
        Listar clientes con paginación.
        
        Args:
            page: Número de página (1-indexed)
            limit: Número de registros por página
            search: Término de búsqueda
            tipo_cliente: Filtrar por tipo de cliente
            only_active: Si solo incluir clientes activos
            
        Returns:
            dict: Lista de clientes con metadatos de paginación
        """
        # Validar parámetros
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 50
        
        skip = (page - 1) * limit
        
        # Obtener clientes y total
        clientes = await self.cliente_repository.get_all(
            skip=skip,
            limit=limit,
            search=search,
            tipo_cliente=tipo_cliente,
            only_active=only_active
        )
        
        total = await self.cliente_repository.count_total(
            search=search,
            tipo_cliente=tipo_cliente,
            only_active=only_active
        )
        
        # Calcular metadatos de paginación
        has_next = skip + limit < total
        has_prev = page > 1
        
        return {
            "clientes": clientes,
            "total": total,
            "page": page,
            "limit": limit,
            "has_next": has_next,
            "has_prev": has_prev
        }


class UpdateClienteUseCase:
    """Caso de uso para actualizar un cliente."""
    
    def __init__(self, cliente_repository: IClienteRepository):
        self.cliente_repository = cliente_repository
    
    async def execute(self, cliente_id: UUID, cliente_data: ClienteUpdate) -> Cliente:
        """
        Actualizar un cliente existente.
        
        Args:
            cliente_id: UUID del cliente a actualizar
            cliente_data: Nuevos datos del cliente
            
        Returns:
            Cliente: El cliente actualizado
            
        Raises:
            ClienteNotFoundError: Si no se encuentra el cliente
            ClienteError: Si hay errores de validación
        """
        try:
            # Verificar que existe el cliente
            existing_cliente = await self.cliente_repository.get_by_id(cliente_id)
            if not existing_cliente:
                raise ClienteNotFoundError(f"Cliente con ID {cliente_id} no encontrado")
            
            # Verificar email si se está actualizando
            if cliente_data.email and cliente_data.email != existing_cliente.email:
                existing_email = await self.cliente_repository.get_by_email(cliente_data.email)
                if existing_email and existing_email.id != cliente_id:
                    raise DuplicateDocumentError(
                        f"Ya existe otro cliente con el email {cliente_data.email}"
                    )
            
            # Actualizar el cliente
            updated_cliente = await self.cliente_repository.update(cliente_id, cliente_data)
            if not updated_cliente:
                raise ClienteNotFoundError(f"Cliente con ID {cliente_id} no encontrado")
            
            return updated_cliente
        
        except (ClienteNotFoundError, DuplicateDocumentError):
            raise
        except Exception as e:
            raise ClienteError(f"Error al actualizar el cliente: {str(e)}")


class DeleteClienteUseCase:
    """Caso de uso para eliminar (desactivar) un cliente."""
    
    def __init__(self, cliente_repository: IClienteRepository):
        self.cliente_repository = cliente_repository
    
    async def execute(self, cliente_id: UUID) -> bool:
        """
        Eliminar (desactivar) un cliente.
        
        Args:
            cliente_id: UUID del cliente a eliminar
            
        Returns:
            bool: True si se eliminó exitosamente
            
        Raises:
            ClienteNotFoundError: Si no se encuentra el cliente
            ClienteInUseError: Si el cliente tiene facturas asociadas
        """
        try:
            # Verificar que existe el cliente
            cliente = await self.cliente_repository.get_by_id(cliente_id)
            if not cliente:
                raise ClienteNotFoundError(f"Cliente con ID {cliente_id} no encontrado")
            
            # Verificar estadísticas del cliente para evitar eliminar clientes con facturas
            estadisticas = await self.cliente_repository.get_estadisticas_cliente(cliente_id)
            if estadisticas["total_facturas"] > 0:
                raise ClienteInUseError(
                    f"No se puede eliminar el cliente porque tiene {estadisticas['total_facturas']} facturas asociadas"
                )
            
            # Eliminar (desactivar) el cliente
            success = await self.cliente_repository.delete(cliente_id)
            if not success:
                raise ClienteNotFoundError(f"Cliente con ID {cliente_id} no encontrado")
            
            return True
        
        except (ClienteNotFoundError, ClienteInUseError):
            raise
        except Exception as e:
            raise ClienteError(f"Error al eliminar el cliente: {str(e)}")


class SearchClientesUseCase:
    """Caso de uso para búsqueda rápida de clientes."""
    
    def __init__(self, cliente_repository: IClienteRepository):
        self.cliente_repository = cliente_repository
    
    async def execute(self, term: str, limit: int = 20) -> List[Cliente]:
        """
        Buscar clientes por término.
        
        Args:
            term: Término de búsqueda
            limit: Número máximo de resultados
            
        Returns:
            List[Cliente]: Lista de clientes que coinciden
        """
        if not term or len(term.strip()) < 2:
            return []
        
        if limit < 1 or limit > 50:
            limit = 20
        
        return await self.cliente_repository.search_clientes(term.strip(), limit)


class GetClientesFrecuentesUseCase:
    """Caso de uso para obtener clientes frecuentes."""
    
    def __init__(self, cliente_repository: IClienteRepository):
        self.cliente_repository = cliente_repository
    
    async def execute(self, limit: int = 10) -> List[Cliente]:
        """
        Obtener clientes más frecuentes.
        
        Args:
            limit: Número máximo de clientes
            
        Returns:
            List[Cliente]: Lista de clientes frecuentes
        """
        if limit < 1 or limit > 50:
            limit = 10
        
        return await self.cliente_repository.get_clientes_frecuentes(limit)


class GetEstadisticasClienteUseCase:
    """Caso de uso para obtener estadísticas de un cliente."""
    
    def __init__(self, cliente_repository: IClienteRepository):
        self.cliente_repository = cliente_repository
    
    async def execute(self, cliente_id: UUID) -> dict:
        """
        Obtener estadísticas de un cliente.
        
        Args:
            cliente_id: UUID del cliente
            
        Returns:
            dict: Estadísticas del cliente
            
        Raises:
            ClienteNotFoundError: Si no se encuentra el cliente
        """
        # Verificar que existe el cliente
        cliente = await self.cliente_repository.get_by_id(cliente_id)
        if not cliente:
            raise ClienteNotFoundError(f"Cliente con ID {cliente_id} no encontrado")
        
        return await self.cliente_repository.get_estadisticas_cliente(cliente_id)


class ActivateClienteUseCase:
    """Caso de uso para reactivar un cliente desactivado."""
    
    def __init__(self, cliente_repository: IClienteRepository):
        self.cliente_repository = cliente_repository
    
    async def execute(self, cliente_id: UUID) -> bool:
        """
        Reactivar un cliente desactivado.
        
        Args:
            cliente_id: UUID del cliente a reactivar
            
        Returns:
            bool: True si se reactivó exitosamente
            
        Raises:
            ClienteNotFoundError: Si no se encuentra el cliente
        """
        success = await self.cliente_repository.activate_cliente(cliente_id)
        if not success:
            raise ClienteNotFoundError(f"Cliente con ID {cliente_id} no encontrado")
        
        return True


class GetClientesByTipoUseCase:
    """Caso de uso para obtener clientes por tipo."""
    
    def __init__(self, cliente_repository: IClienteRepository):
        self.cliente_repository = cliente_repository
    
    async def execute(self, tipo_cliente: TipoCliente) -> List[Cliente]:
        """
        Obtener clientes por tipo.
        
        Args:
            tipo_cliente: Tipo de cliente a buscar
            
        Returns:
            List[Cliente]: Lista de clientes del tipo especificado
        """
        return await self.cliente_repository.get_clientes_by_tipo(tipo_cliente)